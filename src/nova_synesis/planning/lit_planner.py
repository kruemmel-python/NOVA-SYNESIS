from __future__ import annotations

import ast
import json
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nova_synesis.config import Settings
from nova_synesis.domain.models import ResourceType, RollbackStrategy

DEFAULT_RETRY_POLICY: dict[str, Any] = {
    "max_retries": 3,
    "backoff_ms": 250,
    "exponential": True,
    "max_backoff_ms": 10_000,
    "jitter_ratio": 0.0,
}


@dataclass(slots=True)
class PlannerCatalog:
    handlers: list[str]
    agents: list[dict[str, Any]]
    resources: list[dict[str, Any]]
    memory_systems: list[dict[str, Any]]


@dataclass(slots=True)
class PlannerGraphResult:
    flow_request: dict[str, Any]
    explanation: str | None
    warnings: list[str]
    raw_response: str
    model_path: str
    backend: str


class LiteRTPlanner:
    _STANDARD_PROMPT_MAX_CHARS = 12_000
    _COMPACT_PROMPT_MAX_CHARS = 9_000
    _MINIMAL_PROMPT_MAX_CHARS = 6_500

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.binary_path = Path(settings.lit_binary_path).resolve()
        self.model_path = Path(settings.lit_model_path).resolve()

    def status(self) -> dict[str, Any]:
        return {
            "available": self.binary_path.exists() and self.model_path.exists(),
            "binary_path": str(self.binary_path),
            "model_path": str(self.model_path),
            "backend": self.settings.lit_backend,
            "timeout_s": self.settings.lit_timeout_s,
        }

    def ensure_available(self) -> None:
        if not self.binary_path.exists():
            raise FileNotFoundError(f"LiteRT binary not found: {self.binary_path}")
        if not self.model_path.exists():
            raise FileNotFoundError(f"LiteRT model not found: {self.model_path}")

    def generate_text(self, prompt: str, *, timeout_s: int | None = None) -> str:
        self.ensure_available()
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise ValueError("LiteRT text generation requires a non-empty prompt")
        return self._invoke_model(normalized_prompt, timeout_s=timeout_s)

    def generate_flow_request(
        self,
        prompt: str,
        catalog: PlannerCatalog,
        current_flow: dict[str, Any] | None = None,
        max_nodes: int = 12,
    ) -> PlannerGraphResult:
        self.ensure_available()
        planner_warnings: list[str] = []
        raw_response = ""
        prompt_variants = self._build_prompt_variants(
            prompt=prompt,
            catalog=catalog,
            current_flow=current_flow,
            max_nodes=max_nodes,
        )
        last_error: RuntimeError | None = None
        for attempt_index, planner_prompt in enumerate(prompt_variants):
            try:
                raw_response = self._invoke_model(planner_prompt)
                if attempt_index > 0:
                    planner_warnings.append(
                        "Planner prompt was compacted automatically to fit the local model context window."
                    )
                break
            except RuntimeError as exc:
                last_error = exc
                if attempt_index < len(prompt_variants) - 1 and self._looks_like_context_overflow(
                    str(exc)
                ):
                    continue
                raise

        if not raw_response and last_error is not None:
            raise last_error

        parsed, parse_warnings = self._parse_model_output_with_warnings(raw_response)
        normalized, warnings = self._normalize_flow_request(
            parsed=parsed,
            catalog=catalog,
            max_nodes=max_nodes,
        )
        return PlannerGraphResult(
            flow_request=normalized,
            explanation=self._extract_explanation(parsed),
            warnings=parse_warnings + planner_warnings + warnings,
            raw_response=raw_response,
            model_path=str(self.model_path),
            backend=self.settings.lit_backend,
        )

    def _invoke_model(self, planner_prompt: str, *, timeout_s: int | None = None) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".txt",
            prefix="nova_synesis_lit_prompt_",
            delete=False,
        ) as prompt_file:
            prompt_file.write(planner_prompt)
            prompt_path = Path(prompt_file.name)

        try:
            command = [
                str(self.binary_path),
                "run",
                str(self.model_path),
                "-f",
                str(prompt_path),
                "--backend",
                self.settings.lit_backend,
                "--min_log_level",
                "4",
            ]
            completed = self._run_lit_command(command, timeout_s=timeout_s)
            stdout = completed.stdout.strip()
            stderr = completed.stderr.strip()
            if completed.returncode == 0:
                if not stdout:
                    raise RuntimeError("LiteRT planner returned no output")
                return stdout

            detail = stderr or stdout or "LiteRT planner execution failed"
            if self._looks_like_engine_creation_failure(detail):
                quarantined_cache = self._quarantine_xnnpack_cache()
                if quarantined_cache is not None:
                    completed = self._run_lit_command(command, timeout_s=timeout_s)
                    stdout = completed.stdout.strip()
                    stderr = completed.stderr.strip()
                    if completed.returncode == 0:
                        if not stdout:
                            raise RuntimeError("LiteRT planner returned no output")
                        return stdout
                    detail = stderr or stdout or "LiteRT planner execution failed"
                    raise RuntimeError(
                        self._format_engine_creation_failure(detail, quarantined_cache=quarantined_cache)
                    )
                raise RuntimeError(self._format_engine_creation_failure(detail))

            raise RuntimeError(detail)
        finally:
            prompt_path.unlink(missing_ok=True)

    def _run_lit_command(
        self,
        command: list[str],
        *,
        timeout_s: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_s if timeout_s is not None else self.settings.lit_timeout_s,
                cwd=Path(self.settings.working_directory).resolve(),
            )
        except subprocess.TimeoutExpired as exc:
            waited_s = timeout_s if timeout_s is not None else self.settings.lit_timeout_s
            raise RuntimeError(
                f"LiteRT request timed out after {waited_s}s. Reduce the prompt size or switch back to template mode."
            ) from exc

    @staticmethod
    def _looks_like_engine_creation_failure(message: str) -> bool:
        normalized = message.casefold()
        return any(
            token in normalized
            for token in (
                "failed to create engine",
                "weight_cache.cc",
                "cannot get the address of a buffer in a cache",
                "cache file is stale",
                "xnnpack",
            )
        )

    def _xnnpack_cache_path(self) -> Path:
        return Path(f"{self.model_path}.xnnpack_cache")

    def _quarantine_xnnpack_cache(self) -> Path | None:
        cache_path = self._xnnpack_cache_path()
        if not cache_path.exists():
            return None
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        candidate = cache_path.with_name(f"{cache_path.name}.stale-{timestamp}")
        suffix = 1
        while candidate.exists():
            suffix += 1
            candidate = cache_path.with_name(f"{cache_path.name}.stale-{timestamp}-{suffix}")
        cache_path.replace(candidate)
        return candidate

    def _format_engine_creation_failure(
        self,
        detail: str,
        *,
        quarantined_cache: Path | None = None,
    ) -> str:
        prefix = (
            f"LiteRT could not create an inference engine for model '{self.model_path}' "
            f"on backend '{self.settings.lit_backend}'."
        )
        if quarantined_cache is not None:
            return (
                f"{prefix} A stale XNNPACK cache was quarantined to '{quarantined_cache}', "
                "but LiteRT still failed on retry. Verify that the selected model is compatible "
                f"with the current LiteRT binary '{self.binary_path}'. Original error: {detail}"
            )
        return (
            f"{prefix} If you just switched models, remove or regenerate the model-specific "
            f"XNNPACK cache '{self._xnnpack_cache_path()}' or try a different backend/model pair. "
            f"Original error: {detail}"
        )

    def _build_prompt(
        self,
        prompt: str,
        catalog: PlannerCatalog,
        current_flow: dict[str, Any] | None,
        max_nodes: int,
        *,
        detail_level: str,
        max_chars: int,
    ) -> str:
        schema = (
            '{"nodes":[{"node_id":"task-id","title":"Short title","handler_name":"allowed-handler",'
            '"input":{},"dependencies":[],"conditions":{},"required_capabilities":[],'
            '"required_resource_ids":[],"required_resource_types":[],"retry_policy":'
            '{"max_retries":3,"backoff_ms":250,"exponential":true,"max_backoff_ms":10000,'
            '"jitter_ratio":0.0},"rollback_strategy":"FAIL_FAST","preferred_agent_name":null}],'
            '"edges":[{"from_node":"node-a","to_node":"node-b","condition":"True"}],'
            '"explanation":"Brief rationale"}'
        )
        sections = [
            "You plan executable DAG workflows for NOVA-SYNESIS.",
            "Return exactly one JSON object. No markdown fences and no prose outside JSON.",
            f"Use this schema: {schema}",
            "\n".join(
                [
                    "Hard rules:",
                    f"- Maximum {max_nodes} nodes.",
                    "- DAG only. Do not create start, end or placeholder nodes.",
                    "- Every edge source and target must reference an existing node_id.",
                    '- Use "True" for unconditional edges.',
                    "- Use only listed handlers, agents, resources and memories.",
                    "- Agents are execution targets and preferred assignments only. Never put an agent name into handler_name.",
                    "- Build executable inputs for the chosen handler.",
                    "- Do not output TODO, placeholder, dummy, fake or sample values.",
                    "- Prefer preferred_agent_name over preferred_agent_id when selecting an agent.",
                    "- send_message may use target_agent_name or target_agent_id, but only for listed communication-enabled agents.",
                    "- Unless explicitly required, omit approval fields and keep rollback_strategy at FAIL_FAST.",
                    "- For news_search/topic_split workflows, write_csv must export topic_split csv_rows with fieldnames topic,title,source,published_at,link,summary. Do not write embeddings or vector payloads to CSV.",
                ]
            ),
            self._build_handler_section(catalog.handlers, detail_level),
            self._build_agent_section(catalog.agents, detail_level),
            self._build_send_target_section(catalog.agents, detail_level),
            self._build_resource_section(catalog.resources, detail_level),
            self._build_memory_section(catalog.memory_systems, detail_level),
            self._build_current_flow_section(current_flow, detail_level),
            f"User goal:\n{self._truncate_text(prompt.strip(), 2_000)}",
        ]
        prompt_text = "\n\n".join(section for section in sections if section.strip())
        return self._truncate_text(prompt_text, max_chars)

    def _build_prompt_variants(
        self,
        prompt: str,
        catalog: PlannerCatalog,
        current_flow: dict[str, Any] | None,
        max_nodes: int,
    ) -> list[str]:
        variants: list[str] = []
        seen: set[str] = set()
        for detail_level, max_chars in (
            ("standard", self._STANDARD_PROMPT_MAX_CHARS),
            ("compact", self._COMPACT_PROMPT_MAX_CHARS),
            ("minimal", self._MINIMAL_PROMPT_MAX_CHARS),
        ):
            candidate = self._build_prompt(
                prompt=prompt,
                catalog=catalog,
                current_flow=current_flow,
                max_nodes=max_nodes,
                detail_level=detail_level,
                max_chars=max_chars,
            )
            if candidate not in seen:
                seen.add(candidate)
                variants.append(candidate)
        return variants

    @staticmethod
    def _looks_like_context_overflow(message: str) -> bool:
        normalized = message.casefold()
        return (
            "input token ids are too long" in normalized
            or "maximum number of tokens allowed" in normalized
            or "context length" in normalized
            or "prompt is too long" in normalized
        )

    def _build_handler_section(self, handlers: list[str], detail_level: str) -> str:
        contract_map = {
            "http_request": "http_request: input keys url, method, optional headers/params/json/data",
            "filesystem_read": "filesystem_read: input key path; reads a local file from the working directory",
            "filesystem_write": "filesystem_write: input keys path, content, optional append; writes a local file in the working directory",
            "news_search": (
                "news_search: input keys query, optional language, country, time_range, max_items; "
                "uses the built-in Google News RSS search internally, does not require a manual URL, "
                "returns items from a trusted news feed under results[node_id]['items']"
            ),
            "topic_split": (
                "topic_split: input keys items, topics, optional include_uncategorized; "
                "items should normally reference results[upstream_node]['items']; "
                "returns grouped topics and csv_rows with columns topic, title, source, published_at, link, summary"
            ),
            "generate_embedding": (
                "generate_embedding: input key data; data should normally reference the full upstream result "
                "object and it returns embedding, value and metadata for vector memory storage"
            ),
            "memory_store": "memory_store: input keys memory_id, key, value",
            "memory_retrieve": "memory_retrieve: input keys memory_id, key",
            "memory_search": "memory_search: input keys memory_id, query, optional limit",
            "send_message": "send_message: input keys target_agent_name or target_agent_id, message",
            "resource_health_check": "resource_health_check: optional resource_ids list",
            "template_render": "template_render: input keys template, values",
            "local_llm_text": (
                "local_llm_text: input keys prompt or instruction plus data, optional system_prompt and timeout_s; "
                "returns text and prompt for local LiteRT-based analysis or generation"
            ),
            "merge_payloads": "merge_payloads: input keys base, updates",
            "read_file": "read_file: input key path",
            "write_file": "write_file: input keys path, content, optional append",
            "write_csv": (
                "write_csv: input keys path, rows, optional fieldnames, encoding; "
                "rows should normally reference results[upstream_node]['csv_rows']; "
                "for topic_split upstream the fieldnames should be topic, title, source, published_at, link, summary"
            ),
            "json_serialize": "json_serialize: input key value, optional indent",
            "accounts_receivable_extract": (
                "accounts_receivable_extract: input keys path, optional source_type csv|sqlite, "
                "optional table, optional as_of"
            ),
            "accounts_receivable_generate_letters": (
                "accounts_receivable_generate_letters: input keys receivables, optional sender_company, "
                "sender_email, sender_phone, sender_address, payment_deadline_days, "
                "optional generation_mode template|llm, prompt_template, user_instruction, "
                "fallback_to_template_on_error"
            ),
            "accounts_receivable_write_letters": (
                "accounts_receivable_write_letters: input keys letters, output_directory, optional manifest_path, "
                "summary_path, encoding, output_format txt|docx"
            ),
        }
        lines = [contract_map.get(handler, handler) for handler in handlers]
        if detail_level == "minimal":
            lines = [f"- {handler}" for handler in handlers]
        else:
            lines = [f"- {line}" for line in lines]
        return "Allowed handlers:\n" + "\n".join(lines)

    def _build_agent_section(self, agents: list[dict[str, Any]], detail_level: str) -> str:
        if not agents:
            return "Known agents:\n- none\nAgents are not handlers."
        max_items = 24 if detail_level == "standard" else 14 if detail_level == "compact" else 8
        lines: list[str] = []
        for agent in agents[:max_items]:
            capabilities = [
                str(capability.get("name")).strip()
                for capability in agent.get("capabilities", [])
                if str(capability.get("name", "")).strip()
            ]
            capability_text = ", ".join(capabilities[:5]) if capabilities else "none"
            receiver = "yes" if isinstance(agent.get("communication"), dict) else "no"
            lines.append(
                f"- {agent['name']} (id={agent['agent_id']}, role={agent['role']}, caps={capability_text}, can_receive={receiver})"
            )
        if len(agents) > max_items:
            lines.append(f"- ... {len(agents) - max_items} more agents omitted")
        return "Known agents (never use these names as handler_name values):\n" + "\n".join(lines)

    def _build_send_target_section(self, agents: list[dict[str, Any]], detail_level: str) -> str:
        communication_agents = [
            agent for agent in agents if isinstance(agent.get("communication"), dict)
        ]
        if not communication_agents:
            return (
                "Allowed send_message targets:\n"
                "- none\n"
                "If no communication-enabled agent is listed, do not create a send_message node."
            )
        max_items = 16 if detail_level == "standard" else 10 if detail_level == "compact" else 6
        lines = [
            f"- {agent['name']} (id={agent['agent_id']}, protocol={agent['communication'].get('protocol')})"
            for agent in communication_agents[:max_items]
        ]
        if len(communication_agents) > max_items:
            lines.append(f"- ... {len(communication_agents) - max_items} more message targets omitted")
        return "Allowed send_message targets:\n" + "\n".join(lines)

    def _build_resource_section(self, resources: list[dict[str, Any]], detail_level: str) -> str:
        if not resources:
            return "Known resources:\n- none"
        max_items = 28 if detail_level == "standard" else 16 if detail_level == "compact" else 8
        lines = [
            f"- id={resource['resource_id']} type={resource['type']} endpoint={self._shorten_endpoint(resource.get('endpoint'))}"
            for resource in resources[:max_items]
        ]
        if len(resources) > max_items:
            lines.append(f"- ... {len(resources) - max_items} more resources omitted")
        resource_types = ", ".join(resource_type.value for resource_type in ResourceType)
        return f"Allowed resource types: {resource_types}\nKnown resources:\n" + "\n".join(lines)

    def _build_memory_section(self, memory_systems: list[dict[str, Any]], detail_level: str) -> str:
        if not memory_systems:
            return "Known memory systems:\n- none"
        max_items = 24 if detail_level == "standard" else 14 if detail_level == "compact" else 8
        lines = [
            f"- {memory_system['memory_id']} ({memory_system['type']})"
            for memory_system in memory_systems[:max_items]
        ]
        if len(memory_systems) > max_items:
            lines.append(f"- ... {len(memory_systems) - max_items} more memory systems omitted")
        return "Known memory systems:\n" + "\n".join(lines)

    def _build_current_flow_section(
        self,
        current_flow: dict[str, Any] | None,
        detail_level: str,
    ) -> str:
        if current_flow is None:
            return "Current flow context:\n- none"
        nodes = current_flow.get("nodes", []) if isinstance(current_flow, dict) else []
        edges = current_flow.get("edges", []) if isinstance(current_flow, dict) else []
        summary_lines = [
            f"- existing nodes: {len(nodes) if isinstance(nodes, list) else 0}",
            f"- existing edges: {len(edges) if isinstance(edges, list) else 0}",
        ]
        if isinstance(nodes, list) and nodes:
            listed_ids = [
                str(node.get("node_id") or node.get("id") or "").strip()
                for node in nodes[:10]
                if isinstance(node, dict)
            ]
            listed_ids = [node_id for node_id in listed_ids if node_id]
            if listed_ids:
                summary_lines.append(f"- node ids: {', '.join(listed_ids)}")
            if len(nodes) > 10:
                summary_lines.append(f"- ... {len(nodes) - 10} more existing nodes omitted")
        if detail_level == "standard":
            preview_payload, _ = self._sanitize_json_compatible(current_flow)
            preview = self._truncate_text(
                json.dumps(preview_payload, ensure_ascii=False, separators=(",", ":")),
                1_200,
            )
            summary_lines.append(f"- preview: {preview}")
        return "Current flow context:\n" + "\n".join(summary_lines)

    @staticmethod
    def _shorten_endpoint(raw_value: Any) -> str:
        endpoint = str(raw_value or "").strip()
        if len(endpoint) <= 72:
            return endpoint or "n/a"
        return endpoint[:69] + "..."

    @staticmethod
    def _truncate_text(value: str, max_chars: int) -> str:
        if len(value) <= max_chars:
            return value
        if max_chars <= 3:
            return value[:max_chars]
        return value[: max_chars - 3].rstrip() + "..."

    @staticmethod
    def _extract_explanation(parsed: dict[str, Any]) -> str | None:
        explanation = parsed.get("explanation")
        return explanation if isinstance(explanation, str) and explanation.strip() else None

    def _resolve_handler_name(
        self,
        *,
        raw_node: dict[str, Any],
        handler_set: set[str],
        agent_name_to_id: dict[str, int],
        node_id: str,
        warnings: list[str],
    ) -> str:
        raw_handler_name = str(raw_node.get("handler_name", "")).strip()
        if raw_handler_name in handler_set:
            return raw_handler_name
        alias_map = {
            "filesystem_read": "read_file",
            "file_read": "read_file",
            "filesystem_load": "read_file",
            "filesystem_write": "write_file",
            "file_write": "write_file",
            "filesystem_save": "write_file",
            "security_audit": "local_llm_text",
            "vulnerability_scan": "local_llm_text",
            "code_audit": "local_llm_text",
        }
        alias_target = alias_map.get(raw_handler_name.casefold())
        if alias_target in handler_set:
            warnings.append(
                f"Planner selected alias handler '{raw_handler_name}' for node '{node_id}'; normalized it to '{alias_target}'"
            )
            return alias_target

        fallback = self._infer_handler_name(raw_node, handler_set)
        if fallback is not None:
            if raw_handler_name.casefold() in agent_name_to_id:
                warnings.append(
                    f"Planner selected agent name '{raw_handler_name}' as handler for node '{node_id}'; replaced it with '{fallback}'"
                )
            else:
                warnings.append(
                    f"Planner selected unsupported handler '{raw_handler_name}' for node '{node_id}'; replaced it with '{fallback}'"
                )
            return fallback

        raise ValueError(
            f"Planner selected unsupported handler '{raw_handler_name}' for node '{node_id}'"
        )

    @staticmethod
    def _infer_handler_name(raw_node: dict[str, Any], handler_set: set[str]) -> str | None:
        text_parts = [
            str(raw_node.get("handler_name", "")),
            str(raw_node.get("node_id", "")),
            str(raw_node.get("title", "")),
            str(raw_node.get("label", "")),
            json.dumps(
                LiteRTPlanner._sanitize_json_compatible(raw_node.get("input", {}))[0],
                ensure_ascii=False,
                sort_keys=True,
            ),
        ]
        text = " ".join(part for part in text_parts if part).casefold()

        def has_any(*tokens: str) -> bool:
            return any(token in text for token in tokens)

        if "write_csv" in handler_set and has_any("csv", ".csv", "comma separated"):
            return "write_csv"
        if "local_llm_text" in handler_set and has_any(
            "security",
            "audit",
            "vulnerab",
            "scan",
            "review",
            "logic flaw",
            "logic-flaw",
            "injection",
            "typescript",
            "javascript",
            "code analysis",
            "static analysis",
        ):
            return "local_llm_text"
        if "filesystem_read" in handler_set and has_any("filesystem_read"):
            return "filesystem_read"
        if "read_file" in handler_set and has_any("read file", "load file", "ingest file", "local file"):
            return "read_file"
        if "filesystem_write" in handler_set and has_any("filesystem_write"):
            return "filesystem_write"
        if "topic_split" in handler_set and has_any(
            "topic",
            "theme",
            "thema",
            "split",
            "triage",
            "route",
            "classif",
            "filter",
            "separate",
            "segment",
        ):
            return "topic_split"
        if "news_search" in handler_set and has_any(
            "news",
            "nachricht",
            "headline",
            "artikel",
            "article",
            "rss",
            "web search",
            "internet",
            "robotik",
            "ki",
            "ai",
        ):
            return "news_search"
        if "generate_embedding" in handler_set and has_any(
            "embedding",
            "embed",
            "vector",
            "vectorize",
            "vektor",
        ):
            return "generate_embedding"
        if "memory_store" in handler_set and has_any("memory", "speicher", "cache", "store", "persist"):
            return "memory_store"
        if "send_message" in handler_set and has_any("message", "notify", "notification", "alert", "send"):
            return "send_message"
        if "json_serialize" in handler_set and has_any("json", "serialize", "serialis"):
            return "json_serialize"
        if "write_file" in handler_set and has_any("write", "save", "file", "datei"):
            return "write_file"
        if "merge_payloads" in handler_set and has_any("merge", "combine", "payload"):
            return "merge_payloads"
        if "template_render" in handler_set and has_any("render", "template", "format"):
            return "template_render"
        if "http_request" in handler_set and has_any("http", "api", "fetch", "request", "url"):
            return "http_request"
        return None

    @staticmethod
    def _infer_topic_labels(text: str) -> list[str]:
        normalized = text.casefold()
        labels: list[str] = []
        if "robotik" in normalized or "robotics" in normalized or "roboter" in normalized:
            labels.append("Robotik")
        if (
            " ki" in f" {normalized}"
            or "ai" in normalized
            or "artificial intelligence" in normalized
            or "künstliche intelligenz" in normalized
            or "kuenstliche intelligenz" in normalized
        ):
            labels.append("KI")
        seen: set[str] = set()
        deduped: list[str] = []
        for label in labels:
            if label not in seen:
                seen.add(label)
                deduped.append(label)
        return deduped

    def _parse_model_output(self, raw_response: str) -> dict[str, Any]:
        parsed, _ = self._parse_model_output_with_warnings(raw_response)
        return parsed

    def _parse_model_output_with_warnings(self, raw_response: str) -> tuple[dict[str, Any], list[str]]:
        warnings: list[str] = []
        candidates = self._extract_json_candidates(raw_response)
        parse_errors: list[str] = []
        for candidate in candidates:
            parsed, parse_warning = self._try_parse_candidate(candidate)
            if parsed is None:
                parse_errors.append(parse_warning)
                continue
            if parse_warning:
                warnings.append(parse_warning)
            return parsed, warnings

        detail = parse_errors[0] if parse_errors else "unknown parse failure"
        raise ValueError(f"Planner returned invalid JSON: {detail}")

    def _extract_json_candidates(self, raw_response: str) -> list[str]:
        candidates: list[str] = []
        seen: set[str] = set()

        def add_candidate(value: str | None) -> None:
            if value is None:
                return
            normalized = value.strip()
            if not normalized or normalized in seen:
                return
            seen.add(normalized)
            candidates.append(normalized)

        fenced_matches = re.findall(r"```(?:json)?\s*(.*?)```", raw_response, flags=re.DOTALL | re.IGNORECASE)
        for match in fenced_matches:
            add_candidate(match)

        try:
            add_candidate(self._extract_json_object(raw_response))
        except ValueError:
            try:
                add_candidate(self._extract_json_object(raw_response, allow_incomplete=True))
            except ValueError:
                pass

        add_candidate(raw_response)
        return candidates

    def _try_parse_candidate(self, candidate: str) -> tuple[dict[str, Any] | None, str]:
        prepared = self._prepare_json_candidate(candidate)
        direct_error = ""
        try:
            parsed = json.loads(prepared)
        except json.JSONDecodeError as exc:
            direct_error = str(exc)
        else:
            if isinstance(parsed, dict):
                return parsed, ""
            return None, "Planner output must be a JSON object"

        repaired = self._repair_json_text(prepared)
        if repaired != prepared:
            try:
                parsed = json.loads(repaired)
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(parsed, dict):
                    return parsed, "Planner JSON was auto-repaired before normalization."
                return None, "Planner output must be a JSON object"

        python_like = self._repair_python_literal_text(prepared)
        try:
            parsed_literal = ast.literal_eval(python_like)
        except (SyntaxError, ValueError) as exc:
            return None, direct_error or str(exc)
        if not isinstance(parsed_literal, dict):
            return None, "Planner output must be a JSON object"
        sanitized_literal, replaced_unsupported_values = self._sanitize_json_compatible(parsed_literal)
        repaired_payload = json.loads(json.dumps(sanitized_literal, ensure_ascii=False))
        warning = "Planner JSON used a tolerant literal-repair path before normalization."
        if replaced_unsupported_values:
            warning += " Unsupported placeholder values were replaced with null."
        return repaired_payload, warning

    @staticmethod
    def _extract_json_object(text: str, allow_incomplete: bool = False) -> str:
        start = text.find("{")
        if start < 0:
            raise ValueError("Planner response does not contain a JSON object")

        depth = 0
        in_string = False
        escaped = False
        quote_char = ""
        for index in range(start, len(text)):
            character = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote_char:
                    in_string = False
                continue
            if character in {'"', "'"}:
                in_string = True
                quote_char = character
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]
        if allow_incomplete:
            return text[start:]
        raise ValueError("Planner response contains an incomplete JSON object")

    @staticmethod
    def _prepare_json_candidate(candidate: str) -> str:
        cleaned = candidate.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.replace("\ufeff", "")
        quote_map = str.maketrans(
            {
                "“": '"',
                "”": '"',
                "„": '"',
                "‟": '"',
                "’": "'",
                "‘": "'",
                "‚": "'",
                "‛": "'",
            }
        )
        cleaned = cleaned.translate(quote_map)
        cleaned = "".join(character for character in cleaned if character >= " " or character in "\n\r\t")
        return cleaned.strip()

    @staticmethod
    def _sanitize_json_compatible(value: Any) -> tuple[Any, bool]:
        if value is Ellipsis:
            return None, True
        if value is None or isinstance(value, (str, int, float, bool)):
            return value, False
        if isinstance(value, dict):
            changed = False
            sanitized: dict[str, Any] = {}
            for key, entry in value.items():
                sanitized_entry, entry_changed = LiteRTPlanner._sanitize_json_compatible(entry)
                sanitized[str(key)] = sanitized_entry
                changed = changed or entry_changed or not isinstance(key, str)
            return sanitized, changed
        if isinstance(value, (list, tuple, set)):
            changed = not isinstance(value, list)
            sanitized_items: list[Any] = []
            for entry in value:
                sanitized_entry, entry_changed = LiteRTPlanner._sanitize_json_compatible(entry)
                sanitized_items.append(sanitized_entry)
                changed = changed or entry_changed
            return sanitized_items, changed
        return str(value), True

    def _repair_json_text(self, candidate: str) -> str:
        repaired = candidate
        repaired = self._remove_json_comments(repaired)
        repaired = self._quote_bare_object_keys(repaired)
        repaired = self._convert_single_quoted_strings_to_json_strings(repaired)
        repaired = self._replace_keyword_literals(
            repaired,
            {
                "True": "true",
                "False": "false",
                "None": "null",
            },
        )
        repaired = self._insert_missing_object_commas(repaired)
        repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)
        repaired = self._balance_json_structure(repaired)
        return repaired

    def _repair_python_literal_text(self, candidate: str) -> str:
        repaired = candidate
        repaired = self._remove_json_comments(repaired)
        repaired = self._quote_bare_object_keys(repaired)
        repaired = self._replace_keyword_literals(
            repaired,
            {
                "true": "True",
                "false": "False",
                "null": "None",
            },
        )
        repaired = self._balance_json_structure(repaired)
        return repaired

    @staticmethod
    def _remove_json_comments(candidate: str) -> str:
        without_block_comments = re.sub(r"/\*.*?\*/", "", candidate, flags=re.DOTALL)
        return re.sub(r"(^|[ \t])//.*?$", r"\1", without_block_comments, flags=re.MULTILINE)

    @staticmethod
    def _quote_bare_object_keys(candidate: str) -> str:
        key_pattern = re.compile(r'([{\[,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)(\s*:)')
        previous = None
        current = candidate
        while current != previous:
            previous = current
            current = key_pattern.sub(r'\1"\2"\3', current)
        return current

    @staticmethod
    def _replace_keyword_literals(candidate: str, replacements: dict[str, str]) -> str:
        result: list[str] = []
        token: list[str] = []
        in_string = False
        escaped = False
        quote_char = ""

        def flush_token() -> None:
            if not token:
                return
            value = "".join(token)
            result.append(replacements.get(value, value))
            token.clear()

        for character in candidate:
            if in_string:
                result.append(character)
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote_char:
                    in_string = False
                continue

            if character in {'"', "'"}:
                flush_token()
                in_string = True
                quote_char = character
                result.append(character)
                continue

            if character.isalnum() or character == "_":
                token.append(character)
                continue

            flush_token()
            result.append(character)

        flush_token()
        return "".join(result)

    @staticmethod
    def _balance_json_structure(candidate: str) -> str:
        closers: list[str] = []
        result = candidate.rstrip()
        in_string = False
        escaped = False
        quote_char = ""

        for character in result:
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote_char:
                    in_string = False
                continue

            if character in {'"', "'"}:
                in_string = True
                quote_char = character
            elif character == "{":
                closers.append("}")
            elif character == "[":
                closers.append("]")
            elif character in {"}", "]"} and closers and closers[-1] == character:
                closers.pop()

        if in_string:
            result += quote_char
        if closers:
            result += "".join(reversed(closers))
        return result

    @staticmethod
    def _convert_single_quoted_strings_to_json_strings(candidate: str) -> str:
        result: list[str] = []
        in_double = False
        in_single = False
        escaped = False
        single_buffer: list[str] = []

        for character in candidate:
            if in_double:
                result.append(character)
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_double = False
                continue

            if in_single:
                if escaped:
                    single_buffer.append(character)
                    escaped = False
                    continue
                if character == "\\":
                    escaped = True
                    single_buffer.append(character)
                    continue
                if character == "'":
                    decoded = bytes("".join(single_buffer), "utf-8").decode("unicode_escape")
                    result.append(json.dumps(decoded, ensure_ascii=False))
                    single_buffer.clear()
                    in_single = False
                    continue
                single_buffer.append(character)
                continue

            if character == '"':
                in_double = True
                result.append(character)
                continue
            if character == "'":
                in_single = True
                single_buffer.clear()
                escaped = False
                continue
            result.append(character)

        if in_single:
            decoded = bytes("".join(single_buffer), "utf-8").decode("unicode_escape")
            result.append(json.dumps(decoded, ensure_ascii=False))
        return "".join(result)

    @staticmethod
    def _insert_missing_object_commas(candidate: str) -> str:
        result: list[str] = []
        stack: list[str] = []
        in_string = False
        escaped = False
        quote_char = ""

        def previous_significant() -> str:
            for item in reversed(result):
                if not item.isspace():
                    return item
            return ""

        def next_significant(index: int) -> str:
            for item in candidate[index + 1 :]:
                if not item.isspace():
                    return item
            return ""

        for index, character in enumerate(candidate):
            if in_string:
                result.append(character)
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote_char:
                    in_string = False
                continue

            if character in {'"', "'"}:
                in_string = True
                quote_char = character
                result.append(character)
                continue

            if character == "{":
                stack.append("{")
                result.append(character)
                continue
            if character == "[":
                stack.append("[")
                result.append(character)
                continue
            if character in {"}", "]"}:
                if stack and ((character == "}" and stack[-1] == "{") or (character == "]" and stack[-1] == "[")):
                    stack.pop()
                result.append(character)
                continue

            if character == "\n":
                prev_sig = previous_significant()
                next_sig = next_significant(index)
                if (
                    stack
                    and stack[-1] == "{"
                    and prev_sig
                    and prev_sig not in "{[:,"
                    and next_sig
                    and next_sig not in "}]"
                    and (next_sig.isalpha() or next_sig in {'"', "'","_"})
                ):
                    result.append(",")
                result.append(character)
                continue

            result.append(character)

        return "".join(result)

    def _normalize_flow_request(
        self,
        parsed: dict[str, Any],
        catalog: PlannerCatalog,
        max_nodes: int,
    ) -> tuple[dict[str, Any], list[str]]:
        warnings: list[str] = []
        raw_nodes = parsed.get("nodes")
        raw_edges = parsed.get("edges", [])
        if not isinstance(raw_nodes, list) or not raw_nodes:
            raise ValueError("Planner response must contain a non-empty 'nodes' array")

        handler_set = set(catalog.handlers)
        valid_resource_ids = {int(resource["resource_id"]) for resource in catalog.resources}
        agent_name_to_id = {
            str(agent["name"]).casefold(): int(agent["agent_id"]) for agent in catalog.agents
        }
        memory_ids = [str(system["memory_id"]) for system in catalog.memory_systems]
        comm_agent_ids = {
            int(agent["agent_id"])
            for agent in catalog.agents
            if isinstance(agent.get("communication"), dict)
        }
        communication_agents = {
            str(agent["name"]).casefold(): int(agent["agent_id"])
            for agent in catalog.agents
            if isinstance(agent.get("communication"), dict)
        }

        normalized_nodes: list[dict[str, Any]] = []
        omitted_nodes: dict[str, str] = {}
        node_ids: set[str] = set()
        resolved_handlers_by_node_id: dict[str, str] = {}
        for index, raw_node in enumerate(raw_nodes[:max_nodes], start=1):
            if not isinstance(raw_node, dict):
                raise ValueError(f"Planner node at index {index} is not an object")
            node_id = self._normalize_node_id(raw_node.get("node_id") or raw_node.get("id") or f"task-{index}")
            if node_id in node_ids:
                node_id = f"{node_id}-{index}"
            node_ids.add(node_id)

            handler_name = self._resolve_handler_name(
                raw_node=raw_node,
                handler_set=handler_set,
                agent_name_to_id=agent_name_to_id,
                node_id=node_id,
                warnings=warnings,
            )

            preferred_agent_id = None
            raw_agent_name = raw_node.get("preferred_agent_name")
            if isinstance(raw_agent_name, str) and raw_agent_name.strip():
                preferred_agent_id = agent_name_to_id.get(raw_agent_name.casefold())
                if preferred_agent_id is None:
                    warnings.append(
                        f"Unknown preferred_agent_name '{raw_agent_name}' ignored for node '{node_id}'"
                    )
            elif str(raw_node.get("handler_name", "")).strip().casefold() in agent_name_to_id:
                preferred_agent_id = agent_name_to_id[str(raw_node.get("handler_name", "")).strip().casefold()]
                warnings.append(
                    f"Node '{node_id}' reused agent name '{raw_node.get('handler_name')}' as preferred_agent_name after handler repair"
                )

            raw_resource_ids = raw_node.get("required_resource_ids", [])
            resource_ids = []
            if isinstance(raw_resource_ids, list):
                for resource_id in raw_resource_ids:
                    try:
                        numeric_id = int(resource_id)
                    except (TypeError, ValueError):
                        warnings.append(f"Invalid resource id '{resource_id}' ignored for node '{node_id}'")
                        continue
                    if numeric_id in valid_resource_ids:
                        resource_ids.append(numeric_id)
                    else:
                        warnings.append(
                            f"Unknown resource id '{numeric_id}' ignored for node '{node_id}'"
                        )

            resource_types = []
            for raw_type in raw_node.get("required_resource_types", []) or []:
                try:
                    resource_types.append(ResourceType(str(raw_type)).value)
                except ValueError:
                    warnings.append(
                        f"Unknown resource type '{raw_type}' ignored for node '{node_id}'"
                    )

            rollback_strategy = str(
                raw_node.get("rollback_strategy", RollbackStrategy.FAIL_FAST.value)
            )
            if rollback_strategy not in {strategy.value for strategy in RollbackStrategy}:
                warnings.append(
                    f"Unknown rollback strategy '{rollback_strategy}' replaced with FAIL_FAST for node '{node_id}'"
                )
                rollback_strategy = RollbackStrategy.FAIL_FAST.value

            retry_policy = self._normalize_retry_policy(raw_node.get("retry_policy"))
            title = str(raw_node.get("title") or raw_node.get("label") or handler_name).strip()
            metadata = self._normalize_object(raw_node.get("metadata"))
            metadata.setdefault("ui", {})
            if isinstance(metadata["ui"], dict):
                metadata["ui"].setdefault("title", title)

            input_payload = raw_node.get("input", {})
            if not isinstance(input_payload, dict):
                input_payload = {}
            input_payload, omission_reason = self._normalize_handler_input(
                handler_name=handler_name,
                input_payload=dict(input_payload),
                node_id=node_id,
                title=title,
                dependencies=self._normalize_string_list(raw_node.get("dependencies")),
                resolved_handlers_by_node_id=resolved_handlers_by_node_id,
                memory_ids=memory_ids,
                comm_agent_ids=comm_agent_ids,
                communication_agents=communication_agents,
                warnings=warnings,
            )
            if omission_reason is not None:
                omitted_nodes[node_id] = omission_reason
                warnings.append(omission_reason)
                continue

            normalized_nodes.append(
                {
                    "node_id": node_id,
                    "handler_name": handler_name,
                    "input": input_payload,
                    "required_capabilities": self._normalize_string_list(
                        raw_node.get("required_capabilities")
                    ),
                    "required_resource_ids": resource_ids,
                    "required_resource_types": resource_types,
                    "retry_policy": retry_policy,
                    "rollback_strategy": rollback_strategy,
                    "validator_rules": self._normalize_object(raw_node.get("validator_rules")),
                    "metadata": metadata,
                    "requires_manual_approval": bool(raw_node.get("requires_manual_approval", False)),
                    "manual_approval": self._normalize_object(raw_node.get("manual_approval")),
                    "compensation_handler": self._normalize_compensation_handler(
                        raw_node.get("compensation_handler"),
                        handler_set,
                        warnings,
                        node_id,
                    ),
                    "dependencies": self._normalize_string_list(raw_node.get("dependencies")),
                    "conditions": self._normalize_conditions(raw_node.get("conditions")),
                    "preferred_agent_id": preferred_agent_id,
                }
            )
            resolved_handlers_by_node_id[node_id] = handler_name

        normalized_edges = self._normalize_edges(raw_edges, node_ids, warnings)
        if omitted_nodes:
            normalized_edges = self._omit_nodes_from_edges(
                normalized_edges,
                omitted_nodes,
                warnings,
            )
            self._strip_omitted_dependencies(normalized_nodes, set(omitted_nodes))
        self._merge_dependencies(normalized_nodes, normalized_edges)
        self._postprocess_write_csv_nodes(normalized_nodes, warnings)
        if not normalized_nodes:
            raise ValueError("Planner produced no executable nodes after normalization")
        self._validate_acyclic(normalized_nodes)

        if len(raw_nodes) > max_nodes:
            warnings.append(f"Planner returned {len(raw_nodes)} nodes; truncated to {max_nodes}")

        return {
            "nodes": normalized_nodes,
            "edges": normalized_edges,
        }, warnings

    @staticmethod
    def _normalize_node_id(raw_value: Any) -> str:
        base = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(raw_value).strip()).strip("-")
        return base or "task"

    @staticmethod
    def _normalize_object(raw_value: Any) -> dict[str, Any]:
        return raw_value if isinstance(raw_value, dict) else {}

    @staticmethod
    def _normalize_string_list(raw_value: Any) -> list[str]:
        if not isinstance(raw_value, list):
            return []
        return [str(item).strip() for item in raw_value if str(item).strip()]

    @staticmethod
    def _normalize_conditions(raw_value: Any) -> dict[str, str]:
        if not isinstance(raw_value, dict):
            return {}
        return {
            str(key): str(value)
            for key, value in raw_value.items()
            if str(key).strip() and str(value).strip()
        }

    @staticmethod
    def _normalize_retry_policy(raw_value: Any) -> dict[str, Any]:
        if not isinstance(raw_value, dict):
            return dict(DEFAULT_RETRY_POLICY)
        policy = dict(DEFAULT_RETRY_POLICY)
        for key in policy:
            if key in raw_value:
                policy[key] = raw_value[key]
        policy["max_retries"] = int(policy["max_retries"])
        policy["backoff_ms"] = int(policy["backoff_ms"])
        policy["exponential"] = bool(policy["exponential"])
        policy["max_backoff_ms"] = int(policy["max_backoff_ms"])
        policy["jitter_ratio"] = float(policy["jitter_ratio"])
        return policy

    @staticmethod
    def _normalize_compensation_handler(
        raw_value: Any,
        allowed_handlers: set[str],
        warnings: list[str],
        node_id: str,
    ) -> str | None:
        if raw_value is None:
            return None
        handler_name = str(raw_value).strip()
        if not handler_name:
            return None
        if handler_name not in allowed_handlers:
            warnings.append(
                f"Unknown compensation handler '{handler_name}' ignored for node '{node_id}'"
            )
            return None
        return handler_name

    @staticmethod
    def _normalize_edges(
        raw_edges: Any,
        node_ids: set[str],
        warnings: list[str],
    ) -> list[dict[str, str]]:
        if raw_edges is None:
            return []
        if not isinstance(raw_edges, list):
            raise ValueError("Planner response field 'edges' must be an array")

        normalized: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for raw_edge in raw_edges:
            if not isinstance(raw_edge, dict):
                continue
            source = str(raw_edge.get("from_node") or raw_edge.get("source") or "").strip()
            target = str(raw_edge.get("to_node") or raw_edge.get("target") or "").strip()
            if source not in node_ids or target not in node_ids:
                warnings.append(
                    f"Edge '{source}' -> '{target}' ignored because it references unknown nodes"
                )
                continue
            if source == target:
                warnings.append(f"Self-edge on '{source}' ignored")
                continue
            key = (source, target)
            if key in seen:
                continue
            seen.add(key)
            normalized.append(
                {
                    "from_node": source,
                    "to_node": target,
                    "condition": str(raw_edge.get("condition") or raw_edge.get("label") or "True"),
                }
            )
        return normalized

    @staticmethod
    def _merge_dependencies(
        normalized_nodes: list[dict[str, Any]],
        normalized_edges: list[dict[str, str]],
    ) -> None:
        node_index = {node["node_id"]: node for node in normalized_nodes}
        for edge in normalized_edges:
            target_node = node_index[edge["to_node"]]
            if edge["from_node"] not in target_node["dependencies"]:
                target_node["dependencies"].append(edge["from_node"])
            target_node["conditions"].setdefault(edge["from_node"], edge["condition"])

    @classmethod
    def _postprocess_write_csv_nodes(
        cls,
        normalized_nodes: list[dict[str, Any]],
        warnings: list[str],
    ) -> None:
        if not normalized_nodes:
            return
        node_index = {node["node_id"]: node for node in normalized_nodes}
        expected_fieldnames = ["topic", "title", "source", "published_at", "link", "summary"]
        for node in normalized_nodes:
            if node.get("handler_name") != "write_csv":
                continue
            topic_split_node_id = cls._find_upstream_handler_node_id(
                start_node_id=node["node_id"],
                expected_handler="topic_split",
                node_index=node_index,
            )
            if topic_split_node_id is None:
                continue
            input_payload = node.get("input")
            if not isinstance(input_payload, dict):
                continue
            expected_rows_ref = {"$ref": f"results['{topic_split_node_id}']['csv_rows']"}
            if not cls._is_topic_split_csv_rows_reference(input_payload.get("rows"), topic_split_node_id):
                input_payload["rows"] = expected_rows_ref
                warnings.append(
                    f"write_csv node '{node['node_id']}' rewired rows to upstream topic_split '{topic_split_node_id}.csv_rows' for news export"
                )
            normalized_fieldnames, fieldnames_warning = cls._normalize_topic_split_csv_fieldnames(
                input_payload.get("fieldnames"),
                node_id=str(node["node_id"]),
            )
            if normalized_fieldnames is None:
                input_payload["fieldnames"] = expected_fieldnames
                warnings.append(
                    f"write_csv node '{node['node_id']}' set explicit topic_split CSV fieldnames for deterministic news export"
                )
            else:
                input_payload["fieldnames"] = normalized_fieldnames
            if fieldnames_warning:
                warnings.append(fieldnames_warning)

    @classmethod
    def _find_upstream_handler_node_id(
        cls,
        *,
        start_node_id: str,
        expected_handler: str,
        node_index: dict[str, dict[str, Any]],
    ) -> str | None:
        visited: set[str] = set()
        queue: list[str] = list(node_index.get(start_node_id, {}).get("dependencies", []))
        while queue:
            candidate_id = queue.pop(0)
            if candidate_id in visited:
                continue
            visited.add(candidate_id)
            candidate_node = node_index.get(candidate_id)
            if not candidate_node:
                continue
            if candidate_node.get("handler_name") == expected_handler:
                return candidate_id
            queue.extend(
                dependency
                for dependency in candidate_node.get("dependencies", [])
                if dependency not in visited
            )
        return None

    @staticmethod
    def _is_topic_split_csv_rows_reference(raw_value: Any, topic_split_node_id: str) -> bool:
        canonical = f"results['{topic_split_node_id}']['csv_rows']"
        if isinstance(raw_value, dict):
            raw_ref = raw_value.get("$ref")
            return isinstance(raw_ref, str) and raw_ref.replace('"', "'").strip() == canonical
        if isinstance(raw_value, str):
            return raw_value.replace('"', "'").strip() == canonical
        return False

    @staticmethod
    def _validate_acyclic(normalized_nodes: list[dict[str, Any]]) -> None:
        adjacency: dict[str, list[str]] = {node["node_id"]: [] for node in normalized_nodes}
        indegree: dict[str, int] = {node["node_id"]: 0 for node in normalized_nodes}

        for node in normalized_nodes:
            for dependency in node["dependencies"]:
                if dependency not in adjacency:
                    continue
                adjacency[dependency].append(node["node_id"])
                indegree[node["node_id"]] += 1

        queue = [node_id for node_id, degree in indegree.items() if degree == 0]
        visited = 0
        while queue:
            node_id = queue.pop(0)
            visited += 1
            for target in adjacency[node_id]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)

        if visited != len(normalized_nodes):
            raise ValueError("Planner produced a cyclic dependency graph; only DAG flows are supported")

    @staticmethod
    def _combine_edge_conditions(left: str, right: str) -> str:
        normalized_left = str(left or "True").strip() or "True"
        normalized_right = str(right or "True").strip() or "True"
        if normalized_left == "True":
            return normalized_right
        if normalized_right == "True":
            return normalized_left
        if normalized_left == normalized_right:
            return normalized_left
        return f"({normalized_left}) and ({normalized_right})"

    @classmethod
    def _omit_nodes_from_edges(
        cls,
        normalized_edges: list[dict[str, str]],
        omitted_nodes: dict[str, str],
        warnings: list[str],
    ) -> list[dict[str, str]]:
        if not omitted_nodes:
            return normalized_edges

        omitted_node_ids = set(omitted_nodes)
        incoming: dict[str, list[dict[str, str]]] = {}
        outgoing: dict[str, list[dict[str, str]]] = {}
        for edge in normalized_edges:
            outgoing.setdefault(edge["from_node"], []).append(edge)
            incoming.setdefault(edge["to_node"], []).append(edge)

        rewired_edges: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()

        def append_edge(source: str, target: str, condition: str) -> bool:
            if source in omitted_node_ids or target in omitted_node_ids or source == target:
                return False
            key = (source, target)
            if key in seen:
                return False
            seen.add(key)
            rewired_edges.append(
                {
                    "from_node": source,
                    "to_node": target,
                    "condition": condition,
                }
            )
            return True

        for edge in normalized_edges:
            if edge["from_node"] in omitted_node_ids or edge["to_node"] in omitted_node_ids:
                continue
            append_edge(edge["from_node"], edge["to_node"], edge["condition"])

        for omitted_node_id, omission_reason in omitted_nodes.items():
            incoming_edges = incoming.get(omitted_node_id, [])
            outgoing_edges = outgoing.get(omitted_node_id, [])
            rewired_count = 0
            for incoming_edge in incoming_edges:
                for outgoing_edge in outgoing_edges:
                    combined_condition = cls._combine_edge_conditions(
                        incoming_edge["condition"],
                        outgoing_edge["condition"],
                    )
                    if append_edge(
                        incoming_edge["from_node"],
                        outgoing_edge["to_node"],
                        combined_condition,
                    ):
                        rewired_count += 1
            if rewired_count:
                warnings.append(
                    f"{omission_reason}; rewired {rewired_count} edge(s) around omitted node '{omitted_node_id}'"
                )

        return rewired_edges

    @staticmethod
    def _strip_omitted_dependencies(
        normalized_nodes: list[dict[str, Any]],
        omitted_node_ids: set[str],
    ) -> None:
        if not omitted_node_ids:
            return
        for node in normalized_nodes:
            node["dependencies"] = [
                dependency
                for dependency in node["dependencies"]
                if dependency not in omitted_node_ids
            ]
            for omitted_node_id in omitted_node_ids:
                node["conditions"].pop(omitted_node_id, None)

    @staticmethod
    def _normalize_handler_input(
        handler_name: str,
        input_payload: dict[str, Any],
        node_id: str,
        title: str,
        dependencies: list[str],
        resolved_handlers_by_node_id: dict[str, str],
        memory_ids: list[str],
        comm_agent_ids: set[int],
        communication_agents: dict[str, int],
        warnings: list[str],
    ) -> tuple[dict[str, Any] | None, str | None]:
        upstream_reference = (
            {"$ref": f"results['{dependencies[-1]}']"} if dependencies else {}
        )
        upstream_handler_name = (
            resolved_handlers_by_node_id.get(dependencies[-1]) if dependencies else None
        )

        if handler_name == "memory_store":
            if "memory_id" not in input_payload and memory_ids:
                input_payload["memory_id"] = memory_ids[0]
                warnings.append(
                    f"memory_store node '{node_id}' had no memory_id; defaulted to '{memory_ids[0]}'"
                )
            if "key" not in input_payload:
                input_payload["key"] = f"{node_id}-result"
                warnings.append(
                    f"memory_store node '{node_id}' had no key; defaulted to '{node_id}-result'"
                )
            if "value" not in input_payload:
                if "data" in input_payload:
                    input_payload["value"] = input_payload.pop("data")
                    warnings.append(
                        f"memory_store node '{node_id}' used 'data'; remapped to 'value'"
                    )
                elif dependencies:
                    input_payload["value"] = upstream_reference
                else:
                    input_payload["value"] = upstream_reference
                    warnings.append(
                        f"memory_store node '{node_id}' had no value; defaulted to upstream result reference"
                    )
            elif dependencies:
                normalized_value, value_warning = LiteRTPlanner._normalize_upstream_result_input(
                    raw_value=input_payload.get("value"),
                    dependency_node_id=dependencies[-1],
                    handler_name=handler_name,
                    node_id=node_id,
                    input_key="value",
                )
                input_payload["value"] = normalized_value
                if value_warning:
                    warnings.append(value_warning)

        if handler_name == "memory_retrieve":
            if "memory_id" not in input_payload and memory_ids:
                input_payload["memory_id"] = memory_ids[0]
                warnings.append(
                    f"memory_retrieve node '{node_id}' had no memory_id; defaulted to '{memory_ids[0]}'"
                )

        if handler_name == "memory_search":
            if "memory_id" not in input_payload and memory_ids:
                input_payload["memory_id"] = memory_ids[0]
                warnings.append(
                    f"memory_search node '{node_id}' had no memory_id; defaulted to '{memory_ids[0]}'"
                )
            input_payload.setdefault("limit", 5)

        if handler_name == "http_request":
            input_payload.setdefault("method", "GET")

        if handler_name == "news_search":
            input_payload.setdefault("query", "IT Nachrichten")
            input_payload.setdefault("language", "de")
            input_payload.setdefault("country", "DE")
            input_payload.setdefault("time_range", "7d")
            input_payload.setdefault("max_items", 20)

        if handler_name in {"read_file", "filesystem_read"}:
            if "path" not in input_payload:
                for alias in ("file", "filepath", "source_path", "filename"):
                    if alias in input_payload:
                        input_payload["path"] = input_payload.pop(alias)
                        warnings.append(
                            f"{handler_name} node '{node_id}' used '{alias}'; remapped to 'path'"
                        )
                        break

        if handler_name == "local_llm_text":
            if "data" not in input_payload:
                for alias in ("content", "code", "text", "input", "value", "document", "source", "result"):
                    if alias in input_payload:
                        input_payload["data"] = input_payload.pop(alias)
                        warnings.append(
                            f"local_llm_text node '{node_id}' used '{alias}'; remapped to 'data'"
                        )
                        break
            title_context = f"{node_id} {title}".casefold()
            if "prompt" not in input_payload and "instruction" not in input_payload:
                if any(token in title_context for token in ("format", "summary", "report", "structured")):
                    default_instruction = (
                        "Convert the provided findings into a finished structured technical summary. "
                        "Do not ask for more input."
                    )
                elif any(token in title_context for token in ("audit", "security", "vulnerab", "scan", "review")):
                    default_instruction = (
                        "Audit the provided source code for security vulnerabilities, injection risks, logic flaws, "
                        "unsafe file operations and privilege escalation paths. Return a concise technical report."
                    )
                else:
                    default_instruction = "Analyze the provided input and return a concise technical result."
                input_payload.setdefault("instruction", default_instruction)
            if dependencies:
                dependency_node_id = dependencies[-1]
                expected_field = None
                if upstream_handler_name in {"read_file", "filesystem_read"}:
                    expected_field = "content"
                elif upstream_handler_name == "local_llm_text":
                    expected_field = "text"
                elif upstream_handler_name == "template_render":
                    expected_field = "rendered"
                elif upstream_handler_name == "json_serialize":
                    expected_field = "serialized"

                if "data" not in input_payload:
                    if expected_field is None:
                        input_payload["data"] = upstream_reference
                        warnings.append(
                            f"local_llm_text node '{node_id}' had no data; defaulted to upstream '{dependency_node_id}' result reference"
                        )
                    else:
                        input_payload["data"] = {
                            "$ref": f"results['{dependency_node_id}']['{expected_field}']"
                        }
                        warnings.append(
                            f"local_llm_text node '{node_id}' had no data; defaulted to upstream '{dependency_node_id}.{expected_field}' reference"
                        )
                elif "data" in input_payload and expected_field is not None:
                    normalized_data, data_warning = LiteRTPlanner._normalize_upstream_field_input(
                        raw_value=input_payload.get("data"),
                        dependency_node_id=dependency_node_id,
                        expected_field=expected_field,
                        handler_name=handler_name,
                        node_id=node_id,
                        input_key="data",
                    )
                    input_payload["data"] = normalized_data
                    if data_warning:
                        warnings.append(data_warning)
                elif "data" in input_payload:
                    normalized_data, data_warning = LiteRTPlanner._normalize_upstream_result_input(
                        raw_value=input_payload.get("data"),
                        dependency_node_id=dependency_node_id,
                        handler_name=handler_name,
                        node_id=node_id,
                        input_key="data",
                    )
                    input_payload["data"] = normalized_data
                    if data_warning:
                        warnings.append(data_warning)

        if handler_name == "generate_embedding":
            if "data" not in input_payload:
                for alias in ("value", "text", "content", "payload", "input"):
                    if alias in input_payload:
                        input_payload["data"] = input_payload.pop(alias)
                        warnings.append(
                            f"generate_embedding node '{node_id}' used '{alias}'; remapped to 'data'"
                        )
                        break
            if "data" not in input_payload:
                if dependencies:
                    input_payload["data"] = upstream_reference
                else:
                    input_payload["data"] = ""
                    warnings.append(
                        f"generate_embedding node '{node_id}' had no data and no upstream dependency; defaulted to empty text"
                    )
            elif dependencies:
                normalized_data, data_warning = LiteRTPlanner._normalize_upstream_result_input(
                    raw_value=input_payload.get("data"),
                    dependency_node_id=dependencies[-1],
                    handler_name=handler_name,
                    node_id=node_id,
                    input_key="data",
                )
                input_payload["data"] = normalized_data
                if data_warning:
                    warnings.append(data_warning)

        if handler_name == "topic_split":
            if "topics" not in input_payload:
                for alias in ("to", "labels", "categories", "groups"):
                    if alias in input_payload:
                        input_payload["topics"] = input_payload.pop(alias)
                        warnings.append(
                            f"topic_split node '{node_id}' used '{alias}'; remapped to 'topics'"
                        )
                        break
            if "items" not in input_payload:
                if dependencies:
                    input_payload["items"] = {"$ref": f"results['{dependencies[-1]}']['items']"}
                else:
                    input_payload["items"] = []
            elif dependencies:
                normalized_items, items_warning = LiteRTPlanner._normalize_upstream_collection_input(
                    raw_value=input_payload.get("items"),
                    dependency_node_id=dependencies[-1],
                    expected_field="items",
                    handler_name=handler_name,
                    node_id=node_id,
                    input_key="items",
                )
                input_payload["items"] = normalized_items
                if items_warning:
                    warnings.append(items_warning)
            if "topics" not in input_payload:
                inferred_topics = LiteRTPlanner._infer_topic_labels(title)
                if inferred_topics:
                    input_payload["topics"] = inferred_topics
                    warnings.append(
                        f"topic_split node '{node_id}' inferred topics {', '.join(inferred_topics)} from the node title"
                    )
                else:
                    input_payload["topics"] = ["Robotik", "KI"]
                    warnings.append(
                        f"topic_split node '{node_id}' had no topics; defaulted to Robotik and KI"
                    )
            input_payload.setdefault("include_uncategorized", True)

        if handler_name == "send_message":
            if "message" not in input_payload:
                input_payload["message"] = {"text": f"Flow node {node_id} completed."}
                warnings.append(
                    f"send_message node '{node_id}' had no message; inserted default completion message"
                )
            raw_target_id = input_payload.get("target_agent_id")
            if raw_target_id is not None:
                try:
                    numeric_target_id = int(raw_target_id)
                except (TypeError, ValueError):
                    numeric_target_id = None
                else:
                    input_payload["target_agent_id"] = numeric_target_id
                    if numeric_target_id not in comm_agent_ids:
                        if len(comm_agent_ids) == 1:
                            input_payload["target_agent_id"] = next(iter(comm_agent_ids))
                            warnings.append(
                                f"send_message node '{node_id}' referenced non-communication agent '{numeric_target_id}'; defaulted to the only communication-enabled agent"
                            )
                        elif len(comm_agent_ids) == 0:
                            return (
                                None,
                                f"send_message node '{node_id}' was omitted because no communication-enabled target agent is registered",
                            )
            if "target_agent_id" not in input_payload:
                raw_target_name = input_payload.get("target_agent_name")
                if isinstance(raw_target_name, str) and raw_target_name.strip():
                    resolved_agent_id = communication_agents.get(raw_target_name.casefold())
                    if resolved_agent_id is None:
                        if len(communication_agents) == 1:
                            sole_name, sole_id = next(iter(communication_agents.items()))
                            input_payload["target_agent_id"] = sole_id
                            warnings.append(
                                f"send_message node '{node_id}' referenced unknown agent '{raw_target_name}'; defaulted to the only communication-enabled agent '{sole_name}' ({sole_id})"
                            )
                            return input_payload, None
                        if not communication_agents:
                            return (
                                None,
                                f"send_message node '{node_id}' was omitted because no communication-enabled target agent is registered",
                            )
                        allowed_targets = ", ".join(
                            sorted(
                                agent_name for agent_name in communication_agents.keys()
                            )
                        )
                        raise ValueError(
                            f"send_message node '{node_id}' references unknown agent '{raw_target_name}'. Allowed target_agent_name values: {allowed_targets}"
                        )
                    input_payload["target_agent_id"] = resolved_agent_id
                    warnings.append(
                        f"send_message node '{node_id}' resolved target_agent_name '{raw_target_name}' to target_agent_id '{resolved_agent_id}'"
                    )
                    return input_payload, None
                if len(comm_agent_ids) == 1:
                    input_payload["target_agent_id"] = next(iter(comm_agent_ids))
                    warnings.append(
                        f"send_message node '{node_id}' had no target_agent_id; defaulted to the only communication-enabled agent"
                    )
                elif len(comm_agent_ids) == 0:
                    return (
                        None,
                        f"send_message node '{node_id}' was omitted because no communication-enabled target agent is registered",
                    )
                else:
                    raise ValueError(
                        f"send_message node '{node_id}' requires an explicit target_agent_id because multiple communication-enabled agents are registered"
                    )

        if handler_name == "template_render":
            input_payload.setdefault("template", "Task completed: {node_id}")
            input_payload.setdefault("values", {"node_id": node_id})

        if handler_name == "merge_payloads":
            input_payload.setdefault("base", {})
            input_payload.setdefault("updates", [upstream_reference] if dependencies else [{}])

        if handler_name == "json_serialize":
            input_payload.setdefault("value", upstream_reference)
            input_payload.setdefault("indent", 2)

        if handler_name in {"write_file", "filesystem_write"}:
            if "path" not in input_payload:
                for alias in ("file", "filepath", "output_path", "filename"):
                    if alias in input_payload:
                        input_payload["path"] = input_payload.pop(alias)
                        warnings.append(
                            f"{handler_name} node '{node_id}' used '{alias}'; remapped to 'path'"
                        )
                        break
            input_payload.setdefault("path", f"{node_id}.txt")
            if "content" not in input_payload:
                for alias in ("text", "code", "report", "data", "value", "body"):
                    if alias in input_payload:
                        input_payload["content"] = input_payload.pop(alias)
                        warnings.append(
                            f"{handler_name} node '{node_id}' used '{alias}'; remapped to 'content'"
                        )
                        break
            if dependencies:
                dependency_node_id = dependencies[-1]
                expected_field = None
                if upstream_handler_name == "local_llm_text":
                    expected_field = "text"
                elif upstream_handler_name == "template_render":
                    expected_field = "rendered"
                elif upstream_handler_name == "json_serialize":
                    expected_field = "serialized"
                elif upstream_handler_name in {"read_file", "filesystem_read"}:
                    expected_field = "content"

                if "content" not in input_payload:
                    if expected_field is None:
                        input_payload["content"] = upstream_reference
                    else:
                        input_payload["content"] = {
                            "$ref": f"results['{dependency_node_id}']['{expected_field}']"
                        }
                elif expected_field is not None:
                    normalized_content, content_warning = LiteRTPlanner._normalize_upstream_field_input(
                        raw_value=input_payload.get("content"),
                        dependency_node_id=dependency_node_id,
                        expected_field=expected_field,
                        handler_name=handler_name,
                        node_id=node_id,
                        input_key="content",
                    )
                    input_payload["content"] = normalized_content
                    if content_warning:
                        warnings.append(content_warning)
                else:
                    normalized_content, content_warning = LiteRTPlanner._normalize_upstream_result_input(
                        raw_value=input_payload.get("content"),
                        dependency_node_id=dependency_node_id,
                        handler_name=handler_name,
                        node_id=node_id,
                        input_key="content",
                    )
                    input_payload["content"] = normalized_content
                    if content_warning:
                        warnings.append(content_warning)

        if handler_name == "write_csv":
            input_payload.setdefault("path", f"{node_id}.csv")
            if "rows" not in input_payload:
                if dependencies:
                    input_payload["rows"] = {"$ref": f"results['{dependencies[-1]}']['csv_rows']"}
                else:
                    input_payload["rows"] = []
            elif dependencies:
                normalized_rows, rows_warning = LiteRTPlanner._normalize_upstream_collection_input(
                    raw_value=input_payload.get("rows"),
                    dependency_node_id=dependencies[-1],
                    expected_field="csv_rows",
                    handler_name=handler_name,
                    node_id=node_id,
                    input_key="rows",
                )
                input_payload["rows"] = normalized_rows
                if rows_warning:
                    warnings.append(rows_warning)
            if upstream_handler_name == "topic_split":
                normalized_fieldnames, fieldnames_warning = LiteRTPlanner._normalize_topic_split_csv_fieldnames(
                    input_payload.get("fieldnames"),
                    node_id=node_id,
                )
                if normalized_fieldnames is None:
                    input_payload.pop("fieldnames", None)
                else:
                    input_payload["fieldnames"] = normalized_fieldnames
                if fieldnames_warning:
                    warnings.append(fieldnames_warning)

        return input_payload, None

    @staticmethod
    def _normalize_upstream_collection_input(
        raw_value: Any,
        dependency_node_id: str,
        expected_field: str,
        handler_name: str,
        node_id: str,
        input_key: str,
    ) -> tuple[Any, str | None]:
        canonical_ref = {"$ref": f"results['{dependency_node_id}']['{expected_field}']"}

        if isinstance(raw_value, list):
            return raw_value, None

        if isinstance(raw_value, dict):
            raw_ref = raw_value.get("$ref")
            if isinstance(raw_ref, str):
                normalized_ref, changed = LiteRTPlanner._normalize_result_reference_expression(
                    raw_expression=raw_ref,
                    dependency_node_id=dependency_node_id,
                    expected_field=expected_field,
                )
                if changed:
                    return (
                        {"$ref": normalized_ref},
                        f"{handler_name} node '{node_id}' repaired {input_key} reference to upstream '{dependency_node_id}.{expected_field}'",
                    )
                return raw_value, None
            return (
                canonical_ref,
                f"{handler_name} node '{node_id}' replaced non-list {input_key} object with upstream '{dependency_node_id}.{expected_field}' reference",
            )

        if isinstance(raw_value, str) and raw_value.strip():
            normalized_ref, _ = LiteRTPlanner._normalize_result_reference_expression(
                raw_expression=raw_value,
                dependency_node_id=dependency_node_id,
                expected_field=expected_field,
            )
            return (
                {"$ref": normalized_ref},
                f"{handler_name} node '{node_id}' converted string {input_key} to upstream '{dependency_node_id}.{expected_field}' reference",
            )

        return (
            canonical_ref,
            f"{handler_name} node '{node_id}' defaulted {input_key} to upstream '{dependency_node_id}.{expected_field}' reference",
        )

    @staticmethod
    def _normalize_topic_split_csv_fieldnames(
        raw_value: Any,
        *,
        node_id: str,
    ) -> tuple[list[str] | None, str | None]:
        expected_columns = ["topic", "title", "source", "published_at", "link", "summary"]
        if raw_value is None:
            return None, None
        if not isinstance(raw_value, list):
            return (
                expected_columns,
                f"write_csv node '{node_id}' replaced invalid fieldnames with topic_split CSV columns",
            )

        normalized = [str(field).strip() for field in raw_value if str(field).strip()]
        if not normalized:
            return (
                expected_columns,
                f"write_csv node '{node_id}' replaced empty fieldnames with topic_split CSV columns",
            )

        expected_set = {column.casefold() for column in expected_columns}
        normalized_set = {column.casefold() for column in normalized}
        overlap_count = len(expected_set & normalized_set)
        has_placeholder = any("placeholder" in column.casefold() for column in normalized)
        if has_placeholder or overlap_count < 2:
            return (
                expected_columns,
                f"write_csv node '{node_id}' replaced incompatible fieldnames with topic_split CSV columns",
            )
        return normalized, None

    @staticmethod
    def _normalize_upstream_result_input(
        raw_value: Any,
        dependency_node_id: str,
        handler_name: str,
        node_id: str,
        input_key: str,
    ) -> tuple[Any, str | None]:
        canonical_ref = {"$ref": f"results['{dependency_node_id}']"}

        if isinstance(raw_value, dict):
            raw_ref = raw_value.get("$ref")
            if isinstance(raw_ref, str):
                normalized_ref, changed = LiteRTPlanner._normalize_upstream_result_reference_expression(
                    raw_expression=raw_ref,
                    dependency_node_id=dependency_node_id,
                )
                if changed:
                    return (
                        {"$ref": normalized_ref},
                        f"{handler_name} node '{node_id}' repaired {input_key} reference to upstream '{dependency_node_id}' result",
                    )
            if LiteRTPlanner._is_placeholder_input_shell(raw_value):
                return (
                    canonical_ref,
                    f"{handler_name} node '{node_id}' replaced placeholder {input_key} shell with upstream '{dependency_node_id}' result reference",
                )
            return raw_value, None

        if isinstance(raw_value, str) and raw_value.strip():
            if LiteRTPlanner._looks_like_result_reference(raw_value, dependency_node_id):
                normalized_ref, changed = LiteRTPlanner._normalize_upstream_result_reference_expression(
                    raw_expression=raw_value,
                    dependency_node_id=dependency_node_id,
                )
                if changed:
                    return (
                        {"$ref": normalized_ref},
                        f"{handler_name} node '{node_id}' converted string {input_key} to upstream '{dependency_node_id}' result reference",
                    )
                return {"$ref": normalized_ref}, None
            if LiteRTPlanner._is_placeholder_input_shell(raw_value):
                return (
                    canonical_ref,
                    f"{handler_name} node '{node_id}' replaced placeholder {input_key} with upstream '{dependency_node_id}' result reference",
                )
            return raw_value, None

        if isinstance(raw_value, (list, tuple)) and LiteRTPlanner._is_placeholder_input_shell(raw_value):
            return (
                canonical_ref,
                f"{handler_name} node '{node_id}' replaced placeholder {input_key} list with upstream '{dependency_node_id}' result reference",
            )

        if raw_value is None:
            return (
                canonical_ref,
                f"{handler_name} node '{node_id}' defaulted {input_key} to upstream '{dependency_node_id}' result reference",
            )

        return raw_value, None

    @staticmethod
    def _normalize_upstream_field_input(
        raw_value: Any,
        dependency_node_id: str,
        expected_field: str,
        handler_name: str,
        node_id: str,
        input_key: str,
    ) -> tuple[Any, str | None]:
        canonical_ref = {"$ref": f"results['{dependency_node_id}']['{expected_field}']"}

        if isinstance(raw_value, dict):
            raw_ref = raw_value.get("$ref")
            if isinstance(raw_ref, str):
                normalized_ref, changed = LiteRTPlanner._normalize_result_reference_expression(
                    raw_expression=raw_ref,
                    dependency_node_id=dependency_node_id,
                    expected_field=expected_field,
                )
                if changed:
                    return (
                        {"$ref": normalized_ref},
                        f"{handler_name} node '{node_id}' repaired {input_key} reference to upstream '{dependency_node_id}.{expected_field}'",
                    )
                return raw_value, None
            if LiteRTPlanner._is_placeholder_input_shell(raw_value):
                return (
                    canonical_ref,
                    f"{handler_name} node '{node_id}' replaced placeholder {input_key} shell with upstream '{dependency_node_id}.{expected_field}' reference",
                )
            return raw_value, None

        if isinstance(raw_value, str) and raw_value.strip():
            normalized_ref, _ = LiteRTPlanner._normalize_result_reference_expression(
                raw_expression=raw_value,
                dependency_node_id=dependency_node_id,
                expected_field=expected_field,
            )
            return (
                {"$ref": normalized_ref},
                f"{handler_name} node '{node_id}' converted string {input_key} to upstream '{dependency_node_id}.{expected_field}' reference",
            )

        if raw_value is None or LiteRTPlanner._is_placeholder_input_shell(raw_value):
            return (
                canonical_ref,
                f"{handler_name} node '{node_id}' defaulted {input_key} to upstream '{dependency_node_id}.{expected_field}' reference",
            )

        return raw_value, None

    @classmethod
    def _is_placeholder_input_shell(cls, raw_value: Any) -> bool:
        if raw_value is None:
            return True
        if isinstance(raw_value, str):
            normalized = raw_value.strip()
            if not normalized:
                return True
            if re.fullmatch(r"[.\u2026]+", normalized):
                return True
            return normalized.casefold() in {
                "placeholder",
                "<placeholder>",
                "todo",
                "tbd",
                "null",
                "none",
            }
        if isinstance(raw_value, dict):
            if not raw_value:
                return True
            if "$ref" in raw_value and len(raw_value) == 1:
                return False
            return all(cls._is_placeholder_input_shell(value) for value in raw_value.values())
        if isinstance(raw_value, (list, tuple)):
            if not raw_value:
                return True
            return all(cls._is_placeholder_input_shell(value) for value in raw_value)
        return False

    @staticmethod
    def _looks_like_result_reference(raw_value: str, dependency_node_id: str) -> bool:
        normalized = str(raw_value).strip().casefold()
        dependency_normalized = dependency_node_id.casefold()
        return any(
            token in normalized
            for token in (
                dependency_normalized,
                "results[",
                ".output",
                ".result",
                "$ref",
            )
        )

    @staticmethod
    def _normalize_upstream_result_reference_expression(
        raw_expression: str,
        dependency_node_id: str,
    ) -> tuple[str, bool]:
        expression = str(raw_expression).strip()
        if not expression:
            return f"results['{dependency_node_id}']", True

        if expression.startswith("{{") and expression.endswith("}}"):
            expression = expression[2:-2].strip()

        canonical = f"results['{dependency_node_id}']"
        normalized = expression.replace('"', "'").strip()
        if normalized == canonical:
            return canonical, normalized != expression

        if normalized in {
            dependency_node_id,
            f"{dependency_node_id}.output",
            f"{dependency_node_id}.result",
            f"results['{dependency_node_id}']['output']",
            f"results['{dependency_node_id}']['result']",
        }:
            return canonical, True

        if normalized.startswith("results[") and f"'{dependency_node_id}'" in normalized:
            return normalized, normalized != expression

        return canonical, True

    @staticmethod
    def _normalize_result_reference_expression(
        raw_expression: str,
        dependency_node_id: str,
        expected_field: str,
    ) -> tuple[str, bool]:
        expression = str(raw_expression).strip()
        if not expression:
            return f"results['{dependency_node_id}']['{expected_field}']", True

        if expression.startswith("{{") and expression.endswith("}}"):
            expression = expression[2:-2].strip()

        canonical = f"results['{dependency_node_id}']['{expected_field}']"
        normalized = expression.replace('"', "'").strip()
        if normalized == canonical:
            return canonical, normalized != expression

        if normalized in {
            dependency_node_id,
            f"{dependency_node_id}.output",
            f"{dependency_node_id}.result",
            f"results['{dependency_node_id}']",
            f"results['{dependency_node_id}']['output']",
            f"results['{dependency_node_id}']['result']",
        }:
            return canonical, True

        bare_reference = normalized.casefold()
        if bare_reference.endswith(f".{expected_field}") or bare_reference.endswith(
            f".output.{expected_field}"
        ) or bare_reference.endswith(f".result.{expected_field}"):
            return canonical, True

        if normalized.startswith("results[") and f"['{expected_field}']" in normalized:
            return normalized, normalized != expression

        return canonical, True

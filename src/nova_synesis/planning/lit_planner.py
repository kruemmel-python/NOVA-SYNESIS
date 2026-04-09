from __future__ import annotations

import ast
import json
import re
import subprocess
import tempfile
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

    def _invoke_model(self, planner_prompt: str) -> str:
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
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.settings.lit_timeout_s,
                cwd=Path(self.settings.working_directory).resolve(),
            )
            stdout = completed.stdout.strip()
            stderr = completed.stderr.strip()
            if completed.returncode != 0:
                detail = stderr or stdout or "LiteRT planner execution failed"
                raise RuntimeError(detail)
            if not stdout:
                raise RuntimeError("LiteRT planner returned no output")
            return stdout
        finally:
            prompt_path.unlink(missing_ok=True)

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
                    "- Build executable inputs for the chosen handler.",
                    "- Do not output TODO, placeholder, dummy, fake or sample values.",
                    "- Prefer preferred_agent_name over preferred_agent_id when selecting an agent.",
                    "- send_message may use target_agent_name or target_agent_id, but only for listed communication-enabled agents.",
                    "- Unless explicitly required, omit approval fields and keep rollback_strategy at FAIL_FAST.",
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
            "memory_store": "memory_store: input keys memory_id, key, value",
            "memory_retrieve": "memory_retrieve: input keys memory_id, key",
            "memory_search": "memory_search: input keys memory_id, query, optional limit",
            "send_message": "send_message: input keys target_agent_name or target_agent_id, message",
            "resource_health_check": "resource_health_check: optional resource_ids list",
            "template_render": "template_render: input keys template, values",
            "merge_payloads": "merge_payloads: input keys base, updates",
            "read_file": "read_file: input key path",
            "write_file": "write_file: input keys path, content, optional append",
            "json_serialize": "json_serialize: input key value, optional indent",
        }
        lines = [contract_map.get(handler, handler) for handler in handlers]
        if detail_level == "minimal":
            lines = [f"- {handler}" for handler in handlers]
        else:
            lines = [f"- {line}" for line in lines]
        return "Allowed handlers:\n" + "\n".join(lines)

    def _build_agent_section(self, agents: list[dict[str, Any]], detail_level: str) -> str:
        if not agents:
            return "Known agents:\n- none"
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
        return "Known agents:\n" + "\n".join(lines)

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
            preview = self._truncate_text(
                json.dumps(current_flow, ensure_ascii=False, separators=(",", ":")),
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
        repaired_payload = json.loads(json.dumps(parsed_literal, ensure_ascii=False))
        return repaired_payload, "Planner JSON used a tolerant literal-repair path before normalization."

    @staticmethod
    def _extract_json_object(text: str, allow_incomplete: bool = False) -> str:
        start = text.find("{")
        if start < 0:
            raise ValueError("Planner response does not contain a JSON object")

        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            character = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue
            if character == '"':
                in_string = True
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

    def _repair_json_text(self, candidate: str) -> str:
        repaired = candidate
        repaired = self._remove_json_comments(repaired)
        repaired = self._quote_bare_object_keys(repaired)
        repaired = self._replace_keyword_literals(
            repaired,
            {
                "True": "true",
                "False": "false",
                "None": "null",
            },
        )
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
        node_ids: set[str] = set()
        for index, raw_node in enumerate(raw_nodes[:max_nodes], start=1):
            if not isinstance(raw_node, dict):
                raise ValueError(f"Planner node at index {index} is not an object")
            node_id = self._normalize_node_id(raw_node.get("node_id") or raw_node.get("id") or f"task-{index}")
            if node_id in node_ids:
                node_id = f"{node_id}-{index}"
            node_ids.add(node_id)

            handler_name = str(raw_node.get("handler_name", "")).strip()
            if handler_name not in handler_set:
                raise ValueError(
                    f"Planner selected unsupported handler '{handler_name}' for node '{node_id}'"
                )

            preferred_agent_id = None
            raw_agent_name = raw_node.get("preferred_agent_name")
            if isinstance(raw_agent_name, str) and raw_agent_name.strip():
                preferred_agent_id = agent_name_to_id.get(raw_agent_name.casefold())
                if preferred_agent_id is None:
                    warnings.append(
                        f"Unknown preferred_agent_name '{raw_agent_name}' ignored for node '{node_id}'"
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
            input_payload = self._normalize_handler_input(
                handler_name=handler_name,
                input_payload=dict(input_payload),
                node_id=node_id,
                dependencies=self._normalize_string_list(raw_node.get("dependencies")),
                memory_ids=memory_ids,
                comm_agent_ids=comm_agent_ids,
                communication_agents=communication_agents,
                warnings=warnings,
            )

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

        normalized_edges = self._normalize_edges(raw_edges, node_ids, warnings)
        self._merge_dependencies(normalized_nodes, normalized_edges)
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
    def _normalize_handler_input(
        handler_name: str,
        input_payload: dict[str, Any],
        node_id: str,
        dependencies: list[str],
        memory_ids: list[str],
        comm_agent_ids: set[int],
        communication_agents: dict[str, int],
        warnings: list[str],
    ) -> dict[str, Any]:
        upstream_reference = (
            f"{{{{ results['{dependencies[-1]}'] }}}}" if dependencies else {}
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
                else:
                    input_payload["value"] = upstream_reference
                    warnings.append(
                        f"memory_store node '{node_id}' had no value; defaulted to upstream result reference"
                    )

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

        if handler_name == "send_message":
            if "message" not in input_payload:
                input_payload["message"] = {"text": f"Flow node {node_id} completed."}
                warnings.append(
                    f"send_message node '{node_id}' had no message; inserted default completion message"
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
                            return input_payload
                        if not communication_agents:
                            raise ValueError(
                                f"send_message node '{node_id}' cannot be planned because no communication-enabled target agent is registered"
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
                    return input_payload
                if len(comm_agent_ids) == 1:
                    input_payload["target_agent_id"] = next(iter(comm_agent_ids))
                    warnings.append(
                        f"send_message node '{node_id}' had no target_agent_id; defaulted to the only communication-enabled agent"
                    )
                elif len(comm_agent_ids) == 0:
                    raise ValueError(
                        f"send_message node '{node_id}' is not executable because no communication-enabled target agent is registered"
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

        return input_payload

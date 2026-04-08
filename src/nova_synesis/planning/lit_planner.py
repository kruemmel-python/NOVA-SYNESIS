from __future__ import annotations

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
        planner_prompt = self._build_prompt(
            prompt=prompt,
            catalog=catalog,
            current_flow=current_flow,
            max_nodes=max_nodes,
        )
        raw_response = self._invoke_model(planner_prompt)
        parsed = self._parse_model_output(raw_response)
        normalized, warnings = self._normalize_flow_request(
            parsed=parsed,
            catalog=catalog,
            max_nodes=max_nodes,
        )
        return PlannerGraphResult(
            flow_request=normalized,
            explanation=self._extract_explanation(parsed),
            warnings=warnings,
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
    ) -> str:
        resource_types = [resource_type.value for resource_type in ResourceType]
        current_flow_text = (
            json.dumps(current_flow, ensure_ascii=False, indent=2)
            if current_flow is not None
            else "null"
        )
        agent_catalog = [
            {
                "name": agent["name"],
                "agent_id": agent["agent_id"],
                "role": agent["role"],
                "capabilities": [capability["name"] for capability in agent.get("capabilities", [])],
            }
            for agent in catalog.agents
        ]
        resource_catalog = [
            {
                "resource_id": resource["resource_id"],
                "type": resource["type"],
                "endpoint": resource["endpoint"],
            }
            for resource in catalog.resources
        ]
        memory_catalog = catalog.memory_systems
        handler_contracts = {
            "http_request": {
                "required_input": ["url", "method"],
                "example_shape": {
                    "url": "https://...",
                    "method": "GET",
                    "headers": {},
                    "params": {},
                    "json": {},
                    "data": None,
                },
            },
            "memory_store": {
                "required_input": ["memory_id", "key", "value"],
                "example_shape": {
                    "memory_id": "existing-memory-id",
                    "key": "descriptive-key",
                    "value": "{{ results['previous-node'] }}",
                },
            },
            "memory_retrieve": {
                "required_input": ["memory_id", "key"],
                "example_shape": {"memory_id": "existing-memory-id", "key": "descriptive-key"},
            },
            "memory_search": {
                "required_input": ["memory_id", "query"],
                "example_shape": {"memory_id": "existing-memory-id", "query": "keyword", "limit": 5},
            },
            "send_message": {
                "required_input": ["target_agent_id", "message"],
                "example_shape": {"target_agent_id": 1, "message": {"text": "done"}},
            },
            "resource_health_check": {
                "required_input": [],
                "example_shape": {"resource_ids": [1]},
            },
            "template_render": {
                "required_input": ["template", "values"],
                "example_shape": {"template": "Done for {name}", "values": {"name": "world"}},
            },
            "merge_payloads": {
                "required_input": ["base", "updates"],
                "example_shape": {"base": {}, "updates": [{}]},
            },
            "read_file": {
                "required_input": ["path"],
                "example_shape": {"path": "relative/file.txt"},
            },
            "write_file": {
                "required_input": ["path", "content"],
                "example_shape": {"path": "relative/file.txt", "content": "text", "append": False},
            },
            "json_serialize": {
                "required_input": ["value"],
                "example_shape": {"value": {"done": True}, "indent": 2},
            },
        }
        return f"""
You are an expert AI workflow planner for a graph execution engine.
Return exactly one JSON object and nothing else outside the JSON.

The JSON schema must be:
{{
  "nodes": [
    {{
      "node_id": "unique-id",
      "title": "Short human title",
      "handler_name": "one allowed handler",
      "input": {{}},
      "required_capabilities": [],
      "required_resource_ids": [],
      "required_resource_types": [],
      "retry_policy": {{
        "max_retries": 3,
        "backoff_ms": 250,
        "exponential": true,
        "max_backoff_ms": 10000,
        "jitter_ratio": 0.0
      }},
      "rollback_strategy": "FAIL_FAST",
      "validator_rules": {{}},
      "metadata": {{}},
      "compensation_handler": null,
      "dependencies": [],
      "conditions": {{}},
      "preferred_agent_name": null
    }}
  ],
  "edges": [
    {{
      "from_node": "node-a",
      "to_node": "node-b",
      "condition": "True"
    }}
  ],
  "explanation": "Brief rationale"
}}

Rules:
- Maximum {max_nodes} nodes.
- Do not create fake start/end nodes.
- Every edge source and target must reference an existing node_id.
- Use only these handlers: {json.dumps(catalog.handlers, ensure_ascii=False)}.
- Handler contracts: {json.dumps(handler_contracts, ensure_ascii=False)}.
- Use only these resource types: {json.dumps(resource_types, ensure_ascii=False)}.
- If you reference concrete resources, use only these known resources: {json.dumps(resource_catalog, ensure_ascii=False)}.
- If you use memory handlers, use only these known memory systems: {json.dumps(memory_catalog, ensure_ascii=False)}.
- If you pick an agent, use preferred_agent_name from this catalog only: {json.dumps(agent_catalog, ensure_ascii=False)}.
- Only use send_message when a target agent with a communication config is available.
- Do not output TODO, placeholder, example, dummy, sample, or fake values.
- Build executable node inputs that match the chosen handler.
- Prefer explicit dependencies and matching edges.
- If a condition is unconditional, use "True".
- metadata may include domain assumptions, but no prose outside the explanation field.

Current flow for context:
{current_flow_text}

User goal:
{prompt}
""".strip()

    @staticmethod
    def _extract_explanation(parsed: dict[str, Any]) -> str | None:
        explanation = parsed.get("explanation")
        return explanation if isinstance(explanation, str) and explanation.strip() else None

    def _parse_model_output(self, raw_response: str) -> dict[str, Any]:
        fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_response, flags=re.DOTALL)
        candidate = fenced_match.group(1) if fenced_match else self._extract_json_object(raw_response)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Planner returned invalid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Planner output must be a JSON object")
        return parsed

    @staticmethod
    def _extract_json_object(text: str) -> str:
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
        raise ValueError("Planner response contains an incomplete JSON object")

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

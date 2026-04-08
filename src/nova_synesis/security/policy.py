from __future__ import annotations

import ast
import ipaddress
from collections import deque
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from nova_synesis.config import Settings

_SUSPICIOUS_TOKENS = ("__", "import", "lambda", "eval", "exec", "open(", "compile(")
_ALLOWED_EXPRESSION_NODES = (
    ast.Expression,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.USub,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Subscript,
    ast.Slice,
    ast.Call,
    ast.keyword,
)
_ALLOWED_HELPERS = {"len", "sum", "min", "max", "all", "any", "contains", "exists"}
_INGRESS_HANDLERS = {"http_request", "send_message", "read_file"}


@dataclass(slots=True)
class SecurityFinding:
    code: str
    severity: str
    message: str
    node_id: str | None = None
    field: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "node_id": self.node_id,
            "field": self.field,
        }


@dataclass(slots=True)
class FlowSecurityReport:
    approved: bool = True
    violations: list[SecurityFinding] = field(default_factory=list)
    warnings: list[SecurityFinding] = field(default_factory=list)

    def add_violation(
        self,
        code: str,
        message: str,
        node_id: str | None = None,
        field: str | None = None,
    ) -> None:
        self.approved = False
        self.violations.append(
            SecurityFinding(
                code=code,
                severity="error",
                message=message,
                node_id=node_id,
                field=field,
            )
        )

    def add_warning(
        self,
        code: str,
        message: str,
        node_id: str | None = None,
        field: str | None = None,
    ) -> None:
        self.warnings.append(
            SecurityFinding(
                code=code,
                severity="warning",
                message=message,
                node_id=node_id,
                field=field,
            )
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "violations": [finding.as_dict() for finding in self.violations],
            "warnings": [finding.as_dict() for finding in self.warnings],
        }

    def ensure_allowed(self) -> None:
        if not self.violations:
            return
        details = "; ".join(finding.message for finding in self.violations[:5])
        raise ValueError(f"Semantic firewall rejected flow: {details}")


class SemanticFirewall:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._allowed_http_hosts = tuple(host.casefold() for host in settings.security_http_allowed_hosts)
        self._blocked_handler_keywords = tuple(
            keyword.casefold() for keyword in settings.security_blocked_handler_keywords
        )
        self._blocked_capability_keywords = tuple(
            keyword.casefold() for keyword in settings.security_blocked_capability_keywords
        )
        self._allowed_send_protocols = {
            protocol.casefold() for protocol in settings.security_send_message_allowed_protocols
        }

    def validate_agent_registration(
        self,
        name: str,
        capabilities: list[dict[str, Any]],
        communication: dict[str, Any] | None,
        existing_agents: list[dict[str, Any]],
    ) -> FlowSecurityReport:
        report = FlowSecurityReport()
        if any(str(agent["name"]).casefold() == name.casefold() for agent in existing_agents):
            report.add_violation("agent.duplicate_name", f"Agent name '{name}' already exists")

        for capability in capabilities:
            tokens = {
                str(capability.get("name", "")).casefold(),
                str(capability.get("type", "")).casefold(),
            }
            if any(
                blocked in token
                for token in tokens
                for blocked in self._blocked_capability_keywords
            ):
                report.add_violation(
                    "agent.blocked_capability",
                    f"Agent '{name}' declares a blocked capability profile",
                )

        if isinstance(communication, dict):
            protocol = str(communication.get("protocol", "")).casefold()
            endpoint = str(communication.get("endpoint", "")).strip()
            if protocol in {"rest", "websocket"} and endpoint:
                parsed = urlparse(endpoint)
                if not self._is_allowed_host(parsed.hostname):
                    report.add_violation(
                        "agent.external_endpoint",
                        f"Agent '{name}' uses a communication endpoint outside the allowlist",
                    )
        return report

    def validate_flow_request(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]] | None,
        metadata: dict[str, Any] | None,
        agents: list[dict[str, Any]],
        resources: list[dict[str, Any]],
        memory_systems: list[dict[str, Any]],
        planner_generated: bool = False,
        phase: str = "create",
    ) -> FlowSecurityReport:
        report = FlowSecurityReport()
        if not self.settings.security_enabled:
            return report

        if len(nodes) > self.settings.security_max_nodes:
            report.add_violation(
                "flow.max_nodes",
                f"Flow defines {len(nodes)} nodes but the policy limit is {self.settings.security_max_nodes}",
            )

        if len(edges or []) > self.settings.security_max_edges:
            report.add_violation(
                "flow.max_edges",
                f"Flow defines {len(edges or [])} edges but the policy limit is {self.settings.security_max_edges}",
            )

        node_index: dict[str, dict[str, Any]] = {}
        for node in nodes:
            node_id = str(node.get("node_id", "")).strip()
            if not node_id:
                report.add_violation("node.missing_id", "Every node must define a non-empty node_id")
                continue
            if node_id in node_index:
                report.add_violation("node.duplicate_id", f"Duplicate node_id '{node_id}'", node_id=node_id)
                continue
            node_index[node_id] = node

            handler_name = str(node.get("handler_name", "")).strip()
            if any(keyword in handler_name.casefold() for keyword in self._blocked_handler_keywords):
                report.add_violation(
                    "node.blocked_handler",
                    f"Handler '{handler_name}' is blocked by policy",
                    node_id=node_id,
                    field="handler_name",
                )

        merged_edges = self._collect_edges(node_index, edges or [], report)
        self._validate_acyclic(node_index, merged_edges, report)

        total_attempts = sum(
            int(node.get("retry_policy", {}).get("max_retries", 3)) + 1 for node in node_index.values()
        )
        if total_attempts > self.settings.security_max_total_attempts:
            report.add_violation(
                "flow.retry_budget",
                f"Flow retry budget {total_attempts} exceeds the policy limit {self.settings.security_max_total_attempts}",
            )

        if isinstance(metadata, dict):
            max_concurrency = int(metadata.get("max_concurrency", self.settings.max_flow_concurrency))
            if max_concurrency > self.settings.max_flow_concurrency:
                report.add_violation(
                    "flow.max_concurrency",
                    f"Flow max_concurrency {max_concurrency} exceeds the service limit {self.settings.max_flow_concurrency}",
                )

        agent_index = {int(agent["agent_id"]): agent for agent in agents}
        resource_index = {int(resource["resource_id"]): resource for resource in resources}
        memory_index = {str(system["memory_id"]): system for system in memory_systems}

        for node_id, node in node_index.items():
            handler_name = str(node.get("handler_name", "")).strip()
            input_payload = node.get("input")
            if not isinstance(input_payload, dict):
                input_payload = {}

            self._validate_expression_container(
                node_id=node_id,
                field="input",
                value=input_payload,
                allowed_names={"results", "node_id", "flow"},
                report=report,
            )
            self._validate_expression_map(
                node_id=node_id,
                field="conditions",
                expressions=node.get("conditions", {}),
                allowed_names={"results", "source_result", "target_node", "completed", "blocked", "failed"},
                report=report,
            )
            validator_rules = node.get("validator_rules", {})
            if isinstance(validator_rules, dict):
                expression = validator_rules.get("expression")
                if isinstance(expression, str) and expression.strip():
                    self._validate_expression(
                        node_id=node_id,
                        field="validator_rules.expression",
                        expression=expression,
                        allowed_names={"result", "metadata"},
                        report=report,
                    )

            if handler_name == "http_request":
                self._validate_http_request(node_id, node, input_payload, resource_index, report)
            elif handler_name == "send_message":
                self._validate_send_message(node_id, input_payload, agent_index, report)
            elif handler_name in {"read_file", "write_file"}:
                self._validate_file_handler(node_id, input_payload, report)

            if planner_generated and handler_name == "http_request" and "url" in input_payload:
                report.add_warning(
                    "planner.raw_http_url",
                    "Planner generated a raw URL http_request; prefer registered API resources for production",
                    node_id=node_id,
                    field="input.url",
                )

        self._detect_sensitive_exfiltration(node_index, merged_edges, agent_index, memory_index, report)
        self._detect_memory_poisoning(node_index, merged_edges, memory_index, report)
        return report

    def _collect_edges(
        self,
        node_index: dict[str, dict[str, Any]],
        edges: list[dict[str, Any]],
        report: FlowSecurityReport,
    ) -> list[tuple[str, str]]:
        merged: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()

        for node_id, node in node_index.items():
            for dependency in node.get("dependencies", []) or []:
                dependency_id = str(dependency)
                if dependency_id not in node_index:
                    report.add_violation(
                        "edge.unknown_dependency",
                        f"Node '{node_id}' depends on unknown node '{dependency_id}'",
                        node_id=node_id,
                        field="dependencies",
                    )
                    continue
                key = (dependency_id, node_id)
                if key not in seen:
                    merged.append(key)
                    seen.add(key)

        for edge in edges:
            source = str(edge.get("from_node", "")).strip()
            target = str(edge.get("to_node", "")).strip()
            if source not in node_index or target not in node_index:
                report.add_violation(
                    "edge.unknown_node",
                    f"Edge '{source}' -> '{target}' references an unknown node",
                )
                continue
            if source == target:
                report.add_violation(
                    "edge.self_reference",
                    f"Self-referential edge on '{source}' is not allowed",
                    node_id=source,
                )
                continue
            key = (source, target)
            if key not in seen:
                merged.append(key)
                seen.add(key)
        return merged

    def _validate_acyclic(
        self,
        node_index: dict[str, dict[str, Any]],
        edges: list[tuple[str, str]],
        report: FlowSecurityReport,
    ) -> None:
        adjacency = {node_id: [] for node_id in node_index}
        indegree = {node_id: 0 for node_id in node_index}
        for source, target in edges:
            adjacency[source].append(target)
            indegree[target] += 1

        queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            node_id = queue.popleft()
            visited += 1
            for target in adjacency[node_id]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)

        if visited != len(node_index):
            report.add_violation(
                "flow.cycle",
                "Flow contains a cycle. Only DAG execution is allowed by policy.",
            )

    def _validate_http_request(
        self,
        node_id: str,
        node: dict[str, Any],
        input_payload: dict[str, Any],
        resource_index: dict[int, dict[str, Any]],
        report: FlowSecurityReport,
    ) -> None:
        method = str(input_payload.get("method", "GET")).upper()
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"}:
            report.add_violation(
                "http.method",
                f"Unsupported http_request method '{method}'",
                node_id=node_id,
                field="input.method",
            )

        target_urls: list[str] = []
        if isinstance(input_payload.get("url"), str) and input_payload["url"].strip():
            target_urls.append(str(input_payload["url"]).strip())

        for resource_id in node.get("required_resource_ids", []) or []:
            try:
                resource = resource_index[int(resource_id)]
            except (KeyError, TypeError, ValueError):
                continue
            if str(resource.get("type")) == "API":
                target_urls.append(str(resource.get("endpoint", "")).strip())

        if not target_urls:
            report.add_warning(
                "http.no_target",
                "http_request node has no explicit URL and no bound API resource",
                node_id=node_id,
            )
            return

        for target_url in target_urls:
            parsed = urlparse(target_url)
            if parsed.scheme not in {"http", "https"}:
                report.add_violation(
                    "http.scheme",
                    f"Disallowed URL scheme '{parsed.scheme}' in http_request",
                    node_id=node_id,
                    field="input.url",
                )
                continue
            if not self._is_allowed_host(parsed.hostname):
                report.add_violation(
                    "http.host",
                    f"Outbound host '{parsed.hostname}' is outside the semantic firewall allowlist",
                    node_id=node_id,
                    field="input.url",
                )

    def _validate_send_message(
        self,
        node_id: str,
        input_payload: dict[str, Any],
        agent_index: dict[int, dict[str, Any]],
        report: FlowSecurityReport,
    ) -> None:
        if "target_agent_id" not in input_payload:
            report.add_violation(
                "send_message.target_required",
                "send_message requires an explicit target_agent_id",
                node_id=node_id,
                field="input.target_agent_id",
            )
            return

        try:
            target_agent_id = int(input_payload["target_agent_id"])
        except (TypeError, ValueError):
            report.add_violation(
                "send_message.target_invalid",
                "send_message target_agent_id must be numeric",
                node_id=node_id,
                field="input.target_agent_id",
            )
            return

        target_agent = agent_index.get(target_agent_id)
        if target_agent is None:
            report.add_violation(
                "send_message.target_unknown",
                f"send_message references unknown agent '{target_agent_id}'",
                node_id=node_id,
                field="input.target_agent_id",
            )
            return

        communication = target_agent.get("communication")
        if not isinstance(communication, dict):
            report.add_violation(
                "send_message.target_no_comms",
                f"Target agent '{target_agent_id}' has no communication adapter",
                node_id=node_id,
            )
            return

        protocol = str(communication.get("protocol", "")).casefold()
        if protocol not in self._allowed_send_protocols:
            report.add_violation(
                "send_message.protocol_blocked",
                f"Communication protocol '{communication.get('protocol')}' is blocked by policy",
                node_id=node_id,
            )

        message = input_payload.get("message")
        if isinstance(message, dict):
            for blocked_key in ("target_endpoint", "endpoint", "url", "receive_url"):
                if blocked_key in message:
                    report.add_violation(
                        "send_message.endpoint_override",
                        f"send_message message payload may not override '{blocked_key}'",
                        node_id=node_id,
                        field=f"input.message.{blocked_key}",
                    )

    def _validate_file_handler(
        self,
        node_id: str,
        input_payload: dict[str, Any],
        report: FlowSecurityReport,
    ) -> None:
        if bool(input_payload.get("allow_outside_workdir", False)):
            report.add_violation(
                "file.outside_workdir",
                "File handlers may not set allow_outside_workdir under the semantic firewall",
                node_id=node_id,
                field="input.allow_outside_workdir",
            )

    def _validate_expression_container(
        self,
        node_id: str,
        field: str,
        value: Any,
        allowed_names: set[str],
        report: FlowSecurityReport,
    ) -> None:
        if isinstance(value, dict):
            if "$ref" in value and len(value) == 1 and isinstance(value["$ref"], str):
                self._validate_expression(node_id, field, value["$ref"], allowed_names, report)
            for child_key, child_value in value.items():
                child_field = f"{field}.{child_key}"
                self._validate_expression_container(node_id, child_field, child_value, allowed_names, report)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                self._validate_expression_container(node_id, f"{field}[{index}]", child, allowed_names, report)
            return
        if isinstance(value, str) and "{{" in value and "}}" in value:
            self._validate_template_string(node_id, field, value, allowed_names, report)

    def _validate_expression_map(
        self,
        node_id: str,
        field: str,
        expressions: Any,
        allowed_names: set[str],
        report: FlowSecurityReport,
    ) -> None:
        if not isinstance(expressions, dict):
            return
        for key, value in expressions.items():
            if isinstance(value, str) and value.strip():
                self._validate_expression(node_id, f"{field}.{key}", value, allowed_names, report)

    def _validate_template_string(
        self,
        node_id: str,
        field: str,
        template: str,
        allowed_names: set[str],
        report: FlowSecurityReport,
    ) -> None:
        cursor = 0
        while True:
            start = template.find("{{", cursor)
            if start < 0:
                return
            end = template.find("}}", start + 2)
            if end < 0:
                report.add_violation(
                    "expression.unterminated_template",
                    "Template expression is not properly terminated",
                    node_id=node_id,
                    field=field,
                )
                return
            expression = template[start + 2 : end].strip()
            self._validate_expression(node_id, field, expression, allowed_names, report)
            cursor = end + 2

    def _validate_expression(
        self,
        node_id: str,
        field: str,
        expression: str,
        allowed_names: set[str],
        report: FlowSecurityReport,
    ) -> None:
        if len(expression) > self.settings.security_max_expression_length:
            report.add_violation(
                "expression.too_long",
                f"Expression exceeds the policy limit of {self.settings.security_max_expression_length} characters",
                node_id=node_id,
                field=field,
            )
            return

        lowered = expression.casefold()
        if any(token in lowered for token in _SUSPICIOUS_TOKENS):
            report.add_violation(
                "expression.suspicious_token",
                "Expression contains a blocked token sequence",
                node_id=node_id,
                field=field,
            )
            return

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            report.add_violation(
                "expression.syntax",
                f"Invalid expression syntax: {exc.msg}",
                node_id=node_id,
                field=field,
            )
            return

        nodes = list(ast.walk(tree))
        if len(nodes) > self.settings.security_max_expression_nodes:
            report.add_violation(
                "expression.complexity",
                f"Expression exceeds the AST node limit of {self.settings.security_max_expression_nodes}",
                node_id=node_id,
                field=field,
            )
            return

        for node in nodes:
            if not isinstance(node, _ALLOWED_EXPRESSION_NODES):
                report.add_violation(
                    "expression.node_type",
                    f"Expression uses disallowed syntax '{type(node).__name__}'",
                    node_id=node_id,
                    field=field,
                )
                return
            if isinstance(node, ast.Name):
                if node.id not in allowed_names and node.id not in _ALLOWED_HELPERS:
                    report.add_violation(
                        "expression.name",
                        f"Expression references disallowed symbol '{node.id}'",
                        node_id=node_id,
                        field=field,
                    )
                    return
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_HELPERS:
                    report.add_violation(
                        "expression.call",
                        "Expression calls a non-whitelisted helper function",
                        node_id=node_id,
                        field=field,
                    )
                    return

    def _detect_sensitive_exfiltration(
        self,
        node_index: dict[str, dict[str, Any]],
        edges: list[tuple[str, str]],
        agent_index: dict[int, dict[str, Any]],
        memory_index: dict[str, dict[str, Any]],
        report: FlowSecurityReport,
    ) -> None:
        upstream = self._build_upstream_map(node_index, edges)

        sensitive_sources: set[str] = set()
        for node_id, node in node_index.items():
            handler_name = str(node.get("handler_name", "")).strip()
            input_payload = node.get("input") if isinstance(node.get("input"), dict) else {}
            if handler_name not in {"memory_retrieve", "memory_search"}:
                continue
            memory_id = str(input_payload.get("memory_id", "")).strip()
            config = memory_index.get(memory_id, {}).get("config", {})
            if isinstance(config, dict) and bool(config.get("sensitive", False)):
                sensitive_sources.add(node_id)

        if not sensitive_sources:
            return

        for node_id, node in node_index.items():
            handler_name = str(node.get("handler_name", "")).strip()
            if handler_name not in {"http_request", "send_message"}:
                continue
            if not (upstream[node_id] & sensitive_sources):
                continue
            if handler_name == "http_request":
                report.add_violation(
                    "flow.sensitive_exfiltration",
                    "Sensitive memory data may not flow into http_request nodes",
                    node_id=node_id,
                )
                continue

            input_payload = node.get("input") if isinstance(node.get("input"), dict) else {}
            try:
                target_agent_id = int(input_payload.get("target_agent_id"))
            except (TypeError, ValueError):
                continue
            communication = agent_index.get(target_agent_id, {}).get("communication")
            protocol = str(communication.get("protocol", "")) if isinstance(communication, dict) else ""
            if protocol.casefold() != "message_queue":
                report.add_violation(
                    "flow.sensitive_message_exfiltration",
                    "Sensitive memory data may only be dispatched to internal message queues",
                    node_id=node_id,
                )

    def _detect_memory_poisoning(
        self,
        node_index: dict[str, dict[str, Any]],
        edges: list[tuple[str, str]],
        memory_index: dict[str, dict[str, Any]],
        report: FlowSecurityReport,
    ) -> None:
        upstream = self._build_upstream_map(node_index, edges)
        for node_id, node in node_index.items():
            if str(node.get("handler_name", "")).strip() != "memory_store":
                continue
            input_payload = node.get("input") if isinstance(node.get("input"), dict) else {}
            memory_id = str(input_payload.get("memory_id", "")).strip()
            memory_config = memory_index.get(memory_id, {}).get("config", {})
            if not isinstance(memory_config, dict):
                memory_config = {}
            if not bool(memory_config.get("planner_visible", True)):
                continue
            if bool(memory_config.get("allow_untrusted_ingest", False)):
                continue
            if any(
                str(node_index[source].get("handler_name", "")).strip() in _INGRESS_HANDLERS
                for source in upstream[node_id]
            ):
                report.add_violation(
                    "flow.memory_poisoning",
                    "Planner-visible memory may not ingest data from untrusted ingress handlers without explicit opt-in",
                    node_id=node_id,
                )

    @staticmethod
    def _build_upstream_map(
        node_index: dict[str, dict[str, Any]],
        edges: list[tuple[str, str]],
    ) -> dict[str, set[str]]:
        incoming: dict[str, set[str]] = {node_id: set() for node_id in node_index}
        for source, target in edges:
            incoming[target].add(source)

        upstream: dict[str, set[str]] = {node_id: set() for node_id in node_index}
        for node_id in node_index:
            visited: set[str] = set()
            queue = deque(incoming[node_id])
            while queue:
                source = queue.popleft()
                if source in visited:
                    continue
                visited.add(source)
                upstream[node_id].add(source)
                queue.extend(incoming[source])
        return upstream

    def _is_allowed_host(self, host: str | None) -> bool:
        if not host:
            return False
        if self.settings.security_allow_loopback_hosts and self._is_loopback_host(host):
            return True

        resolved_host = host.casefold()
        for allowed in self._allowed_http_hosts:
            if resolved_host == allowed or resolved_host.endswith(f".{allowed}"):
                return True
        return False

    @staticmethod
    def _is_loopback_host(host: str) -> bool:
        resolved_host = host.casefold()
        if resolved_host in {"localhost", "127.0.0.1", "::1"}:
            return True
        try:
            return ipaddress.ip_address(resolved_host).is_loopback
        except ValueError:
            return False

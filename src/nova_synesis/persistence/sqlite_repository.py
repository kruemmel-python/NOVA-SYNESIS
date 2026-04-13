from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from nova_synesis.domain.models import Agent, ExecutionFlow, Intent, Resource, Task, TaskExecution
from nova_synesis.memory.systems import MemorySystem


class SQLiteRepository:
    def __init__(self, database_path: str) -> None:
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self._lock:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS counters (
                    name TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS agents (
                    agent_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    state TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    comms_json TEXT,
                    memory_refs_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    backend TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS resources (
                    resource_id INTEGER PRIMARY KEY,
                    type TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    state TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS intents (
                    intent_id INTEGER PRIMARY KEY,
                    goal TEXT NOT NULL,
                    constraints_json TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY,
                    input_json TEXT NOT NULL,
                    output_json TEXT,
                    status TEXT NOT NULL,
                    assigned_agent_id INTEGER,
                    required_resources_json TEXT NOT NULL,
                    retry_policy_json TEXT NOT NULL,
                    handler_name TEXT NOT NULL,
                    validator_rules_json TEXT NOT NULL,
                    context_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    rollback_strategy TEXT NOT NULL,
                    compensation_handler TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS flows (
                    flow_id INTEGER PRIMARY KEY,
                    state TEXT NOT NULL,
                    nodes_json TEXT NOT NULL,
                    edges_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    active_version_id INTEGER,
                    version_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS flow_versions (
                    version_id INTEGER PRIMARY KEY,
                    flow_id INTEGER NOT NULL,
                    version_number INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    nodes_json TEXT NOT NULL,
                    edges_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT,
                    change_reason TEXT,
                    parent_version_id INTEGER,
                    planner_generated INTEGER NOT NULL DEFAULT 0,
                    security_report_json TEXT,
                    version_hash TEXT NOT NULL,
                    UNIQUE(flow_id, version_number)
                );

                CREATE TABLE IF NOT EXISTS executions (
                    execution_id INTEGER PRIMARY KEY,
                    task_id INTEGER NOT NULL,
                    flow_id INTEGER,
                    start_time TEXT,
                    end_time TEXT,
                    result_json TEXT,
                    status TEXT NOT NULL,
                    errors_json TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    resource_history_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS execution_metrics (
                    metric_id INTEGER PRIMARY KEY,
                    execution_id INTEGER NOT NULL,
                    flow_id INTEGER,
                    node_id TEXT NOT NULL,
                    handler_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latency_ms INTEGER,
                    attempt_count INTEGER NOT NULL,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    estimated_cost REAL,
                    model_name TEXT,
                    resource_history_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            self._ensure_column("flows", "active_version_id", "INTEGER")
            self._ensure_column("flows", "version_count", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column("flows", "created_at", "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")
            self._bootstrap_existing_flow_versions()
            self._connection.commit()

    def _ensure_column(self, table_name: str, column_name: str, ddl: str) -> None:
        columns = {
            row["name"]
            for row in self._connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        if column_name in columns:
            return
        self._connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}")

    def _bootstrap_existing_flow_versions(self) -> None:
        rows = self._connection.execute(
            """
            SELECT f.*
            FROM flows AS f
            LEFT JOIN flow_versions AS v ON v.flow_id = f.flow_id
            GROUP BY f.flow_id
            HAVING COUNT(v.version_id) = 0
            """
        ).fetchall()
        for row in rows:
            version_id = self.next_id("flow_version")
            version_hash = self._compute_version_hash(
                row["nodes_json"],
                row["edges_json"],
                row["metadata_json"],
            )
            self._connection.execute(
                """
                INSERT INTO flow_versions (
                    version_id, flow_id, version_number, state, nodes_json, edges_json, metadata_json,
                    created_at, created_by, change_reason, parent_version_id, planner_generated,
                    security_report_json, version_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    row["flow_id"],
                    1,
                    row["state"],
                    row["nodes_json"],
                    row["edges_json"],
                    row["metadata_json"],
                    row["updated_at"],
                    "migration",
                    "Bootstrap existing flow into version history",
                    None,
                    0,
                    json.dumps({}),
                    version_hash,
                ),
            )
            self._connection.execute(
                """
                UPDATE flows
                SET active_version_id = ?, version_count = ?, created_at = COALESCE(created_at, updated_at)
                WHERE flow_id = ?
                """,
                (version_id, 1, row["flow_id"]),
            )

    def next_id(self, name: str) -> int:
        with self._lock:
            row = self._connection.execute(
                "SELECT value FROM counters WHERE name = ?",
                (name,),
            ).fetchone()
            if row is None:
                value = 1
                self._connection.execute(
                    "INSERT INTO counters (name, value) VALUES (?, ?)",
                    (name, value),
                )
            else:
                value = int(row["value"]) + 1
                self._connection.execute(
                    "UPDATE counters SET value = ? WHERE name = ?",
                    (value, name),
                )
            self._connection.commit()
            return value

    def save_agent(self, agent: Agent) -> None:
        comms_payload = None
        if agent.comms is not None:
            comms_payload = {
                "protocol": agent.comms.protocol.value,
                "endpoint": agent.comms.endpoint,
                "config": agent.comms.config,
            }
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO agents (agent_id, name, role, state, capabilities_json, comms_json, memory_refs_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(agent_id) DO UPDATE SET
                    name = excluded.name,
                    role = excluded.role,
                    state = excluded.state,
                    capabilities_json = excluded.capabilities_json,
                    comms_json = excluded.comms_json,
                    memory_refs_json = excluded.memory_refs_json,
                    updated_at = excluded.updated_at
                """,
                (
                    agent.agent_id,
                    agent.name,
                    agent.role,
                    agent.state.value,
                    json.dumps(
                        [
                            {
                                "name": capability.name,
                                "type": capability.type,
                                "constraints": capability.constraints,
                            }
                            for capability in agent.capabilities
                        ]
                    ),
                    json.dumps(comms_payload) if comms_payload else None,
                    json.dumps([memory.memory_id for memory in agent.memory_refs]),
                ),
            )
            self._connection.commit()

    def save_memory_system(self, memory_system: MemorySystem) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO memories (memory_id, type, backend, config_json, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(memory_id) DO UPDATE SET
                    type = excluded.type,
                    backend = excluded.backend,
                    config_json = excluded.config_json,
                    updated_at = excluded.updated_at
                """,
                (
                    memory_system.memory_id,
                    memory_system.type.value,
                    memory_system.backend,
                    json.dumps(memory_system.config),
                ),
            )
            self._connection.commit()

    def save_resource(self, resource: Resource) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO resources (resource_id, type, endpoint, metadata_json, state, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(resource_id) DO UPDATE SET
                    type = excluded.type,
                    endpoint = excluded.endpoint,
                    metadata_json = excluded.metadata_json,
                    state = excluded.state,
                    updated_at = excluded.updated_at
                """,
                (
                    resource.resource_id,
                    resource.type.value,
                    resource.endpoint,
                    json.dumps(resource.metadata),
                    resource.state.value,
                ),
            )
            self._connection.commit()

    def save_intent(self, intent: Intent) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO intents (intent_id, goal, constraints_json, priority, timestamp)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(intent_id) DO UPDATE SET
                    goal = excluded.goal,
                    constraints_json = excluded.constraints_json,
                    priority = excluded.priority,
                    timestamp = excluded.timestamp
                """,
                (
                    intent.intent_id,
                    intent.goal,
                    json.dumps(intent.constraints),
                    intent.priority,
                    intent.timestamp.isoformat(),
                ),
            )
            self._connection.commit()

    def save_task(self, task: Task) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO tasks (
                    task_id, input_json, output_json, status, assigned_agent_id, required_resources_json,
                    retry_policy_json, handler_name, validator_rules_json, context_json, metadata_json,
                    rollback_strategy, compensation_handler, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(task_id) DO UPDATE SET
                    input_json = excluded.input_json,
                    output_json = excluded.output_json,
                    status = excluded.status,
                    assigned_agent_id = excluded.assigned_agent_id,
                    required_resources_json = excluded.required_resources_json,
                    retry_policy_json = excluded.retry_policy_json,
                    handler_name = excluded.handler_name,
                    validator_rules_json = excluded.validator_rules_json,
                    context_json = excluded.context_json,
                    metadata_json = excluded.metadata_json,
                    rollback_strategy = excluded.rollback_strategy,
                    compensation_handler = excluded.compensation_handler,
                    updated_at = excluded.updated_at
                """,
                (
                    task.task_id,
                    json.dumps(task.input, default=str),
                    json.dumps(task.output, default=str) if task.output is not None else None,
                    task.status.value,
                    task.assigned_agent.agent_id if task.assigned_agent else None,
                    json.dumps([resource.resource_id for resource in task.required_resources]),
                    json.dumps(
                        {
                            "max_retries": task.retry_policy.max_retries,
                            "backoff_ms": task.retry_policy.backoff_ms,
                            "exponential": task.retry_policy.exponential,
                            "max_backoff_ms": task.retry_policy.max_backoff_ms,
                            "jitter_ratio": task.retry_policy.jitter_ratio,
                        }
                    ),
                    task.handler_name,
                    json.dumps(task.validator_rules),
                    json.dumps(task.context, default=str),
                    json.dumps(
                        {
                            **task.metadata,
                            "requires_manual_approval": task.requires_manual_approval,
                            "manual_approval": task.manual_approval.as_dict(),
                        },
                        default=str,
                    ),
                    task.rollback_strategy.value,
                    task.compensation_handler,
                ),
            )
            self._connection.commit()

    def save_flow(self, flow: ExecutionFlow) -> None:
        serialized = self._serialize_flow(flow)
        with self._lock:
            existing = self._connection.execute(
                "SELECT active_version_id, version_count, created_at FROM flows WHERE flow_id = ?",
                (flow.flow_id,),
            ).fetchone()
            active_version_id = existing["active_version_id"] if existing else None
            version_count = int(existing["version_count"]) if existing else 0
            created_at = existing["created_at"] if existing else None
            self._connection.execute(
                """
                INSERT INTO flows (
                    flow_id, state, nodes_json, edges_json, metadata_json,
                    active_version_id, version_count, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP)
                ON CONFLICT(flow_id) DO UPDATE SET
                    state = excluded.state,
                    nodes_json = excluded.nodes_json,
                    edges_json = excluded.edges_json,
                    metadata_json = excluded.metadata_json,
                    active_version_id = COALESCE(excluded.active_version_id, flows.active_version_id),
                    version_count = CASE
                        WHEN excluded.version_count > 0 THEN excluded.version_count
                        ELSE flows.version_count
                    END,
                    created_at = COALESCE(flows.created_at, excluded.created_at),
                    updated_at = excluded.updated_at
                """,
                (
                    flow.flow_id,
                    flow.state.value,
                    serialized["nodes_json"],
                    serialized["edges_json"],
                    serialized["metadata_json"],
                    active_version_id,
                    version_count,
                    created_at,
                ),
            )
            self._connection.commit()

    def create_flow_version(
        self,
        flow: ExecutionFlow,
        *,
        created_by: str | None = None,
        change_reason: str | None = None,
        parent_version_id: int | None = None,
        planner_generated: bool = False,
        security_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        serialized = self._serialize_flow(flow)
        security_payload = json.dumps(security_report or {}, default=str)
        version_hash = self._compute_version_hash(
            serialized["nodes_json"],
            serialized["edges_json"],
            serialized["metadata_json"],
        )
        with self._lock:
            existing = self._connection.execute(
                "SELECT active_version_id, version_count, created_at FROM flows WHERE flow_id = ?",
                (flow.flow_id,),
            ).fetchone()
            current_active_version_id = (
                int(existing["active_version_id"])
                if existing and existing["active_version_id"] is not None
                else None
            )
            version_number = (int(existing["version_count"]) if existing else 0) + 1
            version_id = self.next_id("flow_version")
            self._connection.execute(
                """
                INSERT INTO flow_versions (
                    version_id, flow_id, version_number, state, nodes_json, edges_json, metadata_json,
                    created_at, created_by, change_reason, parent_version_id, planner_generated,
                    security_report_json, version_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    flow.flow_id,
                    version_number,
                    flow.state.value,
                    serialized["nodes_json"],
                    serialized["edges_json"],
                    serialized["metadata_json"],
                    created_by,
                    change_reason,
                    parent_version_id if parent_version_id is not None else current_active_version_id,
                    1 if planner_generated else 0,
                    security_payload,
                    version_hash,
                ),
            )
            self._connection.execute(
                """
                INSERT INTO flows (
                    flow_id, state, nodes_json, edges_json, metadata_json,
                    active_version_id, version_count, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP)
                ON CONFLICT(flow_id) DO UPDATE SET
                    state = excluded.state,
                    nodes_json = excluded.nodes_json,
                    edges_json = excluded.edges_json,
                    metadata_json = excluded.metadata_json,
                    active_version_id = excluded.active_version_id,
                    version_count = excluded.version_count,
                    updated_at = excluded.updated_at
                """,
                (
                    flow.flow_id,
                    flow.state.value,
                    serialized["nodes_json"],
                    serialized["edges_json"],
                    serialized["metadata_json"],
                    version_id,
                    version_number,
                    existing["created_at"] if existing else None,
                ),
            )
            self._connection.commit()
        return {
            "version_id": version_id,
            "flow_id": flow.flow_id,
            "version_number": version_number,
            "created_by": created_by,
            "change_reason": change_reason,
            "parent_version_id": (
                parent_version_id if parent_version_id is not None else current_active_version_id
            ),
            "planner_generated": planner_generated,
            "security_report": security_report or {},
            "version_hash": version_hash,
        }

    def list_flow_versions(self, flow_id: int) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT version_id, flow_id, version_number, created_at, created_by, change_reason,
                       parent_version_id, planner_generated, security_report_json, version_hash
                FROM flow_versions
                WHERE flow_id = ?
                ORDER BY version_number ASC
                """,
                (flow_id,),
            ).fetchall()
        versions: list[dict[str, Any]] = []
        for row in rows:
            versions.append(
                {
                    "version_id": row["version_id"],
                    "flow_id": row["flow_id"],
                    "version_number": row["version_number"],
                    "created_at": row["created_at"],
                    "created_by": row["created_by"],
                    "change_reason": row["change_reason"],
                    "parent_version_id": row["parent_version_id"],
                    "planner_generated": bool(row["planner_generated"]),
                    "security_report": json.loads(row["security_report_json"] or "{}"),
                    "version_hash": row["version_hash"],
                }
            )
        return versions

    def get_flow_record(self, flow_id: int) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM flows WHERE flow_id = ?",
                (flow_id,),
            ).fetchone()
        if row is None:
            return None
        payload = self._decode_flow_row(row)
        versions = self.list_flow_versions(flow_id)
        payload["available_versions"] = versions
        payload["active_version_id"] = row["active_version_id"]
        payload["version_count"] = int(row["version_count"] or 0)
        payload["created_at"] = row["created_at"]
        active = next(
            (version for version in versions if version["version_id"] == row["active_version_id"]),
            None,
        )
        payload["version_id"] = row["active_version_id"]
        payload["version_number"] = active["version_number"] if active else None
        return payload

    def get_flow_version_record(
        self,
        flow_id: int,
        version_id: int | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            if version_id is None:
                container = self._connection.execute(
                    "SELECT active_version_id FROM flows WHERE flow_id = ?",
                    (flow_id,),
                ).fetchone()
                if container is None or container["active_version_id"] is None:
                    return None
                version_id = int(container["active_version_id"])
            row = self._connection.execute(
                """
                SELECT version_id, flow_id, version_number, state, nodes_json, edges_json, metadata_json,
                       created_at, created_by, change_reason, parent_version_id, planner_generated,
                       security_report_json, version_hash
                FROM flow_versions
                WHERE flow_id = ? AND version_id = ?
                """,
                (flow_id, version_id),
            ).fetchone()
        if row is None:
            return None
        payload = self._decode_version_row(row)
        payload["available_versions"] = self.list_flow_versions(flow_id)
        return payload

    def activate_flow_version(self, flow_id: int, version_id: int) -> dict[str, Any]:
        version_record = self.get_flow_version_record(flow_id, version_id)
        if version_record is None:
            raise KeyError(f"Unknown flow version '{version_id}' for flow '{flow_id}'")
        with self._lock:
            self._connection.execute(
                """
                UPDATE flows
                SET state = ?, nodes_json = ?, edges_json = ?, metadata_json = ?,
                    active_version_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE flow_id = ?
                """,
                (
                    version_record["state"],
                    json.dumps(version_record["nodes"], default=str),
                    json.dumps(version_record["edges"], default=str),
                    json.dumps(version_record["metadata"], default=str),
                    version_id,
                    flow_id,
                ),
            )
            self._connection.commit()
        return self.get_flow_record(flow_id) or version_record

    def save_execution(self, execution: TaskExecution, flow_id: int | None = None) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO executions (
                    execution_id, task_id, flow_id, start_time, end_time, result_json, status,
                    errors_json, attempt_count, resource_history_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(execution_id) DO UPDATE SET
                    task_id = excluded.task_id,
                    flow_id = excluded.flow_id,
                    start_time = excluded.start_time,
                    end_time = excluded.end_time,
                    result_json = excluded.result_json,
                    status = excluded.status,
                    errors_json = excluded.errors_json,
                    attempt_count = excluded.attempt_count,
                    resource_history_json = excluded.resource_history_json,
                    updated_at = excluded.updated_at
                """,
                (
                    execution.execution_id,
                    execution.task_ref.task_id,
                    flow_id,
                    execution.start_time.isoformat() if execution.start_time else None,
                    execution.end_time.isoformat() if execution.end_time else None,
                    json.dumps(execution.result, default=str) if execution.result is not None else None,
                    execution.status.value,
                    json.dumps([error.as_dict() for error in execution.errors], default=str),
                    execution.attempt_count,
                    json.dumps(execution.resource_history),
                ),
            )
            self._connection.commit()

    def save_execution_metric(
        self,
        *,
        execution: TaskExecution,
        flow_id: int | None,
        node_id: str,
        handler_name: str,
        telemetry: dict[str, Any] | None = None,
    ) -> None:
        telemetry_payload = dict(telemetry or {})
        prompt_tokens = telemetry_payload.get("prompt_tokens")
        completion_tokens = telemetry_payload.get("completion_tokens")
        estimated_cost = telemetry_payload.get("estimated_cost")
        model_name = telemetry_payload.get("model_name")
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO execution_metrics (
                    metric_id, execution_id, flow_id, node_id, handler_name, status, latency_ms,
                    attempt_count, prompt_tokens, completion_tokens, estimated_cost, model_name,
                    resource_history_json, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    self.next_id("execution_metric"),
                    execution.execution_id,
                    flow_id,
                    node_id,
                    handler_name,
                    execution.status.value,
                    execution.latency_ms,
                    execution.attempt_count,
                    int(prompt_tokens) if prompt_tokens not in {None, ""} else None,
                    int(completion_tokens) if completion_tokens not in {None, ""} else None,
                    float(estimated_cost) if estimated_cost not in {None, ""} else None,
                    str(model_name) if model_name not in {None, ""} else None,
                    json.dumps(execution.resource_history),
                    json.dumps(telemetry_payload, default=str),
                ),
            )
            self._connection.commit()

    def list_executions(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM executions ORDER BY execution_id ASC"
            ).fetchall()
        return [self._decode_execution_row(row) for row in rows]

    def list_execution_metrics(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT metric_id, execution_id, flow_id, node_id, handler_name, status, latency_ms,
                       attempt_count, prompt_tokens, completion_tokens, estimated_cost, model_name,
                       resource_history_json, metadata_json, created_at
                FROM execution_metrics
                ORDER BY metric_id ASC
                """
            ).fetchall()
        return [self._decode_metric_row(row) for row in rows]

    def summarize_execution_metrics(self) -> dict[str, Any]:
        with self._lock:
            handler_rows = self._connection.execute(
                """
                SELECT handler_name,
                       COUNT(*) AS execution_count,
                       SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count,
                       AVG(latency_ms) AS avg_latency_ms,
                       MAX(latency_ms) AS max_latency_ms,
                       SUM(COALESCE(prompt_tokens, 0)) AS prompt_tokens,
                       SUM(COALESCE(completion_tokens, 0)) AS completion_tokens
                FROM execution_metrics
                GROUP BY handler_name
                ORDER BY handler_name ASC
                """
            ).fetchall()
            flow_rows = self._connection.execute(
                """
                SELECT flow_id,
                       COUNT(*) AS execution_count,
                       SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count,
                       AVG(latency_ms) AS avg_latency_ms,
                       MAX(latency_ms) AS max_latency_ms
                FROM execution_metrics
                WHERE flow_id IS NOT NULL
                GROUP BY flow_id
                ORDER BY flow_id ASC
                """
            ).fetchall()
        return {
            "handlers": [
                {
                    "handler_name": row["handler_name"],
                    "execution_count": int(row["execution_count"] or 0),
                    "failed_count": int(row["failed_count"] or 0),
                    "avg_latency_ms": (
                        float(row["avg_latency_ms"]) if row["avg_latency_ms"] is not None else None
                    ),
                    "max_latency_ms": (
                        int(row["max_latency_ms"]) if row["max_latency_ms"] is not None else None
                    ),
                    "prompt_tokens": int(row["prompt_tokens"] or 0),
                    "completion_tokens": int(row["completion_tokens"] or 0),
                }
                for row in handler_rows
            ],
            "flows": [
                {
                    "flow_id": int(row["flow_id"]),
                    "execution_count": int(row["execution_count"] or 0),
                    "failed_count": int(row["failed_count"] or 0),
                    "avg_latency_ms": (
                        float(row["avg_latency_ms"]) if row["avg_latency_ms"] is not None else None
                    ),
                    "max_latency_ms": (
                        int(row["max_latency_ms"]) if row["max_latency_ms"] is not None else None
                    ),
                }
                for row in flow_rows
            ],
        }

    @staticmethod
    def _serialize_flow(flow: ExecutionFlow) -> dict[str, str]:
        nodes_json = json.dumps(
            {
                node_id: {
                    "task_id": node.task.task_id,
                    "task_status": node.task.status.value,
                    "handler_name": node.task.handler_name,
                    "assigned_agent_id": node.agent.agent_id if node.agent else None,
                    "input": node.task.input,
                    "output": node.task.output,
                    "required_capabilities": node.task.context.get("required_capabilities", []),
                    "required_resource_ids": [
                        resource.resource_id for resource in node.task.required_resources
                    ],
                    "required_resource_types": [
                        resource.type.value for resource in node.task.required_resources
                    ],
                    "retry_policy": {
                        "max_retries": node.task.retry_policy.max_retries,
                        "backoff_ms": node.task.retry_policy.backoff_ms,
                        "exponential": node.task.retry_policy.exponential,
                        "max_backoff_ms": node.task.retry_policy.max_backoff_ms,
                        "jitter_ratio": node.task.retry_policy.jitter_ratio,
                    },
                    "rollback_strategy": node.task.rollback_strategy.value,
                    "validator_rules": node.task.validator_rules,
                    "metadata": node.task.metadata,
                    "requires_manual_approval": node.task.requires_manual_approval,
                    "manual_approval": node.task.manual_approval.as_dict(),
                    "compensation_handler": node.task.compensation_handler,
                }
                for node_id, node in flow.nodes.items()
            },
            default=str,
        )
        edges_json = json.dumps(
            [
                {
                    "from_node": edge.from_node,
                    "to_node": edge.to_node,
                    "condition": edge.condition.expression,
                }
                for edge in flow.edges
            ]
        )
        metadata_json = json.dumps(flow.metadata, default=str)
        return {
            "nodes_json": nodes_json,
            "edges_json": edges_json,
            "metadata_json": metadata_json,
        }

    @staticmethod
    def _compute_version_hash(nodes_json: str, edges_json: str, metadata_json: str) -> str:
        digest = hashlib.sha256()
        digest.update(nodes_json.encode("utf-8"))
        digest.update(edges_json.encode("utf-8"))
        digest.update(metadata_json.encode("utf-8"))
        return digest.hexdigest()

    @staticmethod
    def _decode_execution_row(row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        for field in ("result_json", "errors_json", "resource_history_json"):
            if payload.get(field):
                payload[field] = json.loads(payload[field])
        return payload

    @staticmethod
    def _decode_metric_row(row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        payload["resource_history_json"] = json.loads(payload["resource_history_json"] or "[]")
        payload["metadata_json"] = json.loads(payload["metadata_json"] or "{}")
        return payload

    def _decode_version_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "flow_id": row["flow_id"],
            "version_id": row["version_id"],
            "version_number": row["version_number"],
            "state": row["state"],
            "nodes": json.loads(row["nodes_json"]),
            "edges": json.loads(row["edges_json"]),
            "metadata": json.loads(row["metadata_json"]),
            "created_at": row["created_at"],
            "created_by": row["created_by"],
            "change_reason": row["change_reason"],
            "parent_version_id": row["parent_version_id"],
            "planner_generated": bool(row["planner_generated"]),
            "security_report": json.loads(row["security_report_json"] or "{}"),
            "version_hash": row["version_hash"],
        }

    def _decode_flow_row(self, row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        return {
            "flow_id": payload["flow_id"],
            "state": payload["state"],
            "nodes": json.loads(payload["nodes_json"]),
            "edges": json.loads(payload["edges_json"]),
            "metadata": json.loads(payload["metadata_json"]),
            "updated_at": payload["updated_at"],
        }

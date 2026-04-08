from __future__ import annotations

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
                    updated_at TEXT NOT NULL
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
                """
            )
            self._connection.commit()

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
                    json.dumps(task.metadata, default=str),
                    task.rollback_strategy.value,
                    task.compensation_handler,
                ),
            )
            self._connection.commit()

    def save_flow(self, flow: ExecutionFlow) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO flows (flow_id, state, nodes_json, edges_json, metadata_json, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(flow_id) DO UPDATE SET
                    state = excluded.state,
                    nodes_json = excluded.nodes_json,
                    edges_json = excluded.edges_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    flow.flow_id,
                    flow.state.value,
                    json.dumps(
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
                                "task_metadata": node.task.metadata,
                                "flow_node_metadata": node.metadata,
                                "compensation_handler": node.task.compensation_handler,
                            }
                            for node_id, node in flow.nodes.items()
                        },
                        default=str,
                    ),
                    json.dumps(
                        [
                            {
                                "from_node": edge.from_node,
                                "to_node": edge.to_node,
                                "condition": edge.condition.expression,
                            }
                            for edge in flow.edges
                        ]
                    ),
                    json.dumps(flow.metadata, default=str),
                ),
            )
            self._connection.commit()

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

    def list_executions(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM executions ORDER BY execution_id ASC"
            ).fetchall()
        return [self._decode_execution_row(row) for row in rows]

    def get_flow_record(self, flow_id: int) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM flows WHERE flow_id = ?",
                (flow_id,),
            ).fetchone()
        return self._decode_flow_row(row) if row else None

    @staticmethod
    def _decode_execution_row(row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        for field in ("result_json", "errors_json", "resource_history_json"):
            if payload.get(field):
                payload[field] = json.loads(payload[field])
        return payload

    @staticmethod
    def _decode_flow_row(row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        return {
            "flow_id": payload["flow_id"],
            "state": payload["state"],
            "nodes": json.loads(payload["nodes_json"]),
            "edges": json.loads(payload["edges_json"]),
            "metadata": json.loads(payload["metadata_json"]),
            "updated_at": payload["updated_at"],
        }

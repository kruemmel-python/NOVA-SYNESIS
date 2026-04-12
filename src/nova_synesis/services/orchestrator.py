from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from nova_synesis.communication.adapters import CommunicationAdapterFactory
from nova_synesis.config import Settings
from nova_synesis.domain.models import (
    Agent,
    Capability,
    ExecutionFlow,
    Intent,
    MemoryType,
    ProtocolType,
    Resource,
    ResourceType,
)
from nova_synesis.memory.systems import MemoryManager, MemorySystemFactory
from nova_synesis.persistence.sqlite_repository import SQLiteRepository
from nova_synesis.planning.lit_planner import LiteRTPlanner, PlannerCatalog
from nova_synesis.planning.planner import IntentPlanner
from nova_synesis.resources.manager import ResourceManager
from nova_synesis.runtime.engine import ExecutionContext, FlowExecutor, TaskExecutor
from nova_synesis.runtime.handlers import (
    TaskHandlerRegistry,
    preview_accounts_receivable_letter_draft,
    register_default_handlers,
)
from nova_synesis.security import SemanticFirewall

_PLANNER_BOOTSTRAP_AGENT = "nova-system-agent"
_PLANNER_BOOTSTRAP_LONG_TERM = "planner-scratch"
_PLANNER_BOOTSTRAP_VECTOR = "planner-vector"


class OrchestratorService:
    def __init__(
        self,
        settings: Settings,
        repository: SQLiteRepository,
        planner: IntentPlanner,
        resource_manager: ResourceManager,
        memory_manager: MemoryManager,
        handler_registry: TaskHandlerRegistry,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.planner = planner
        self.resource_manager = resource_manager
        self.memory_manager = memory_manager
        self.handler_registry = handler_registry
        self.agents: dict[int, Agent] = {}
        self.flows: dict[int, ExecutionFlow] = {}
        self._flow_subscribers: dict[int, set[asyncio.Queue[dict[str, Any]]]] = {}
        self.lit_planner = LiteRTPlanner(settings)
        self.semantic_firewall = SemanticFirewall(settings)

        register_default_handlers(self.handler_registry)

        execution_context = ExecutionContext(
            settings=self.settings,
            repository=self.repository,
            resource_manager=self.resource_manager,
            memory_manager=self.memory_manager,
            handler_registry=self.handler_registry,
            agents=self.agents,
            flows=self.flows,
            working_directory=Path(self.settings.working_directory).resolve(),
            max_flow_concurrency=self.settings.max_flow_concurrency,
            event_publisher=self.publish_flow_event,
        )
        self.task_executor = TaskExecutor(execution_context)
        self.flow_executor = FlowExecutor(execution_context, self.task_executor)

    def register_handler(
        self,
        name: str,
        handler: Callable[[dict[str, Any]], Any],
        *,
        certificate: dict[str, Any] | None = None,
    ) -> None:
        self.handler_registry.register(name, handler, certificate=certificate)

    def list_handlers(self) -> list[dict[str, Any]]:
        return self.handler_registry.describe()

    def issue_handler_certificate(
        self,
        handler_name: str,
        expires_in_hours: int | None = None,
    ) -> dict[str, Any]:
        return self.handler_registry.issue_certificate(
            handler_name,
            expires_in_hours=expires_in_hours,
        )

    def register_memory_system(
        self,
        memory_id: str,
        memory_type: MemoryType,
        backend: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_backend = backend or self._default_memory_backend(memory_type)
        system = MemorySystemFactory.create(
            memory_id=memory_id,
            memory_type=memory_type,
            backend=resolved_backend,
            config=config,
        )
        self.memory_manager.register(system)
        self.repository.save_memory_system(system)
        return self._serialize_memory_system(system)

    def register_agent(
        self,
        name: str,
        role: str,
        capabilities: list[dict[str, Any]] | None = None,
        communication: dict[str, Any] | None = None,
        memory_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        firewall_report = self.semantic_firewall.validate_agent_registration(
            name=name,
            capabilities=capabilities or [],
            communication=communication,
            existing_agents=self.list_agents(),
        )
        firewall_report.ensure_allowed()

        comms = None
        if communication is not None:
            comms = CommunicationAdapterFactory.create(
                protocol=ProtocolType(communication["protocol"]),
                endpoint=str(communication["endpoint"]),
                config=dict(communication.get("config", {})),
            )
        agent = Agent(
            agent_id=self.repository.next_id("agent"),
            name=name,
            role=role,
            capabilities=[
                Capability(
                    name=item["name"],
                    type=item["type"],
                    constraints=dict(item.get("constraints", {})),
                )
                for item in capabilities or []
            ],
            comms=comms,
            memory_refs=[self.memory_manager.get(memory_id) for memory_id in memory_ids or []],
        )
        self.agents[agent.agent_id] = agent
        self.repository.save_agent(agent)
        return self._serialize_agent(agent)

    def register_resource(
        self,
        resource_type: ResourceType,
        endpoint: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resource = Resource(
            resource_id=self.repository.next_id("resource"),
            type=resource_type,
            endpoint=endpoint,
            metadata=dict(metadata or {}),
        )
        self.resource_manager.register(resource)
        self.repository.save_resource(resource)
        return self._serialize_resource(resource)

    def create_intent(self, goal: str, constraints: dict[str, Any], priority: int = 1) -> Intent:
        intent = Intent(
            intent_id=self.repository.next_id("intent"),
            goal=goal,
            constraints=dict(constraints),
            priority=priority,
        )
        self.repository.save_intent(intent)
        return intent

    def create_flow(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.validate_flow_request(nodes=nodes, edges=edges or [], metadata=metadata or {}).ensure_allowed()
        intent = self.create_intent(
            goal="Direct flow creation",
            constraints={
                "tasks": nodes,
                "edges": edges or [],
                "flow_metadata": metadata or {},
            },
        )
        flow = self.planner.plan_intent(
            intent=intent,
            agents=list(self.agents.values()),
            resources=self.resource_manager.list(),
            task_id_allocator=lambda: self.repository.next_id("task"),
            flow_id_allocator=lambda: self.repository.next_id("flow"),
        )
        self._persist_flow(flow)
        self.flows[flow.flow_id] = flow
        self._schedule_publish(flow.flow_id, "flow.created", self._serialize_flow(flow))
        return self._serialize_flow(flow)

    def plan_intent(
        self,
        goal: str,
        constraints: dict[str, Any],
        priority: int = 1,
    ) -> dict[str, Any]:
        intent = self.create_intent(goal=goal, constraints=constraints, priority=priority)
        flow = self.planner.plan_intent(
            intent=intent,
            agents=list(self.agents.values()),
            resources=self.resource_manager.list(),
            task_id_allocator=lambda: self.repository.next_id("task"),
            flow_id_allocator=lambda: self.repository.next_id("flow"),
        )
        flow_snapshot = self._serialize_flow(flow)
        self.validate_flow_request(
            nodes=self._snapshot_nodes_to_specs(flow_snapshot),
            edges=flow_snapshot["edges"],
            metadata=flow_snapshot.get("metadata", {}),
        ).ensure_allowed()
        self._persist_flow(flow)
        self.flows[flow.flow_id] = flow
        self._schedule_publish(flow.flow_id, "flow.created", flow_snapshot)
        return flow_snapshot

    async def execute_intent(
        self,
        goal: str,
        constraints: dict[str, Any],
        priority: int = 1,
    ) -> dict[str, Any]:
        flow_snapshot = self.plan_intent(goal=goal, constraints=constraints, priority=priority)
        return await self.run_flow(flow_snapshot["flow_id"])

    async def run_flow(self, flow_id: int) -> dict[str, Any]:
        if flow_id not in self.flows:
            raise KeyError(f"Unknown flow '{flow_id}'")
        flow_snapshot = self._serialize_flow(self.flows[flow_id])
        self.validate_flow_request(
            nodes=self._snapshot_nodes_to_specs(flow_snapshot),
            edges=flow_snapshot.get("edges", []),
            metadata=flow_snapshot.get("metadata", {}),
            phase="run",
        ).ensure_allowed()
        snapshot = await self.flow_executor.run_flow(self.flows[flow_id])
        self.repository.save_flow(self.flows[flow_id])
        return snapshot

    def pause_flow(self, flow_id: int) -> dict[str, Any]:
        if flow_id not in self.flows:
            raise KeyError(f"Unknown flow '{flow_id}'")
        self.flows[flow_id].pause()
        self.repository.save_flow(self.flows[flow_id])
        return self._serialize_flow(self.flows[flow_id])

    def get_flow(self, flow_id: int) -> dict[str, Any]:
        if flow_id in self.flows:
            return self._serialize_flow(self.flows[flow_id])
        record = self.repository.get_flow_record(flow_id)
        if record is None:
            raise KeyError(f"Unknown flow '{flow_id}'")
        return record

    def list_agents(self) -> list[dict[str, Any]]:
        return [self._serialize_agent(agent) for agent in self.agents.values()]

    def list_resources(self) -> list[dict[str, Any]]:
        return [self._serialize_resource(resource) for resource in self.resource_manager.list()]

    def list_memory_systems(self) -> list[dict[str, Any]]:
        return [self._serialize_memory_system(system) for system in self.memory_manager.list()]

    def list_executions(self) -> list[dict[str, Any]]:
        return self.repository.list_executions()

    def get_llm_planner_status(self) -> dict[str, Any]:
        return self.lit_planner.status()

    def approve_flow_node(
        self,
        flow_id: int,
        node_id: str,
        approved_by: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        flow = self.flows.get(flow_id)
        if flow is None:
            raise KeyError(f"Unknown flow '{flow_id}'")
        if node_id not in flow.nodes:
            raise KeyError(f"Unknown node '{node_id}' in flow '{flow_id}'")
        task = flow.nodes[node_id].task
        task.manual_approval.approve(approved_by=approved_by, reason=reason)
        self.repository.save_task(task)
        self.repository.save_flow(flow)
        snapshot = self._serialize_flow(flow)
        self._schedule_publish(flow_id, "node.approval.updated", snapshot)
        return snapshot

    def revoke_flow_node_approval(
        self,
        flow_id: int,
        node_id: str,
        revoked_by: str | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        flow = self.flows.get(flow_id)
        if flow is None:
            raise KeyError(f"Unknown flow '{flow_id}'")
        if node_id not in flow.nodes:
            raise KeyError(f"Unknown node '{node_id}' in flow '{flow_id}'")
        task = flow.nodes[node_id].task
        task.manual_approval.revoke(revoked_by=revoked_by, reason=reason)
        self.repository.save_task(task)
        self.repository.save_flow(flow)
        snapshot = self._serialize_flow(flow)
        self._schedule_publish(flow_id, "node.approval.revoked", snapshot)
        return snapshot

    async def generate_flow_with_llm(
        self,
        prompt: str,
        current_flow: dict[str, Any] | None = None,
        max_nodes: int = 12,
    ) -> dict[str, Any]:
        bootstrap_warnings = self._ensure_llm_planner_bootstrap()
        result = await asyncio.to_thread(
            self.lit_planner.generate_flow_request,
            prompt,
            self._build_planner_catalog(),
            current_flow,
            max_nodes,
        )
        security_report = self.validate_flow_request(
            nodes=result.flow_request["nodes"],
            edges=result.flow_request.get("edges", []),
            metadata=result.flow_request.get("metadata", {}),
            planner_generated=True,
            phase="planner",
        )
        security_report.ensure_allowed()
        
        # Sicherstellen, dass die gesamte Antwort JSON-serialisierbar ist
        response = {
            "flow_request": result.flow_request,
            "explanation": result.explanation,
            "warnings": bootstrap_warnings
            + result.warnings
            + [finding.message for finding in security_report.warnings],
            "security_report": security_report.as_dict(),
            "model_path": result.model_path,
            "backend": result.backend,
            "raw_response": result.raw_response,
        }
        # NUTZT default=str UM SETS UND DATETIMES ABZUFANGEN
        return json.loads(json.dumps(response, default=str))

    def _ensure_llm_planner_bootstrap(self) -> list[str]:
        warnings: list[str] = []
        existing_agent_names = {agent["name"].casefold() for agent in self.list_agents()}
        existing_memory_ids = {memory["memory_id"] for memory in self.list_memory_systems()}

        if _PLANNER_BOOTSTRAP_AGENT.casefold() not in existing_agent_names:
            self.register_agent(
                name=_PLANNER_BOOTSTRAP_AGENT,
                role="system",
                capabilities=[
                    {"name": "http", "type": "network"},
                    {"name": "memory", "type": "storage"},
                    {"name": "messaging", "type": "dispatch"},
                    {"name": "filesystem", "type": "io"},
                    {"name": "rendering", "type": "transform"},
                    {"name": "serialization", "type": "transform"},
                    {"name": "search", "type": "research"},
                    {"name": "classification", "type": "analysis"},
                    {"name": "generate_embedding", "type": "transform"},
                ],
                communication={
                    "protocol": ProtocolType.MESSAGE_QUEUE.value,
                    "endpoint": "queue://nova-system-agent",
                    "config": {"planner_bootstrap": True},
                },
            )
            warnings.append(f"Planner bootstrap registered agent '{_PLANNER_BOOTSTRAP_AGENT}'.")

        if _PLANNER_BOOTSTRAP_LONG_TERM not in existing_memory_ids:
            self.register_memory_system(
                memory_id=_PLANNER_BOOTSTRAP_LONG_TERM,
                memory_type=MemoryType.LONG_TERM,
                config={"planner_visible": True, "allow_untrusted_ingest": True, "bootstrap": True},
            )
            warnings.append(f"Planner bootstrap registered memory '{_PLANNER_BOOTSTRAP_LONG_TERM}'.")

        if _PLANNER_BOOTSTRAP_VECTOR not in existing_memory_ids:
            self.register_memory_system(
                memory_id=_PLANNER_BOOTSTRAP_VECTOR,
                memory_type=MemoryType.VECTOR,
                config={"planner_visible": True, "allow_untrusted_ingest": True, "bootstrap": True},
            )
            warnings.append(f"Planner bootstrap registered memory '{_PLANNER_BOOTSTRAP_VECTOR}'.")

        return warnings

    def validate_flow_request(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        planner_generated: bool = False,
        phase: str = "create",
    ) -> Any:
        return self.semantic_firewall.validate_flow_request(
            nodes=nodes,
            edges=edges or [],
            metadata=metadata or {},
            handlers=self.list_handlers(),
            agents=self.list_agents(),
            resources=self.list_resources(),
            memory_systems=self.list_memory_systems(),
            planner_generated=planner_generated,
            phase=phase,
        )

    def preview_accounts_receivable_draft(
        self,
        extract_input: dict[str, Any],
        generate_input: dict[str, Any],
        customer_index: int = 0,
    ) -> dict[str, Any]:
        return preview_accounts_receivable_letter_draft(
            settings=self.settings,
            working_directory=Path(self.settings.working_directory).resolve(),
            extract_input=extract_input,
            generate_input=generate_input,
            customer_index=customer_index,
        )

    async def shutdown(self) -> None:
        for agent in self.agents.values():
            if agent.comms is not None:
                await agent.comms.close()
        await self.memory_manager.persist_all()

    def subscribe_flow(self, flow_id: int) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=64)
        self._flow_subscribers.setdefault(flow_id, set()).add(queue)
        return queue

    def unsubscribe_flow(self, flow_id: int, queue: asyncio.Queue[dict[str, Any]]) -> None:
        subscribers = self._flow_subscribers.get(flow_id)
        if not subscribers:
            return
        subscribers.discard(queue)
        if not subscribers:
            self._flow_subscribers.pop(flow_id, None)

    async def publish_flow_event(
        self,
        flow_id: int,
        event_type: str,
        snapshot: dict[str, Any],
    ) -> None:
        subscribers = list(self._flow_subscribers.get(flow_id, set()))
        if not subscribers:
            return
        # Sicherstellen, dass das Event-Payload JSON-konform ist
        event = json.loads(json.dumps({
            "type": event_type,
            "flow_id": flow_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "snapshot": snapshot,
        }, default=str))
        
        for queue in subscribers:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            await queue.put(event)

    def _persist_flow(self, flow: ExecutionFlow) -> None:
        for node in flow.nodes.values():
            self.repository.save_task(node.task)
        self.repository.save_flow(flow)

    def _schedule_publish(self, flow_id: int, event_type: str, snapshot: dict[str, Any]) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        loop.create_task(self.publish_flow_event(flow_id, event_type, snapshot))

    def _build_planner_catalog(self) -> PlannerCatalog:
        return PlannerCatalog(
            handlers=self.handler_registry.names(trusted_only=True),
            agents=self.list_agents(),
            resources=[
                r for r in self.list_resources() 
                if bool(r.get("metadata", {}).get("planner_visible", True)) 
                and not bool(r.get("metadata", {}).get("sensitive", False))
            ],
            memory_systems=[
                m for m in self.list_memory_systems() 
                if bool(m.get("config", {}).get("planner_visible", True)) 
                and not bool(m.get("config", {}).get("sensitive", False))
            ],
        )

    @staticmethod
    def _snapshot_nodes_to_specs(flow_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        nodes = []
        for node_id, node in flow_snapshot.get("nodes", {}).items():
            nodes.append({
                "node_id": node_id,
                "handler_name": node.get("handler_name"),
                "input": node.get("input"),
                "required_capabilities": node.get("required_capabilities", []),
                "required_resource_ids": node.get("required_resource_ids", []),
                "required_resource_types": node.get("required_resource_types", []),
                "retry_policy": node.get("retry_policy", {}),
                "rollback_strategy": node.get("rollback_strategy", "FAIL_FAST"),
                "validator_rules": node.get("validator_rules", {}),
                "metadata": node.get("metadata", {}),
                "requires_manual_approval": node.get("requires_manual_approval", False),
                "manual_approval": node.get("manual_approval", {}),
                "compensation_handler": node.get("compensation_handler"),
                "dependencies": [e["from_node"] for e in flow_snapshot.get("edges", []) if e.get("to_node") == node_id],
                "conditions": {e["from_node"]: e.get("condition", "True") for e in flow_snapshot.get("edges", []) if e.get("to_node") == node_id},
                "preferred_agent_id": node.get("assigned_agent_id"),
            })
        return nodes

    def _default_memory_backend(self, memory_type: MemoryType) -> str:
        if memory_type == MemoryType.SHORT_TERM:
            return self.settings.default_short_term_backend
        if memory_type == MemoryType.LONG_TERM:
            return self.settings.default_long_term_backend
        if memory_type == MemoryType.VECTOR:
            return self.settings.default_vector_backend
        raise ValueError(f"Unsupported memory type '{memory_type}'")

    @staticmethod
    def _serialize_agent(agent: Agent) -> dict[str, Any]:
        return json.loads(json.dumps({
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "state": agent.state.value,
            "capabilities": [{"name": c.name, "type": c.type, "constraints": c.constraints} for c in agent.capabilities],
            "communication": {"protocol": agent.comms.protocol.value, "endpoint": agent.comms.endpoint, "config": agent.comms.config} if agent.comms else None,
            "memory_refs": [m.memory_id for m in agent.memory_refs],
        }, default=str))

    @staticmethod
    def _serialize_resource(resource: Resource) -> dict[str, Any]:
        return json.loads(json.dumps({
            "resource_id": resource.resource_id,
            "type": resource.type.value,
            "endpoint": resource.endpoint,
            "metadata": resource.metadata,
            "state": resource.state.value,
        }, default=str))

    @staticmethod
    def _serialize_memory_system(system: Any) -> dict[str, Any]:
        return json.loads(json.dumps({
            "memory_id": system.memory_id,
            "type": system.type.value,
            "backend": system.backend,
            "config": system.config,
        }, default=str))

    @staticmethod
    def _serialize_flow(flow: ExecutionFlow) -> dict[str, Any]:
        snapshot = flow.observe()
        # REINIGT DEN SNAPSHOT VON SETS, DATETIMES ETC.
        safe_snapshot = json.loads(json.dumps(snapshot, default=str))
        safe_snapshot["flow_id"] = flow.flow_id
        return safe_snapshot


def create_orchestrator(settings: Settings | None = None) -> OrchestratorService:
    resolved_settings = settings or Settings.from_env()
    resolved_settings.ensure_directories()
    return OrchestratorService(
        settings=resolved_settings,
        repository=SQLiteRepository(resolved_settings.database_path),
        planner=IntentPlanner(),
        resource_manager=ResourceManager(),
        memory_manager=MemoryManager(),
        handler_registry=TaskHandlerRegistry(resolved_settings),
    )
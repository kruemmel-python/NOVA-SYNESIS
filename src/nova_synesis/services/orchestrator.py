from __future__ import annotations

import asyncio
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
from nova_synesis.runtime.handlers import TaskHandlerRegistry, register_default_handlers


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

        register_default_handlers(self.handler_registry)

        execution_context = ExecutionContext(
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

    def register_handler(self, name: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        self.handler_registry.register(name, handler)

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
        self._persist_flow(flow)
        self.flows[flow.flow_id] = flow
        self._schedule_publish(flow.flow_id, "flow.created", self._serialize_flow(flow))
        return self._serialize_flow(flow)

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

    async def generate_flow_with_llm(
        self,
        prompt: str,
        current_flow: dict[str, Any] | None = None,
        max_nodes: int = 12,
    ) -> dict[str, Any]:
        result = await asyncio.to_thread(
            self.lit_planner.generate_flow_request,
            prompt,
            self._build_planner_catalog(),
            current_flow,
            max_nodes,
        )
        return {
            "flow_request": result.flow_request,
            "explanation": result.explanation,
            "warnings": result.warnings,
            "model_path": result.model_path,
            "backend": result.backend,
            "raw_response": result.raw_response,
        }

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
        event = {
            "type": event_type,
            "flow_id": flow_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "snapshot": snapshot,
        }
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
            handlers=self.handler_registry.names(),
            agents=self.list_agents(),
            resources=self.list_resources(),
            memory_systems=self.list_memory_systems(),
        )

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
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "state": agent.state.value,
            "capabilities": [
                {
                    "name": capability.name,
                    "type": capability.type,
                    "constraints": capability.constraints,
                }
                for capability in agent.capabilities
            ],
            "communication": (
                {
                    "protocol": agent.comms.protocol.value,
                    "endpoint": agent.comms.endpoint,
                    "config": agent.comms.config,
                }
                if agent.comms is not None
                else None
            ),
            "memory_refs": [memory.memory_id for memory in agent.memory_refs],
        }

    @staticmethod
    def _serialize_resource(resource: Resource) -> dict[str, Any]:
        return {
            "resource_id": resource.resource_id,
            "type": resource.type.value,
            "endpoint": resource.endpoint,
            "metadata": resource.metadata,
            "state": resource.state.value,
        }

    @staticmethod
    def _serialize_memory_system(system: Any) -> dict[str, Any]:
        return {
            "memory_id": system.memory_id,
            "type": system.type.value,
            "backend": system.backend,
            "config": system.config,
        }

    @staticmethod
    def _serialize_flow(flow: ExecutionFlow) -> dict[str, Any]:
        snapshot = flow.observe()
        snapshot["flow_id"] = flow.flow_id
        return snapshot


def create_orchestrator(settings: Settings | None = None) -> OrchestratorService:
    resolved_settings = settings or Settings.from_env()
    resolved_settings.ensure_directories()
    return OrchestratorService(
        settings=resolved_settings,
        repository=SQLiteRepository(resolved_settings.database_path),
        planner=IntentPlanner(),
        resource_manager=ResourceManager(),
        memory_manager=MemoryManager(),
        handler_registry=TaskHandlerRegistry(),
    )

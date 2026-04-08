from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from nova_synesis.config import Settings
from nova_synesis.domain.models import MemoryType, ProtocolType, ResourceType, RollbackStrategy
from nova_synesis.services.orchestrator import OrchestratorService, create_orchestrator


class CapabilityModel(BaseModel):
    name: str
    type: str
    constraints: dict[str, Any] = Field(default_factory=dict)


class CommunicationModel(BaseModel):
    protocol: ProtocolType
    endpoint: str
    config: dict[str, Any] = Field(default_factory=dict)


class AgentCreateRequest(BaseModel):
    name: str
    role: str
    capabilities: list[CapabilityModel] = Field(default_factory=list)
    communication: CommunicationModel | None = None
    memory_ids: list[str] = Field(default_factory=list)


class MemorySystemCreateRequest(BaseModel):
    memory_id: str
    type: MemoryType
    backend: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class ResourceCreateRequest(BaseModel):
    type: ResourceType
    endpoint: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetryPolicyModel(BaseModel):
    max_retries: int = 3
    backoff_ms: int = 250
    exponential: bool = True
    max_backoff_ms: int = 10_000
    jitter_ratio: float = 0.0


class ManualApprovalModel(BaseModel):
    approved: bool = False
    approved_by: str | None = None
    approved_at: str | None = None
    reason: str | None = None
    revoked_by: str | None = None
    revoked_at: str | None = None


class TaskSpecModel(BaseModel):
    node_id: str
    handler_name: str
    input: Any = None
    required_capabilities: list[str] = Field(default_factory=list)
    required_resource_ids: list[int] = Field(default_factory=list)
    required_resource_types: list[ResourceType] = Field(default_factory=list)
    retry_policy: RetryPolicyModel = Field(default_factory=RetryPolicyModel)
    rollback_strategy: RollbackStrategy = RollbackStrategy.FAIL_FAST
    validator_rules: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    requires_manual_approval: bool = False
    manual_approval: ManualApprovalModel = Field(default_factory=ManualApprovalModel)
    compensation_handler: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    conditions: dict[str, str] = Field(default_factory=dict)
    preferred_agent_id: int | None = None


class EdgeModel(BaseModel):
    from_node: str
    to_node: str
    condition: str = "True"


class FlowCreateRequest(BaseModel):
    nodes: list[TaskSpecModel]
    edges: list[EdgeModel] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntentRequest(BaseModel):
    goal: str
    constraints: dict[str, Any] = Field(default_factory=dict)
    priority: int = 1


class LLMPlannerRequest(BaseModel):
    prompt: str
    current_flow: FlowCreateRequest | None = None
    max_nodes: int = Field(default=12, ge=1, le=40)


class NodeApprovalRequest(BaseModel):
    approved_by: str = Field(min_length=1)
    reason: str | None = None


class NodeApprovalRevokeRequest(BaseModel):
    revoked_by: str | None = None
    reason: str | None = None


def create_app(
    settings: Settings | None = None,
    orchestrator: OrchestratorService | None = None,
) -> FastAPI:
    runtime = orchestrator or create_orchestrator(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await runtime.shutdown()

    app = FastAPI(title=runtime.settings.app_name, version="1.0.4", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime.settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _translate_error(exc: Exception) -> HTTPException:
        if isinstance(exc, KeyError):
            return HTTPException(status_code=404, detail=str(exc))
        return HTTPException(status_code=400, detail=str(exc))

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "agents": len(runtime.agents),
            "resources": len(runtime.resource_manager.list()),
            "memory_systems": len(runtime.memory_manager.list()),
            "handlers": runtime.handler_registry.names(),
        }

    @app.get("/handlers")
    async def list_handlers() -> dict[str, Any]:
        details = runtime.list_handlers()
        return {
            "handlers": [item["name"] for item in details],
            "details": details,
        }

    @app.get("/planner/status")
    async def planner_status() -> dict[str, Any]:
        return runtime.get_llm_planner_status()

    @app.post("/memory-systems")
    async def create_memory_system(request: MemorySystemCreateRequest) -> dict[str, Any]:
        try:
            return runtime.register_memory_system(
                memory_id=request.memory_id,
                memory_type=request.type,
                backend=request.backend,
                config=request.config,
            )
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.get("/memory-systems")
    async def list_memory_systems() -> list[dict[str, Any]]:
        return runtime.list_memory_systems()

    @app.post("/agents")
    async def create_agent(request: AgentCreateRequest) -> dict[str, Any]:
        try:
            return runtime.register_agent(
                name=request.name,
                role=request.role,
                capabilities=[item.model_dump() for item in request.capabilities],
                communication=request.communication.model_dump() if request.communication else None,
                memory_ids=request.memory_ids,
            )
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.get("/agents")
    async def list_agents() -> list[dict[str, Any]]:
        return runtime.list_agents()

    @app.post("/resources")
    async def create_resource(request: ResourceCreateRequest) -> dict[str, Any]:
        try:
            return runtime.register_resource(
                resource_type=request.type,
                endpoint=request.endpoint,
                metadata=request.metadata,
            )
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.get("/resources")
    async def list_resources() -> list[dict[str, Any]]:
        return runtime.list_resources()

    @app.post("/flows")
    async def create_flow_endpoint(request: FlowCreateRequest) -> dict[str, Any]:
        try:
            return runtime.create_flow(
                nodes=[node.model_dump(mode="json") for node in request.nodes],
                edges=[edge.model_dump(mode="json") for edge in request.edges],
                metadata=request.metadata,
            )
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.post("/flows/validate")
    async def validate_flow_endpoint(request: FlowCreateRequest) -> dict[str, Any]:
        try:
            report = runtime.validate_flow_request(
                nodes=[node.model_dump(mode="json") for node in request.nodes],
                edges=[edge.model_dump(mode="json") for edge in request.edges],
                metadata=request.metadata,
                phase="validate",
            )
            return report.as_dict()
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.get("/flows/{flow_id}")
    async def get_flow(flow_id: int) -> dict[str, Any]:
        try:
            return runtime.get_flow(flow_id)
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.post("/flows/{flow_id}/run")
    async def run_flow(flow_id: int, background: bool = False) -> dict[str, Any]:
        try:
            if background:
                asyncio.create_task(runtime.run_flow(flow_id))
                return {"flow_id": flow_id, "scheduled": True}
            return await runtime.run_flow(flow_id)
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.post("/flows/{flow_id}/pause")
    async def pause_flow(flow_id: int) -> dict[str, Any]:
        try:
            return runtime.pause_flow(flow_id)
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.post("/flows/{flow_id}/nodes/{node_id}/approval")
    async def approve_flow_node(
        flow_id: int,
        node_id: str,
        request: NodeApprovalRequest,
    ) -> dict[str, Any]:
        try:
            return runtime.approve_flow_node(
                flow_id=flow_id,
                node_id=node_id,
                approved_by=request.approved_by,
                reason=request.reason,
            )
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.delete("/flows/{flow_id}/nodes/{node_id}/approval")
    async def revoke_flow_node_approval(
        flow_id: int,
        node_id: str,
        request: NodeApprovalRevokeRequest,
    ) -> dict[str, Any]:
        try:
            return runtime.revoke_flow_node_approval(
                flow_id=flow_id,
                node_id=node_id,
                revoked_by=request.revoked_by,
                reason=request.reason,
            )
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.post("/intents/plan")
    async def plan_intent(request: IntentRequest) -> dict[str, Any]:
        try:
            return runtime.plan_intent(
                goal=request.goal,
                constraints=request.constraints,
                priority=request.priority,
            )
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.post("/intents/execute")
    async def execute_intent(request: IntentRequest) -> dict[str, Any]:
        try:
            return await runtime.execute_intent(
                goal=request.goal,
                constraints=request.constraints,
                priority=request.priority,
            )
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.post("/planner/generate-flow")
    async def generate_flow_with_llm(request: LLMPlannerRequest) -> dict[str, Any]:
        try:
            return await runtime.generate_flow_with_llm(
                prompt=request.prompt,
                current_flow=request.current_flow.model_dump(mode="json")
                if request.current_flow
                else None,
                max_nodes=request.max_nodes,
            )
        except Exception as exc:
            raise _translate_error(exc) from exc

    @app.get("/executions")
    async def list_executions() -> list[dict[str, Any]]:
        return runtime.list_executions()

    @app.websocket("/ws/flows/{flow_id}")
    async def flow_events(websocket: WebSocket, flow_id: int) -> None:
        await websocket.accept()
        try:
            snapshot = runtime.get_flow(flow_id)
        except KeyError:
            await websocket.send_json(
                {
                    "type": "flow.not_found",
                    "flow_id": flow_id,
                    "detail": f"Unknown flow '{flow_id}'",
                }
            )
            await websocket.close(code=1008)
            return

        queue = runtime.subscribe_flow(flow_id)
        await websocket.send_json(
            {
                "type": "flow.snapshot",
                "flow_id": flow_id,
                "snapshot": snapshot,
            }
        )

        disconnect_task = asyncio.create_task(websocket.receive())
        queue_task: asyncio.Task[dict[str, Any]] | None = None

        try:
            while True:
                queue_task = asyncio.create_task(queue.get())
                done, pending = await asyncio.wait(
                    {disconnect_task, queue_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )

                if disconnect_task in done:
                    try:
                        message = disconnect_task.result()
                    except WebSocketDisconnect:
                        break
                    if message.get("type") == "websocket.disconnect":
                        break
                    disconnect_task = asyncio.create_task(websocket.receive())

                if queue_task in done:
                    await websocket.send_json(queue_task.result())
                    queue_task = None

                if queue_task in pending:
                    queue_task.cancel()
                    queue_task = None
        finally:
            runtime.unsubscribe_flow(flow_id, queue)
            if queue_task is not None:
                queue_task.cancel()
            disconnect_task.cancel()

    return app

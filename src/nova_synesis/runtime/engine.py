from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nova_synesis.domain.models import (
    AgentState,
    ErrorEvent,
    ExecutionFlow,
    ExecutionStatus,
    FlowState,
    HumanInputResponse,
    RollbackStrategy,
    Task,
    TaskExecution,
    TaskStatus,
    maybe_await,
    safe_evaluate,
)
from nova_synesis.config import Settings
from nova_synesis.memory.systems import MemoryManager
from nova_synesis.persistence.sqlite_repository import SQLiteRepository
from nova_synesis.resources.manager import ResourceManager
from nova_synesis.runtime.handlers import HumanInputRequiredError, TaskHandlerRegistry

_TEMPLATE_PATTERN = re.compile(r"\{\{\s*(.+?)\s*\}\}")


@dataclass(slots=True)
class ExecutionContext:
    settings: Settings
    repository: SQLiteRepository
    resource_manager: ResourceManager
    memory_manager: MemoryManager
    handler_registry: TaskHandlerRegistry
    agents: dict[int, Any]
    flows: dict[int, ExecutionFlow]
    working_directory: Path
    orchestrator: Any | None = None
    max_flow_concurrency: int = 4
    event_publisher: Callable[[int, str, dict[str, Any]], Awaitable[None] | None] | None = None


def resolve_templates(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        matches = list(_TEMPLATE_PATTERN.finditer(value))
        if not matches:
            return value
        if len(matches) == 1 and matches[0].span() == (0, len(value)):
            return safe_evaluate(matches[0].group(1), context)
        rendered = value
        for match in matches:
            replacement = safe_evaluate(match.group(1), context)
            rendered = rendered.replace(match.group(0), str(replacement))
        return rendered
    if isinstance(value, list):
        return [resolve_templates(item, context) for item in value]
    if isinstance(value, tuple):
        return tuple(resolve_templates(item, context) for item in value)
    if isinstance(value, dict):
        if "$ref" in value and len(value) == 1:
            return safe_evaluate(value["$ref"], context)
        return {key: resolve_templates(item, context) for key, item in value.items()}
    return value


class TaskExecutor:
    def __init__(self, context: ExecutionContext) -> None:
        self.context = context

    async def execute_task(
        self,
        task: Task,
        flow: ExecutionFlow,
        flow_results: dict[str, Any],
        node_id: str,
    ) -> TaskExecution:
        execution = TaskExecution(
            execution_id=self.context.repository.next_id("execution"),
            task_ref=task,
        )
        execution.start()
        self.context.repository.save_task(task)
        self.context.repository.save_execution(execution, flow.flow_id)
        await self._publish_task_event(flow.flow_id, "node.started", flow.observe())

        current_resources = list(task.required_resources)
        prepared_input: Any = task.input
        handler_context: dict[str, Any] = {}
        max_attempts = task.retry_policy.max_retries + 1

        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                execution.retry()
            execution.attempt_count = attempt
            acquired_resources = []
            try:
                await task.execute()
                acquired_resources = await self.context.resource_manager.acquire_many(current_resources)
                execution.resource_history.extend([resource.resource_id for resource in acquired_resources])

                runtime_view = {
                    "results": flow_results,
                    "node_id": node_id,
                    "flow": {
                        "flow_id": flow.flow_id,
                        "state": flow.state.value,
                        "version_id": flow.metadata.get("version_id"),
                    },
                }
                prepared_input = resolve_templates(task.input, runtime_view)

                perception = None
                decision = None
                action = None
                if task.assigned_agent is not None:
                    perception = await task.assigned_agent.perceive(prepared_input)
                    decision = await task.assigned_agent.decide(
                        {
                            "required_capabilities": task.context.get("required_capabilities", []),
                            "task": task,
                            "results": flow_results,
                        }
                    )
                    if not decision.get("selected", True):
                        raise RuntimeError(
                            f"Agent '{task.assigned_agent.name}' cannot satisfy task {task.task_id}"
                        )
                    action = await task.assigned_agent.act(task)

                handler_context = {
                    "input": prepared_input,
                    "settings": self.context.settings,
                    "task": task,
                    "node_id": node_id,
                    "flow": flow,
                    "results": flow_results,
                    "execution": execution,
                    "agent": task.assigned_agent,
                    "agents": self.context.agents,
                    "resources": acquired_resources,
                    "resource_manager": self.context.resource_manager,
                    "memory_manager": self.context.memory_manager,
                    "repository": self.context.repository,
                    "working_directory": self.context.working_directory,
                    "orchestrator": self.context.orchestrator,
                    "perception": perception,
                    "decision": decision,
                    "action": action,
                }
                result = await self.context.handler_registry.execute(task.handler_name, handler_context)
                task.validate(result)
                execution.finish(result)
                if task.assigned_agent is not None:
                    task.assigned_agent.state = AgentState.IDLE
                self.context.repository.save_task(task)
                self.context.repository.save_execution(execution, flow.flow_id)
                self.context.repository.save_execution_metric(
                    execution=execution,
                    flow_id=flow.flow_id,
                    node_id=node_id,
                    handler_name=task.handler_name,
                    telemetry=self._extract_execution_telemetry(result),
                )
                await self._publish_task_event(flow.flow_id, "node.completed", flow.observe())
                return execution
            except HumanInputRequiredError as exc:
                execution.wait_for_input(exc.request)
                if task.assigned_agent is not None:
                    task.assigned_agent.state = AgentState.WAITING
                self.context.repository.save_task(task)
                self.context.repository.save_execution(execution, flow.flow_id)
                self.context.repository.save_execution_metric(
                    execution=execution,
                    flow_id=flow.flow_id,
                    node_id=node_id,
                    handler_name=task.handler_name,
                    telemetry={},
                )
                await self._publish_task_event(flow.flow_id, "node.waiting_for_input", flow.observe())
                return execution
            except Exception as exc:
                if task.assigned_agent is not None:
                    task.assigned_agent.state = AgentState.ERROR

                error = ErrorEvent(
                    type=exc.__class__.__name__,
                    message=str(exc),
                    context={
                        "task_id": task.task_id,
                        "node_id": node_id,
                        "attempt": attempt,
                        "handler_name": task.handler_name,
                    },
                )
                execution.record_error(error)
                self.context.repository.save_task(task)
                self.context.repository.save_execution(execution, flow.flow_id)
                self.context.repository.save_execution_metric(
                    execution=execution,
                    flow_id=flow.flow_id,
                    node_id=node_id,
                    handler_name=task.handler_name,
                    telemetry={},
                )
                await self._publish_task_event(flow.flow_id, "node.failed", flow.observe())

                should_retry = (
                    task.rollback_strategy in {RollbackStrategy.RETRY, RollbackStrategy.FALLBACK_RESOURCE}
                    and attempt < max_attempts
                )

                if task.rollback_strategy == RollbackStrategy.FAIL_FAST:
                    should_retry = False

                if task.rollback_strategy == RollbackStrategy.FALLBACK_RESOURCE:
                    fallback_resources = self.context.resource_manager.find_fallback_resources(current_resources)
                    if [resource.resource_id for resource in fallback_resources] != [
                        resource.resource_id for resource in current_resources
                    ]:
                        current_resources = fallback_resources

                if should_retry:
                    await asyncio.sleep(task.retry_policy.next_delay(attempt))
                    continue

                if (
                    task.rollback_strategy == RollbackStrategy.COMPENSATE
                    and task.compensation_handler is not None
                ):
                    await self.context.handler_registry.execute(
                        task.compensation_handler,
                        {
                            **handler_context,
                            "input": task.metadata.get("compensation_input", prepared_input),
                            "failure": error.as_dict(),
                        },
                    )

                execution.rollback(task.rollback_strategy)
                self.context.repository.save_execution(execution, flow.flow_id)
                await self._publish_task_event(flow.flow_id, "node.rolled_back", flow.observe())
                raise
            finally:
                await self.context.resource_manager.release_many(acquired_resources)

        execution.status = ExecutionStatus.FAILED
        self.context.repository.save_execution(execution, flow.flow_id)
        return execution

    @staticmethod
    def _extract_execution_telemetry(result: Any) -> dict[str, Any]:
        if not isinstance(result, dict):
            return {}
        telemetry = result.get("_telemetry")
        if isinstance(telemetry, dict):
            return dict(telemetry)
        return {}

    async def _publish_task_event(
        self,
        flow_id: int,
        event_type: str,
        snapshot: dict[str, Any],
    ) -> None:
        if self.context.event_publisher is None:
            return
        await maybe_await(self.context.event_publisher(flow_id, event_type, snapshot))


class FlowExecutor:
    def __init__(self, context: ExecutionContext, task_executor: TaskExecutor) -> None:
        self.context = context
        self.task_executor = task_executor

    async def run_flow(self, flow: ExecutionFlow) -> dict[str, Any]:
        flow.state = FlowState.RUNNING
        flow.metadata.setdefault("results", {})
        flow.metadata.pop("pause_requested", None)
        waiting_for_input = flow.metadata.get("waiting_for_input", {})
        completed: set[str] = set(flow.metadata.get("completed_nodes", []))
        blocked: set[str] = set(flow.metadata.get("blocked_nodes", []))
        failed: dict[str, str] = dict(flow.metadata.get("failed_nodes", {}))
        for node_id, node in flow.nodes.items():
            if node.task.status == TaskStatus.SUCCESS and node_id in flow.metadata["results"]:
                completed.add(node_id)
        pending = {
            node_id
            for node_id in flow.nodes.keys()
            if node_id not in completed and node_id not in blocked and node_id not in failed
        }

        self.context.flows[flow.flow_id] = flow
        self.context.repository.save_flow(flow)
        await self._publish_snapshot(flow, completed, blocked, failed, "flow.started")

        while pending:
            if flow.metadata.get("pause_requested"):
                flow.state = FlowState.PAUSED
                self.context.repository.save_flow(flow)
                snapshot = self._snapshot(flow, completed, blocked, failed)
                await self._publish_event(flow.flow_id, "flow.paused", snapshot)
                return snapshot

            ready = [
                node_id
                for node_id in pending
                if self._is_ready(flow, node_id, completed, blocked, failed)
            ]
            blocked_now = [
                node_id
                for node_id in list(pending)
                if self._is_blocked(flow, node_id, completed, blocked, failed)
            ]
            for node_id in blocked_now:
                pending.discard(node_id)
                blocked.add(node_id)

            if not ready:
                if pending:
                    flow.state = FlowState.FAILED
                    flow.metadata["deadlock_nodes"] = sorted(pending)
                else:
                    flow.state = FlowState.FAILED if failed else FlowState.COMPLETED
                self.context.repository.save_flow(flow)
                snapshot = self._snapshot(flow, completed, blocked, failed)
                await self._publish_event(
                    flow.flow_id,
                    "flow.failed" if flow.state == FlowState.FAILED else "flow.completed",
                    snapshot,
                )
                return snapshot

            semaphore = asyncio.Semaphore(int(flow.metadata.get("max_concurrency", self.context.max_flow_concurrency)))

            async def execute_node(node_id: str) -> tuple[str, TaskExecution | None, Exception | None]:
                async with semaphore:
                    try:
                        execution = await self.task_executor.execute_task(
                            task=flow.nodes[node_id].task,
                            flow=flow,
                            flow_results=flow.metadata["results"],
                            node_id=node_id,
                        )
                        return node_id, execution, None
                    except Exception as exc:
                        return node_id, None, exc

            results = await asyncio.gather(*(execute_node(node_id) for node_id in ready))

            for node_id, execution, error in results:
                if execution is not None and execution.status == ExecutionStatus.WAITING_FOR_INPUT:
                    flow.state = FlowState.WAITING_FOR_INPUT
                    flow.metadata.setdefault("waiting_for_input", {})
                    flow.metadata["waiting_for_input"][node_id] = (
                        execution.result.get("human_input_request", {})
                        if isinstance(execution.result, dict)
                        else {}
                    )
                    flow.metadata["completed_nodes"] = sorted(completed)
                    flow.metadata["blocked_nodes"] = sorted(blocked)
                    flow.metadata["failed_nodes"] = dict(failed)
                    self.context.repository.save_flow(flow)
                    snapshot = self._snapshot(flow, completed, blocked, failed)
                    await self._publish_event(flow.flow_id, "flow.waiting_for_input", snapshot)
                    return snapshot
                pending.discard(node_id)
                if error is None and execution is not None:
                    completed.add(node_id)
                    flow.metadata["results"][node_id] = execution.result
                    if isinstance(waiting_for_input, dict):
                        waiting_for_input.pop(node_id, None)
                else:
                    failed[node_id] = str(error)
                    flow.metadata.setdefault("failed_nodes", {})[node_id] = str(error)
                    if not bool(flow.metadata.get("continue_on_error", False)):
                        flow.state = FlowState.FAILED
                        flow.metadata["completed_nodes"] = sorted(completed)
                        flow.metadata["blocked_nodes"] = sorted(blocked)
                        self.context.repository.save_flow(flow)
                        snapshot = self._snapshot(flow, completed, blocked, failed)
                        await self._publish_event(flow.flow_id, "flow.failed", snapshot)
                        return snapshot

            flow.metadata["completed_nodes"] = sorted(completed)
            flow.metadata["blocked_nodes"] = sorted(blocked)
            flow.metadata["failed_nodes"] = dict(failed)
            self.context.repository.save_flow(flow)
            await self._publish_snapshot(flow, completed, blocked, failed, "flow.progress")

        flow.state = FlowState.FAILED if failed else FlowState.COMPLETED
        flow.metadata["completed_nodes"] = sorted(completed)
        flow.metadata["blocked_nodes"] = sorted(blocked)
        flow.metadata["failed_nodes"] = dict(failed)
        self.context.repository.save_flow(flow)
        snapshot = self._snapshot(flow, completed, blocked, failed)
        await self._publish_event(
            flow.flow_id,
            "flow.failed" if flow.state == FlowState.FAILED else "flow.completed",
            snapshot,
        )
        return snapshot

    def _is_ready(
        self,
        flow: ExecutionFlow,
        node_id: str,
        completed: set[str],
        blocked: set[str],
        failed: dict[str, str],
    ) -> bool:
        incoming_edges = flow.incoming_edges(node_id)
        if not incoming_edges:
            return True
        if not all(edge.from_node in completed for edge in incoming_edges):
            return False
        return all(
            edge.condition.evaluate(
                {
                    "results": flow.metadata.get("results", {}),
                    "source_result": flow.metadata.get("results", {}).get(edge.from_node),
                    "target_node": node_id,
                    "completed": sorted(completed),
                    "blocked": sorted(blocked),
                    "failed": failed,
                }
            )
            for edge in incoming_edges
        )

    def _is_blocked(
        self,
        flow: ExecutionFlow,
        node_id: str,
        completed: set[str],
        blocked: set[str],
        failed: dict[str, str],
    ) -> bool:
        incoming_edges = flow.incoming_edges(node_id)
        if not incoming_edges:
            return False
        terminal = completed.union(blocked).union(failed.keys())
        if not all(edge.from_node in terminal for edge in incoming_edges):
            return False
        if any(edge.from_node in blocked or edge.from_node in failed for edge in incoming_edges):
            return True
        return not self._is_ready(flow, node_id, completed, blocked, failed)

    @staticmethod
    def _snapshot(
        flow: ExecutionFlow,
        completed: set[str],
        blocked: set[str],
        failed: dict[str, str],
    ) -> dict[str, Any]:
        snapshot = flow.observe()
        snapshot.update(
            {
                "results": flow.metadata.get("results", {}),
                "completed_nodes": sorted(completed),
                "blocked_nodes": sorted(blocked),
                "failed_nodes": failed,
            }
        )
        return snapshot

    async def _publish_snapshot(
        self,
        flow: ExecutionFlow,
        completed: set[str],
        blocked: set[str],
        failed: dict[str, str],
        event_type: str,
    ) -> None:
        snapshot = self._snapshot(flow, completed, blocked, failed)
        await self._publish_event(flow.flow_id, event_type, snapshot)

    async def _publish_event(
        self,
        flow_id: int,
        event_type: str,
        snapshot: dict[str, Any],
    ) -> None:
        if self.context.event_publisher is None:
            return
        await maybe_await(self.context.event_publisher(flow_id, event_type, snapshot))

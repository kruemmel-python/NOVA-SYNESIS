from __future__ import annotations

import ast
import asyncio
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from random import uniform
from typing import TYPE_CHECKING, Any, Callable

import httpx

if TYPE_CHECKING:
    from nova_synesis.communication.adapters import CommunicationAdapter
    from nova_synesis.memory.systems import MemorySystem
    from nova_synesis.planning.planner import IntentPlanner
    from nova_synesis.runtime.engine import FlowExecutor


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def maybe_await(value: Any) -> Any:
    if asyncio.iscoroutine(value) or isinstance(value, asyncio.Future):
        return await value
    return value


class AgentState(StrEnum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    ERROR = "ERROR"
    WAITING = "WAITING"


class ProtocolType(StrEnum):
    REST = "REST"
    WEBSOCKET = "WEBSOCKET"
    MESSAGE_QUEUE = "MESSAGE_QUEUE"


class MemoryType(StrEnum):
    SHORT_TERM = "SHORT_TERM"
    LONG_TERM = "LONG_TERM"
    VECTOR = "VECTOR"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ExecutionStatus(StrEnum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class RollbackStrategy(StrEnum):
    RETRY = "RETRY"
    COMPENSATE = "COMPENSATE"
    FAIL_FAST = "FAIL_FAST"
    FALLBACK_RESOURCE = "FALLBACK_RESOURCE"


class ResourceType(StrEnum):
    API = "API"
    MODEL = "MODEL"
    DATABASE = "DATABASE"
    FILE = "FILE"
    GPU = "GPU"


class ResourceState(StrEnum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    DOWN = "DOWN"


class FlowState(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(slots=True)
class Capability:
    name: str
    type: str
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetryPolicy:
    max_retries: int = 3
    backoff_ms: int = 250
    exponential: bool = True
    max_backoff_ms: int = 10_000
    jitter_ratio: float = 0.0

    def next_delay(self, attempt: int) -> float:
        base_delay_ms = self.backoff_ms * (2 ** (attempt - 1) if self.exponential else 1)
        bounded_ms = min(base_delay_ms, self.max_backoff_ms)
        jitter_ms = bounded_ms * self.jitter_ratio
        return max(0.0, (bounded_ms + uniform(-jitter_ms, jitter_ms)) / 1000)


@dataclass(slots=True)
class ErrorEvent:
    type: str
    message: str
    timestamp: datetime = field(default_factory=utcnow)
    context: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }


class SafeExpressionEvaluator(ast.NodeVisitor):
    _comparators: dict[type[ast.AST], Callable[[Any, Any], bool]] = {
        ast.Eq: lambda left, right: left == right,
        ast.NotEq: lambda left, right: left != right,
        ast.Lt: lambda left, right: left < right,
        ast.LtE: lambda left, right: left <= right,
        ast.Gt: lambda left, right: left > right,
        ast.GtE: lambda left, right: left >= right,
        ast.In: lambda left, right: left in right,
        ast.NotIn: lambda left, right: left not in right,
    }
    _binary: dict[type[ast.AST], Callable[[Any, Any], Any]] = {
        ast.Add: lambda left, right: left + right,
        ast.Sub: lambda left, right: left - right,
        ast.Mult: lambda left, right: left * right,
        ast.Div: lambda left, right: left / right,
        ast.Mod: lambda left, right: left % right,
    }
    _allowed_functions: dict[str, Callable[..., Any]] = {
        "len": len,
        "sum": sum,
        "min": min,
        "max": max,
        "all": all,
        "any": any,
        "contains": lambda collection, item: item in collection,
        "exists": lambda value: value is not None,
    }

    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context

    def evaluate(self, expression: str) -> Any:
        tree = ast.parse(expression, mode="eval")
        return self.visit(tree.body)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id not in self.context:
            raise ValueError(f"Unknown symbol '{node.id}' in condition")
        return self.context[node.id]

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_List(self, node: ast.List) -> list[Any]:
        return [self.visit(element) for element in node.elts]

    def visit_Tuple(self, node: ast.Tuple) -> tuple[Any, ...]:
        return tuple(self.visit(element) for element in node.elts)

    def visit_Dict(self, node: ast.Dict) -> dict[Any, Any]:
        return {
            self.visit(key): self.visit(value)
            for key, value in zip(node.keys, node.values, strict=True)
        }

    def visit_BoolOp(self, node: ast.BoolOp) -> bool:
        values = [bool(self.visit(value)) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise ValueError(f"Unsupported boolean operator: {type(node.op).__name__}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        operator = self._binary.get(type(node.op))
        if operator is None:
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
        return operator(self.visit(node.left), self.visit(node.right))

    def visit_Compare(self, node: ast.Compare) -> bool:
        left = self.visit(node.left)
        for operator_node, comparator_node in zip(node.ops, node.comparators, strict=True):
            comparator = self._comparators.get(type(operator_node))
            right = self.visit(comparator_node)
            if comparator is None or not comparator(left, right):
                return False
            left = right
        return True

    def visit_Subscript(self, node: ast.Subscript) -> Any:
        value = self.visit(node.value)
        if isinstance(node.slice, ast.Slice):
            lower = self.visit(node.slice.lower) if node.slice.lower else None
            upper = self.visit(node.slice.upper) if node.slice.upper else None
            step = self.visit(node.slice.step) if node.slice.step else None
            return value[slice(lower, upper, step)]
        return value[self.visit(node.slice)]

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only named helper functions are allowed in conditions")
        function = self._allowed_functions.get(node.func.id)
        if function is None:
            raise ValueError(f"Unsupported function '{node.func.id}' in condition")
        args = [self.visit(argument) for argument in node.args]
        kwargs = {
            keyword.arg: self.visit(keyword.value)
            for keyword in node.keywords
            if keyword.arg is not None
        }
        return function(*args, **kwargs)

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def safe_evaluate(expression: str, context: dict[str, Any]) -> Any:
    return SafeExpressionEvaluator(context).evaluate(expression)


@dataclass(slots=True)
class Condition:
    expression: str

    def evaluate(self, context: dict[str, Any]) -> bool:
        return bool(safe_evaluate(self.expression, context))


@dataclass(slots=True)
class Resource:
    resource_id: int
    type: ResourceType
    endpoint: str
    metadata: dict[str, Any] = field(default_factory=dict)
    state: ResourceState = ResourceState.AVAILABLE
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    _semaphore: asyncio.BoundedSemaphore = field(init=False, repr=False)
    _in_use: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        capacity = int(self.metadata.get("capacity", 1))
        self._semaphore = asyncio.BoundedSemaphore(capacity)

    @property
    def capacity(self) -> int:
        return int(self.metadata.get("capacity", 1))

    async def acquire(self, timeout: float | None = None) -> bool:
        if self.state == ResourceState.DOWN:
            return False
        try:
            if timeout is None:
                await self._semaphore.acquire()
            else:
                await asyncio.wait_for(self._semaphore.acquire(), timeout=timeout)
        except TimeoutError:
            return False
        async with self._lock:
            self._in_use += 1
            self.state = (
                ResourceState.BUSY
                if self._in_use >= self.capacity
                else ResourceState.AVAILABLE
            )
        return True

    async def release(self) -> None:
        async with self._lock:
            if self._in_use > 0:
                self._in_use -= 1
                self._semaphore.release()
            self.state = (
                ResourceState.BUSY if self._in_use >= self.capacity else ResourceState.AVAILABLE
            )

    async def health_check(self) -> bool:
        custom_checker = self.metadata.get("health_check")
        if callable(custom_checker):
            is_healthy = bool(await maybe_await(custom_checker(self)))
            self.state = ResourceState.AVAILABLE if is_healthy else ResourceState.DOWN
            return is_healthy

        try:
            if self.type == ResourceType.API and self.endpoint:
                method = self.metadata.get("health_method", "GET")
                timeout = float(self.metadata.get("timeout_s", 3.0))
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.request(method, self.endpoint)
                is_healthy = response.status_code < 500
            elif self.type == ResourceType.FILE:
                is_healthy = Path(self.endpoint).exists()
            elif self.type == ResourceType.DATABASE:
                database_path = self.metadata.get("database_path", self.endpoint)
                with sqlite3.connect(database_path) as connection:
                    connection.execute("SELECT 1")
                is_healthy = True
            else:
                is_healthy = self.state != ResourceState.DOWN
        except Exception:
            is_healthy = False

        self.state = ResourceState.AVAILABLE if is_healthy else ResourceState.DOWN
        return is_healthy


@dataclass(slots=True)
class Agent:
    agent_id: int
    name: str
    role: str
    capabilities: list[Capability] = field(default_factory=list)
    state: AgentState = AgentState.IDLE
    comms: CommunicationAdapter | None = None
    memory_refs: list[MemorySystem] = field(default_factory=list)

    def capability_index(self) -> set[str]:
        values = {self.role}
        for capability in self.capabilities:
            values.add(capability.name)
            values.add(capability.type)
        return values

    def can_execute(self, required_capabilities: list[str]) -> bool:
        if not required_capabilities:
            return True
        available = self.capability_index()
        return all(capability in available for capability in required_capabilities)

    async def perceive(self, input_data: Any) -> dict[str, Any]:
        return {
            "input": input_data,
            "agent_id": self.agent_id,
            "role": self.role,
            "capabilities": [capability.name for capability in self.capabilities],
            "timestamp": utcnow().isoformat(),
        }

    async def decide(self, context: dict[str, Any]) -> dict[str, Any]:
        required = set(context.get("required_capabilities", []))
        available = self.capability_index()
        matched = sorted(required.intersection(available))
        return {
            "selected": not required or required.issubset(available),
            "matched_capabilities": matched,
            "available_capabilities": sorted(available),
        }

    async def act(self, task: "Task") -> dict[str, Any]:
        self.state = AgentState.RUNNING
        return {
            "task_id": task.task_id,
            "handler_name": task.handler_name,
            "timestamp": utcnow().isoformat(),
        }

    async def communicate(
        self,
        message: Any,
        target: str | int | None = None,
        protocol: ProtocolType | None = None,
    ) -> Any:
        if self.comms is None:
            raise RuntimeError(f"Agent '{self.name}' has no communication adapter configured")
        payload = {
            "source_agent_id": self.agent_id,
            "target": target,
            "protocol": str(protocol or self.comms.protocol),
            "message": message,
            "timestamp": utcnow().isoformat(),
        }
        return await self.comms.send(payload)


@dataclass(slots=True)
class Task:
    task_id: int
    input: Any
    output: Any = None
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Agent | None = None
    required_resources: list[Resource] = field(default_factory=list)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    handler_name: str = "template_render"
    validator_rules: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    rollback_strategy: RollbackStrategy = RollbackStrategy.FAIL_FAST
    compensation_handler: str | None = None

    async def execute(self) -> None:
        self.status = TaskStatus.RUNNING

    def validate(self, result: Any) -> bool:
        required_keys = self.validator_rules.get("required_keys", [])
        if required_keys:
            if not isinstance(result, dict):
                raise ValueError("Validation failed: result is not a dictionary")
            missing = [key for key in required_keys if key not in result]
            if missing:
                raise ValueError(f"Validation failed: missing keys {missing}")

        expected_type = self.validator_rules.get("output_type")
        if expected_type:
            type_mapping = {
                "str": str,
                "int": int,
                "float": float,
                "dict": dict,
                "list": list,
                "bool": bool,
            }
            target_type = type_mapping.get(expected_type)
            if target_type is None or not isinstance(result, target_type):
                raise ValueError(f"Validation failed: output is not of type {expected_type}")

        expression = self.validator_rules.get("expression")
        if expression and not safe_evaluate(
            expression,
            {
                "result": result,
                "metadata": self.metadata,
            },
        ):
            raise ValueError("Validation failed: expression evaluated to false")
        return True

    def complete(self, output: Any) -> Any:
        self.output = output
        self.status = TaskStatus.SUCCESS
        return output

    def reset(self) -> None:
        self.output = None
        self.status = TaskStatus.PENDING


@dataclass(slots=True)
class TaskExecution:
    execution_id: int
    task_ref: Task
    start_time: datetime | None = None
    end_time: datetime | None = None
    result: Any = None
    status: ExecutionStatus = ExecutionStatus.STARTED
    errors: list[ErrorEvent] = field(default_factory=list)
    attempt_count: int = 0
    resource_history: list[int] = field(default_factory=list)

    def start(self) -> None:
        self.start_time = utcnow()
        self.status = ExecutionStatus.STARTED
        self.task_ref.status = TaskStatus.RUNNING

    def finish(self, result: Any) -> None:
        self.end_time = utcnow()
        self.result = result
        self.status = ExecutionStatus.COMPLETED
        self.task_ref.complete(result)

    def record_error(self, error: ErrorEvent) -> ErrorEvent:
        self.errors.append(error)
        self.status = ExecutionStatus.FAILED
        self.task_ref.status = TaskStatus.FAILED
        return error

    def rollback(self, strategy: RollbackStrategy) -> None:
        self.end_time = utcnow()
        self.status = ExecutionStatus.ROLLED_BACK
        self.task_ref.metadata["rollback_strategy_used"] = strategy.value

    def retry(self) -> None:
        self.attempt_count += 1
        self.status = ExecutionStatus.STARTED
        self.task_ref.status = TaskStatus.RUNNING


@dataclass(slots=True)
class Intent:
    intent_id: int
    goal: str
    constraints: dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    timestamp: datetime = field(default_factory=utcnow)

    def refine(self, updates: dict[str, Any]) -> "Intent":
        merged_constraints = dict(self.constraints)
        merged_constraints.update(updates)
        self.constraints = merged_constraints
        return self

    async def plan(
        self,
        planner: IntentPlanner,
        agents: list[Agent],
        resources: list[Resource],
        task_id_allocator: Callable[[], int],
        flow_id_allocator: Callable[[], int],
    ) -> "ExecutionFlow":
        return planner.plan_intent(
            self,
            agents=agents,
            resources=resources,
            task_id_allocator=task_id_allocator,
            flow_id_allocator=flow_id_allocator,
        )

    async def promote_to_task(
        self,
        planner: IntentPlanner,
        agents: list[Agent],
        resources: list[Resource],
        task_id_allocator: Callable[[], int],
    ) -> Task:
        return planner.promote_to_task(
            self,
            agents=agents,
            resources=resources,
            task_id_allocator=task_id_allocator,
        )


@dataclass(slots=True)
class FlowNode:
    node_id: str
    task: Task
    agent: Agent | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FlowEdge:
    from_node: str
    to_node: str
    condition: Condition = field(default_factory=lambda: Condition("True"))


@dataclass(slots=True)
class ExecutionFlow:
    flow_id: int
    state: FlowState = FlowState.CREATED
    nodes: dict[str, FlowNode] = field(default_factory=dict)
    edges: list[FlowEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: FlowNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: FlowEdge) -> None:
        if edge.from_node not in self.nodes:
            raise ValueError(f"Unknown source node '{edge.from_node}'")
        if edge.to_node not in self.nodes:
            raise ValueError(f"Unknown target node '{edge.to_node}'")
        self.edges.append(edge)

    def incoming_edges(self, node_id: str) -> list[FlowEdge]:
        return [edge for edge in self.edges if edge.to_node == node_id]

    def outgoing_edges(self, node_id: str) -> list[FlowEdge]:
        return [edge for edge in self.edges if edge.from_node == node_id]

    async def run(self, executor: FlowExecutor) -> dict[str, Any]:
        return await executor.run_flow(self)

    def pause(self) -> None:
        self.state = FlowState.PAUSED
        self.metadata["pause_requested"] = True

    def observe(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "state": self.state.value,
            "metadata": self.metadata,
            "nodes": {
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
                    "compensation_handler": node.task.compensation_handler,
                }
                for node_id, node in self.nodes.items()
            },
            "edges": [
                {
                    "from_node": edge.from_node,
                    "to_node": edge.to_node,
                    "condition": edge.condition.expression,
                }
                for edge in self.edges
            ],
        }

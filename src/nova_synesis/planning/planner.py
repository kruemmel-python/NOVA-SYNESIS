from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from nova_synesis.domain.models import (
    Agent,
    Condition,
    ExecutionFlow,
    FlowEdge,
    FlowNode,
    Intent,
    ManualApproval,
    Resource,
    ResourceType,
    RetryPolicy,
    RollbackStrategy,
    Task,
)


@dataclass(slots=True)
class TaskBlueprint:
    node_id: str
    handler_name: str
    input: Any
    required_capabilities: list[str] = field(default_factory=list)
    required_resource_ids: list[int] = field(default_factory=list)
    required_resource_types: list[ResourceType] = field(default_factory=list)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    rollback_strategy: RollbackStrategy = RollbackStrategy.FAIL_FAST
    validator_rules: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    requires_manual_approval: bool = False
    manual_approval: dict[str, Any] = field(default_factory=dict)
    compensation_handler: str | None = None
    dependencies: list[str] = field(default_factory=list)
    conditions: dict[str, str] = field(default_factory=dict)
    preferred_agent_id: int | None = None


class IntentPlanner:
    def plan_intent(
        self,
        intent: Intent,
        agents: list[Agent],
        resources: list[Resource],
        task_id_allocator: Callable[[], int],
        flow_id_allocator: Callable[[], int],
    ) -> ExecutionFlow:
        blueprints, extra_edges, flow_metadata = self._extract_blueprints(intent)
        flow = ExecutionFlow(flow_id=flow_id_allocator())
        flow.metadata.update(
            {
                "intent_id": intent.intent_id,
                "goal": intent.goal,
                "priority": intent.priority,
                **flow_metadata,
            }
        )

        resource_index = {resource.resource_id: resource for resource in resources}
        resources_by_type = self._group_resources_by_type(resources)

        for blueprint in blueprints:
            assigned_agent = self._select_agent(blueprint, agents)
            task = Task(
                task_id=task_id_allocator(),
                input=blueprint.input,
                assigned_agent=assigned_agent,
                required_resources=self._resolve_resources(
                    blueprint=blueprint,
                    resource_index=resource_index,
                    resources_by_type=resources_by_type,
                ),
                retry_policy=blueprint.retry_policy,
                handler_name=blueprint.handler_name,
                validator_rules=blueprint.validator_rules,
                context={"required_capabilities": blueprint.required_capabilities},
                metadata=blueprint.metadata,
                requires_manual_approval=blueprint.requires_manual_approval,
                manual_approval=ManualApproval.from_dict(blueprint.manual_approval),
                rollback_strategy=blueprint.rollback_strategy,
                compensation_handler=blueprint.compensation_handler,
            )
            flow.add_node(
                FlowNode(
                    node_id=blueprint.node_id,
                    task=task,
                    agent=assigned_agent,
                    metadata={"required_capabilities": blueprint.required_capabilities},
                )
            )

        for blueprint in blueprints:
            for dependency in blueprint.dependencies:
                flow.add_edge(
                    FlowEdge(
                        from_node=dependency,
                        to_node=blueprint.node_id,
                        condition=Condition(blueprint.conditions.get(dependency, "True")),
                    )
                )

        for edge in extra_edges:
            flow.add_edge(edge)

        return flow

    def promote_to_task(
        self,
        intent: Intent,
        agents: list[Agent],
        resources: list[Resource],
        task_id_allocator: Callable[[], int],
    ) -> Task:
        constraints = intent.constraints
        handler_name = constraints.get("handler_name", "template_render")
        required_capabilities = list(constraints.get("required_capabilities", []))
        resource_types = [
            self._normalize_resource_type(value)
            for value in constraints.get("required_resource_types", [])
        ]
        blueprint = TaskBlueprint(
            node_id=f"intent-{intent.intent_id}",
            handler_name=handler_name,
            input=constraints.get("input", {"goal": intent.goal}),
            required_capabilities=required_capabilities,
            required_resource_ids=list(constraints.get("required_resource_ids", [])),
            required_resource_types=resource_types,
            retry_policy=self._build_retry_policy(constraints.get("retry_policy")),
            rollback_strategy=RollbackStrategy(
                constraints.get("rollback_strategy", RollbackStrategy.FAIL_FAST.value)
            ),
            validator_rules=dict(constraints.get("validator_rules", {})),
            metadata=dict(constraints.get("metadata", {})),
            compensation_handler=constraints.get("compensation_handler"),
        )
        return Task(
            task_id=task_id_allocator(),
            input=blueprint.input,
            assigned_agent=self._select_agent(blueprint, agents),
            required_resources=self._resolve_resources(
                blueprint=blueprint,
                resource_index={resource.resource_id: resource for resource in resources},
                resources_by_type=self._group_resources_by_type(resources),
            ),
            retry_policy=blueprint.retry_policy,
            handler_name=blueprint.handler_name,
            validator_rules=blueprint.validator_rules,
            context={"required_capabilities": required_capabilities},
            metadata=blueprint.metadata,
            requires_manual_approval=blueprint.requires_manual_approval,
            manual_approval=ManualApproval.from_dict(blueprint.manual_approval),
            rollback_strategy=blueprint.rollback_strategy,
            compensation_handler=blueprint.compensation_handler,
        )

    def _extract_blueprints(
        self,
        intent: Intent,
    ) -> tuple[list[TaskBlueprint], list[FlowEdge], dict[str, Any]]:
        constraints = intent.constraints
        flow_container = constraints.get("workflow", constraints)
        raw_tasks = flow_container.get("tasks") or flow_container.get("steps")

        if not raw_tasks:
            blueprint = TaskBlueprint(
                node_id="task-1",
                handler_name=constraints.get("handler_name", "template_render"),
                input=constraints.get("input", {"goal": intent.goal, "constraints": constraints}),
                required_capabilities=list(constraints.get("required_capabilities", [])),
                required_resource_ids=list(constraints.get("required_resource_ids", [])),
                required_resource_types=[
                    self._normalize_resource_type(value)
                    for value in constraints.get("required_resource_types", [])
                ],
                retry_policy=self._build_retry_policy(constraints.get("retry_policy")),
                rollback_strategy=RollbackStrategy(
                    constraints.get("rollback_strategy", RollbackStrategy.FAIL_FAST.value)
                ),
                validator_rules=dict(constraints.get("validator_rules", {})),
                metadata=dict(constraints.get("metadata", {})),
                requires_manual_approval=bool(constraints.get("requires_manual_approval", False)),
                manual_approval=dict(constraints.get("manual_approval", {})),
                compensation_handler=constraints.get("compensation_handler"),
            )
            return [blueprint], [], dict(flow_container.get("flow_metadata", {}))

        blueprints: list[TaskBlueprint] = []
        for index, raw_task in enumerate(raw_tasks, start=1):
            blueprints.append(
                TaskBlueprint(
                    node_id=str(raw_task.get("node_id", f"task-{index}")),
                    handler_name=str(raw_task["handler_name"]),
                    input=raw_task.get("input"),
                    required_capabilities=list(raw_task.get("required_capabilities", [])),
                    required_resource_ids=list(raw_task.get("required_resource_ids", [])),
                    required_resource_types=[
                        self._normalize_resource_type(value)
                        for value in raw_task.get("required_resource_types", [])
                    ],
                    retry_policy=self._build_retry_policy(raw_task.get("retry_policy")),
                    rollback_strategy=RollbackStrategy(
                        raw_task.get("rollback_strategy", RollbackStrategy.FAIL_FAST.value)
                    ),
                    validator_rules=dict(raw_task.get("validator_rules", {})),
                    metadata=dict(raw_task.get("metadata", {})),
                    requires_manual_approval=bool(raw_task.get("requires_manual_approval", False)),
                    manual_approval=dict(raw_task.get("manual_approval", {})),
                    compensation_handler=raw_task.get("compensation_handler"),
                    dependencies=list(raw_task.get("dependencies", [])),
                    conditions=dict(raw_task.get("conditions", {})),
                    preferred_agent_id=raw_task.get("preferred_agent_id"),
                )
            )

        extra_edges = [
            FlowEdge(
                from_node=str(edge["from_node"]),
                to_node=str(edge["to_node"]),
                condition=Condition(str(edge.get("condition", "True"))),
            )
            for edge in flow_container.get("edges", [])
        ]
        return blueprints, extra_edges, dict(flow_container.get("flow_metadata", {}))

    @staticmethod
    def _build_retry_policy(raw_policy: dict[str, Any] | None) -> RetryPolicy:
        if not raw_policy:
            return RetryPolicy()
        return RetryPolicy(
            max_retries=int(raw_policy.get("max_retries", 3)),
            backoff_ms=int(raw_policy.get("backoff_ms", 250)),
            exponential=bool(raw_policy.get("exponential", True)),
            max_backoff_ms=int(raw_policy.get("max_backoff_ms", 10_000)),
            jitter_ratio=float(raw_policy.get("jitter_ratio", 0.0)),
        )

    @staticmethod
    def _normalize_resource_type(value: str | ResourceType) -> ResourceType:
        return value if isinstance(value, ResourceType) else ResourceType(value)

    @staticmethod
    def _group_resources_by_type(resources: list[Resource]) -> dict[ResourceType, list[Resource]]:
        grouped: dict[ResourceType, list[Resource]] = {}
        for resource in resources:
            grouped.setdefault(resource.type, []).append(resource)
        return grouped

    def _resolve_resources(
        self,
        blueprint: TaskBlueprint,
        resource_index: dict[int, Resource],
        resources_by_type: dict[ResourceType, list[Resource]],
    ) -> list[Resource]:
        resolved: list[Resource] = []
        seen: set[int] = set()
        for resource_id in blueprint.required_resource_ids:
            if resource_id not in resource_index:
                raise KeyError(f"Unknown resource '{resource_id}' referenced by node '{blueprint.node_id}'")
            resource = resource_index[resource_id]
            resolved.append(resource)
            seen.add(resource.resource_id)
        for resource_type in blueprint.required_resource_types:
            for resource in resources_by_type.get(resource_type, []):
                if resource.resource_id not in seen:
                    resolved.append(resource)
                    seen.add(resource.resource_id)
        return resolved

    def _select_agent(self, blueprint: TaskBlueprint, agents: list[Agent]) -> Agent | None:
        if not agents:
            return None

        if blueprint.preferred_agent_id is not None:
            preferred = next(
                (agent for agent in agents if agent.agent_id == blueprint.preferred_agent_id),
                None,
            )
            if preferred is not None:
                return preferred

        required_capabilities = set(blueprint.required_capabilities)
        ranked = sorted(
            agents,
            key=lambda agent: (
                sum(1 for value in required_capabilities if value in agent.capability_index()),
                1 if agent.can_execute(list(required_capabilities)) else 0,
                1 if agent.state.value == "IDLE" else 0,
            ),
            reverse=True,
        )
        return ranked[0]

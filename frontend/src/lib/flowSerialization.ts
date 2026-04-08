import { MarkerType } from "@xyflow/react";

import type {
  ConditionEdgeData,
  EdgeModel,
  FlowNodeSnapshot,
  FlowRequest,
  FlowSnapshot,
  RetryPolicy,
  RollbackStrategy,
  TaskFlowEdge,
  TaskFlowNode,
  TaskNodeData,
  TaskSpecModel,
} from "../types/api";

export const DEFAULT_RETRY_POLICY: RetryPolicy = {
  max_retries: 3,
  backoff_ms: 250,
  exponential: true,
  max_backoff_ms: 10_000,
  jitter_ratio: 0,
};

export const DEFAULT_ROLLBACK_STRATEGY: RollbackStrategy = "FAIL_FAST";
export const DEFAULT_MANUAL_APPROVAL = {
  approved: false,
  approved_by: null,
  approved_at: null,
  reason: null,
  revoked_by: null,
  revoked_at: null,
};

export function createTaskNode(
  handlerName: string,
  position: { x: number; y: number },
  id = crypto.randomUUID(),
): TaskFlowNode {
  return {
    id,
    type: "task",
    position,
    data: {
      title: humanizeHandlerName(handlerName),
      handler_name: handlerName,
      input: {},
      required_capabilities: [],
      required_resource_ids: [],
      required_resource_types: [],
      retry_policy: { ...DEFAULT_RETRY_POLICY },
      rollback_strategy: DEFAULT_ROLLBACK_STRATEGY,
      validator_rules: {},
      metadata: {},
      requires_manual_approval: false,
      manual_approval: { ...DEFAULT_MANUAL_APPROVAL },
      compensation_handler: null,
      preferred_agent_id: null,
      task_status: "PENDING",
      output: null,
    },
  };
}

export function createTaskEdge(source: string, target: string): TaskFlowEdge {
  const data: ConditionEdgeData = { condition: "True", label: "True" };
  return {
    id: `${source}-${target}-${crypto.randomUUID()}`,
    source,
    target,
    markerEnd: {
      type: MarkerType.ArrowClosed,
    },
    label: data.label,
    data,
  };
}

export function toTaskSpec(node: TaskFlowNode, edges: TaskFlowEdge[]): TaskSpecModel {
  const dependencyEdges = edges.filter((edge) => edge.target === node.id);
  return {
    node_id: node.id,
    handler_name: node.data.handler_name,
    input: node.data.input,
    required_capabilities: node.data.required_capabilities,
    required_resource_ids: node.data.required_resource_ids,
    required_resource_types: node.data.required_resource_types,
    retry_policy: node.data.retry_policy,
    rollback_strategy: node.data.rollback_strategy,
    validator_rules: node.data.validator_rules,
    metadata: {
      ...node.data.metadata,
      ui: {
        ...readUiMetadata(node.data.metadata),
        position: node.position,
        title: node.data.title,
      },
    },
    requires_manual_approval: node.data.requires_manual_approval,
    manual_approval: node.data.manual_approval,
    compensation_handler: node.data.compensation_handler,
    dependencies: dependencyEdges.map((edge) => edge.source),
    conditions: dependencyEdges.reduce<Record<string, string>>((accumulator, edge) => {
      accumulator[edge.source] = edge.data?.condition ?? "True";
      return accumulator;
    }, {}),
    preferred_agent_id: node.data.preferred_agent_id,
  };
}

export function toEdgeModel(edge: TaskFlowEdge): EdgeModel {
  return {
    from_node: edge.source,
    to_node: edge.target,
    condition: edge.data?.condition ?? "True",
  };
}

export function toFlowRequest(nodes: TaskFlowNode[], edges: TaskFlowEdge[]): FlowRequest {
  return {
    nodes: nodes.map((node) => toTaskSpec(node, edges)),
    edges: edges.map(toEdgeModel),
  };
}

export function fromFlowSnapshot(snapshot: FlowSnapshot): {
  nodes: TaskFlowNode[];
  edges: TaskFlowEdge[];
} {
  const nodes = Object.entries(snapshot.nodes).map(([nodeId, node], index) =>
    snapshotNodeToEditorNode(nodeId, node, index),
  );

  const edges = snapshot.edges.map((edge) => ({
    id: `${edge.from_node}-${edge.to_node}`,
    source: edge.from_node,
    target: edge.to_node,
    markerEnd: { type: MarkerType.ArrowClosed },
    label: edge.condition,
    data: {
      condition: edge.condition,
      label: edge.condition,
    },
  }));

  return { nodes, edges };
}

export function fromFlowRequest(request: FlowRequest): {
  nodes: TaskFlowNode[];
  edges: TaskFlowEdge[];
} {
  const snapshotNodes = request.nodes.reduce<Record<string, FlowNodeSnapshot>>((accumulator, node) => {
    accumulator[node.node_id] = {
      task_id: 0,
      task_status: "PENDING",
      handler_name: node.handler_name,
      assigned_agent_id: node.preferred_agent_id,
      input: node.input,
      output: null,
      required_capabilities: node.required_capabilities,
      required_resource_ids: node.required_resource_ids,
      required_resource_types: node.required_resource_types,
      retry_policy: node.retry_policy,
      rollback_strategy: node.rollback_strategy,
      validator_rules: node.validator_rules,
      metadata: node.metadata,
      requires_manual_approval: node.requires_manual_approval,
      manual_approval: node.manual_approval,
      compensation_handler: node.compensation_handler,
    };
    return accumulator;
  }, {});

  return fromFlowSnapshot({
    flow_id: 0,
    state: "CREATED",
    metadata: {},
    nodes: snapshotNodes,
    edges: request.edges,
  });
}

export function humanizeHandlerName(handlerName: string): string {
  return handlerName
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function readUiMetadata(metadata: Record<string, unknown> | undefined): Record<string, unknown> {
  if (!metadata || typeof metadata !== "object") {
    return {};
  }
  const ui = metadata.ui;
  return ui && typeof ui === "object" ? (ui as Record<string, unknown>) : {};
}

function asPosition(position: unknown, index: number): { x: number; y: number } {
  if (
    position &&
    typeof position === "object" &&
    typeof (position as { x?: unknown }).x === "number" &&
    typeof (position as { y?: unknown }).y === "number"
  ) {
    return {
      x: Number((position as { x: number }).x),
      y: Number((position as { y: number }).y),
    };
  }

  return {
    x: 80 + (index % 3) * 340,
    y: 80 + Math.floor(index / 3) * 220,
  };
}

function snapshotNodeToEditorNode(
  nodeId: string,
  node: FlowNodeSnapshot,
  index: number,
): TaskFlowNode {
  const uiMetadata = readUiMetadata(node.metadata);
  const position = asPosition(uiMetadata.position, index);
  const data: TaskNodeData = {
    title:
      typeof uiMetadata.title === "string"
        ? uiMetadata.title
        : humanizeHandlerName(node.handler_name),
    handler_name: node.handler_name,
    input: node.input ?? {},
    required_capabilities: node.required_capabilities ?? [],
    required_resource_ids: node.required_resource_ids ?? [],
    required_resource_types: node.required_resource_types ?? [],
    retry_policy: node.retry_policy ?? { ...DEFAULT_RETRY_POLICY },
    rollback_strategy: node.rollback_strategy ?? DEFAULT_ROLLBACK_STRATEGY,
    validator_rules: node.validator_rules ?? {},
    metadata: node.metadata ?? {},
    requires_manual_approval: node.requires_manual_approval ?? false,
    manual_approval: node.manual_approval ?? { ...DEFAULT_MANUAL_APPROVAL },
    compensation_handler: node.compensation_handler ?? null,
    preferred_agent_id: node.assigned_agent_id ?? null,
    task_status: node.task_status,
    output: node.output ?? null,
  };

  return {
    id: nodeId,
    type: "task",
    position,
    data,
  };
}

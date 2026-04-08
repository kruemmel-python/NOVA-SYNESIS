import type { Edge, Node } from "@xyflow/react";

export type ResourceType = "API" | "MODEL" | "DATABASE" | "FILE" | "GPU";
export type RollbackStrategy =
  | "RETRY"
  | "COMPENSATE"
  | "FAIL_FAST"
  | "FALLBACK_RESOURCE";
export type TaskStatus = "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";
export type FlowState = "CREATED" | "RUNNING" | "PAUSED" | "COMPLETED" | "FAILED";

export interface RetryPolicy {
  max_retries: number;
  backoff_ms: number;
  exponential: boolean;
  max_backoff_ms: number;
  jitter_ratio: number;
}

export interface AgentSummary {
  agent_id: number;
  name: string;
  role: string;
  state: string;
  capabilities: Array<{
    name: string;
    type: string;
    constraints: Record<string, unknown>;
  }>;
  communication: {
    protocol: string;
    endpoint: string;
    config: Record<string, unknown>;
  } | null;
  memory_refs: string[];
}

export interface ResourceSummary {
  resource_id: number;
  type: ResourceType;
  endpoint: string;
  metadata: Record<string, unknown>;
  state: string;
}

export interface TaskNodeData extends Record<string, unknown> {
  title: string;
  handler_name: string;
  input: unknown;
  required_capabilities: string[];
  required_resource_ids: number[];
  required_resource_types: ResourceType[];
  retry_policy: RetryPolicy;
  rollback_strategy: RollbackStrategy;
  validator_rules: Record<string, unknown>;
  metadata: Record<string, unknown>;
  compensation_handler: string | null;
  preferred_agent_id: number | null;
  task_status: TaskStatus;
  output: unknown;
}

export interface ConditionEdgeData extends Record<string, unknown> {
  condition: string;
  label?: string;
}

export type TaskFlowNode = Node<TaskNodeData, "task">;
export type TaskFlowEdge = Edge<ConditionEdgeData>;

export interface TaskSpecModel {
  node_id: string;
  handler_name: string;
  input: unknown;
  required_capabilities: string[];
  required_resource_ids: number[];
  required_resource_types: ResourceType[];
  retry_policy: RetryPolicy;
  rollback_strategy: RollbackStrategy;
  validator_rules: Record<string, unknown>;
  metadata: Record<string, unknown>;
  compensation_handler: string | null;
  dependencies: string[];
  conditions: Record<string, string>;
  preferred_agent_id: number | null;
}

export interface EdgeModel {
  from_node: string;
  to_node: string;
  condition: string;
}

export interface FlowRequest {
  nodes: TaskSpecModel[];
  edges: EdgeModel[];
}

export interface FlowNodeSnapshot {
  task_id: number;
  task_status: TaskStatus;
  handler_name: string;
  assigned_agent_id: number | null;
  input: unknown;
  output: unknown;
  required_capabilities: string[];
  required_resource_ids: number[];
  required_resource_types: ResourceType[];
  retry_policy: RetryPolicy;
  rollback_strategy: RollbackStrategy;
  validator_rules: Record<string, unknown>;
  metadata: Record<string, unknown>;
  compensation_handler: string | null;
}

export interface FlowSnapshot {
  flow_id: number;
  state: FlowState | string;
  metadata: Record<string, unknown>;
  nodes: Record<string, FlowNodeSnapshot>;
  edges: EdgeModel[];
  results?: Record<string, unknown>;
  completed_nodes?: string[];
  blocked_nodes?: string[];
  failed_nodes?: Record<string, string>;
  updated_at?: string;
}

export interface FlowEventMessage {
  type: string;
  flow_id: number;
  timestamp?: string;
  snapshot: FlowSnapshot;
}

export interface EditorExport {
  version: 1;
  flowId: number | null;
  nodes: TaskFlowNode[];
  edges: TaskFlowEdge[];
}

export interface PlannerStatus {
  available: boolean;
  binary_path: string;
  model_path: string;
  backend: string;
  timeout_s: number;
}

export interface PlannerGenerateRequest {
  prompt: string;
  current_flow: FlowRequest | null;
  max_nodes: number;
}

export interface PlannerGenerateResponse {
  flow_request: FlowRequest;
  explanation: string | null;
  warnings: string[];
  model_path: string;
  backend: string;
  raw_response: string;
}

import type { Edge, Node } from "@xyflow/react";

export type ResourceType = "API" | "MODEL" | "DATABASE" | "FILE" | "GPU";
export type RollbackStrategy =
  | "RETRY"
  | "COMPENSATE"
  | "FAIL_FAST"
  | "FALLBACK_RESOURCE";
export type TaskStatus = "PENDING" | "RUNNING" | "WAITING_FOR_INPUT" | "SUCCESS" | "FAILED";
export type FlowState =
  | "CREATED"
  | "RUNNING"
  | "WAITING_FOR_INPUT"
  | "PAUSED"
  | "COMPLETED"
  | "FAILED";

export interface RetryPolicy {
  max_retries: number;
  backoff_ms: number;
  exponential: boolean;
  max_backoff_ms: number;
  jitter_ratio: number;
}

export interface HandlerCertificate {
  handler_name: string;
  fingerprint: string;
  module_name: string;
  qualname: string;
  issuer: string;
  issued_at: string;
  expires_at: string;
  built_in: boolean;
  signature: string;
}

export interface HandlerSummary {
  name: string;
  module_name: string;
  qualname: string;
  fingerprint: string;
  trusted: boolean;
  built_in: boolean;
  trust_reason: string;
  certificate: HandlerCertificate | null;
}

export interface ManualApproval {
  approved: boolean;
  approved_by: string | null;
  approved_at: string | null;
  reason: string | null;
  revoked_by: string | null;
  revoked_at: string | null;
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
  requires_manual_approval: boolean;
  manual_approval: ManualApproval;
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
  requires_manual_approval: boolean;
  manual_approval: ManualApproval;
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
  requires_manual_approval: boolean;
  manual_approval: ManualApproval;
  compensation_handler: string | null;
}

export interface FlowSnapshot {
  flow_id: number;
  version_id?: number | null;
  version_number?: number | null;
  state: FlowState | string;
  metadata: Record<string, unknown>;
  nodes: Record<string, FlowNodeSnapshot>;
  edges: EdgeModel[];
  available_versions?: FlowVersionSummary[];
  active_version_id?: number | null;
  version_count?: number;
  created_at?: string;
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
  flowVersionId?: number | null;
  nodes: TaskFlowNode[];
  edges: TaskFlowEdge[];
}

export interface FlowVersionSummary {
  version_id: number;
  flow_id: number;
  version_number: number;
  created_at: string;
  created_by: string | null;
  change_reason: string | null;
  parent_version_id: number | null;
  planner_generated: boolean;
  security_report: Record<string, unknown>;
  version_hash: string | null;
}

export interface FlowVersionCreateRequest extends FlowRequest {
  created_by?: string | null;
  change_reason?: string | null;
  planner_generated?: boolean;
}

export interface HumanInputRequestPayload {
  title: string;
  description: string | null;
  schema: Record<string, unknown>;
  default_value: unknown;
  required_role: string | null;
  timeout_s: number | null;
  requested_by: string | null;
  requested_at: string;
}

export interface HumanInputRequestEnvelope {
  flow_id: number;
  node_id: string;
  request: HumanInputRequestPayload;
}

export interface HumanInputResumeRequest {
  value: unknown;
  submitted_by: string;
  metadata: Record<string, unknown>;
  auto_run: boolean;
}

export interface HandlerMetricSummary {
  handler_name: string;
  execution_count: number;
  failed_count: number;
  avg_latency_ms: number | null;
  max_latency_ms: number | null;
  prompt_tokens: number;
  completion_tokens: number;
}

export interface FlowMetricSummary {
  flow_id: number;
  execution_count: number;
  failed_count: number;
  avg_latency_ms: number | null;
  max_latency_ms: number | null;
}

export interface MetricsSummary {
  handlers: HandlerMetricSummary[];
  flows: FlowMetricSummary[];
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

export interface AccountsReceivableDraftPreviewRequest {
  extract_input: Record<string, unknown>;
  generate_input: Record<string, unknown>;
  customer_index: number;
}

export interface AccountsReceivableDraftPreviewResponse {
  customer_index: number;
  customer_name: string;
  customer_id: string | null;
  generation_mode: string;
  prompt: string | null;
  letter: string;
  warnings: string[];
  source_summary: {
    customer_count: number;
    invoice_count: number;
    overdue_count: number;
    total_outstanding: number;
    currency: string;
    source_type: string | null;
    source_path: string | null;
  };
  llm: {
    enabled: boolean;
    model_path: string | null;
    backend: string | null;
    fallback_to_template_on_error: boolean;
  };
  customer: Record<string, unknown>;
}

export interface HandlerCatalogResponse {
  handlers: string[];
  details: HandlerSummary[];
}

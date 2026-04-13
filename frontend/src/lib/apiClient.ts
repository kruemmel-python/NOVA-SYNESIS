import type {
  AccountsReceivableDraftPreviewRequest,
  AccountsReceivableDraftPreviewResponse,
  AgentSummary,
  FlowMetricSummary,
  FlowRequest,
  FlowSnapshot,
  FlowVersionCreateRequest,
  FlowVersionSummary,
  HandlerCatalogResponse,
  HandlerMetricSummary,
  HandlerSummary,
  HumanInputRequestEnvelope,
  HumanInputResumeRequest,
  MetricsSummary,
  PlannerGenerateRequest,
  PlannerGenerateResponse,
  PlannerStatus,
  ResourceSummary,
} from "../types/api";

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const apiBaseUrl = rawBaseUrl.replace(/\/+$/, "");

export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

export function getWebSocketBaseUrl(): string {
  if (apiBaseUrl.startsWith("https://")) {
    return apiBaseUrl.replace("https://", "wss://");
  }
  if (apiBaseUrl.startsWith("http://")) {
    return apiBaseUrl.replace("http://", "ws://");
  }
  return apiBaseUrl;
}

async function request<T>(path: string, init?: RequestInit, timeoutMs?: number): Promise<T> {
  const controller = timeoutMs ? new AbortController() : null;
  const timeoutHandle = timeoutMs
    ? window.setTimeout(() => controller?.abort(`Request timeout after ${timeoutMs}ms`), timeoutMs)
    : null;

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      ...init,
      signal: controller?.signal ?? init?.signal,
    });
  } catch (error) {
    if (timeoutHandle !== null) {
      window.clearTimeout(timeoutHandle);
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The request timed out before the backend returned a result.");
    }
    throw error;
  }

  if (timeoutHandle !== null) {
    window.clearTimeout(timeoutHandle);
  }

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      detail = await response.text();
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function fetchHandlers(): Promise<HandlerSummary[]> {
  const payload = await request<HandlerCatalogResponse>("/handlers");
  return payload.details;
}

export function fetchPlannerStatus(): Promise<PlannerStatus> {
  return request<PlannerStatus>("/planner/status");
}

export function fetchAgents(): Promise<AgentSummary[]> {
  return request<AgentSummary[]>("/agents");
}

export function fetchResources(): Promise<ResourceSummary[]> {
  return request<ResourceSummary[]>("/resources");
}

export function createFlow(requestBody: FlowRequest): Promise<FlowSnapshot> {
  return request<FlowSnapshot>("/flows", {
    method: "POST",
    body: JSON.stringify(requestBody),
  });
}

export function createFlowVersion(
  flowId: number,
  requestBody: FlowVersionCreateRequest,
): Promise<FlowSnapshot> {
  return request<FlowSnapshot>(`/flows/${flowId}/versions`, {
    method: "POST",
    body: JSON.stringify(requestBody),
  });
}

export function runFlow(
  flowId: number,
  background = true,
  versionId?: number | null,
): Promise<FlowSnapshot | { flow_id: number; version_id?: number | null; scheduled: boolean }> {
  const search = new URLSearchParams();
  if (background) {
    search.set("background", "true");
  }
  if (versionId != null) {
    search.set("version_id", String(versionId));
  }
  const suffix = search.size > 0 ? `?${search.toString()}` : "";
  return request<FlowSnapshot | { flow_id: number; version_id?: number | null; scheduled: boolean }>(`/flows/${flowId}/run${suffix}`, {
    method: "POST",
  });
}

export function fetchFlow(flowId: number): Promise<FlowSnapshot> {
  return request<FlowSnapshot>(`/flows/${flowId}`);
}

export function fetchFlowVersions(flowId: number): Promise<FlowVersionSummary[]> {
  return request<FlowVersionSummary[]>(`/flows/${flowId}/versions`);
}

export function fetchFlowVersion(flowId: number, versionId: number): Promise<FlowSnapshot> {
  return request<FlowSnapshot>(`/flows/${flowId}/versions/${versionId}`);
}

export function activateFlowVersion(flowId: number, versionId: number): Promise<FlowSnapshot> {
  return request<FlowSnapshot>(`/flows/${flowId}/versions/${versionId}/activate`, {
    method: "POST",
  });
}

export function approveFlowNode(
  flowId: number,
  nodeId: string,
  requestBody: { approved_by: string; reason?: string | null },
): Promise<FlowSnapshot> {
  return request<FlowSnapshot>(`/flows/${flowId}/nodes/${nodeId}/approval`, {
    method: "POST",
    body: JSON.stringify(requestBody),
  });
}

export function revokeFlowNodeApproval(
  flowId: number,
  nodeId: string,
  requestBody: { revoked_by?: string | null; reason?: string | null },
): Promise<FlowSnapshot> {
  return request<FlowSnapshot>(`/flows/${flowId}/nodes/${nodeId}/approval`, {
    method: "DELETE",
    body: JSON.stringify(requestBody),
  });
}

export function fetchHumanInputRequest(
  flowId: number,
  nodeId: string,
): Promise<HumanInputRequestEnvelope> {
  return request<HumanInputRequestEnvelope>(`/flows/${flowId}/nodes/${nodeId}/input-request`);
}

export function resumeFlowNode(
  flowId: number,
  nodeId: string,
  requestBody: HumanInputResumeRequest,
): Promise<FlowSnapshot> {
  return request<FlowSnapshot>(`/flows/${flowId}/nodes/${nodeId}/resume`, {
    method: "POST",
    body: JSON.stringify(requestBody),
  });
}

export function generateFlowWithPlanner(
  requestBody: PlannerGenerateRequest,
): Promise<PlannerGenerateResponse> {
  return request<PlannerGenerateResponse>("/planner/generate-flow", {
    method: "POST",
    body: JSON.stringify(requestBody),
  });
}

export function previewAccountsReceivableDraft(
  requestBody: AccountsReceivableDraftPreviewRequest,
): Promise<AccountsReceivableDraftPreviewResponse> {
  return request<AccountsReceivableDraftPreviewResponse>("/tools/accounts-receivable/preview-draft", {
    method: "POST",
    body: JSON.stringify(requestBody),
  }, 90_000);
}

export function fetchMetricsSummary(): Promise<MetricsSummary> {
  return request<MetricsSummary>("/metrics/summary");
}

export function fetchFlowMetrics(): Promise<FlowMetricSummary[]> {
  return request<FlowMetricSummary[]>("/metrics/flows");
}

export function fetchHandlerMetrics(): Promise<HandlerMetricSummary[]> {
  return request<HandlerMetricSummary[]>("/metrics/handlers");
}

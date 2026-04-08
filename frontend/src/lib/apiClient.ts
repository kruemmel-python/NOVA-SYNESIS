import type {
  AgentSummary,
  FlowRequest,
  FlowSnapshot,
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

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

export async function fetchHandlers(): Promise<string[]> {
  const payload = await request<{ handlers: string[] }>("/handlers");
  return payload.handlers;
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

export function runFlow(flowId: number, background = true): Promise<FlowSnapshot | { flow_id: number; scheduled: boolean }> {
  const search = background ? "?background=true" : "";
  return request<FlowSnapshot | { flow_id: number; scheduled: boolean }>(`/flows/${flowId}/run${search}`, {
    method: "POST",
  });
}

export function fetchFlow(flowId: number): Promise<FlowSnapshot> {
  return request<FlowSnapshot>(`/flows/${flowId}`);
}

export function generateFlowWithPlanner(
  requestBody: PlannerGenerateRequest,
): Promise<PlannerGenerateResponse> {
  return request<PlannerGenerateResponse>("/planner/generate-flow", {
    method: "POST",
    body: JSON.stringify(requestBody),
  });
}

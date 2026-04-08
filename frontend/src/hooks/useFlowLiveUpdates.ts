import { useEffect } from "react";

import { fetchFlow, getWebSocketBaseUrl } from "../lib/apiClient";
import { useFlowStore } from "../store/useFlowStore";
import type { FlowEventMessage } from "../types/api";

export function useFlowLiveUpdates(flowId: number | null) {
  const applyFlowSnapshot = useFlowStore((state) => state.applyFlowSnapshot);
  const setExecutionError = useFlowStore((state) => state.setExecutionError);
  const setWebSocketConnected = useFlowStore((state) => state.setWebSocketConnected);

  useEffect(() => {
    if (!flowId) {
      setWebSocketConnected(false);
      return;
    }

    const socket = new WebSocket(`${getWebSocketBaseUrl()}/ws/flows/${flowId}`);

    socket.addEventListener("open", () => {
      setWebSocketConnected(true);
      setExecutionError(null);
    });

    socket.addEventListener("message", (event) => {
      try {
        const payload = JSON.parse(event.data) as FlowEventMessage;
        if (payload.snapshot) {
          applyFlowSnapshot(payload.snapshot, payload.type, payload.timestamp);
        }
      } catch (error) {
        setExecutionError(
          error instanceof Error ? error.message : "Failed to process live update",
        );
      }
    });

    socket.addEventListener("error", () => {
      setWebSocketConnected(false);
    });

    socket.addEventListener("close", () => {
      setWebSocketConnected(false);
    });

    const pollFallback = window.setInterval(async () => {
      if (socket.readyState === WebSocket.OPEN) {
        return;
      }
      try {
        const snapshot = await fetchFlow(flowId);
        applyFlowSnapshot(snapshot, "flow.poll");
      } catch {
        // Polling is a fallback; websocket remains the primary channel.
      }
    }, 2500);

    return () => {
      window.clearInterval(pollFallback);
      socket.close();
    };
  }, [applyFlowSnapshot, flowId, setExecutionError, setWebSocketConnected]);
}

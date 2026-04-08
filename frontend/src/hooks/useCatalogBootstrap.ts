import { useEffect } from "react";

import { fetchAgents, fetchHandlers, fetchResources } from "../lib/apiClient";
import { useFlowStore } from "../store/useFlowStore";

export function useCatalogBootstrap() {
  const setCatalogData = useFlowStore((state) => state.setCatalogData);
  const setExecutionError = useFlowStore((state) => state.setExecutionError);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [handlers, agents, resources] = await Promise.all([
          fetchHandlers(),
          fetchAgents(),
          fetchResources(),
        ]);

        if (!cancelled) {
          setCatalogData({ handlers, agents, resources });
        }
      } catch (error) {
        if (!cancelled) {
          setExecutionError(
            error instanceof Error ? error.message : "Failed to load orchestration catalog",
          );
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [setCatalogData, setExecutionError]);
}

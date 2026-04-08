import { ReactFlowProvider } from "@xyflow/react";
import { useCallback, useEffect, useState } from "react";

import { FlowCanvas } from "./components/flow/FlowCanvas";
import { InspectorPanel } from "./components/layout/InspectorPanel";
import { PlannerComposer } from "./components/layout/PlannerComposer";
import { Sidebar } from "./components/layout/Sidebar";
import { TopBar } from "./components/layout/TopBar";
import { useCatalogBootstrap } from "./hooks/useCatalogBootstrap";
import { useFlowLiveUpdates } from "./hooks/useFlowLiveUpdates";
import {
  createFlow,
  fetchFlow,
  fetchPlannerStatus,
  generateFlowWithPlanner,
  runFlow,
} from "./lib/apiClient";
import { fromFlowRequest, toFlowRequest } from "./lib/flowSerialization";
import { prettyJson, safeJsonParse } from "./lib/json";
import { useFlowStore } from "./store/useFlowStore";
import type {
  EditorExport,
  FlowRequest,
  PlannerGenerateResponse,
  PlannerStatus,
} from "./types/api";

function App() {
  useCatalogBootstrap();
  const [plannerOpen, setPlannerOpen] = useState(false);
  const [plannerStatus, setPlannerStatus] = useState<PlannerStatus | null>(null);
  const [lastPlannerResult, setLastPlannerResult] = useState<PlannerGenerateResponse | null>(null);

  const nodes = useFlowStore((state) => state.nodes);
  const edges = useFlowStore((state) => state.edges);
  const flowId = useFlowStore((state) => state.flowId);
  const dirty = useFlowStore((state) => state.dirty);
  const history = useFlowStore((state) => state.history);
  const future = useFlowStore((state) => state.future);
  const executionState = useFlowStore((state) => state.executionState);
  const markSaved = useFlowStore((state) => state.markSaved);
  const beginRun = useFlowStore((state) => state.beginRun);
  const applyFlowSnapshot = useFlowStore((state) => state.applyFlowSnapshot);
  const setExecutionError = useFlowStore((state) => state.setExecutionError);
  const autoLayout = useFlowStore((state) => state.autoLayout);
  const undo = useFlowStore((state) => state.undo);
  const redo = useFlowStore((state) => state.redo);
  const replaceGraph = useFlowStore((state) => state.replaceGraph);

  useFlowLiveUpdates(flowId);

  useEffect(() => {
    let cancelled = false;

    const loadPlannerStatus = async () => {
      try {
        const status = await fetchPlannerStatus();
        if (!cancelled) {
          setPlannerStatus(status);
        }
      } catch (error) {
        if (!cancelled) {
          setExecutionError(
            error instanceof Error ? error.message : "Failed to load planner status",
          );
        }
      }
    };

    void loadPlannerStatus();

    return () => {
      cancelled = true;
    };
  }, [setExecutionError]);

  const saveCurrentFlow = useCallback(async (): Promise<number> => {
    if (nodes.length === 0) {
      throw new Error("Add at least one node before saving the flow");
    }

    const request = toFlowRequest(nodes, edges);
    const snapshot = await createFlow(request);
    markSaved(snapshot.flow_id);
    applyFlowSnapshot(snapshot, "flow.created");
    setExecutionError(null);
    return snapshot.flow_id;
  }, [applyFlowSnapshot, edges, markSaved, nodes, setExecutionError]);

  const handleRun = useCallback(async () => {
    try {
      const activeFlowId = !flowId || dirty ? await saveCurrentFlow() : flowId;
      beginRun();
      const response = await runFlow(activeFlowId, true);
      if ("scheduled" in response) {
        const snapshot = await fetchFlow(activeFlowId);
        applyFlowSnapshot(snapshot, "flow.run.requested");
      } else {
        applyFlowSnapshot(response, "flow.run.completed");
      }
    } catch (error) {
      setExecutionError(error instanceof Error ? error.message : "Flow execution failed");
    }
  }, [applyFlowSnapshot, beginRun, dirty, flowId, saveCurrentFlow, setExecutionError]);

  const handleExport = useCallback(() => {
    const payload: EditorExport = {
      version: 1,
      flowId,
      nodes,
      edges,
    };
    const blob = new Blob([prettyJson(payload)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "nova-synesis-workflow.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }, [edges, flowId, nodes]);

  const handleImport = useCallback(
    async (file: File) => {
      try {
        const raw = await file.text();
        const payload = safeJsonParse<EditorExport | FlowRequest>(raw);
        if ("version" in payload) {
          replaceGraph(payload);
          return;
        }
        const graph = fromFlowRequest(payload);
        replaceGraph({
          version: 1,
          flowId: null,
          nodes: graph.nodes,
          edges: graph.edges,
        });
      } catch (error) {
        setExecutionError(error instanceof Error ? error.message : "Import failed");
      }
    },
    [replaceGraph, setExecutionError],
  );

  const handleGenerateWithPlanner = useCallback(
    async ({ prompt, maxNodes }: { prompt: string; maxNodes: number }) => {
      const currentFlow = nodes.length > 0 ? toFlowRequest(nodes, edges) : null;
      const result = await generateFlowWithPlanner({
        prompt,
        current_flow: currentFlow,
        max_nodes: maxNodes,
      });
      const graph = fromFlowRequest(result.flow_request);
      replaceGraph({
        version: 1,
        flowId: null,
        nodes: graph.nodes,
        edges: graph.edges,
      });
      setLastPlannerResult(result);
      setExecutionError(null);
    },
    [edges, nodes, replaceGraph, setExecutionError],
  );

  return (
    <ReactFlowProvider>
      <div className="app-shell">
        <TopBar
          flowId={flowId}
          dirty={dirty}
          canUndo={history.length > 0}
          canRedo={future.length > 0}
          executionState={executionState}
          plannerStatus={plannerStatus}
          onSave={saveCurrentFlow}
          onRun={handleRun}
          onOpenPlanner={() => setPlannerOpen(true)}
          onAutoLayout={autoLayout}
          onUndo={undo}
          onRedo={redo}
          onExport={handleExport}
          onImport={handleImport}
        />

        <div className="workspace">
          <Sidebar />
          <main className="workspace__canvas">
            <FlowCanvas />
          </main>
          <InspectorPanel />
        </div>

        <PlannerComposer
          open={plannerOpen}
          plannerStatus={plannerStatus}
          onClose={() => setPlannerOpen(false)}
          onGenerate={handleGenerateWithPlanner}
          lastResult={lastPlannerResult}
        />
      </div>
    </ReactFlowProvider>
  );
}

export default App;

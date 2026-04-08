import { useRef } from "react";

import { StatusBadge } from "../common/StatusBadge";
import type { PlannerStatus } from "../../types/api";

interface TopBarProps {
  flowId: number | null;
  dirty: boolean;
  canUndo: boolean;
  canRedo: boolean;
  executionState: {
    flowState: string;
    running: boolean;
    websocketConnected: boolean;
    lastUpdated: string | null;
    error: string | null;
  };
  plannerStatus: PlannerStatus | null;
  onSave: () => void | Promise<unknown>;
  onRun: () => void | Promise<unknown>;
  onOpenPlanner: () => void;
  onAutoLayout: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onExport: () => void;
  onImport: (file: File) => void;
}

export function TopBar({
  flowId,
  dirty,
  canUndo,
  canRedo,
  executionState,
  plannerStatus,
  onSave,
  onRun,
  onOpenPlanner,
  onAutoLayout,
  onUndo,
  onRedo,
  onExport,
  onImport,
}: TopBarProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  return (
    <header className="topbar">
      <div className="topbar__title">
        <p className="eyebrow">Neural Orchestration Visual Autonomy</p>
        <h1>NOVA-SYNESIS</h1>
        <p className="topbar__brand-copy">
          Stateful Yielding Node-based Execution Semantic Integrated Surface
        </p>
      </div>

      <div className="topbar__status">
        <StatusBadge
          label={executionState.flowState}
          tone={statusTone(executionState.flowState)}
        />
        <StatusBadge
          label={executionState.websocketConnected ? "Live" : "Offline"}
          tone={executionState.websocketConnected ? "running" : "neutral"}
        />
        <StatusBadge
          label={plannerStatus?.available ? "LLM Planner" : "Planner Offline"}
          tone={plannerStatus?.available ? "success" : "failed"}
        />
        <span className="topbar__meta">
          Flow ID: <strong>{flowId ?? "unsaved"}</strong>
        </span>
        <span className="topbar__meta">{dirty ? "Unsaved changes" : "Synced"}</span>
        {executionState.error ? (
          <span className="topbar__error">{executionState.error}</span>
        ) : null}
      </div>

      <div className="topbar__actions">
        <button type="button" className="ghost-button" onClick={onUndo} disabled={!canUndo}>
          Undo
        </button>
        <button type="button" className="ghost-button" onClick={onRedo} disabled={!canRedo}>
          Redo
        </button>
        <button type="button" className="ghost-button" onClick={onAutoLayout}>
          Auto Layout
        </button>
        <button type="button" className="ghost-button" onClick={onOpenPlanner}>
          AI Plan
        </button>
        <button type="button" className="ghost-button" onClick={onExport}>
          Export JSON
        </button>
        <button
          type="button"
          className="ghost-button"
          onClick={() => inputRef.current?.click()}
        >
          Import JSON
        </button>
        <button type="button" className="primary-button" onClick={() => void onSave()}>
          Save Flow
        </button>
        <button
          type="button"
          className="accent-button"
          onClick={() => void onRun()}
          disabled={executionState.running}
        >
          {executionState.running ? "Running..." : "Run Flow"}
        </button>
      </div>

      <input
        ref={inputRef}
        hidden
        type="file"
        accept="application/json"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) {
            onImport(file);
          }
          event.target.value = "";
        }}
      />
    </header>
  );
}

function statusTone(status: string): "neutral" | "running" | "success" | "failed" | "paused" {
  if (status === "RUNNING") return "running";
  if (status === "COMPLETED" || status === "SUCCESS") return "success";
  if (status === "FAILED") return "failed";
  if (status === "PAUSED") return "paused";
  return "neutral";
}

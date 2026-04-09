import { Handle, Position, type NodeProps } from "@xyflow/react";

import { useFlowStore } from "../../store/useFlowStore";
import type { TaskFlowNode } from "../../types/api";

const statusClassMap: Record<string, string> = {
  PENDING: "pending",
  RUNNING: "running",
  SUCCESS: "success",
  FAILED: "failed",
};

export function TaskNode({ id, data, selected }: NodeProps<TaskFlowNode>) {
  const setSelectedNode = useFlowStore((state) => state.setSelectedNode);
  const handler = useFlowStore((state) =>
    state.handlers.find((entry) => entry.name === data.handler_name) ?? null,
  );
  const statusClass = statusClassMap[data.task_status] ?? "pending";
  const approvalPending = data.requires_manual_approval && !data.manual_approval.approved;
  const uiMetadata = readUiMetadata(data.metadata);
  const summary =
    typeof uiMetadata.summary === "string"
      ? uiMetadata.summary
      : typeof uiMetadata.description === "string"
        ? uiMetadata.description
        : null;

  return (
    <div className={`task-node task-node--${statusClass} ${selected ? "task-node--selected" : ""}`}>
      <Handle type="target" position={Position.Left} className="task-node__handle" />
      <div className="task-node__header">
        <div>
          <div className="task-node__title">{data.title}</div>
          <div className="task-node__subtitle">{data.handler_name}</div>
        </div>
        <button
          type="button"
          className="task-node__edit"
          onClick={(event) => {
            event.stopPropagation();
            setSelectedNode(id);
          }}
        >
          Edit
        </button>
      </div>
      <div className="task-node__meta">
        <span className={`task-node__status task-node__status--${statusClass}`}>
          {data.task_status}
        </span>
        <span>{handler?.trusted ? "Trusted" : "Untrusted"}</span>
        <span>{approvalPending ? "Approval pending" : data.manual_approval.approved ? "Approved" : "No approval"}</span>
        <span>{data.required_capabilities.length} caps</span>
        <span>{data.required_resource_types.length} resource types</span>
      </div>
      {summary ? <p className="task-node__summary">{summary}</p> : null}
      <div className="task-node__body">
        <code>{typeof data.input === "object" ? JSON.stringify(data.input) : String(data.input ?? "{}")}</code>
      </div>
      <Handle type="source" position={Position.Right} className="task-node__handle" />
    </div>
  );
}

function readUiMetadata(metadata: Record<string, unknown> | undefined): Record<string, unknown> {
  if (!metadata || typeof metadata !== "object") {
    return {};
  }
  const ui = metadata.ui;
  return ui && typeof ui === "object" ? (ui as Record<string, unknown>) : {};
}

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
  const statusClass = statusClassMap[data.task_status] ?? "pending";

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
        <span>{data.required_capabilities.length} caps</span>
        <span>{data.required_resource_types.length} resource types</span>
      </div>
      <div className="task-node__body">
        <code>{typeof data.input === "object" ? JSON.stringify(data.input) : String(data.input ?? "{}")}</code>
      </div>
      <Handle type="source" position={Position.Right} className="task-node__handle" />
    </div>
  );
}

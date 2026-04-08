import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  useReactFlow,
  type OnSelectionChangeParams,
} from "@xyflow/react";
import { useCallback, useRef } from "react";

import { useFlowStore } from "../../store/useFlowStore";
import type { TaskFlowEdge, TaskFlowNode } from "../../types/api";
import { TaskNode } from "./TaskNode";

const nodeTypes = {
  task: TaskNode,
};

export function FlowCanvas() {
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const reactFlow = useReactFlow<TaskFlowNode, TaskFlowEdge>();
  const nodes = useFlowStore((state) => state.nodes);
  const edges = useFlowStore((state) => state.edges);
  const onNodesChange = useFlowStore((state) => state.onNodesChange);
  const onEdgesChange = useFlowStore((state) => state.onEdgesChange);
  const onConnect = useFlowStore((state) => state.onConnect);
  const addNodeFromHandler = useFlowStore((state) => state.addNodeFromHandler);
  const setSelectedNode = useFlowStore((state) => state.setSelectedNode);
  const setSelectedEdge = useFlowStore((state) => state.setSelectedEdge);

  const onDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      const handlerName = event.dataTransfer.getData("application/ao-handler");
      if (!handlerName) {
        return;
      }
      const position = reactFlow.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      addNodeFromHandler(handlerName, position);
    },
    [addNodeFromHandler, reactFlow],
  );

  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes, edges: selectedEdges }: OnSelectionChangeParams<TaskFlowNode, TaskFlowEdge>) => {
      setSelectedNode(selectedNodes[0]?.id ?? null);
      setSelectedEdge(selectedEdges[0]?.id ?? null);
    },
    [setSelectedEdge, setSelectedNode],
  );

  return (
    <div className="canvas-shell" ref={wrapperRef} onDragOver={onDragOver} onDrop={onDrop}>
      <ReactFlow<TaskFlowNode, TaskFlowEdge>
        fitView
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={(_, node) => setSelectedNode(node.id)}
        onEdgeClick={(_, edge) => setSelectedEdge(edge.id)}
        onPaneClick={() => {
          setSelectedNode(null);
          setSelectedEdge(null);
        }}
        onSelectionChange={onSelectionChange}
        defaultEdgeOptions={{
          animated: false,
        }}
      >
        <Background
          gap={28}
          size={1}
          variant={BackgroundVariant.Dots}
          color="rgba(132, 158, 187, 0.18)"
        />
        <MiniMap
          pannable
          zoomable
          nodeColor={(node) => {
            const status = (node.data as TaskNodeDataLike).task_status;
            if (status === "SUCCESS") return "#3ddc97";
            if (status === "FAILED") return "#ff6b6b";
            if (status === "RUNNING") return "#4db5ff";
            return "#7f8a99";
          }}
        />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

interface TaskNodeDataLike {
  task_status?: string;
}

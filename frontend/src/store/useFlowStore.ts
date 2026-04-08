import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type EdgeChange,
  type NodeChange,
} from "@xyflow/react";
import { create } from "zustand";

import { autoLayoutNodes } from "../lib/autoLayout";
import {
  DEFAULT_RETRY_POLICY,
  createTaskEdge,
  createTaskNode,
  fromFlowSnapshot,
} from "../lib/flowSerialization";
import type {
  AgentSummary,
  EditorExport,
  FlowSnapshot,
  ResourceSummary,
  RollbackStrategy,
  TaskFlowEdge,
  TaskFlowNode,
} from "../types/api";

interface GraphSnapshot {
  nodes: TaskFlowNode[];
  edges: TaskFlowEdge[];
  flowId: number | null;
  dirty: boolean;
}

interface ExecutionState {
  flowState: string;
  running: boolean;
  websocketConnected: boolean;
  lastEventType: string | null;
  lastUpdated: string | null;
  error: string | null;
}

interface FlowStore {
  nodes: TaskFlowNode[];
  edges: TaskFlowEdge[];
  handlers: string[];
  agents: AgentSummary[];
  resources: ResourceSummary[];
  flowId: number | null;
  dirty: boolean;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  executionState: ExecutionState;
  history: GraphSnapshot[];
  future: GraphSnapshot[];
  setCatalogData: (payload: {
    handlers: string[];
    agents: AgentSummary[];
    resources: ResourceSummary[];
  }) => void;
  setSelectedNode: (nodeId: string | null) => void;
  setSelectedEdge: (edgeId: string | null) => void;
  addNodeFromHandler: (handlerName: string, position: { x: number; y: number }) => void;
  onNodesChange: (changes: NodeChange<TaskFlowNode>[]) => void;
  onEdgesChange: (changes: EdgeChange<TaskFlowEdge>[]) => void;
  onConnect: (connection: Connection) => void;
  updateNodeData: (nodeId: string, updater: (node: TaskFlowNode) => TaskFlowNode) => void;
  updateEdgeCondition: (edgeId: string, condition: string) => void;
  deleteSelection: () => void;
  markSaved: (flowId: number) => void;
  beginRun: () => void;
  applyFlowSnapshot: (snapshot: FlowSnapshot, eventType?: string, timestamp?: string) => void;
  setExecutionError: (message: string | null) => void;
  setWebSocketConnected: (connected: boolean) => void;
  undo: () => void;
  redo: () => void;
  autoLayout: () => void;
  replaceGraph: (payload: EditorExport) => void;
}

const initialExecutionState: ExecutionState = {
  flowState: "CREATED",
  running: false,
  websocketConnected: false,
  lastEventType: null,
  lastUpdated: null,
  error: null,
};

function snapshotGraph(state: Pick<FlowStore, "nodes" | "edges" | "flowId" | "dirty">): GraphSnapshot {
  return {
    nodes: structuredClone(state.nodes),
    edges: structuredClone(state.edges),
    flowId: state.flowId,
    dirty: state.dirty,
  };
}

function withHistory(state: FlowStore): Pick<FlowStore, "history" | "future"> {
  return {
    history: [...state.history, snapshotGraph(state)].slice(-120),
    future: [],
  };
}

function mergeSnapshotIntoNode(node: TaskFlowNode, snapshot: FlowSnapshot): TaskFlowNode {
  const info = snapshot.nodes[node.id];
  if (!info) {
    return node;
  }

  return {
    ...node,
    data: {
      ...node.data,
      handler_name: info.handler_name,
      input: info.input,
      required_capabilities: info.required_capabilities,
      required_resource_ids: info.required_resource_ids,
      required_resource_types: info.required_resource_types,
      retry_policy: info.retry_policy ?? { ...DEFAULT_RETRY_POLICY },
      rollback_strategy: info.rollback_strategy as RollbackStrategy,
      validator_rules: info.validator_rules,
      metadata: info.metadata ?? {},
      compensation_handler: info.compensation_handler,
      preferred_agent_id: info.assigned_agent_id,
      task_status: info.task_status,
      output: info.output,
    },
  };
}

export const useFlowStore = create<FlowStore>((set, get) => ({
  nodes: [],
  edges: [],
  handlers: [],
  agents: [],
  resources: [],
  flowId: null,
  dirty: false,
  selectedNodeId: null,
  selectedEdgeId: null,
  executionState: initialExecutionState,
  history: [],
  future: [],

  setCatalogData: ({ handlers, agents, resources }) =>
    set({
      handlers,
      agents,
      resources,
    }),

  setSelectedNode: (nodeId) =>
    set({
      selectedNodeId: nodeId,
      selectedEdgeId: nodeId ? null : get().selectedEdgeId,
    }),

  setSelectedEdge: (edgeId) =>
    set({
      selectedEdgeId: edgeId,
      selectedNodeId: edgeId ? null : get().selectedNodeId,
    }),

  addNodeFromHandler: (handlerName, position) =>
    set((state) => {
      const node = createTaskNode(handlerName, position);
      return {
        ...withHistory(state),
        nodes: [...state.nodes, node],
        dirty: true,
        selectedNodeId: node.id,
        selectedEdgeId: null,
      };
    }),

  onNodesChange: (changes) =>
    set((state) => {
      const shouldSnapshot = changes.some(
        (change) =>
          change.type === "remove" ||
          (change.type === "position" && change.dragging === false),
      );

      const historyPatch = shouldSnapshot ? withHistory(state) : {};
      const nextNodes = applyNodeChanges(changes, state.nodes);

      return {
        ...historyPatch,
        nodes: nextNodes,
        dirty: shouldSnapshot ? true : state.dirty,
      };
    }),

  onEdgesChange: (changes) =>
    set((state) => {
      const shouldSnapshot = changes.some((change) => change.type === "remove");
      const historyPatch = shouldSnapshot ? withHistory(state) : {};
      return {
        ...historyPatch,
        edges: applyEdgeChanges(changes, state.edges),
        dirty: shouldSnapshot ? true : state.dirty,
      };
    }),

  onConnect: (connection) =>
    set((state) => {
      if (!connection.source || !connection.target) {
        return state;
      }
      const edge = createTaskEdge(connection.source, connection.target);
      const nextEdges = addEdge(edge, state.edges);
      return {
        ...withHistory(state),
        edges: nextEdges,
        dirty: true,
        selectedNodeId: null,
        selectedEdgeId: edge.id,
      };
    }),

  updateNodeData: (nodeId, updater) =>
    set((state) => ({
      ...withHistory(state),
      nodes: state.nodes.map((node) => (node.id === nodeId ? updater(node) : node)),
      dirty: true,
    })),

  updateEdgeCondition: (edgeId, condition) =>
    set((state) => ({
      ...withHistory(state),
      edges: state.edges.map((edge) =>
        edge.id === edgeId
          ? {
              ...edge,
              label: condition,
              data: {
                condition,
                label: condition,
              },
            }
          : edge,
      ),
      dirty: true,
    })),

  deleteSelection: () =>
    set((state) => {
      if (!state.selectedNodeId && !state.selectedEdgeId) {
        return state;
      }
      return {
        ...withHistory(state),
        nodes: state.nodes.filter((node) => node.id !== state.selectedNodeId),
        edges: state.edges.filter(
          (edge) =>
            edge.id !== state.selectedEdgeId &&
            edge.source !== state.selectedNodeId &&
            edge.target !== state.selectedNodeId,
        ),
        selectedNodeId: null,
        selectedEdgeId: null,
        dirty: true,
      };
    }),

  markSaved: (flowId) =>
    set({
      flowId,
      dirty: false,
    }),

  beginRun: () =>
    set((state) => ({
      executionState: {
        ...state.executionState,
        flowState: "RUNNING",
        running: true,
        error: null,
      },
    })),

  applyFlowSnapshot: (snapshot, eventType, timestamp) =>
    set((state) => {
      const localNodeIds = new Set(state.nodes.map((node) => node.id));
      const snapshotNodeIds = Object.keys(snapshot.nodes);
      const shouldReplaceGraph =
        state.nodes.length === 0 ||
        snapshotNodeIds.length !== state.nodes.length ||
        snapshotNodeIds.some((nodeId) => !localNodeIds.has(nodeId));

      if (shouldReplaceGraph) {
        const graph = fromFlowSnapshot(snapshot);
        return {
          nodes: graph.nodes,
          edges: graph.edges,
          flowId: snapshot.flow_id,
          dirty: state.dirty,
          selectedNodeId: null,
          selectedEdgeId: null,
          history: [],
          future: [],
          executionState: {
            flowState: snapshot.state,
            running: snapshot.state === "RUNNING",
            websocketConnected: state.executionState.websocketConnected,
            lastEventType: eventType ?? state.executionState.lastEventType,
            lastUpdated: timestamp ?? state.executionState.lastUpdated,
            error: state.executionState.error,
          },
        };
      }

      return {
        nodes: state.nodes.map((node) => mergeSnapshotIntoNode(node, snapshot)),
        edges: state.edges.map((edge) => {
          const snapshotEdge = snapshot.edges.find(
            (candidate) =>
              candidate.from_node === edge.source && candidate.to_node === edge.target,
          );
          if (!snapshotEdge) {
            return edge;
          }
          return {
            ...edge,
            label: snapshotEdge.condition,
            data: {
              condition: snapshotEdge.condition,
              label: snapshotEdge.condition,
            },
          };
        }),
        flowId: snapshot.flow_id,
        dirty: state.dirty,
        executionState: {
          flowState: snapshot.state,
          running: snapshot.state === "RUNNING",
          websocketConnected: state.executionState.websocketConnected,
          lastEventType: eventType ?? state.executionState.lastEventType,
          lastUpdated: timestamp ?? state.executionState.lastUpdated,
          error: state.executionState.error,
        },
      };
    }),

  setExecutionError: (message) =>
    set((state) => ({
      executionState: {
        ...state.executionState,
        error: message,
        running: false,
      },
    })),

  setWebSocketConnected: (connected) =>
    set((state) => ({
      executionState: {
        ...state.executionState,
        websocketConnected: connected,
      },
    })),

  undo: () =>
    set((state) => {
      const previous = state.history[state.history.length - 1];
      if (!previous) {
        return state;
      }
      const current = snapshotGraph(state);
      return {
        nodes: previous.nodes,
        edges: previous.edges,
        flowId: previous.flowId,
        dirty: true,
        history: state.history.slice(0, -1),
        future: [current, ...state.future].slice(0, 120),
        selectedNodeId: null,
        selectedEdgeId: null,
      };
    }),

  redo: () =>
    set((state) => {
      const next = state.future[0];
      if (!next) {
        return state;
      }
      const current = snapshotGraph(state);
      return {
        nodes: next.nodes,
        edges: next.edges,
        flowId: next.flowId,
        dirty: true,
        history: [...state.history, current].slice(-120),
        future: state.future.slice(1),
        selectedNodeId: null,
        selectedEdgeId: null,
      };
    }),

  autoLayout: () =>
    set((state) => ({
      ...withHistory(state),
      nodes: autoLayoutNodes(state.nodes, state.edges),
      dirty: true,
    })),

  replaceGraph: (payload) =>
    set({
      nodes: payload.nodes,
      edges: payload.edges,
      flowId: payload.flowId,
      dirty: true,
      history: [],
      future: [],
      selectedNodeId: null,
      selectedEdgeId: null,
      executionState: initialExecutionState,
    }),
}));

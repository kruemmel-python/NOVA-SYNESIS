import type { TaskFlowEdge, TaskFlowNode } from "../types/api";

export function autoLayoutNodes(nodes: TaskFlowNode[], edges: TaskFlowEdge[]): TaskFlowNode[] {
  const incoming = new Map<string, number>();
  const outgoing = new Map<string, string[]>();

  for (const node of nodes) {
    incoming.set(node.id, 0);
    outgoing.set(node.id, []);
  }

  for (const edge of edges) {
    incoming.set(edge.target, (incoming.get(edge.target) ?? 0) + 1);
    outgoing.set(edge.source, [...(outgoing.get(edge.source) ?? []), edge.target]);
  }

  const queue = nodes
    .filter((node) => (incoming.get(node.id) ?? 0) === 0)
    .map((node) => node.id);
  const levels = new Map<string, number>();

  while (queue.length > 0) {
    const nodeId = queue.shift()!;
    const level = levels.get(nodeId) ?? 0;
    for (const target of outgoing.get(nodeId) ?? []) {
      levels.set(target, Math.max(levels.get(target) ?? 0, level + 1));
      incoming.set(target, (incoming.get(target) ?? 1) - 1);
      if ((incoming.get(target) ?? 0) <= 0) {
        queue.push(target);
      }
    }
  }

  const grouped = new Map<number, TaskFlowNode[]>();
  for (const node of nodes) {
    const level = levels.get(node.id) ?? 0;
    grouped.set(level, [...(grouped.get(level) ?? []), node]);
  }

  return [...nodes]
    .sort((left, right) => (levels.get(left.id) ?? 0) - (levels.get(right.id) ?? 0))
    .map((node) => {
      const level = levels.get(node.id) ?? 0;
      const group = grouped.get(level) ?? [];
      const row = group.findIndex((candidate) => candidate.id === node.id);

      return {
        ...node,
        position: {
          x: 80 + level * 340,
          y: 80 + row * 220,
        },
      };
    });
}

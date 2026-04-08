# `frontend/src/types/api.ts`

- Quellpfad: [frontend/src/types/api.ts](../../../../../frontend/src/types/api.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Gemeinsame TypeScript-Schemata fuer API, Snapshots und Editorgraph.

## Wann du diese Datei bearbeitest

Wenn Backend-Vertraege oder UI-Datentypen erweitert werden.

## Exporte und oeffentliche Definitionen

- `ResourceType`: TypeScript-Typ `ResourceType` fuer einen Datenvertrag.
- `RollbackStrategy`: TypeScript-Typ `RollbackStrategy` fuer einen Datenvertrag.
- `TaskStatus`: TypeScript-Typ `TaskStatus` fuer einen Datenvertrag.
- `FlowState`: TypeScript-Typ `FlowState` fuer einen Datenvertrag.
- `TaskFlowNode`: TypeScript-Typ `TaskFlowNode` fuer einen Datenvertrag.
- `TaskFlowEdge`: TypeScript-Typ `TaskFlowEdge` fuer einen Datenvertrag.
- `RetryPolicy`: TypeScript-Typ `RetryPolicy` fuer einen Datenvertrag.
- `AgentSummary`: TypeScript-Typ `AgentSummary` fuer einen Datenvertrag.
- `ResourceSummary`: TypeScript-Typ `ResourceSummary` fuer einen Datenvertrag.
- `TaskNodeData`: TypeScript-Typ `TaskNodeData` fuer einen Datenvertrag.
- `ConditionEdgeData`: TypeScript-Typ `ConditionEdgeData` fuer einen Datenvertrag.
- `TaskSpecModel`: TypeScript-Typ `TaskSpecModel` fuer einen Datenvertrag.
- `EdgeModel`: TypeScript-Typ `EdgeModel` fuer einen Datenvertrag.
- `FlowRequest`: TypeScript-Typ `FlowRequest` fuer einen Datenvertrag.
- `FlowNodeSnapshot`: TypeScript-Typ `FlowNodeSnapshot` fuer einen Datenvertrag.
- `FlowSnapshot`: TypeScript-Typ `FlowSnapshot` fuer einen Datenvertrag.
- `FlowEventMessage`: TypeScript-Typ `FlowEventMessage` fuer einen Datenvertrag.
- `EditorExport`: TypeScript-Typ `EditorExport` fuer einen Datenvertrag.
- `PlannerStatus`: TypeScript-Typ `PlannerStatus` fuer einen Datenvertrag.
- `PlannerGenerateRequest`: TypeScript-Typ `PlannerGenerateRequest` fuer einen Datenvertrag.
- `PlannerGenerateResponse`: TypeScript-Typ `PlannerGenerateResponse` fuer einen Datenvertrag.

## Abhaengigkeiten

- `import type { Edge, Node } from "@xyflow/react";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/api/app.py](../../../src/nova_synesis/api/app.py.md)
- [frontend/src/lib/flowSerialization.ts](../lib/flowSerialization.ts.md)

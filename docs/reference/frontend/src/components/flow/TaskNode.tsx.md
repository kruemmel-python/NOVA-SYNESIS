# `frontend/src/components/flow/TaskNode.tsx`

- Quellpfad: [frontend/src/components/flow/TaskNode.tsx](../../../../../../frontend/src/components/flow/TaskNode.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `TaskNode`: Custom Node fuer einzelne Tasks im Canvas.

## Abhaengigkeiten

- `import { Handle, Position, type NodeProps } from "@xyflow/react";`
- `import { useFlowStore } from "../../store/useFlowStore";`
- `import type { TaskFlowNode } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

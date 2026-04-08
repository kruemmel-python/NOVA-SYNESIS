# `frontend/src/components/flow/FlowCanvas.tsx`

- Quellpfad: [frontend/src/components/flow/FlowCanvas.tsx](../../../../../../frontend/src/components/flow/FlowCanvas.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `FlowCanvas`: React-Flow-Leinwand des Editors.

## Abhaengigkeiten

- `import {`
- `import { useCallback, useRef } from "react";`
- `import { useFlowStore } from "../../store/useFlowStore";`
- `import type { TaskFlowEdge, TaskFlowNode } from "../../types/api";`
- `import { TaskNode } from "./TaskNode";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

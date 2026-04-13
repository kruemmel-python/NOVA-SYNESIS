# `frontend/src/App.tsx`

- Quellpfad: [frontend/src/App.tsx](../../../../frontend/src/App.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Root-Komponente der UI mit Layout, Planner, Versionen, Analytics, Save/Run und Live-Sync.

## Wann du diese Datei bearbeitest

Wenn globale Frontend-Aktionen, Versionierung, Analytics oder das Seitenlayout geaendert werden.

## Exporte und oeffentliche Definitionen

- `App`: React-Komponente `App` fuer einen klar abgegrenzten UI-Bereich.

## Wichtige interne Routinen

- `saveCurrentFlow`: Speichert den aktuellen Canvas als echten Flow im Backend.
- `handleRun`: Speichert bei Bedarf und startet anschliessend die Flow-Ausfuehrung.
- `handleExport`: Exportiert den Editorzustand als JSON-Datei.
- `handleImport`: Importiert einen Editor-Export oder einen nackten FlowRequest.
- `handleGenerateWithPlanner`: Fordert ueber das Backend einen neuen Graphen vom LLM-Planer an.

## Abhaengigkeiten

- `import { ReactFlowProvider } from "@xyflow/react";`
- `import { useCallback, useEffect, useState } from "react";`
- `import { FlowCanvas } from "./components/flow/FlowCanvas";`
- `import { AnalyticsPanel } from "./components/layout/AnalyticsPanel";`
- `import { InspectorPanel } from "./components/layout/InspectorPanel";`
- `import { PlannerComposer } from "./components/layout/PlannerComposer";`
- `import { Sidebar } from "./components/layout/Sidebar";`
- `import { TopBar } from "./components/layout/TopBar";`
- `import { useCatalogBootstrap } from "./hooks/useCatalogBootstrap";`
- `import { useFlowLiveUpdates } from "./hooks/useFlowLiveUpdates";`
- `import {`
- `import { fromFlowRequest, toFlowRequest } from "./lib/flowSerialization";`
- `import { prettyJson, safeJsonParse } from "./lib/json";`
- `import { useFlowStore } from "./store/useFlowStore";`
- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/store/useFlowStore.ts](store/useFlowStore.ts.md)
- [frontend/src/components/layout/TopBar.tsx](components/layout/TopBar.tsx.md)

# `frontend/src/hooks/useFlowLiveUpdates.ts`

- Quellpfad: [frontend/src/hooks/useFlowLiveUpdates.ts](../../../../../frontend/src/hooks/useFlowLiveUpdates.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `useFlowLiveUpdates`: Funktion oder Definition `useFlowLiveUpdates` dieses Moduls.

## Abhaengigkeiten

- `import { useEffect } from "react";`
- `import { fetchFlow, getWebSocketBaseUrl } from "../lib/apiClient";`
- `import { useFlowStore } from "../store/useFlowStore";`
- `import type { FlowEventMessage } from "../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

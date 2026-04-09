# `frontend/src/hooks/useCatalogBootstrap.ts`

- Quellpfad: [frontend/src/hooks/useCatalogBootstrap.ts](../../../../../frontend/src/hooks/useCatalogBootstrap.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `useCatalogBootstrap`: Funktion oder Definition `useCatalogBootstrap` dieses Moduls.

## Abhaengigkeiten

- `import { useEffect } from "react";`
- `import { fetchAgents, fetchHandlers, fetchResources } from "../lib/apiClient";`
- `import { useFlowStore } from "../store/useFlowStore";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

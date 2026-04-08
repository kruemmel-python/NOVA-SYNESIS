# `frontend/src/store/useFlowStore.ts`

- Quellpfad: [frontend/src/store/useFlowStore.ts](../../../../../frontend/src/store/useFlowStore.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Zustand-Store fuer Graph, Auswahl, Undo/Redo und Laufzeitstatus.

## Wann du diese Datei bearbeitest

Wenn Editorverhalten oder Snapshot-Uebernahme angepasst werden.

## Exporte und oeffentliche Definitionen

- `useFlowStore`: Globaler Zustandsspeicher der UI auf Basis von Zustand.

## Wichtige interne Routinen

- `snapshotGraph`: Erzeugt einen unveraenderlichen Graph-Snapshot fuer Undo/Redo.
- `withHistory`: Haengt den aktuellen Zustand an die Undo-Historie an.
- `mergeSnapshotIntoNode`: Uebernimmt Runtime-Daten aus einem Backend-Snapshot in einen Editor-Node.

## Abhaengigkeiten

- `import {`
- `import { create } from "zustand";`
- `import { autoLayoutNodes } from "../lib/autoLayout";`
- `import {`
- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/App.tsx](../App.tsx.md)
- [frontend/src/hooks/useFlowLiveUpdates.ts](../hooks/useFlowLiveUpdates.ts.md)

# `frontend/src/components/layout/Sidebar.tsx`

- Quellpfad: [frontend/src/components/layout/Sidebar.tsx](../../../../../../frontend/src/components/layout/Sidebar.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Linke Katalogleiste mit Handlern, Agenten und Ressourcen.

## Wann du diese Datei bearbeitest

Wenn Drag-and-Drop oder Katalogdarstellung geaendert wird.

## Exporte und oeffentliche Definitionen

- `Sidebar`: Funktion oder Definition `Sidebar` dieses Moduls.

## Abhaengigkeiten

- `import { useMemo, useState } from "react";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import { useFlowStore } from "../../store/useFlowStore";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/components/flow/FlowCanvas.tsx](../flow/FlowCanvas.tsx.md)
- [frontend/src/store/useFlowStore.ts](../../store/useFlowStore.ts.md)

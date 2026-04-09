# `frontend/src/components/layout/TopBar.tsx`

- Quellpfad: [frontend/src/components/layout/TopBar.tsx](../../../../../../frontend/src/components/layout/TopBar.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Globale Aktionsleiste fuer Save, Run, Planner, Import und Export.

## Wann du diese Datei bearbeitest

Wenn globale Bedienaktionen oder Statusanzeigen geaendert werden.

## Exporte und oeffentliche Definitionen

- `TopBar`: Funktion oder Definition `TopBar` dieses Moduls.

## Wichtige interne Routinen

- `statusTone`: Ordnet globale Flow-Zustaende den Topbar-Badge-Farben zu.

## Abhaengigkeiten

- `import { useRef } from "react";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import type { PlannerStatus } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/App.tsx](../../App.tsx.md)
- [frontend/src/components/common/StatusBadge.tsx](../common/StatusBadge.tsx.md)

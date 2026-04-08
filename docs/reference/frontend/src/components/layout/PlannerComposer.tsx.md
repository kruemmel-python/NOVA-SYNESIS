# `frontend/src/components/layout/PlannerComposer.tsx`

- Quellpfad: [frontend/src/components/layout/PlannerComposer.tsx](../../../../../../frontend/src/components/layout/PlannerComposer.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Planner-Dialog fuer die lokale LLM-Graph-Erzeugung.

## Wann du diese Datei bearbeitest

Wenn Prompting-UX oder Planner-Rueckmeldungen im Frontend erweitert werden.

## Exporte und oeffentliche Definitionen

- `PlannerComposer`: Dialog fuer die autonome Graph-Erzeugung.

## Abhaengigkeiten

- `import { useEffect, useState } from "react";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import type { PlannerGenerateResponse, PlannerStatus } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/App.tsx](../../App.tsx.md)
- [src/nova_synesis/planning/lit_planner.py](../../../../src/nova_synesis/planning/lit_planner.py.md)

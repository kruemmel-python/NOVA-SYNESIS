# `frontend/src/components/layout/AnalyticsPanel.tsx`

- Quellpfad: [frontend/src/components/layout/AnalyticsPanel.tsx](../../../../../../frontend/src/components/layout/AnalyticsPanel.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Kompakte Betriebsansicht fuer aggregierte Flow- und Handler-Metriken direkt in der Web-UI.

## Wann du diese Datei bearbeitest

Wenn Analytics-Kennzahlen, Darstellung oder Drilldowns fuer Betreiber erweitert werden sollen.

## Exporte und oeffentliche Definitionen

- `AnalyticsPanel`: Frontend-Modal fuer aggregierte Flow- und Handlermetriken.

## Abhaengigkeiten

- `import type { MetricsSummary } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/App.tsx](../../App.tsx.md)
- [frontend/src/lib/apiClient.ts](../../lib/apiClient.ts.md)
- [src/nova_synesis/api/app.py](../../../../src/nova_synesis/api/app.py.md)

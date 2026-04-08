# `frontend/src/components/layout/InspectorPanel.tsx`

- Quellpfad: [frontend/src/components/layout/InspectorPanel.tsx](../../../../../../frontend/src/components/layout/InspectorPanel.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Node- und Edge-Inspector fuer bearbeitbare Eigenschaften.

## Wann du diese Datei bearbeitest

Wenn weitere konfigurierbare Felder in der UI auftauchen sollen.

## Exporte und oeffentliche Definitionen

- `InspectorPanel`: Eigenschaftseditor fuer Nodes und Edges.

## Wichtige interne Routinen

- `patchNode`: Wendet ein Teilupdate auf die Daten eines Nodes an.
- `splitCsv`: Konvertiert komma-separierte Texte in Stringlisten.
- `asObject`: Normalisiert unbekannte Werte zu einem sicheren Objekt.
- `statusTone`: Ordnet Task-Status einer Badge-Farbe zu.
- `handleApproveNode`: Freigabe eines Nodes lokal oder ueber die Approval-API.
- `handleRevokeNodeApproval`: Hebt eine bestehende manuelle Freigabe lokal oder ueber die Approval-API auf.
- `NodeField`: Hilfskomponente fuer einfache Texteingaben im Inspector.
- `NumericField`: Hilfskomponente fuer numerische Eingaben im Inspector.

## Abhaengigkeiten

- `import { JsonEditor } from "../common/JsonEditor";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import { approveFlowNode, revokeFlowNodeApproval } from "../../lib/apiClient";`
- `import { useFlowStore } from "../../store/useFlowStore";`
- `import type { ResourceType, RollbackStrategy, TaskFlowNode } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/store/useFlowStore.ts](../../store/useFlowStore.ts.md)
- [frontend/src/components/common/JsonEditor.tsx](../common/JsonEditor.tsx.md)

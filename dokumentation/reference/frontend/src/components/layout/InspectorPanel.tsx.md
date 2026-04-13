# `frontend/src/components/layout/InspectorPanel.tsx`

- Quellpfad: [frontend/src/components/layout/InspectorPanel.tsx](../../../../../../frontend/src/components/layout/InspectorPanel.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Node- und Edge-Inspector fuer bearbeitbare Eigenschaften, manuelle Freigaben, HITL-Resume und lokale LLM-Briefvorschauen.

## Wann du diese Datei bearbeitest

Wenn weitere konfigurierbare Felder, Approval-/Resume-Aktionen oder interaktive Vorschaufunktionen in der UI auftauchen sollen.

## Exporte und oeffentliche Definitionen

- `InspectorPanel`: Eigenschaftseditor fuer Nodes und Edges.

## Wichtige interne Routinen

- `patchNode`: Wendet ein Teilupdate auf die Daten eines Nodes an.
- `patchNodeInputObject`: Aktualisiert gezielt Felder innerhalb des Node-Inputs, ohne das restliche Objekt zu verlieren.
- `findReceivableExtractNode`: Findet den zum Forderungs-Use-Case gehoerigen Extract-Node fuer serverseitige Vorschaulaufe.
- `splitCsv`: Konvertiert komma-separierte Texte in Stringlisten.
- `asObject`: Normalisiert unbekannte Werte zu einem sicheren Objekt.
- `asNodeInputObject`: Normalisiert den Node-Input fuer Inspector-Operationen zu einem veraenderbaren Objekt.
- `readReceivableDraftingConfig`: Leitet den aktiven LLM-Schreibmodus und seine Prompt-Felder aus dem Node-Input ab.
- `statusTone`: Ordnet Task-Status einer Badge-Farbe zu.
- `handleApproveNode`: Freigabe eines Nodes lokal oder ueber die Approval-API.
- `handleRevokeNodeApproval`: Hebt eine bestehende manuelle Freigabe lokal oder ueber die Approval-API auf.
- `handlePreviewDraft`: Fordert ueber das Backend eine einzelne LLM-Briefvorschau fuer den aktuell konfigurierten Forderungs-Node an.
- `NodeField`: Hilfskomponente fuer einfache Texteingaben im Inspector.
- `NumericField`: Hilfskomponente fuer numerische Eingaben im Inspector.

## Abhaengigkeiten

- `import { useEffect, useState } from "react";`
- `import { JsonEditor } from "../common/JsonEditor";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import {`
- `import { useFlowStore } from "../../store/useFlowStore";`
- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/store/useFlowStore.ts](../../store/useFlowStore.ts.md)
- [frontend/src/components/common/JsonEditor.tsx](../common/JsonEditor.tsx.md)
- [src/nova_synesis/api/app.py](../../../../src/nova_synesis/api/app.py.md)

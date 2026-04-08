# `frontend/src/lib/flowSerialization.ts`

- Quellpfad: [frontend/src/lib/flowSerialization.ts](../../../../../frontend/src/lib/flowSerialization.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Uebersetzung zwischen React-Flow und echtem Backend-Flow-Schema.

## Wann du diese Datei bearbeitest

Wenn Node-Felder oder Flow-Schema geaendert werden.

## Exporte und oeffentliche Definitionen

- `createTaskNode`: Erzeugt einen neuen Task-Node mit Defaultwerten.
- `createTaskEdge`: Erzeugt eine neue Kante mit Standardbedingung.
- `toTaskSpec`: Funktion oder Definition `toTaskSpec` dieses Moduls.
- `toEdgeModel`: Funktion oder Definition `toEdgeModel` dieses Moduls.
- `toFlowRequest`: Serialisiert den Editorgraphen exakt in das Backend-Schema.
- `fromFlowSnapshot`: Wandelt einen Backend-Snapshot in React-Flow-Elemente um.
- `fromFlowRequest`: Funktion oder Definition `fromFlowRequest` dieses Moduls.
- `humanizeHandlerName`: Funktion oder Definition `humanizeHandlerName` dieses Moduls.
- `DEFAULT_RETRY_POLICY`: Funktion oder Definition `DEFAULT_RETRY_POLICY` dieses Moduls.
- `DEFAULT_ROLLBACK_STRATEGY`: Funktion oder Definition `DEFAULT_ROLLBACK_STRATEGY` dieses Moduls.
- `DEFAULT_MANUAL_APPROVAL`: Funktion oder Definition `DEFAULT_MANUAL_APPROVAL` dieses Moduls.

## Wichtige interne Routinen

- `readUiMetadata`: Liest UI-spezifische Metadaten aus dem allgemeinen Metadata-Objekt.
- `asPosition`: Leitet eine gueltige Canvas-Position aus Metadaten oder Fallbacks ab.
- `snapshotNodeToEditorNode`: Wandelt einen Backend-Node-Snapshot in einen Editor-Node um.

## Abhaengigkeiten

- `import { MarkerType } from "@xyflow/react";`
- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/types/api.ts](../types/api.ts.md)
- [src/nova_synesis/api/app.py](../../../src/nova_synesis/api/app.py.md)

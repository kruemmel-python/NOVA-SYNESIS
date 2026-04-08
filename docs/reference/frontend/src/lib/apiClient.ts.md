# `frontend/src/lib/apiClient.ts`

- Quellpfad: [frontend/src/lib/apiClient.ts](../../../../../frontend/src/lib/apiClient.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Echter API-Client fuer REST und WebSocket-Basis-URLs.

## Wann du diese Datei bearbeitest

Wenn neue Backend-Endpunkte im Frontend angebunden werden.

## Exporte und oeffentliche Definitionen

- `getApiBaseUrl`: Funktion oder Definition `getApiBaseUrl` dieses Moduls.
- `getWebSocketBaseUrl`: Funktion oder Definition `getWebSocketBaseUrl` dieses Moduls.
- `fetchPlannerStatus`: Funktion oder Definition `fetchPlannerStatus` dieses Moduls.
- `fetchAgents`: Funktion oder Definition `fetchAgents` dieses Moduls.
- `fetchResources`: Funktion oder Definition `fetchResources` dieses Moduls.
- `createFlow`: Funktion oder Definition `createFlow` dieses Moduls.
- `runFlow`: Steuert den Ablauf von `runFlow`.
- `fetchFlow`: Funktion oder Definition `fetchFlow` dieses Moduls.
- `generateFlowWithPlanner`: Funktion oder Definition `generateFlowWithPlanner` dieses Moduls.

## Abhaengigkeiten

- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/api/app.py](../../../src/nova_synesis/api/app.py.md)
- [frontend/src/types/api.ts](../types/api.ts.md)

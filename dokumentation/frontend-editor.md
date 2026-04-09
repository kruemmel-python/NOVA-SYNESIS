# Frontend-Editor

Die UI besteht aus `App.tsx`, dem Zustand-Store `useFlowStore.ts`, der Zeichenflaeche `FlowCanvas.tsx`, der linken `Sidebar.tsx`, dem `InspectorPanel.tsx`, dem Planner-Dialog und der `TopBar.tsx`.

## Was der Editor wirklich tut

- laedt Handler, Agenten und Ressourcen aus dem echten Backend
- baut daraus React-Flow-Nodes und -Edges
- serialisiert den Editorzustand ueber `toFlowRequest()`
- speichert und startet echte Flows
- uebernimmt Live-Snapshots ueber WebSocket oder Polling
- zeigt pro Node Handler-Trust und manuelle Freigaben im Inspector

## Kritische Integrationsstellen

- `frontend/src/lib/flowSerialization.ts`: muss exakt zum FastAPI-Schema passen
- `frontend/src/lib/apiClient.ts`: enthaelt die echten REST-, Approval- und WebSocket-Aufrufe inklusive `POST /flows/validate`
- `frontend/src/store/useFlowStore.ts`: haelt den kanonischen UI-Zustand fuer Nodes, Edges, Auswahl und Laufzeitstatus
- `frontend/src/hooks/useFlowLiveUpdates.ts`: faellt bei Socket-Problemen auf Polling zurueck

## Betreiberperspektive im Inspector

- `Handler trust` zeigt Zertifikatsstatus, Issuer, Fingerprint und Ablaufdatum
- `Require manual approval before execution` markiert einen Node als freigabepflichtig
- `Approve Node` und `Revoke Approval` sprechen direkt mit der Approval-API, wenn der Flow bereits gespeichert ist
- bei ungespeicherten lokalen Aenderungen arbeitet der Inspector bewusst lokal weiter, um den Canvas-Zustand nicht zu ueberschreiben

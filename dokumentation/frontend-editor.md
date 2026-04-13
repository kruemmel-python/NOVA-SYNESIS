# Frontend-Editor

Die UI besteht aus `App.tsx`, dem Zustand-Store `useFlowStore.ts`, der Zeichenflaeche `FlowCanvas.tsx`, der linken `Sidebar.tsx`, dem `InspectorPanel.tsx`, dem Planner-Dialog und der `TopBar.tsx`.

## Was der Editor wirklich tut

- laedt Handler, Agenten und Ressourcen aus dem echten Backend
- baut daraus React-Flow-Nodes und -Edges
- serialisiert den Editorzustand ueber `toFlowRequest()`
- speichert Flow-Container und neue Flow-Versionen
- startet echte Flows gegen die aktive oder geladene Version
- uebernimmt Live-Snapshots ueber WebSocket oder Polling
- zeigt pro Node Handler-Trust, manuelle Freigaben und HITL-Zustaende im Inspector
- oeffnet ueber ein Analytics-Panel aggregierte Handler- und Flow-Metriken

## Kritische Integrationsstellen

- `frontend/src/lib/flowSerialization.ts`: muss exakt zum FastAPI-Schema passen
- `frontend/src/lib/apiClient.ts`: enthaelt die echten REST-, Versions-, Approval-, Resume-, Preview-, Metrics- und WebSocket-Aufrufe inklusive `POST /flows/validate`
- `frontend/src/store/useFlowStore.ts`: haelt den kanonischen UI-Zustand fuer Nodes, Edges, Auswahl, Versionen und Laufzeitstatus
- `frontend/src/hooks/useFlowLiveUpdates.ts`: faellt bei Socket-Problemen auf Polling zurueck

## Topbar und Versionen

- `Save Flow` legt bei einem bereits bestehenden Flow keine stillschweigende Ueberschreibung mehr an, sondern erzeugt eine neue Version
- die Versionsauswahl in `TopBar.tsx` laedt eine konkrete persistierte Version zurueck in den Canvas
- `Run Flow` verwendet die aktuell geladene Version, sofern eine `flowVersionId` vorhanden ist
- `Analytics` oeffnet eine kompakte Betreiberansicht auf Handler- und Flow-Metriken

## Human-in-the-Loop im Inspector

- wenn ein Node den Status `WAITING_FOR_INPUT` meldet, laedt der Inspector automatisch die offene Eingabeanforderung
- das Formular wird aus dem gelieferten JSON-Schema aufgebaut; bei komplexeren Strukturen gibt es einen JSON-Fallback
- `Submit Input` ruft `POST /flows/{flow_id}/nodes/{node_id}/resume` auf
- `Submitted by` wird mitpersistiert und ist Teil des Audit-Pfads
- wenn die Anforderung eine Rolle enthaelt, zeigt der Inspector diese als `Erforderliche Rolle` an
- ein `WAITING_FOR_INPUT`-Node ist kein Absturz, sondern ein kontrollierter Runtime-Stopp bis zur menschlichen Antwort

## Betreiberperspektive im Inspector

- `Handler trust` zeigt Zertifikatsstatus, Issuer, Fingerprint und Ablaufdatum
- `Require manual approval before execution` markiert einen Node als freigabepflichtig
- `Approval granted` setzt die Freigabe per Checkbox; bei bereits gespeichertem Flow wird die Approval-API direkt genutzt
- ohne gesetzten Freigabe-Haken bleibt ein freigabepflichtiger Node im Status `Pending`
- der Node `Generate Reminder Letters` besitzt zusaetzlich den Bereich `LLM Letter Drafting`
- `Use local LLM to draft the letter text` schaltet den Handler von festem Template auf lokalen LiteRT-Textentwurf um
- `Business instruction` steuert den fachlichen Ton des Briefs direkt durch den Benutzer
- `Prompt template` definiert den vollstaendigen Modellprompt pro Kunde mit Platzhaltern wie `{customer_name}`, `{invoice_lines}` oder `{total_outstanding}`
- `Preview Draft` ruft `POST /tools/accounts-receivable/preview-draft` auf, laesst serverseitig nur den Extract-Schritt plus einen einzelnen LLM-Entwurf laufen und zeigt Prompt und Ergebnis im Inspector an
- `Preview customer index` waehlt aus, fuer welchen Kunden aus der aktuellen Quelldatei die Vorschau erzeugt wird
- Vorschau-Requests sind zeitlich begrenzt, damit die UI nicht unbegrenzt auf ein blockiertes oder zu langsames lokales Modell warten muss
- bei ungespeicherten lokalen Aenderungen arbeitet der Inspector bewusst lokal weiter, um den Canvas-Zustand nicht zu ueberschreiben
- wenn RBAC aktiv ist, bleibt die echte Freigabe- oder Resume-Entscheidung trotzdem serverseitig; die UI ist nur die Bedienflaeche

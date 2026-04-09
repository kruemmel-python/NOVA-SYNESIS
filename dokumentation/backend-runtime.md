# Backend-Laufzeit

Die Backend-Laufzeit wird durch `OrchestratorService` zusammengesetzt. Er verdrahtet Repository, Speicher, Ressourcenmanager, Handler-Registry, Planner, Semantic Firewall und Execution-Engine.

## Reihenfolge eines normalen Flows

1. API nimmt einen `FlowCreateRequest` oder eine Planner-Anfrage entgegen.
2. `TaskHandlerRegistry` bewertet alle Handler gegen digitale Zertifikate und erzeugt Trust-Records.
3. `OrchestratorService.validate_flow_request()` laesst die semantische Firewall laufen.
4. Der Flow wird in Domaenenobjekte ueberfuehrt und in SQLite gespeichert.
5. `FlowExecutor.run_flow()` startet die DAG-Ausfuehrung.
6. `TaskExecutor.execute_task()` loest Templates auf, reserviert Ressourcen, ruft Agent und Handler auf und persistiert Snapshots.
7. WebSocket-Abonnenten erhalten Ereignisse wie `flow.started`, `node.completed`, `node.approval.updated` oder `flow.failed`.

## Trust- und Approval-Gates

- `GET /handlers` ist die kanonische Betriebsansicht auf Handler-Trust.
- Der Planner-Katalog enthaelt nur trusted Handler.
- Freigaben liegen an `Task.manual_approval` und werden im Flow-Snapshot persistiert.
- `POST /flows/{flow_id}/nodes/{node_id}/approval` und `DELETE /flows/{flow_id}/nodes/{node_id}/approval` aendern den Freigabestatus ohne den ganzen Flow neu anzulegen.

## Regel fuer Aenderungen

Wenn du etwas an einem Runtime-Vertrag aenderst, pruefe fast immer gleichzeitig API, Domaenenmodell, Engine, Frontend-Typen, Serialisierung und Tests.

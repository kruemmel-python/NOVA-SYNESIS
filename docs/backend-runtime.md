# Backend-Laufzeit

Die Backend-Laufzeit wird durch `OrchestratorService` zusammengesetzt. Er verdrahtet Repository, Speicher, Ressourcenmanager, Handler-Registry, Planner, Semantic Firewall und Execution-Engine.

## Reihenfolge eines normalen Flows

1. API nimmt einen `FlowCreateRequest` oder eine Planner-Anfrage entgegen.
2. `OrchestratorService.validate_flow_request()` laesst die semantische Firewall laufen.
3. Der Flow wird in Domaenenobjekte ueberfuehrt und in SQLite gespeichert.
4. `FlowExecutor.run_flow()` startet die DAG-Ausfuehrung.
5. `TaskExecutor.execute_task()` loest Templates auf, reserviert Ressourcen, ruft Agent und Handler auf und persistiert Snapshots.
6. WebSocket-Abonnenten erhalten Ereignisse wie `flow.started`, `node.completed` oder `flow.failed`.

## Regel fuer Aenderungen

Wenn du etwas an einem Runtime-Vertrag aenderst, pruefe fast immer gleichzeitig API, Domaenenmodell, Engine, Frontend-Typen, Serialisierung und Tests.

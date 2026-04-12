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

## Relevante Runtime-Handler fuer freie Arbeitsablaeufe

- `news_search` zieht Nachrichten intern ueber RSS und braucht keine manuell gesetzte Ziel-URL
- `topic_split` erwartet eine echte Listenstruktur in `items` und erzeugt daraus `categorized_items` und `csv_rows`
- `generate_embedding` erzeugt den Vektor-Payload fuer `memory_store` in Vector-Memories
- `memory_store` speichert einfache Werte oder Embeddings; bei alten Platzhalter-Flows biegt der Runtime-Pfad offensichtliche Scheindaten auf das echte Upstream-Ergebnis um
- `filesystem_read` und `filesystem_write` sind technische Alias-Handler fuer lokale Datei-Workflows und vereinheitlichen Planner-Prompts fuer Audit- oder Reporting-Flows
- `local_llm_text` ist der generische lokale Text- und Analyse-Handler fuer Review-, Audit-, Zusammenfassungs- und Reporting-Nodes

## Audit- und Analyse-Pfade mit lokalem LLM

- Ein typischer lokaler Audit-Flow liest zunaechst eine Datei ueber `filesystem_read`
- Danach analysiert `local_llm_text` den Dateiinhalt mit einem Prompt oder einer standardisierten Audit-Instruktion
- Wenn Upstream-Daten vorhanden sind, kombiniert der Handler Prompt und Daten zu einer finalen Modellanfrage
- Meta-Antworten wie `Please provide ...` werden serverseitig abgefangen und in eine direkte Endausgabe umgelenkt, damit kein halbfertiger Rueckfrage-Text im Report landet
- `filesystem_write` speichert die finalen Analyse- oder Reporttexte wieder lokal ab

## Regel fuer Aenderungen

Wenn du etwas an einem Runtime-Vertrag aenderst, pruefe fast immer gleichzeitig API, Domaenenmodell, Engine, Frontend-Typen, Serialisierung und Tests.

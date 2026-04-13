# Backend-Laufzeit

Die Backend-Laufzeit wird durch `OrchestratorService` zusammengesetzt. Er verdrahtet Repository, Speicher, Ressourcenmanager, Handler-Registry, Planner, Semantic Firewall und Execution-Engine.

## Flow-Container und Versionen

- `POST /flows` erzeugt einen logischen Flow-Container und legt direkt `version 1` an
- `POST /flows/{flow_id}/versions` schreibt spaetere Graphaenderungen als neue unveraenderliche Version
- `POST /flows/{flow_id}/versions/{version_id}/activate` setzt die Zielversion fuer spaetere Loads und Runs
- `run_flow(..., version_id=...)` kann bewusst gegen eine nicht aktive Version laufen
- die Persistenz dafuer liegt in `flows` plus `flow_versions` innerhalb von `SQLiteRepository`

## Reihenfolge eines normalen Flows

1. API nimmt einen `FlowCreateRequest`, eine Planner-Anfrage oder einen Versions-Write entgegen.
2. `TaskHandlerRegistry` bewertet alle Handler gegen digitale Zertifikate und erzeugt Trust-Records.
3. `OrchestratorService.validate_flow_request()` laesst die semantische Firewall laufen.
4. Der Flow wird in Domaenenobjekte ueberfuehrt und als Version in SQLite gespeichert.
5. `FlowExecutor.run_flow()` startet die DAG-Ausfuehrung gegen eine konkrete Flow-Version.
6. `TaskExecutor.execute_task()` loest Templates auf, reserviert Ressourcen, ruft Agent und Handler auf und persistiert Snapshots.
7. Handler koennen Erfolg, Fehler oder `WAITING_FOR_INPUT` melden.
8. WebSocket-Abonnenten erhalten Ereignisse wie `flow.started`, `node.completed`, `node.waiting_for_input`, `node.approval.updated` oder `flow.failed`.

## Human in the Loop und Resume

- der Built-in-Handler `human_input_request` wirft intern eine `HumanInputRequiredError`
- die Engine persistiert dadurch keinen Crash, sondern einen kontrollierten `WAITING_FOR_INPUT`-Zustand
- offene Eingaben liegen serialisiert am Node und koennen ueber `GET /flows/{flow_id}/nodes/{node_id}/input-request` gelesen werden
- `POST /flows/{flow_id}/nodes/{node_id}/resume` uebergibt die Benutzerantwort, die danach in `results[node_id]` landet
- `FlowExecutor` setzt den pausierten Graphen ab dem wartenden Node fort, statt den gesamten Flow neu aufzubauen

## Telemetrie und Analytics

- jeder ausgefuehrte Task schreibt Laufzeitdaten wie Start, Ende, Status und `latency_ms`
- LLM-nahe Handler koennen zusaetzliche Metadaten wie geschaetzte Prompt- und Completion-Tokens mitgeben
- `SQLiteRepository.save_execution_metric()` persistiert diese Daten fuer Auswertungen
- `GET /metrics/summary`, `GET /metrics/flows` und `GET /metrics/handlers` liefern die aggregierte Betreiberansicht

## Rollen und serverseitige Freigaben

- RBAC wird nicht im Frontend entschieden, sondern in `OrchestratorService._ensure_actor_role()`
- Approvals und HITL-Resumes koennen einen `required_role` erzwingen
- wenn `NS_SECURITY_RBAC_ENABLED=true` aktiv ist, erwartet die API standardmaessig `X-NOVA-User` und `X-NOVA-Roles`
- die Default-Rolle fuer manuelle Freigaben ist `approver`, solange keine node-spezifische Rolle gesetzt ist

## Sub-Flows

- `execute_subflow` ist ein echter Built-in-Handler und kein UI-Trick
- der Handler startet ueber den Orchestrator einen Child-Flow in isoliertem Unterkontext
- `target_version_id` ist fuer reproduzierbare Child-Runs der saubere Pfad; ohne diese Angabe gibt die Policy bewusst eine Warnung aus
- Parent- und Child-Run haben getrennte Snapshots, aber der Rueckgabewert des Child-Flows wird als Ergebnis des Parent-Nodes veroeffentlicht

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
- `human_input_request` pausiert einen Flow kontrolliert und fordert strukturierte Benutzereingaben an
- `execute_subflow` kapselt einen anderen gespeicherten Flow als wiederverwendbaren Child-Baustein

## Audit- und Analyse-Pfade mit lokalem LLM

- Ein typischer lokaler Audit-Flow liest zunaechst eine Datei ueber `filesystem_read`
- Danach analysiert `local_llm_text` den Dateiinhalt mit einem Prompt oder einer standardisierten Audit-Instruktion
- Wenn Upstream-Daten vorhanden sind, kombiniert der Handler Prompt und Daten zu einer finalen Modellanfrage
- Meta-Antworten wie `Please provide ...` werden serverseitig abgefangen und in eine direkte Endausgabe umgelenkt, damit kein halbfertiger Rueckfrage-Text im Report landet
- `filesystem_write` speichert die finalen Analyse- oder Reporttexte wieder lokal ab

## Regel fuer Aenderungen

Wenn du etwas an einem Runtime-Vertrag aenderst, pruefe fast immer gleichzeitig API, Domaenenmodell, Engine, Frontend-Typen, Serialisierung und Tests.

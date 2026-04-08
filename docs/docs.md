# CodeDump for Project: `docs.zip`

_Generated on 2026-04-08T22:12:01.302991+00:00_

## File: `backend-runtime.md`  
- Path: `backend-runtime.md`  
- Size: 975 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
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
```

## File: `change-workflows.md`  
- Path: `change-workflows.md`  
- Size: 1135 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# Aenderungsleitfaden

## Neuer Handler

1. Handler in `runtime/handlers.py` implementieren und registrieren
2. pruefen, ob der Handler im Planner sichtbar sein soll
3. Security-Regeln fuer Egress, Templates oder Seiteneffekte in `security/policy.py` bewerten
4. Tests in `tests/test_orchestrator.py` erweitern
5. Frontend prueft den Handler automatisch ueber `/handlers`
6. `tools/generate_docs.py` und danach `docs/` neu erzeugen

## Neues Node-Feld

1. Backend-Schema in `api/app.py`
2. Domaenenmodell und Snapshot in `domain/models.py`
3. TypeScript-Typen in `frontend/src/types/api.ts`
4. Serialisierung in `frontend/src/lib/flowSerialization.ts`
5. Inspector in `frontend/src/components/layout/InspectorPanel.tsx`
6. Validierung und Security-Auswirkungen pruefen
7. Tests und Dokumentation nachziehen

## Neue Security-Regel

1. Policy in `security/policy.py` erweitern
2. Settings in `config.py` und `.env.example` nachziehen
3. API- und Planner-Auswirkungen pruefen
4. mindestens einen positiven und einen negativen Testfall schreiben
5. `tools/generate_docs.py` ausfuehren und `docs/` neu erzeugen
```

## File: `coverage.md`  
- Path: `coverage.md`  
- Size: 3486 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# Abdeckung

- Dokumentierte Projektdateien: `80`
- Referenzdateien: `81`

## Ausgeschlossene Bereiche

- `data/`, `debug_tmp/`, `planner_live_check*/`, `ws_debug/`: Laufzeit- und Debug-Artefakte
- `frontend/node_modules/`, `frontend/dist/`: Fremd- und Buildartefakte
- `__pycache__/`, `.pytest_cache/`: Cache-Verzeichnisse
- `.git/`, `release/`, lokale `.env`, `Use_Cases/**/output`, `Use_Cases/**/state`, `*.zip`, `*.exe`, `*.db`, `*.pdf`, `*.litertlm`, `*.xnnpack_cache`, `*.tsbuildinfo`: Artefakte, Binaries oder maschinenlokale Dateien

## Dokumentierte Dateien

- `.env.example`
- `.gitignore`
- `Anweisung.md`
- `Dockerfile`
- `LICENSE`
- `LIT/README.md`
- `LIT/planner_test_prompt.txt`
- `README.md`
- `Use_Cases/README.md`
- `Use_Cases/platform_health_snapshot/README.md`
- `Use_Cases/platform_health_snapshot/flow.json`
- `Use_Cases/platform_health_snapshot/run.ps1`
- `Use_Cases/platform_health_snapshot/setup.ps1`
- `Use_Cases/semantic_ticket_triage/README.md`
- `Use_Cases/semantic_ticket_triage/flow.json`
- `Use_Cases/semantic_ticket_triage/run.ps1`
- `Use_Cases/semantic_ticket_triage/setup.ps1`
- `frontend/.env.example`
- `frontend/index.html`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/app.css`
- `frontend/src/components/common/JsonEditor.tsx`
- `frontend/src/components/common/StatusBadge.tsx`
- `frontend/src/components/flow/FlowCanvas.tsx`
- `frontend/src/components/flow/TaskNode.tsx`
- `frontend/src/components/layout/InspectorPanel.tsx`
- `frontend/src/components/layout/PlannerComposer.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/TopBar.tsx`
- `frontend/src/hooks/useCatalogBootstrap.ts`
- `frontend/src/hooks/useFlowLiveUpdates.ts`
- `frontend/src/lib/apiClient.ts`
- `frontend/src/lib/autoLayout.ts`
- `frontend/src/lib/flowSerialization.ts`
- `frontend/src/lib/json.ts`
- `frontend/src/main.tsx`
- `frontend/src/store/useFlowStore.ts`
- `frontend/src/types/api.ts`
- `frontend/src/vite-env.d.ts`
- `frontend/tsconfig.app.json`
- `frontend/tsconfig.json`
- `frontend/tsconfig.node.json`
- `frontend/vite.config.d.ts`
- `frontend/vite.config.js`
- `frontend/vite.config.ts`
- `pyproject.toml`
- `run-backend.cmd`
- `run-backend.ps1`
- `src/nova_synesis/__init__.py`
- `src/nova_synesis/api/__init__.py`
- `src/nova_synesis/api/app.py`
- `src/nova_synesis/cli.py`
- `src/nova_synesis/communication/__init__.py`
- `src/nova_synesis/communication/adapters.py`
- `src/nova_synesis/config.py`
- `src/nova_synesis/domain/__init__.py`
- `src/nova_synesis/domain/models.py`
- `src/nova_synesis/memory/__init__.py`
- `src/nova_synesis/memory/systems.py`
- `src/nova_synesis/persistence/__init__.py`
- `src/nova_synesis/persistence/sqlite_repository.py`
- `src/nova_synesis/planning/__init__.py`
- `src/nova_synesis/planning/lit_planner.py`
- `src/nova_synesis/planning/planner.py`
- `src/nova_synesis/resources/__init__.py`
- `src/nova_synesis/resources/manager.py`
- `src/nova_synesis/runtime/__init__.py`
- `src/nova_synesis/runtime/engine.py`
- `src/nova_synesis/runtime/handlers.py`
- `src/nova_synesis/security/__init__.py`
- `src/nova_synesis/security/policy.py`
- `src/nova_synesis/services/__init__.py`
- `src/nova_synesis/services/orchestrator.py`
- `tests/test_orchestrator.py`
- `tools/build_code_release.ps1`
- `tools/generate_docs.py`
- `uml.html`
- `uml_V3.mmd`
```

## File: `decision-guide.md`  
- Path: `decision-guide.md`  
- Size: 3908 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# Decision Guide

Diese Seite dokumentiert Entscheidungslogik. Genau dieses Wissen fehlt oft, wenn ein System zwar sauber gebaut, aber noch nicht betriebssicher uebergeben wurde.

## 1. Wann Planner, wann manuell?

Nutze den LiteRT-Planer, wenn:

- du aus einer fachlichen Beschreibung schnell einen ersten Graphen ableiten willst
- du eine komplexe Kette mit mehreren Handlern skizzieren musst
- du anschliessend im visuellen Editor nacharbeiten willst

Baue den Flow lieber manuell, wenn:

- die exakte Kantenlogik bereits feststeht
- du einen Produktionsfehler analysierst
- du ein sehr kleines, deterministisches Setup mit 1 bis 3 Nodes hast

## 2. Neuer Handler oder bestehenden Handler erweitern?

Erweitere einen bestehenden Handler, wenn:

- dieselbe Grundoperation bleibt
- Ein- und Ausgabeform nur optional waechst
- Fehlerbild und Retry-Verhalten gleich bleiben

Baue einen neuen Handler, wenn:

- eine neue Nebenwirkung entsteht
- eine andere externe Abhaengigkeit angebunden wird
- der Inputvertrag fachlich anders ist
- der Nutzer den Baustein im Editor als eigenstaendige Aktion verstehen soll

## 3. Flow, einzelne Task oder Agent?

- Verwende einen Flow, wenn Reihenfolge, Verzweigung oder Fehlerbehandlung sichtbar modelliert werden muessen.
- Verwende nur eine einzelne Task, wenn genau ein isolierter Arbeitsschritt existiert.
- Verwende einen Agenten, wenn Faehigkeiten, Kommunikationsadapter oder eine feste Verantwortlichkeit wichtig sind.

Ein Agent ersetzt keinen Flow. Der Flow modelliert den Prozess. Der Agent modelliert, wer oder was eine Task ausfuehren darf.

## 4. Wann ist eine Resource wirklich notwendig?

Nutze eine Resource, wenn der Schritt an ein echtes externes Ziel oder eine limitierte Kapazitaet gebunden ist:

- API-Endpunkt
- Modellinstanz
- Datenbank
- Dateiablage
- GPU

Nutze keine Resource, wenn der Schritt rein lokal und transformativ ist:

- `template_render`
- `merge_payloads`
- `json_serialize`

## 5. Konkrete Resource-ID oder nur Resource-Type?

- `required_resource_ids`: wenn exakt ein bestimmtes System getroffen werden muss
- `required_resource_types`: wenn jeder passende Vertreter einer Kategorie ausreicht oder Fallback sinnvoll ist

Faustregel: feste Kern-API per ID, austauschbare Replikate oder GPUs per Typ.

## 6. Welche Rollback-Strategie ist die richtige?

- `FAIL_FAST`: wenn Folgeschritte ohne Erfolg des Nodes keinen Sinn ergeben
- `RETRY`: bei transienten Netz- oder Dienstfehlern
- `FALLBACK_RESOURCE`: wenn mehrere Ressourcen gleicher Art vorhanden sind
- `COMPENSATE`: wenn ein Fehler nach einer Nebenwirkung aktiv bereinigt werden muss

## 7. Wann musst du `POST /flows/validate` aktiv nutzen?

Immer vor produktivem Speichern oder Ausfuehren, wenn:

- ein Flow durch den Planner erzeugt wurde
- neue Templates, Conditions oder Validator-Ausdruecke eingebaut wurden
- neue Ressourcen, Agenten oder Memory-Systeme beteiligt sind
- du Security-Grenzen geaendert hast

## 8. Wie klassifizierst du Memory-Systeme?

- `sensitive = true`: fuer vertrauliche Inhalte, die nicht in Planner oder externe Sinks gelangen sollen
- `planner_visible = false`: wenn ein Memory manuell nutzbar, aber nicht planner-sichtbar sein soll
- `allow_untrusted_ingest = true`: nur wenn bewusst Daten aus HTTP, Messaging oder Dateiquellen in planner-sichtbares Wissen einfliessen duerfen

Wenn du unsicher bist, starte konservativ: `sensitive = true` oder `planner_visible = false`.

## 9. Wann soll eine Condition auf eine Edge?

Eine Edge-Condition ist richtig, wenn du einen fachlichen Branch modellierst:

- Erfolgspfad vs Fehlerpfad
- weitere Verarbeitung nur bei gueltigem Ergebnis
- optionale Folgeaktionen

Eine Edge-Condition ist falsch, wenn du damit Daten umbauen oder fehlende Vorverarbeitung verstecken willst. Dann fehlt meist ein eigener Node.
```

## File: `failure-playbook.md`  
- Path: `failure-playbook.md`  
- Size: 6634 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# Failure Playbook

Diese Seite beschreibt die realen Stoerungsbilder des Systems. Ziel ist nicht nur Fehler zu benennen, sondern eine belastbare Reihenfolge fuer Diagnose und Behebung zu geben.

## Triage-Reihenfolge

1. Zuerst unterscheiden: Planner-Problem, Policy-Rejektion, Live-Transportproblem oder echte Runtime-Stoerung.
2. Immer den echten Snapshot ueber `GET /flows/{flow_id}` lesen.
3. Bei Save-/Run-Fehlern zuerst `POST /flows/validate` auswerten.
4. Erst danach UI, WebSocket oder Planner-Oberflaeche beurteilen.

## 1. Planner liefert ungueltiges JSON

### Woran du es erkennst

- `POST /planner/generate-flow` antwortet mit Fehler
- im Frontend erscheint keine neue Graphstruktur
- typische Backend-Meldungen:
  - `Planner returned invalid JSON`
  - `Planner response does not contain a JSON object`
  - `Planner response contains an incomplete JSON object`

### Sofortmassnahmen

1. `GET /planner/status` pruefen
2. Prompt kuerzen und restriktiver machen
3. `max_nodes` senken
4. sicherstellen, dass benoetigte Handler, Agenten, Ressourcen und Memory-IDs wirklich registriert sind
5. bei wiederholtem Fehler den Flow manuell im Editor bauen

## 2. Semantic Firewall lehnt den Flow ab

### Woran du es erkennst

- `POST /flows/validate`, `POST /flows` oder `POST /planner/generate-flow` liefert einen Fehler
- typische Fehlermeldungen:
  - `Semantic firewall rejected flow`
  - `Outbound host ... is outside the semantic firewall allowlist`
  - `Flow contains a cycle`
  - `Sensitive memory data may not flow into http_request nodes`

### Typische Ursachen

- zyklischer Graph
- `http_request` auf einen nicht erlaubten Host
- `send_message` ohne `target_agent_id` oder mit Endpoint-Override
- Template oder Condition mit nicht erlaubten Symbolen
- planner-sichtbare Memory-Store-Node hinter untrusted Ingest

### Sofortmassnahmen

1. denselben Payload gegen `POST /flows/validate` schicken
2. `violations` und `warnings` getrennt lesen
3. pruefen, ob das Problem fachlich oder rein policy-seitig ist
4. bei legitimen Produktionsfaellen erst Settings oder Memory-/Resource-Metadaten anpassen, nicht die Regel blind entfernen

## 3. WebSocket bricht waehrend der Execution ab

### Woran du es erkennst

- die Topbar zeigt `Offline`
- Live-Status friert ein oder aktualisiert sich nur stoerend langsam
- der Flow laeuft im Backend oft trotzdem weiter

### Was das System bereits fuer dich macht

`frontend/src/hooks/useFlowLiveUpdates.ts` faellt automatisch auf Polling gegen `GET /flows/{flow_id}` zurueck. Die UI bleibt dadurch nutzbar, auch wenn der Socket weg ist.

### Sofortmassnahmen

1. `GET /flows/{flow_id}` direkt pruefen
2. `frontend/.env` gegen die echte Backend-Adresse pruefen
3. unterscheiden: ist nur `/ws/flows/{flow_id}` defekt oder auch REST?
4. wenn REST geht, die Ausfuehrung nicht abbrechen, sondern Snapshot weiter per Polling beobachten

## 4. Resource haengt oder laeuft in Timeout / Sattlauf

### Woran du es erkennst

- eine oder mehrere Nodes bleiben lange auf `RUNNING`
- der Flow macht keine sichtbaren Fortschritte, ohne sofort auf `FAILED` zu springen
- einzelne Ressourcen stehen auf `BUSY` oder `DOWN`

### Wichtige technische Besonderheit

`ResourceManager.acquire_many()` hat keinen globalen Flow-Timeout. Handler-Timeouts wie `http_request.timeout_s` greifen erst nach erfolgreicher Ressourcenreservierung.

### Sofortmassnahmen

1. `GET /flows/{flow_id}` lesen und die `RUNNING`-Nodes identifizieren
2. `GET /resources` und gegebenenfalls `resource_health_check` verwenden
3. `max_concurrency`, Kapazitaet und `required_resource_ids` gegen die echte Infrastruktur pruefen
4. bei HTTP-Aufrufen explizit `timeout_s` setzen
5. wenn moeglich auf `required_resource_types` plus `FALLBACK_RESOURCE` umstellen

## 5. Flow bleibt auf `RUNNING` stehen

### Woran du es erkennst

- `GET /flows/{flow_id}` zeigt dauerhaft `state = RUNNING`
- dieselben Nodes bleiben ueber mehrere Snapshots hinweg `RUNNING`
- `completed_nodes` waechst nicht mehr

### Typische Ursachen

- Handler wartet auf externen Dienst
- Ressource wartet auf Freigabe
- externer Endpunkt antwortet nie innerhalb eines sinnvollen Timeouts
- ein lang laufender Seiteneffekt wurde nicht in kleinere Nodes zerlegt

### Sofortmassnahmen

1. mehrere Snapshots hintereinander vergleichen
2. den oder die `RUNNING`-Nodes identifizieren
3. Handlervertrag des betroffenen Nodes pruefen
4. bei `http_request` ein sinnvolles `timeout_s` setzen
5. pruefen, ob Ressource oder Kommunikationsziel erreichbar sind

## 6. Graph-Deadlock oder logisch blockierter Flow

Wichtig: Wenn keine Node mehr startbar ist und trotzdem noch `pending` existiert, setzt `FlowExecutor.run_flow()` den Flow auf `FAILED` und schreibt `deadlock_nodes` in die Metadaten.

### Sofortmassnahmen

1. `deadlock_nodes`, `blocked_nodes` und `failed_nodes` vergleichen
2. alle eingehenden Kantenbedingungen des betroffenen Knotens lesen
3. nur die von der Engine gelieferten Bedingungssymbole verwenden:
   - `results`
   - `source_result`
   - `target_node`
   - `completed`
   - `blocked`
   - `failed`
4. pruefen, ob mindestens ein Node ohne eingehende Kante existiert

## 7. Handler wirft Exception

### Woran du es erkennst

- eine Node springt auf `FAILED`
- oft folgt `node.rolled_back`
- der Flow endet mit `FAILED`, ausser `continue_on_error` ist aktiv
- `failed_nodes` enthaelt die konkrete Fehlermeldung

### Typische reale Ursachen in diesem Projekt

- unbekannter Handlername in `TaskHandlerRegistry`
- `http_request` ohne `url` und ohne API-Ressource
- `send_message` ohne Kommunikationsadapter
- `read_file` oder `write_file` greifen ausserhalb des erlaubten Arbeitsverzeichnisses zu
- `merge_payloads` bekommt Werte, die keine Dictionaries sind
- `validator_rules` schlagen fehl
- eine Ressource kann nicht reserviert werden

### Sofortmassnahmen

1. `failed_nodes` im Snapshot lesen
2. Input des Nodes mit dem echten Handlervertrag vergleichen
3. Ressourcen, Agenten und Memory-Systeme pruefen
4. `retry_policy` und `rollback_strategy` auf Infrastrukturrealitaet abstimmen

## Welche Daten du vor tieferer Analyse sammeln solltest

- `flow_id`
- kompletter Snapshot aus `GET /flows/{flow_id}`
- Ergebnis von `POST /flows/validate`, falls Save oder Run scheitert
- alle aktuell `RUNNING`, `FAILED` und `blocked` Nodes
- Handlername und Input der auffaelligen Node
- verwendete Ressourcen, Agenten und Memory-IDs
- bei Planner-Problemen: Prompt, `max_nodes` und `security_report`
```

## File: `frontend-editor.md`  
- Path: `frontend-editor.md`  
- Size: 966 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# Frontend-Editor

Die UI besteht aus `App.tsx`, dem Zustand-Store `useFlowStore.ts`, der Zeichenflaeche `FlowCanvas.tsx`, der linken `Sidebar.tsx`, dem `InspectorPanel.tsx`, dem Planner-Dialog und der `TopBar.tsx`.

## Was der Editor wirklich tut

- laedt Handler, Agenten und Ressourcen aus dem echten Backend
- baut daraus React-Flow-Nodes und -Edges
- serialisiert den Editorzustand ueber `toFlowRequest()`
- speichert und startet echte Flows
- uebernimmt Live-Snapshots ueber WebSocket oder Polling

## Kritische Integrationsstellen

- `frontend/src/lib/flowSerialization.ts`: muss exakt zum FastAPI-Schema passen
- `frontend/src/lib/apiClient.ts`: enthaelt die echten REST- und WebSocket-Aufrufe inklusive `POST /flows/validate`
- `frontend/src/store/useFlowStore.ts`: haelt den kanonischen UI-Zustand fuer Nodes, Edges, Auswahl und Laufzeitstatus
- `frontend/src/hooks/useFlowLiveUpdates.ts`: faellt bei Socket-Problemen auf Polling zurueck
```

## File: `getting-started.md`  
- Path: `getting-started.md`  
- Size: 1647 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# Schnellstart

## 1. Backend starten

```powershell
./run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

Wichtige URLs:

- `GET /docs`
- `GET /health`
- `GET /planner/status`
- `POST /flows/validate`

## 2. Frontend starten

`frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8552
```

Dann:

```powershell
cd frontend
npm run dev
```

## 3. Minimaler Arbeitsablauf

1. Handler, Agenten und Ressourcen im Frontend laden.
2. Einen Graphen im Canvas zeichnen oder ueber den Planner erzeugen.
3. Vor dem Speichern `POST /flows/validate` verwenden oder die UI-Validierung ausloesen.
4. Den Flow ueber `POST /flows` speichern.
5. Den Flow ueber `POST /flows/{flow_id}/run` ausfuehren.
6. Laufzeit und Status ueber `GET /flows/{flow_id}` oder `/ws/flows/{flow_id}` beobachten.

## 4. Wichtige Umgebungsvariablen

- `NS_API_HOST`, `NS_API_PORT`: FastAPI-Bindung
- `NS_LIT_BINARY_PATH`, `NS_LIT_MODEL_PATH`, `NS_LIT_TIMEOUT_S`: lokaler Planner
- `NS_SECURITY_ENABLED`: Semantic Firewall global ein- oder ausschalten
- `NS_SECURITY_HTTP_ALLOWED_HOSTS`: erlaubte HTTP-Zielhosts
- `NS_SECURITY_SEND_PROTOCOLS`: erlaubte Kommunikationsprotokolle fuer `send_message`
- `NS_CORS_ORIGINS`: erlaubte Frontend-Urspruenge

## 5. Mentales Modell

- Das Frontend bearbeitet einen gerichteten Graphen aus Nodes und Edges.
- `toFlowRequest()` wandelt den Editorgraphen in das Backend-Schema.
- Das Backend validiert Struktur, Expressions und Sicherheitsregeln.
- Erst danach wird gespeichert oder ausgefuehrt.
- Die Runtime fuehrt nur DAGs aus und meldet Snapshots laufend an UI und Persistenz zurueck.
```

## File: `planner-and-lit.md`  
- Path: `planner-and-lit.md`  
- Size: 1075 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# LLM-Planer und LiteRT

Der Planner erzeugt keine Mock-Graphen. Er nutzt die lokale `lit`-Binary und das Gemma-Modell im `LIT/`-Ordner, extrahiert JSON und normalisiert das Resultat auf das echte `FlowRequest`-Schema.

## Ablauf

1. `LiteRTPlanner._build_prompt()` baut den Prompt aus Benutzerziel und echtem Katalog.
2. `_invoke_model()` ruft `lit.windows_x86_64.exe` mit `gemma-4-E2B-it.litertlm` auf.
3. `_parse_model_output()` extrahiert genau ein JSON-Objekt.
4. `_normalize_flow_request()` korrigiert IDs, Defaults, Abhaengigkeiten und Handler-Inputs.
5. `OrchestratorService.generate_flow_with_llm()` laesst den Graphen anschliessend noch durch die Semantic Firewall laufen.

## Wichtige Sicherheitsgrenzen

- Ressourcen und Memories mit `sensitive = true` oder `planner_visible = false` werden aus dem Planner-Katalog herausgefiltert.
- Die Antwort enthaelt `security_report`, damit UI und Betreiber sehen, ob der generierte Graph policy-konform war.
- Planner-Warnungen bedeuten: der Graph wurde normalisiert, aber nicht stillschweigend erweitert.
```

## File: `README.md`  
- Path: `README.md`  
- Size: 1261 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# NOVA-SYNESIS Dokumentation

Neural Orchestration Visual Autonomy  
Stateful Yielding Node-based Execution Semantic Integrated Surface

Diese Dokumentation erklaert das System so, dass auch ein Entwickler ohne Vorwissen NOVA-SYNESIS starten, verstehen, absichern und gezielt aendern kann.

## Einstieg

1. [Schnellstart](getting-started.md)
2. [Systemueberblick](system-overview.md)
3. [Backend-Laufzeit](backend-runtime.md)
4. [Frontend-Editor](frontend-editor.md)
5. [LLM-Planer und LiteRT](planner-and-lit.md)
6. [Security und Policy](security-and-policy.md)
7. [Failure Playbook](failure-playbook.md)
8. [Decision Guide](decision-guide.md)
9. [Real World Scenarios](real-world-scenarios.md)
10. [Aenderungsleitfaden](change-workflows.md)
11. [Referenzindex](reference/index.md)

## Wie du diese Doku liest

- Starte mit `getting-started.md`, wenn du das System lokal hochfahren willst.
- Lies `system-overview.md` und `backend-runtime.md`, wenn du Architektur und Laufzeit verstehen willst.
- Nutze `security-and-policy.md` und `failure-playbook.md`, bevor du produktive Flows oder neue Handler einsetzt.
- Verwende `decision-guide.md` und `real-world-scenarios.md`, wenn du eigene Flows sicher entwerfen oder veraendern willst.
```

## File: `real-world-scenarios.md`  
- Path: `real-world-scenarios.md`  
- Size: 3437 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# Real World Scenarios

Diese Seite enthaelt bewusst nur drei End-to-End-Beispiele. Ziel ist nicht Vollstaendigkeit, sondern sichere Anwendbarkeit mit dem echten Backend und der aktiven Security-Policy.

## Szenario 1: Einfacher Betriebsflow "Platform Health Snapshot"

Referenz: `Use_Cases/platform_health_snapshot/`

### Ziel

Die lokale Plattform pruefen, einen Snapshot speichern und daraus eine Textzusammenfassung schreiben.

### Warum dieser Flow produktionsnah ist

- nutzt nur echte Built-in-Handler
- benoetigt keinen Mock-Service
- zeigt HTTP, Memory, Serialisierung und Dateiablage in einer kleinen, gut kontrollierbaren Kette

### Typischer Ablauf

1. `http_request` gegen einen lokalen oder allowlist-konformen Health-Endpunkt
2. `json_serialize` fuer den Snapshot
3. `write_file` fuer Rohdaten
4. `template_render` fuer die Zusammenfassung
5. `write_file` fuer den lesbaren Report
6. optional `memory_store` fuer den letzten Snapshot-Key

## Szenario 2: Komplexer Flow mit Branching "Semantic Ticket Triage"

Referenz: `Use_Cases/semantic_ticket_triage/`

### Ziel

Tickets semantisch bewerten, Wissen aus Memory laden und je nach Ergebnis an unterschiedliche interne Queue-Agenten dispatchen.

### Warum dieser Flow produktionsnah ist

- kombiniert Vector Memory, Planner-verwertbares Wissen und Messaging
- nutzt Branching ueber Edge-Conditions
- bleibt policy-konform, weil `send_message` auf interne Message Queues begrenzt bleibt

### Typischer Ablauf

1. Ticketdaten laden oder als Input entgegennehmen
2. `memory_search` in einem Vector-Memory
3. `template_render` fuer die Triage-Zusammenfassung
4. Branching auf `dispatch-support` oder `dispatch-sales`
5. `send_message` an registrierte Queue-Agenten

## Szenario 3: Fehlerfall mit Retry und Fallback "API-Replica uebernimmt"

### Ziel

Ein fragiler Infrastrukturzugriff soll auch dann stabil laufen, wenn die bevorzugte Ressource kurzzeitig ausfaellt.

### Beispielstruktur

```json
{
  "nodes": [
    {
      "node_id": "fetch-primary-or-fallback",
      "handler_name": "http_request",
      "input": { "method": "GET", "timeout_s": 8 },
      "required_resource_types": ["API"],
      "retry_policy": {
        "max_retries": 3,
        "backoff_ms": 500,
        "exponential": true,
        "max_backoff_ms": 5000,
        "jitter_ratio": 0.1
      },
      "rollback_strategy": "FALLBACK_RESOURCE",
      "validator_rules": {
        "required_keys": ["status_code", "body"],
        "expression": "result['status_code'] < 500"
      }
    },
    {
      "node_id": "store-result",
      "handler_name": "memory_store",
      "input": {
        "memory_id": "working-memory",
        "key": "resilient-fetch-result",
        "value": "{{ results['fetch-primary-or-fallback']['body'] }}"
      },
      "dependencies": ["fetch-primary-or-fallback"],
      "conditions": { "fetch-primary-or-fallback": "source_result['status_code'] < 400" }
    }
  ],
  "edges": [
    {
      "from_node": "fetch-primary-or-fallback",
      "to_node": "store-result",
      "condition": "source_result['status_code'] < 400"
    }
  ]
}
```

### Sichere Betriebsreihenfolge

1. zuerst `POST /flows/validate`
2. danach speichern
3. Laufzeit ueber `GET /flows/{flow_id}` beobachten
4. bei Auffaelligkeiten pruefen, ob wirklich Retry oder bereits Resource-Fallback greift
```

## File: `reference/.env.example.md`  
- Path: `reference/.env.example.md`  
- Size: 1047 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `.env.example`

- Quellpfad: [.env.example](../../.env.example)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Beispielkonfiguration fuer Backend, Planner, CORS und die semantische Sicherheitsrichtlinie.

## Wann du diese Datei bearbeitest

Wenn neue Umgebungsvariablen eingefuehrt, Security-Grenzen angepasst oder Standardwerte kommuniziert werden muessen.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/config.py](src/nova_synesis/config.py.md)
- [README.md](README.md.md)
```

## File: `reference/.gitignore.md`  
- Path: `reference/.gitignore.md`  
- Size: 835 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `.gitignore`

- Quellpfad: [.gitignore](../../.gitignore)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Projektdatei mit eigener Rolle im Repository.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/Anweisung.md.md`  
- Path: `reference/Anweisung.md.md`  
- Size: 932 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Anweisung.md`

- Quellpfad: [Anweisung.md](../../Anweisung.md)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Fachliche Ursprungsspezifikation des Systems.

## Wann du diese Datei bearbeitest

Wenn Anforderungen nachgezogen oder gegen die Implementierung gespiegelt werden.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [uml_V3.mmd](uml_V3.mmd.md)
- [README.md](README.md.md)
```

## File: `reference/Dockerfile.md`  
- Path: `reference/Dockerfile.md`  
- Size: 945 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Dockerfile`

- Quellpfad: [Dockerfile](../../Dockerfile)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Container-Build fuer das Python-Backend.

## Wann du diese Datei bearbeitest

Wenn Build, Startkommando oder Image-Basis angepasst werden muessen.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [pyproject.toml](pyproject.toml.md)
- [src/nova_synesis/cli.py](src/nova_synesis/cli.py.md)
```

## File: `reference/frontend/.env.example.md`  
- Path: `reference/frontend/.env.example.md`  
- Size: 881 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/.env.example`

- Quellpfad: [frontend/.env.example](../../../frontend/.env.example)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Projektdatei mit eigener Rolle im Repository.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/index.html.md`  
- Path: `reference/frontend/index.html.md`  
- Size: 883 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/index.html`

- Quellpfad: [frontend/index.html](../../../frontend/index.html)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

HTML-Datei fuer Visualisierung oder Browser-Einstieg.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/package-lock.json.md`  
- Path: `reference/frontend/package-lock.json.md`  
- Size: 878 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/package-lock.json`

- Quellpfad: [frontend/package-lock.json](../../../frontend/package-lock.json)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/package.json.md`  
- Path: `reference/frontend/package.json.md`  
- Size: 863 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/package.json`

- Quellpfad: [frontend/package.json](../../../frontend/package.json)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/app.css.md`  
- Path: `reference/frontend/src/app.css.md`  
- Size: 843 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/app.css`

- Quellpfad: [frontend/src/app.css](../../../../frontend/src/app.css)
- Kategorie: `Frontend`

## Aufgabe der Datei

Stylesheet der Weboberflaeche.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/App.tsx.md`  
- Path: `reference/frontend/src/App.tsx.md`  
- Size: 2199 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/App.tsx`

- Quellpfad: [frontend/src/App.tsx](../../../../frontend/src/App.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Root-Komponente der UI mit Layout, Planner, Save/Run und Live-Sync.

## Wann du diese Datei bearbeitest

Wenn globale Frontend-Aktionen oder das Seitenlayout geaendert werden.

## Exporte und oeffentliche Definitionen

- `App`: React-Komponente `App` fuer einen klar abgegrenzten UI-Bereich.

## Wichtige interne Routinen

- `saveCurrentFlow`: Speichert den aktuellen Canvas als echten Flow im Backend.
- `handleRun`: Speichert bei Bedarf und startet anschliessend die Flow-Ausfuehrung.
- `handleExport`: Exportiert den Editorzustand als JSON-Datei.
- `handleImport`: Importiert einen Editor-Export oder einen nackten FlowRequest.
- `handleGenerateWithPlanner`: Fordert ueber das Backend einen neuen Graphen vom LLM-Planer an.

## Abhaengigkeiten

- `import { ReactFlowProvider } from "@xyflow/react";`
- `import { useCallback, useEffect, useState } from "react";`
- `import { FlowCanvas } from "./components/flow/FlowCanvas";`
- `import { InspectorPanel } from "./components/layout/InspectorPanel";`
- `import { PlannerComposer } from "./components/layout/PlannerComposer";`
- `import { Sidebar } from "./components/layout/Sidebar";`
- `import { TopBar } from "./components/layout/TopBar";`
- `import { useCatalogBootstrap } from "./hooks/useCatalogBootstrap";`
- `import { useFlowLiveUpdates } from "./hooks/useFlowLiveUpdates";`
- `import {`
- `import { fromFlowRequest, toFlowRequest } from "./lib/flowSerialization";`
- `import { prettyJson, safeJsonParse } from "./lib/json";`
- `import { useFlowStore } from "./store/useFlowStore";`
- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/store/useFlowStore.ts](store/useFlowStore.ts.md)
- [frontend/src/components/layout/TopBar.tsx](components/layout/TopBar.tsx.md)
```

## File: `reference/frontend/src/components/common/JsonEditor.tsx.md`  
- Path: `reference/frontend/src/components/common/JsonEditor.tsx.md`  
- Size: 921 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/components/common/JsonEditor.tsx`

- Quellpfad: [frontend/src/components/common/JsonEditor.tsx](../../../../../../frontend/src/components/common/JsonEditor.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `JsonEditor`: Funktion oder Definition `JsonEditor` dieses Moduls.

## Abhaengigkeiten

- `import { useEffect, useMemo, useState } from "react";`
- `import { prettyJson, safeJsonParse } from "../../lib/json";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/components/common/StatusBadge.tsx.md`  
- Path: `reference/frontend/src/components/common/StatusBadge.tsx.md`  
- Size: 875 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/components/common/StatusBadge.tsx`

- Quellpfad: [frontend/src/components/common/StatusBadge.tsx](../../../../../../frontend/src/components/common/StatusBadge.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `StatusBadge`: Funktion oder Definition `StatusBadge` dieses Moduls.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/components/flow/FlowCanvas.tsx.md`  
- Path: `reference/frontend/src/components/flow/FlowCanvas.tsx.md`  
- Size: 1013 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/components/flow/FlowCanvas.tsx`

- Quellpfad: [frontend/src/components/flow/FlowCanvas.tsx](../../../../../../frontend/src/components/flow/FlowCanvas.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `FlowCanvas`: React-Flow-Leinwand des Editors.

## Abhaengigkeiten

- `import {`
- `import { useCallback, useRef } from "react";`
- `import { useFlowStore } from "../../store/useFlowStore";`
- `import type { TaskFlowEdge, TaskFlowNode } from "../../types/api";`
- `import { TaskNode } from "./TaskNode";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/components/flow/TaskNode.tsx.md`  
- Path: `reference/frontend/src/components/flow/TaskNode.tsx.md`  
- Size: 964 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/components/flow/TaskNode.tsx`

- Quellpfad: [frontend/src/components/flow/TaskNode.tsx](../../../../../../frontend/src/components/flow/TaskNode.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `TaskNode`: Custom Node fuer einzelne Tasks im Canvas.

## Abhaengigkeiten

- `import { Handle, Position, type NodeProps } from "@xyflow/react";`
- `import { useFlowStore } from "../../store/useFlowStore";`
- `import type { TaskFlowNode } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/components/layout/InspectorPanel.tsx.md`  
- Path: `reference/frontend/src/components/layout/InspectorPanel.tsx.md`  
- Size: 1714 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
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
- `NodeField`: Hilfskomponente fuer einfache Texteingaben im Inspector.
- `NumericField`: Hilfskomponente fuer numerische Eingaben im Inspector.

## Abhaengigkeiten

- `import { JsonEditor } from "../common/JsonEditor";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import { useFlowStore } from "../../store/useFlowStore";`
- `import type { ResourceType, RollbackStrategy, TaskFlowNode } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/store/useFlowStore.ts](../../store/useFlowStore.ts.md)
- [frontend/src/components/common/JsonEditor.tsx](../common/JsonEditor.tsx.md)
```

## File: `reference/frontend/src/components/layout/PlannerComposer.tsx.md`  
- Path: `reference/frontend/src/components/layout/PlannerComposer.tsx.md`  
- Size: 1200 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/components/layout/PlannerComposer.tsx`

- Quellpfad: [frontend/src/components/layout/PlannerComposer.tsx](../../../../../../frontend/src/components/layout/PlannerComposer.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Planner-Dialog fuer die lokale LLM-Graph-Erzeugung.

## Wann du diese Datei bearbeitest

Wenn Prompting-UX oder Planner-Rueckmeldungen im Frontend erweitert werden.

## Exporte und oeffentliche Definitionen

- `PlannerComposer`: Dialog fuer die autonome Graph-Erzeugung.

## Abhaengigkeiten

- `import { useEffect, useState } from "react";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import type { PlannerGenerateResponse, PlannerStatus } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/App.tsx](../../App.tsx.md)
- [src/nova_synesis/planning/lit_planner.py](../../../../src/nova_synesis/planning/lit_planner.py.md)
```

## File: `reference/frontend/src/components/layout/Sidebar.tsx.md`  
- Path: `reference/frontend/src/components/layout/Sidebar.tsx.md`  
- Size: 1142 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/components/layout/Sidebar.tsx`

- Quellpfad: [frontend/src/components/layout/Sidebar.tsx](../../../../../../frontend/src/components/layout/Sidebar.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Linke Katalogleiste mit Handlern, Agenten und Ressourcen.

## Wann du diese Datei bearbeitest

Wenn Drag-and-Drop oder Katalogdarstellung geaendert wird.

## Exporte und oeffentliche Definitionen

- `Sidebar`: Funktion oder Definition `Sidebar` dieses Moduls.

## Abhaengigkeiten

- `import { useMemo, useState } from "react";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import { useFlowStore } from "../../store/useFlowStore";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/components/flow/FlowCanvas.tsx](../flow/FlowCanvas.tsx.md)
- [frontend/src/store/useFlowStore.ts](../../store/useFlowStore.ts.md)
```

## File: `reference/frontend/src/components/layout/TopBar.tsx.md`  
- Path: `reference/frontend/src/components/layout/TopBar.tsx.md`  
- Size: 1225 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/components/layout/TopBar.tsx`

- Quellpfad: [frontend/src/components/layout/TopBar.tsx](../../../../../../frontend/src/components/layout/TopBar.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Globale Aktionsleiste fuer Save, Run, Planner, Import und Export.

## Wann du diese Datei bearbeitest

Wenn globale Bedienaktionen oder Statusanzeigen geaendert werden.

## Exporte und oeffentliche Definitionen

- `TopBar`: Funktion oder Definition `TopBar` dieses Moduls.

## Wichtige interne Routinen

- `statusTone`: Ordnet globale Flow-Zustaende den Topbar-Badge-Farben zu.

## Abhaengigkeiten

- `import { useRef } from "react";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import type { PlannerStatus } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/App.tsx](../../App.tsx.md)
- [frontend/src/components/common/StatusBadge.tsx](../common/StatusBadge.tsx.md)
```

## File: `reference/frontend/src/hooks/useCatalogBootstrap.ts.md`  
- Path: `reference/frontend/src/hooks/useCatalogBootstrap.ts.md`  
- Size: 983 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/hooks/useCatalogBootstrap.ts`

- Quellpfad: [frontend/src/hooks/useCatalogBootstrap.ts](../../../../../frontend/src/hooks/useCatalogBootstrap.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `useCatalogBootstrap`: Funktion oder Definition `useCatalogBootstrap` dieses Moduls.

## Abhaengigkeiten

- `import { useEffect } from "react";`
- `import { fetchAgents, fetchHandlers, fetchResources } from "../lib/apiClient";`
- `import { useFlowStore } from "../store/useFlowStore";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/hooks/useFlowLiveUpdates.ts.md`  
- Path: `reference/frontend/src/hooks/useFlowLiveUpdates.ts.md`  
- Size: 1025 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/hooks/useFlowLiveUpdates.ts`

- Quellpfad: [frontend/src/hooks/useFlowLiveUpdates.ts](../../../../../frontend/src/hooks/useFlowLiveUpdates.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `useFlowLiveUpdates`: Funktion oder Definition `useFlowLiveUpdates` dieses Moduls.

## Abhaengigkeiten

- `import { useEffect } from "react";`
- `import { fetchFlow, getWebSocketBaseUrl } from "../lib/apiClient";`
- `import { useFlowStore } from "../store/useFlowStore";`
- `import type { FlowEventMessage } from "../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/lib/apiClient.ts.md`  
- Path: `reference/frontend/src/lib/apiClient.ts.md`  
- Size: 1569 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/lib/apiClient.ts`

- Quellpfad: [frontend/src/lib/apiClient.ts](../../../../../frontend/src/lib/apiClient.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Echter API-Client fuer REST, Flow-Validierung, Planner und WebSocket-Basis-URLs.

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
```

## File: `reference/frontend/src/lib/autoLayout.ts.md`  
- Path: `reference/frontend/src/lib/autoLayout.ts.md`  
- Size: 828 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/lib/autoLayout.ts`

- Quellpfad: [frontend/src/lib/autoLayout.ts](../../../../../frontend/src/lib/autoLayout.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `autoLayoutNodes`: Funktion oder Definition `autoLayoutNodes` dieses Moduls.

## Abhaengigkeiten

- `import type { TaskFlowEdge, TaskFlowNode } from "../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/lib/flowSerialization.ts.md`  
- Path: `reference/frontend/src/lib/flowSerialization.ts.md`  
- Size: 2038 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
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
```

## File: `reference/frontend/src/lib/json.ts.md`  
- Path: `reference/frontend/src/lib/json.ts.md`  
- Size: 880 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/lib/json.ts`

- Quellpfad: [frontend/src/lib/json.ts](../../../../../frontend/src/lib/json.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `safeJsonParse`: Funktion oder Definition `safeJsonParse` dieses Moduls.
- `prettyJson`: Funktion oder Definition `prettyJson` dieses Moduls.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/main.tsx.md`  
- Path: `reference/frontend/src/main.tsx.md`  
- Size: 870 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/main.tsx`

- Quellpfad: [frontend/src/main.tsx](../../../../frontend/src/main.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Inhalt

Diese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.

## Abhaengigkeiten

- `import React from "react";`
- `import ReactDOM from "react-dom/client";`
- `import "@xyflow/react/dist/style.css";`
- `import "./app.css";`
- `import App from "./App";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/src/store/useFlowStore.ts.md`  
- Path: `reference/frontend/src/store/useFlowStore.ts.md`  
- Size: 1379 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/store/useFlowStore.ts`

- Quellpfad: [frontend/src/store/useFlowStore.ts](../../../../../frontend/src/store/useFlowStore.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Zustand-Store fuer Graph, Auswahl, Undo/Redo und Laufzeitstatus.

## Wann du diese Datei bearbeitest

Wenn Editorverhalten oder Snapshot-Uebernahme angepasst werden.

## Exporte und oeffentliche Definitionen

- `useFlowStore`: Globaler Zustandsspeicher der UI auf Basis von Zustand.

## Wichtige interne Routinen

- `snapshotGraph`: Erzeugt einen unveraenderlichen Graph-Snapshot fuer Undo/Redo.
- `withHistory`: Haengt den aktuellen Zustand an die Undo-Historie an.
- `mergeSnapshotIntoNode`: Uebernimmt Runtime-Daten aus einem Backend-Snapshot in einen Editor-Node.

## Abhaengigkeiten

- `import {`
- `import { create } from "zustand";`
- `import { autoLayoutNodes } from "../lib/autoLayout";`
- `import {`
- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/App.tsx](../App.tsx.md)
- [frontend/src/hooks/useFlowLiveUpdates.ts](../hooks/useFlowLiveUpdates.ts.md)
```

## File: `reference/frontend/src/types/api.ts.md`  
- Path: `reference/frontend/src/types/api.ts.md`  
- Size: 2542 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/types/api.ts`

- Quellpfad: [frontend/src/types/api.ts](../../../../../frontend/src/types/api.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Gemeinsame TypeScript-Schemata fuer API, Snapshots und Editorgraph.

## Wann du diese Datei bearbeitest

Wenn Backend-Vertraege oder UI-Datentypen erweitert werden.

## Exporte und oeffentliche Definitionen

- `ResourceType`: TypeScript-Typ `ResourceType` fuer einen Datenvertrag.
- `RollbackStrategy`: TypeScript-Typ `RollbackStrategy` fuer einen Datenvertrag.
- `TaskStatus`: TypeScript-Typ `TaskStatus` fuer einen Datenvertrag.
- `FlowState`: TypeScript-Typ `FlowState` fuer einen Datenvertrag.
- `TaskFlowNode`: TypeScript-Typ `TaskFlowNode` fuer einen Datenvertrag.
- `TaskFlowEdge`: TypeScript-Typ `TaskFlowEdge` fuer einen Datenvertrag.
- `RetryPolicy`: TypeScript-Typ `RetryPolicy` fuer einen Datenvertrag.
- `AgentSummary`: TypeScript-Typ `AgentSummary` fuer einen Datenvertrag.
- `ResourceSummary`: TypeScript-Typ `ResourceSummary` fuer einen Datenvertrag.
- `TaskNodeData`: TypeScript-Typ `TaskNodeData` fuer einen Datenvertrag.
- `ConditionEdgeData`: TypeScript-Typ `ConditionEdgeData` fuer einen Datenvertrag.
- `TaskSpecModel`: TypeScript-Typ `TaskSpecModel` fuer einen Datenvertrag.
- `EdgeModel`: TypeScript-Typ `EdgeModel` fuer einen Datenvertrag.
- `FlowRequest`: TypeScript-Typ `FlowRequest` fuer einen Datenvertrag.
- `FlowNodeSnapshot`: TypeScript-Typ `FlowNodeSnapshot` fuer einen Datenvertrag.
- `FlowSnapshot`: TypeScript-Typ `FlowSnapshot` fuer einen Datenvertrag.
- `FlowEventMessage`: TypeScript-Typ `FlowEventMessage` fuer einen Datenvertrag.
- `EditorExport`: TypeScript-Typ `EditorExport` fuer einen Datenvertrag.
- `PlannerStatus`: TypeScript-Typ `PlannerStatus` fuer einen Datenvertrag.
- `PlannerGenerateRequest`: TypeScript-Typ `PlannerGenerateRequest` fuer einen Datenvertrag.
- `PlannerGenerateResponse`: TypeScript-Typ `PlannerGenerateResponse` fuer einen Datenvertrag.

## Abhaengigkeiten

- `import type { Edge, Node } from "@xyflow/react";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/api/app.py](../../../src/nova_synesis/api/app.py.md)
- [frontend/src/lib/flowSerialization.ts](../lib/flowSerialization.ts.md)
```

## File: `reference/frontend/src/vite-env.d.ts.md`  
- Path: `reference/frontend/src/vite-env.d.ts.md`  
- Size: 781 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/src/vite-env.d.ts`

- Quellpfad: [frontend/src/vite-env.d.ts](../../../../frontend/src/vite-env.d.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Inhalt

Diese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/tsconfig.app.json.md`  
- Path: `reference/frontend/tsconfig.app.json.md`  
- Size: 878 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/tsconfig.app.json`

- Quellpfad: [frontend/tsconfig.app.json](../../../frontend/tsconfig.app.json)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/tsconfig.json.md`  
- Path: `reference/frontend/tsconfig.json.md`  
- Size: 866 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/tsconfig.json`

- Quellpfad: [frontend/tsconfig.json](../../../frontend/tsconfig.json)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/tsconfig.node.json.md`  
- Path: `reference/frontend/tsconfig.node.json.md`  
- Size: 881 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/tsconfig.node.json`

- Quellpfad: [frontend/tsconfig.node.json](../../../frontend/tsconfig.node.json)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/vite.config.d.ts.md`  
- Path: `reference/frontend/vite.config.d.ts.md`  
- Size: 789 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/vite.config.d.ts`

- Quellpfad: [frontend/vite.config.d.ts](../../../frontend/vite.config.d.ts)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Inhalt

Diese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/vite.config.js.md`  
- Path: `reference/frontend/vite.config.js.md`  
- Size: 822 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/vite.config.js`

- Quellpfad: [frontend/vite.config.js](../../../frontend/vite.config.js)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Projektdatei mit eigener Rolle im Repository.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.

## Abhaengigkeiten

- `import { defineConfig } from "vite";`
- `import react from "@vitejs/plugin-react";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/frontend/vite.config.ts.md`  
- Path: `reference/frontend/vite.config.ts.md`  
- Size: 799 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `frontend/vite.config.ts`

- Quellpfad: [frontend/vite.config.ts](../../../frontend/vite.config.ts)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Inhalt

Diese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.

## Abhaengigkeiten

- `import { defineConfig } from "vite";`
- `import react from "@vitejs/plugin-react";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/index.md`  
- Path: `reference/index.md`  
- Size: 5899 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# Referenzindex

## Backend

- [src/nova_synesis/__init__.py](src/nova_synesis/__init__.py.md)
- [src/nova_synesis/api/__init__.py](src/nova_synesis/api/__init__.py.md)
- [src/nova_synesis/api/app.py](src/nova_synesis/api/app.py.md)
- [src/nova_synesis/cli.py](src/nova_synesis/cli.py.md)
- [src/nova_synesis/communication/__init__.py](src/nova_synesis/communication/__init__.py.md)
- [src/nova_synesis/communication/adapters.py](src/nova_synesis/communication/adapters.py.md)
- [src/nova_synesis/config.py](src/nova_synesis/config.py.md)
- [src/nova_synesis/domain/__init__.py](src/nova_synesis/domain/__init__.py.md)
- [src/nova_synesis/domain/models.py](src/nova_synesis/domain/models.py.md)
- [src/nova_synesis/memory/__init__.py](src/nova_synesis/memory/__init__.py.md)
- [src/nova_synesis/memory/systems.py](src/nova_synesis/memory/systems.py.md)
- [src/nova_synesis/persistence/__init__.py](src/nova_synesis/persistence/__init__.py.md)
- [src/nova_synesis/persistence/sqlite_repository.py](src/nova_synesis/persistence/sqlite_repository.py.md)
- [src/nova_synesis/planning/__init__.py](src/nova_synesis/planning/__init__.py.md)
- [src/nova_synesis/planning/lit_planner.py](src/nova_synesis/planning/lit_planner.py.md)
- [src/nova_synesis/planning/planner.py](src/nova_synesis/planning/planner.py.md)
- [src/nova_synesis/resources/__init__.py](src/nova_synesis/resources/__init__.py.md)
- [src/nova_synesis/resources/manager.py](src/nova_synesis/resources/manager.py.md)
- [src/nova_synesis/runtime/__init__.py](src/nova_synesis/runtime/__init__.py.md)
- [src/nova_synesis/runtime/engine.py](src/nova_synesis/runtime/engine.py.md)
- [src/nova_synesis/runtime/handlers.py](src/nova_synesis/runtime/handlers.py.md)
- [src/nova_synesis/security/__init__.py](src/nova_synesis/security/__init__.py.md)
- [src/nova_synesis/security/policy.py](src/nova_synesis/security/policy.py.md)
- [src/nova_synesis/services/__init__.py](src/nova_synesis/services/__init__.py.md)
- [src/nova_synesis/services/orchestrator.py](src/nova_synesis/services/orchestrator.py.md)

## Frontend

- [frontend/src/App.tsx](frontend/src/App.tsx.md)
- [frontend/src/app.css](frontend/src/app.css.md)
- [frontend/src/components/common/JsonEditor.tsx](frontend/src/components/common/JsonEditor.tsx.md)
- [frontend/src/components/common/StatusBadge.tsx](frontend/src/components/common/StatusBadge.tsx.md)
- [frontend/src/components/flow/FlowCanvas.tsx](frontend/src/components/flow/FlowCanvas.tsx.md)
- [frontend/src/components/flow/TaskNode.tsx](frontend/src/components/flow/TaskNode.tsx.md)
- [frontend/src/components/layout/InspectorPanel.tsx](frontend/src/components/layout/InspectorPanel.tsx.md)
- [frontend/src/components/layout/PlannerComposer.tsx](frontend/src/components/layout/PlannerComposer.tsx.md)
- [frontend/src/components/layout/Sidebar.tsx](frontend/src/components/layout/Sidebar.tsx.md)
- [frontend/src/components/layout/TopBar.tsx](frontend/src/components/layout/TopBar.tsx.md)
- [frontend/src/hooks/useCatalogBootstrap.ts](frontend/src/hooks/useCatalogBootstrap.ts.md)
- [frontend/src/hooks/useFlowLiveUpdates.ts](frontend/src/hooks/useFlowLiveUpdates.ts.md)
- [frontend/src/lib/apiClient.ts](frontend/src/lib/apiClient.ts.md)
- [frontend/src/lib/autoLayout.ts](frontend/src/lib/autoLayout.ts.md)
- [frontend/src/lib/flowSerialization.ts](frontend/src/lib/flowSerialization.ts.md)
- [frontend/src/lib/json.ts](frontend/src/lib/json.ts.md)
- [frontend/src/main.tsx](frontend/src/main.tsx.md)
- [frontend/src/store/useFlowStore.ts](frontend/src/store/useFlowStore.ts.md)
- [frontend/src/types/api.ts](frontend/src/types/api.ts.md)
- [frontend/src/vite-env.d.ts](frontend/src/vite-env.d.ts.md)

## Frontend-Konfiguration

- [frontend/.env.example](frontend/.env.example.md)
- [frontend/index.html](frontend/index.html.md)
- [frontend/package-lock.json](frontend/package-lock.json.md)
- [frontend/package.json](frontend/package.json.md)
- [frontend/tsconfig.app.json](frontend/tsconfig.app.json.md)
- [frontend/tsconfig.json](frontend/tsconfig.json.md)
- [frontend/tsconfig.node.json](frontend/tsconfig.node.json.md)
- [frontend/vite.config.d.ts](frontend/vite.config.d.ts.md)
- [frontend/vite.config.js](frontend/vite.config.js.md)
- [frontend/vite.config.ts](frontend/vite.config.ts.md)

## LLM-Runtime

- [LIT/README.md](LIT/README.md.md)
- [LIT/planner_test_prompt.txt](LIT/planner_test_prompt.txt.md)

## Projektdatei

- [.env.example](.env.example.md)
- [.gitignore](.gitignore.md)
- [Anweisung.md](Anweisung.md.md)
- [Dockerfile](Dockerfile.md)
- [LICENSE](LICENSE.md)
- [README.md](README.md.md)
- [pyproject.toml](pyproject.toml.md)
- [run-backend.cmd](run-backend.cmd.md)
- [run-backend.ps1](run-backend.ps1.md)
- [uml.html](uml.html.md)
- [uml_V3.mmd](uml_V3.mmd.md)

## Tests

- [tests/test_orchestrator.py](tests/test_orchestrator.py.md)

## Use Cases

- [Use_Cases/README.md](Use_Cases/README.md.md)
- [Use_Cases/platform_health_snapshot/README.md](Use_Cases/platform_health_snapshot/README.md.md)
- [Use_Cases/platform_health_snapshot/flow.json](Use_Cases/platform_health_snapshot/flow.json.md)
- [Use_Cases/platform_health_snapshot/run.ps1](Use_Cases/platform_health_snapshot/run.ps1.md)
- [Use_Cases/platform_health_snapshot/setup.ps1](Use_Cases/platform_health_snapshot/setup.ps1.md)
- [Use_Cases/semantic_ticket_triage/README.md](Use_Cases/semantic_ticket_triage/README.md.md)
- [Use_Cases/semantic_ticket_triage/flow.json](Use_Cases/semantic_ticket_triage/flow.json.md)
- [Use_Cases/semantic_ticket_triage/run.ps1](Use_Cases/semantic_ticket_triage/run.ps1.md)
- [Use_Cases/semantic_ticket_triage/setup.ps1](Use_Cases/semantic_ticket_triage/setup.ps1.md)

## Werkzeug

- [tools/build_code_release.ps1](tools/build_code_release.ps1.md)
- [tools/generate_docs.py](tools/generate_docs.py.md)
```

## File: `reference/LICENSE.md`  
- Path: `reference/LICENSE.md`  
- Size: 826 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `LICENSE`

- Quellpfad: [LICENSE](../../LICENSE)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Projektdatei mit eigener Rolle im Repository.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/LIT/planner_test_prompt.txt.md`  
- Path: `reference/LIT/planner_test_prompt.txt.md`  
- Size: 888 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `LIT/planner_test_prompt.txt`

- Quellpfad: [LIT/planner_test_prompt.txt](../../../LIT/planner_test_prompt.txt)
- Kategorie: `LLM-Runtime`

## Aufgabe der Datei

Projektdatei mit eigener Rolle im Repository.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/LIT/README.md.md`  
- Path: `reference/LIT/README.md.md`  
- Size: 993 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `LIT/README.md`

- Quellpfad: [LIT/README.md](../../../LIT/README.md)
- Kategorie: `LLM-Runtime`

## Aufgabe der Datei

Hinweise zur lokalen LiteRT-LM-Laufzeit und zu Modelldateien.

## Wann du diese Datei bearbeitest

Wenn Binary- oder Modellsetup aktualisiert wird.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/planning/lit_planner.py](../src/nova_synesis/planning/lit_planner.py.md)
- [.env.example](../.env.example.md)
```

## File: `reference/pyproject.toml.md`  
- Path: `reference/pyproject.toml.md`  
- Size: 1012 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `pyproject.toml`

- Quellpfad: [pyproject.toml](../../pyproject.toml)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Python-Paketdefinition mit Abhaengigkeiten, CLI und Testkonfiguration.

## Wann du diese Datei bearbeitest

Wenn Python-Abhaengigkeiten, Packaging oder Skripte geaendert werden.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/cli.py](src/nova_synesis/cli.py.md)
- [tests/test_orchestrator.py](tests/test_orchestrator.py.md)
```

## File: `reference/README.md.md`  
- Path: `reference/README.md.md`  
- Size: 1000 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `README.md`

- Quellpfad: [README.md](../../README.md)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Projektweiter Schnellstart fuer Backend, Frontend und Planner.

## Wann du diese Datei bearbeitest

Wenn sich Startablauf oder Hauptfunktionen fuer Entwickler aendern.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [docs/README.md](docs/README.md.md)
- [run-backend.ps1](run-backend.ps1.md)
- [frontend/package.json](frontend/package.json.md)
```

## File: `reference/run-backend.cmd.md`  
- Path: `reference/run-backend.cmd.md`  
- Size: 843 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `run-backend.cmd`

- Quellpfad: [run-backend.cmd](../../run-backend.cmd)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Skript fuer lokale Entwicklerablaeufe.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/run-backend.ps1.md`  
- Path: `reference/run-backend.ps1.md`  
- Size: 971 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `run-backend.ps1`

- Quellpfad: [run-backend.ps1](../../run-backend.ps1)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Empfohlenes Windows-Startskript fuer das Backend.

## Wann du diese Datei bearbeitest

Wenn der lokale Backend-Start fuer Entwickler angepasst werden soll.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/cli.py](src/nova_synesis/cli.py.md)
- [run-backend.cmd](run-backend.cmd.md)
```

## File: `reference/src/nova_synesis/__init__.py.md`  
- Path: `reference/src/nova_synesis/__init__.py.md`  
- Size: 917 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/__init__.py`

- Quellpfad: [src/nova_synesis/__init__.py](../../../../src/nova_synesis/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.api.app import create_app`
- `from nova_synesis.config import Settings`
- `from nova_synesis.services.orchestrator import OrchestratorService, create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/api/__init__.py.md`  
- Path: `reference/src/nova_synesis/api/__init__.py.md`  
- Size: 793 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/api/__init__.py`

- Quellpfad: [src/nova_synesis/api/__init__.py](../../../../../src/nova_synesis/api/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.api.app import create_app`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/api/app.py.md`  
- Path: `reference/src/nova_synesis/api/app.py.md`  
- Size: 2692 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/api/app.py`

- Quellpfad: [src/nova_synesis/api/app.py](../../../../../src/nova_synesis/api/app.py)
- Kategorie: `Backend`

## Aufgabe der Datei

FastAPI- und WebSocket-Schicht des Backends inklusive Request-Modelle, Flow-Validierung und Live-Streaming.

## Wann du diese Datei bearbeitest

Wenn API-Endpunkte, Schemafelder, Sicherheitspruefung oder Live-Streaming erweitert werden.

## Klassen

### `CapabilityModel`

Datenmodell `CapabilityModel` fuer validierte Schichtgrenzen.

### `CommunicationModel`

Datenmodell `CommunicationModel` fuer validierte Schichtgrenzen.

### `AgentCreateRequest`

Datenmodell `AgentCreateRequest` fuer validierte Schichtgrenzen.

### `MemorySystemCreateRequest`

Datenmodell `MemorySystemCreateRequest` fuer validierte Schichtgrenzen.

### `ResourceCreateRequest`

Datenmodell `ResourceCreateRequest` fuer validierte Schichtgrenzen.

### `RetryPolicyModel`

Datenmodell `RetryPolicyModel` fuer validierte Schichtgrenzen.

### `TaskSpecModel`

Datenmodell `TaskSpecModel` fuer validierte Schichtgrenzen.

### `EdgeModel`

Datenmodell `EdgeModel` fuer validierte Schichtgrenzen.

### `FlowCreateRequest`

Datenmodell `FlowCreateRequest` fuer validierte Schichtgrenzen.

### `IntentRequest`

Datenmodell `IntentRequest` fuer validierte Schichtgrenzen.

### `LLMPlannerRequest`

Datenmodell `LLMPlannerRequest` fuer validierte Schichtgrenzen.

## Funktionen

- `create_app(settings, orchestrator)`: Erzeugt die FastAPI-Anwendung und registriert ihre Endpunkte.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `from contextlib import asynccontextmanager`
- `from typing import Any`
- `from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect`
- `from fastapi.middleware.cors import CORSMiddleware`
- `from pydantic import BaseModel, Field`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import MemoryType, ProtocolType, ResourceType, RollbackStrategy`
- `from nova_synesis.services.orchestrator import OrchestratorService, create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)
- [frontend/src/lib/apiClient.ts](../../../frontend/src/lib/apiClient.ts.md)
- [frontend/src/types/api.ts](../../../frontend/src/types/api.ts.md)
```

## File: `reference/src/nova_synesis/cli.py.md`  
- Path: `reference/src/nova_synesis/cli.py.md`  
- Size: 1585 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/cli.py`

- Quellpfad: [src/nova_synesis/cli.py](../../../../src/nova_synesis/cli.py)
- Kategorie: `Backend`

## Aufgabe der Datei

CLI-Einstiegspunkt fuer API-Start, Flow-Ausfuehrung und lokale Hilfsaufgaben.

## Wann du diese Datei bearbeitest

Wenn neue CLI-Kommandos oder Startoptionen hinzukommen.

## Funktionen

- `build_parser()`: Funktion oder Definition `build_parser` dieses Moduls.
- `_build_settings(args)`: Funktion oder Definition `_build_settings` dieses Moduls.
- `_execute_intent_from_file(file_path, settings)`: Funktion oder Definition `_execute_intent_from_file` dieses Moduls.
- `_run_flow_spec_from_file(file_path, settings)`: Funktion oder Definition `_run_flow_spec_from_file` dieses Moduls.
- `main()`: Funktion oder Definition `main` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import argparse`
- `import asyncio`
- `import json`
- `from pathlib import Path`
- `from typing import Any`
- `import uvicorn`
- `from nova_synesis.api.app import create_app`
- `from nova_synesis.config import Settings`
- `from nova_synesis.services.orchestrator import create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [run-backend.ps1](../../run-backend.ps1.md)
- [pyproject.toml](../../pyproject.toml.md)
```

## File: `reference/src/nova_synesis/communication/__init__.py.md`  
- Path: `reference/src/nova_synesis/communication/__init__.py.md`  
- Size: 855 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/communication/__init__.py`

- Quellpfad: [src/nova_synesis/communication/__init__.py](../../../../../src/nova_synesis/communication/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.communication.adapters import CommunicationAdapterFactory`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/communication/adapters.py.md`  
- Path: `reference/src/nova_synesis/communication/adapters.py.md`  
- Size: 2974 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/communication/adapters.py`

- Quellpfad: [src/nova_synesis/communication/adapters.py](../../../../../src/nova_synesis/communication/adapters.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Klassen

### `CommunicationAdapter`

Klasse `CommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, protocol, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.
- `close(self)`: Funktion oder Definition `close` dieses Moduls.

### `RestCommunicationAdapter`

Klasse `RestCommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_get_client(self)`: Funktion oder Definition `_get_client` dieses Moduls.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.
- `close(self)`: Funktion oder Definition `close` dieses Moduls.

### `WebSocketCommunicationAdapter`

Klasse `WebSocketCommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_get_connection(self)`: Funktion oder Definition `_get_connection` dieses Moduls.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.
- `close(self)`: Funktion oder Definition `close` dieses Moduls.

### `MessageQueueCommunicationAdapter`

Klasse `MessageQueueCommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_get_queue(self, endpoint)`: Funktion oder Definition `_get_queue` dieses Moduls.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.

### `CommunicationAdapterFactory`

Factory-Klasse `CommunicationAdapterFactory` zum Erzeugen passender Objekte.

Methoden:

- `create(protocol, endpoint, config)`: Funktion oder Definition `create` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import json`
- `from typing import Any`
- `import httpx`
- `import websockets`
- `from nova_synesis.domain.models import ProtocolType`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/config.py.md`  
- Path: `reference/src/nova_synesis/config.py.md`  
- Size: 1301 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/config.py`

- Quellpfad: [src/nova_synesis/config.py](../../../../src/nova_synesis/config.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Zentrale Laufzeitkonfiguration des Backends inklusive LiteRT- und Semantic-Firewall-Settings.

## Wann du diese Datei bearbeitest

Wenn neue Settings, Standardpfade, Planner-Optionen oder Policy-Grenzen benoetigt werden.

## Klassen

### `Settings`

Dataklasse fuer die Backend-Laufzeitkonfiguration.

Methoden:

- `from_env(cls)`: Laedt Settings aus Umgebungsvariablen mit sicheren Defaults.
- `ensure_directories(self)`: Erzeugt benoetigte Daten- und Arbeitsverzeichnisse.

## Funktionen

- `_env(primary, legacy, default)`: Funktion oder Definition `_env` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import os`
- `from dataclasses import dataclass`
- `from pathlib import Path`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [.env.example](../../.env.example.md)
- [src/nova_synesis/cli.py](cli.py.md)
```

## File: `reference/src/nova_synesis/domain/__init__.py.md`  
- Path: `reference/src/nova_synesis/domain/__init__.py.md`  
- Size: 799 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/domain/__init__.py`

- Quellpfad: [src/nova_synesis/domain/__init__.py](../../../../../src/nova_synesis/domain/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.domain.models import (`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/domain/models.py.md`  
- Path: `reference/src/nova_synesis/domain/models.py.md`  
- Size: 6691 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/domain/models.py`

- Quellpfad: [src/nova_synesis/domain/models.py](../../../../../src/nova_synesis/domain/models.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Kern-Domaenenmodell mit Agenten, Ressourcen, Tasks, Bedingungen und ExecutionFlow.

## Wann du diese Datei bearbeitest

Wenn das fachliche Laufzeitmodell des Systems veraendert wird.

## Klassen

### `AgentState`

Klasse `AgentState` dieses Moduls.

### `ProtocolType`

Klasse `ProtocolType` dieses Moduls.

### `MemoryType`

Klasse `MemoryType` dieses Moduls.

### `TaskStatus`

Klasse `TaskStatus` dieses Moduls.

### `ExecutionStatus`

Klasse `ExecutionStatus` dieses Moduls.

### `RollbackStrategy`

Klasse `RollbackStrategy` dieses Moduls.

### `ResourceType`

Klasse `ResourceType` dieses Moduls.

### `ResourceState`

Klasse `ResourceState` dieses Moduls.

### `FlowState`

Klasse `FlowState` dieses Moduls.

### `Capability`

Klasse `Capability` dieses Moduls.

### `RetryPolicy`

Klasse `RetryPolicy` dieses Moduls.

Methoden:

- `next_delay(self, attempt)`: Funktion oder Definition `next_delay` dieses Moduls.

### `ErrorEvent`

Klasse `ErrorEvent` dieses Moduls.

Methoden:

- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.

### `SafeExpressionEvaluator`

Klasse `SafeExpressionEvaluator` dieses Moduls.

Methoden:

- `__init__(self, context)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `evaluate(self, expression)`: Funktion oder Definition `evaluate` dieses Moduls.
- `visit_Name(self, node)`: AST-Besuchsmethode fuer `Name`-Knoten.
- `visit_Constant(self, node)`: AST-Besuchsmethode fuer `Constant`-Knoten.
- `visit_List(self, node)`: AST-Besuchsmethode fuer `List`-Knoten.
- `visit_Tuple(self, node)`: AST-Besuchsmethode fuer `Tuple`-Knoten.
- `visit_Dict(self, node)`: AST-Besuchsmethode fuer `Dict`-Knoten.
- `visit_BoolOp(self, node)`: AST-Besuchsmethode fuer `BoolOp`-Knoten.
- `visit_UnaryOp(self, node)`: AST-Besuchsmethode fuer `UnaryOp`-Knoten.
- `visit_BinOp(self, node)`: AST-Besuchsmethode fuer `BinOp`-Knoten.
- `visit_Compare(self, node)`: AST-Besuchsmethode fuer `Compare`-Knoten.
- `visit_Subscript(self, node)`: AST-Besuchsmethode fuer `Subscript`-Knoten.
- `visit_Call(self, node)`: AST-Besuchsmethode fuer `Call`-Knoten.
- `generic_visit(self, node)`: Funktion oder Definition `generic_visit` dieses Moduls.

### `Condition`

Klasse `Condition` dieses Moduls.

Methoden:

- `evaluate(self, context)`: Funktion oder Definition `evaluate` dieses Moduls.

### `Resource`

Klasse `Resource` dieses Moduls.

Methoden:

- `__post_init__(self)`: Funktion oder Definition `__post_init__` dieses Moduls.
- `capacity(self)`: Funktion oder Definition `capacity` dieses Moduls.
- `acquire(self, timeout)`: Funktion oder Definition `acquire` dieses Moduls.
- `release(self)`: Funktion oder Definition `release` dieses Moduls.
- `health_check(self)`: Funktion oder Definition `health_check` dieses Moduls.

### `Agent`

Klasse `Agent` dieses Moduls.

Methoden:

- `capability_index(self)`: Funktion oder Definition `capability_index` dieses Moduls.
- `can_execute(self, required_capabilities)`: Funktion oder Definition `can_execute` dieses Moduls.
- `perceive(self, input_data)`: Funktion oder Definition `perceive` dieses Moduls.
- `decide(self, context)`: Funktion oder Definition `decide` dieses Moduls.
- `act(self, task)`: Funktion oder Definition `act` dieses Moduls.
- `communicate(self, message, target, protocol)`: Funktion oder Definition `communicate` dieses Moduls.

### `Task`

Klasse `Task` dieses Moduls.

Methoden:

- `execute(self)`: Fuehrt die Kernarbeit von `execute` aus.
- `validate(self, result)`: Funktion oder Definition `validate` dieses Moduls.
- `complete(self, output)`: Funktion oder Definition `complete` dieses Moduls.
- `reset(self)`: Funktion oder Definition `reset` dieses Moduls.

### `TaskExecution`

Klasse `TaskExecution` dieses Moduls.

Methoden:

- `start(self)`: Funktion oder Definition `start` dieses Moduls.
- `finish(self, result)`: Funktion oder Definition `finish` dieses Moduls.
- `record_error(self, error)`: Funktion oder Definition `record_error` dieses Moduls.
- `rollback(self, strategy)`: Funktion oder Definition `rollback` dieses Moduls.
- `retry(self)`: Funktion oder Definition `retry` dieses Moduls.

### `Intent`

Klasse `Intent` dieses Moduls.

Methoden:

- `refine(self, updates)`: Funktion oder Definition `refine` dieses Moduls.
- `plan(self, planner, agents, resources, task_id_allocator, flow_id_allocator)`: Funktion oder Definition `plan` dieses Moduls.
- `promote_to_task(self, planner, agents, resources, task_id_allocator)`: Funktion oder Definition `promote_to_task` dieses Moduls.

### `FlowNode`

Klasse `FlowNode` dieses Moduls.

### `FlowEdge`

Klasse `FlowEdge` dieses Moduls.

### `ExecutionFlow`

Graph-Modell des ausfuehrbaren Workflows.

Methoden:

- `add_node(self, node)`: Funktion oder Definition `add_node` dieses Moduls.
- `add_edge(self, edge)`: Funktion oder Definition `add_edge` dieses Moduls.
- `incoming_edges(self, node_id)`: Funktion oder Definition `incoming_edges` dieses Moduls.
- `outgoing_edges(self, node_id)`: Funktion oder Definition `outgoing_edges` dieses Moduls.
- `run(self, executor)`: Steuert den Ablauf von `run`.
- `pause(self)`: Funktion oder Definition `pause` dieses Moduls.
- `observe(self)`: Erzeugt den serialisierbaren Zustand eines Flows fuer API und UI.

## Funktionen

- `utcnow()`: Funktion oder Definition `utcnow` dieses Moduls.
- `maybe_await(value)`: Funktion oder Definition `maybe_await` dieses Moduls.
- `safe_evaluate(expression, context)`: Funktion oder Definition `safe_evaluate` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import ast`
- `import asyncio`
- `import sqlite3`
- `from dataclasses import dataclass, field`
- `from datetime import datetime, timezone`
- `from enum import StrEnum`
- `from pathlib import Path`
- `from random import uniform`
- `from typing import TYPE_CHECKING, Any, Callable`
- `import httpx`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/engine.py](../runtime/engine.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)
```

## File: `reference/src/nova_synesis/memory/__init__.py.md`  
- Path: `reference/src/nova_synesis/memory/__init__.py.md`  
- Size: 833 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/memory/__init__.py`

- Quellpfad: [src/nova_synesis/memory/__init__.py](../../../../../src/nova_synesis/memory/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.memory.systems import MemoryManager, MemorySystemFactory`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/memory/systems.py.md`  
- Path: `reference/src/nova_synesis/memory/systems.py.md`  
- Size: 4945 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/memory/systems.py`

- Quellpfad: [src/nova_synesis/memory/systems.py](../../../../../src/nova_synesis/memory/systems.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Implementierungen fuer Kurzzeit-, Langzeit- und Vektor-Speicher.

## Wann du diese Datei bearbeitest

Wenn Speicherverhalten, Suche oder Persistenz geaendert werden.

## Klassen

### `MemorySearchHit`

Klasse `MemorySearchHit` dieses Moduls.

Methoden:

- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.

### `MemorySystem`

Klasse `MemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, memory_type, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `ShortTermMemorySystem`

Klasse `ShortTermMemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_load_from_disk(self)`: Funktion oder Definition `_load_from_disk` dieses Moduls.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `_score_value(self, value, query)`: Funktion oder Definition `_score_value` dieses Moduls.
- `_extract_embedding(value)`: Funktion oder Definition `_extract_embedding` dieses Moduls.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `LongTermMemorySystem`

Klasse `LongTermMemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `VectorMemorySystem`

Klasse `VectorMemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `MemorySystemFactory`

Factory-Klasse `MemorySystemFactory` zum Erzeugen passender Objekte.

Methoden:

- `create(memory_id, memory_type, backend, config)`: Funktion oder Definition `create` dieses Moduls.

### `MemoryManager`

Koordinationsklasse `MemoryManager` fuer mehrere Instanzen oder Zustandsobjekte.

Methoden:

- `__init__(self)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register(self, system)`: Registriert Verhalten oder Objekte fuer `register`.
- `get(self, memory_id)`: Funktion oder Definition `get` dieses Moduls.
- `list(self)`: Funktion oder Definition `list` dieses Moduls.
- `store(self, memory_id, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, memory_id, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, memory_id, query, limit)`: Sucht passende Daten fuer `search`.
- `persist_all(self)`: Schreibt Daten fuer `persist_all` in einen dauerhaften Speicher.

## Funktionen

- `utcnow_iso()`: Funktion oder Definition `utcnow_iso` dieses Moduls.
- `cosine_similarity(left, right)`: Funktion oder Definition `cosine_similarity` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import json`
- `import math`
- `import sqlite3`
- `from abc import ABC, abstractmethod`
- `from collections import OrderedDict`
- `from dataclasses import dataclass, field`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import Any`
- `from nova_synesis.domain.models import MemoryType`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/handlers.py](../runtime/handlers.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)
```

## File: `reference/src/nova_synesis/persistence/__init__.py.md`  
- Path: `reference/src/nova_synesis/persistence/__init__.py.md`  
- Size: 845 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/persistence/__init__.py`

- Quellpfad: [src/nova_synesis/persistence/__init__.py](../../../../../src/nova_synesis/persistence/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.persistence.sqlite_repository import SQLiteRepository`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/persistence/sqlite_repository.py.md`  
- Path: `reference/src/nova_synesis/persistence/sqlite_repository.py.md`  
- Size: 2488 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/persistence/sqlite_repository.py`

- Quellpfad: [src/nova_synesis/persistence/sqlite_repository.py](../../../../../src/nova_synesis/persistence/sqlite_repository.py)
- Kategorie: `Backend`

## Aufgabe der Datei

SQLite-Persistenzschicht fuer Flows, Ausfuehrungen und Katalogobjekte.

## Wann du diese Datei bearbeitest

Wenn Datenbankstruktur oder gespeicherte Felder angepasst werden.

## Klassen

### `SQLiteRepository`

Persistenzschicht fuer SQLite.

Methoden:

- `__init__(self, database_path)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_initialize_schema(self)`: Funktion oder Definition `_initialize_schema` dieses Moduls.
- `next_id(self, name)`: Funktion oder Definition `next_id` dieses Moduls.
- `save_agent(self, agent)`: Persistiert Daten fuer `save_agent` dauerhaft.
- `save_memory_system(self, memory_system)`: Persistiert Daten fuer `save_memory_system` dauerhaft.
- `save_resource(self, resource)`: Persistiert Daten fuer `save_resource` dauerhaft.
- `save_intent(self, intent)`: Persistiert Daten fuer `save_intent` dauerhaft.
- `save_task(self, task)`: Persistiert Daten fuer `save_task` dauerhaft.
- `save_flow(self, flow)`: Persistiert Daten fuer `save_flow` dauerhaft.
- `save_execution(self, execution, flow_id)`: Persistiert Daten fuer `save_execution` dauerhaft.
- `list_executions(self)`: Gibt eine Liste von Daten fuer `list_executions` zurueck.
- `get_flow_record(self, flow_id)`: Liest Daten fuer `get_flow_record` aus einem Speicher oder einer Laufzeitquelle.
- `_decode_execution_row(row)`: Funktion oder Definition `_decode_execution_row` dieses Moduls.
- `_decode_flow_row(row)`: Funktion oder Definition `_decode_flow_row` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import json`
- `import sqlite3`
- `import threading`
- `from pathlib import Path`
- `from typing import Any`
- `from nova_synesis.domain.models import Agent, ExecutionFlow, Intent, Resource, Task, TaskExecution`
- `from nova_synesis.memory.systems import MemorySystem`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)
```

## File: `reference/src/nova_synesis/planning/__init__.py.md`  
- Path: `reference/src/nova_synesis/planning/__init__.py.md`  
- Size: 921 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/planning/__init__.py`

- Quellpfad: [src/nova_synesis/planning/__init__.py](../../../../../src/nova_synesis/planning/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.planning.planner import IntentPlanner`
- `from nova_synesis.planning.lit_planner import LiteRTPlanner, PlannerCatalog, PlannerGraphResult`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/planning/lit_planner.py.md`  
- Path: `reference/src/nova_synesis/planning/lit_planner.py.md`  
- Size: 3866 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/planning/lit_planner.py`

- Quellpfad: [src/nova_synesis/planning/lit_planner.py](../../../../../src/nova_synesis/planning/lit_planner.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Lokaler LLM-Planer ueber LiteRT-LM inklusive Prompting, Parsing, Katalognutzung und Graph-Normalisierung.

## Wann du diese Datei bearbeitest

Wenn Planner-Qualitaet, Modellaufruf, Katalogfilterung oder Vorvalidierung verbessert werden soll.

## Klassen

### `PlannerCatalog`

Klasse `PlannerCatalog` dieses Moduls.

### `PlannerGraphResult`

Klasse `PlannerGraphResult` dieses Moduls.

### `LiteRTPlanner`

Lokale LLM-Planung ueber LiteRT-LM.

Methoden:

- `__init__(self, settings)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `status(self)`: Funktion oder Definition `status` dieses Moduls.
- `ensure_available(self)`: Funktion oder Definition `ensure_available` dieses Moduls.
- `generate_flow_request(self, prompt, catalog, current_flow, max_nodes)`: Erzeugt aus natuerlicher Sprache einen validierten FlowRequest.
- `_invoke_model(self, planner_prompt)`: Funktion oder Definition `_invoke_model` dieses Moduls.
- `_build_prompt(self, prompt, catalog, current_flow, max_nodes)`: Funktion oder Definition `_build_prompt` dieses Moduls.
- `_extract_explanation(parsed)`: Funktion oder Definition `_extract_explanation` dieses Moduls.
- `_parse_model_output(self, raw_response)`: Funktion oder Definition `_parse_model_output` dieses Moduls.
- `_extract_json_object(text)`: Funktion oder Definition `_extract_json_object` dieses Moduls.
- `_normalize_flow_request(self, parsed, catalog, max_nodes)`: Funktion oder Definition `_normalize_flow_request` dieses Moduls.
- `_normalize_node_id(raw_value)`: Funktion oder Definition `_normalize_node_id` dieses Moduls.
- `_normalize_object(raw_value)`: Funktion oder Definition `_normalize_object` dieses Moduls.
- `_normalize_string_list(raw_value)`: Funktion oder Definition `_normalize_string_list` dieses Moduls.
- `_normalize_conditions(raw_value)`: Funktion oder Definition `_normalize_conditions` dieses Moduls.
- `_normalize_retry_policy(raw_value)`: Funktion oder Definition `_normalize_retry_policy` dieses Moduls.
- `_normalize_compensation_handler(raw_value, allowed_handlers, warnings, node_id)`: Funktion oder Definition `_normalize_compensation_handler` dieses Moduls.
- `_normalize_edges(raw_edges, node_ids, warnings)`: Funktion oder Definition `_normalize_edges` dieses Moduls.
- `_merge_dependencies(normalized_nodes, normalized_edges)`: Funktion oder Definition `_merge_dependencies` dieses Moduls.
- `_validate_acyclic(normalized_nodes)`: Funktion oder Definition `_validate_acyclic` dieses Moduls.
- `_normalize_handler_input(handler_name, input_payload, node_id, dependencies, memory_ids, comm_agent_ids, warnings)`: Funktion oder Definition `_normalize_handler_input` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import json`
- `import re`
- `import subprocess`
- `import tempfile`
- `from dataclasses import dataclass`
- `from pathlib import Path`
- `from typing import Any`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import ResourceType, RollbackStrategy`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [LIT/lit.windows_x86_64.exe](../../../LIT/lit.windows_x86_64.exe.md)
- [LIT/gemma-4-E2B-it.litertlm](../../../LIT/gemma-4-E2B-it.litertlm.md)
- [frontend/src/components/layout/PlannerComposer.tsx](../../../frontend/src/components/layout/PlannerComposer.tsx.md)
```

## File: `reference/src/nova_synesis/planning/planner.py.md`  
- Path: `reference/src/nova_synesis/planning/planner.py.md`  
- Size: 2092 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/planning/planner.py`

- Quellpfad: [src/nova_synesis/planning/planner.py](../../../../../src/nova_synesis/planning/planner.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Regelbasierter Intent-zu-Task-Planer.

## Wann du diese Datei bearbeitest

Wenn strukturierte Intents anders in Tasks zerlegt werden sollen.

## Klassen

### `TaskBlueprint`

Klasse `TaskBlueprint` dieses Moduls.

### `IntentPlanner`

Regelbasierter Planer fuer strukturierte Intents.

Methoden:

- `plan_intent(self, intent, agents, resources, task_id_allocator, flow_id_allocator)`: Funktion oder Definition `plan_intent` dieses Moduls.
- `promote_to_task(self, intent, agents, resources, task_id_allocator)`: Funktion oder Definition `promote_to_task` dieses Moduls.
- `_extract_blueprints(self, intent)`: Funktion oder Definition `_extract_blueprints` dieses Moduls.
- `_build_retry_policy(raw_policy)`: Funktion oder Definition `_build_retry_policy` dieses Moduls.
- `_normalize_resource_type(value)`: Funktion oder Definition `_normalize_resource_type` dieses Moduls.
- `_group_resources_by_type(resources)`: Funktion oder Definition `_group_resources_by_type` dieses Moduls.
- `_resolve_resources(self, blueprint, resource_index, resources_by_type)`: Funktion oder Definition `_resolve_resources` dieses Moduls.
- `_select_agent(self, blueprint, agents)`: Funktion oder Definition `_select_agent` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `from dataclasses import dataclass, field`
- `from typing import Any, Callable`
- `from nova_synesis.domain.models import (`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/domain/models.py](../domain/models.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)
```

## File: `reference/src/nova_synesis/resources/__init__.py.md`  
- Path: `reference/src/nova_synesis/resources/__init__.py.md`  
- Size: 826 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/resources/__init__.py`

- Quellpfad: [src/nova_synesis/resources/__init__.py](../../../../../src/nova_synesis/resources/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.resources.manager import ResourceManager`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/resources/manager.py.md`  
- Path: `reference/src/nova_synesis/resources/manager.py.md`  
- Size: 1916 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/resources/manager.py`

- Quellpfad: [src/nova_synesis/resources/manager.py](../../../../../src/nova_synesis/resources/manager.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Verwaltung und Aufloesung registrierter Ressourcen.

## Wann du diese Datei bearbeitest

Wenn Ressourcenallokation oder Fallbacks angepasst werden.

## Klassen

### `ResourceManager`

Koordinationsklasse `ResourceManager` fuer mehrere Instanzen oder Zustandsobjekte.

Methoden:

- `__init__(self)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register(self, resource)`: Registriert Verhalten oder Objekte fuer `register`.
- `get(self, resource_id)`: Funktion oder Definition `get` dieses Moduls.
- `list(self)`: Funktion oder Definition `list` dieses Moduls.
- `resolve_resources(self, resource_ids, resource_types)`: Funktion oder Definition `resolve_resources` dieses Moduls.
- `acquire_many(self, resources, timeout)`: Funktion oder Definition `acquire_many` dieses Moduls.
- `release_many(self, resources)`: Funktion oder Definition `release_many` dieses Moduls.
- `health_report(self)`: Funktion oder Definition `health_report` dieses Moduls.
- `find_fallback_resources(self, required_resources)`: Funktion oder Definition `find_fallback_resources` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `from collections import defaultdict`
- `from typing import Iterable`
- `from nova_synesis.domain.models import Resource, ResourceState, ResourceType`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/engine.py](../runtime/engine.py.md)
```

## File: `reference/src/nova_synesis/runtime/__init__.py.md`  
- Path: `reference/src/nova_synesis/runtime/__init__.py.md`  
- Size: 940 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/runtime/__init__.py`

- Quellpfad: [src/nova_synesis/runtime/__init__.py](../../../../../src/nova_synesis/runtime/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.runtime.engine import ExecutionContext, FlowExecutor, TaskExecutor`
- `from nova_synesis.runtime.handlers import TaskHandlerRegistry, register_default_handlers`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/runtime/engine.py.md`  
- Path: `reference/src/nova_synesis/runtime/engine.py.md`  
- Size: 2901 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/runtime/engine.py`

- Quellpfad: [src/nova_synesis/runtime/engine.py](../../../../../src/nova_synesis/runtime/engine.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Graph-Ausfuehrungsengine fuer Task- und Flow-Lifecycle inklusive Template-Aufloesung und Live-Snapshots.

## Wann du diese Datei bearbeitest

Wenn Ablaufsteuerung, Parallelitaet, Template-Kontext oder Snapshot-Logik geaendert wird.

## Klassen

### `ExecutionContext`

Klasse `ExecutionContext` dieses Moduls.

### `TaskExecutor`

Fuehrt eine einzelne Task inklusive Fehlerbehandlung aus.

Methoden:

- `__init__(self, context)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `execute_task(self, task, flow, flow_results, node_id)`: Fuehrt die Kernarbeit von `execute_task` aus.
- `_publish_task_event(self, flow_id, event_type, snapshot)`: Funktion oder Definition `_publish_task_event` dieses Moduls.

### `FlowExecutor`

Fuehrt einen gesamten Workflow-Graphen aus.

Methoden:

- `__init__(self, context, task_executor)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `run_flow(self, flow)`: Steuert den Ablauf von `run_flow`.
- `_is_ready(self, flow, node_id, completed, blocked, failed)`: Funktion oder Definition `_is_ready` dieses Moduls.
- `_is_blocked(self, flow, node_id, completed, blocked, failed)`: Funktion oder Definition `_is_blocked` dieses Moduls.
- `_snapshot(flow, completed, blocked, failed)`: Funktion oder Definition `_snapshot` dieses Moduls.
- `_publish_snapshot(self, flow, completed, blocked, failed, event_type)`: Funktion oder Definition `_publish_snapshot` dieses Moduls.
- `_publish_event(self, flow_id, event_type, snapshot)`: Funktion oder Definition `_publish_event` dieses Moduls.

## Funktionen

- `resolve_templates(value, context)`: Funktion oder Definition `resolve_templates` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import re`
- `from collections.abc import Awaitable, Callable`
- `from dataclasses import dataclass`
- `from pathlib import Path`
- `from typing import Any`
- `from nova_synesis.domain.models import (`
- `from nova_synesis.memory.systems import MemoryManager`
- `from nova_synesis.persistence.sqlite_repository import SQLiteRepository`
- `from nova_synesis.resources.manager import ResourceManager`
- `from nova_synesis.runtime.handlers import TaskHandlerRegistry`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/domain/models.py](../domain/models.py.md)
- [src/nova_synesis/runtime/handlers.py](handlers.py.md)
```

## File: `reference/src/nova_synesis/runtime/handlers.py.md`  
- Path: `reference/src/nova_synesis/runtime/handlers.py.md`  
- Size: 3149 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/runtime/handlers.py`

- Quellpfad: [src/nova_synesis/runtime/handlers.py](../../../../../src/nova_synesis/runtime/handlers.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Eingebaute Handler fuer HTTP, Memory, Messaging, Dateien und Serialisierung.

## Wann du diese Datei bearbeitest

Wenn neue Arbeitsbausteine hinzugefuegt oder bestehende Handler verbessert werden.

## Klassen

### `TaskHandlerRegistry`

Registry der registrierten Runtime-Handler.

Methoden:

- `__init__(self)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register(self, name, handler)`: Registriert Verhalten oder Objekte fuer `register`.
- `get(self, name)`: Funktion oder Definition `get` dieses Moduls.
- `names(self)`: Funktion oder Definition `names` dieses Moduls.
- `execute(self, name, context)`: Fuehrt die Kernarbeit von `execute` aus.

## Funktionen

- `_resolve_working_path(working_directory, raw_path, allow_outside_workdir)`: Funktion oder Definition `_resolve_working_path` dieses Moduls.
- `_primary_resource_endpoint(context, resource_type)`: Funktion oder Definition `_primary_resource_endpoint` dieses Moduls.
- `http_request_handler(context)`: Funktion oder Definition `http_request_handler` dieses Moduls.
- `memory_store_handler(context)`: Funktion oder Definition `memory_store_handler` dieses Moduls.
- `memory_retrieve_handler(context)`: Funktion oder Definition `memory_retrieve_handler` dieses Moduls.
- `memory_search_handler(context)`: Funktion oder Definition `memory_search_handler` dieses Moduls.
- `send_message_handler(context)`: Funktion oder Definition `send_message_handler` dieses Moduls.
- `resource_health_check_handler(context)`: Funktion oder Definition `resource_health_check_handler` dieses Moduls.
- `template_render_handler(context)`: Funktion oder Definition `template_render_handler` dieses Moduls.
- `merge_payloads_handler(context)`: Funktion oder Definition `merge_payloads_handler` dieses Moduls.
- `read_file_handler(context)`: Funktion oder Definition `read_file_handler` dieses Moduls.
- `write_file_handler(context)`: Funktion oder Definition `write_file_handler` dieses Moduls.
- `json_serialize_handler(context)`: Funktion oder Definition `json_serialize_handler` dieses Moduls.
- `register_default_handlers(registry)`: Registriert alle eingebauten Handler.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import inspect`
- `import json`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import Any, Awaitable, Callable`
- `import httpx`
- `from nova_synesis.domain.models import ResourceType`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/engine.py](engine.py.md)
- [frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx.md)
```

## File: `reference/src/nova_synesis/security/__init__.py.md`  
- Path: `reference/src/nova_synesis/security/__init__.py.md`  
- Size: 1048 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/security/__init__.py`

- Quellpfad: [src/nova_synesis/security/__init__.py](../../../../../src/nova_synesis/security/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Paketexporte fuer die semantische Sicherheitspruefung.

## Wann du diese Datei bearbeitest

Wenn Security-Klassen neu exportiert oder das Security-Paket umstrukturiert werden soll.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from .policy import FlowSecurityReport, SecurityFinding, SemanticFirewall`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/security/policy.py](policy.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)
```

## File: `reference/src/nova_synesis/security/policy.py.md`  
- Path: `reference/src/nova_synesis/security/policy.py.md`  
- Size: 4412 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/security/policy.py`

- Quellpfad: [src/nova_synesis/security/policy.py](../../../../../src/nova_synesis/security/policy.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Semantische Firewall fuer Flow- und Agent-Validierung vor Planung, Speicherung und Ausfuehrung.

## Wann du diese Datei bearbeitest

Wenn Sicherheitsregeln, Allowlists oder die Graph-Absichtspruefung veraendert werden muessen.

## Klassen

### `SecurityFinding`

Klasse `SecurityFinding` dieses Moduls.

Methoden:

- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.

### `FlowSecurityReport`

Strukturiertes Ergebnis einer Policy-Pruefung mit Fehlern und Warnungen.

Methoden:

- `add_violation(self, code, message, node_id, field)`: Funktion oder Definition `add_violation` dieses Moduls.
- `add_warning(self, code, message, node_id, field)`: Funktion oder Definition `add_warning` dieses Moduls.
- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.
- `ensure_allowed(self)`: Bricht den aktuellen Vorgang ab, wenn Regelverletzungen gefunden wurden.

### `SemanticFirewall`

Semantische Sicherheitspruefung fuer Flows, Agenten und aus Planner-Graphen abgeleitete Absichten.

Methoden:

- `__init__(self, settings)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `validate_agent_registration(self, name, capabilities, communication, existing_agents)`: Prueft Agent-Registrierung auf riskante Capabilities und unerlaubte Endpunkte.
- `validate_flow_request(self, nodes, edges, metadata, agents, resources, memory_systems, planner_generated, phase)`: Prueft Graph-Struktur, Expressions, Egress und Memory-Fluesse vor der Ausfuehrung.
- `_collect_edges(self, node_index, edges, report)`: Funktion oder Definition `_collect_edges` dieses Moduls.
- `_validate_acyclic(self, node_index, edges, report)`: Funktion oder Definition `_validate_acyclic` dieses Moduls.
- `_validate_http_request(self, node_id, node, input_payload, resource_index, report)`: Funktion oder Definition `_validate_http_request` dieses Moduls.
- `_validate_send_message(self, node_id, input_payload, agent_index, report)`: Funktion oder Definition `_validate_send_message` dieses Moduls.
- `_validate_file_handler(self, node_id, input_payload, report)`: Funktion oder Definition `_validate_file_handler` dieses Moduls.
- `_validate_expression_container(self, node_id, field, value, allowed_names, report)`: Funktion oder Definition `_validate_expression_container` dieses Moduls.
- `_validate_expression_map(self, node_id, field, expressions, allowed_names, report)`: Funktion oder Definition `_validate_expression_map` dieses Moduls.
- `_validate_template_string(self, node_id, field, template, allowed_names, report)`: Funktion oder Definition `_validate_template_string` dieses Moduls.
- `_validate_expression(self, node_id, field, expression, allowed_names, report)`: Funktion oder Definition `_validate_expression` dieses Moduls.
- `_detect_sensitive_exfiltration(self, node_index, edges, agent_index, memory_index, report)`: Funktion oder Definition `_detect_sensitive_exfiltration` dieses Moduls.
- `_detect_memory_poisoning(self, node_index, edges, memory_index, report)`: Funktion oder Definition `_detect_memory_poisoning` dieses Moduls.
- `_build_upstream_map(node_index, edges)`: Funktion oder Definition `_build_upstream_map` dieses Moduls.
- `_is_allowed_host(self, host)`: Funktion oder Definition `_is_allowed_host` dieses Moduls.
- `_is_loopback_host(host)`: Funktion oder Definition `_is_loopback_host` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import ast`
- `import ipaddress`
- `from collections import deque`
- `from dataclasses import dataclass, field`
- `from typing import Any`
- `from urllib.parse import urlparse`
- `from nova_synesis.config import Settings`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)
- [src/nova_synesis/config.py](../config.py.md)
- [tests/test_orchestrator.py](../../../tests/test_orchestrator.py.md)
```

## File: `reference/src/nova_synesis/services/__init__.py.md`  
- Path: `reference/src/nova_synesis/services/__init__.py.md`  
- Size: 852 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/services/__init__.py`

- Quellpfad: [src/nova_synesis/services/__init__.py](../../../../../src/nova_synesis/services/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.services.orchestrator import OrchestratorService, create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/src/nova_synesis/services/orchestrator.py.md`  
- Path: `reference/src/nova_synesis/services/orchestrator.py.md`  
- Size: 5516 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `src/nova_synesis/services/orchestrator.py`

- Quellpfad: [src/nova_synesis/services/orchestrator.py](../../../../../src/nova_synesis/services/orchestrator.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Zentrale Service-Fassade des Backends inklusive Security-Gates, Planner-Katalog und Lifecycle-Management.

## Wann du diese Datei bearbeitest

Wenn Systemkomposition, Registrierungen, Policy-Durchsetzung oder Lifecycle-Management geaendert werden.

## Klassen

### `OrchestratorService`

Zentrale Fassade, die alle Backend-Bausteine zusammenhaelt.

Methoden:

- `__init__(self, settings, repository, planner, resource_manager, memory_manager, handler_registry)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register_handler(self, name, handler)`: Registriert Verhalten oder Objekte fuer `register_handler`.
- `register_memory_system(self, memory_id, memory_type, backend, config)`: Registriert Verhalten oder Objekte fuer `register_memory_system`.
- `register_agent(self, name, role, capabilities, communication, memory_ids)`: Registriert Verhalten oder Objekte fuer `register_agent`.
- `register_resource(self, resource_type, endpoint, metadata)`: Registriert Verhalten oder Objekte fuer `register_resource`.
- `create_intent(self, goal, constraints, priority)`: Funktion oder Definition `create_intent` dieses Moduls.
- `create_flow(self, nodes, edges, metadata)`: Funktion oder Definition `create_flow` dieses Moduls.
- `plan_intent(self, goal, constraints, priority)`: Funktion oder Definition `plan_intent` dieses Moduls.
- `execute_intent(self, goal, constraints, priority)`: Fuehrt die Kernarbeit von `execute_intent` aus.
- `run_flow(self, flow_id)`: Steuert den Ablauf von `run_flow`.
- `pause_flow(self, flow_id)`: Funktion oder Definition `pause_flow` dieses Moduls.
- `get_flow(self, flow_id)`: Liest Daten fuer `get_flow` aus einem Speicher oder einer Laufzeitquelle.
- `list_agents(self)`: Gibt eine Liste von Daten fuer `list_agents` zurueck.
- `list_resources(self)`: Gibt eine Liste von Daten fuer `list_resources` zurueck.
- `list_memory_systems(self)`: Gibt eine Liste von Daten fuer `list_memory_systems` zurueck.
- `list_executions(self)`: Gibt eine Liste von Daten fuer `list_executions` zurueck.
- `get_llm_planner_status(self)`: Liest Daten fuer `get_llm_planner_status` aus einem Speicher oder einer Laufzeitquelle.
- `generate_flow_with_llm(self, prompt, current_flow, max_nodes)`: Funktion oder Definition `generate_flow_with_llm` dieses Moduls.
- `shutdown(self)`: Funktion oder Definition `shutdown` dieses Moduls.
- `subscribe_flow(self, flow_id)`: Funktion oder Definition `subscribe_flow` dieses Moduls.
- `unsubscribe_flow(self, flow_id, queue)`: Funktion oder Definition `unsubscribe_flow` dieses Moduls.
- `publish_flow_event(self, flow_id, event_type, snapshot)`: Funktion oder Definition `publish_flow_event` dieses Moduls.
- `_persist_flow(self, flow)`: Funktion oder Definition `_persist_flow` dieses Moduls.
- `_schedule_publish(self, flow_id, event_type, snapshot)`: Funktion oder Definition `_schedule_publish` dieses Moduls.
- `_build_planner_catalog(self)`: Funktion oder Definition `_build_planner_catalog` dieses Moduls.
- `validate_flow_request(self, nodes, edges, metadata, planner_generated, phase)`: Funktion oder Definition `validate_flow_request` dieses Moduls.
- `_snapshot_nodes_to_specs(flow_snapshot)`: Funktion oder Definition `_snapshot_nodes_to_specs` dieses Moduls.
- `_default_memory_backend(self, memory_type)`: Funktion oder Definition `_default_memory_backend` dieses Moduls.
- `_serialize_agent(agent)`: Funktion oder Definition `_serialize_agent` dieses Moduls.
- `_serialize_resource(resource)`: Funktion oder Definition `_serialize_resource` dieses Moduls.
- `_serialize_memory_system(system)`: Funktion oder Definition `_serialize_memory_system` dieses Moduls.
- `_serialize_flow(flow)`: Funktion oder Definition `_serialize_flow` dieses Moduls.

## Funktionen

- `create_orchestrator(settings)`: Factory fuer ein komplett verdrahtetes Orchestrator-System.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import Any, Callable`
- `from nova_synesis.communication.adapters import CommunicationAdapterFactory`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import (`
- `from nova_synesis.memory.systems import MemoryManager, MemorySystemFactory`
- `from nova_synesis.persistence.sqlite_repository import SQLiteRepository`
- `from nova_synesis.planning.lit_planner import LiteRTPlanner, PlannerCatalog`
- `from nova_synesis.planning.planner import IntentPlanner`
- `from nova_synesis.resources.manager import ResourceManager`
- `from nova_synesis.runtime.engine import ExecutionContext, FlowExecutor, TaskExecutor`
- `from nova_synesis.runtime.handlers import TaskHandlerRegistry, register_default_handlers`
- `from nova_synesis.security import SemanticFirewall`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/api/app.py](../api/app.py.md)
- [src/nova_synesis/runtime/engine.py](../runtime/engine.py.md)
```

## File: `reference/tests/test_orchestrator.py.md`  
- Path: `reference/tests/test_orchestrator.py.md`  
- Size: 3466 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `tests/test_orchestrator.py`

- Quellpfad: [tests/test_orchestrator.py](../../../tests/test_orchestrator.py)
- Kategorie: `Tests`

## Aufgabe der Datei

Regressionstests fuer Backend, Planner, WebSocket-Livebetrieb und Semantic-Firewall.

## Wann du diese Datei bearbeitest

Wenn neue Features abgesichert, Sicherheitsregeln erweitert oder Fehler reproduzierbar getestet werden.

## Funktionen

- `build_settings(tmp_path)`: Funktion oder Definition `build_settings` dieses Moduls.
- `test_end_to_end_flow_with_vector_memory_and_message_queue(tmp_path)`: Funktion oder Definition `test_end_to_end_flow_with_vector_memory_and_message_queue` dieses Moduls.
- `test_fallback_resource_strategy_switches_to_secondary_resource(tmp_path)`: Funktion oder Definition `test_fallback_resource_strategy_switches_to_secondary_resource` dieses Moduls.
- `test_fastapi_flow_execution_endpoint(tmp_path)`: Funktion oder Definition `test_fastapi_flow_execution_endpoint` dieses Moduls.
- `test_websocket_flow_updates_stream_runtime_events(tmp_path)`: Funktion oder Definition `test_websocket_flow_updates_stream_runtime_events` dieses Moduls.
- `test_lit_planner_normalizes_graph_output(tmp_path)`: Funktion oder Definition `test_lit_planner_normalizes_graph_output` dieses Moduls.
- `test_semantic_firewall_rejects_cyclic_flow(tmp_path)`: Funktion oder Definition `test_semantic_firewall_rejects_cyclic_flow` dieses Moduls.
- `test_semantic_firewall_rejects_external_http_request(tmp_path)`: Funktion oder Definition `test_semantic_firewall_rejects_external_http_request` dieses Moduls.
- `test_semantic_firewall_blocks_send_message_endpoint_override(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_send_message_endpoint_override` dieses Moduls.
- `test_semantic_firewall_blocks_external_rest_agent_registration(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_external_rest_agent_registration` dieses Moduls.
- `test_semantic_firewall_blocks_sensitive_memory_exfiltration(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_sensitive_memory_exfiltration` dieses Moduls.
- `test_semantic_firewall_blocks_template_context_escape(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_template_context_escape` dieses Moduls.
- `test_planner_status_endpoint_exposes_lit_configuration(tmp_path)`: Funktion oder Definition `test_planner_status_endpoint_exposes_lit_configuration` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import threading`
- `from pathlib import Path`
- `import pytest`
- `from fastapi.testclient import TestClient`
- `from nova_synesis.api.app import create_app`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import MemoryType, ResourceType`
- `from nova_synesis.planning.lit_planner import LiteRTPlanner, PlannerCatalog`
- `from nova_synesis.services.orchestrator import create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/services/orchestrator.py](../src/nova_synesis/services/orchestrator.py.md)
- [src/nova_synesis/api/app.py](../src/nova_synesis/api/app.py.md)
```

## File: `reference/tools/build_code_release.ps1.md`  
- Path: `reference/tools/build_code_release.ps1.md`  
- Size: 881 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `tools/build_code_release.ps1`

- Quellpfad: [tools/build_code_release.ps1](../../../tools/build_code_release.ps1)
- Kategorie: `Werkzeug`

## Aufgabe der Datei

Skript fuer lokale Entwicklerablaeufe.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/tools/generate_docs.py.md`  
- Path: `reference/tools/generate_docs.py.md`  
- Size: 2233 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `tools/generate_docs.py`

- Quellpfad: [tools/generate_docs.py](../../../tools/generate_docs.py)
- Kategorie: `Werkzeug`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Funktionen

- `rel(path)`: Funktion oder Definition `rel` dieses Moduls.
- `excluded(path)`: Funktion oder Definition `excluded` dieses Moduls.
- `project_files()`: Funktion oder Definition `project_files` dieses Moduls.
- `doc_path(source)`: Funktion oder Definition `doc_path` dieses Moduls.
- `rlink(base, target)`: Funktion oder Definition `rlink` dieses Moduls.
- `source_link(doc, source)`: Funktion oder Definition `source_link` dieses Moduls.
- `doc_link(doc, source)`: Funktion oder Definition `doc_link` dieses Moduls.
- `category(r)`: Funktion oder Definition `category` dieses Moduls.
- `generic_purpose(path)`: Funktion oder Definition `generic_purpose` dieses Moduls.
- `generic_edit(path)`: Funktion oder Definition `generic_edit` dieses Moduls.
- `symbol_desc(name, kind, parent)`: Funktion oder Definition `symbol_desc` dieses Moduls.
- `imports_for(path)`: Funktion oder Definition `imports_for` dieses Moduls.
- `py_args(node)`: Funktion oder Definition `py_args` dieses Moduls.
- `py_symbols(path)`: Funktion oder Definition `py_symbols` dieses Moduls.
- `ts_symbols(path)`: Funktion oder Definition `ts_symbols` dieses Moduls.
- `symbol_block(path)`: Funktion oder Definition `symbol_block` dieses Moduls.
- `write_reference(files)`: Funktion oder Definition `write_reference` dieses Moduls.
- `write_guides(files)`: Funktion oder Definition `write_guides` dieses Moduls.
- `main()`: Funktion oder Definition `main` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import ast`
- `import os`
- `import re`
- `from collections import defaultdict`
- `from pathlib import Path`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/uml.html.md`  
- Path: `reference/uml.html.md`  
- Size: 837 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `uml.html`

- Quellpfad: [uml.html](../../uml.html)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

HTML-Datei fuer Visualisierung oder Browser-Einstieg.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/uml_V3.mmd.md`  
- Path: `reference/uml_V3.mmd.md`  
- Size: 904 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `uml_V3.mmd`

- Quellpfad: [uml_V3.mmd](../../uml_V3.mmd)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Mermaid-Quelle des Architekturdiagramms.

## Wann du diese Datei bearbeitest

Wenn die dokumentierte Zielarchitektur angepasst werden soll.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [uml.html](uml.html.md)
- [Anweisung.md](Anweisung.md.md)
```

## File: `reference/Use_Cases/platform_health_snapshot/flow.json.md`  
- Path: `reference/Use_Cases/platform_health_snapshot/flow.json.md`  
- Size: 922 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Use_Cases/platform_health_snapshot/flow.json`

- Quellpfad: [Use_Cases/platform_health_snapshot/flow.json](../../../../Use_Cases/platform_health_snapshot/flow.json)
- Kategorie: `Use Cases`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/Use_Cases/platform_health_snapshot/README.md.md`  
- Path: `reference/Use_Cases/platform_health_snapshot/README.md.md`  
- Size: 945 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Use_Cases/platform_health_snapshot/README.md`

- Quellpfad: [Use_Cases/platform_health_snapshot/README.md](../../../../Use_Cases/platform_health_snapshot/README.md)
- Kategorie: `Use Cases`

## Aufgabe der Datei

Markdown-Datei mit Projektwissen oder Anweisungen.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/Use_Cases/platform_health_snapshot/run.ps1.md`  
- Path: `reference/Use_Cases/platform_health_snapshot/run.ps1.md`  
- Size: 927 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Use_Cases/platform_health_snapshot/run.ps1`

- Quellpfad: [Use_Cases/platform_health_snapshot/run.ps1](../../../../Use_Cases/platform_health_snapshot/run.ps1)
- Kategorie: `Use Cases`

## Aufgabe der Datei

Skript fuer lokale Entwicklerablaeufe.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/Use_Cases/platform_health_snapshot/setup.ps1.md`  
- Path: `reference/Use_Cases/platform_health_snapshot/setup.ps1.md`  
- Size: 933 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Use_Cases/platform_health_snapshot/setup.ps1`

- Quellpfad: [Use_Cases/platform_health_snapshot/setup.ps1](../../../../Use_Cases/platform_health_snapshot/setup.ps1)
- Kategorie: `Use Cases`

## Aufgabe der Datei

Skript fuer lokale Entwicklerablaeufe.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/Use_Cases/README.md.md`  
- Path: `reference/Use_Cases/README.md.md`  
- Size: 867 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Use_Cases/README.md`

- Quellpfad: [Use_Cases/README.md](../../../Use_Cases/README.md)
- Kategorie: `Use Cases`

## Aufgabe der Datei

Markdown-Datei mit Projektwissen oder Anweisungen.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/Use_Cases/semantic_ticket_triage/flow.json.md`  
- Path: `reference/Use_Cases/semantic_ticket_triage/flow.json.md`  
- Size: 916 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Use_Cases/semantic_ticket_triage/flow.json`

- Quellpfad: [Use_Cases/semantic_ticket_triage/flow.json](../../../../Use_Cases/semantic_ticket_triage/flow.json)
- Kategorie: `Use Cases`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/Use_Cases/semantic_ticket_triage/README.md.md`  
- Path: `reference/Use_Cases/semantic_ticket_triage/README.md.md`  
- Size: 939 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Use_Cases/semantic_ticket_triage/README.md`

- Quellpfad: [Use_Cases/semantic_ticket_triage/README.md](../../../../Use_Cases/semantic_ticket_triage/README.md)
- Kategorie: `Use Cases`

## Aufgabe der Datei

Markdown-Datei mit Projektwissen oder Anweisungen.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/Use_Cases/semantic_ticket_triage/run.ps1.md`  
- Path: `reference/Use_Cases/semantic_ticket_triage/run.ps1.md`  
- Size: 921 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Use_Cases/semantic_ticket_triage/run.ps1`

- Quellpfad: [Use_Cases/semantic_ticket_triage/run.ps1](../../../../Use_Cases/semantic_ticket_triage/run.ps1)
- Kategorie: `Use Cases`

## Aufgabe der Datei

Skript fuer lokale Entwicklerablaeufe.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `reference/Use_Cases/semantic_ticket_triage/setup.ps1.md`  
- Path: `reference/Use_Cases/semantic_ticket_triage/setup.ps1.md`  
- Size: 927 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# `Use_Cases/semantic_ticket_triage/setup.ps1`

- Quellpfad: [Use_Cases/semantic_ticket_triage/setup.ps1](../../../../Use_Cases/semantic_ticket_triage/setup.ps1)
- Kategorie: `Use Cases`

## Aufgabe der Datei

Skript fuer lokale Entwicklerablaeufe.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.
```

## File: `security-and-policy.md`  
- Path: `security-and-policy.md`  
- Size: 1454 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# Security und Policy

NOVA-SYNESIS sichert nicht nur Code, sondern die Absicht eines Graphen. Diese Aufgabe uebernimmt die Semantic Firewall in `src/nova_synesis/security/policy.py`.

## Wann die Policy greift

- bei Agent-Registrierung
- bei `POST /flows/validate`
- bei `POST /flows`
- vor `POST /flows/{flow_id}/run`
- nach einer Planner-Generierung, bevor der Graph an die UI zurueckgeht

## Was geprueft wird

- Graph-Struktur: keine Zyklen, keine Selbstkanten, keine unbekannten Nodes
- Retry-Budget und maximale Graphgroesse
- Expressions und Templates: nur erlaubte Symbole und AST-Knoten
- HTTP-Egress: nur erlaubte Hosts oder Loopback
- Messaging: nur erlaubte Protokolle und kein Endpoint-Override im Payload
- Dateioperationen: kein `allow_outside_workdir`
- Sensitive Memories: kein Abfluss in `http_request` oder externe Nachrichtenziele
- Planner-visible Memories: kein untrusted Ingest ohne explizites Opt-in
- Agent-Registrierung: keine unerlaubten REST/WebSocket-Endpunkte und keine blockierten Capability-Profile

## Bedeutende Felder

- `sensitive = true`
- `planner_visible = false`
- `allow_untrusted_ingest = true`

## Wichtige Settings

- `NS_SECURITY_ENABLED`
- `NS_SECURITY_MAX_NODES`
- `NS_SECURITY_MAX_EDGES`
- `NS_SECURITY_MAX_TOTAL_ATTEMPTS`
- `NS_SECURITY_MAX_EXPRESSION_LENGTH`
- `NS_SECURITY_MAX_EXPRESSION_NODES`
- `NS_SECURITY_HTTP_ALLOWED_HOSTS`
- `NS_SECURITY_SEND_PROTOCOLS`
```

## File: `system-overview.md`  
- Path: `system-overview.md`  
- Size: 1086 Bytes  
- Modified: 2026-04-08 22:11:47 UTC

```markdown
# Systemueberblick

## Schichten

- Domaene: `src/nova_synesis/domain/models.py`
- Planung: `planning/planner.py` und `planning/lit_planner.py`
- Sicherheitspruefung: `security/policy.py`
- Runtime: `runtime/engine.py` und `runtime/handlers.py`
- Persistenz: `persistence/sqlite_repository.py`
- API: `api/app.py`
- UI: `frontend/src/`

## Hauptdatenfluss

1. Graph im Frontend erstellen oder ueber den LiteRT-Planer generieren
2. `toFlowRequest()` erzeugt das Backend-Schema
3. `POST /flows/validate` prueft Graph, Expressions, Egress und Memory-Fluesse
4. `POST /flows` speichert den Graphen
5. `POST /flows/{id}/run` startet die Ausfuehrung
6. `FlowExecutor` verarbeitet den Graphen Node fuer Node
7. `/ws/flows/{flow_id}` uebertraegt Snapshots an die UI
8. `GET /flows/{flow_id}` bleibt die kanonische Wahrheit fuer den Laufzeitstand

## Was dieses System bewusst ist

- graphbasiert statt chatbasiert
- zustandsbehaftet statt nur requestbasiert
- planner-unterstuetzt, aber nicht planner-abhaengig
- sicherheitsgefiltert, bevor Seiteneffekte entstehen
```

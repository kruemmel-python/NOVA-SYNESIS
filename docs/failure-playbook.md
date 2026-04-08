# Failure Playbook

Diese Seite beschreibt die realen Stoerungsbilder des Systems. Ziel ist nicht nur Fehler zu benennen, sondern eine belastbare Reihenfolge fuer Diagnose und Behebung zu geben.

## Triage-Reihenfolge

1. Zuerst unterscheiden: Planner-Problem, Live-Transportproblem oder echte Runtime-Stoerung.
2. Immer den echten Snapshot ueber `GET /flows/{flow_id}` lesen.
3. Erst danach UI, WebSocket oder Planner-Oberflaeche beurteilen.

## 1. Planner liefert ungueltiges JSON

### Woran du es erkennst

- `POST /planner/generate-flow` antwortet mit Fehler
- im Frontend erscheint keine neue Graphstruktur
- typische Backend-Meldungen:
  - `Planner returned invalid JSON`
  - `Planner response does not contain a JSON object`
  - `Planner response contains an incomplete JSON object`

### Was im Code passiert

- `LiteRTPlanner._invoke_model()` ruft die lokale `lit`-Binary auf
- `LiteRTPlanner._parse_model_output()` extrahiert den JSON-Anteil
- `LiteRTPlanner._normalize_flow_request()` validiert das Resultat gegen echte Handler, Ressourcen, Agenten und Memory-Systeme

### Typische Ursachen

- das Modell schreibt Text ausserhalb des JSON
- das JSON ist syntaktisch unvollstaendig
- das Modell erfindet Handler oder Ressourcen
- `max_nodes` ist zu hoch und das Modell driftet
- Binary- oder Modellpfad sind falsch

### Sofortmassnahmen

1. `GET /planner/status` pruefen
2. den Prompt kuerzer und restriktiver formulieren
3. `max_nodes` senken
4. sicherstellen, dass benoetigte Memory-IDs, Agenten und Ressourcen wirklich registriert sind
5. bei wiederholtem Fehler den Flow manuell im Editor bauen

### Dauerhafte Korrektur

- Prompt-Kontrakt in `src/nova_synesis/planning/lit_planner.py` schaerfen
- Normalisierung erweitern, wenn das Modell wiederholt denselben plausiblen, aber falschen Vertrag produziert
- nur echte Handler in den Planner-Katalog aufnehmen

## 2. WebSocket bricht waehrend der Execution ab

### Woran du es erkennst

- die Topbar zeigt `Offline`
- Live-Status friert ein oder aktualisiert sich nur stoerend langsam
- der Flow laeuft im Backend oft trotzdem weiter

### Was das System bereits fuer dich macht

`frontend/src/hooks/useFlowLiveUpdates.ts` faellt automatisch auf Polling gegen `GET /flows/{flow_id}` zurueck. Das bedeutet: Die UI bleibt nutzbar, auch wenn der Socket weg ist.

### Typische Ursachen

- Backend wurde neu gestartet
- Port oder Host in `frontend/.env` stimmen nicht
- Proxy oder Netzwerkumgebung blockieren WebSocket-Upgrades
- der Benutzer ist noch auf einem alten `flow_id`

### Sofortmassnahmen

1. `GET /flows/{flow_id}` direkt pruefen
2. `frontend/.env` gegen die echte Backend-Adresse pruefen
3. unterscheiden: ist nur `/ws/flows/{flow_id}` defekt oder auch REST?
4. wenn REST geht, die Ausfuehrung nicht abbrechen, sondern Snapshot weiter per Polling beobachten

### Dauerhafte Korrektur

- gleiche Host-/Port-Konfiguration fuer REST und WebSocket erzwingen
- bei Reverse Proxy WebSocket-Support explizit konfigurieren
- Polling-Fallback als Sicherheitsnetz beibehalten

## 3. Resource haengt oder laeuft in Timeout / Sattlauf

### Woran du es erkennst

- eine oder mehrere Nodes bleiben lange auf `RUNNING`
- der Flow macht keine sichtbaren Fortschritte, ohne sofort auf `FAILED` zu springen
- einzelne Ressourcen stehen auf `BUSY` oder `DOWN`

### Wichtige technische Besonderheit dieses Projekts

Die Engine ruft `ResourceManager.acquire_many()` ohne globalen Timeout auf. Das heisst:

- ist eine Ressource `DOWN`, scheitert die Reservierung schnell
- ist eine Ressource nur voll ausgelastet, kann eine Task auf Freigabe warten
- handler-spezifische Timeouts, etwa `http_request.timeout_s`, greifen nur innerhalb des Handlers, nicht waehrend der Ressourcenreservierung selbst

### Typische Ursachen

- Resource-Kapazitaet (`metadata.capacity`) ist zu klein fuer die Flow-Konkurrenz
- externe API oder Dateiressource blockiert
- eine vorherige Task haelt die Ressource laenger als erwartet
- der Flow nutzt feste `required_resource_ids`, obwohl eigentlich ein Typ-Fallback sinnvoll waere

### Sofortmassnahmen

1. `GET /flows/{flow_id}` lesen und die auf `RUNNING` stehenden Nodes identifizieren
2. `GET /resources` und gegebenenfalls `resource_health_check` verwenden
3. pruefen, ob `max_concurrency` oder die Ressourcenkapazitaet zu aggressiv eingestellt sind
4. bei HTTP-Aufrufen explizit `timeout_s` setzen
5. wenn moeglich auf `required_resource_types` plus `FALLBACK_RESOURCE` umstellen

### Dauerhafte Korrektur

- Kapazitaet der Ressource realistisch modellieren
- konkurrierende Flows oder Node-Level-Konkurrenz reduzieren
- fuer fragilen Infrastrukturzugriff `RETRY` oder `FALLBACK_RESOURCE` statt `FAIL_FAST` nutzen
- lang laufende Seiteneffekte in kleinere, kontrollierbare Nodes zerlegen

## 4. Flow bleibt auf `RUNNING` stehen

### Woran du es erkennst

- `GET /flows/{flow_id}` zeigt dauerhaft `state = RUNNING`
- dieselben Nodes bleiben ueber mehrere Snapshots hinweg `RUNNING`
- `completed_nodes` waechst nicht mehr

### Was das in diesem System meist bedeutet

Das ist haeufig kein Graph-Deadlock, sondern eine laufende Task, die nie sauber zurueckkehrt:

- Handler wartet auf externen Dienst
- Ressource wartet auf Freigabe
- externer Endpunkt antwortet nie innerhalb eines sinnvollen Timeouts
- die UI hat den letzten erfolgreichen Zustand gezeigt und der Nutzer verwechselt das mit einem eigentlichen Engine-Stall

### Sofortmassnahmen

1. mehrere Snapshots hintereinander vergleichen
2. den oder die `RUNNING`-Nodes identifizieren
3. Handlervertrag des betroffenen Nodes pruefen
4. bei `http_request` ein sinnvolles `timeout_s` setzen
5. pruefen, ob Ressource oder Kommunikationsziel erreichbar sind

### Dauerhafte Korrektur

- fuer externe I/O immer explizite Timeouts und Retries modellieren
- Flows nicht mit ungebremster Parallelitaet gegen knappe Ressourcen fahren
- problematische Langlaeufer erst manuell als Einzel-Flow testen

## 5. Graph-Deadlock oder logisch blockierter Flow

Wichtig: Wenn keine Node mehr startbar ist und trotzdem noch `pending` existiert, setzt `FlowExecutor.run_flow()` den Flow auf `FAILED` und schreibt `deadlock_nodes` in die Metadaten.

### Woran du es erkennst

- `GET /flows/{flow_id}` zeigt `state = FAILED`
- `metadata.deadlock_nodes` ist gesetzt
- `blocked_nodes` enthaelt Knoten, deren Bedingungen nie wahr wurden

### Typische Ursachen

- zyklische Abhaengigkeiten
- alle Kantenbedingungen sind formal ausgewertet, aber keine fuehrt zu einem startbaren Node
- ein Bedingungsausdruck referenziert unbekannte Symbole
- es existiert kein echter Startknoten

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

### Dauerhafte Korrektur

- Graph strikt als DAG modellieren
- Branching nur fuer fachliche Entscheidungen verwenden
- komplexe Vorbedingungen lieber als eigenen vorbereitenden Node modellieren

## 6. Handler wirft Exception

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

### Was die Engine dann macht

- sie erzeugt ein `ErrorEvent`
- je nach `rollback_strategy` folgt:
  - `FAIL_FAST`
  - `RETRY`
  - `COMPENSATE`
  - `FALLBACK_RESOURCE`
- bei `FALLBACK_RESOURCE` versucht `ResourceManager.find_fallback_resources()` einen Ersatz gleicher Art

### Sofortmassnahmen

1. `failed_nodes` im Snapshot lesen
2. Input des Nodes mit dem echten Handlervertrag vergleichen
3. Ressourcen, Agenten und Memory-Systeme pruefen
4. `retry_policy` und `rollback_strategy` auf Infrastrukturrealitaet abstimmen

### Dauerhafte Korrektur

- Handler klein und vertragsscharf halten
- `validator_rules` bewusst einsetzen
- bei externen Diensten eher `RETRY` oder `FALLBACK_RESOURCE` als `FAIL_FAST` verwenden

## Welche Daten du vor tieferer Analyse sammeln solltest

- `flow_id`
- kompletter Snapshot aus `GET /flows/{flow_id}`
- alle aktuell `RUNNING`, `FAILED` und `blocked` Nodes
- Handlername und Input der auffaelligen Node
- verwendete Ressourcen, Agenten und Memory-IDs
- bei Planner-Problemen: Prompt und `max_nodes`

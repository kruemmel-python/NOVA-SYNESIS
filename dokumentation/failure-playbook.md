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
2. zuerst pruefen, ob der Planner bereits eine Warnung zur automatischen JSON-Reparatur oder Prompt-Kompaktierung geliefert hat
3. Prompt kuerzen und restriktiver machen
4. `max_nodes` senken
5. sicherstellen, dass benoetigte Handler, Agenten, Ressourcen und Memory-IDs wirklich registriert sind
6. bei wiederholtem Fehler den Flow manuell im Editor bauen

### Wichtig seit v1.0.5

- formale JSON-Fehler wie Single Quotes, Python-True/None, trailing commas oder fehlende Abschlussklammern werden zuerst automatisch repariert
- LiteRT-Kontextfehler loesen einen automatischen Retry mit kompakterem Prompt aus
- bleibt der Fehler trotzdem bestehen, ist die Antwort meist fachlich unbrauchbar und nicht nur formal kaputt

## 2. Semantic Firewall lehnt den Flow ab

### Woran du es erkennst

- `POST /flows/validate`, `POST /flows` oder `POST /planner/generate-flow` liefert einen Fehler
- typische Fehlermeldungen:
  - `Semantic firewall rejected flow`
  - `Outbound host ... is outside the semantic firewall allowlist`
  - `Flow contains a cycle`
  - `Sensitive memory data may not flow into http_request nodes`
  - `send_message references unknown agent '...'`

### Typische Ursachen

- zyklischer Graph
- `http_request` auf einen nicht erlaubten Host
- `send_message` ohne echtes Kommunikationsziel oder mit Endpoint-Override
- Template oder Condition mit nicht erlaubten Symbolen
- planner-sichtbare Memory-Store-Node hinter untrusted Ingest

### Sofortmassnahmen

1. denselben Payload gegen `POST /flows/validate` schicken
2. `violations` und `warnings` getrennt lesen
3. bei `send_message` pruefen, ob in `GET /agents` mindestens ein Agent mit `communication` registriert ist
4. wenn der Planner einen unbekannten Agentennamen verwendet hat, den Flow neu generieren oder den Node auf einen echten Sink-Agenten umstellen
5. pruefen, ob das Problem fachlich oder rein policy-seitig ist
6. bei legitimen Produktionsfaellen erst Settings oder Memory-/Resource-Metadaten anpassen, nicht die Regel blind entfernen

## 3. Handler ist untrusted, Zertifikat abgelaufen oder Freigabe fehlt

### Woran du es erkennst

- `POST /flows/{flow_id}/run` liefert einen Policy-Fehler
- `POST /flows/validate` meldet Warnungen zu `requires_manual_approval` oder einem untrusted Handler
- `GET /handlers` zeigt `trusted = false` oder ein abgelaufenes Zertifikat

### Typische Ursachen

- Custom Handler wurde ohne Zertifikat registriert
- Handler-Code hat sich geaendert und der Fingerprint passt nicht mehr
- Zertifikat ist abgelaufen
- `requires_manual_approval = true`, aber der Node wurde nicht freigegeben
- `manual_approval.approved = true`, aber `approved_by` fehlt

### Sofortmassnahmen

1. `GET /handlers` lesen und `trust_reason`, Fingerprint und Ablaufdatum pruefen
2. bei gespeichertem Flow den Node ueber `POST /flows/{flow_id}/nodes/{node_id}/approval` freigeben oder im Inspector freigeben
3. bei echten Custom Handlern ein neues Zertifikat ausstellen statt die Policy zu lockern
4. nur wenn fachlich gewollt `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS` verwenden

## 4. WebSocket bricht waehrend der Execution ab

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

## 5. Flow wartet auf menschliche Eingabe und wirkt haengend

### Woran du es erkennst

- die UI zeigt einen Node mit `WAITING_FOR_INPUT`
- der Flow laeuft nicht weiter, obwohl keine technische Exception sichtbar ist
- im Inspector erscheint ein Formular statt einer klassischen Fehlermeldung

### Sofortmassnahmen

1. den wartenden Node anklicken
2. `GET /flows/{flow_id}/nodes/{node_id}/input-request` pruefen
3. benoetigte Eingabe und gegebenenfalls `required_role` lesen
4. ueber den Inspector oder `POST /flows/{flow_id}/nodes/{node_id}/resume` eine Antwort schicken
5. bei `403` die gesendeten Rollenheader pruefen

## 6. Resource haengt oder laeuft in Timeout / Sattlauf

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

## 7. Flow bleibt auf `RUNNING` stehen

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

## 8. Falsche Flow-Version wurde gestartet

### Woran du es erkennst

- der Canvas zeigt eine andere Konfiguration als der gerade gelaufene Snapshot
- ein alter Fehler taucht erneut auf, obwohl der Graph lokal bereits korrigiert wurde
- `GET /flows/{flow_id}` zeigt eine andere `version_id` als erwartet

### Sofortmassnahmen

1. in der Topbar die aktuell geladene Version pruefen
2. `GET /flows/{flow_id}/versions` lesen und die aktive Version mit dem UI-Zustand vergleichen
3. falls noetig die gewuenschte Version aktivieren oder explizit diese Version starten
4. nach einer lokalen Aenderung zuerst `Save Flow` ausfuehren, damit eine neue Version entsteht

## 9. Graph-Deadlock oder logisch blockierter Flow

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

## 10. Handler wirft Exception

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

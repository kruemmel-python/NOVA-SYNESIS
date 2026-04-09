# Platform Health Snapshot

## Ziel

Dieser Use-Case bildet einen einfachen, realen Betriebs-Workflow ab:

1. Die laufende NOVA-SYNESIS-Instanz wird ueber `GET /health` abgefragt.
2. Die Antwort wird in Long-Term Memory gespeichert.
3. Der komplette Health-Status wird als JSON-Datei persistiert.
4. Eine kompakte Text-Zusammenfassung wird erzeugt und ebenfalls geschrieben.

Damit ist der Flow als Startpunkt fuer Operations-, Audit- und Monitoring-Automation geeignet.

## Verwendete Handler

- `http_request`
- `memory_store`
- `json_serialize`
- `template_render`
- `write_file`

## Voraussetzung

Der Backend-Server muss laufen, zum Beispiel:

```powershell
.\run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

## Schnellstart

```powershell
.\Use_Cases\platform_health_snapshot\run.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Optional kann das Setup auch separat ausgefuehrt werden:

```powershell
.\Use_Cases\platform_health_snapshot\setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

`setup.ps1` aktualisiert `ops-long-term` bewusst mit `planner_visible = false`, damit der Flow auch in der Web UI direkt gespeichert und gestartet werden kann, ohne an der Memory-Poisoning-Regel zu scheitern.
Zusaetzlich registriert das Setup einen Message-Queue-Sink `ops-notify`, damit der LLM-Planner fuer Completion-Flows ein legales `send_message`-Ziel hat.

## Ablauf im Graphen

- `fetch_health`: holt `GET /health` von der laufenden Instanz
- `store_health_snapshot`: legt das Resultat in `ops-long-term` ab
- `serialize_health`: formatiert die Antwort als JSON
- `write_health_report`: schreibt `output/latest-health.json`
- `render_health_summary`: erzeugt eine lesbare Kurzfassung
- `persist_summary`: schreibt `output/latest-health-summary.txt`

Fuer planner-generierte Varianten steht ausserdem der Agent `ops-notify` als Kommunikationsziel fuer `send_message` zur Verfuegung.

## Erwartete Artefakte

Nach einem erfolgreichen Lauf existieren:

- `Use_Cases/platform_health_snapshot/output/latest-health.json`
- `Use_Cases/platform_health_snapshot/output/latest-health-summary.txt`

Zusätzlich enthaelt das Long-Term Memory `ops-long-term` unter dem Key `latest-health-snapshot` den letzten Snapshot.

## Typische Anpassungen

- Anderen Backend-Port verwenden: `-ApiBaseUrl` beim Skript anpassen
- Anderen Health-Endpunkt pruefen: URL in `flow.json` aendern
- Mehr Diagnose schreiben: weitere `http_request`, `template_render` oder `write_file` Nodes ergaenzen

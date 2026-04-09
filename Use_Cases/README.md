# Use Cases

Dieser Ordner enthaelt reale, direkt nutzbare NOVA-SYNESIS-Workflows.
Beide Use-Cases laufen gegen das bestehende FastAPI-Backend und verwenden nur reale Endpunkte und Built-in-Handler.

Enthalten sind:

- `accounts_receivable_reminder`: fordert offene Rechnungen aus `data/orders.csv` oder `data/orders.db` an, gruppiert sie pro Kunde und erzeugt Anschreiben
- `platform_health_snapshot`: einfacher Betriebs-Workflow fuer Health-Fetch, Persistenz und Report-Dateien
- `semantic_ticket_triage`: komplexerer Routing-Workflow mit Vector Memory, Branching und Message Queue Dispatch

## Voraussetzungen

- NOVA-SYNESIS laeuft lokal, zum Beispiel auf `http://127.0.0.1:8552`
- PowerShell steht zur Verfuegung

## Ausfuehrung

Jeder Use-Case enthaelt:

- `README.md`: fachliche und technische Erklaerung
- `flow*.json`: vollstaendiger `POST /flows` Request
- `setup.ps1`: registriert die benoetigten Memory-Systeme und Agents idempotent
- `run.ps1`: fuehrt `setup.ps1` aus, erstellt den Flow und startet ihn

Beispiel:

```powershell
.\Use_Cases\accounts_receivable_reminder\run.ps1 -ApiBaseUrl http://127.0.0.1:8552 -Source csv
.\Use_Cases\accounts_receivable_reminder\run.ps1 -ApiBaseUrl http://127.0.0.1:8552 -Source db
.\Use_Cases\platform_health_snapshot\run.ps1 -ApiBaseUrl http://127.0.0.1:8552
.\Use_Cases\semantic_ticket_triage\run.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

## Verwendung in der Web UI

Die `flow.json` Dateien koennen auch in den visuellen Editor importiert werden.
Die Skripte sind trotzdem sinnvoll, weil sie vor dem Lauf die erforderlichen Memory-Systeme und Agents anlegen.

Wichtig:

- `accounts_receivable_reminder` benoetigt keine zusaetzlichen Agents, Resources oder Memory-Systeme. `setup.ps1` prueft nur, ob der laufende Backend-Prozess die erforderlichen Rechnungs-Handler bereits geladen hat. Die eigentlichen Anschreiben werden als `.docx` unter `billing/` geschrieben.
- `accounts_receivable_reminder` enthaelt zusaetzlich `flow.web_ui.*.json` Varianten mit vorbelegten Node-Titeln, Positionen und Kurzbeschreibungen fuer den visuellen Editor.
- `platform_health_snapshot/setup.ps1` setzt `ops-long-term` absichtlich auf `planner_visible = false`, damit der Import nicht an der Memory-Poisoning-Policy scheitert.
- `platform_health_snapshot/setup.ps1` registriert zusaetzlich `ops-notify` als Message-Queue-Sink, damit planner-generierte `send_message`-Nodes ein echtes Ziel haben.
- `semantic_ticket_triage/flow.json` verwendet stabile `target_agent_name` Werte statt lokaler Agent-IDs, damit derselbe Flow nach dem Setup direkt in der Web UI gespeichert und gestartet werden kann.

## Erwartete Ergebnisse

- `accounts_receivable_reminder` schreibt einen Forderungsreport, ein Manifest und je Kunde ein `.docx`-Anschreiben unter `billing/`
- `platform_health_snapshot` schreibt einen JSON-Health-Report und eine Text-Zusammenfassung
- `semantic_ticket_triage` schreibt eine Triage-Zusammenfassung und je nach Branch einen Dispatch-Nachweis

## Hinweise

- Die Skripte sind absichtlich idempotent bei Memory-Systemen und Agents. Wiederholte Aufrufe verwenden vorhandene Objekte, wenn Name oder `memory_id` bereits existieren.
- Jeder Lauf erzeugt einen neuen Flow.
- Die generierten Dateien liegen innerhalb der jeweiligen Use-Case-Ordner unter `output/`.

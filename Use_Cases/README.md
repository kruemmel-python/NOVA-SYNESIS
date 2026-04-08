# Use Cases

Dieser Ordner enthaelt zwei reale, direkt nutzbare NOVA-SYNESIS-Workflows.
Beide Use-Cases laufen gegen das bestehende FastAPI-Backend und verwenden nur reale Endpunkte und Built-in-Handler.

Enthalten sind:

- `platform_health_snapshot`: einfacher Betriebs-Workflow fuer Health-Fetch, Persistenz und Report-Dateien
- `semantic_ticket_triage`: komplexerer Routing-Workflow mit Vector Memory, Branching und Message Queue Dispatch

## Voraussetzungen

- NOVA-SYNESIS laeuft lokal, zum Beispiel auf `http://127.0.0.1:8552`
- PowerShell steht zur Verfuegung

## Ausfuehrung

Jeder Use-Case enthaelt:

- `README.md`: fachliche und technische Erklaerung
- `flow.json`: vollstaendiger `POST /flows` Request
- `setup.ps1`: registriert die benoetigten Memory-Systeme und Agents idempotent
- `run.ps1`: fuehrt `setup.ps1` aus, erstellt den Flow und startet ihn

Beispiel:

```powershell
.\Use_Cases\platform_health_snapshot\run.ps1 -ApiBaseUrl http://127.0.0.1:8552
.\Use_Cases\semantic_ticket_triage\run.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

## Verwendung in der Web UI

Die `flow.json` Dateien koennen auch in den visuellen Editor importiert werden.
Die Skripte sind trotzdem sinnvoll, weil sie vor dem Lauf die erforderlichen Memory-Systeme und Agents anlegen.

## Erwartete Ergebnisse

- `platform_health_snapshot` schreibt einen JSON-Health-Report und eine Text-Zusammenfassung
- `semantic_ticket_triage` schreibt eine Triage-Zusammenfassung und je nach Branch einen Dispatch-Nachweis

## Hinweise

- Die Skripte sind absichtlich idempotent bei Memory-Systemen und Agents. Wiederholte Aufrufe verwenden vorhandene Objekte, wenn Name oder `memory_id` bereits existieren.
- Jeder Lauf erzeugt einen neuen Flow.
- Die generierten Dateien liegen innerhalb der jeweiligen Use-Case-Ordner unter `output/`.

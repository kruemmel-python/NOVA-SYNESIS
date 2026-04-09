# Schnellstart

Diese Datei zeigt den kuerzesten Weg, um NOVA-SYNESIS lokal zu starten und die registrierten Beispiele in der Web-UI zu nutzen.

## 1. Backend starten

```powershell
.\run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

Wichtige URLs:

- `http://127.0.0.1:8552/docs`
- `http://127.0.0.1:8552/health`
- `http://127.0.0.1:8552/planner/status`

## 2. Frontend starten

`frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8552
```

Dann:

```powershell
cd frontend
npm install
npm run dev
```

Die Web-UI laeuft danach normalerweise unter `http://127.0.0.1:5173`.

## 3. Wichtig fuer Use Cases und AI Plan

Die Web-UI sieht nur, was im laufenden Backend bereits registriert ist.

Das bedeutet:

- `setup.ps1`-Skripte muessen gegen das laufende Backend ausgefuehrt werden
- erst danach erscheinen Agenten, Ressourcen und Memory-Systeme im Katalog der Web-UI
- erst danach kann `AI Plan` diese Objekte ueberhaupt verwenden

Wichtig:

- ein Prompt registriert keine neuen Agenten, Ressourcen oder Memory-Systeme
- `AI Plan` plant nur mit den aktuell vorhandenen Katalogobjekten
- wenn etwas nicht registriert ist, kann der Planner es nicht sauber verwenden

Nach einem `setup.ps1`:

1. Web-UI neu laden
2. Sidebar und Planner erneut oeffnen
3. erst dann `AI Plan`, `Import JSON` oder `Run Flow` nutzen

## 4. Use Cases in der Web-UI nutzen

### accounts_receivable_reminder

Setup zuerst ausfuehren:

```powershell
.\Use_Cases\accounts_receivable_reminder\setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Danach in der Web-UI:

1. `Import JSON`
2. bevorzugt `Use_Cases/accounts_receivable_reminder/flow.web_ui.orders_csv.json` oder `Use_Cases/accounts_receivable_reminder/flow.web_ui.orders_db.json` laden
3. `Save Flow`
4. `Run Flow`

Ergebnis:

- Reports unter `Use_Cases/accounts_receivable_reminder/output/...`
- Serienanschreiben als `.docx` unter `billing/csv` oder `billing/db`

Alternativ direkt per Skript:

```powershell
.\Use_Cases\accounts_receivable_reminder\run.ps1 -ApiBaseUrl http://127.0.0.1:8552 -Source csv
.\Use_Cases\accounts_receivable_reminder\run.ps1 -ApiBaseUrl http://127.0.0.1:8552 -Source db
```

### platform_health_snapshot

Setup zuerst ausfuehren:

```powershell
.\Use_Cases\platform_health_snapshot\setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Danach in der Web-UI:

1. `Import JSON`
2. Datei `Use_Cases/platform_health_snapshot/flow.json` laden
3. `Save Flow`
4. `Run Flow`

Alternativ direkt per Skript:

```powershell
.\Use_Cases\platform_health_snapshot\run.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

### semantic_ticket_triage

Setup zuerst ausfuehren:

```powershell
.\Use_Cases\semantic_ticket_triage\setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Danach in der Web-UI:

1. `Import JSON`
2. Datei `Use_Cases/semantic_ticket_triage/flow.json` laden
3. `Save Flow`
4. `Run Flow`

Alternativ direkt per Skript:

```powershell
.\Use_Cases\semantic_ticket_triage\run.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

## 5. LLM_Planer Beispiele nutzen

Der Ordner `Use_Cases/LLM_Planer` enthaelt nur getestete Prompts.

Zuerst das Katalog-Setup ausfuehren:

```powershell
.\Use_Cases\LLM_Planer\setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Dieses Skript registriert die fuer die Planner-Beispiele benoetigten Objekte im laufenden Backend:

- API-Resource `http://127.0.0.1:8552/health`
- Memory-System `llm-planner-notes`
- Queue-Agent `llm-planner-notify`

Danach gibt es zwei Wege:

### In der Web-UI

1. Seite neu laden
2. `AI Plan` oeffnen
3. den Inhalt einer Prompt-Datei aus `Use_Cases/LLM_Planer` einfuellen
4. `Generate Graph`
5. `Save Flow`
6. `Run Flow`

Verwendbare Prompt-Dateien:

- `Use_Cases/LLM_Planer/prompt_01_smoke_message.txt`
- `Use_Cases/LLM_Planer/prompt_03_memory_roundtrip.txt`
- `Use_Cases/LLM_Planer/prompt_04_resource_notify.txt`
- `Use_Cases/LLM_Planer/prompt_05_accounts_receivable_csv.txt`
- `Use_Cases/LLM_Planer/prompt_06_accounts_receivable_db.txt`

### Per Verifikationsskript

```powershell
.\Use_Cases\LLM_Planer\verify.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Das Skript:

- fuehrt bei Bedarf das Setup aus
- sendet die Prompts an `/planner/generate-flow`
- speichert die Flows
- startet die Ausfuehrung
- prueft die Ergebnisse

## 6. Die wichtigste Regel fuer AI Plan

`AI Plan` arbeitet nur mit dem aktuellen Planner-Katalog des laufenden Backends.

Also:

- ohne `setup.ps1` keine neuen Agenten
- ohne `setup.ps1` keine neuen Ressourcen
- ohne `setup.ps1` keine neuen Memory-Systeme
- ohne diese Registrierungen kann der Planner nur mit dem arbeiten, was bereits vorhanden ist

Wenn ein Prompt einen Agenten, eine Resource oder ein Memory nennt, das nicht registriert ist, wird der Planner entweder fehlschlagen, den Node weglassen oder die Semantic Firewall blockiert den Flow.

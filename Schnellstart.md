# Schnellstart

Diese Datei zeigt den kuerzesten Weg, um NOVA-SYNESIS lokal zu starten und die registrierten Beispiele in der Web-UI zu nutzen.

## 1. Backend starten

```powershell
.\run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

Alternativ kannst du das LiteRT-Modell direkt beim Start wechseln:

```powershell
.\run-backend.ps1 -BindHost 127.0.0.1 -Port 8552 -LitModel gemma-4-E2B-it.litertlm
.\run-backend.ps1 -BindHost 127.0.0.1 -Port 8552 -LitModel model_multimodal.litertlm
```

Wenn nur ein Dateiname angegeben wird, sucht NOVA-SYNESIS automatisch im Ordner `LIT/`.

Wenn nach einem Modellwechsel eine LiteRT-Meldung wie `failed to create engine` erscheint, versucht NOVA-SYNESIS automatisch, den modellbezogenen XNNPACK-Cache zu quarantainen und den Start zu wiederholen. Wenn der Fehler bleibt, ist das Modell wahrscheinlich nicht mit der aktuellen `lit`-Binary oder dem gewaehlten Backend kompatibel.

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

## 3. Was sich seit den Enterprise-Phasen geaendert hat

- `Save Flow` ueberschreibt einen bestehenden Flow nicht mehr still, sondern schreibt bei vorhandener `Flow ID` eine neue Flow-Version
- die Topbar zeigt die aktuell geladene Version und erlaubt das Laden aelterer Versionen
- `Analytics` oeffnet eine kompakte Betreiberansicht auf Handler- und Flow-Metriken
- ein Node kann waehrend der Ausfuehrung auf `WAITING_FOR_INPUT` gehen; dann erscheint im Inspector ein Eingabeformular statt eines Fehlers
- `Run Flow` startet die aktuell geladene Version, nicht zwingend immer nur den zuletzt sichtbaren Containerzustand

## 4. Human in the Loop in der Web-UI

Wenn ein Flow absichtlich auf menschliche Eingabe wartet:

1. den wartenden Node anklicken
2. im Inspector den Bereich fuer die offene Eingabe lesen
3. die angeforderten Felder oder den JSON-Fallback ausfuellen
4. `Submitted by` setzen
5. `Submit Input` klicken

Wichtig:

- `WAITING_FOR_INPUT` ist kein Absturz, sondern ein kontrollierter Runtime-Stopp
- wenn der Node eine Rolle verlangt, zeigt der Inspector diese als Hinweis an
- die eigentliche Rollenpruefung passiert serverseitig

## 5. Optional: Identity-Header fuer Rollenpfade

Wenn Freigaben oder HITL-Resumes ueber Rollen abgesichert werden sollen, sendet die API standardmaessig diese Header:

- `X-NOVA-User`
- `X-NOVA-Roles`

Beispiel fuer einen direkten API-Aufruf:

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8552/metrics/summary" `
  -Headers @{
    "X-NOVA-User" = "operator@example.local"
    "X-NOVA-Roles" = "approver,ops"
  }
```

## 6. Wichtig fuer Use Cases und AI Plan

Die Web-UI sieht nur, was im laufenden Backend bereits registriert ist.

Das bedeutet:

- `setup.ps1`-Skripte muessen gegen das laufende Backend ausgefuehrt werden
- erst danach erscheinen Agenten, Ressourcen und Memory-Systeme im Katalog der Web-UI
- erst danach kann `AI Plan` diese Objekte ueberhaupt verwenden

Wichtig:

- `AI Plan` bootstrappt inzwischen automatisch einen generischen System-Agenten sowie die Scratch-Memories `planner-scratch` und `planner-vector`, wenn sie noch fehlen
- Ressourcen werden weiterhin nicht aus freiem Text erraten oder extern freigeschaltet
- spezialisierte Use-Case-Objekte aus `setup.ps1` bleiben wichtig, wenn ein Prompt ganz bestimmte Agenten, Ressourcen oder Memory-IDs nutzen soll

Nach einem `setup.ps1`:

1. Web-UI neu laden
2. Sidebar und Planner erneut oeffnen
3. erst dann `AI Plan`, `Import JSON` oder `Run Flow` nutzen

## 7. Use Cases in der Web-UI nutzen

### accounts_receivable_reminder

Setup zuerst ausfuehren:

```powershell
.\Use_Cases\accounts_receivable_reminder\setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Danach in der Web-UI:

1. `Import JSON`
2. bevorzugt `Use_Cases/accounts_receivable_reminder/flow.web_ui.orders_csv.json` oder `Use_Cases/accounts_receivable_reminder/flow.web_ui.orders_db.json` laden
3. Node `Generate Reminder Letters` anklicken
4. optional `Use local LLM to draft the letter text` aktivieren
5. bei Bedarf `Preview Draft` nutzen, `Business instruction` und `Prompt template` anpassen
6. `Save Flow`
7. `Run Flow`

Ergebnis:

- Reports unter `Use_Cases/accounts_receivable_reminder/output/...`
- Serienanschreiben als `.docx` unter `billing/csv` oder `billing/db`

Wenn der LLM-Schreibmodus aktiv ist:

- entscheidet der Benutzer im Inspector selbst, wie das lokale Modell schreiben soll
- `Preview Draft` erzeugt einen einzelnen Beispielbrief fuer einen Kunden, ohne den ganzen Flow zu starten
- `Preview Draft` verwendet die gerade im Inspector sichtbaren Werte, auch wenn der Flow noch nicht gespeichert wurde
- beim spaeteren `Run Flow` wird derselbe konfigurierte Prompt fuer jeden Kunden aus `orders.csv` oder `orders.db` erneut ausgefuehrt
- wenn die Vorschau zu lange braucht, beendet die UI den Request automatisch und zeigt einen Fehler statt endlos weiterzulaufen

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

## 8. LLM_Planer Beispiele nutzen

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

## 9. Die wichtigste Regel fuer AI Plan

`AI Plan` arbeitet nur mit dem aktuellen Planner-Katalog des laufenden Backends.

Also:

- ohne `setup.ps1` keine spezialisierten Agenten oder Ressourcen fuer deinen konkreten Fachfall
- das Backend erzeugt fuer freie Prompts zwar automatisch `nova-system-agent`, `planner-scratch` und `planner-vector`
- ohne weitere Registrierungen kann der Planner aber trotzdem nur mit den vorhandenen Built-in-Handlern und diesen generischen Bootstrap-Objekten arbeiten

Wenn ein Prompt einen Agenten, eine Resource oder ein Memory nennt, das nicht registriert ist, wird der Planner entweder fehlschlagen, den Node weglassen oder die Semantic Firewall blockiert den Flow.

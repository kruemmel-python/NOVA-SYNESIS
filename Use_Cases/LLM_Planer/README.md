# LLM Planer

Dieser Ordner enthaelt nur Planner-Prompts, die gegen das laufende Backend auf `http://127.0.0.1:8552` erfolgreich getestet wurden.

Getestet wurde immer end-to-end:

1. `POST /planner/generate-flow`
2. `POST /flows`
3. `POST /flows/{flow_id}/run`
4. Pruefung auf `state = COMPLETED`
5. Pruefung des erzeugten Artefakts im Ordner `Use_Cases/LLM_Planer/output`

## Wichtiger Kontext

Die ersten beiden Prompts funktionieren sogar dann, wenn der Live-Katalog leer ist fuer:

- Agenten
- Ressourcen
- Memory-Systeme

Darum arbeiten die ersten beiden Prompts ausschliesslich mit lokal ausfuehrbaren Built-in-Handlern.

Zusaetzlich bootstrappt der Backend-Planner inzwischen bei freien Prompts automatisch:

- den generischen Agenten `nova-system-agent`
- das Long-Term-Memory `planner-scratch`
- das Vector-Memory `planner-vector`

Damit koennen freie Prompts robuster mit `send_message`, `memory_store` und `memory_search` geplant werden, selbst wenn vorher noch kein eigener Fachkatalog registriert wurde.

Zusaetzlich gibt es jetzt zwei Prompts mit echten Katalogobjekten:

- ein Prompt mit `memory_store` und `memory_retrieve`
- ein Prompt mit `resource_health_check` und `send_message`
- zwei Prompts fuer den Forderungsprozess mit `accounts_receivable_*`, `json_serialize` und `write_file`

Dafuer muss vorher das lokale Setup ausgefuehrt werden:

```powershell
.\Use_Cases\LLM_Planer\setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

## Warum freie Web-Prompts trotzdem Grenzen haben

Prompts mit `http_request` oder allgemeiner Web-Recherche sind deutlich fragiler, weil sie gleichzeitig von

- Host-Allowlist
- API-Ressourcen
- Planner-URL-Auswahl
- Memory-Poisoning-Regeln

abhaengen.

Nicht enthalten sind deshalb absichtlich keine Prompts mit:

- `http_request`
- `memory_store`
- `memory_retrieve`
- `memory_search`
- `send_message`

Solche Prompts koennen erst dann stabil funktionieren, wenn das Backend vorher passende API-Ressourcen registriert hat oder wenn der Planner auf dafuer vorhandene Built-ins wie `news_search`, `topic_split` und `write_csv` ausweichen kann.

Die beiden Forderungs-Prompts sind davon ausgenommen, weil sie ausschliesslich mit lokalen Built-in-Handlern und Projektdateien arbeiten.

## Enthaltene Prompts

1. [prompt_01_smoke_message.txt](prompt_01_smoke_message.txt)
   Ergebnis: schreibt eine verifizierte Smoke-Test-Nachricht nach `output/prompt1.txt`

2. [prompt_03_memory_roundtrip.txt](prompt_03_memory_roundtrip.txt)
   Ergebnis: nutzt das echte Memory-System `llm-planner-notes` und schreibt einen verifizierten Memory-Flow

3. [prompt_04_resource_notify.txt](prompt_04_resource_notify.txt)
   Ergebnis: nutzt die echte API-Resource `http://127.0.0.1:8552/health` und den Queue-Agenten `llm-planner-notify`

4. [prompt_05_accounts_receivable_csv.txt](prompt_05_accounts_receivable_csv.txt)
   Ergebnis: plant den Forderungsprozess fuer `data/orders.csv` und erzeugt `.docx`-Anschreiben unter `billing/csv`

5. [prompt_06_accounts_receivable_db.txt](prompt_06_accounts_receivable_db.txt)
   Ergebnis: plant den Forderungsprozess fuer `data/orders.db` und erzeugt `.docx`-Anschreiben unter `billing/db`

## Erneut verifizieren

```powershell
.\Use_Cases\LLM_Planer\verify.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

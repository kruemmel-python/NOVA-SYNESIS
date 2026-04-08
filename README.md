# NOVA-SYNESIS

Neural Orchestration Visual Autonomy  
Stateful Yielding Node-based Execution Semantic Integrated Surface

Dieses Repository implementiert das in [uml_V3.mmd](/d:/Agenten_UML/uml_V3.mmd) definierte Orchestrierungs-System als produktionsreife NOVA-SYNESIS-Plattform fuer autonome, visuelle und zustandsbehaftete Agenten-Workflows.

Enthalten sind:

- Agentenmodell mit Capabilities, Kommunikationsadaptern und Memory-Referenzen
- Intent-zu-Task-Planung
- Task- und Execution-Layer mit Retry, Rollback und Error Events
- Ressourcenverwaltung mit Health Checks und Fallback-Auswahl
- Flow-Graph-Ausführung mit Bedingungen, Parallelisierung und Beobachtbarkeit
- Persistenz über SQLite
- FastAPI-Service und CLI
- Automatisierte Tests

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## API starten

```bash
nova-synesis run-api --host 127.0.0.1 --port 8000
```

Der bisherige CLI-Name `agent-orchestrator` bleibt als Kompatibilitaetsalias erhalten, die offizielle Bezeichnung ist aber `nova-synesis`.

Wenn das Konsolenskript noch nicht per `pip install -e .` installiert wurde, funktioniert der repo-lokale Start direkt so:

```powershell
.\run-backend.ps1 -BindHost 127.0.0.1 -Port 8000
```

oder ohne PowerShell-Skript:

```powershell
$env:PYTHONPATH="src"
python -m nova_synesis.cli run-api --host 127.0.0.1 --port 8000
```

## Web UI starten

Das Frontend liegt in [frontend](d:/Agenten_UML/frontend) und nutzt ausschließlich die bestehende FastAPI-API.

```bash
cd frontend
npm install
npm run dev
```

Standardmäßig erwartet die UI das Backend unter `http://127.0.0.1:8000`.
Abweichende Ziele werden über `frontend/.env` mit `VITE_API_BASE_URL=...` konfiguriert.

## Live-Updates

Die UI verwendet den WebSocket-Endpunkt `/ws/flows/{flow_id}` für Laufzeit-Updates.
Node-Status werden live aus der Backend-Runtime gestreamt und farblich markiert:

- `PENDING`: grau
- `RUNNING`: blau
- `SUCCESS`: grün
- `FAILED`: rot

## Use Cases

Reale, direkt startbare Beispiel-Workflows liegen in [Use_Cases](d:/Agenten_UML/Use_Cases).
Dort sind zwei lauffaehige Beispiele mit Dokumentation, `flow.json` und PowerShell-Skripten fuer Setup und Ausfuehrung enthalten.

## LLM Planner

Der visuelle Editor kann Graphen durch das lokale LiteRT-LM-Modell in [LIT](d:/Agenten_UML/LIT) erzeugen.
Verwendet werden:

- Binary: `LIT/lit.windows_x86_64.exe`
- Modell: `LIT/gemma-4-E2B-it.litertlm`

Relevante Endpunkte:

- `GET /planner/status`
- `POST /planner/generate-flow`

Die UI ruft den Planner über den Button `AI Plan` auf und ersetzt den Canvas mit dem generierten `FlowRequest`.
Der Planner erzeugt ausschließlich Graphen gegen die real registrierten Handler, Agents, Resources und Memory-Backends.

## Semantic Firewall

Vor Flow-Erstellung, LLM-Planung und Ausführung prüft eine semantische Policy-Schicht den Graphen.
Sie blockiert unter anderem:

- zyklische oder übermäßig aggressive Retry-Topologien
- externe `http_request` Ziele außerhalb der Host-Allowlist
- `send_message` ohne explizites `target_agent_id` oder mit Endpoint-Override
- Expressions mit nicht erlaubten Symbolen oder verdächtigen Token-Sequenzen
- Exfiltration aus als `sensitive` markierten Memory-Systemen
- untrusted Ingest in planner-sichtbare Memories ohne explizites Opt-in

Relevanter API-Endpunkt:

- `POST /flows/validate`

## Branding

`NOVA-SYNESIS` steht in diesem Projekt für:

- `N` Neural
- `O` Orchestration
- `V` Visual
- `A` Autonomous
- `S` Stateful
- `Y` Yielding
- `N` Node-based
- `E` Execution
- `S` Semantic
- `I` Integrated
- `S` Surface

## Kernkonzepte

- `Agent`: verarbeitet Kontext, trifft Ausführungsentscheidungen und kommuniziert über REST, WebSocket oder Message Queue.
- `Task` und `TaskExecution`: trennen fachlichen Auftrag von Laufzeitversuch, Fehlern und Rollback.
- `Resource`: modelliert APIs, Modelle, Datenbanken, Dateien oder GPU-Kapazitäten.
- `MemorySystem`: stellt Short-Term-, Long-Term- und Vector-Memory bereit.
- `ExecutionFlow`: führt einen gerichteten Graphen mit Bedingungen und Parallelisierung aus.
- `IntentPlanner`: übersetzt strukturierte Intents deterministisch in Flows und Tasks.

## Strukturierter Intent

Der produktive Pfad für die Planung nutzt strukturierte Constraints:

```json
{
  "goal": "Data ingestion workflow",
  "constraints": {
    "tasks": [
      {
        "node_id": "fetch",
        "handler_name": "http_request",
        "input": {
          "url": "https://example.org/api/items",
          "method": "GET"
        },
        "required_capabilities": ["http"],
        "required_resource_types": ["API"]
      },
      {
        "node_id": "store",
        "handler_name": "memory_store",
        "input": {
          "memory_id": "long-term",
          "key": "latest-items",
          "value": "{{ results.fetch.body }}"
        },
        "dependencies": ["fetch"],
        "conditions": {
          "fetch": "results['fetch']['status_code'] == 200"
        }
      }
    ]
  }
}
```

## Tests

```bash
pytest
```

## Frontend Build

```bash
cd frontend
npm run build
```

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

Fuer den schnellsten operativen Einstieg siehe auch [Schnellstart.md](/d:/Agenten_UML/Schnellstart.md).
Die gepflegte Markdown-Dokumentation liegt unter [dokumentation/README.md](/d:/Agenten_UML/dokumentation/README.md), die statische HTML-Doku unter [docs/index.html](/d:/Agenten_UML/docs/index.html).
Die verdichtete architektonische Einordnung findest du in [fazit.md](/d:/Agenten_UML/fazit.md), der ausfuehrliche Fachartikel liegt in [Fachartikel_NOVA-SYNESIS.md](/d:/Agenten_UML/Fachartikel_NOVA-SYNESIS.md).

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
Seit `1.0.5` kompaktisiert der Planner LiteRT-Prompts bei Token-Overflow automatisch und repariert typische LLM-JSON-Formfehler vor der Normalisierung.

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

## Handler Trust und manuelle Freigabe

Handler werden in NOVA-SYNESIS nicht nur namentlich registriert, sondern kryptographisch als vertrauenswuerdig markiert. Die Runtime erzeugt fuer Built-in-Handler automatisch digitale Zertifikate auf Basis eines signierten Handler-Fingerprints. Eigene Handler koennen beim Registrieren mit einem Zertifikat eingebracht oder spaeter ueber die Service-Schicht signiert werden.

Wichtige Regeln:

- `GET /handlers` liefert nicht nur Handlernamen, sondern auch Trust-Metadaten, Zertifikatsinformationen und den aktuellen Fingerprint.
- Der LiteRT-Planer sieht nur trusted Handler im Planner-Katalog.
- Wenn `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS=true` aktiv ist, blockiert die Semantic Firewall untrusted Handler spaetestens beim Run.
- Wenn `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS=true` gesetzt ist, kann ein Node im InspectorPanel explizit fuer die Ausfuehrung freigegeben werden.

Relevante Endpunkte:

- `GET /handlers`
- `POST /flows/{flow_id}/nodes/{node_id}/approval`
- `DELETE /flows/{flow_id}/nodes/{node_id}/approval`

Relevante Settings:

- `NS_HANDLER_CERTIFICATE_SECRET`
- `NS_HANDLER_CERTIFICATE_ISSUER`
- `NS_HANDLER_CERTIFICATE_TTL_HOURS`
- `NS_SECURITY_AUTO_ISSUE_BUILTIN_HANDLER_CERTIFICATES`
- `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS`
- `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS`

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

## HTML-Dokumentation

Aus dem Ordner `dokumentation` kann eine statische HTML-Dokumentationsseite mit Side-Menue, Suche und Source-Ansichten erzeugt werden:

```bash
python tools/build_web_docs.py
```

Danach liegt die fertige Seite unter `docs/index.html`.

from __future__ import annotations

import ast
import os
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
REF = DOCS / 'reference'

EXCLUDED = {
    '.git',
    'docs',
    'web',
    'data',
    'debug_tmp',
    'planner_live_check',
    'planner_live_check2',
    'release',
    'ws_debug',
    '.pytest_cache',
    '__pycache__',
    'frontend/node_modules',
    'frontend/dist',
}

FILE_NOTES = {
    '.env.example': {
        'purpose': 'Beispielkonfiguration fuer Backend, Planner, CORS und die semantische Sicherheitsrichtlinie.',
        'edit': 'Wenn neue Umgebungsvariablen eingefuehrt, Security-Grenzen angepasst oder Standardwerte kommuniziert werden muessen.',
        'related': ['src/nova_synesis/config.py', 'README.md'],
    },
    'Anweisung.md': {
        'purpose': 'Fachliche Ursprungsspezifikation des Systems.',
        'edit': 'Wenn Anforderungen nachgezogen oder gegen die Implementierung gespiegelt werden.',
        'related': ['uml_V3.mmd', 'README.md'],
    },
    'Dockerfile': {
        'purpose': 'Container-Build fuer das Python-Backend.',
        'edit': 'Wenn Build, Startkommando oder Image-Basis angepasst werden muessen.',
        'related': ['pyproject.toml', 'src/nova_synesis/cli.py'],
    },
    'pyproject.toml': {
        'purpose': 'Python-Paketdefinition mit Abhaengigkeiten, CLI und Testkonfiguration.',
        'edit': 'Wenn Python-Abhaengigkeiten, Packaging oder Skripte geaendert werden.',
        'related': ['src/nova_synesis/cli.py', 'tests/test_orchestrator.py'],
    },
    'README.md': {
        'purpose': 'Projektweiter Schnellstart fuer Backend, Frontend und Planner.',
        'edit': 'Wenn sich Startablauf oder Hauptfunktionen fuer Entwickler aendern.',
        'related': ['docs/README.md', 'run-backend.ps1', 'frontend/package.json'],
    },
    'run-backend.ps1': {
        'purpose': 'Empfohlenes Windows-Startskript fuer das Backend.',
        'edit': 'Wenn der lokale Backend-Start fuer Entwickler angepasst werden soll.',
        'related': ['src/nova_synesis/cli.py', 'run-backend.cmd'],
    },
    'uml_V3.mmd': {
        'purpose': 'Mermaid-Quelle des Architekturdiagramms.',
        'edit': 'Wenn die dokumentierte Zielarchitektur angepasst werden soll.',
        'related': ['uml.html', 'Anweisung.md'],
    },
    'LIT/README.md': {
        'purpose': 'Hinweise zur lokalen LiteRT-LM-Laufzeit und zu Modelldateien.',
        'edit': 'Wenn Binary- oder Modellsetup aktualisiert wird.',
        'related': ['src/nova_synesis/planning/lit_planner.py', '.env.example'],
    },
    'LIT/lit.windows_x86_64.exe': {
        'purpose': 'Windows-Binary fuer die lokale LiteRT-LM-Inferenz.',
        'edit': 'Nur beim gezielten Update der lokalen Runtime.',
        'related': ['LIT/gemma-4-E2B-it.litertlm', 'src/nova_synesis/planning/lit_planner.py'],
    },
    'LIT/gemma-4-E2B-it.litertlm': {
        'purpose': 'Lokales Modell fuer den autonomen Flow-Planer.',
        'edit': 'Nur wenn ein anderes Planner-Modell eingesetzt wird.',
        'related': ['LIT/lit.windows_x86_64.exe', 'src/nova_synesis/planning/lit_planner.py'],
    },
    'src/nova_synesis/api/app.py': {
        'purpose': 'FastAPI- und WebSocket-Schicht des Backends inklusive Request-Modelle, Flow-Validierung und Live-Streaming.',
        'edit': 'Wenn API-Endpunkte, Schemafelder, Sicherheitspruefung oder Live-Streaming erweitert werden.',
        'related': ['src/nova_synesis/services/orchestrator.py', 'frontend/src/lib/apiClient.ts', 'frontend/src/types/api.ts'],
    },
    'src/nova_synesis/cli.py': {
        'purpose': 'CLI-Einstiegspunkt fuer API-Start, Flow-Ausfuehrung und lokale Hilfsaufgaben.',
        'edit': 'Wenn neue CLI-Kommandos oder Startoptionen hinzukommen.',
        'related': ['run-backend.ps1', 'pyproject.toml'],
    },
    'src/nova_synesis/config.py': {
        'purpose': 'Zentrale Laufzeitkonfiguration des Backends inklusive LiteRT- und Semantic-Firewall-Settings.',
        'edit': 'Wenn neue Settings, Standardpfade, Planner-Optionen oder Policy-Grenzen benoetigt werden.',
        'related': ['.env.example', 'src/nova_synesis/cli.py'],
    },
    'src/nova_synesis/domain/models.py': {
        'purpose': 'Kern-Domaenenmodell mit Agenten, Ressourcen, Tasks, Bedingungen und ExecutionFlow.',
        'edit': 'Wenn das fachliche Laufzeitmodell des Systems veraendert wird.',
        'related': ['src/nova_synesis/runtime/engine.py', 'src/nova_synesis/services/orchestrator.py'],
    },
    'src/nova_synesis/memory/systems.py': {
        'purpose': 'Implementierungen fuer Kurzzeit-, Langzeit- und Vektor-Speicher.',
        'edit': 'Wenn Speicherverhalten, Suche oder Persistenz geaendert werden.',
        'related': ['src/nova_synesis/runtime/handlers.py', 'src/nova_synesis/services/orchestrator.py'],
    },
    'src/nova_synesis/persistence/sqlite_repository.py': {
        'purpose': 'SQLite-Persistenzschicht fuer Flows, Ausfuehrungen und Katalogobjekte.',
        'edit': 'Wenn Datenbankstruktur oder gespeicherte Felder angepasst werden.',
        'related': ['src/nova_synesis/services/orchestrator.py'],
    },
    'src/nova_synesis/planning/planner.py': {
        'purpose': 'Regelbasierter Intent-zu-Task-Planer.',
        'edit': 'Wenn strukturierte Intents anders in Tasks zerlegt werden sollen.',
        'related': ['src/nova_synesis/domain/models.py', 'src/nova_synesis/services/orchestrator.py'],
    },
    'src/nova_synesis/planning/lit_planner.py': {
        'purpose': 'Lokaler LLM-Planer ueber LiteRT-LM inklusive Prompting, Parsing, Katalognutzung und Graph-Normalisierung.',
        'edit': 'Wenn Planner-Qualitaet, Modellaufruf, Katalogfilterung oder Vorvalidierung verbessert werden soll.',
        'related': ['LIT/lit.windows_x86_64.exe', 'LIT/gemma-4-E2B-it.litertlm', 'frontend/src/components/layout/PlannerComposer.tsx'],
    },
    'src/nova_synesis/security/__init__.py': {
        'purpose': 'Paketexporte fuer die semantische Sicherheitspruefung.',
        'edit': 'Wenn Security-Klassen neu exportiert oder das Security-Paket umstrukturiert werden soll.',
        'related': ['src/nova_synesis/security/policy.py', 'src/nova_synesis/services/orchestrator.py'],
    },
    'src/nova_synesis/security/trust.py': {
        'purpose': 'Digitale Handler-Zertifikate, Fingerprints und Trust-Validierung fuer Runtime-Handler.',
        'edit': 'Wenn Handler-Zertifikate, Fingerprinting oder der Signaturmechanismus angepasst werden muessen.',
        'related': ['src/nova_synesis/runtime/handlers.py', 'src/nova_synesis/config.py', 'src/nova_synesis/services/orchestrator.py'],
    },
    'src/nova_synesis/security/policy.py': {
        'purpose': 'Semantische Firewall fuer Flow- und Agent-Validierung vor Planung, Speicherung und Ausfuehrung.',
        'edit': 'Wenn Sicherheitsregeln, Allowlists oder die Graph-Absichtspruefung veraendert werden muessen.',
        'related': ['src/nova_synesis/services/orchestrator.py', 'src/nova_synesis/config.py', 'tests/test_orchestrator.py'],
    },
    'src/nova_synesis/resources/manager.py': {
        'purpose': 'Verwaltung und Aufloesung registrierter Ressourcen.',
        'edit': 'Wenn Ressourcenallokation oder Fallbacks angepasst werden.',
        'related': ['src/nova_synesis/runtime/engine.py'],
    },
    'src/nova_synesis/runtime/engine.py': {
        'purpose': 'Graph-Ausfuehrungsengine fuer Task- und Flow-Lifecycle inklusive Template-Aufloesung und Live-Snapshots.',
        'edit': 'Wenn Ablaufsteuerung, Parallelitaet, Template-Kontext oder Snapshot-Logik geaendert wird.',
        'related': ['src/nova_synesis/domain/models.py', 'src/nova_synesis/runtime/handlers.py'],
    },
    'src/nova_synesis/runtime/handlers.py': {
        'purpose': 'Eingebaute Handler fuer HTTP, Memory, Messaging, Dateien und Serialisierung.',
        'edit': 'Wenn neue Arbeitsbausteine hinzugefuegt oder bestehende Handler verbessert werden.',
        'related': ['src/nova_synesis/runtime/engine.py', 'frontend/src/components/layout/Sidebar.tsx'],
    },
    'src/nova_synesis/services/orchestrator.py': {
        'purpose': 'Zentrale Service-Fassade des Backends inklusive Security-Gates, Planner-Katalog und Lifecycle-Management.',
        'edit': 'Wenn Systemkomposition, Registrierungen, Policy-Durchsetzung oder Lifecycle-Management geaendert werden.',
        'related': ['src/nova_synesis/api/app.py', 'src/nova_synesis/runtime/engine.py'],
    },
    'tests/test_orchestrator.py': {
        'purpose': 'Regressionstests fuer Backend, Planner, WebSocket-Livebetrieb und Semantic-Firewall.',
        'edit': 'Wenn neue Features abgesichert, Sicherheitsregeln erweitert oder Fehler reproduzierbar getestet werden.',
        'related': ['src/nova_synesis/services/orchestrator.py', 'src/nova_synesis/api/app.py'],
    },
    'frontend/src/App.tsx': {
        'purpose': 'Root-Komponente der UI mit Layout, Planner, Save/Run und Live-Sync.',
        'edit': 'Wenn globale Frontend-Aktionen oder das Seitenlayout geaendert werden.',
        'related': ['frontend/src/store/useFlowStore.ts', 'frontend/src/components/layout/TopBar.tsx'],
    },
    'frontend/src/types/api.ts': {
        'purpose': 'Gemeinsame TypeScript-Schemata fuer API, Snapshots und Editorgraph.',
        'edit': 'Wenn Backend-Vertraege oder UI-Datentypen erweitert werden.',
        'related': ['src/nova_synesis/api/app.py', 'frontend/src/lib/flowSerialization.ts'],
    },
    'frontend/src/lib/apiClient.ts': {
        'purpose': 'Echter API-Client fuer REST, Flow-Validierung, Planner und WebSocket-Basis-URLs.',
        'edit': 'Wenn neue Backend-Endpunkte im Frontend angebunden werden.',
        'related': ['src/nova_synesis/api/app.py', 'frontend/src/types/api.ts'],
    },
    'frontend/src/lib/flowSerialization.ts': {
        'purpose': 'Uebersetzung zwischen React-Flow und echtem Backend-Flow-Schema.',
        'edit': 'Wenn Node-Felder oder Flow-Schema geaendert werden.',
        'related': ['frontend/src/types/api.ts', 'src/nova_synesis/api/app.py'],
    },
    'frontend/src/store/useFlowStore.ts': {
        'purpose': 'Zustand-Store fuer Graph, Auswahl, Undo/Redo und Laufzeitstatus.',
        'edit': 'Wenn Editorverhalten oder Snapshot-Uebernahme angepasst werden.',
        'related': ['frontend/src/App.tsx', 'frontend/src/hooks/useFlowLiveUpdates.ts'],
    },
    'frontend/src/components/layout/InspectorPanel.tsx': {
        'purpose': 'Node- und Edge-Inspector fuer bearbeitbare Eigenschaften.',
        'edit': 'Wenn weitere konfigurierbare Felder in der UI auftauchen sollen.',
        'related': ['frontend/src/store/useFlowStore.ts', 'frontend/src/components/common/JsonEditor.tsx'],
    },
    'frontend/src/components/layout/PlannerComposer.tsx': {
        'purpose': 'Planner-Dialog fuer die lokale LLM-Graph-Erzeugung.',
        'edit': 'Wenn Prompting-UX oder Planner-Rueckmeldungen im Frontend erweitert werden.',
        'related': ['frontend/src/App.tsx', 'src/nova_synesis/planning/lit_planner.py'],
    },
    'frontend/src/components/layout/Sidebar.tsx': {
        'purpose': 'Linke Katalogleiste mit Handlern, Agenten und Ressourcen.',
        'edit': 'Wenn Drag-and-Drop oder Katalogdarstellung geaendert wird.',
        'related': ['frontend/src/components/flow/FlowCanvas.tsx', 'frontend/src/store/useFlowStore.ts'],
    },
    'frontend/src/components/layout/TopBar.tsx': {
        'purpose': 'Globale Aktionsleiste fuer Save, Run, Planner, Import und Export.',
        'edit': 'Wenn globale Bedienaktionen oder Statusanzeigen geaendert werden.',
        'related': ['frontend/src/App.tsx', 'frontend/src/components/common/StatusBadge.tsx'],
    },
    'tools/build_web_docs.py': {
        'purpose': 'Generiert aus dem docs-Ordner eine statische HTML-Dokumentationsseite mit Navigation, Suche und Source-Ansichten.',
        'edit': 'Wenn Layout, Suchlogik, Seitenrouting oder die statische Web-Doku erweitert werden sollen.',
        'related': ['docs/README.md', 'README.md', 'web/index.html'],
    },
}

SYMBOL_NOTES = {
    'create_app': 'Erzeugt die FastAPI-Anwendung und registriert ihre Endpunkte.',
    'Settings': 'Dataklasse fuer die Backend-Laufzeitkonfiguration.',
    'Settings.from_env': 'Laedt Settings aus Umgebungsvariablen mit sicheren Defaults.',
    'Settings.ensure_directories': 'Erzeugt benoetigte Daten- und Arbeitsverzeichnisse.',
    'OrchestratorService': 'Zentrale Fassade, die alle Backend-Bausteine zusammenhaelt.',
    'create_orchestrator': 'Factory fuer ein komplett verdrahtetes Orchestrator-System.',
    'ExecutionFlow': 'Graph-Modell des ausfuehrbaren Workflows.',
    'ExecutionFlow.observe': 'Erzeugt den serialisierbaren Zustand eines Flows fuer API und UI.',
    'ManualApproval': 'Speichert den manuellen Freigabestatus eines Nodes fuer die Ausfuehrung.',
    'TaskExecutor': 'Fuehrt eine einzelne Task inklusive Fehlerbehandlung aus.',
    'FlowExecutor': 'Fuehrt einen gesamten Workflow-Graphen aus.',
    'TaskHandlerRegistry': 'Registry der registrierten Runtime-Handler.',
    'TaskHandlerRegistry.issue_certificate': 'Erzeugt ein digitales Zertifikat fuer einen bereits registrierten Handler.',
    'register_default_handlers': 'Registriert alle eingebauten Handler.',
    'SQLiteRepository': 'Persistenzschicht fuer SQLite.',
    'LiteRTPlanner': 'Lokale LLM-Planung ueber LiteRT-LM.',
    'LiteRTPlanner.generate_flow_request': 'Erzeugt aus natuerlicher Sprache einen validierten FlowRequest.',
    'IntentPlanner': 'Regelbasierter Planer fuer strukturierte Intents.',
    'HandlerCertificate': 'Signierte Beschreibung eines vertrauenswuerdigen Handlers inklusive Fingerprint und Ablaufdatum.',
    'HandlerTrustRecord': 'Serialisierbare Trust-Sicht auf einen registrierten Handler fuer API und UI.',
    'HandlerTrustAuthority': 'Signiert und validiert Handler-Zertifikate gegen den aktuellen Code-Fingerprint.',
    'SemanticFirewall': 'Semantische Sicherheitspruefung fuer Flows, Agenten und aus Planner-Graphen abgeleitete Absichten.',
    'FlowSecurityReport': 'Strukturiertes Ergebnis einer Policy-Pruefung mit Fehlern und Warnungen.',
    'FlowSecurityReport.ensure_allowed': 'Bricht den aktuellen Vorgang ab, wenn Regelverletzungen gefunden wurden.',
    'SemanticFirewall.validate_flow_request': 'Prueft Graph-Struktur, Expressions, Egress und Memory-Fluesse vor der Ausfuehrung.',
    'SemanticFirewall.validate_agent_registration': 'Prueft Agent-Registrierung auf riskante Capabilities und unerlaubte Endpunkte.',
    'FlowCanvas': 'React-Flow-Leinwand des Editors.',
    'TaskNode': 'Custom Node fuer einzelne Tasks im Canvas.',
    'InspectorPanel': 'Eigenschaftseditor fuer Nodes und Edges.',
    'PlannerComposer': 'Dialog fuer die autonome Graph-Erzeugung.',
    'useFlowStore': 'Globaler Zustandsspeicher der UI auf Basis von Zustand.',
    'toFlowRequest': 'Serialisiert den Editorgraphen exakt in das Backend-Schema.',
    'fromFlowSnapshot': 'Wandelt einen Backend-Snapshot in React-Flow-Elemente um.',
    'createTaskNode': 'Erzeugt einen neuen Task-Node mit Defaultwerten.',
    'createTaskEdge': 'Erzeugt eine neue Kante mit Standardbedingung.',
}

TS_INTERNALS = {
    'frontend/src/App.tsx': [
        ('saveCurrentFlow', 'Speichert den aktuellen Canvas als echten Flow im Backend.'),
        ('handleRun', 'Speichert bei Bedarf und startet anschliessend die Flow-Ausfuehrung.'),
        ('handleExport', 'Exportiert den Editorzustand als JSON-Datei.'),
        ('handleImport', 'Importiert einen Editor-Export oder einen nackten FlowRequest.'),
        ('handleGenerateWithPlanner', 'Fordert ueber das Backend einen neuen Graphen vom LLM-Planer an.'),
    ],
    'frontend/src/store/useFlowStore.ts': [
        ('snapshotGraph', 'Erzeugt einen unveraenderlichen Graph-Snapshot fuer Undo/Redo.'),
        ('withHistory', 'Haengt den aktuellen Zustand an die Undo-Historie an.'),
        ('mergeSnapshotIntoNode', 'Uebernimmt Runtime-Daten aus einem Backend-Snapshot in einen Editor-Node.'),
    ],
    'frontend/src/components/layout/InspectorPanel.tsx': [
        ('patchNode', 'Wendet ein Teilupdate auf die Daten eines Nodes an.'),
        ('splitCsv', 'Konvertiert komma-separierte Texte in Stringlisten.'),
        ('asObject', 'Normalisiert unbekannte Werte zu einem sicheren Objekt.'),
        ('statusTone', 'Ordnet Task-Status einer Badge-Farbe zu.'),
        ('handleApproveNode', 'Freigabe eines Nodes lokal oder ueber die Approval-API.'),
        ('handleRevokeNodeApproval', 'Hebt eine bestehende manuelle Freigabe lokal oder ueber die Approval-API auf.'),
        ('NodeField', 'Hilfskomponente fuer einfache Texteingaben im Inspector.'),
        ('NumericField', 'Hilfskomponente fuer numerische Eingaben im Inspector.'),
    ],
    'frontend/src/lib/flowSerialization.ts': [
        ('readUiMetadata', 'Liest UI-spezifische Metadaten aus dem allgemeinen Metadata-Objekt.'),
        ('asPosition', 'Leitet eine gueltige Canvas-Position aus Metadaten oder Fallbacks ab.'),
        ('snapshotNodeToEditorNode', 'Wandelt einen Backend-Node-Snapshot in einen Editor-Node um.'),
    ],
    'frontend/src/components/layout/TopBar.tsx': [
        ('statusTone', 'Ordnet globale Flow-Zustaende den Topbar-Badge-Farben zu.'),
    ],
}

GUIDES = {
    'README.md': '''# NOVA-SYNESIS Dokumentation

Neural Orchestration Visual Autonomy  
Stateful Yielding Node-based Execution Semantic Integrated Surface

Diese Dokumentation erklaert das System so, dass auch ein Entwickler ohne Vorwissen NOVA-SYNESIS starten, verstehen, absichern und gezielt aendern kann.

## Einstieg

1. [Schnellstart](getting-started.md)
2. [Systemueberblick](system-overview.md)
3. [Backend-Laufzeit](backend-runtime.md)
4. [Frontend-Editor](frontend-editor.md)
5. [LLM-Planer und LiteRT](planner-and-lit.md)
6. [Security und Policy](security-and-policy.md)
7. [Handler Trust und Freigaben](handler-trust-and-approval.md)
8. [Failure Playbook](failure-playbook.md)
9. [Decision Guide](decision-guide.md)
10. [Real World Scenarios](real-world-scenarios.md)
11. [Aenderungsleitfaden](change-workflows.md)
12. [Referenzindex](reference/index.md)

## Wie du diese Doku liest

- Starte mit `getting-started.md`, wenn du das System lokal hochfahren willst.
- Lies `system-overview.md` und `backend-runtime.md`, wenn du Architektur und Laufzeit verstehen willst.
- Nutze `security-and-policy.md`, `handler-trust-and-approval.md` und `failure-playbook.md`, bevor du produktive Flows oder neue Handler einsetzt.
- Verwende `decision-guide.md` und `real-world-scenarios.md`, wenn du eigene Flows sicher entwerfen oder veraendern willst.
''',
    'getting-started.md': '''# Schnellstart

## 1. Backend starten

```powershell
./run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

Wichtige URLs:

- `GET /docs`
- `GET /health`
- `GET /planner/status`
- `POST /flows/validate`

## 2. Frontend starten

`frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8552
```

Dann:

```powershell
cd frontend
npm run dev
```

## 3. Minimaler Arbeitsablauf

1. Handler, Agenten und Ressourcen im Frontend laden.
2. In `GET /handlers` oder der Sidebar pruefen, welche Handler trusted sind.
3. Einen Graphen im Canvas zeichnen oder ueber den Planner erzeugen.
4. Fuer sensitive oder untrusted Handler im Inspector entscheiden, ob `requires_manual_approval` gesetzt sein soll.
5. Vor dem Speichern `POST /flows/validate` verwenden oder die UI-Validierung ausloesen.
6. Den Flow ueber `POST /flows` speichern.
7. Falls noetig den Node per Inspector oder Approval-API freigeben.
8. Den Flow ueber `POST /flows/{flow_id}/run` ausfuehren.
9. Laufzeit und Status ueber `GET /flows/{flow_id}` oder `/ws/flows/{flow_id}` beobachten.

## 4. Wichtige Umgebungsvariablen

- `NS_API_HOST`, `NS_API_PORT`: FastAPI-Bindung
- `NS_LIT_BINARY_PATH`, `NS_LIT_MODEL_PATH`, `NS_LIT_TIMEOUT_S`: lokaler Planner
- `NS_HANDLER_CERTIFICATE_SECRET`, `NS_HANDLER_CERTIFICATE_ISSUER`, `NS_HANDLER_CERTIFICATE_TTL_HOURS`: Handler-Zertifikate
- `NS_SECURITY_ENABLED`: Semantic Firewall global ein- oder ausschalten
- `NS_SECURITY_AUTO_ISSUE_BUILTIN_HANDLER_CERTIFICATES`: Built-ins automatisch signieren
- `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS`: untrusted Handler beim Run blockieren
- `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS`: explizite Override-Freigabe zulassen
- `NS_SECURITY_HTTP_ALLOWED_HOSTS`: erlaubte HTTP-Zielhosts
- `NS_SECURITY_SEND_PROTOCOLS`: erlaubte Kommunikationsprotokolle fuer `send_message`
- `NS_CORS_ORIGINS`: erlaubte Frontend-Urspruenge

## 5. Mentales Modell

- Das Frontend bearbeitet einen gerichteten Graphen aus Nodes und Edges.
- `toFlowRequest()` wandelt den Editorgraphen in das Backend-Schema.
- Das Backend validiert Struktur, Expressions, Handler-Trust und Sicherheitsregeln.
- Erst danach wird gespeichert oder ausgefuehrt.
- Die Runtime fuehrt nur DAGs aus und meldet Snapshots laufend an UI und Persistenz zurueck.
''',
    'system-overview.md': '''# Systemueberblick

## Schichten

- Domaene: `src/nova_synesis/domain/models.py`
- Planung: `planning/planner.py` und `planning/lit_planner.py`
- Sicherheitspruefung: `security/policy.py` und `security/trust.py`
- Runtime: `runtime/engine.py` und `runtime/handlers.py`
- Persistenz: `persistence/sqlite_repository.py`
- API: `api/app.py`
- UI: `frontend/src/`

## Hauptdatenfluss

1. Graph im Frontend erstellen oder ueber den LiteRT-Planer generieren
2. `toFlowRequest()` erzeugt das Backend-Schema
3. `POST /flows/validate` prueft Graph, Expressions, Handler-Trust, Egress und Memory-Fluesse
4. `POST /flows` speichert den Graphen
5. optionale manuelle Freigaben werden node-spezifisch gesetzt
6. `POST /flows/{id}/run` startet die Ausfuehrung
7. `FlowExecutor` verarbeitet den Graphen Node fuer Node
8. `/ws/flows/{flow_id}` uebertraegt Snapshots an die UI
9. `GET /flows/{flow_id}` bleibt die kanonische Wahrheit fuer den Laufzeitstand

## Was dieses System bewusst ist

- graphbasiert statt chatbasiert
- zustandsbehaftet statt nur requestbasiert
- planner-unterstuetzt, aber nicht planner-abhaengig
- sicherheitsgefiltert, bevor Seiteneffekte entstehen
- handler-vertrauensbasiert statt nur handler-namensbasiert
''',
    'backend-runtime.md': '''# Backend-Laufzeit

Die Backend-Laufzeit wird durch `OrchestratorService` zusammengesetzt. Er verdrahtet Repository, Speicher, Ressourcenmanager, Handler-Registry, Planner, Semantic Firewall und Execution-Engine.

## Reihenfolge eines normalen Flows

1. API nimmt einen `FlowCreateRequest` oder eine Planner-Anfrage entgegen.
2. `TaskHandlerRegistry` bewertet alle Handler gegen digitale Zertifikate und erzeugt Trust-Records.
3. `OrchestratorService.validate_flow_request()` laesst die semantische Firewall laufen.
4. Der Flow wird in Domaenenobjekte ueberfuehrt und in SQLite gespeichert.
5. `FlowExecutor.run_flow()` startet die DAG-Ausfuehrung.
6. `TaskExecutor.execute_task()` loest Templates auf, reserviert Ressourcen, ruft Agent und Handler auf und persistiert Snapshots.
7. WebSocket-Abonnenten erhalten Ereignisse wie `flow.started`, `node.completed`, `node.approval.updated` oder `flow.failed`.

## Trust- und Approval-Gates

- `GET /handlers` ist die kanonische Betriebsansicht auf Handler-Trust.
- Der Planner-Katalog enthaelt nur trusted Handler.
- Freigaben liegen an `Task.manual_approval` und werden im Flow-Snapshot persistiert.
- `POST /flows/{flow_id}/nodes/{node_id}/approval` und `DELETE /flows/{flow_id}/nodes/{node_id}/approval` aendern den Freigabestatus ohne den ganzen Flow neu anzulegen.

## Regel fuer Aenderungen

Wenn du etwas an einem Runtime-Vertrag aenderst, pruefe fast immer gleichzeitig API, Domaenenmodell, Engine, Frontend-Typen, Serialisierung und Tests.
''',
    'frontend-editor.md': '''# Frontend-Editor

Die UI besteht aus `App.tsx`, dem Zustand-Store `useFlowStore.ts`, der Zeichenflaeche `FlowCanvas.tsx`, der linken `Sidebar.tsx`, dem `InspectorPanel.tsx`, dem Planner-Dialog und der `TopBar.tsx`.

## Was der Editor wirklich tut

- laedt Handler, Agenten und Ressourcen aus dem echten Backend
- baut daraus React-Flow-Nodes und -Edges
- serialisiert den Editorzustand ueber `toFlowRequest()`
- speichert und startet echte Flows
- uebernimmt Live-Snapshots ueber WebSocket oder Polling
- zeigt pro Node Handler-Trust und manuelle Freigaben im Inspector

## Kritische Integrationsstellen

- `frontend/src/lib/flowSerialization.ts`: muss exakt zum FastAPI-Schema passen
- `frontend/src/lib/apiClient.ts`: enthaelt die echten REST-, Approval- und WebSocket-Aufrufe inklusive `POST /flows/validate`
- `frontend/src/store/useFlowStore.ts`: haelt den kanonischen UI-Zustand fuer Nodes, Edges, Auswahl und Laufzeitstatus
- `frontend/src/hooks/useFlowLiveUpdates.ts`: faellt bei Socket-Problemen auf Polling zurueck

## Betreiberperspektive im Inspector

- `Handler trust` zeigt Zertifikatsstatus, Issuer, Fingerprint und Ablaufdatum
- `Require manual approval before execution` markiert einen Node als freigabepflichtig
- `Approve Node` und `Revoke Approval` sprechen direkt mit der Approval-API, wenn der Flow bereits gespeichert ist
- bei ungespeicherten lokalen Aenderungen arbeitet der Inspector bewusst lokal weiter, um den Canvas-Zustand nicht zu ueberschreiben
''',
    'planner-and-lit.md': '''# LLM-Planer und LiteRT

Der Planner erzeugt keine Mock-Graphen. Er nutzt die lokale `lit`-Binary und das Gemma-Modell im `LIT/`-Ordner, extrahiert JSON und normalisiert das Resultat auf das echte `FlowRequest`-Schema.

## Ablauf

1. `LiteRTPlanner._build_prompt()` baut den Prompt aus Benutzerziel und echtem Katalog.
2. `_invoke_model()` ruft `lit.windows_x86_64.exe` mit `gemma-4-E2B-it.litertlm` auf.
3. `_parse_model_output()` extrahiert genau ein JSON-Objekt.
4. `_normalize_flow_request()` korrigiert IDs, Defaults, Abhaengigkeiten und Handler-Inputs.
5. `OrchestratorService.generate_flow_with_llm()` laesst den Graphen anschliessend noch durch die Semantic Firewall laufen.

## Wichtige Sicherheitsgrenzen

- Ressourcen und Memories mit `sensitive = true` oder `planner_visible = false` werden aus dem Planner-Katalog herausgefiltert.
- untrusted Handler werden komplett aus dem Planner-Katalog entfernt.
- Die Antwort enthaelt `security_report`, damit UI und Betreiber sehen, ob der generierte Graph policy-konform war.
- Planner-Warnungen bedeuten: der Graph wurde normalisiert, aber nicht stillschweigend erweitert.
- `requires_manual_approval` wird standardmaessig auf `false` normalisiert und nur uebernommen, wenn es explizit im Graphen gesetzt ist.
''',
    'security-and-policy.md': '''# Security und Policy

NOVA-SYNESIS sichert nicht nur Code, sondern die Absicht eines Graphen. Diese Aufgabe uebernimmt die Semantic Firewall in `src/nova_synesis/security/policy.py`.

## Wann die Policy greift

- bei Agent-Registrierung
- bei `POST /flows/validate`
- bei `POST /flows`
- vor `POST /flows/{flow_id}/run`
- nach einer Planner-Generierung, bevor der Graph an die UI zurueckgeht

## Was geprueft wird

- Graph-Struktur: keine Zyklen, keine Selbstkanten, keine unbekannten Nodes
- Retry-Budget und maximale Graphgroesse
- Handler-Trust: unbekannte, untrusted oder abgelaufene Handler-Zustaende
- Expressions und Templates: nur erlaubte Symbole und AST-Knoten
- HTTP-Egress: nur erlaubte Hosts oder Loopback
- Messaging: nur erlaubte Protokolle und kein Endpoint-Override im Payload
- Dateioperationen: kein `allow_outside_workdir`
- Sensitive Memories: kein Abfluss in `http_request` oder externe Nachrichtenziele
- Planner-visible Memories: kein untrusted Ingest ohne explizites Opt-in
- Agent-Registrierung: keine unerlaubten REST/WebSocket-Endpunkte und keine blockierten Capability-Profile

## Digitale Handler-Zertifikate

- `HandlerTrustAuthority` signiert interne Handler-Zertifikate mit HMAC ueber einen kanonischen Payload.
- Der Fingerprint wird aus Handlername, Modul, Qualname und Quellcode abgeleitet.
- Built-in-Handler koennen automatisch signiert werden.
- Custom Handler bleiben ohne Zertifikat sichtbar, aber sie gelten als untrusted.
- `GET /handlers` ist die Betriebsansicht fuer `trusted`, `trust_reason`, `fingerprint` und `certificate`.

## Manuelle Freigabe

- Ein Node kann `requires_manual_approval = true` tragen.
- Die Freigabe liegt in `manual_approval`.
- Im Create- und Validate-Pfad wird das als Warnung behandelt.
- Im Run-Pfad blockiert die Policy den Start, solange keine gueltige Freigabe mit `approved_by` vorliegt.
- Wenn `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS=true` aktiv ist, kann eine explizite Node-Freigabe einen untrusted Handler fuer genau diesen Flow-Node erlauben.

## Bedeutende Felder

- `sensitive = true`
- `planner_visible = false`
- `allow_untrusted_ingest = true`
- `requires_manual_approval = true`
- `manual_approval.approved = true`

## Wichtige Settings

- `NS_HANDLER_CERTIFICATE_SECRET`
- `NS_HANDLER_CERTIFICATE_ISSUER`
- `NS_HANDLER_CERTIFICATE_TTL_HOURS`
- `NS_SECURITY_ENABLED`
- `NS_SECURITY_AUTO_ISSUE_BUILTIN_HANDLER_CERTIFICATES`
- `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS`
- `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS`
- `NS_SECURITY_MAX_NODES`
- `NS_SECURITY_MAX_EDGES`
- `NS_SECURITY_MAX_TOTAL_ATTEMPTS`
- `NS_SECURITY_MAX_EXPRESSION_LENGTH`
- `NS_SECURITY_MAX_EXPRESSION_NODES`
- `NS_SECURITY_HTTP_ALLOWED_HOSTS`
- `NS_SECURITY_SEND_PROTOCOLS`
''',
    'handler-trust-and-approval.md': '''# Handler Trust und Freigaben

Diese Seite beschreibt die zweite Sicherheitslinie nach der Semantic Firewall: vertrauenswuerdige Handler und die explizite manuelle Node-Freigabe.

## 1. Was ein Handler-Zertifikat hier bedeutet

NOVA-SYNESIS nutzt kein externes X.509-PKI, sondern ein internes, signiertes Handler-Zertifikat:

- der Fingerprint wird aus Modul, Qualname und Quellcode des Handlers abgeleitet
- `HandlerTrustAuthority` signiert diesen Fingerprint per HMAC
- das Zertifikat enthaelt `issuer`, `issued_at`, `expires_at`, `fingerprint` und `built_in`
- bei jeder Registrierung wird geprueft, ob Zertifikat und aktueller Handler-Code noch zusammenpassen

## 2. Trust-Lebenszyklus

1. Ein Handler wird registriert.
2. Built-in-Handler erhalten automatisch ein Zertifikat, wenn `NS_SECURITY_AUTO_ISSUE_BUILTIN_HANDLER_CERTIFICATES=true` ist.
3. Custom Handler koennen beim Registrieren ein Zertifikat mitgeben oder spaeter ueber `TaskHandlerRegistry.issue_certificate()` signiert werden.
4. `GET /handlers` liefert den aktuellen Trust-Status inklusive Zertifikat an UI und Betrieb.
5. Der LiteRT-Planer sieht nur trusted Handler im Katalog.

## 3. API und UI

- `GET /handlers`: liefert `handlers` und `details`
- `POST /flows/{flow_id}/nodes/{node_id}/approval`: setzt eine manuelle Freigabe
- `DELETE /flows/{flow_id}/nodes/{node_id}/approval`: hebt sie wieder auf

Im `InspectorPanel` sieht der Betreiber:

- ob der aktuelle Handler trusted oder untrusted ist
- warum der Handler so eingestuft wurde
- Zertifikatsdetails wie Issuer, Fingerprint und Ablaufdatum
- ob fuer den Node eine manuelle Freigabe erforderlich oder bereits gesetzt ist

## 4. Wann die Ausfuehrung blockiert wird

- unbekannter Handler: immer blockiert
- untrusted Handler bei `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS=true`: spaetestens beim Run blockiert
- `requires_manual_approval=true`, aber keine Freigabe gesetzt: beim Run blockiert
- Freigabe ohne `approved_by`: ebenfalls blockiert

## 5. Operator-Regeln

- Built-in-Handler bleiben der Normalfall.
- Eigene Handler nur dann trusten, wenn Codequelle und Seiteneffektprofil klar sind.
- Manuelle Freigaben sind flow-spezifisch, nicht global.
- Eine Freigabe ersetzt kein Zertifikat; sie ist eine bewusste Ausnahme fuer einen konkreten Node.

## 6. Relevante Settings

- `NS_HANDLER_CERTIFICATE_SECRET`
- `NS_HANDLER_CERTIFICATE_ISSUER`
- `NS_HANDLER_CERTIFICATE_TTL_HOURS`
- `NS_SECURITY_AUTO_ISSUE_BUILTIN_HANDLER_CERTIFICATES`
- `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS`
- `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS`
''',
    'failure-playbook.md': '''# Failure Playbook

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
2. Prompt kuerzen und restriktiver machen
3. `max_nodes` senken
4. sicherstellen, dass benoetigte Handler, Agenten, Ressourcen und Memory-IDs wirklich registriert sind
5. bei wiederholtem Fehler den Flow manuell im Editor bauen

## 2. Semantic Firewall lehnt den Flow ab

### Woran du es erkennst

- `POST /flows/validate`, `POST /flows` oder `POST /planner/generate-flow` liefert einen Fehler
- typische Fehlermeldungen:
  - `Semantic firewall rejected flow`
  - `Outbound host ... is outside the semantic firewall allowlist`
  - `Flow contains a cycle`
  - `Sensitive memory data may not flow into http_request nodes`

### Typische Ursachen

- zyklischer Graph
- `http_request` auf einen nicht erlaubten Host
- `send_message` ohne `target_agent_id` oder mit Endpoint-Override
- Template oder Condition mit nicht erlaubten Symbolen
- planner-sichtbare Memory-Store-Node hinter untrusted Ingest

### Sofortmassnahmen

1. denselben Payload gegen `POST /flows/validate` schicken
2. `violations` und `warnings` getrennt lesen
3. pruefen, ob das Problem fachlich oder rein policy-seitig ist
4. bei legitimen Produktionsfaellen erst Settings oder Memory-/Resource-Metadaten anpassen, nicht die Regel blind entfernen

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

## 5. Resource haengt oder laeuft in Timeout / Sattlauf

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

## 6. Flow bleibt auf `RUNNING` stehen

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

## 7. Graph-Deadlock oder logisch blockierter Flow

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

## 8. Handler wirft Exception

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
''',
    'decision-guide.md': '''# Decision Guide

Diese Seite dokumentiert Entscheidungslogik. Genau dieses Wissen fehlt oft, wenn ein System zwar sauber gebaut, aber noch nicht betriebssicher uebergeben wurde.

## 1. Wann Planner, wann manuell?

Nutze den LiteRT-Planer, wenn:

- du aus einer fachlichen Beschreibung schnell einen ersten Graphen ableiten willst
- du eine komplexe Kette mit mehreren Handlern skizzieren musst
- du anschliessend im visuellen Editor nacharbeiten willst

Baue den Flow lieber manuell, wenn:

- die exakte Kantenlogik bereits feststeht
- du einen Produktionsfehler analysierst
- du ein sehr kleines, deterministisches Setup mit 1 bis 3 Nodes hast

## 2. Neuer Handler oder bestehenden Handler erweitern?

Erweitere einen bestehenden Handler, wenn:

- dieselbe Grundoperation bleibt
- Ein- und Ausgabeform nur optional waechst
- Fehlerbild und Retry-Verhalten gleich bleiben

Baue einen neuen Handler, wenn:

- eine neue Nebenwirkung entsteht
- eine andere externe Abhaengigkeit angebunden wird
- der Inputvertrag fachlich anders ist
- der Nutzer den Baustein im Editor als eigenstaendige Aktion verstehen soll

## 3. Flow, einzelne Task oder Agent?

- Verwende einen Flow, wenn Reihenfolge, Verzweigung oder Fehlerbehandlung sichtbar modelliert werden muessen.
- Verwende nur eine einzelne Task, wenn genau ein isolierter Arbeitsschritt existiert.
- Verwende einen Agenten, wenn Faehigkeiten, Kommunikationsadapter oder eine feste Verantwortlichkeit wichtig sind.

Ein Agent ersetzt keinen Flow. Der Flow modelliert den Prozess. Der Agent modelliert, wer oder was eine Task ausfuehren darf.

## 4. Wann ist eine Resource wirklich notwendig?

Nutze eine Resource, wenn der Schritt an ein echtes externes Ziel oder eine limitierte Kapazitaet gebunden ist:

- API-Endpunkt
- Modellinstanz
- Datenbank
- Dateiablage
- GPU

Nutze keine Resource, wenn der Schritt rein lokal und transformativ ist:

- `template_render`
- `merge_payloads`
- `json_serialize`

## 5. Konkrete Resource-ID oder nur Resource-Type?

- `required_resource_ids`: wenn exakt ein bestimmtes System getroffen werden muss
- `required_resource_types`: wenn jeder passende Vertreter einer Kategorie ausreicht oder Fallback sinnvoll ist

Faustregel: feste Kern-API per ID, austauschbare Replikate oder GPUs per Typ.

## 6. Welche Rollback-Strategie ist die richtige?

- `FAIL_FAST`: wenn Folgeschritte ohne Erfolg des Nodes keinen Sinn ergeben
- `RETRY`: bei transienten Netz- oder Dienstfehlern
- `FALLBACK_RESOURCE`: wenn mehrere Ressourcen gleicher Art vorhanden sind
- `COMPENSATE`: wenn ein Fehler nach einer Nebenwirkung aktiv bereinigt werden muss

## 7. Wann musst du `POST /flows/validate` aktiv nutzen?

Immer vor produktivem Speichern oder Ausfuehren, wenn:

- ein Flow durch den Planner erzeugt wurde
- neue Templates, Conditions oder Validator-Ausdruecke eingebaut wurden
- neue Ressourcen, Agenten oder Memory-Systeme beteiligt sind
- du Security-Grenzen geaendert hast

## 8. Wie klassifizierst du Memory-Systeme?

- `sensitive = true`: fuer vertrauliche Inhalte, die nicht in Planner oder externe Sinks gelangen sollen
- `planner_visible = false`: wenn ein Memory manuell nutzbar, aber nicht planner-sichtbar sein soll
- `allow_untrusted_ingest = true`: nur wenn bewusst Daten aus HTTP, Messaging oder Dateiquellen in planner-sichtbares Wissen einfliessen duerfen

Wenn du unsicher bist, starte konservativ: `sensitive = true` oder `planner_visible = false`.

## 9. Wann soll eine Condition auf eine Edge?

Eine Edge-Condition ist richtig, wenn du einen fachlichen Branch modellierst:

- Erfolgspfad vs Fehlerpfad
- weitere Verarbeitung nur bei gueltigem Ergebnis
- optionale Folgeaktionen

Eine Edge-Condition ist falsch, wenn du damit Daten umbauen oder fehlende Vorverarbeitung verstecken willst. Dann fehlt meist ein eigener Node.
''',
    'real-world-scenarios.md': '''# Real World Scenarios

Diese Seite enthaelt bewusst nur drei End-to-End-Beispiele. Ziel ist nicht Vollstaendigkeit, sondern sichere Anwendbarkeit mit dem echten Backend und der aktiven Security-Policy.

## Szenario 1: Einfacher Betriebsflow "Platform Health Snapshot"

Referenz: `Use_Cases/platform_health_snapshot/`

### Ziel

Die lokale Plattform pruefen, einen Snapshot speichern und daraus eine Textzusammenfassung schreiben.

### Warum dieser Flow produktionsnah ist

- nutzt nur echte Built-in-Handler
- benoetigt keinen Mock-Service
- zeigt HTTP, Memory, Serialisierung und Dateiablage in einer kleinen, gut kontrollierbaren Kette

### Typischer Ablauf

1. `http_request` gegen einen lokalen oder allowlist-konformen Health-Endpunkt
2. `json_serialize` fuer den Snapshot
3. `write_file` fuer Rohdaten
4. `template_render` fuer die Zusammenfassung
5. `write_file` fuer den lesbaren Report
6. optional `memory_store` fuer den letzten Snapshot-Key

## Szenario 2: Komplexer Flow mit Branching "Semantic Ticket Triage"

Referenz: `Use_Cases/semantic_ticket_triage/`

### Ziel

Tickets semantisch bewerten, Wissen aus Memory laden und je nach Ergebnis an unterschiedliche interne Queue-Agenten dispatchen.

### Warum dieser Flow produktionsnah ist

- kombiniert Vector Memory, Planner-verwertbares Wissen und Messaging
- nutzt Branching ueber Edge-Conditions
- bleibt policy-konform, weil `send_message` auf interne Message Queues begrenzt bleibt

### Typischer Ablauf

1. Ticketdaten laden oder als Input entgegennehmen
2. `memory_search` in einem Vector-Memory
3. `template_render` fuer die Triage-Zusammenfassung
4. Branching auf `dispatch-support` oder `dispatch-sales`
5. `send_message` an registrierte Queue-Agenten

## Szenario 3: Fehlerfall mit Retry und Fallback "API-Replica uebernimmt"

### Ziel

Ein fragiler Infrastrukturzugriff soll auch dann stabil laufen, wenn die bevorzugte Ressource kurzzeitig ausfaellt.

### Beispielstruktur

```json
{
  "nodes": [
    {
      "node_id": "fetch-primary-or-fallback",
      "handler_name": "http_request",
      "input": { "method": "GET", "timeout_s": 8 },
      "required_resource_types": ["API"],
      "retry_policy": {
        "max_retries": 3,
        "backoff_ms": 500,
        "exponential": true,
        "max_backoff_ms": 5000,
        "jitter_ratio": 0.1
      },
      "rollback_strategy": "FALLBACK_RESOURCE",
      "validator_rules": {
        "required_keys": ["status_code", "body"],
        "expression": "result['status_code'] < 500"
      }
    },
    {
      "node_id": "store-result",
      "handler_name": "memory_store",
      "input": {
        "memory_id": "working-memory",
        "key": "resilient-fetch-result",
        "value": "{{ results['fetch-primary-or-fallback']['body'] }}"
      },
      "dependencies": ["fetch-primary-or-fallback"],
      "conditions": { "fetch-primary-or-fallback": "source_result['status_code'] < 400" }
    }
  ],
  "edges": [
    {
      "from_node": "fetch-primary-or-fallback",
      "to_node": "store-result",
      "condition": "source_result['status_code'] < 400"
    }
  ]
}
```

### Sichere Betriebsreihenfolge

1. zuerst `POST /flows/validate`
2. danach speichern
3. Laufzeit ueber `GET /flows/{flow_id}` beobachten
4. bei Auffaelligkeiten pruefen, ob wirklich Retry oder bereits Resource-Fallback greift
''',
    'change-workflows.md': '''# Aenderungsleitfaden

## Neuer Handler

1. Handler in `runtime/handlers.py` implementieren und registrieren
2. entscheiden, ob der Handler ein digitales Zertifikat erhalten soll oder bewusst untrusted bleibt
3. pruefen, ob der Handler im Planner sichtbar sein soll
4. Security-Regeln fuer Egress, Templates oder Seiteneffekte in `security/policy.py` bewerten
5. Tests in `tests/test_orchestrator.py` erweitern
6. Frontend prueft den Handler automatisch ueber `/handlers`
7. `tools/generate_docs.py` und danach `docs/` neu erzeugen

## Neues Node-Feld

1. Backend-Schema in `api/app.py`
2. Domaenenmodell und Snapshot in `domain/models.py`
3. TypeScript-Typen in `frontend/src/types/api.ts`
4. Serialisierung in `frontend/src/lib/flowSerialization.ts`
5. Inspector in `frontend/src/components/layout/InspectorPanel.tsx`
6. Validierung und Security-Auswirkungen pruefen
7. Tests und Dokumentation nachziehen

## Neue Security-Regel

1. Policy in `security/policy.py` erweitern
2. Settings in `config.py` und `.env.example` nachziehen
3. API- und Planner-Auswirkungen pruefen
4. mindestens einen positiven und einen negativen Testfall schreiben
5. `tools/generate_docs.py` ausfuehren und `docs/` neu erzeugen

## Neuer Trust- oder Approval-Pfad

1. Zertifikats- oder Approval-Logik in `security/trust.py`, `runtime/handlers.py` oder `domain/models.py` anpassen
2. `services/orchestrator.py` und `api/app.py` auf neue Operator-Aktionen abstimmen
3. Frontend-Inspector und Typen synchronisieren
4. mindestens einen positiven und einen negativen Security-Test ergaenzen
5. danach Referenzdoku und Betriebsdoku neu erzeugen
''',
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def excluded(path: Path) -> bool:
    r = rel(path)
    parts = set(path.relative_to(ROOT).parts)
    if '.pytest_cache' in parts or '__pycache__' in parts:
        return True
    if 'output' in parts or 'state' in parts:
        return True
    if path.name == '.env':
        return True
    if path.suffix in {'.zip', '.exe', '.db', '.pdf'}:
        return True
    if r.endswith('.tsbuildinfo') or r.endswith('.xnnpack_cache') or r.endswith('.litertlm'):
        return True
    return any(r == item or r.startswith(item + '/') for item in EXCLUDED)


def project_files() -> list[Path]:
    files = [p for p in ROOT.rglob('*') if p.is_file() and not excluded(p)]
    return sorted(files, key=lambda p: rel(p))


def doc_path(source: Path) -> Path:
    r = source.relative_to(ROOT)
    return REF / r.parent / f'{r.name}.md'


def rlink(base: Path, target: Path) -> str:
    return os.path.relpath(target, base).replace('\\', '/')


def source_link(doc: Path, source: Path) -> str:
    return f'[{rel(source)}]({rlink(doc.parent, source)})'


def doc_link(doc: Path, source: Path) -> str:
    target = doc_path(source)
    return f'[{rel(source)}]({rlink(doc.parent, target)})'


def category(r: str) -> str:
    if r.startswith('src/nova_synesis/'):
        return 'Backend'
    if r.startswith('Use_Cases/'):
        return 'Use Cases'
    if r.startswith('frontend/src/'):
        return 'Frontend'
    if r.startswith('frontend/'):
        return 'Frontend-Konfiguration'
    if r.startswith('LIT/'):
        return 'LLM-Runtime'
    if r.startswith('tests/'):
        return 'Tests'
    if r.startswith('tools/'):
        return 'Werkzeug'
    return 'Projektdatei'


def generic_purpose(path: Path) -> str:
    r = rel(path)
    if path.suffix == '.py':
        return 'Python-Modul des Projekts.'
    if path.suffix in {'.ts', '.tsx'}:
        return 'TypeScript-Modul des Frontends.'
    if path.suffix == '.css':
        return 'Stylesheet der Weboberflaeche.'
    if path.suffix in {'.json', '.toml'}:
        return 'Konfigurationsdatei des Projekts.'
    if path.suffix == '.md':
        return 'Markdown-Datei mit Projektwissen oder Anweisungen.'
    if path.suffix in {'.html'}:
        return 'HTML-Datei fuer Visualisierung oder Browser-Einstieg.'
    if path.suffix in {'.ps1', '.cmd'}:
        return 'Skript fuer lokale Entwicklerablaeufe.'
    if r.endswith('.tsbuildinfo') or r.endswith('.xnnpack_cache'):
        return 'Generiertes Cache-Artefakt, das Builds oder Inferenz beschleunigt.'
    if path.suffix in {'.exe', '.zip'} or '.litertlm' in r:
        return 'Binaeres Artefakt des Projekts.'
    return 'Projektdatei mit eigener Rolle im Repository.'


def generic_edit(path: Path) -> str:
    r = rel(path)
    if path.suffix in {'.py', '.ts', '.tsx', '.css'}:
        return 'Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.'
    if path.suffix in {'.json', '.toml'}:
        return 'Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.'
    if r.endswith('.tsbuildinfo') or r.endswith('.xnnpack_cache'):
        return 'Normalerweise nie direkt. Bei Bedarf loeschen und neu erzeugen lassen.'
    if path.suffix in {'.exe', '.zip'} or '.litertlm' in r:
        return 'Nur bei gezieltem Austausch des Artefakts.'
    return 'Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.'

def symbol_desc(name: str, kind: str, parent: str | None = None) -> str:
    key = f'{parent}.{name}' if parent else name
    if key in SYMBOL_NOTES:
        return SYMBOL_NOTES[key]
    if name in SYMBOL_NOTES:
        return SYMBOL_NOTES[name]
    low = name.lower()
    if kind == 'class':
        if name.endswith(('Request', 'Response', 'Model')):
            return f'Datenmodell `{name}` fuer validierte Schichtgrenzen.'
        if name.endswith('Manager'):
            return f'Koordinationsklasse `{name}` fuer mehrere Instanzen oder Zustandsobjekte.'
        if name.endswith('Factory'):
            return f'Factory-Klasse `{name}` zum Erzeugen passender Objekte.'
        if name.endswith('Registry'):
            return f'Registry `{name}` fuer die Registrierung und spaetere Aufloesung von Verhalten.'
        if name.endswith('Executor'):
            return f'Ausfuehrungskomponente `{name}` fuer Runtime-Logik.'
        if name.endswith('Service'):
            return f'Service-Klasse `{name}` als fachliche Fassade.'
        return f'Klasse `{name}` dieses Moduls.'
    if low == '__init__':
        return 'Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.'
    if low.startswith('from_'):
        return f'Wandelt externe Daten fuer `{name}` in das interne Format um.'
    if low.startswith('to_'):
        return f'Wandelt interne Daten fuer `{name}` in ein Zielformat um.'
    if low.startswith('get_'):
        return f'Liest Daten fuer `{name}` aus einem Speicher oder einer Laufzeitquelle.'
    if low.startswith('list_'):
        return f'Gibt eine Liste von Daten fuer `{name}` zurueck.'
    if low.startswith('save_'):
        return f'Persistiert Daten fuer `{name}` dauerhaft.'
    if low.startswith('fetch_'):
        return f'Laedt Daten fuer `{name}` ueber eine externe oder interne API.'
    if low.startswith('register'):
        return f'Registriert Verhalten oder Objekte fuer `{name}`.'
    if low.startswith('execute'):
        return f'Fuehrt die Kernarbeit von `{name}` aus.'
    if low.startswith('run'):
        return f'Steuert den Ablauf von `{name}`.'
    if low.startswith('update'):
        return f'Aktualisiert den Zustand von `{name}`.'
    if low.startswith('search'):
        return f'Sucht passende Daten fuer `{name}`.'
    if low.startswith('persist'):
        return f'Schreibt Daten fuer `{name}` in einen dauerhaften Speicher.'
    if low.startswith('retrieve'):
        return f'Liests Daten fuer `{name}` aus einem Speicher zurueck.'
    if low.startswith('visit_'):
        return f'AST-Besuchsmethode fuer `{name[6:]}`-Knoten.'
    if kind in {'type', 'interface'}:
        return f'TypeScript-Typ `{name}` fuer einen Datenvertrag.'
    if kind == 'component':
        return f'React-Komponente `{name}` fuer einen klar abgegrenzten UI-Bereich.'
    return f'Funktion oder Definition `{name}` dieses Moduls.'


def imports_for(path: Path) -> list[str]:
    if path.suffix == '.py':
        pattern = re.compile(r'^(from\s+\S+\s+import\s+.+|import\s+.+)$', re.MULTILINE)
    elif path.suffix in {'.ts', '.tsx', '.js', '.d.ts'}:
        pattern = re.compile(r'^import\s+.+$', re.MULTILINE)
    else:
        return []
    return pattern.findall(path.read_text(encoding='utf-8', errors='ignore'))


def py_args(node: ast.AST) -> list[str]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    out: list[str] = []
    for arg in node.args.posonlyargs:
        out.append(arg.arg)
    if node.args.posonlyargs:
        out.append('/')
    for arg in node.args.args:
        out.append(arg.arg)
    if node.args.vararg:
        out.append(f'*{node.args.vararg.arg}')
    elif node.args.kwonlyargs:
        out.append('*')
    for arg in node.args.kwonlyargs:
        out.append(arg.arg)
    if node.args.kwarg:
        out.append(f'**{node.args.kwarg.arg}')
    return out


def py_symbols(path: Path) -> tuple[list[tuple[str, str]], list[tuple[str, list[tuple[str, str]]]]]:
    mod = ast.parse(path.read_text(encoding='utf-8'))
    funcs: list[tuple[str, str]] = []
    classes: list[tuple[str, list[tuple[str, str]]]] = []
    for node in mod.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append((node.name, f"{node.name}({', '.join(py_args(node))})"))
        elif isinstance(node, ast.ClassDef):
            methods: list[tuple[str, str]] = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append((child.name, f"{child.name}({', '.join(py_args(child))})"))
            classes.append((node.name, methods))
    return funcs, classes


def ts_symbols(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding='utf-8')
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    patterns = [
        (r'export\s+type\s+([A-Za-z0-9_]+)', 'type'),
        (r'export\s+interface\s+([A-Za-z0-9_]+)', 'interface'),
        (r'export\s+function\s+([A-Za-z0-9_]+)', 'export'),
        (r'export\s+const\s+([A-Za-z0-9_]+)', 'export'),
        (r'function\s+([A-Za-z0-9_]+)\s*\(', 'internal'),
    ]
    for pattern, kind in patterns:
        for name in re.findall(pattern, text):
            item = (name, kind)
            if item not in seen:
                seen.add(item)
                results.append(item)
    if path.name == 'App.tsx' and ('App', 'component') not in seen:
        results.insert(0, ('App', 'component'))
    return results


def symbol_block(path: Path) -> str:
    r = rel(path)
    if path.suffix == '.py':
        funcs, classes = py_symbols(path)
        lines: list[str] = []
        if classes:
            lines += ['## Klassen', '']
            for cname, methods in classes:
                lines += [f'### `{cname}`', '', symbol_desc(cname, 'class'), '']
                if methods:
                    lines += ['Methoden:', '']
                    for mname, sig in methods:
                        lines.append(f'- `{sig}`: {symbol_desc(mname, "method", cname)}')
                    lines.append('')
        if funcs:
            lines += ['## Funktionen', '']
            for fname, sig in funcs:
                lines.append(f'- `{sig}`: {symbol_desc(fname, "function")}')
            lines.append('')
        return '\n'.join(lines) if lines else '## Code-Inhalt\n\nDiese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.\n'
    if path.suffix in {'.ts', '.tsx', '.js', '.d.ts'}:
        symbols = ts_symbols(path)
        lines: list[str] = []
        public_items = [(n, k) for n, k in symbols if k in {'type', 'interface', 'export', 'component'}]
        if public_items:
            lines += ['## Exporte und oeffentliche Definitionen', '']
            for name, kind in public_items:
                lines.append(f'- `{name}`: {symbol_desc(name, kind)}')
            lines.append('')
        if r in TS_INTERNALS:
            lines += ['## Wichtige interne Routinen', '']
            for name, description in TS_INTERNALS[r]:
                lines.append(f'- `{name}`: {description}')
            lines.append('')
        return '\n'.join(lines) if lines else '## Inhalt\n\nDiese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.\n'
    return '## Inhalt\n\nDiese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.\n'


def write_reference(files: list[Path]) -> None:
    for source in files:
        r = rel(source)
        meta = FILE_NOTES.get(r, {})
        purpose = meta.get('purpose', generic_purpose(source))
        edit = meta.get('edit', generic_edit(source))
        related = meta.get('related', [])
        doc = doc_path(source)
        doc.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f'# `{r}`',
            '',
            f'- Quellpfad: {source_link(doc, source)}',
            f'- Kategorie: `{category(r)}`',
            '',
            '## Aufgabe der Datei',
            '',
            str(purpose),
            '',
            '## Wann du diese Datei bearbeitest',
            '',
            str(edit),
            '',
            symbol_block(source).strip(),
            '',
            '## Abhaengigkeiten',
            '',
        ]
        imports = imports_for(source)
        if imports:
            lines.extend(f'- `{item}`' for item in imports)
        else:
            lines.append('Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.')
        lines += [
            '',
            '## Aenderungshinweise',
            '',
            '- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.',
            '- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.',
            '- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.',
            '',
        ]
        if related:
            lines += ['## Verwandte Dateien', '']
            for item in related:
                target = ROOT / item
                lines.append(f'- {doc_link(doc, target) if target.exists() else item}')
            lines.append('')
        doc.write_text('\n'.join(lines).strip() + '\n', encoding='utf-8')


def write_guides(files: list[Path]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    for name, content in GUIDES.items():
        (DOCS / name).write_text(content.strip() + '\n', encoding='utf-8')

    idx = ['# Referenzindex', '']
    grouped: dict[str, list[Path]] = defaultdict(list)
    for file in files:
        grouped[category(rel(file))].append(file)
    ref_index = DOCS / 'reference' / 'index.md'
    ref_index.parent.mkdir(parents=True, exist_ok=True)
    for group in sorted(grouped):
        idx += [f'## {group}', '']
        for file in grouped[group]:
            idx.append(f'- {doc_link(ref_index, file)}')
        idx.append('')
    ref_index.write_text('\n'.join(idx).strip() + '\n', encoding='utf-8')

    coverage = [
        '# Abdeckung',
        '',
        f'- Dokumentierte Projektdateien: `{len(files)}`',
        f'- Referenzdateien: `{len(list(REF.rglob("*.md")))}`',
        '',
        '## Ausgeschlossene Bereiche',
        '',
        '- `data/`, `debug_tmp/`, `planner_live_check*/`, `ws_debug/`: Laufzeit- und Debug-Artefakte',
        '- `frontend/node_modules/`, `frontend/dist/`: Fremd- und Buildartefakte',
        '- `__pycache__/`, `.pytest_cache/`: Cache-Verzeichnisse',
        '- `.git/`, `release/`, lokale `.env`, `Use_Cases/**/output`, `Use_Cases/**/state`, `*.zip`, `*.exe`, `*.db`, `*.pdf`, `*.litertlm`, `*.xnnpack_cache`, `*.tsbuildinfo`: Artefakte, Binaries oder maschinenlokale Dateien',
        '',
        '## Dokumentierte Dateien',
        '',
    ]
    coverage.extend(f'- `{rel(file)}`' for file in files)
    (DOCS / 'coverage.md').write_text('\n'.join(coverage).strip() + '\n', encoding='utf-8')


def main() -> None:
    files = project_files()
    write_reference(files)
    write_guides(files)
    print(f'Generated docs for {len(files)} files in {DOCS}')


if __name__ == '__main__':
    main()

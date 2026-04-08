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
    'docs',
    'data',
    'debug_tmp',
    'planner_live_check',
    'planner_live_check2',
    'ws_debug',
    '.pytest_cache',
    '__pycache__',
    'frontend/node_modules',
    'frontend/dist',
}

FILE_NOTES = {
    '.env.example': {
        'purpose': 'Beispielkonfiguration fuer das Backend mit API-, Speicher-, Planner- und CORS-Settings.',
        'edit': 'Wenn neue Umgebungsvariablen eingefuehrt oder Standardwerte kommuniziert werden muessen.',
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
        'purpose': 'FastAPI- und WebSocket-Schicht des Backends inklusive Request-Modelle.',
        'edit': 'Wenn API-Endpunkte, Schemafelder oder Live-Streaming erweitert werden.',
        'related': ['src/nova_synesis/services/orchestrator.py', 'frontend/src/lib/apiClient.ts', 'frontend/src/types/api.ts'],
    },
    'src/nova_synesis/cli.py': {
        'purpose': 'CLI-Einstiegspunkt fuer API-Start, Flow-Ausfuehrung und lokale Hilfsaufgaben.',
        'edit': 'Wenn neue CLI-Kommandos oder Startoptionen hinzukommen.',
        'related': ['run-backend.ps1', 'pyproject.toml'],
    },
    'src/nova_synesis/config.py': {
        'purpose': 'Zentrale Laufzeitkonfiguration des Backends.',
        'edit': 'Wenn neue Settings, Standardpfade oder Planner-Optionen benoetigt werden.',
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
        'purpose': 'Lokaler LLM-Planer ueber LiteRT-LM inklusive Prompting, Parsing und Normalisierung.',
        'edit': 'Wenn Planner-Qualitaet, Modellaufruf oder Validierung verbessert werden soll.',
        'related': ['LIT/lit.windows_x86_64.exe', 'LIT/gemma-4-E2B-it.litertlm', 'frontend/src/components/layout/PlannerComposer.tsx'],
    },
    'src/nova_synesis/resources/manager.py': {
        'purpose': 'Verwaltung und Aufloesung registrierter Ressourcen.',
        'edit': 'Wenn Ressourcenallokation oder Fallbacks angepasst werden.',
        'related': ['src/nova_synesis/runtime/engine.py'],
    },
    'src/nova_synesis/runtime/engine.py': {
        'purpose': 'Graph-Ausfuehrungsengine fuer Task- und Flow-Lifecycle.',
        'edit': 'Wenn Ablaufsteuerung, Parallelitaet oder Snapshot-Logik geaendert wird.',
        'related': ['src/nova_synesis/domain/models.py', 'src/nova_synesis/runtime/handlers.py'],
    },
    'src/nova_synesis/runtime/handlers.py': {
        'purpose': 'Eingebaute Handler fuer HTTP, Memory, Messaging, Dateien und Serialisierung.',
        'edit': 'Wenn neue Arbeitsbausteine hinzugefuegt oder bestehende Handler verbessert werden.',
        'related': ['src/nova_synesis/runtime/engine.py', 'frontend/src/components/layout/Sidebar.tsx'],
    },
    'src/nova_synesis/services/orchestrator.py': {
        'purpose': 'Zentrale Service-Fassade des Backends.',
        'edit': 'Wenn Systemkomposition, Registrierungen oder Lifecycle-Management geaendert werden.',
        'related': ['src/nova_synesis/api/app.py', 'src/nova_synesis/runtime/engine.py'],
    },
    'tests/test_orchestrator.py': {
        'purpose': 'Regressionstests fuer Kernfunktionen des Backends.',
        'edit': 'Wenn neue Features abgesichert oder Fehler reproduzierbar getestet werden.',
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
        'purpose': 'Echter API-Client fuer REST und WebSocket-Basis-URLs.',
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
    'TaskExecutor': 'Fuehrt eine einzelne Task inklusive Fehlerbehandlung aus.',
    'FlowExecutor': 'Fuehrt einen gesamten Workflow-Graphen aus.',
    'TaskHandlerRegistry': 'Registry der registrierten Runtime-Handler.',
    'register_default_handlers': 'Registriert alle eingebauten Handler.',
    'SQLiteRepository': 'Persistenzschicht fuer SQLite.',
    'LiteRTPlanner': 'Lokale LLM-Planung ueber LiteRT-LM.',
    'LiteRTPlanner.generate_flow_request': 'Erzeugt aus natuerlicher Sprache einen validierten FlowRequest.',
    'IntentPlanner': 'Regelbasierter Planer fuer strukturierte Intents.',
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

Diese Dokumentation erklaert das System so, dass auch ein Entwickler ohne Vorwissen NOVA-SYNESIS starten, verstehen und gezielt aendern kann.

## Einstieg

1. [Schnellstart](getting-started.md)
2. [Systemueberblick](system-overview.md)
3. [Backend-Laufzeit](backend-runtime.md)
4. [Frontend-Editor](frontend-editor.md)
5. [LLM-Planer und LiteRT](planner-and-lit.md)
6. [Failure Playbook](failure-playbook.md)
7. [Decision Guide](decision-guide.md)
8. [Real World Scenarios](real-world-scenarios.md)
9. [Aenderungsleitfaden](change-workflows.md)
10. [Referenzindex](reference/index.md)
''',
    'getting-started.md': '''# Schnellstart

## Backend

```powershell
./run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

Wichtige URLs:

- `/docs`
- `/health`
- `/planner/status`

## Frontend

`frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8552
```

Dann:

```powershell
cd frontend
npm run dev
```

## Mentales Modell

- Das Frontend baut einen gerichteten Graphen.
- Das Backend speichert ihn als `FlowRequest`.
- Die Runtime fuehrt Knoten gemaess ihren Abhaengigkeiten aus.
- Live-Snapshots fliessen per WebSocket zur UI zurueck.
''',
    'system-overview.md': '''# Systemueberblick

## Schichten

- Domaene: `src/nova_synesis/domain/models.py`
- Planung: `planning/planner.py` und `planning/lit_planner.py`
- Runtime: `runtime/engine.py` und `runtime/handlers.py`
- Persistenz: `persistence/sqlite_repository.py`
- API: `api/app.py`
- UI: `frontend/src/`

## Hauptdatenfluss

1. Graph im Frontend erstellen oder generieren
2. `toFlowRequest()` erzeugt das Backend-Schema
3. `POST /flows` speichert den Graphen
4. `POST /flows/{id}/run` startet die Ausfuehrung
5. `FlowExecutor` verarbeitet den Graphen
6. `/ws/flows/{flow_id}` uebertraegt Snapshots an die UI
''',
    'backend-runtime.md': '''# Backend-Laufzeit

Die Backend-Laufzeit wird durch `OrchestratorService` zusammengesetzt. Er besitzt Repository, Speicher, Ressourcenmanager, Planner, Handler-Registry und Execution-Engine.

Wichtige Regel: Laufzeitveraenderungen betreffen fast immer gleichzeitig Domaene, Engine und API-Snapshot.
''',
    'frontend-editor.md': '''# Frontend-Editor

Die UI besteht aus `App.tsx`, dem Zustand-Store `useFlowStore.ts`, der Zeichenflaeche `FlowCanvas.tsx`, der linken `Sidebar.tsx`, dem `InspectorPanel.tsx` und der `TopBar.tsx`.

Die kritischste Integrationsdatei ist `frontend/src/lib/flowSerialization.ts`. Wenn dort Felder falsch gemappt werden, speichert die UI keinen korrekten Backend-Flow.
''',
    'planner-and-lit.md': '''# LLM-Planer und LiteRT

Der Planner erzeugt keine Mock-Graphen. Er nutzt die lokale `lit`-Binary und das Gemma-Modell im `LIT/`-Ordner, extrahiert JSON und validiert das Resultat gegen den echten Backend-Katalog.

Wenn du Planner-Qualitaet verbesserst, arbeite primär in `src/nova_synesis/planning/lit_planner.py`.
''',
    'failure-playbook.md': '''# Failure Playbook

Diese Seite beschreibt die realen Stoerungsbilder des Systems. Ziel ist nicht nur Fehler zu benennen, sondern eine belastbare Reihenfolge fuer Diagnose und Behebung zu geben.

## Triage-Reihenfolge

1. Zuerst unterscheiden: Planner-Problem, Live-Transportproblem oder echte Runtime-Stoerung.
2. Immer den echten Snapshot ueber `GET /flows/{flow_id}` lesen.
3. Erst danach UI, WebSocket oder Planner-Oberflaeche beurteilen.

## 1. Planner liefert ungueltiges JSON

### Woran du es erkennst

- `POST /planner/generate-flow` antwortet mit Fehler
- im Frontend erscheint keine neue Graphstruktur
- typische Backend-Meldungen:
  - `Planner returned invalid JSON`
  - `Planner response does not contain a JSON object`
  - `Planner response contains an incomplete JSON object`

### Was im Code passiert

- `LiteRTPlanner._invoke_model()` ruft die lokale `lit`-Binary auf
- `LiteRTPlanner._parse_model_output()` extrahiert den JSON-Anteil
- `LiteRTPlanner._normalize_flow_request()` validiert das Resultat gegen echte Handler, Ressourcen, Agenten und Memory-Systeme

### Typische Ursachen

- das Modell schreibt Text ausserhalb des JSON
- das JSON ist syntaktisch unvollstaendig
- das Modell erfindet Handler oder Ressourcen
- `max_nodes` ist zu hoch und das Modell driftet
- Binary- oder Modellpfad sind falsch

### Sofortmassnahmen

1. `GET /planner/status` pruefen
2. den Prompt kuerzer und restriktiver formulieren
3. `max_nodes` senken
4. sicherstellen, dass benoetigte Memory-IDs, Agenten und Ressourcen wirklich registriert sind
5. bei wiederholtem Fehler den Flow manuell im Editor bauen

### Dauerhafte Korrektur

- Prompt-Kontrakt in `src/nova_synesis/planning/lit_planner.py` schaerfen
- Normalisierung erweitern, wenn das Modell wiederholt denselben plausiblen, aber falschen Vertrag produziert
- nur echte Handler in den Planner-Katalog aufnehmen

## 2. WebSocket bricht waehrend der Execution ab

### Woran du es erkennst

- die Topbar zeigt `Offline`
- Live-Status friert ein oder aktualisiert sich nur stoerend langsam
- der Flow laeuft im Backend oft trotzdem weiter

### Was das System bereits fuer dich macht

`frontend/src/hooks/useFlowLiveUpdates.ts` faellt automatisch auf Polling gegen `GET /flows/{flow_id}` zurueck. Das bedeutet: Die UI bleibt nutzbar, auch wenn der Socket weg ist.

### Typische Ursachen

- Backend wurde neu gestartet
- Port oder Host in `frontend/.env` stimmen nicht
- Proxy oder Netzwerkumgebung blockieren WebSocket-Upgrades
- der Benutzer ist noch auf einem alten `flow_id`

### Sofortmassnahmen

1. `GET /flows/{flow_id}` direkt pruefen
2. `frontend/.env` gegen die echte Backend-Adresse pruefen
3. unterscheiden: ist nur `/ws/flows/{flow_id}` defekt oder auch REST?
4. wenn REST geht, die Ausfuehrung nicht abbrechen, sondern Snapshot weiter per Polling beobachten

### Dauerhafte Korrektur

- gleiche Host-/Port-Konfiguration fuer REST und WebSocket erzwingen
- bei Reverse Proxy WebSocket-Support explizit konfigurieren
- Polling-Fallback als Sicherheitsnetz beibehalten

## 3. Resource haengt oder laeuft in Timeout / Sattlauf

### Woran du es erkennst

- eine oder mehrere Nodes bleiben lange auf `RUNNING`
- der Flow macht keine sichtbaren Fortschritte, ohne sofort auf `FAILED` zu springen
- einzelne Ressourcen stehen auf `BUSY` oder `DOWN`

### Wichtige technische Besonderheit dieses Projekts

Die Engine ruft `ResourceManager.acquire_many()` ohne globalen Timeout auf. Das heisst:

- ist eine Ressource `DOWN`, scheitert die Reservierung schnell
- ist eine Ressource nur voll ausgelastet, kann eine Task auf Freigabe warten
- handler-spezifische Timeouts, etwa `http_request.timeout_s`, greifen nur innerhalb des Handlers, nicht waehrend der Ressourcenreservierung selbst

### Typische Ursachen

- Resource-Kapazitaet (`metadata.capacity`) ist zu klein fuer die Flow-Konkurrenz
- externe API oder Dateiressource blockiert
- eine vorherige Task haelt die Ressource laenger als erwartet
- der Flow nutzt feste `required_resource_ids`, obwohl eigentlich ein Typ-Fallback sinnvoll waere

### Sofortmassnahmen

1. `GET /flows/{flow_id}` lesen und die auf `RUNNING` stehenden Nodes identifizieren
2. `GET /resources` und gegebenenfalls `resource_health_check` verwenden
3. pruefen, ob `max_concurrency` oder die Ressourcenkapazitaet zu aggressiv eingestellt sind
4. bei HTTP-Aufrufen explizit `timeout_s` setzen
5. wenn moeglich auf `required_resource_types` plus `FALLBACK_RESOURCE` umstellen

### Dauerhafte Korrektur

- Kapazitaet der Ressource realistisch modellieren
- konkurrierende Flows oder Node-Level-Konkurrenz reduzieren
- fuer fragilen Infrastrukturzugriff `RETRY` oder `FALLBACK_RESOURCE` statt `FAIL_FAST` nutzen
- lang laufende Seiteneffekte in kleinere, kontrollierbare Nodes zerlegen

## 4. Flow bleibt auf `RUNNING` stehen

### Woran du es erkennst

- `GET /flows/{flow_id}` zeigt dauerhaft `state = RUNNING`
- dieselben Nodes bleiben ueber mehrere Snapshots hinweg `RUNNING`
- `completed_nodes` waechst nicht mehr

### Was das in diesem System meist bedeutet

Das ist haeufig kein Graph-Deadlock, sondern eine laufende Task, die nie sauber zurueckkehrt:

- Handler wartet auf externen Dienst
- Ressource wartet auf Freigabe
- externer Endpunkt antwortet nie innerhalb eines sinnvollen Timeouts
- die UI hat den letzten erfolgreichen Zustand gezeigt und der Nutzer verwechselt das mit einem eigentlichen Engine-Stall

### Sofortmassnahmen

1. mehrere Snapshots hintereinander vergleichen
2. den oder die `RUNNING`-Nodes identifizieren
3. Handlervertrag des betroffenen Nodes pruefen
4. bei `http_request` ein sinnvolles `timeout_s` setzen
5. pruefen, ob Ressource oder Kommunikationsziel erreichbar sind

### Dauerhafte Korrektur

- fuer externe I/O immer explizite Timeouts und Retries modellieren
- Flows nicht mit ungebremster Parallelitaet gegen knappe Ressourcen fahren
- problematische Langlaeufer erst manuell als Einzel-Flow testen

## 5. Graph-Deadlock oder logisch blockierter Flow

Wichtig: Wenn keine Node mehr startbar ist und trotzdem noch `pending` existiert, setzt `FlowExecutor.run_flow()` den Flow auf `FAILED` und schreibt `deadlock_nodes` in die Metadaten.

### Woran du es erkennst

- `GET /flows/{flow_id}` zeigt `state = FAILED`
- `metadata.deadlock_nodes` ist gesetzt
- `blocked_nodes` enthaelt Knoten, deren Bedingungen nie wahr wurden

### Typische Ursachen

- zyklische Abhaengigkeiten
- alle Kantenbedingungen sind formal ausgewertet, aber keine fuehrt zu einem startbaren Node
- ein Bedingungsausdruck referenziert unbekannte Symbole
- es existiert kein echter Startknoten

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

### Dauerhafte Korrektur

- Graph strikt als DAG modellieren
- Branching nur fuer fachliche Entscheidungen verwenden
- komplexe Vorbedingungen lieber als eigenen vorbereitenden Node modellieren

## 6. Handler wirft Exception

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

### Was die Engine dann macht

- sie erzeugt ein `ErrorEvent`
- je nach `rollback_strategy` folgt:
  - `FAIL_FAST`
  - `RETRY`
  - `COMPENSATE`
  - `FALLBACK_RESOURCE`
- bei `FALLBACK_RESOURCE` versucht `ResourceManager.find_fallback_resources()` einen Ersatz gleicher Art

### Sofortmassnahmen

1. `failed_nodes` im Snapshot lesen
2. Input des Nodes mit dem echten Handlervertrag vergleichen
3. Ressourcen, Agenten und Memory-Systeme pruefen
4. `retry_policy` und `rollback_strategy` auf Infrastrukturrealitaet abstimmen

### Dauerhafte Korrektur

- Handler klein und vertragsscharf halten
- `validator_rules` bewusst einsetzen
- bei externen Diensten eher `RETRY` oder `FALLBACK_RESOURCE` als `FAIL_FAST` verwenden

## Welche Daten du vor tieferer Analyse sammeln solltest

- `flow_id`
- kompletter Snapshot aus `GET /flows/{flow_id}`
- alle aktuell `RUNNING`, `FAILED` und `blocked` Nodes
- Handlername und Input der auffaelligen Node
- verwendete Ressourcen, Agenten und Memory-IDs
- bei Planner-Problemen: Prompt und `max_nodes`
''',
    'decision-guide.md': '''# Decision Guide

Diese Seite dokumentiert keine Syntax, sondern Entscheidungslogik. Genau dieses Wissen fehlt oft, wenn ein System zwar sauber gebaut, aber noch nicht betriebssicher uebergeben wurde.

## 1. Warum dieser Planner der Standard ist

Der lokale LiteRT-Planer ist hier die richtige Standardwahl, weil er vier Anforderungen gleichzeitig erfuellt:

- lokal und ohne Cloud-Abhaengigkeit
- auf den echten Handler-, Agenten- und Ressourcenkatalog begrenzt
- normalisiert auf das reale `FlowRequest`-Schema
- fuer manuelle Nachbearbeitung im visuellen Editor geeignet

Nutze den Planner, wenn:

- du einen Workflow schnell aus einer fachlichen Beschreibung ableiten willst
- du eine erste Graph-Struktur brauchst
- du vorhandene Flows mit neuen Ideen erweitern willst

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

Praktische Regel:

- `http_request` mit neuen optionalen Headern: bestehenden Handler erweitern
- Dateischreiben plus Upload zu einem Fremddienst: neuer Handler

Vermeide absichtlich einen Mega-Handler, der viele unverbundene Modi mit einem einzigen Namen abdeckt. Solche Handler sind schwer zu testen, schwer zu dokumentieren und fuehren im Planner schnell zu unsauberen Flows.

## 3. Flow, einzelne Task oder Agent?

### Verwende einen Flow, wenn

- Reihenfolge wichtig ist
- Verzweigungen oder Bedingungen existieren
- mehrere Nebenwirkungen koordiniert werden muessen
- Fehlerbehandlung ueber mehrere Schritte sichtbar sein soll

### Verwende nur eine einzelne Task, wenn

- genau ein Arbeitsschritt benoetigt wird
- keine Verzweigung und keine nachgelagerten Schritte existieren

### Verwende einen Agenten, wenn

- eine Task bewusst an einen bestimmten Faehigkeitstraeger gebunden sein soll
- Kommunikationsadapter benoetigt werden
- Capability-Gating fachlich wichtig ist

Wichtig:

Ein Agent ersetzt keinen Flow. Der Flow modelliert den Prozess. Der Agent modelliert, wer eine Task uebernehmen darf oder wie eine Task in ein Kommunikationsnetz eingebettet ist.

Viele sinnvolle Flows brauchen ueberhaupt keinen Agenten. Ein deterministischer `http_request -> memory_store`-Flow ist dafuer das beste Beispiel.

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

Nutze `required_resource_ids`, wenn:

- exakt ein bestimmter Endpunkt oder ein bestimmtes System getroffen werden muss
- Compliance, Umgebung oder Datenlokalitaet fest vorgegeben sind

Nutze `required_resource_types`, wenn:

- jeder passende Vertreter einer Kategorie ausreicht
- Fallback zwischen Ressourcen gleicher Art sinnvoll ist

Praxis:

- produktive Kern-API mit fester URL: konkrete Resource-ID
- beliebige freie GPU oder alternatives API-Replica: Resource-Type

## 6. Welche Rollback-Strategie ist die richtige?

- `FAIL_FAST`: bei irreversiblen Fehlern oder wenn Folgeschritte keinen Sinn mehr ergeben
- `RETRY`: bei transienten Netz- oder Dienstfehlern
- `FALLBACK_RESOURCE`: wenn mehrere Ressourcen gleicher Art vorhanden sind
- `COMPENSATE`: wenn ein Fehler nach einer Nebenwirkung aktiv bereinigt werden muss

Die Standardwahl fuer reine Infrastrukturprobleme ist meist `RETRY` oder `FALLBACK_RESOURCE`, nicht `COMPENSATE`.

## 7. Wann soll eine Condition auf eine Edge?

Eine Edge-Condition ist richtig, wenn du einen fachlichen Branch modellierst:

- Erfolgspfad vs Fehlerpfad
- weitere Verarbeitung nur bei gueltigem Ergebnis
- optionale Folgeaktionen

Eine Edge-Condition ist falsch, wenn du damit versuchst, Daten umzubauen oder fehlende Vorverarbeitung zu kompensieren. Dann fehlt meist ein eigener Node.
''',
    'real-world-scenarios.md': '''# Real World Scenarios

Diese Seite enthaelt bewusst nur drei End-to-End-Beispiele. Ziel ist nicht Vollstaendigkeit, sondern sichere Anwendbarkeit.

## Szenario 1: Einfacher Flow "API abrufen und Ergebnis merken"

### Ziel

Remote-Daten laden und in einem vorhandenen Memory-System speichern.

### Voraussetzungen

- mindestens eine API-Ressource ist registriert
- ein Memory-System mit passender `memory_id` existiert

### Ablauf

1. API-Ressource pruefen
2. Daten abrufen
3. Antwort bei Erfolg im Memory sichern

### Beispielstruktur

```json
{
  "nodes": [
    {
      "node_id": "check-api",
      "handler_name": "resource_health_check",
      "input": { "resource_ids": [1] },
      "dependencies": []
    },
    {
      "node_id": "fetch-data",
      "handler_name": "http_request",
      "input": { "method": "GET", "timeout_s": 10 },
      "required_resource_ids": [1],
      "validator_rules": {
        "required_keys": ["status_code", "body"],
        "expression": "result['status_code'] < 400"
      },
      "dependencies": ["check-api"],
      "conditions": { "check-api": "True" }
    },
    {
      "node_id": "store-result",
      "handler_name": "memory_store",
      "input": {
        "memory_id": "working-memory",
        "key": "latest-api-result",
        "value": "{{ results['fetch-data']['body'] }}"
      },
      "dependencies": ["fetch-data"],
      "conditions": { "fetch-data": "source_result['status_code'] < 400" }
    }
  ],
  "edges": [
    { "from_node": "check-api", "to_node": "fetch-data", "condition": "True" },
    { "from_node": "fetch-data", "to_node": "store-result", "condition": "source_result['status_code'] < 400" }
  ]
}
```

### Warum dieses Beispiel wichtig ist

- nutzt nur reale Built-in-Handler
- zeigt Resource-Einsatz, Validierung und Template-Zugriff
- ist klein genug, um die komplette Lebenslinie des Systems zu verstehen

## Szenario 2: Komplexer Flow mit Branching "Erfolgspfad und Fehlerpfad trennen"

### Ziel

Eine API-Antwort soll unterschiedlich weiterverarbeitet werden, je nachdem ob der HTTP-Status erfolgreich ist oder nicht.

### Ablauf

1. Daten abrufen
2. bei Erfolg eine Zusammenfassung schreiben und speichern
3. bei Fehler einen Fehlerbericht rendern und separat persistieren

### Beispielstruktur

```json
{
  "nodes": [
    {
      "node_id": "fetch-data",
      "handler_name": "http_request",
      "input": { "url": "https://example.invalid/data", "method": "GET", "timeout_s": 10 },
      "dependencies": []
    },
    {
      "node_id": "render-success",
      "handler_name": "template_render",
      "input": {
        "template": "Fetch succeeded with status {status}",
        "values": { "status": "{{ results['fetch-data']['status_code'] }}" }
      },
      "dependencies": ["fetch-data"],
      "conditions": { "fetch-data": "source_result['status_code'] < 400" }
    },
    {
      "node_id": "store-success",
      "handler_name": "memory_store",
      "input": {
        "memory_id": "working-memory",
        "key": "last-success-summary",
        "value": "{{ results['render-success']['rendered'] }}"
      },
      "dependencies": ["render-success"],
      "conditions": { "render-success": "True" }
    },
    {
      "node_id": "render-error",
      "handler_name": "template_render",
      "input": {
        "template": "Fetch failed with status {status}",
        "values": { "status": "{{ results['fetch-data']['status_code'] }}" }
      },
      "dependencies": ["fetch-data"],
      "conditions": { "fetch-data": "source_result['status_code'] >= 400" }
    },
    {
      "node_id": "write-error-report",
      "handler_name": "write_file",
      "input": {
        "path": "reports/fetch-error.txt",
        "content": "{{ results['render-error']['rendered'] }}",
        "append": false
      },
      "dependencies": ["render-error"],
      "conditions": { "render-error": "True" }
    }
  ],
  "edges": [
    { "from_node": "fetch-data", "to_node": "render-success", "condition": "source_result['status_code'] < 400" },
    { "from_node": "render-success", "to_node": "store-success", "condition": "True" },
    { "from_node": "fetch-data", "to_node": "render-error", "condition": "source_result['status_code'] >= 400" },
    { "from_node": "render-error", "to_node": "write-error-report", "condition": "True" }
  ]
}
```

### Warum dieses Beispiel wichtig ist

- zeigt echtes Branching statt linearer Demo-Flows
- benutzt Kantenbedingungen korrekt fuer fachliche Entscheidungen
- trennt Erfolgspfad und Fehlerpfad sauber

## Szenario 3: Fehler plus Retry / Fallback "API-Replica uebernimmt bei Ausfall"

### Ziel

Eine Anfrage soll nicht sofort scheitern, wenn die bevorzugte API-Ressource nicht nutzbar ist.

### Voraussetzungen

- mindestens zwei Ressourcen vom Typ `API` sind registriert
- die Node verwendet `rollback_strategy = FALLBACK_RESOURCE`

### Ablauf

1. Daten ueber eine API-Ressource abrufen
2. bei transientem Fehler erneut versuchen
3. wenn noetig auf eine andere API-Ressource gleicher Art wechseln
4. nur bei Erfolg das Ergebnis speichern

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
      },
      "dependencies": []
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
    { "from_node": "fetch-primary-or-fallback", "to_node": "store-result", "condition": "source_result['status_code'] < 400" }
  ]
}
```

### Warum dieses Beispiel wichtig ist

- zeigt den Unterschied zwischen Retry und Fallback
- bildet ein realistisches Produktionsmuster fuer fragile Infrastruktur ab
- ist direkt mit den vorhandenen Built-in-Handlern und Runtime-Regeln vereinbar
''',
    'change-workflows.md': '''# Aenderungsleitfaden

## Neuer Handler

1. Handler in `runtime/handlers.py` implementieren und registrieren
2. Tests erweitern
3. UI laedt den Handler automatisch ueber `/handlers`

## Neues Node-Feld

1. Backend-Schema in `api/app.py`
2. TypeScript-Typen in `frontend/src/types/api.ts`
3. Serialisierung in `frontend/src/lib/flowSerialization.ts`
4. Inspector in `frontend/src/components/layout/InspectorPanel.tsx`
''',
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def excluded(path: Path) -> bool:
    r = rel(path)
    parts = set(path.relative_to(ROOT).parts)
    if '.pytest_cache' in parts or '__pycache__' in parts:
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

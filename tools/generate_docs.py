from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'dokumentation'
REF = DOCS / 'reference'

EXCLUDED = {
    '.git',
    'billing',
    'dokumentation',
    'docs',
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
    'test.csv',
}

FILE_NOTES = {
    '.env.example': {
        'purpose': 'Beispielkonfiguration fuer Backend, Planner, CORS und die semantische Sicherheitsrichtlinie.',
        'edit': 'Wenn neue Umgebungsvariablen eingefuehrt, Security-Grenzen angepasst oder Standardwerte kommuniziert werden muessen.',
        'related': ['src/nova_synesis/config.py', 'README.md'],
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
        'related': ['run-backend.ps1', 'frontend/package.json', 'tools/build_web_docs.py'],
    },
    'Schnellstart.md': {
        'purpose': 'Knappe operative Startanleitung fuer Backend, Frontend, Use Cases und Planner-Beispiele.',
        'edit': 'Wenn sich Startports, Setup-Skripte, Use-Case-Ablauf oder Planner-Voraussetzungen aendern.',
        'related': ['README.md', 'Use_Cases/README.md', 'Use_Cases/LLM_Planer/README.md'],
    },
    'fazit.md': {
        'purpose': 'Verdichtete architektonische Schlussfolgerung ueber den Sicherheits- und Betriebsansatz von NOVA-SYNESIS.',
        'edit': 'Wenn sich die Kernargumentation des Systems oder die sicherheitsrelevanten Architekturprinzipien veraendern.',
        'related': ['Fachartikel_NOVA-SYNESIS.md', 'dokumentation/security-and-policy.md', 'README.md'],
    },
    'Fachartikel_NOVA-SYNESIS.md': {
        'purpose': 'Ausfuehrlicher Fachartikel zur Einordnung von NOVA-SYNESIS als kontrollierte Agentenplattform.',
        'edit': 'Wenn die strategische, fachliche oder architektonische Darstellung fuer externe Leser aktualisiert werden muss.',
        'related': ['fazit.md', 'dokumentation/README.md', 'dokumentation/system-overview.md'],
    },
    'run-backend.ps1': {
        'purpose': 'Empfohlenes Windows-Startskript fuer das Backend.',
        'edit': 'Wenn der lokale Backend-Start fuer Entwickler angepasst werden soll.',
        'related': ['src/nova_synesis/cli.py', 'run-backend.cmd'],
    },
    'uml_V3.mmd': {
        'purpose': 'Mermaid-Quelle des Architekturdiagramms.',
        'edit': 'Wenn die dokumentierte Zielarchitektur angepasst werden soll.',
        'related': ['uml.html', 'README.md'],
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
        'purpose': 'FastAPI- und WebSocket-Schicht des Backends inklusive Request-Modelle, Flow-Versionen, HITL-Resume, Metrics und Live-Streaming.',
        'edit': 'Wenn API-Endpunkte, Schemafelder, Versionssteuerung, Sicherheitspruefung, HITL oder Live-Streaming erweitert werden.',
        'related': ['src/nova_synesis/services/orchestrator.py', 'frontend/src/lib/apiClient.ts', 'frontend/src/types/api.ts'],
    },
    'src/nova_synesis/cli.py': {
        'purpose': 'CLI-Einstiegspunkt fuer API-Start, Flow-Ausfuehrung und lokale Hilfsaufgaben.',
        'edit': 'Wenn neue CLI-Kommandos oder Startoptionen hinzukommen.',
        'related': ['run-backend.ps1', 'pyproject.toml'],
    },
    'src/nova_synesis/config.py': {
        'purpose': 'Zentrale Laufzeitkonfiguration des Backends inklusive LiteRT-, Semantic-Firewall- und RBAC-Settings.',
        'edit': 'Wenn neue Settings, Standardpfade, Planner-Optionen, Identity-Header oder Policy-Grenzen benoetigt werden.',
        'related': ['.env.example', 'src/nova_synesis/cli.py'],
    },
    'src/nova_synesis/domain/models.py': {
        'purpose': 'Kern-Domaenenmodell mit Agenten, Ressourcen, Tasks, Human-Input-Zustaenden, Versionen und ExecutionFlow.',
        'edit': 'Wenn das fachliche Laufzeitmodell, Statusuebergaenge oder vertragliche Task-Felder des Systems veraendert werden.',
        'related': ['src/nova_synesis/runtime/engine.py', 'src/nova_synesis/services/orchestrator.py'],
    },
    'src/nova_synesis/memory/systems.py': {
        'purpose': 'Implementierungen fuer Kurzzeit-, Langzeit- und Vektor-Speicher.',
        'edit': 'Wenn Speicherverhalten, Suche oder Persistenz geaendert werden.',
        'related': ['src/nova_synesis/runtime/handlers.py', 'src/nova_synesis/services/orchestrator.py'],
    },
    'src/nova_synesis/persistence/sqlite_repository.py': {
        'purpose': 'SQLite-Persistenzschicht fuer Flow-Container, Flow-Versionen, Ausfuehrungen, Katalogobjekte und Metriken.',
        'edit': 'Wenn Datenbankstruktur, Versionierung, gespeicherte Felder oder Laufzeitmetriken angepasst werden.',
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
        'purpose': 'Graph-Ausfuehrungsengine fuer Task- und Flow-Lifecycle inklusive WAITING_FOR_INPUT, Template-Aufloesung, Telemetrie und Live-Snapshots.',
        'edit': 'Wenn Ablaufsteuerung, Parallelitaet, Resume-Logik, Template-Kontext, Telemetrie oder Snapshot-Logik geaendert wird.',
        'related': ['src/nova_synesis/domain/models.py', 'src/nova_synesis/runtime/handlers.py'],
    },
    'src/nova_synesis/runtime/handlers.py': {
        'purpose': 'Eingebaute Handler fuer HTTP, Memory, Messaging, Dateien, Human Input, Sub-Flows und lokale LLM-Textarbeit.',
        'edit': 'Wenn neue Arbeitsbausteine hinzugefuegt, HITL/Sub-Flow-Vertraege erweitert oder bestehende Handler verbessert werden.',
        'related': ['src/nova_synesis/runtime/engine.py', 'frontend/src/components/layout/Sidebar.tsx'],
    },
    'src/nova_synesis/services/orchestrator.py': {
        'purpose': 'Zentrale Service-Fassade des Backends inklusive Security-Gates, Flow-Versionierung, HITL-Resume, Planner-Katalog, RBAC und Lifecycle-Management.',
        'edit': 'Wenn Systemkomposition, Registrierungen, Versionssteuerung, Policy-Durchsetzung, Metriken oder Lifecycle-Management geaendert werden.',
        'related': ['src/nova_synesis/api/app.py', 'src/nova_synesis/runtime/engine.py'],
    },
    'tests/test_orchestrator.py': {
        'purpose': 'Regressionstests fuer Backend, Planner, WebSocket-Livebetrieb und Semantic-Firewall.',
        'edit': 'Wenn neue Features abgesichert, Sicherheitsregeln erweitert oder Fehler reproduzierbar getestet werden.',
        'related': ['src/nova_synesis/services/orchestrator.py', 'src/nova_synesis/api/app.py'],
    },
    'frontend/src/App.tsx': {
        'purpose': 'Root-Komponente der UI mit Layout, Planner, Versionen, Analytics, Save/Run und Live-Sync.',
        'edit': 'Wenn globale Frontend-Aktionen, Versionierung, Analytics oder das Seitenlayout geaendert werden.',
        'related': ['frontend/src/store/useFlowStore.ts', 'frontend/src/components/layout/TopBar.tsx'],
    },
    'frontend/src/types/api.ts': {
        'purpose': 'Gemeinsame TypeScript-Schemata fuer API, Versions-Snapshots, HITL-Vertraege, Metriken und Editorgraph.',
        'edit': 'Wenn Backend-Vertraege, UI-Datentypen oder Laufzeitstatus erweitert werden.',
        'related': ['src/nova_synesis/api/app.py', 'frontend/src/lib/flowSerialization.ts'],
    },
    'frontend/src/lib/apiClient.ts': {
        'purpose': 'Echter API-Client fuer REST, Flow-Validierung, Versionen, HITL-Resume, Analytics, Planner und WebSocket-Basis-URLs.',
        'edit': 'Wenn neue Backend-Endpunkte im Frontend angebunden oder bestehende Vertrage geaendert werden.',
        'related': ['src/nova_synesis/api/app.py', 'frontend/src/types/api.ts'],
    },
    'frontend/src/lib/flowSerialization.ts': {
        'purpose': 'Uebersetzung zwischen React-Flow und echtem Backend-Flow-Schema.',
        'edit': 'Wenn Node-Felder oder Flow-Schema geaendert werden.',
        'related': ['frontend/src/types/api.ts', 'src/nova_synesis/api/app.py'],
    },
    'frontend/src/store/useFlowStore.ts': {
        'purpose': 'Zustand-Store fuer Graph, Auswahl, Versionen, Undo/Redo und Laufzeitstatus.',
        'edit': 'Wenn Editorverhalten, Versionszustand oder Snapshot-Uebernahme angepasst werden.',
        'related': ['frontend/src/App.tsx', 'frontend/src/hooks/useFlowLiveUpdates.ts'],
    },
    'frontend/src/components/layout/InspectorPanel.tsx': {
        'purpose': 'Node- und Edge-Inspector fuer bearbeitbare Eigenschaften, manuelle Freigaben, HITL-Resume und lokale LLM-Briefvorschauen.',
        'edit': 'Wenn weitere konfigurierbare Felder, Approval-/Resume-Aktionen oder interaktive Vorschaufunktionen in der UI auftauchen sollen.',
        'related': ['frontend/src/store/useFlowStore.ts', 'frontend/src/components/common/JsonEditor.tsx', 'src/nova_synesis/api/app.py'],
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
        'purpose': 'Globale Aktionsleiste fuer Save, Run, Planner, Versionen, Analytics, Import und Export.',
        'edit': 'Wenn globale Bedienaktionen, Versionsumschaltung oder Statusanzeigen geaendert werden.',
        'related': ['frontend/src/App.tsx', 'frontend/src/components/common/StatusBadge.tsx'],
    },
    'frontend/src/components/layout/AnalyticsPanel.tsx': {
        'purpose': 'Kompakte Betriebsansicht fuer aggregierte Flow- und Handler-Metriken direkt in der Web-UI.',
        'edit': 'Wenn Analytics-Kennzahlen, Darstellung oder Drilldowns fuer Betreiber erweitert werden sollen.',
        'related': ['frontend/src/App.tsx', 'frontend/src/lib/apiClient.ts', 'src/nova_synesis/api/app.py'],
    },
    'tools/build_web_docs.py': {
        'purpose': 'Generiert aus dem dokumentation-Ordner eine statische HTML-Dokumentationsseite mit Navigation, Suche und Source-Ansichten.',
        'edit': 'Wenn Layout, Suchlogik, Seitenrouting oder die statische Web-Doku erweitert werden sollen.',
        'related': ['tools/generate_docs.py', 'README.md', 'pyproject.toml'],
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
    'HumanInputRequest': 'Beschreibt eine laufende HITL-Eingabeanforderung inklusive Formularschema, Rolle und Timeout-Kontext.',
    'HumanInputResponse': 'Serialisiert die Antwort eines Operators auf eine offene HITL-Anfrage.',
    'FlowVersionRecord': 'Persistierte Version eines Flow-Containers inklusive Snapshot, Nummer und Metadaten.',
    'TaskExecutor': 'Fuehrt eine einzelne Task inklusive Fehlerbehandlung aus.',
    'FlowExecutor': 'Fuehrt einen gesamten Workflow-Graphen aus.',
    'Task.wait_for_input': 'Markiert eine Task als pausiert und haengt eine Human-Input-Anforderung an den Node.',
    'Task.resume_with_input': 'Nimmt eine Benutzerantwort auf und ueberfuehrt die Task wieder in einen ausfuehrbaren Zustand.',
    'TaskExecution.wait_for_input': 'Persistiert den WAITING_FOR_INPUT-Zustand fuer einen einzelnen Ausfuehrungsversuch.',
    'TaskHandlerRegistry': 'Registry der registrierten Runtime-Handler.',
    'TaskHandlerRegistry.issue_certificate': 'Erzeugt ein digitales Zertifikat fuer einen bereits registrierten Handler.',
    'register_default_handlers': 'Registriert alle eingebauten Handler.',
    'HumanInputRequiredError': 'Signalisiert der Engine, dass ein Handler kontrolliert auf menschliche Eingabe warten muss.',
    'human_input_request_handler': 'Erzeugt eine offene HITL-Anfrage und stoppt den aktuellen Node bis zur Resume-Antwort.',
    'execute_subflow_handler': 'Startet einen anderen gespeicherten Flow als Child-Ausfuehrung und mappt dessen Ergebnis zurueck.',
    'read_file_handler': 'Liest lokale Dateien aus dem Arbeitsverzeichnis und stellt ihren Inhalt fuer nachgelagerte Nodes bereit.',
    'write_file_handler': 'Schreibt Text- oder JSON-Inhalte in lokale Dateien innerhalb des Arbeitsverzeichnisses.',
    'local_llm_text_handler': 'Erzeugt oder analysiert Text lokal ueber LiteRT und kombiniert dabei Benutzerprompt und Upstream-Daten zu einer finalen Antwort.',
    'SQLiteRepository': 'Persistenzschicht fuer SQLite.',
    'SQLiteRepository.create_flow_version': 'Legt eine neue unveraenderliche Version fuer einen bestehenden Flow-Container an.',
    'SQLiteRepository.list_flow_versions': 'Liefert die bekannten Versionen eines Flow-Containers fuer API und UI.',
    'SQLiteRepository.activate_flow_version': 'Setzt die aktive Version eines Flow-Containers um, ohne alte Versionen zu verlieren.',
    'SQLiteRepository.save_execution_metric': 'Persistiert verdichtete Laufzeitdaten fuer Handler- und Flow-Analytics.',
    'LiteRTPlanner': 'Lokale LLM-Planung ueber LiteRT-LM.',
    'LiteRTPlanner.generate_text': 'Erzeugt reinen Modelltext ueber den lokalen LiteRT-Stack ausserhalb des Graph-Planungsmodus.',
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
    'OrchestratorService.save_flow_version': 'Persistiert aus dem aktuellen Editorgraphen eine neue Version zu einem bestehenden Flow-Container.',
    'OrchestratorService.list_flow_versions': 'Liefert die Versionstabelle eines Flows fuer UI und API.',
    'OrchestratorService.activate_flow_version': 'Aktiviert eine vorhandene Version fuer spaetere Runs und Ladeoperationen.',
    'OrchestratorService.get_node_input_request': 'Liest die offene HITL-Anforderung eines WAITING_FOR_INPUT-Nodes aus.',
    'OrchestratorService.resume_flow_node': 'Nimmt Operator-Eingaben entgegen und setzt einen pausierten Node fort.',
    'OrchestratorService.summarize_execution_metrics': 'Aggregiert Handler- und Flow-Metriken fuer das Analytics-Panel.',
    'OrchestratorService.run_subflow': 'Fuehrt einen Child-Flow isoliert gegen eine gepinnte Version aus.',
    'FlowCanvas': 'React-Flow-Leinwand des Editors.',
    'TaskNode': 'Custom Node fuer einzelne Tasks im Canvas.',
    'InspectorPanel': 'Eigenschaftseditor fuer Nodes und Edges.',
    'AnalyticsPanel': 'Frontend-Modal fuer aggregierte Flow- und Handlermetriken.',
    'preview_accounts_receivable_letter_draft': 'Erzeugt serverseitig einen einzelnen Beispielbrief fuer den Forderungs-Workflow, ohne den ganzen Flow auszufuehren.',
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
        ('patchNodeInputObject', 'Aktualisiert gezielt Felder innerhalb des Node-Inputs, ohne das restliche Objekt zu verlieren.'),
        ('findReceivableExtractNode', 'Findet den zum Forderungs-Use-Case gehoerigen Extract-Node fuer serverseitige Vorschaulaufe.'),
        ('splitCsv', 'Konvertiert komma-separierte Texte in Stringlisten.'),
        ('asObject', 'Normalisiert unbekannte Werte zu einem sicheren Objekt.'),
        ('asNodeInputObject', 'Normalisiert den Node-Input fuer Inspector-Operationen zu einem veraenderbaren Objekt.'),
        ('readReceivableDraftingConfig', 'Leitet den aktiven LLM-Schreibmodus und seine Prompt-Felder aus dem Node-Input ab.'),
        ('statusTone', 'Ordnet Task-Status einer Badge-Farbe zu.'),
        ('handleApproveNode', 'Freigabe eines Nodes lokal oder ueber die Approval-API.'),
        ('handleRevokeNodeApproval', 'Hebt eine bestehende manuelle Freigabe lokal oder ueber die Approval-API auf.'),
        ('handlePreviewDraft', 'Fordert ueber das Backend eine einzelne LLM-Briefvorschau fuer den aktuell konfigurierten Forderungs-Node an.'),
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

Seit dem aktuellen Stand umfasst das System neben Planner, Semantic Firewall und Handler Trust auch:

- unveraenderliche Flow-Versionen mit aktivierbarer Zielversion
- Human-in-the-Loop-Nodes mit pausierbarer Runtime und Resume-API
- Metrikaggregation fuer Flows und Handler
- rollenbasierte Freigabe- und Resume-Pfade ueber Identity-Header
- kompilierbare Sub-Flows ueber einen eigenen Built-in-Handler

Hinweis zur Ausgabestrategie:

- `dokumentation/` ist die vollstaendige Markdown-Dokumentation.
- `docs/` ist die reduzierte HTML-Sicht fuer Projektcode und Beispiel-Flows; Whitepaper, Fachartikel und README-artige Begleittexte werden dort bewusst nicht veroeffentlicht.

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
11. [Fazit und Einordnung](fazit-und-einordnung.md)
12. [Fachartikel](fachartikel-nova-synesis.md)
13. [Aenderungsleitfaden](change-workflows.md)
14. [Referenzindex](reference/index.md)

## Wie du diese Doku liest

- Starte mit `getting-started.md`, wenn du das System lokal hochfahren willst.
- Lies `system-overview.md` und `backend-runtime.md`, wenn du Architektur und Laufzeit verstehen willst.
- Nutze `security-and-policy.md`, `handler-trust-and-approval.md` und `failure-playbook.md`, bevor du produktive Flows oder neue Handler einsetzt.
- Verwende `decision-guide.md` und `real-world-scenarios.md`, wenn du eigene Flows sicher entwerfen oder veraendern willst.
- Lies `fazit-und-einordnung.md` oder `fachartikel-nova-synesis.md`, wenn du die Architektur fachlich einordnen oder extern erklaeren musst.
''',
    'getting-started.md': '''# Schnellstart

Diese Datei zeigt den kuerzesten Weg, um NOVA-SYNESIS lokal zu starten und die registrierten Beispiele in der Web-UI zu nutzen.

## 1. Backend starten

```powershell
./run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

Wichtige URLs:

- `http://127.0.0.1:8552/docs`
- `http://127.0.0.1:8552/health`
- `http://127.0.0.1:8552/planner/status`
- `POST /flows/validate`

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

- `AI Plan` bootstrappt inzwischen automatisch einen generischen System-Agenten sowie die Scratch-Memories `planner-scratch` und `planner-vector`, wenn sie noch fehlen
- Ressourcen werden weiterhin nicht aus freiem Text erraten oder extern freigeschaltet
- spezialisierte Use-Case-Objekte aus `setup.ps1` bleiben wichtig, wenn ein Prompt ganz bestimmte Agenten, Ressourcen oder Memory-IDs nutzen soll

Nach einem `setup.ps1`:

1. Web-UI neu laden
2. Sidebar und Planner erneut oeffnen
3. erst dann `AI Plan`, `Import JSON` oder `Run Flow` nutzen

## 4. Use Cases in der Web-UI nutzen

### `platform_health_snapshot`

Setup zuerst ausfuehren:

```powershell
./Use_Cases/platform_health_snapshot/setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Danach in der Web-UI:

1. `Import JSON`
2. Datei `Use_Cases/platform_health_snapshot/flow.json` laden
3. `Save Flow`
4. `Run Flow`

Alternativ direkt per Skript:

```powershell
./Use_Cases/platform_health_snapshot/run.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

### `semantic_ticket_triage`

Setup zuerst ausfuehren:

```powershell
./Use_Cases/semantic_ticket_triage/setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Danach in der Web-UI:

1. `Import JSON`
2. Datei `Use_Cases/semantic_ticket_triage/flow.json` laden
3. `Save Flow`
4. `Run Flow`

Alternativ direkt per Skript:

```powershell
./Use_Cases/semantic_ticket_triage/run.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

## 5. `LLM_Planer`-Beispiele nutzen

Der Ordner `Use_Cases/LLM_Planer` enthaelt nur getestete Prompts.

Zuerst das Katalog-Setup ausfuehren:

```powershell
./Use_Cases/LLM_Planer/setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
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

### Per Verifikationsskript

```powershell
./Use_Cases/LLM_Planer/verify.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Das Skript:

- fuehrt bei Bedarf das Setup aus
- sendet die Prompts an `/planner/generate-flow`
- speichert die Flows
- startet die Ausfuehrung
- prueft die Ergebnisse

## 6. Die wichtigste Regel fuer `AI Plan`

`AI Plan` arbeitet nur mit dem aktuellen Planner-Katalog des laufenden Backends.

Also:

- ohne `setup.ps1` keine spezialisierten Agenten oder Ressourcen fuer deinen konkreten Fachfall
- das Backend erzeugt fuer freie Prompts zwar automatisch `nova-system-agent`, `planner-scratch` und `planner-vector`
- ohne weitere Registrierungen kann der Planner aber trotzdem nur mit den vorhandenen Built-in-Handlern und diesen generischen Bootstrap-Objekten arbeiten

Wenn ein Prompt einen Agenten, eine Resource oder ein Memory nennt, das nicht registriert ist, wird der Planner entweder fehlschlagen, den Node weglassen oder die Semantic Firewall blockiert den Flow.

## 7. Wichtige Umgebungsvariablen

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

## 8. Mentales Modell

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
4. `POST /flows` legt einen Flow-Container mit initialer Version an
5. spaetere Speicherungen erzeugen ueber `POST /flows/{id}/versions` neue unveraenderliche Versionen
6. optionale manuelle Freigaben oder HITL-Eingaben werden node-spezifisch gesetzt
7. `POST /flows/{id}/run` startet die aktive oder explizit angegebene Version
8. `FlowExecutor` verarbeitet den Graphen Node fuer Node und kann kontrolliert auf `WAITING_FOR_INPUT` pausieren
9. `/ws/flows/{flow_id}` uebertraegt Snapshots, Waiting-Zustaende und Resume-Ereignisse an die UI
10. `GET /flows/{flow_id}` bleibt die kanonische Wahrheit fuer Laufzeitstand und aktive Version

## Betriebsachsen seit Phase 1 bis 5

- `Flow Versioning`: ein Flow ist jetzt ein Container mit historisierten Versionen statt ein einzelner ueberschriebener Snapshot
- `Human in the Loop`: Nodes koennen kontrolliert auf menschliche Eingabe warten und spaeter fortgesetzt werden
- `Observability`: jeder Task-Lauf kann Telemetriedaten fuer Handler- und Flow-Analytics erzeugen
- `RBAC`: Freigaben und HITL-Resumes koennen an Rollen wie `approver` gebunden werden
- `Sub-Flows`: wiederverwendbare Child-Workflows laufen als eigener Handler in isoliertem Unterkontext

## Was dieses System bewusst ist

- graphbasiert statt chatbasiert
- zustandsbehaftet statt nur requestbasiert
- planner-unterstuetzt, aber nicht planner-abhaengig
- sicherheitsgefiltert, bevor Seiteneffekte entstehen
- handler-vertrauensbasiert statt nur handler-namensbasiert
''',
    'backend-runtime.md': '''# Backend-Laufzeit

Die Backend-Laufzeit wird durch `OrchestratorService` zusammengesetzt. Er verdrahtet Repository, Speicher, Ressourcenmanager, Handler-Registry, Planner, Semantic Firewall und Execution-Engine.

## Flow-Container und Versionen

- `POST /flows` erzeugt einen logischen Flow-Container und legt direkt `version 1` an
- `POST /flows/{flow_id}/versions` schreibt spaetere Graphaenderungen als neue unveraenderliche Version
- `POST /flows/{flow_id}/versions/{version_id}/activate` setzt die Zielversion fuer spaetere Loads und Runs
- `run_flow(..., version_id=...)` kann bewusst gegen eine nicht aktive Version laufen
- die Persistenz dafuer liegt in `flows` plus `flow_versions` innerhalb von `SQLiteRepository`

## Reihenfolge eines normalen Flows

1. API nimmt einen `FlowCreateRequest`, eine Planner-Anfrage oder einen Versions-Write entgegen.
2. `TaskHandlerRegistry` bewertet alle Handler gegen digitale Zertifikate und erzeugt Trust-Records.
3. `OrchestratorService.validate_flow_request()` laesst die semantische Firewall laufen.
4. Der Flow wird in Domaenenobjekte ueberfuehrt und als Version in SQLite gespeichert.
5. `FlowExecutor.run_flow()` startet die DAG-Ausfuehrung gegen eine konkrete Flow-Version.
6. `TaskExecutor.execute_task()` loest Templates auf, reserviert Ressourcen, ruft Agent und Handler auf und persistiert Snapshots.
7. Handler koennen Erfolg, Fehler oder `WAITING_FOR_INPUT` melden.
8. WebSocket-Abonnenten erhalten Ereignisse wie `flow.started`, `node.completed`, `node.waiting_for_input`, `node.approval.updated` oder `flow.failed`.

## Human in the Loop und Resume

- der Built-in-Handler `human_input_request` wirft intern eine `HumanInputRequiredError`
- die Engine persistiert dadurch keinen Crash, sondern einen kontrollierten `WAITING_FOR_INPUT`-Zustand
- offene Eingaben liegen serialisiert am Node und koennen ueber `GET /flows/{flow_id}/nodes/{node_id}/input-request` gelesen werden
- `POST /flows/{flow_id}/nodes/{node_id}/resume` uebergibt die Benutzerantwort, die danach in `results[node_id]` landet
- `FlowExecutor` setzt den pausierten Graphen ab dem wartenden Node fort, statt den gesamten Flow neu aufzubauen

## Telemetrie und Analytics

- jeder ausgefuehrte Task schreibt Laufzeitdaten wie Start, Ende, Status und `latency_ms`
- LLM-nahe Handler koennen zusaetzliche Metadaten wie geschaetzte Prompt- und Completion-Tokens mitgeben
- `SQLiteRepository.save_execution_metric()` persistiert diese Daten fuer Auswertungen
- `GET /metrics/summary`, `GET /metrics/flows` und `GET /metrics/handlers` liefern die aggregierte Betreiberansicht

## Rollen und serverseitige Freigaben

- RBAC wird nicht im Frontend entschieden, sondern in `OrchestratorService._ensure_actor_role()`
- Approvals und HITL-Resumes koennen einen `required_role` erzwingen
- wenn `NS_SECURITY_RBAC_ENABLED=true` aktiv ist, erwartet die API standardmaessig `X-NOVA-User` und `X-NOVA-Roles`
- die Default-Rolle fuer manuelle Freigaben ist `approver`, solange keine node-spezifische Rolle gesetzt ist

## Sub-Flows

- `execute_subflow` ist ein echter Built-in-Handler und kein UI-Trick
- der Handler startet ueber den Orchestrator einen Child-Flow in isoliertem Unterkontext
- `target_version_id` ist fuer reproduzierbare Child-Runs der saubere Pfad; ohne diese Angabe gibt die Policy bewusst eine Warnung aus
- Parent- und Child-Run haben getrennte Snapshots, aber der Rueckgabewert des Child-Flows wird als Ergebnis des Parent-Nodes veroeffentlicht

## Trust- und Approval-Gates

- `GET /handlers` ist die kanonische Betriebsansicht auf Handler-Trust.
- Der Planner-Katalog enthaelt nur trusted Handler.
- Freigaben liegen an `Task.manual_approval` und werden im Flow-Snapshot persistiert.
- `POST /flows/{flow_id}/nodes/{node_id}/approval` und `DELETE /flows/{flow_id}/nodes/{node_id}/approval` aendern den Freigabestatus ohne den ganzen Flow neu anzulegen.

## Relevante Runtime-Handler fuer freie Arbeitsablaeufe

- `news_search` zieht Nachrichten intern ueber RSS und braucht keine manuell gesetzte Ziel-URL
- `topic_split` erwartet eine echte Listenstruktur in `items` und erzeugt daraus `categorized_items` und `csv_rows`
- `generate_embedding` erzeugt den Vektor-Payload fuer `memory_store` in Vector-Memories
- `memory_store` speichert einfache Werte oder Embeddings; bei alten Platzhalter-Flows biegt der Runtime-Pfad offensichtliche Scheindaten auf das echte Upstream-Ergebnis um
- `filesystem_read` und `filesystem_write` sind technische Alias-Handler fuer lokale Datei-Workflows und vereinheitlichen Planner-Prompts fuer Audit- oder Reporting-Flows
- `local_llm_text` ist der generische lokale Text- und Analyse-Handler fuer Review-, Audit-, Zusammenfassungs- und Reporting-Nodes
- `human_input_request` pausiert einen Flow kontrolliert und fordert strukturierte Benutzereingaben an
- `execute_subflow` kapselt einen anderen gespeicherten Flow als wiederverwendbaren Child-Baustein

## Audit- und Analyse-Pfade mit lokalem LLM

- Ein typischer lokaler Audit-Flow liest zunaechst eine Datei ueber `filesystem_read`
- Danach analysiert `local_llm_text` den Dateiinhalt mit einem Prompt oder einer standardisierten Audit-Instruktion
- Wenn Upstream-Daten vorhanden sind, kombiniert der Handler Prompt und Daten zu einer finalen Modellanfrage
- Meta-Antworten wie `Please provide ...` werden serverseitig abgefangen und in eine direkte Endausgabe umgelenkt, damit kein halbfertiger Rueckfrage-Text im Report landet
- `filesystem_write` speichert die finalen Analyse- oder Reporttexte wieder lokal ab

## Regel fuer Aenderungen

Wenn du etwas an einem Runtime-Vertrag aenderst, pruefe fast immer gleichzeitig API, Domaenenmodell, Engine, Frontend-Typen, Serialisierung und Tests.
''',
    'frontend-editor.md': '''# Frontend-Editor

Die UI besteht aus `App.tsx`, dem Zustand-Store `useFlowStore.ts`, der Zeichenflaeche `FlowCanvas.tsx`, der linken `Sidebar.tsx`, dem `InspectorPanel.tsx`, dem Planner-Dialog und der `TopBar.tsx`.

## Was der Editor wirklich tut

- laedt Handler, Agenten und Ressourcen aus dem echten Backend
- baut daraus React-Flow-Nodes und -Edges
- serialisiert den Editorzustand ueber `toFlowRequest()`
- speichert Flow-Container und neue Flow-Versionen
- startet echte Flows gegen die aktive oder geladene Version
- uebernimmt Live-Snapshots ueber WebSocket oder Polling
- zeigt pro Node Handler-Trust, manuelle Freigaben und HITL-Zustaende im Inspector
- oeffnet ueber ein Analytics-Panel aggregierte Handler- und Flow-Metriken

## Kritische Integrationsstellen

- `frontend/src/lib/flowSerialization.ts`: muss exakt zum FastAPI-Schema passen
- `frontend/src/lib/apiClient.ts`: enthaelt die echten REST-, Versions-, Approval-, Resume-, Preview-, Metrics- und WebSocket-Aufrufe inklusive `POST /flows/validate`
- `frontend/src/store/useFlowStore.ts`: haelt den kanonischen UI-Zustand fuer Nodes, Edges, Auswahl, Versionen und Laufzeitstatus
- `frontend/src/hooks/useFlowLiveUpdates.ts`: faellt bei Socket-Problemen auf Polling zurueck

## Topbar und Versionen

- `Save Flow` legt bei einem bereits bestehenden Flow keine stillschweigende Ueberschreibung mehr an, sondern erzeugt eine neue Version
- die Versionsauswahl in `TopBar.tsx` laedt eine konkrete persistierte Version zurueck in den Canvas
- `Run Flow` verwendet die aktuell geladene Version, sofern eine `flowVersionId` vorhanden ist
- `Analytics` oeffnet eine kompakte Betreiberansicht auf Handler- und Flow-Metriken

## Human-in-the-Loop im Inspector

- wenn ein Node den Status `WAITING_FOR_INPUT` meldet, laedt der Inspector automatisch die offene Eingabeanforderung
- das Formular wird aus dem gelieferten JSON-Schema aufgebaut; bei komplexeren Strukturen gibt es einen JSON-Fallback
- `Submit Input` ruft `POST /flows/{flow_id}/nodes/{node_id}/resume` auf
- `Submitted by` wird mitpersistiert und ist Teil des Audit-Pfads
- wenn die Anforderung eine Rolle enthaelt, zeigt der Inspector diese als `Erforderliche Rolle` an
- ein `WAITING_FOR_INPUT`-Node ist kein Absturz, sondern ein kontrollierter Runtime-Stopp bis zur menschlichen Antwort

## Betreiberperspektive im Inspector

- `Handler trust` zeigt Zertifikatsstatus, Issuer, Fingerprint und Ablaufdatum
- `Require manual approval before execution` markiert einen Node als freigabepflichtig
- `Approval granted` setzt die Freigabe per Checkbox; bei bereits gespeichertem Flow wird die Approval-API direkt genutzt
- ohne gesetzten Freigabe-Haken bleibt ein freigabepflichtiger Node im Status `Pending`
- der Node `Generate Reminder Letters` besitzt zusaetzlich den Bereich `LLM Letter Drafting`
- `Use local LLM to draft the letter text` schaltet den Handler von festem Template auf lokalen LiteRT-Textentwurf um
- `Business instruction` steuert den fachlichen Ton des Briefs direkt durch den Benutzer
- `Prompt template` definiert den vollstaendigen Modellprompt pro Kunde mit Platzhaltern wie `{customer_name}`, `{invoice_lines}` oder `{total_outstanding}`
- `Preview Draft` ruft `POST /tools/accounts-receivable/preview-draft` auf, laesst serverseitig nur den Extract-Schritt plus einen einzelnen LLM-Entwurf laufen und zeigt Prompt und Ergebnis im Inspector an
- `Preview customer index` waehlt aus, fuer welchen Kunden aus der aktuellen Quelldatei die Vorschau erzeugt wird
- Vorschau-Requests sind zeitlich begrenzt, damit die UI nicht unbegrenzt auf ein blockiertes oder zu langsames lokales Modell warten muss
- bei ungespeicherten lokalen Aenderungen arbeitet der Inspector bewusst lokal weiter, um den Canvas-Zustand nicht zu ueberschreiben
- wenn RBAC aktiv ist, bleibt die echte Freigabe- oder Resume-Entscheidung trotzdem serverseitig; die UI ist nur die Bedienflaeche
''',
    'planner-and-lit.md': '''# LLM-Planer und LiteRT

Der Planner erzeugt keine Mock-Graphen. Er nutzt die lokale `lit`-Binary und das Gemma-Modell im `LIT/`-Ordner, extrahiert JSON und normalisiert das Resultat auf das echte `FlowRequest`-Schema.

## Ablauf

1. `LiteRTPlanner._build_prompt()` baut den Prompt aus Benutzerziel und echtem Katalog.
2. `_invoke_model()` ruft `lit.windows_x86_64.exe` mit `gemma-4-E2B-it.litertlm` auf.
3. `_parse_model_output_with_warnings()` extrahiert genau ein JSON-Objekt und repariert haeufige Formfehler aus LLM-Antworten wie Single Quotes, Bare Keys, fehlende Kommata, unvollstaendige Objekte und gemischte JSON/Python-Literale.
4. `_normalize_flow_request()` korrigiert IDs, Defaults, Abhaengigkeiten, Handler-Inputs und ersetzt offensichtliche Platzhalter-Shells im Embedding- und Memory-Pfad durch echte Upstream-Referenzen.
5. `OrchestratorService.generate_flow_with_llm()` laesst den Graphen anschliessend noch durch die Semantic Firewall laufen.

## Modellwechsel beim Serverstart

- `run-backend.ps1` akzeptiert `-LitModel`, `-LitBinary` und `-LitBackend`
- `python -m nova_synesis.cli run-api` akzeptiert `--lit-model`, `--lit-binary` und `--lit-backend`
- wenn bei `--lit-model` oder `-LitModel` nur ein Dateiname uebergeben wird, sucht NOVA-SYNESIS automatisch im Ordner `LIT/`
- `GET /planner/status` zeigt danach das aktiv verwendete Modell und Backend an
- multimodale `.litertlm`-Modelle koennen als Textmodell gestartet werden, Bild-Inputs sind damit aber noch nicht automatisch in Planner oder Web-UI verdrahtet
- wenn LiteRT beim Modellwechsel mit `failed to create engine` oder einem XNNPACK-Cache-Fehler scheitert, quarantaint NOVA-SYNESIS den modellbezogenen Cache automatisch und versucht einen Retry
- wenn auch der Retry scheitert, ist die Modell-/Binary-/Backend-Kombination wahrscheinlich nicht kompatibel
- bei freien Prompts bootstrappt der Planner automatisch `nova-system-agent`, `planner-scratch` und `planner-vector`, falls diese Objekte noch nicht existieren
- freie Web- oder CSV-Workflows koennen auf die Built-ins `news_search`, `topic_split` und `write_csv` zurueckgreifen
- lokale Datei- und Audit-Workflows koennen auf `filesystem_read`, `local_llm_text` und `filesystem_write` geplant werden
- wenn das Modell im Vector-Pfad nur Platzhalter wie `{"embedding":"..."}` liefert, repariert der Planner neue Flows auf echte `generate_embedding`-Result-Referenzen
- bereits gespeicherte Alt-Flows mit demselben Platzhalterfehler werden zur Laufzeit im `memory_store`-Handler auf das echte Upstream-Embedding umgebogen
- wenn das Modell bei `topic_split`, `write_csv`, `filesystem_read`, `filesystem_write` oder `local_llm_text` Aliasfelder, falsche Referenzformen oder Agentennamen als Handler liefert, normalisiert der Planner diese Inputs und Handler-Namen auf die echten Built-ins
- wenn ein Audit- oder Review-Node bereits einen Prompt besitzt, sorgt die Planner-Normalisierung trotzdem dafuer, dass die Upstream-Daten als `data` in den Node wandern
- der lokale Text-Handler erzwingt im Zusammenspiel mit dem Planner eine finale Antwort und verhindert Folgefragen wie `Please provide ...`, sobald ein Prompt und echte Eingangsdaten vorliegen
- neue Graphen koennen spaeter als eigene Flow-Version gespeichert werden; der Planner selbst schreibt aber nie direkt an einer bestehenden Version vorbei

## Wichtige Sicherheitsgrenzen

- Ressourcen und Memories mit `sensitive = true` oder `planner_visible = false` werden aus dem Planner-Katalog herausgefiltert.
- untrusted Handler werden komplett aus dem Planner-Katalog entfernt.
- `send_message` darf nur auf registrierte Kommunikationsziele zeigen. Wenn keins existiert, wird der Node aus dem Planner-Graphen entfernt und als Warnung gemeldet.
- Die Antwort enthaelt `security_report`, damit UI und Betreiber sehen, ob der generierte Graph policy-konform war.
- Planner-Warnungen bedeuten: der Graph wurde normalisiert, aber nicht stillschweigend erweitert.
- `requires_manual_approval` wird standardmaessig auf `false` normalisiert und nur uebernommen, wenn es explizit im Graphen gesetzt ist.
- freie Prompts duerfen weiterhin keine beliebigen neuen Fachhandler oder unbekannte Infrastruktur herbeifantasieren; sie bleiben an den echten Katalog gebunden

## Betriebsregel fuer echte Planner-Beispiele

- `AI Plan` kann nur mit dem arbeiten, was im laufenden Backend registriert ist.
- Deshalb muessen `Use_Cases/**/setup.ps1` oder andere Registrierungswege zuerst ausgefuehrt werden.
- Der Ordner `Use_Cases/LLM_Planer` enthaelt nur verifizierte Prompts fuer den jeweils registrierten Live-Katalog.
- Wenn Agenten, Ressourcen oder Memories nicht registriert sind, kann der Planner sie nicht sicher verwenden und entfernt betroffene Nodes oder die Semantic Firewall blockiert den Flow.
''',
    'security-and-policy.md': '''# Security und Policy

NOVA-SYNESIS sichert nicht nur Code, sondern die Absicht eines Graphen. Diese Aufgabe uebernimmt die Semantic Firewall in `src/nova_synesis/security/policy.py`.

## Wann die Policy greift

- bei Agent-Registrierung
- bei `POST /flows/validate`
- bei `POST /flows`
- bei `POST /flows/{flow_id}/versions`
- vor `POST /flows/{flow_id}/run`
- nach einer Planner-Generierung, bevor der Graph an die UI zurueckgeht
- bei serverseitigen Approval- und HITL-Resume-Entscheidungen ueber Rollen

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
- `execute_subflow`: `target_flow_id` muss gesetzt sein; fehlende `target_version_id` fuehrt bewusst zu einer Warnung gegen unscharfe Child-Runs

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

## Rollen und Identity-Header

- wenn `NS_SECURITY_RBAC_ENABLED=true` aktiv ist, wertet die API standardmaessig `X-NOVA-User` und `X-NOVA-Roles` aus
- die Default-Rolle fuer Freigaben ist `approver`, solange der Node keine spezifischere Rolle vorgibt
- dieselbe Rollenpruefung gilt fuer `POST /flows/{flow_id}/nodes/{node_id}/resume`, wenn eine offene HITL-Anforderung ein `required_role` enthaelt
- die UI kann Rollenhints anzeigen, aber die eigentliche Erlaubnis wird nur serverseitig entschieden

## Bedeutende Felder

- `sensitive = true`
- `planner_visible = false`
- `allow_untrusted_ingest = true`
- `requires_manual_approval = true`
- `manual_approval.approved = true`
- `manual_approval.required_role = "approver"`
- `input_request.required_role = "approver"`

## Wichtige Settings

- `NS_HANDLER_CERTIFICATE_SECRET`
- `NS_HANDLER_CERTIFICATE_ISSUER`
- `NS_HANDLER_CERTIFICATE_TTL_HOURS`
- `NS_SECURITY_ENABLED`
- `NS_SECURITY_AUTO_ISSUE_BUILTIN_HANDLER_CERTIFICATES`
- `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS`
- `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS`
- `NS_SECURITY_RBAC_ENABLED`
- `NS_SECURITY_DEFAULT_APPROVER_ROLE`
- `NS_SECURITY_IDENTITY_HEADER_USER`
- `NS_SECURITY_IDENTITY_HEADER_ROLES`
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
- `GET /flows/{flow_id}/nodes/{node_id}/input-request`: liest eine offene HITL-Anforderung
- `POST /flows/{flow_id}/nodes/{node_id}/resume`: setzt einen wartenden Node mit Benutzereingaben fort

Im `InspectorPanel` sieht der Betreiber:

- ob der aktuelle Handler trusted oder untrusted ist
- warum der Handler so eingestuft wurde
- Zertifikatsdetails wie Issuer, Fingerprint und Ablaufdatum
- ob fuer den Node eine manuelle Freigabe erforderlich oder bereits gesetzt ist
- ob fuer einen WAITING_FOR_INPUT-Node eine Rolle verlangt wird und welche Eingaben erwartet werden

## 4. Wann die Ausfuehrung blockiert wird

- unbekannter Handler: immer blockiert
- untrusted Handler bei `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS=true`: spaetestens beim Run blockiert
- `requires_manual_approval=true`, aber keine Freigabe gesetzt: beim Run blockiert
- Freigabe ohne `approved_by`: ebenfalls blockiert
- Resume ohne erforderliche Rolle: serverseitig mit `403` blockiert

## 5. Operator-Regeln

- Built-in-Handler bleiben der Normalfall.
- Eigene Handler nur dann trusten, wenn Codequelle und Seiteneffektprofil klar sind.
- Manuelle Freigaben sind flow-spezifisch, nicht global.
- Eine Freigabe ersetzt kein Zertifikat; sie ist eine bewusste Ausnahme fuer einen konkreten Node.
- Freigaben und HITL-Resumes sollten im RBAC-Betrieb immer mit `X-NOVA-User` und `X-NOVA-Roles` nachvollziehbar gemacht werden.

## 6. Relevante Settings

- `NS_HANDLER_CERTIFICATE_SECRET`
- `NS_HANDLER_CERTIFICATE_ISSUER`
- `NS_HANDLER_CERTIFICATE_TTL_HOURS`
- `NS_SECURITY_AUTO_ISSUE_BUILTIN_HANDLER_CERTIFICATES`
- `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS`
- `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS`
- `NS_SECURITY_RBAC_ENABLED`
- `NS_SECURITY_DEFAULT_APPROVER_ROLE`
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
2. zuerst pruefen, ob der Planner bereits eine Warnung zur automatischen JSON-Reparatur oder Prompt-Kompaktierung geliefert hat
3. Prompt kuerzen und restriktiver machen
4. `max_nodes` senken
5. sicherstellen, dass benoetigte Handler, Agenten, Ressourcen und Memory-IDs wirklich registriert sind
6. bei wiederholtem Fehler den Flow manuell im Editor bauen

### Wichtig seit v1.0.5

- formale JSON-Fehler wie Single Quotes, Python-True/None, trailing commas oder fehlende Abschlussklammern werden zuerst automatisch repariert
- LiteRT-Kontextfehler loesen einen automatischen Retry mit kompakterem Prompt aus
- bleibt der Fehler trotzdem bestehen, ist die Antwort meist fachlich unbrauchbar und nicht nur formal kaputt

## 2. Semantic Firewall lehnt den Flow ab

### Woran du es erkennst

- `POST /flows/validate`, `POST /flows` oder `POST /planner/generate-flow` liefert einen Fehler
- typische Fehlermeldungen:
  - `Semantic firewall rejected flow`
  - `Outbound host ... is outside the semantic firewall allowlist`
  - `Flow contains a cycle`
  - `Sensitive memory data may not flow into http_request nodes`
  - `send_message references unknown agent '...'`

### Typische Ursachen

- zyklischer Graph
- `http_request` auf einen nicht erlaubten Host
- `send_message` ohne echtes Kommunikationsziel oder mit Endpoint-Override
- Template oder Condition mit nicht erlaubten Symbolen
- planner-sichtbare Memory-Store-Node hinter untrusted Ingest

### Sofortmassnahmen

1. denselben Payload gegen `POST /flows/validate` schicken
2. `violations` und `warnings` getrennt lesen
3. bei `send_message` pruefen, ob in `GET /agents` mindestens ein Agent mit `communication` registriert ist
4. wenn der Planner einen unbekannten Agentennamen verwendet hat, den Flow neu generieren oder den Node auf einen echten Sink-Agenten umstellen
5. pruefen, ob das Problem fachlich oder rein policy-seitig ist
6. bei legitimen Produktionsfaellen erst Settings oder Memory-/Resource-Metadaten anpassen, nicht die Regel blind entfernen

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

## 5. Flow wartet auf menschliche Eingabe und wirkt haengend

### Woran du es erkennst

- die UI zeigt einen Node mit `WAITING_FOR_INPUT`
- der Flow laeuft nicht weiter, obwohl keine technische Exception sichtbar ist
- im Inspector erscheint ein Formular statt einer klassischen Fehlermeldung

### Sofortmassnahmen

1. den wartenden Node anklicken
2. `GET /flows/{flow_id}/nodes/{node_id}/input-request` pruefen
3. benoetigte Eingabe und gegebenenfalls `required_role` lesen
4. ueber den Inspector oder `POST /flows/{flow_id}/nodes/{node_id}/resume` eine Antwort schicken
5. bei `403` die gesendeten Rollenheader pruefen

## 6. Resource haengt oder laeuft in Timeout / Sattlauf

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

## 7. Flow bleibt auf `RUNNING` stehen

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

## 8. Falsche Flow-Version wurde gestartet

### Woran du es erkennst

- der Canvas zeigt eine andere Konfiguration als der gerade gelaufene Snapshot
- ein alter Fehler taucht erneut auf, obwohl der Graph lokal bereits korrigiert wurde
- `GET /flows/{flow_id}` zeigt eine andere `version_id` als erwartet

### Sofortmassnahmen

1. in der Topbar die aktuell geladene Version pruefen
2. `GET /flows/{flow_id}/versions` lesen und die aktive Version mit dem UI-Zustand vergleichen
3. falls noetig die gewuenschte Version aktivieren oder explizit diese Version starten
4. nach einer lokalen Aenderung zuerst `Save Flow` ausfuehren, damit eine neue Version entsteht

## 9. Graph-Deadlock oder logisch blockierter Flow

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

## 10. Handler wirft Exception

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
7. `tools/generate_docs.py` und danach `dokumentation/` neu erzeugen

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
5. `tools/generate_docs.py` ausfuehren und `dokumentation/` neu erzeugen

## Neuer Trust- oder Approval-Pfad

1. Zertifikats- oder Approval-Logik in `security/trust.py`, `runtime/handlers.py` oder `domain/models.py` anpassen
2. `services/orchestrator.py` und `api/app.py` auf neue Operator-Aktionen abstimmen
3. Frontend-Inspector und Typen synchronisieren
4. mindestens einen positiven und einen negativen Security-Test ergaenzen
5. danach Referenzdoku und Betriebsdoku neu erzeugen
''',
}

ROOT_GUIDE_SOURCES = {
    'getting-started.md': ROOT / 'Schnellstart.md',
    'fazit-und-einordnung.md': ROOT / 'fazit.md',
    'fachartikel-nova-synesis.md': ROOT / 'Fachartikel_NOVA-SYNESIS.md',
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    for encoding in ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1'):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding='utf-8', errors='ignore')


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
    if r.endswith('.tsbuildinfo') or '.xnnpack_cache' in r or r.endswith('.litertlm'):
        return True
    return any(r == item or r.startswith(item + '/') for item in EXCLUDED)


def project_files() -> list[Path]:
    tracked_files: list[Path] | None = None
    try:
        result = subprocess.run(
            ['git', 'ls-files'],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
        )
        tracked_files = []
        for line in result.stdout.splitlines():
            relative = line.strip()
            if not relative:
                continue
            candidate = ROOT / relative
            if candidate.is_file() and not excluded(candidate):
                tracked_files.append(candidate)
    except (OSError, subprocess.SubprocessError):
        tracked_files = None

    def is_project_code_file(path: Path) -> bool:
        relative = rel(path)
        return (
            relative.startswith('src/nova_synesis/')
            or relative.startswith('frontend/src/')
            or relative.startswith('tests/')
            or relative.startswith('tools/')
            or relative.startswith('Use_Cases/')
        )

    discovered_files = [p for p in ROOT.rglob('*') if p.is_file() and not excluded(p) and is_project_code_file(p)]
    if tracked_files is None:
        files = discovered_files
    else:
        merged: dict[str, Path] = {rel(path): path for path in tracked_files}
        for path in discovered_files:
            merged.setdefault(rel(path), path)
        files = list(merged.values())
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
    if REF.exists():
        shutil.rmtree(REF)
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
    for name, source in ROOT_GUIDE_SOURCES.items():
        if source.exists():
            (DOCS / name).write_text(read_text(source).strip() + '\n', encoding='utf-8')

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
        '- `data/`, `billing/`, `debug_tmp/`, `planner_live_check*/`, `ws_debug/`: Laufzeit- und Debug-Artefakte',
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

# CodeDump for Project: `docs.zip`

_Generated on 2026-04-08T20:30:28.005Z_

## File: `backend-runtime.md`  
- Path: `backend-runtime.md`  
- Size: 304 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# Backend-Laufzeit

Die Backend-Laufzeit wird durch `OrchestratorService` zusammengesetzt. Er besitzt Repository, Speicher, Ressourcenmanager, Planner, Handler-Registry und Execution-Engine.

Wichtige Regel: Laufzeitveraenderungen betreffen fast immer gleichzeitig Domaene, Engine und API-Snapshot.

```

## File: `change-workflows.md`  
- Path: `change-workflows.md`  
- Size: 431 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# Aenderungsleitfaden

## Neuer Handler

1. Handler in `runtime/handlers.py` implementieren und registrieren
2. Tests erweitern
3. UI laedt den Handler automatisch ueber `/handlers`

## Neues Node-Feld

1. Backend-Schema in `api/app.py`
2. TypeScript-Typen in `frontend/src/types/api.ts`
3. Serialisierung in `frontend/src/lib/flowSerialization.ts`
4. Inspector in `frontend/src/components/layout/InspectorPanel.tsx`

```

## File: `coverage.md`  
- Path: `coverage.md`  
- Size: 3077 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# Abdeckung

- Dokumentierte Projektdateien: `73`
- Referenzdateien: `74`

## Ausgeschlossene Bereiche

- `data/`, `debug_tmp/`, `planner_live_check*/`, `ws_debug/`: Laufzeit- und Debug-Artefakte
- `frontend/node_modules/`, `frontend/dist/`: Fremd- und Buildartefakte
- `__pycache__/`, `.pytest_cache/`: Cache-Verzeichnisse

## Dokumentierte Dateien

- `.env.example`
- `Agenten_UML.zip`
- `Anweisung.md`
- `Dockerfile`
- `LIT/README.md`
- `LIT/gemma-4-E2B-it.litertlm`
- `LIT/gemma-4-E2B-it.litertlm.xnnpack_cache`
- `LIT/lit.windows_x86_64.exe`
- `LIT/planner_test_prompt.txt`
- `README.md`
- `frontend/.env`
- `frontend/.env.example`
- `frontend/index.html`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/app.css`
- `frontend/src/components/common/JsonEditor.tsx`
- `frontend/src/components/common/StatusBadge.tsx`
- `frontend/src/components/flow/FlowCanvas.tsx`
- `frontend/src/components/flow/TaskNode.tsx`
- `frontend/src/components/layout/InspectorPanel.tsx`
- `frontend/src/components/layout/PlannerComposer.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/TopBar.tsx`
- `frontend/src/hooks/useCatalogBootstrap.ts`
- `frontend/src/hooks/useFlowLiveUpdates.ts`
- `frontend/src/lib/apiClient.ts`
- `frontend/src/lib/autoLayout.ts`
- `frontend/src/lib/flowSerialization.ts`
- `frontend/src/lib/json.ts`
- `frontend/src/main.tsx`
- `frontend/src/store/useFlowStore.ts`
- `frontend/src/types/api.ts`
- `frontend/src/vite-env.d.ts`
- `frontend/tsconfig.app.json`
- `frontend/tsconfig.app.tsbuildinfo`
- `frontend/tsconfig.json`
- `frontend/tsconfig.node.json`
- `frontend/tsconfig.node.tsbuildinfo`
- `frontend/vite.config.d.ts`
- `frontend/vite.config.js`
- `frontend/vite.config.ts`
- `pyproject.toml`
- `run-backend.cmd`
- `run-backend.ps1`
- `src/nova_synesis/__init__.py`
- `src/nova_synesis/api/__init__.py`
- `src/nova_synesis/api/app.py`
- `src/nova_synesis/cli.py`
- `src/nova_synesis/communication/__init__.py`
- `src/nova_synesis/communication/adapters.py`
- `src/nova_synesis/config.py`
- `src/nova_synesis/domain/__init__.py`
- `src/nova_synesis/domain/models.py`
- `src/nova_synesis/memory/__init__.py`
- `src/nova_synesis/memory/systems.py`
- `src/nova_synesis/persistence/__init__.py`
- `src/nova_synesis/persistence/sqlite_repository.py`
- `src/nova_synesis/planning/__init__.py`
- `src/nova_synesis/planning/lit_planner.py`
- `src/nova_synesis/planning/planner.py`
- `src/nova_synesis/resources/__init__.py`
- `src/nova_synesis/resources/manager.py`
- `src/nova_synesis/runtime/__init__.py`
- `src/nova_synesis/runtime/engine.py`
- `src/nova_synesis/runtime/handlers.py`
- `src/nova_synesis/services/__init__.py`
- `src/nova_synesis/services/orchestrator.py`
- `tests/test_orchestrator.py`
- `tools/generate_docs.py`
- `uml.html`
- `uml_V3.mmd`

```

## File: `frontend-editor.md`  
- Path: `frontend-editor.md`  
- Size: 369 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# Frontend-Editor

Die UI besteht aus `App.tsx`, dem Zustand-Store `useFlowStore.ts`, der Zeichenflaeche `FlowCanvas.tsx`, der linken `Sidebar.tsx`, dem `InspectorPanel.tsx` und der `TopBar.tsx`.

Die kritischste Integrationsdatei ist `frontend/src/lib/flowSerialization.ts`. Wenn dort Felder falsch gemappt werden, speichert die UI keinen korrekten Backend-Flow.

```

## File: `getting-started.md`  
- Path: `getting-started.md`  
- Size: 556 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# Schnellstart

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

```

## File: `planner-and-lit.md`  
- Path: `planner-and-lit.md`  
- Size: 328 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# LLM-Planer und LiteRT

Der Planner erzeugt keine Mock-Graphen. Er nutzt die lokale `lit`-Binary und das Gemma-Modell im `LIT/`-Ordner, extrahiert JSON und validiert das Resultat gegen den echten Backend-Katalog.

Wenn du Planner-Qualitaet verbesserst, arbeite primär in `src/nova_synesis/planning/lit_planner.py`.

```

## File: `README.md`  
- Path: `README.md`  
- Size: 480 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# Dokumentation

Diese Dokumentation erklaert das System so, dass auch ein Entwickler ohne Vorwissen das Projekt starten, verstehen und gezielt aendern kann.

## Einstieg

1. [Schnellstart](getting-started.md)
2. [Systemueberblick](system-overview.md)
3. [Backend-Laufzeit](backend-runtime.md)
4. [Frontend-Editor](frontend-editor.md)
5. [LLM-Planer und LiteRT](planner-and-lit.md)
6. [Aenderungsleitfaden](change-workflows.md)
7. [Referenzindex](reference/index.md)

```

## File: `reference/Agenten_UML.zip.md`  
- Path: `reference/Agenten_UML.zip.md`  
- Size: 803 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `Agenten_UML.zip`

- Quellpfad: [Agenten_UML.zip](../../Agenten_UML.zip)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Binaeres Artefakt des Projekts.

## Wann du diese Datei bearbeitest

Nur bei gezieltem Austausch des Artefakts.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/Anweisung.md.md`  
- Path: `reference/Anweisung.md.md`  
- Size: 932 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `Anweisung.md`

- Quellpfad: [Anweisung.md](../../Anweisung.md)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Fachliche Ursprungsspezifikation des Systems.

## Wann du diese Datei bearbeitest

Wenn Anforderungen nachgezogen oder gegen die Implementierung gespiegelt werden.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [uml_V3.mmd](uml_V3.mmd.md)
- [README.md](README.md.md)

```

## File: `reference/Dockerfile.md`  
- Path: `reference/Dockerfile.md`  
- Size: 957 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `Dockerfile`

- Quellpfad: [Dockerfile](../../Dockerfile)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Container-Build fuer das Python-Backend.

## Wann du diese Datei bearbeitest

Wenn Build, Startkommando oder Image-Basis angepasst werden muessen.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [pyproject.toml](pyproject.toml.md)
- [src/nova_synesis/cli.py](src/nova_synesis/cli.py.md)

```

## File: `reference/frontend/index.html.md`  
- Path: `reference/frontend/index.html.md`  
- Size: 883 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/index.html`

- Quellpfad: [frontend/index.html](../../../frontend/index.html)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

HTML-Datei fuer Visualisierung oder Browser-Einstieg.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/package-lock.json.md`  
- Path: `reference/frontend/package-lock.json.md`  
- Size: 878 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/package-lock.json`

- Quellpfad: [frontend/package-lock.json](../../../frontend/package-lock.json)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/package.json.md`  
- Path: `reference/frontend/package.json.md`  
- Size: 863 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/package.json`

- Quellpfad: [frontend/package.json](../../../frontend/package.json)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/app.css.md`  
- Path: `reference/frontend/src/app.css.md`  
- Size: 843 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/app.css`

- Quellpfad: [frontend/src/app.css](../../../../frontend/src/app.css)
- Kategorie: `Frontend`

## Aufgabe der Datei

Stylesheet der Weboberflaeche.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/App.tsx.md`  
- Path: `reference/frontend/src/App.tsx.md`  
- Size: 2199 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/App.tsx`

- Quellpfad: [frontend/src/App.tsx](../../../../frontend/src/App.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Root-Komponente der UI mit Layout, Planner, Save/Run und Live-Sync.

## Wann du diese Datei bearbeitest

Wenn globale Frontend-Aktionen oder das Seitenlayout geaendert werden.

## Exporte und oeffentliche Definitionen

- `App`: React-Komponente `App` fuer einen klar abgegrenzten UI-Bereich.

## Wichtige interne Routinen

- `saveCurrentFlow`: Speichert den aktuellen Canvas als echten Flow im Backend.
- `handleRun`: Speichert bei Bedarf und startet anschliessend die Flow-Ausfuehrung.
- `handleExport`: Exportiert den Editorzustand als JSON-Datei.
- `handleImport`: Importiert einen Editor-Export oder einen nackten FlowRequest.
- `handleGenerateWithPlanner`: Fordert ueber das Backend einen neuen Graphen vom LLM-Planer an.

## Abhaengigkeiten

- `import { ReactFlowProvider } from "@xyflow/react";`
- `import { useCallback, useEffect, useState } from "react";`
- `import { FlowCanvas } from "./components/flow/FlowCanvas";`
- `import { InspectorPanel } from "./components/layout/InspectorPanel";`
- `import { PlannerComposer } from "./components/layout/PlannerComposer";`
- `import { Sidebar } from "./components/layout/Sidebar";`
- `import { TopBar } from "./components/layout/TopBar";`
- `import { useCatalogBootstrap } from "./hooks/useCatalogBootstrap";`
- `import { useFlowLiveUpdates } from "./hooks/useFlowLiveUpdates";`
- `import {`
- `import { fromFlowRequest, toFlowRequest } from "./lib/flowSerialization";`
- `import { prettyJson, safeJsonParse } from "./lib/json";`
- `import { useFlowStore } from "./store/useFlowStore";`
- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/store/useFlowStore.ts](store/useFlowStore.ts.md)
- [frontend/src/components/layout/TopBar.tsx](components/layout/TopBar.tsx.md)

```

## File: `reference/frontend/src/components/common/JsonEditor.tsx.md`  
- Path: `reference/frontend/src/components/common/JsonEditor.tsx.md`  
- Size: 921 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/components/common/JsonEditor.tsx`

- Quellpfad: [frontend/src/components/common/JsonEditor.tsx](../../../../../../frontend/src/components/common/JsonEditor.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `JsonEditor`: Funktion oder Definition `JsonEditor` dieses Moduls.

## Abhaengigkeiten

- `import { useEffect, useMemo, useState } from "react";`
- `import { prettyJson, safeJsonParse } from "../../lib/json";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/components/common/StatusBadge.tsx.md`  
- Path: `reference/frontend/src/components/common/StatusBadge.tsx.md`  
- Size: 875 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/components/common/StatusBadge.tsx`

- Quellpfad: [frontend/src/components/common/StatusBadge.tsx](../../../../../../frontend/src/components/common/StatusBadge.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `StatusBadge`: Funktion oder Definition `StatusBadge` dieses Moduls.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/components/flow/FlowCanvas.tsx.md`  
- Path: `reference/frontend/src/components/flow/FlowCanvas.tsx.md`  
- Size: 1013 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/components/flow/FlowCanvas.tsx`

- Quellpfad: [frontend/src/components/flow/FlowCanvas.tsx](../../../../../../frontend/src/components/flow/FlowCanvas.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `FlowCanvas`: React-Flow-Leinwand des Editors.

## Abhaengigkeiten

- `import {`
- `import { useCallback, useRef } from "react";`
- `import { useFlowStore } from "../../store/useFlowStore";`
- `import type { TaskFlowEdge, TaskFlowNode } from "../../types/api";`
- `import { TaskNode } from "./TaskNode";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/components/flow/TaskNode.tsx.md`  
- Path: `reference/frontend/src/components/flow/TaskNode.tsx.md`  
- Size: 964 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/components/flow/TaskNode.tsx`

- Quellpfad: [frontend/src/components/flow/TaskNode.tsx](../../../../../../frontend/src/components/flow/TaskNode.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `TaskNode`: Custom Node fuer einzelne Tasks im Canvas.

## Abhaengigkeiten

- `import { Handle, Position, type NodeProps } from "@xyflow/react";`
- `import { useFlowStore } from "../../store/useFlowStore";`
- `import type { TaskFlowNode } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/components/layout/InspectorPanel.tsx.md`  
- Path: `reference/frontend/src/components/layout/InspectorPanel.tsx.md`  
- Size: 1714 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/components/layout/InspectorPanel.tsx`

- Quellpfad: [frontend/src/components/layout/InspectorPanel.tsx](../../../../../../frontend/src/components/layout/InspectorPanel.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Node- und Edge-Inspector fuer bearbeitbare Eigenschaften.

## Wann du diese Datei bearbeitest

Wenn weitere konfigurierbare Felder in der UI auftauchen sollen.

## Exporte und oeffentliche Definitionen

- `InspectorPanel`: Eigenschaftseditor fuer Nodes und Edges.

## Wichtige interne Routinen

- `patchNode`: Wendet ein Teilupdate auf die Daten eines Nodes an.
- `splitCsv`: Konvertiert komma-separierte Texte in Stringlisten.
- `asObject`: Normalisiert unbekannte Werte zu einem sicheren Objekt.
- `statusTone`: Ordnet Task-Status einer Badge-Farbe zu.
- `NodeField`: Hilfskomponente fuer einfache Texteingaben im Inspector.
- `NumericField`: Hilfskomponente fuer numerische Eingaben im Inspector.

## Abhaengigkeiten

- `import { JsonEditor } from "../common/JsonEditor";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import { useFlowStore } from "../../store/useFlowStore";`
- `import type { ResourceType, RollbackStrategy, TaskFlowNode } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/store/useFlowStore.ts](../../store/useFlowStore.ts.md)
- [frontend/src/components/common/JsonEditor.tsx](../common/JsonEditor.tsx.md)

```

## File: `reference/frontend/src/components/layout/PlannerComposer.tsx.md`  
- Path: `reference/frontend/src/components/layout/PlannerComposer.tsx.md`  
- Size: 1212 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/components/layout/PlannerComposer.tsx`

- Quellpfad: [frontend/src/components/layout/PlannerComposer.tsx](../../../../../../frontend/src/components/layout/PlannerComposer.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Planner-Dialog fuer die lokale LLM-Graph-Erzeugung.

## Wann du diese Datei bearbeitest

Wenn Prompting-UX oder Planner-Rueckmeldungen im Frontend erweitert werden.

## Exporte und oeffentliche Definitionen

- `PlannerComposer`: Dialog fuer die autonome Graph-Erzeugung.

## Abhaengigkeiten

- `import { useEffect, useState } from "react";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import type { PlannerGenerateResponse, PlannerStatus } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/App.tsx](../../App.tsx.md)
- [src/nova_synesis/planning/lit_planner.py](../../../../src/nova_synesis/planning/lit_planner.py.md)

```

## File: `reference/frontend/src/components/layout/Sidebar.tsx.md`  
- Path: `reference/frontend/src/components/layout/Sidebar.tsx.md`  
- Size: 1142 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/components/layout/Sidebar.tsx`

- Quellpfad: [frontend/src/components/layout/Sidebar.tsx](../../../../../../frontend/src/components/layout/Sidebar.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Linke Katalogleiste mit Handlern, Agenten und Ressourcen.

## Wann du diese Datei bearbeitest

Wenn Drag-and-Drop oder Katalogdarstellung geaendert wird.

## Exporte und oeffentliche Definitionen

- `Sidebar`: Funktion oder Definition `Sidebar` dieses Moduls.

## Abhaengigkeiten

- `import { useMemo, useState } from "react";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import { useFlowStore } from "../../store/useFlowStore";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/components/flow/FlowCanvas.tsx](../flow/FlowCanvas.tsx.md)
- [frontend/src/store/useFlowStore.ts](../../store/useFlowStore.ts.md)

```

## File: `reference/frontend/src/components/layout/TopBar.tsx.md`  
- Path: `reference/frontend/src/components/layout/TopBar.tsx.md`  
- Size: 1225 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/components/layout/TopBar.tsx`

- Quellpfad: [frontend/src/components/layout/TopBar.tsx](../../../../../../frontend/src/components/layout/TopBar.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

Globale Aktionsleiste fuer Save, Run, Planner, Import und Export.

## Wann du diese Datei bearbeitest

Wenn globale Bedienaktionen oder Statusanzeigen geaendert werden.

## Exporte und oeffentliche Definitionen

- `TopBar`: Funktion oder Definition `TopBar` dieses Moduls.

## Wichtige interne Routinen

- `statusTone`: Ordnet globale Flow-Zustaende den Topbar-Badge-Farben zu.

## Abhaengigkeiten

- `import { useRef } from "react";`
- `import { StatusBadge } from "../common/StatusBadge";`
- `import type { PlannerStatus } from "../../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/App.tsx](../../App.tsx.md)
- [frontend/src/components/common/StatusBadge.tsx](../common/StatusBadge.tsx.md)

```

## File: `reference/frontend/src/hooks/useCatalogBootstrap.ts.md`  
- Path: `reference/frontend/src/hooks/useCatalogBootstrap.ts.md`  
- Size: 983 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/hooks/useCatalogBootstrap.ts`

- Quellpfad: [frontend/src/hooks/useCatalogBootstrap.ts](../../../../../frontend/src/hooks/useCatalogBootstrap.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `useCatalogBootstrap`: Funktion oder Definition `useCatalogBootstrap` dieses Moduls.

## Abhaengigkeiten

- `import { useEffect } from "react";`
- `import { fetchAgents, fetchHandlers, fetchResources } from "../lib/apiClient";`
- `import { useFlowStore } from "../store/useFlowStore";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/hooks/useFlowLiveUpdates.ts.md`  
- Path: `reference/frontend/src/hooks/useFlowLiveUpdates.ts.md`  
- Size: 1025 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/hooks/useFlowLiveUpdates.ts`

- Quellpfad: [frontend/src/hooks/useFlowLiveUpdates.ts](../../../../../frontend/src/hooks/useFlowLiveUpdates.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `useFlowLiveUpdates`: Funktion oder Definition `useFlowLiveUpdates` dieses Moduls.

## Abhaengigkeiten

- `import { useEffect } from "react";`
- `import { fetchFlow, getWebSocketBaseUrl } from "../lib/apiClient";`
- `import { useFlowStore } from "../store/useFlowStore";`
- `import type { FlowEventMessage } from "../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/lib/apiClient.ts.md`  
- Path: `reference/frontend/src/lib/apiClient.ts.md`  
- Size: 1554 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/lib/apiClient.ts`

- Quellpfad: [frontend/src/lib/apiClient.ts](../../../../../frontend/src/lib/apiClient.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Echter API-Client fuer REST und WebSocket-Basis-URLs.

## Wann du diese Datei bearbeitest

Wenn neue Backend-Endpunkte im Frontend angebunden werden.

## Exporte und oeffentliche Definitionen

- `getApiBaseUrl`: Funktion oder Definition `getApiBaseUrl` dieses Moduls.
- `getWebSocketBaseUrl`: Funktion oder Definition `getWebSocketBaseUrl` dieses Moduls.
- `fetchPlannerStatus`: Funktion oder Definition `fetchPlannerStatus` dieses Moduls.
- `fetchAgents`: Funktion oder Definition `fetchAgents` dieses Moduls.
- `fetchResources`: Funktion oder Definition `fetchResources` dieses Moduls.
- `createFlow`: Funktion oder Definition `createFlow` dieses Moduls.
- `runFlow`: Steuert den Ablauf von `runFlow`.
- `fetchFlow`: Funktion oder Definition `fetchFlow` dieses Moduls.
- `generateFlowWithPlanner`: Funktion oder Definition `generateFlowWithPlanner` dieses Moduls.

## Abhaengigkeiten

- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/api/app.py](../../../src/nova_synesis/api/app.py.md)
- [frontend/src/types/api.ts](../types/api.ts.md)

```

## File: `reference/frontend/src/lib/autoLayout.ts.md`  
- Path: `reference/frontend/src/lib/autoLayout.ts.md`  
- Size: 828 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/lib/autoLayout.ts`

- Quellpfad: [frontend/src/lib/autoLayout.ts](../../../../../frontend/src/lib/autoLayout.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `autoLayoutNodes`: Funktion oder Definition `autoLayoutNodes` dieses Moduls.

## Abhaengigkeiten

- `import type { TaskFlowEdge, TaskFlowNode } from "../types/api";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/lib/flowSerialization.ts.md`  
- Path: `reference/frontend/src/lib/flowSerialization.ts.md`  
- Size: 2050 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/lib/flowSerialization.ts`

- Quellpfad: [frontend/src/lib/flowSerialization.ts](../../../../../frontend/src/lib/flowSerialization.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Uebersetzung zwischen React-Flow und echtem Backend-Flow-Schema.

## Wann du diese Datei bearbeitest

Wenn Node-Felder oder Flow-Schema geaendert werden.

## Exporte und oeffentliche Definitionen

- `createTaskNode`: Erzeugt einen neuen Task-Node mit Defaultwerten.
- `createTaskEdge`: Erzeugt eine neue Kante mit Standardbedingung.
- `toTaskSpec`: Funktion oder Definition `toTaskSpec` dieses Moduls.
- `toEdgeModel`: Funktion oder Definition `toEdgeModel` dieses Moduls.
- `toFlowRequest`: Serialisiert den Editorgraphen exakt in das Backend-Schema.
- `fromFlowSnapshot`: Wandelt einen Backend-Snapshot in React-Flow-Elemente um.
- `fromFlowRequest`: Funktion oder Definition `fromFlowRequest` dieses Moduls.
- `humanizeHandlerName`: Funktion oder Definition `humanizeHandlerName` dieses Moduls.
- `DEFAULT_RETRY_POLICY`: Funktion oder Definition `DEFAULT_RETRY_POLICY` dieses Moduls.
- `DEFAULT_ROLLBACK_STRATEGY`: Funktion oder Definition `DEFAULT_ROLLBACK_STRATEGY` dieses Moduls.

## Wichtige interne Routinen

- `readUiMetadata`: Liest UI-spezifische Metadaten aus dem allgemeinen Metadata-Objekt.
- `asPosition`: Leitet eine gueltige Canvas-Position aus Metadaten oder Fallbacks ab.
- `snapshotNodeToEditorNode`: Wandelt einen Backend-Node-Snapshot in einen Editor-Node um.

## Abhaengigkeiten

- `import { MarkerType } from "@xyflow/react";`
- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/types/api.ts](../types/api.ts.md)
- [src/nova_synesis/api/app.py](../../../src/nova_synesis/api/app.py.md)

```

## File: `reference/frontend/src/lib/json.ts.md`  
- Path: `reference/frontend/src/lib/json.ts.md`  
- Size: 880 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/lib/json.ts`

- Quellpfad: [frontend/src/lib/json.ts](../../../../../frontend/src/lib/json.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `safeJsonParse`: Funktion oder Definition `safeJsonParse` dieses Moduls.
- `prettyJson`: Funktion oder Definition `prettyJson` dieses Moduls.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/main.tsx.md`  
- Path: `reference/frontend/src/main.tsx.md`  
- Size: 870 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/main.tsx`

- Quellpfad: [frontend/src/main.tsx](../../../../frontend/src/main.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Inhalt

Diese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.

## Abhaengigkeiten

- `import React from "react";`
- `import ReactDOM from "react-dom/client";`
- `import "@xyflow/react/dist/style.css";`
- `import "./app.css";`
- `import App from "./App";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/src/store/useFlowStore.ts.md`  
- Path: `reference/frontend/src/store/useFlowStore.ts.md`  
- Size: 1379 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/store/useFlowStore.ts`

- Quellpfad: [frontend/src/store/useFlowStore.ts](../../../../../frontend/src/store/useFlowStore.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Zustand-Store fuer Graph, Auswahl, Undo/Redo und Laufzeitstatus.

## Wann du diese Datei bearbeitest

Wenn Editorverhalten oder Snapshot-Uebernahme angepasst werden.

## Exporte und oeffentliche Definitionen

- `useFlowStore`: Globaler Zustandsspeicher der UI auf Basis von Zustand.

## Wichtige interne Routinen

- `snapshotGraph`: Erzeugt einen unveraenderlichen Graph-Snapshot fuer Undo/Redo.
- `withHistory`: Haengt den aktuellen Zustand an die Undo-Historie an.
- `mergeSnapshotIntoNode`: Uebernimmt Runtime-Daten aus einem Backend-Snapshot in einen Editor-Node.

## Abhaengigkeiten

- `import {`
- `import { create } from "zustand";`
- `import { autoLayoutNodes } from "../lib/autoLayout";`
- `import {`
- `import type {`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [frontend/src/App.tsx](../App.tsx.md)
- [frontend/src/hooks/useFlowLiveUpdates.ts](../hooks/useFlowLiveUpdates.ts.md)

```

## File: `reference/frontend/src/types/api.ts.md`  
- Path: `reference/frontend/src/types/api.ts.md`  
- Size: 2554 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/types/api.ts`

- Quellpfad: [frontend/src/types/api.ts](../../../../../frontend/src/types/api.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

Gemeinsame TypeScript-Schemata fuer API, Snapshots und Editorgraph.

## Wann du diese Datei bearbeitest

Wenn Backend-Vertraege oder UI-Datentypen erweitert werden.

## Exporte und oeffentliche Definitionen

- `ResourceType`: TypeScript-Typ `ResourceType` fuer einen Datenvertrag.
- `RollbackStrategy`: TypeScript-Typ `RollbackStrategy` fuer einen Datenvertrag.
- `TaskStatus`: TypeScript-Typ `TaskStatus` fuer einen Datenvertrag.
- `FlowState`: TypeScript-Typ `FlowState` fuer einen Datenvertrag.
- `TaskFlowNode`: TypeScript-Typ `TaskFlowNode` fuer einen Datenvertrag.
- `TaskFlowEdge`: TypeScript-Typ `TaskFlowEdge` fuer einen Datenvertrag.
- `RetryPolicy`: TypeScript-Typ `RetryPolicy` fuer einen Datenvertrag.
- `AgentSummary`: TypeScript-Typ `AgentSummary` fuer einen Datenvertrag.
- `ResourceSummary`: TypeScript-Typ `ResourceSummary` fuer einen Datenvertrag.
- `TaskNodeData`: TypeScript-Typ `TaskNodeData` fuer einen Datenvertrag.
- `ConditionEdgeData`: TypeScript-Typ `ConditionEdgeData` fuer einen Datenvertrag.
- `TaskSpecModel`: TypeScript-Typ `TaskSpecModel` fuer einen Datenvertrag.
- `EdgeModel`: TypeScript-Typ `EdgeModel` fuer einen Datenvertrag.
- `FlowRequest`: TypeScript-Typ `FlowRequest` fuer einen Datenvertrag.
- `FlowNodeSnapshot`: TypeScript-Typ `FlowNodeSnapshot` fuer einen Datenvertrag.
- `FlowSnapshot`: TypeScript-Typ `FlowSnapshot` fuer einen Datenvertrag.
- `FlowEventMessage`: TypeScript-Typ `FlowEventMessage` fuer einen Datenvertrag.
- `EditorExport`: TypeScript-Typ `EditorExport` fuer einen Datenvertrag.
- `PlannerStatus`: TypeScript-Typ `PlannerStatus` fuer einen Datenvertrag.
- `PlannerGenerateRequest`: TypeScript-Typ `PlannerGenerateRequest` fuer einen Datenvertrag.
- `PlannerGenerateResponse`: TypeScript-Typ `PlannerGenerateResponse` fuer einen Datenvertrag.

## Abhaengigkeiten

- `import type { Edge, Node } from "@xyflow/react";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/api/app.py](../../../src/nova_synesis/api/app.py.md)
- [frontend/src/lib/flowSerialization.ts](../lib/flowSerialization.ts.md)

```

## File: `reference/frontend/src/vite-env.d.ts.md`  
- Path: `reference/frontend/src/vite-env.d.ts.md`  
- Size: 781 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/src/vite-env.d.ts`

- Quellpfad: [frontend/src/vite-env.d.ts](../../../../frontend/src/vite-env.d.ts)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Inhalt

Diese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/tsconfig.app.json.md`  
- Path: `reference/frontend/tsconfig.app.json.md`  
- Size: 878 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/tsconfig.app.json`

- Quellpfad: [frontend/tsconfig.app.json](../../../frontend/tsconfig.app.json)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/tsconfig.app.tsbuildinfo.md`  
- Path: `reference/frontend/tsconfig.app.tsbuildinfo.md`  
- Size: 933 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/tsconfig.app.tsbuildinfo`

- Quellpfad: [frontend/tsconfig.app.tsbuildinfo](../../../frontend/tsconfig.app.tsbuildinfo)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Generiertes Cache-Artefakt, das Builds oder Inferenz beschleunigt.

## Wann du diese Datei bearbeitest

Normalerweise nie direkt. Bei Bedarf loeschen und neu erzeugen lassen.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/tsconfig.json.md`  
- Path: `reference/frontend/tsconfig.json.md`  
- Size: 866 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/tsconfig.json`

- Quellpfad: [frontend/tsconfig.json](../../../frontend/tsconfig.json)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/tsconfig.node.json.md`  
- Path: `reference/frontend/tsconfig.node.json.md`  
- Size: 881 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/tsconfig.node.json`

- Quellpfad: [frontend/tsconfig.node.json](../../../frontend/tsconfig.node.json)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Konfigurationsdatei des Projekts.

## Wann du diese Datei bearbeitest

Wenn Build-, Paket- oder Compilerkonfiguration angepasst werden muss.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/tsconfig.node.tsbuildinfo.md`  
- Path: `reference/frontend/tsconfig.node.tsbuildinfo.md`  
- Size: 936 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/tsconfig.node.tsbuildinfo`

- Quellpfad: [frontend/tsconfig.node.tsbuildinfo](../../../frontend/tsconfig.node.tsbuildinfo)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Generiertes Cache-Artefakt, das Builds oder Inferenz beschleunigt.

## Wann du diese Datei bearbeitest

Normalerweise nie direkt. Bei Bedarf loeschen und neu erzeugen lassen.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/vite.config.d.ts.md`  
- Path: `reference/frontend/vite.config.d.ts.md`  
- Size: 789 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/vite.config.d.ts`

- Quellpfad: [frontend/vite.config.d.ts](../../../frontend/vite.config.d.ts)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Inhalt

Diese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/vite.config.js.md`  
- Path: `reference/frontend/vite.config.js.md`  
- Size: 822 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/vite.config.js`

- Quellpfad: [frontend/vite.config.js](../../../frontend/vite.config.js)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

Projektdatei mit eigener Rolle im Repository.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.

## Abhaengigkeiten

- `import { defineConfig } from "vite";`
- `import react from "@vitejs/plugin-react";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/frontend/vite.config.ts.md`  
- Path: `reference/frontend/vite.config.ts.md`  
- Size: 799 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `frontend/vite.config.ts`

- Quellpfad: [frontend/vite.config.ts](../../../frontend/vite.config.ts)
- Kategorie: `Frontend-Konfiguration`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Inhalt

Diese Datei dient als Bootstrap-, Deklarations- oder Konfigurationsmodul.

## Abhaengigkeiten

- `import { defineConfig } from "vite";`
- `import react from "@vitejs/plugin-react";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/index.md`  
- Path: `reference/index.md`  
- Size: 5506 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# Referenzindex

## Backend

- [src/nova_synesis/__init__.py](src/nova_synesis/__init__.py.md)
- [src/nova_synesis/api/__init__.py](src/nova_synesis/api/__init__.py.md)
- [src/nova_synesis/api/app.py](src/nova_synesis/api/app.py.md)
- [src/nova_synesis/cli.py](src/nova_synesis/cli.py.md)
- [src/nova_synesis/communication/__init__.py](src/nova_synesis/communication/__init__.py.md)
- [src/nova_synesis/communication/adapters.py](src/nova_synesis/communication/adapters.py.md)
- [src/nova_synesis/config.py](src/nova_synesis/config.py.md)
- [src/nova_synesis/domain/__init__.py](src/nova_synesis/domain/__init__.py.md)
- [src/nova_synesis/domain/models.py](src/nova_synesis/domain/models.py.md)
- [src/nova_synesis/memory/__init__.py](src/nova_synesis/memory/__init__.py.md)
- [src/nova_synesis/memory/systems.py](src/nova_synesis/memory/systems.py.md)
- [src/nova_synesis/persistence/__init__.py](src/nova_synesis/persistence/__init__.py.md)
- [src/nova_synesis/persistence/sqlite_repository.py](src/nova_synesis/persistence/sqlite_repository.py.md)
- [src/nova_synesis/planning/__init__.py](src/nova_synesis/planning/__init__.py.md)
- [src/nova_synesis/planning/lit_planner.py](src/nova_synesis/planning/lit_planner.py.md)
- [src/nova_synesis/planning/planner.py](src/nova_synesis/planning/planner.py.md)
- [src/nova_synesis/resources/__init__.py](src/nova_synesis/resources/__init__.py.md)
- [src/nova_synesis/resources/manager.py](src/nova_synesis/resources/manager.py.md)
- [src/nova_synesis/runtime/__init__.py](src/nova_synesis/runtime/__init__.py.md)
- [src/nova_synesis/runtime/engine.py](src/nova_synesis/runtime/engine.py.md)
- [src/nova_synesis/runtime/handlers.py](src/nova_synesis/runtime/handlers.py.md)
- [src/nova_synesis/services/__init__.py](src/nova_synesis/services/__init__.py.md)
- [src/nova_synesis/services/orchestrator.py](src/nova_synesis/services/orchestrator.py.md)

## Frontend

- [frontend/src/App.tsx](frontend/src/App.tsx.md)
- [frontend/src/app.css](frontend/src/app.css.md)
- [frontend/src/components/common/JsonEditor.tsx](frontend/src/components/common/JsonEditor.tsx.md)
- [frontend/src/components/common/StatusBadge.tsx](frontend/src/components/common/StatusBadge.tsx.md)
- [frontend/src/components/flow/FlowCanvas.tsx](frontend/src/components/flow/FlowCanvas.tsx.md)
- [frontend/src/components/flow/TaskNode.tsx](frontend/src/components/flow/TaskNode.tsx.md)
- [frontend/src/components/layout/InspectorPanel.tsx](frontend/src/components/layout/InspectorPanel.tsx.md)
- [frontend/src/components/layout/PlannerComposer.tsx](frontend/src/components/layout/PlannerComposer.tsx.md)
- [frontend/src/components/layout/Sidebar.tsx](frontend/src/components/layout/Sidebar.tsx.md)
- [frontend/src/components/layout/TopBar.tsx](frontend/src/components/layout/TopBar.tsx.md)
- [frontend/src/hooks/useCatalogBootstrap.ts](frontend/src/hooks/useCatalogBootstrap.ts.md)
- [frontend/src/hooks/useFlowLiveUpdates.ts](frontend/src/hooks/useFlowLiveUpdates.ts.md)
- [frontend/src/lib/apiClient.ts](frontend/src/lib/apiClient.ts.md)
- [frontend/src/lib/autoLayout.ts](frontend/src/lib/autoLayout.ts.md)
- [frontend/src/lib/flowSerialization.ts](frontend/src/lib/flowSerialization.ts.md)
- [frontend/src/lib/json.ts](frontend/src/lib/json.ts.md)
- [frontend/src/main.tsx](frontend/src/main.tsx.md)
- [frontend/src/store/useFlowStore.ts](frontend/src/store/useFlowStore.ts.md)
- [frontend/src/types/api.ts](frontend/src/types/api.ts.md)
- [frontend/src/vite-env.d.ts](frontend/src/vite-env.d.ts.md)

## Frontend-Konfiguration

- [frontend/.env](frontend/.env.md)
- [frontend/.env.example](frontend/.env.example.md)
- [frontend/index.html](frontend/index.html.md)
- [frontend/package-lock.json](frontend/package-lock.json.md)
- [frontend/package.json](frontend/package.json.md)
- [frontend/tsconfig.app.json](frontend/tsconfig.app.json.md)
- [frontend/tsconfig.app.tsbuildinfo](frontend/tsconfig.app.tsbuildinfo.md)
- [frontend/tsconfig.json](frontend/tsconfig.json.md)
- [frontend/tsconfig.node.json](frontend/tsconfig.node.json.md)
- [frontend/tsconfig.node.tsbuildinfo](frontend/tsconfig.node.tsbuildinfo.md)
- [frontend/vite.config.d.ts](frontend/vite.config.d.ts.md)
- [frontend/vite.config.js](frontend/vite.config.js.md)
- [frontend/vite.config.ts](frontend/vite.config.ts.md)

## LLM-Runtime

- [LIT/README.md](LIT/README.md.md)
- [LIT/gemma-4-E2B-it.litertlm](LIT/gemma-4-E2B-it.litertlm.md)
- [LIT/gemma-4-E2B-it.litertlm.xnnpack_cache](LIT/gemma-4-E2B-it.litertlm.xnnpack_cache.md)
- [LIT/lit.windows_x86_64.exe](LIT/lit.windows_x86_64.exe.md)
- [LIT/planner_test_prompt.txt](LIT/planner_test_prompt.txt.md)

## Projektdatei

- [.env.example](.env.example.md)
- [Agenten_UML.zip](Agenten_UML.zip.md)
- [Anweisung.md](Anweisung.md.md)
- [Dockerfile](Dockerfile.md)
- [README.md](README.md.md)
- [pyproject.toml](pyproject.toml.md)
- [run-backend.cmd](run-backend.cmd.md)
- [run-backend.ps1](run-backend.ps1.md)
- [uml.html](uml.html.md)
- [uml_V3.mmd](uml_V3.mmd.md)

## Tests

- [tests/test_orchestrator.py](tests/test_orchestrator.py.md)

## Werkzeug

- [tools/generate_docs.py](tools/generate_docs.py.md)

```

## File: `reference/LIT/gemma-4-E2B-it.litertlm.md`  
- Path: `reference/LIT/gemma-4-E2B-it.litertlm.md`  
- Size: 1057 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `LIT/gemma-4-E2B-it.litertlm`

- Quellpfad: [LIT/gemma-4-E2B-it.litertlm](../../../LIT/gemma-4-E2B-it.litertlm)
- Kategorie: `LLM-Runtime`

## Aufgabe der Datei

Lokales Modell fuer den autonomen Flow-Planer.

## Wann du diese Datei bearbeitest

Nur wenn ein anderes Planner-Modell eingesetzt wird.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [LIT/lit.windows_x86_64.exe](lit.windows_x86_64.exe.md)
- [src/nova_synesis/planning/lit_planner.py](../src/nova_synesis/planning/lit_planner.py.md)

```

## File: `reference/LIT/gemma-4-E2B-it.litertlm.xnnpack_cache.md`  
- Path: `reference/LIT/gemma-4-E2B-it.litertlm.xnnpack_cache.md`  
- Size: 946 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `LIT/gemma-4-E2B-it.litertlm.xnnpack_cache`

- Quellpfad: [LIT/gemma-4-E2B-it.litertlm.xnnpack_cache](../../../LIT/gemma-4-E2B-it.litertlm.xnnpack_cache)
- Kategorie: `LLM-Runtime`

## Aufgabe der Datei

Generiertes Cache-Artefakt, das Builds oder Inferenz beschleunigt.

## Wann du diese Datei bearbeitest

Normalerweise nie direkt. Bei Bedarf loeschen und neu erzeugen lassen.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/LIT/lit.windows_x86_64.exe.md`  
- Path: `reference/LIT/lit.windows_x86_64.exe.md`  
- Size: 1054 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `LIT/lit.windows_x86_64.exe`

- Quellpfad: [LIT/lit.windows_x86_64.exe](../../../LIT/lit.windows_x86_64.exe)
- Kategorie: `LLM-Runtime`

## Aufgabe der Datei

Windows-Binary fuer die lokale LiteRT-LM-Inferenz.

## Wann du diese Datei bearbeitest

Nur beim gezielten Update der lokalen Runtime.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [LIT/gemma-4-E2B-it.litertlm](gemma-4-E2B-it.litertlm.md)
- [src/nova_synesis/planning/lit_planner.py](../src/nova_synesis/planning/lit_planner.py.md)

```

## File: `reference/LIT/planner_test_prompt.txt.md`  
- Path: `reference/LIT/planner_test_prompt.txt.md`  
- Size: 888 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `LIT/planner_test_prompt.txt`

- Quellpfad: [LIT/planner_test_prompt.txt](../../../LIT/planner_test_prompt.txt)
- Kategorie: `LLM-Runtime`

## Aufgabe der Datei

Projektdatei mit eigener Rolle im Repository.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/LIT/README.md.md`  
- Path: `reference/LIT/README.md.md`  
- Size: 1005 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `LIT/README.md`

- Quellpfad: [LIT/README.md](../../../LIT/README.md)
- Kategorie: `LLM-Runtime`

## Aufgabe der Datei

Hinweise zur lokalen LiteRT-LM-Laufzeit und zu Modelldateien.

## Wann du diese Datei bearbeitest

Wenn Binary- oder Modellsetup aktualisiert wird.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/planning/lit_planner.py](../src/nova_synesis/planning/lit_planner.py.md)
- [.env.example](../.env.example.md)

```

## File: `reference/pyproject.toml.md`  
- Path: `reference/pyproject.toml.md`  
- Size: 1024 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `pyproject.toml`

- Quellpfad: [pyproject.toml](../../pyproject.toml)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Python-Paketdefinition mit Abhaengigkeiten, CLI und Testkonfiguration.

## Wann du diese Datei bearbeitest

Wenn Python-Abhaengigkeiten, Packaging oder Skripte geaendert werden.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/cli.py](src/nova_synesis/cli.py.md)
- [tests/test_orchestrator.py](tests/test_orchestrator.py.md)

```

## File: `reference/README.md.md`  
- Path: `reference/README.md.md`  
- Size: 979 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `README.md`

- Quellpfad: [README.md](../../README.md)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Projektweiter Schnellstart fuer Backend, Frontend und Planner.

## Wann du diese Datei bearbeitest

Wenn sich Startablauf oder Hauptfunktionen fuer Entwickler aendern.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- docs/README.md
- [run-backend.ps1](run-backend.ps1.md)
- [frontend/package.json](frontend/package.json.md)

```

## File: `reference/run-backend.cmd.md`  
- Path: `reference/run-backend.cmd.md`  
- Size: 843 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `run-backend.cmd`

- Quellpfad: [run-backend.cmd](../../run-backend.cmd)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Skript fuer lokale Entwicklerablaeufe.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/run-backend.ps1.md`  
- Path: `reference/run-backend.ps1.md`  
- Size: 983 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `run-backend.ps1`

- Quellpfad: [run-backend.ps1](../../run-backend.ps1)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Empfohlenes Windows-Startskript fuer das Backend.

## Wann du diese Datei bearbeitest

Wenn der lokale Backend-Start fuer Entwickler angepasst werden soll.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/cli.py](src/nova_synesis/cli.py.md)
- [run-backend.cmd](run-backend.cmd.md)

```

## File: `reference/src/nova_synesis/__init__.py.md`  
- Path: `reference/src/nova_synesis/__init__.py.md`  
- Size: 953 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/__init__.py`

- Quellpfad: [src/nova_synesis/__init__.py](../../../../src/nova_synesis/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.api.app import create_app`
- `from nova_synesis.config import Settings`
- `from nova_synesis.services.orchestrator import OrchestratorService, create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/api/__init__.py.md`  
- Path: `reference/src/nova_synesis/api/__init__.py.md`  
- Size: 817 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/api/__init__.py`

- Quellpfad: [src/nova_synesis/api/__init__.py](../../../../../src/nova_synesis/api/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.api.app import create_app`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/api/app.py.md`  
- Path: `reference/src/nova_synesis/api/app.py.md`  
- Size: 2676 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/api/app.py`

- Quellpfad: [src/nova_synesis/api/app.py](../../../../../src/nova_synesis/api/app.py)
- Kategorie: `Backend`

## Aufgabe der Datei

FastAPI- und WebSocket-Schicht des Backends inklusive Request-Modelle.

## Wann du diese Datei bearbeitest

Wenn API-Endpunkte, Schemafelder oder Live-Streaming erweitert werden.

## Klassen

### `CapabilityModel`

Datenmodell `CapabilityModel` fuer validierte Schichtgrenzen.

### `CommunicationModel`

Datenmodell `CommunicationModel` fuer validierte Schichtgrenzen.

### `AgentCreateRequest`

Datenmodell `AgentCreateRequest` fuer validierte Schichtgrenzen.

### `MemorySystemCreateRequest`

Datenmodell `MemorySystemCreateRequest` fuer validierte Schichtgrenzen.

### `ResourceCreateRequest`

Datenmodell `ResourceCreateRequest` fuer validierte Schichtgrenzen.

### `RetryPolicyModel`

Datenmodell `RetryPolicyModel` fuer validierte Schichtgrenzen.

### `TaskSpecModel`

Datenmodell `TaskSpecModel` fuer validierte Schichtgrenzen.

### `EdgeModel`

Datenmodell `EdgeModel` fuer validierte Schichtgrenzen.

### `FlowCreateRequest`

Datenmodell `FlowCreateRequest` fuer validierte Schichtgrenzen.

### `IntentRequest`

Datenmodell `IntentRequest` fuer validierte Schichtgrenzen.

### `LLMPlannerRequest`

Datenmodell `LLMPlannerRequest` fuer validierte Schichtgrenzen.

## Funktionen

- `create_app(settings, orchestrator)`: Erzeugt die FastAPI-Anwendung und registriert ihre Endpunkte.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `from contextlib import asynccontextmanager`
- `from typing import Any`
- `from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect`
- `from fastapi.middleware.cors import CORSMiddleware`
- `from pydantic import BaseModel, Field`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import MemoryType, ProtocolType, ResourceType, RollbackStrategy`
- `from nova_synesis.services.orchestrator import OrchestratorService, create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)
- [frontend/src/lib/apiClient.ts](../../../frontend/src/lib/apiClient.ts.md)
- [frontend/src/types/api.ts](../../../frontend/src/types/api.ts.md)

```

## File: `reference/src/nova_synesis/cli.py.md`  
- Path: `reference/src/nova_synesis/cli.py.md`  
- Size: 1621 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/cli.py`

- Quellpfad: [src/nova_synesis/cli.py](../../../../src/nova_synesis/cli.py)
- Kategorie: `Backend`

## Aufgabe der Datei

CLI-Einstiegspunkt fuer API-Start, Flow-Ausfuehrung und lokale Hilfsaufgaben.

## Wann du diese Datei bearbeitest

Wenn neue CLI-Kommandos oder Startoptionen hinzukommen.

## Funktionen

- `build_parser()`: Funktion oder Definition `build_parser` dieses Moduls.
- `_build_settings(args)`: Funktion oder Definition `_build_settings` dieses Moduls.
- `_execute_intent_from_file(file_path, settings)`: Funktion oder Definition `_execute_intent_from_file` dieses Moduls.
- `_run_flow_spec_from_file(file_path, settings)`: Funktion oder Definition `_run_flow_spec_from_file` dieses Moduls.
- `main()`: Funktion oder Definition `main` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import argparse`
- `import asyncio`
- `import json`
- `from pathlib import Path`
- `from typing import Any`
- `import uvicorn`
- `from nova_synesis.api.app import create_app`
- `from nova_synesis.config import Settings`
- `from nova_synesis.services.orchestrator import create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [run-backend.ps1](../../run-backend.ps1.md)
- [pyproject.toml](../../pyproject.toml.md)

```

## File: `reference/src/nova_synesis/communication/__init__.py.md`  
- Path: `reference/src/nova_synesis/communication/__init__.py.md`  
- Size: 879 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/communication/__init__.py`

- Quellpfad: [src/nova_synesis/communication/__init__.py](../../../../../src/nova_synesis/communication/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.communication.adapters import CommunicationAdapterFactory`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/communication/adapters.py.md`  
- Path: `reference/src/nova_synesis/communication/adapters.py.md`  
- Size: 2998 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/communication/adapters.py`

- Quellpfad: [src/nova_synesis/communication/adapters.py](../../../../../src/nova_synesis/communication/adapters.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Klassen

### `CommunicationAdapter`

Klasse `CommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, protocol, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.
- `close(self)`: Funktion oder Definition `close` dieses Moduls.

### `RestCommunicationAdapter`

Klasse `RestCommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_get_client(self)`: Funktion oder Definition `_get_client` dieses Moduls.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.
- `close(self)`: Funktion oder Definition `close` dieses Moduls.

### `WebSocketCommunicationAdapter`

Klasse `WebSocketCommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_get_connection(self)`: Funktion oder Definition `_get_connection` dieses Moduls.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.
- `close(self)`: Funktion oder Definition `close` dieses Moduls.

### `MessageQueueCommunicationAdapter`

Klasse `MessageQueueCommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_get_queue(self, endpoint)`: Funktion oder Definition `_get_queue` dieses Moduls.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.

### `CommunicationAdapterFactory`

Factory-Klasse `CommunicationAdapterFactory` zum Erzeugen passender Objekte.

Methoden:

- `create(protocol, endpoint, config)`: Funktion oder Definition `create` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import json`
- `from typing import Any`
- `import httpx`
- `import websockets`
- `from nova_synesis.domain.models import ProtocolType`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/config.py.md`  
- Path: `reference/src/nova_synesis/config.py.md`  
- Size: 1157 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/config.py`

- Quellpfad: [src/nova_synesis/config.py](../../../../src/nova_synesis/config.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Zentrale Laufzeitkonfiguration des Backends.

## Wann du diese Datei bearbeitest

Wenn neue Settings, Standardpfade oder Planner-Optionen benoetigt werden.

## Klassen

### `Settings`

Dataklasse fuer die Backend-Laufzeitkonfiguration.

Methoden:

- `from_env(cls)`: Laedt Settings aus Umgebungsvariablen mit sicheren Defaults.
- `ensure_directories(self)`: Erzeugt benoetigte Daten- und Arbeitsverzeichnisse.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import os`
- `from dataclasses import dataclass`
- `from pathlib import Path`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [.env.example](../../.env.example.md)
- [src/nova_synesis/cli.py](cli.py.md)

```

## File: `reference/src/nova_synesis/domain/__init__.py.md`  
- Path: `reference/src/nova_synesis/domain/__init__.py.md`  
- Size: 823 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/domain/__init__.py`

- Quellpfad: [src/nova_synesis/domain/__init__.py](../../../../../src/nova_synesis/domain/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.domain.models import (`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/domain/models.py.md`  
- Path: `reference/src/nova_synesis/domain/models.py.md`  
- Size: 6721 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/domain/models.py`

- Quellpfad: [src/nova_synesis/domain/models.py](../../../../../src/nova_synesis/domain/models.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Kern-Domaenenmodell mit Agenten, Ressourcen, Tasks, Bedingungen und ExecutionFlow.

## Wann du diese Datei bearbeitest

Wenn das fachliche Laufzeitmodell des Systems veraendert wird.

## Klassen

### `AgentState`

Klasse `AgentState` dieses Moduls.

### `ProtocolType`

Klasse `ProtocolType` dieses Moduls.

### `MemoryType`

Klasse `MemoryType` dieses Moduls.

### `TaskStatus`

Klasse `TaskStatus` dieses Moduls.

### `ExecutionStatus`

Klasse `ExecutionStatus` dieses Moduls.

### `RollbackStrategy`

Klasse `RollbackStrategy` dieses Moduls.

### `ResourceType`

Klasse `ResourceType` dieses Moduls.

### `ResourceState`

Klasse `ResourceState` dieses Moduls.

### `FlowState`

Klasse `FlowState` dieses Moduls.

### `Capability`

Klasse `Capability` dieses Moduls.

### `RetryPolicy`

Klasse `RetryPolicy` dieses Moduls.

Methoden:

- `next_delay(self, attempt)`: Funktion oder Definition `next_delay` dieses Moduls.

### `ErrorEvent`

Klasse `ErrorEvent` dieses Moduls.

Methoden:

- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.

### `SafeExpressionEvaluator`

Klasse `SafeExpressionEvaluator` dieses Moduls.

Methoden:

- `__init__(self, context)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `evaluate(self, expression)`: Funktion oder Definition `evaluate` dieses Moduls.
- `visit_Name(self, node)`: AST-Besuchsmethode fuer `Name`-Knoten.
- `visit_Constant(self, node)`: AST-Besuchsmethode fuer `Constant`-Knoten.
- `visit_List(self, node)`: AST-Besuchsmethode fuer `List`-Knoten.
- `visit_Tuple(self, node)`: AST-Besuchsmethode fuer `Tuple`-Knoten.
- `visit_Dict(self, node)`: AST-Besuchsmethode fuer `Dict`-Knoten.
- `visit_BoolOp(self, node)`: AST-Besuchsmethode fuer `BoolOp`-Knoten.
- `visit_UnaryOp(self, node)`: AST-Besuchsmethode fuer `UnaryOp`-Knoten.
- `visit_BinOp(self, node)`: AST-Besuchsmethode fuer `BinOp`-Knoten.
- `visit_Compare(self, node)`: AST-Besuchsmethode fuer `Compare`-Knoten.
- `visit_Subscript(self, node)`: AST-Besuchsmethode fuer `Subscript`-Knoten.
- `visit_Call(self, node)`: AST-Besuchsmethode fuer `Call`-Knoten.
- `generic_visit(self, node)`: Funktion oder Definition `generic_visit` dieses Moduls.

### `Condition`

Klasse `Condition` dieses Moduls.

Methoden:

- `evaluate(self, context)`: Funktion oder Definition `evaluate` dieses Moduls.

### `Resource`

Klasse `Resource` dieses Moduls.

Methoden:

- `__post_init__(self)`: Funktion oder Definition `__post_init__` dieses Moduls.
- `capacity(self)`: Funktion oder Definition `capacity` dieses Moduls.
- `acquire(self, timeout)`: Funktion oder Definition `acquire` dieses Moduls.
- `release(self)`: Funktion oder Definition `release` dieses Moduls.
- `health_check(self)`: Funktion oder Definition `health_check` dieses Moduls.

### `Agent`

Klasse `Agent` dieses Moduls.

Methoden:

- `capability_index(self)`: Funktion oder Definition `capability_index` dieses Moduls.
- `can_execute(self, required_capabilities)`: Funktion oder Definition `can_execute` dieses Moduls.
- `perceive(self, input_data)`: Funktion oder Definition `perceive` dieses Moduls.
- `decide(self, context)`: Funktion oder Definition `decide` dieses Moduls.
- `act(self, task)`: Funktion oder Definition `act` dieses Moduls.
- `communicate(self, message, target, protocol)`: Funktion oder Definition `communicate` dieses Moduls.

### `Task`

Klasse `Task` dieses Moduls.

Methoden:

- `execute(self)`: Fuehrt die Kernarbeit von `execute` aus.
- `validate(self, result)`: Funktion oder Definition `validate` dieses Moduls.
- `complete(self, output)`: Funktion oder Definition `complete` dieses Moduls.
- `reset(self)`: Funktion oder Definition `reset` dieses Moduls.

### `TaskExecution`

Klasse `TaskExecution` dieses Moduls.

Methoden:

- `start(self)`: Funktion oder Definition `start` dieses Moduls.
- `finish(self, result)`: Funktion oder Definition `finish` dieses Moduls.
- `record_error(self, error)`: Funktion oder Definition `record_error` dieses Moduls.
- `rollback(self, strategy)`: Funktion oder Definition `rollback` dieses Moduls.
- `retry(self)`: Funktion oder Definition `retry` dieses Moduls.

### `Intent`

Klasse `Intent` dieses Moduls.

Methoden:

- `refine(self, updates)`: Funktion oder Definition `refine` dieses Moduls.
- `plan(self, planner, agents, resources, task_id_allocator, flow_id_allocator)`: Funktion oder Definition `plan` dieses Moduls.
- `promote_to_task(self, planner, agents, resources, task_id_allocator)`: Funktion oder Definition `promote_to_task` dieses Moduls.

### `FlowNode`

Klasse `FlowNode` dieses Moduls.

### `FlowEdge`

Klasse `FlowEdge` dieses Moduls.

### `ExecutionFlow`

Graph-Modell des ausfuehrbaren Workflows.

Methoden:

- `add_node(self, node)`: Funktion oder Definition `add_node` dieses Moduls.
- `add_edge(self, edge)`: Funktion oder Definition `add_edge` dieses Moduls.
- `incoming_edges(self, node_id)`: Funktion oder Definition `incoming_edges` dieses Moduls.
- `outgoing_edges(self, node_id)`: Funktion oder Definition `outgoing_edges` dieses Moduls.
- `run(self, executor)`: Steuert den Ablauf von `run`.
- `pause(self)`: Funktion oder Definition `pause` dieses Moduls.
- `observe(self)`: Erzeugt den serialisierbaren Zustand eines Flows fuer API und UI.

## Funktionen

- `utcnow()`: Funktion oder Definition `utcnow` dieses Moduls.
- `maybe_await(value)`: Funktion oder Definition `maybe_await` dieses Moduls.
- `safe_evaluate(expression, context)`: Funktion oder Definition `safe_evaluate` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import ast`
- `import asyncio`
- `import sqlite3`
- `from dataclasses import dataclass, field`
- `from datetime import datetime, timezone`
- `from enum import StrEnum`
- `from pathlib import Path`
- `from random import uniform`
- `from typing import TYPE_CHECKING, Any, Callable`
- `import httpx`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/engine.py](../runtime/engine.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)

```

## File: `reference/src/nova_synesis/memory/__init__.py.md`  
- Path: `reference/src/nova_synesis/memory/__init__.py.md`  
- Size: 857 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/memory/__init__.py`

- Quellpfad: [src/nova_synesis/memory/__init__.py](../../../../../src/nova_synesis/memory/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.memory.systems import MemoryManager, MemorySystemFactory`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/memory/systems.py.md`  
- Path: `reference/src/nova_synesis/memory/systems.py.md`  
- Size: 4981 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/memory/systems.py`

- Quellpfad: [src/nova_synesis/memory/systems.py](../../../../../src/nova_synesis/memory/systems.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Implementierungen fuer Kurzzeit-, Langzeit- und Vektor-Speicher.

## Wann du diese Datei bearbeitest

Wenn Speicherverhalten, Suche oder Persistenz geaendert werden.

## Klassen

### `MemorySearchHit`

Klasse `MemorySearchHit` dieses Moduls.

Methoden:

- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.

### `MemorySystem`

Klasse `MemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, memory_type, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `ShortTermMemorySystem`

Klasse `ShortTermMemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_load_from_disk(self)`: Funktion oder Definition `_load_from_disk` dieses Moduls.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `_score_value(self, value, query)`: Funktion oder Definition `_score_value` dieses Moduls.
- `_extract_embedding(value)`: Funktion oder Definition `_extract_embedding` dieses Moduls.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `LongTermMemorySystem`

Klasse `LongTermMemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `VectorMemorySystem`

Klasse `VectorMemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `MemorySystemFactory`

Factory-Klasse `MemorySystemFactory` zum Erzeugen passender Objekte.

Methoden:

- `create(memory_id, memory_type, backend, config)`: Funktion oder Definition `create` dieses Moduls.

### `MemoryManager`

Koordinationsklasse `MemoryManager` fuer mehrere Instanzen oder Zustandsobjekte.

Methoden:

- `__init__(self)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register(self, system)`: Registriert Verhalten oder Objekte fuer `register`.
- `get(self, memory_id)`: Funktion oder Definition `get` dieses Moduls.
- `list(self)`: Funktion oder Definition `list` dieses Moduls.
- `store(self, memory_id, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, memory_id, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, memory_id, query, limit)`: Sucht passende Daten fuer `search`.
- `persist_all(self)`: Schreibt Daten fuer `persist_all` in einen dauerhaften Speicher.

## Funktionen

- `utcnow_iso()`: Funktion oder Definition `utcnow_iso` dieses Moduls.
- `cosine_similarity(left, right)`: Funktion oder Definition `cosine_similarity` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import json`
- `import math`
- `import sqlite3`
- `from abc import ABC, abstractmethod`
- `from collections import OrderedDict`
- `from dataclasses import dataclass, field`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import Any`
- `from nova_synesis.domain.models import MemoryType`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/handlers.py](../runtime/handlers.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)

```

## File: `reference/src/nova_synesis/persistence/__init__.py.md`  
- Path: `reference/src/nova_synesis/persistence/__init__.py.md`  
- Size: 869 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/persistence/__init__.py`

- Quellpfad: [src/nova_synesis/persistence/__init__.py](../../../../../src/nova_synesis/persistence/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.persistence.sqlite_repository import SQLiteRepository`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/persistence/sqlite_repository.py.md`  
- Path: `reference/src/nova_synesis/persistence/sqlite_repository.py.md`  
- Size: 2524 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/persistence/sqlite_repository.py`

- Quellpfad: [src/nova_synesis/persistence/sqlite_repository.py](../../../../../src/nova_synesis/persistence/sqlite_repository.py)
- Kategorie: `Backend`

## Aufgabe der Datei

SQLite-Persistenzschicht fuer Flows, Ausfuehrungen und Katalogobjekte.

## Wann du diese Datei bearbeitest

Wenn Datenbankstruktur oder gespeicherte Felder angepasst werden.

## Klassen

### `SQLiteRepository`

Persistenzschicht fuer SQLite.

Methoden:

- `__init__(self, database_path)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_initialize_schema(self)`: Funktion oder Definition `_initialize_schema` dieses Moduls.
- `next_id(self, name)`: Funktion oder Definition `next_id` dieses Moduls.
- `save_agent(self, agent)`: Persistiert Daten fuer `save_agent` dauerhaft.
- `save_memory_system(self, memory_system)`: Persistiert Daten fuer `save_memory_system` dauerhaft.
- `save_resource(self, resource)`: Persistiert Daten fuer `save_resource` dauerhaft.
- `save_intent(self, intent)`: Persistiert Daten fuer `save_intent` dauerhaft.
- `save_task(self, task)`: Persistiert Daten fuer `save_task` dauerhaft.
- `save_flow(self, flow)`: Persistiert Daten fuer `save_flow` dauerhaft.
- `save_execution(self, execution, flow_id)`: Persistiert Daten fuer `save_execution` dauerhaft.
- `list_executions(self)`: Gibt eine Liste von Daten fuer `list_executions` zurueck.
- `get_flow_record(self, flow_id)`: Liest Daten fuer `get_flow_record` aus einem Speicher oder einer Laufzeitquelle.
- `_decode_execution_row(row)`: Funktion oder Definition `_decode_execution_row` dieses Moduls.
- `_decode_flow_row(row)`: Funktion oder Definition `_decode_flow_row` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import json`
- `import sqlite3`
- `import threading`
- `from pathlib import Path`
- `from typing import Any`
- `from nova_synesis.domain.models import Agent, ExecutionFlow, Intent, Resource, Task, TaskExecution`
- `from nova_synesis.memory.systems import MemorySystem`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)

```

## File: `reference/src/nova_synesis/planning/__init__.py.md`  
- Path: `reference/src/nova_synesis/planning/__init__.py.md`  
- Size: 951 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/planning/__init__.py`

- Quellpfad: [src/nova_synesis/planning/__init__.py](../../../../../src/nova_synesis/planning/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.planning.planner import IntentPlanner`
- `from nova_synesis.planning.lit_planner import LiteRTPlanner, PlannerCatalog, PlannerGraphResult`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/planning/lit_planner.py.md`  
- Path: `reference/src/nova_synesis/planning/lit_planner.py.md`  
- Size: 3853 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/planning/lit_planner.py`

- Quellpfad: [src/nova_synesis/planning/lit_planner.py](../../../../../src/nova_synesis/planning/lit_planner.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Lokaler LLM-Planer ueber LiteRT-LM inklusive Prompting, Parsing und Normalisierung.

## Wann du diese Datei bearbeitest

Wenn Planner-Qualitaet, Modellaufruf oder Validierung verbessert werden soll.

## Klassen

### `PlannerCatalog`

Klasse `PlannerCatalog` dieses Moduls.

### `PlannerGraphResult`

Klasse `PlannerGraphResult` dieses Moduls.

### `LiteRTPlanner`

Lokale LLM-Planung ueber LiteRT-LM.

Methoden:

- `__init__(self, settings)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `status(self)`: Funktion oder Definition `status` dieses Moduls.
- `ensure_available(self)`: Funktion oder Definition `ensure_available` dieses Moduls.
- `generate_flow_request(self, prompt, catalog, current_flow, max_nodes)`: Erzeugt aus natuerlicher Sprache einen validierten FlowRequest.
- `_invoke_model(self, planner_prompt)`: Funktion oder Definition `_invoke_model` dieses Moduls.
- `_build_prompt(self, prompt, catalog, current_flow, max_nodes)`: Funktion oder Definition `_build_prompt` dieses Moduls.
- `_extract_explanation(parsed)`: Funktion oder Definition `_extract_explanation` dieses Moduls.
- `_parse_model_output(self, raw_response)`: Funktion oder Definition `_parse_model_output` dieses Moduls.
- `_extract_json_object(text)`: Funktion oder Definition `_extract_json_object` dieses Moduls.
- `_normalize_flow_request(self, parsed, catalog, max_nodes)`: Funktion oder Definition `_normalize_flow_request` dieses Moduls.
- `_normalize_node_id(raw_value)`: Funktion oder Definition `_normalize_node_id` dieses Moduls.
- `_normalize_object(raw_value)`: Funktion oder Definition `_normalize_object` dieses Moduls.
- `_normalize_string_list(raw_value)`: Funktion oder Definition `_normalize_string_list` dieses Moduls.
- `_normalize_conditions(raw_value)`: Funktion oder Definition `_normalize_conditions` dieses Moduls.
- `_normalize_retry_policy(raw_value)`: Funktion oder Definition `_normalize_retry_policy` dieses Moduls.
- `_normalize_compensation_handler(raw_value, allowed_handlers, warnings, node_id)`: Funktion oder Definition `_normalize_compensation_handler` dieses Moduls.
- `_normalize_edges(raw_edges, node_ids, warnings)`: Funktion oder Definition `_normalize_edges` dieses Moduls.
- `_merge_dependencies(normalized_nodes, normalized_edges)`: Funktion oder Definition `_merge_dependencies` dieses Moduls.
- `_validate_acyclic(normalized_nodes)`: Funktion oder Definition `_validate_acyclic` dieses Moduls.
- `_normalize_handler_input(handler_name, input_payload, node_id, dependencies, memory_ids, comm_agent_ids, warnings)`: Funktion oder Definition `_normalize_handler_input` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import json`
- `import re`
- `import subprocess`
- `import tempfile`
- `from dataclasses import dataclass`
- `from pathlib import Path`
- `from typing import Any`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import ResourceType, RollbackStrategy`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [LIT/lit.windows_x86_64.exe](../../../LIT/lit.windows_x86_64.exe.md)
- [LIT/gemma-4-E2B-it.litertlm](../../../LIT/gemma-4-E2B-it.litertlm.md)
- [frontend/src/components/layout/PlannerComposer.tsx](../../../frontend/src/components/layout/PlannerComposer.tsx.md)

```

## File: `reference/src/nova_synesis/planning/planner.py.md`  
- Path: `reference/src/nova_synesis/planning/planner.py.md`  
- Size: 2128 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/planning/planner.py`

- Quellpfad: [src/nova_synesis/planning/planner.py](../../../../../src/nova_synesis/planning/planner.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Regelbasierter Intent-zu-Task-Planer.

## Wann du diese Datei bearbeitest

Wenn strukturierte Intents anders in Tasks zerlegt werden sollen.

## Klassen

### `TaskBlueprint`

Klasse `TaskBlueprint` dieses Moduls.

### `IntentPlanner`

Regelbasierter Planer fuer strukturierte Intents.

Methoden:

- `plan_intent(self, intent, agents, resources, task_id_allocator, flow_id_allocator)`: Funktion oder Definition `plan_intent` dieses Moduls.
- `promote_to_task(self, intent, agents, resources, task_id_allocator)`: Funktion oder Definition `promote_to_task` dieses Moduls.
- `_extract_blueprints(self, intent)`: Funktion oder Definition `_extract_blueprints` dieses Moduls.
- `_build_retry_policy(raw_policy)`: Funktion oder Definition `_build_retry_policy` dieses Moduls.
- `_normalize_resource_type(value)`: Funktion oder Definition `_normalize_resource_type` dieses Moduls.
- `_group_resources_by_type(resources)`: Funktion oder Definition `_group_resources_by_type` dieses Moduls.
- `_resolve_resources(self, blueprint, resource_index, resources_by_type)`: Funktion oder Definition `_resolve_resources` dieses Moduls.
- `_select_agent(self, blueprint, agents)`: Funktion oder Definition `_select_agent` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `from dataclasses import dataclass, field`
- `from typing import Any, Callable`
- `from nova_synesis.domain.models import (`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/domain/models.py](../domain/models.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)

```

## File: `reference/src/nova_synesis/resources/__init__.py.md`  
- Path: `reference/src/nova_synesis/resources/__init__.py.md`  
- Size: 850 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/resources/__init__.py`

- Quellpfad: [src/nova_synesis/resources/__init__.py](../../../../../src/nova_synesis/resources/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.resources.manager import ResourceManager`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/resources/manager.py.md`  
- Path: `reference/src/nova_synesis/resources/manager.py.md`  
- Size: 1946 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/resources/manager.py`

- Quellpfad: [src/nova_synesis/resources/manager.py](../../../../../src/nova_synesis/resources/manager.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Verwaltung und Aufloesung registrierter Ressourcen.

## Wann du diese Datei bearbeitest

Wenn Ressourcenallokation oder Fallbacks angepasst werden.

## Klassen

### `ResourceManager`

Koordinationsklasse `ResourceManager` fuer mehrere Instanzen oder Zustandsobjekte.

Methoden:

- `__init__(self)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register(self, resource)`: Registriert Verhalten oder Objekte fuer `register`.
- `get(self, resource_id)`: Funktion oder Definition `get` dieses Moduls.
- `list(self)`: Funktion oder Definition `list` dieses Moduls.
- `resolve_resources(self, resource_ids, resource_types)`: Funktion oder Definition `resolve_resources` dieses Moduls.
- `acquire_many(self, resources, timeout)`: Funktion oder Definition `acquire_many` dieses Moduls.
- `release_many(self, resources)`: Funktion oder Definition `release_many` dieses Moduls.
- `health_report(self)`: Funktion oder Definition `health_report` dieses Moduls.
- `find_fallback_resources(self, required_resources)`: Funktion oder Definition `find_fallback_resources` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `from collections import defaultdict`
- `from typing import Iterable`
- `from nova_synesis.domain.models import Resource, ResourceState, ResourceType`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/engine.py](../runtime/engine.py.md)

```

## File: `reference/src/nova_synesis/runtime/__init__.py.md`  
- Path: `reference/src/nova_synesis/runtime/__init__.py.md`  
- Size: 970 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/runtime/__init__.py`

- Quellpfad: [src/nova_synesis/runtime/__init__.py](../../../../../src/nova_synesis/runtime/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.runtime.engine import ExecutionContext, FlowExecutor, TaskExecutor`
- `from nova_synesis.runtime.handlers import TaskHandlerRegistry, register_default_handlers`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/runtime/engine.py.md`  
- Path: `reference/src/nova_synesis/runtime/engine.py.md`  
- Size: 2894 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/runtime/engine.py`

- Quellpfad: [src/nova_synesis/runtime/engine.py](../../../../../src/nova_synesis/runtime/engine.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Graph-Ausfuehrungsengine fuer Task- und Flow-Lifecycle.

## Wann du diese Datei bearbeitest

Wenn Ablaufsteuerung, Parallelitaet oder Snapshot-Logik geaendert wird.

## Klassen

### `ExecutionContext`

Klasse `ExecutionContext` dieses Moduls.

### `TaskExecutor`

Fuehrt eine einzelne Task inklusive Fehlerbehandlung aus.

Methoden:

- `__init__(self, context)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `execute_task(self, task, flow, flow_results, node_id)`: Fuehrt die Kernarbeit von `execute_task` aus.
- `_publish_task_event(self, flow_id, event_type, snapshot)`: Funktion oder Definition `_publish_task_event` dieses Moduls.

### `FlowExecutor`

Fuehrt einen gesamten Workflow-Graphen aus.

Methoden:

- `__init__(self, context, task_executor)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `run_flow(self, flow)`: Steuert den Ablauf von `run_flow`.
- `_is_ready(self, flow, node_id, completed, blocked, failed)`: Funktion oder Definition `_is_ready` dieses Moduls.
- `_is_blocked(self, flow, node_id, completed, blocked, failed)`: Funktion oder Definition `_is_blocked` dieses Moduls.
- `_snapshot(flow, completed, blocked, failed)`: Funktion oder Definition `_snapshot` dieses Moduls.
- `_publish_snapshot(self, flow, completed, blocked, failed, event_type)`: Funktion oder Definition `_publish_snapshot` dieses Moduls.
- `_publish_event(self, flow_id, event_type, snapshot)`: Funktion oder Definition `_publish_event` dieses Moduls.

## Funktionen

- `resolve_templates(value, context)`: Funktion oder Definition `resolve_templates` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import re`
- `from collections.abc import Awaitable, Callable`
- `from dataclasses import dataclass`
- `from pathlib import Path`
- `from typing import Any`
- `from nova_synesis.domain.models import (`
- `from nova_synesis.memory.systems import MemoryManager`
- `from nova_synesis.persistence.sqlite_repository import SQLiteRepository`
- `from nova_synesis.resources.manager import ResourceManager`
- `from nova_synesis.runtime.handlers import TaskHandlerRegistry`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/domain/models.py](../domain/models.py.md)
- [src/nova_synesis/runtime/handlers.py](handlers.py.md)

```

## File: `reference/src/nova_synesis/runtime/handlers.py.md`  
- Path: `reference/src/nova_synesis/runtime/handlers.py.md`  
- Size: 3179 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/runtime/handlers.py`

- Quellpfad: [src/nova_synesis/runtime/handlers.py](../../../../../src/nova_synesis/runtime/handlers.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Eingebaute Handler fuer HTTP, Memory, Messaging, Dateien und Serialisierung.

## Wann du diese Datei bearbeitest

Wenn neue Arbeitsbausteine hinzugefuegt oder bestehende Handler verbessert werden.

## Klassen

### `TaskHandlerRegistry`

Registry der registrierten Runtime-Handler.

Methoden:

- `__init__(self)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register(self, name, handler)`: Registriert Verhalten oder Objekte fuer `register`.
- `get(self, name)`: Funktion oder Definition `get` dieses Moduls.
- `names(self)`: Funktion oder Definition `names` dieses Moduls.
- `execute(self, name, context)`: Fuehrt die Kernarbeit von `execute` aus.

## Funktionen

- `_resolve_working_path(working_directory, raw_path, allow_outside_workdir)`: Funktion oder Definition `_resolve_working_path` dieses Moduls.
- `_primary_resource_endpoint(context, resource_type)`: Funktion oder Definition `_primary_resource_endpoint` dieses Moduls.
- `http_request_handler(context)`: Funktion oder Definition `http_request_handler` dieses Moduls.
- `memory_store_handler(context)`: Funktion oder Definition `memory_store_handler` dieses Moduls.
- `memory_retrieve_handler(context)`: Funktion oder Definition `memory_retrieve_handler` dieses Moduls.
- `memory_search_handler(context)`: Funktion oder Definition `memory_search_handler` dieses Moduls.
- `send_message_handler(context)`: Funktion oder Definition `send_message_handler` dieses Moduls.
- `resource_health_check_handler(context)`: Funktion oder Definition `resource_health_check_handler` dieses Moduls.
- `template_render_handler(context)`: Funktion oder Definition `template_render_handler` dieses Moduls.
- `merge_payloads_handler(context)`: Funktion oder Definition `merge_payloads_handler` dieses Moduls.
- `read_file_handler(context)`: Funktion oder Definition `read_file_handler` dieses Moduls.
- `write_file_handler(context)`: Funktion oder Definition `write_file_handler` dieses Moduls.
- `json_serialize_handler(context)`: Funktion oder Definition `json_serialize_handler` dieses Moduls.
- `register_default_handlers(registry)`: Registriert alle eingebauten Handler.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import inspect`
- `import json`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import Any, Awaitable, Callable`
- `import httpx`
- `from nova_synesis.domain.models import ResourceType`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/engine.py](engine.py.md)
- [frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx.md)

```

## File: `reference/src/nova_synesis/services/__init__.py.md`  
- Path: `reference/src/nova_synesis/services/__init__.py.md`  
- Size: 876 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/services/__init__.py`

- Quellpfad: [src/nova_synesis/services/__init__.py](../../../../../src/nova_synesis/services/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.services.orchestrator import OrchestratorService, create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/src/nova_synesis/services/orchestrator.py.md`  
- Path: `reference/src/nova_synesis/services/orchestrator.py.md`  
- Size: 5201 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `src/nova_synesis/services/orchestrator.py`

- Quellpfad: [src/nova_synesis/services/orchestrator.py](../../../../../src/nova_synesis/services/orchestrator.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Zentrale Service-Fassade des Backends.

## Wann du diese Datei bearbeitest

Wenn Systemkomposition, Registrierungen oder Lifecycle-Management geaendert werden.

## Klassen

### `OrchestratorService`

Zentrale Fassade, die alle Backend-Bausteine zusammenhaelt.

Methoden:

- `__init__(self, settings, repository, planner, resource_manager, memory_manager, handler_registry)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register_handler(self, name, handler)`: Registriert Verhalten oder Objekte fuer `register_handler`.
- `register_memory_system(self, memory_id, memory_type, backend, config)`: Registriert Verhalten oder Objekte fuer `register_memory_system`.
- `register_agent(self, name, role, capabilities, communication, memory_ids)`: Registriert Verhalten oder Objekte fuer `register_agent`.
- `register_resource(self, resource_type, endpoint, metadata)`: Registriert Verhalten oder Objekte fuer `register_resource`.
- `create_intent(self, goal, constraints, priority)`: Funktion oder Definition `create_intent` dieses Moduls.
- `create_flow(self, nodes, edges, metadata)`: Funktion oder Definition `create_flow` dieses Moduls.
- `plan_intent(self, goal, constraints, priority)`: Funktion oder Definition `plan_intent` dieses Moduls.
- `execute_intent(self, goal, constraints, priority)`: Fuehrt die Kernarbeit von `execute_intent` aus.
- `run_flow(self, flow_id)`: Steuert den Ablauf von `run_flow`.
- `pause_flow(self, flow_id)`: Funktion oder Definition `pause_flow` dieses Moduls.
- `get_flow(self, flow_id)`: Liest Daten fuer `get_flow` aus einem Speicher oder einer Laufzeitquelle.
- `list_agents(self)`: Gibt eine Liste von Daten fuer `list_agents` zurueck.
- `list_resources(self)`: Gibt eine Liste von Daten fuer `list_resources` zurueck.
- `list_memory_systems(self)`: Gibt eine Liste von Daten fuer `list_memory_systems` zurueck.
- `list_executions(self)`: Gibt eine Liste von Daten fuer `list_executions` zurueck.
- `get_llm_planner_status(self)`: Liest Daten fuer `get_llm_planner_status` aus einem Speicher oder einer Laufzeitquelle.
- `generate_flow_with_llm(self, prompt, current_flow, max_nodes)`: Funktion oder Definition `generate_flow_with_llm` dieses Moduls.
- `shutdown(self)`: Funktion oder Definition `shutdown` dieses Moduls.
- `subscribe_flow(self, flow_id)`: Funktion oder Definition `subscribe_flow` dieses Moduls.
- `unsubscribe_flow(self, flow_id, queue)`: Funktion oder Definition `unsubscribe_flow` dieses Moduls.
- `publish_flow_event(self, flow_id, event_type, snapshot)`: Funktion oder Definition `publish_flow_event` dieses Moduls.
- `_persist_flow(self, flow)`: Funktion oder Definition `_persist_flow` dieses Moduls.
- `_schedule_publish(self, flow_id, event_type, snapshot)`: Funktion oder Definition `_schedule_publish` dieses Moduls.
- `_build_planner_catalog(self)`: Funktion oder Definition `_build_planner_catalog` dieses Moduls.
- `_default_memory_backend(self, memory_type)`: Funktion oder Definition `_default_memory_backend` dieses Moduls.
- `_serialize_agent(agent)`: Funktion oder Definition `_serialize_agent` dieses Moduls.
- `_serialize_resource(resource)`: Funktion oder Definition `_serialize_resource` dieses Moduls.
- `_serialize_memory_system(system)`: Funktion oder Definition `_serialize_memory_system` dieses Moduls.
- `_serialize_flow(flow)`: Funktion oder Definition `_serialize_flow` dieses Moduls.

## Funktionen

- `create_orchestrator(settings)`: Factory fuer ein komplett verdrahtetes Orchestrator-System.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import Any, Callable`
- `from nova_synesis.communication.adapters import CommunicationAdapterFactory`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import (`
- `from nova_synesis.memory.systems import MemoryManager, MemorySystemFactory`
- `from nova_synesis.persistence.sqlite_repository import SQLiteRepository`
- `from nova_synesis.planning.lit_planner import LiteRTPlanner, PlannerCatalog`
- `from nova_synesis.planning.planner import IntentPlanner`
- `from nova_synesis.resources.manager import ResourceManager`
- `from nova_synesis.runtime.engine import ExecutionContext, FlowExecutor, TaskExecutor`
- `from nova_synesis.runtime.handlers import TaskHandlerRegistry, register_default_handlers`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/api/app.py](../api/app.py.md)
- [src/nova_synesis/runtime/engine.py](../runtime/engine.py.md)

```

## File: `reference/tests/test_orchestrator.py.md`  
- Path: `reference/tests/test_orchestrator.py.md`  
- Size: 2422 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `tests/test_orchestrator.py`

- Quellpfad: [tests/test_orchestrator.py](../../../tests/test_orchestrator.py)
- Kategorie: `Tests`

## Aufgabe der Datei

Regressionstests fuer Kernfunktionen des Backends.

## Wann du diese Datei bearbeitest

Wenn neue Features abgesichert oder Fehler reproduzierbar getestet werden.

## Funktionen

- `build_settings(tmp_path)`: Funktion oder Definition `build_settings` dieses Moduls.
- `test_end_to_end_flow_with_vector_memory_and_message_queue(tmp_path)`: Funktion oder Definition `test_end_to_end_flow_with_vector_memory_and_message_queue` dieses Moduls.
- `test_fallback_resource_strategy_switches_to_secondary_resource(tmp_path)`: Funktion oder Definition `test_fallback_resource_strategy_switches_to_secondary_resource` dieses Moduls.
- `test_fastapi_flow_execution_endpoint(tmp_path)`: Funktion oder Definition `test_fastapi_flow_execution_endpoint` dieses Moduls.
- `test_websocket_flow_updates_stream_runtime_events(tmp_path)`: Funktion oder Definition `test_websocket_flow_updates_stream_runtime_events` dieses Moduls.
- `test_lit_planner_normalizes_graph_output(tmp_path)`: Funktion oder Definition `test_lit_planner_normalizes_graph_output` dieses Moduls.
- `test_planner_status_endpoint_exposes_lit_configuration(tmp_path)`: Funktion oder Definition `test_planner_status_endpoint_exposes_lit_configuration` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import threading`
- `from pathlib import Path`
- `from fastapi.testclient import TestClient`
- `from nova_synesis.api.app import create_app`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import MemoryType, ResourceType`
- `from nova_synesis.planning.lit_planner import LiteRTPlanner, PlannerCatalog`
- `from nova_synesis.services.orchestrator import create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/services/orchestrator.py](../src/nova_synesis/services/orchestrator.py.md)
- [src/nova_synesis/api/app.py](../src/nova_synesis/api/app.py.md)

```

## File: `reference/tools/generate_docs.py.md`  
- Path: `reference/tools/generate_docs.py.md`  
- Size: 2233 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `tools/generate_docs.py`

- Quellpfad: [tools/generate_docs.py](../../../tools/generate_docs.py)
- Kategorie: `Werkzeug`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Funktionen

- `rel(path)`: Funktion oder Definition `rel` dieses Moduls.
- `excluded(path)`: Funktion oder Definition `excluded` dieses Moduls.
- `project_files()`: Funktion oder Definition `project_files` dieses Moduls.
- `doc_path(source)`: Funktion oder Definition `doc_path` dieses Moduls.
- `rlink(base, target)`: Funktion oder Definition `rlink` dieses Moduls.
- `source_link(doc, source)`: Funktion oder Definition `source_link` dieses Moduls.
- `doc_link(doc, source)`: Funktion oder Definition `doc_link` dieses Moduls.
- `category(r)`: Funktion oder Definition `category` dieses Moduls.
- `generic_purpose(path)`: Funktion oder Definition `generic_purpose` dieses Moduls.
- `generic_edit(path)`: Funktion oder Definition `generic_edit` dieses Moduls.
- `symbol_desc(name, kind, parent)`: Funktion oder Definition `symbol_desc` dieses Moduls.
- `imports_for(path)`: Funktion oder Definition `imports_for` dieses Moduls.
- `py_args(node)`: Funktion oder Definition `py_args` dieses Moduls.
- `py_symbols(path)`: Funktion oder Definition `py_symbols` dieses Moduls.
- `ts_symbols(path)`: Funktion oder Definition `ts_symbols` dieses Moduls.
- `symbol_block(path)`: Funktion oder Definition `symbol_block` dieses Moduls.
- `write_reference(files)`: Funktion oder Definition `write_reference` dieses Moduls.
- `write_guides(files)`: Funktion oder Definition `write_guides` dieses Moduls.
- `main()`: Funktion oder Definition `main` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import ast`
- `import os`
- `import re`
- `from collections import defaultdict`
- `from pathlib import Path`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `reference/uml_V3.mmd.md`  
- Path: `reference/uml_V3.mmd.md`  
- Size: 904 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `uml_V3.mmd`

- Quellpfad: [uml_V3.mmd](../../uml_V3.mmd)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

Mermaid-Quelle des Architekturdiagramms.

## Wann du diese Datei bearbeitest

Wenn die dokumentierte Zielarchitektur angepasst werden soll.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [uml.html](uml.html.md)
- [Anweisung.md](Anweisung.md.md)

```

## File: `reference/uml.html.md`  
- Path: `reference/uml.html.md`  
- Size: 837 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# `uml.html`

- Quellpfad: [uml.html](../../uml.html)
- Kategorie: `Projektdatei`

## Aufgabe der Datei

HTML-Datei fuer Visualisierung oder Browser-Einstieg.

## Wann du diese Datei bearbeitest

Wenn sich die fachliche oder technische Verantwortung dieser Datei aendert.

## Inhalt

Diese Datei ist keine klassische Code-Datei mit Klassen und Funktionen. Relevant ist vor allem ihre Rolle im Build-, Laufzeit- oder Dokumentationsprozess.

## Abhaengigkeiten

Keine direkten Importzeilen oder fuer diese Dateiklasse nicht sinnvoll.

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

```

## File: `system-overview.md`  
- Path: `system-overview.md`  
- Size: 621 Bytes  
- Modified: 2026-04-08 11:23:56 UTC

```markdown
# Systemueberblick

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

```


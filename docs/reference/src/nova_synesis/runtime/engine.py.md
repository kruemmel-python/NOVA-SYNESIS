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

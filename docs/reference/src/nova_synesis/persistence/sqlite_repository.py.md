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

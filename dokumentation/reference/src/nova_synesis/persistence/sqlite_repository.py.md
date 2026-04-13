# `src/nova_synesis/persistence/sqlite_repository.py`

- Quellpfad: [src/nova_synesis/persistence/sqlite_repository.py](../../../../../src/nova_synesis/persistence/sqlite_repository.py)
- Kategorie: `Backend`

## Aufgabe der Datei

SQLite-Persistenzschicht fuer Flow-Container, Flow-Versionen, Ausfuehrungen, Katalogobjekte und Metriken.

## Wann du diese Datei bearbeitest

Wenn Datenbankstruktur, Versionierung, gespeicherte Felder oder Laufzeitmetriken angepasst werden.

## Klassen

### `SQLiteRepository`

Persistenzschicht fuer SQLite.

Methoden:

- `__init__(self, database_path)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_initialize_schema(self)`: Funktion oder Definition `_initialize_schema` dieses Moduls.
- `_ensure_column(self, table_name, column_name, ddl)`: Funktion oder Definition `_ensure_column` dieses Moduls.
- `_bootstrap_existing_flow_versions(self)`: Funktion oder Definition `_bootstrap_existing_flow_versions` dieses Moduls.
- `next_id(self, name)`: Funktion oder Definition `next_id` dieses Moduls.
- `save_agent(self, agent)`: Persistiert Daten fuer `save_agent` dauerhaft.
- `save_memory_system(self, memory_system)`: Persistiert Daten fuer `save_memory_system` dauerhaft.
- `save_resource(self, resource)`: Persistiert Daten fuer `save_resource` dauerhaft.
- `save_intent(self, intent)`: Persistiert Daten fuer `save_intent` dauerhaft.
- `save_task(self, task)`: Persistiert Daten fuer `save_task` dauerhaft.
- `save_flow(self, flow)`: Persistiert Daten fuer `save_flow` dauerhaft.
- `create_flow_version(self, flow, *, created_by, change_reason, parent_version_id, planner_generated, security_report)`: Legt eine neue unveraenderliche Version fuer einen bestehenden Flow-Container an.
- `list_flow_versions(self, flow_id)`: Liefert die bekannten Versionen eines Flow-Containers fuer API und UI.
- `get_flow_record(self, flow_id)`: Liest Daten fuer `get_flow_record` aus einem Speicher oder einer Laufzeitquelle.
- `get_flow_version_record(self, flow_id, version_id)`: Liest Daten fuer `get_flow_version_record` aus einem Speicher oder einer Laufzeitquelle.
- `activate_flow_version(self, flow_id, version_id)`: Setzt die aktive Version eines Flow-Containers um, ohne alte Versionen zu verlieren.
- `save_execution(self, execution, flow_id)`: Persistiert Daten fuer `save_execution` dauerhaft.
- `save_execution_metric(self, *, execution, flow_id, node_id, handler_name, telemetry)`: Persistiert verdichtete Laufzeitdaten fuer Handler- und Flow-Analytics.
- `list_executions(self)`: Gibt eine Liste von Daten fuer `list_executions` zurueck.
- `list_execution_metrics(self)`: Gibt eine Liste von Daten fuer `list_execution_metrics` zurueck.
- `summarize_execution_metrics(self)`: Funktion oder Definition `summarize_execution_metrics` dieses Moduls.
- `_serialize_flow(flow)`: Funktion oder Definition `_serialize_flow` dieses Moduls.
- `_compute_version_hash(nodes_json, edges_json, metadata_json)`: Funktion oder Definition `_compute_version_hash` dieses Moduls.
- `_decode_execution_row(row)`: Funktion oder Definition `_decode_execution_row` dieses Moduls.
- `_decode_metric_row(row)`: Funktion oder Definition `_decode_metric_row` dieses Moduls.
- `_decode_version_row(self, row)`: Funktion oder Definition `_decode_version_row` dieses Moduls.
- `_decode_flow_row(self, row)`: Funktion oder Definition `_decode_flow_row` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import hashlib`
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

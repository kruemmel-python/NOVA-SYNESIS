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

# `tests/test_orchestrator.py`

- Quellpfad: [tests/test_orchestrator.py](../../../tests/test_orchestrator.py)
- Kategorie: `Tests`

## Aufgabe der Datei

Regressionstests fuer Backend, Planner, WebSocket-Livebetrieb und Semantic-Firewall.

## Wann du diese Datei bearbeitest

Wenn neue Features abgesichert, Sicherheitsregeln erweitert oder Fehler reproduzierbar getestet werden.

## Funktionen

- `build_settings(tmp_path)`: Funktion oder Definition `build_settings` dieses Moduls.
- `test_end_to_end_flow_with_vector_memory_and_message_queue(tmp_path)`: Funktion oder Definition `test_end_to_end_flow_with_vector_memory_and_message_queue` dieses Moduls.
- `test_fallback_resource_strategy_switches_to_secondary_resource(tmp_path)`: Funktion oder Definition `test_fallback_resource_strategy_switches_to_secondary_resource` dieses Moduls.
- `test_fastapi_flow_execution_endpoint(tmp_path)`: Funktion oder Definition `test_fastapi_flow_execution_endpoint` dieses Moduls.
- `test_handlers_endpoint_exposes_trust_metadata(tmp_path)`: Funktion oder Definition `test_handlers_endpoint_exposes_trust_metadata` dieses Moduls.
- `test_manual_approval_endpoint_enables_execution(tmp_path)`: Funktion oder Definition `test_manual_approval_endpoint_enables_execution` dieses Moduls.
- `test_websocket_flow_updates_stream_runtime_events(tmp_path)`: Funktion oder Definition `test_websocket_flow_updates_stream_runtime_events` dieses Moduls.
- `test_lit_planner_normalizes_graph_output(tmp_path)`: Funktion oder Definition `test_lit_planner_normalizes_graph_output` dieses Moduls.
- `test_lit_planner_repairs_common_malformed_json_patterns(tmp_path)`: Funktion oder Definition `test_lit_planner_repairs_common_malformed_json_patterns` dieses Moduls.
- `test_lit_planner_repairs_incomplete_json_object(tmp_path)`: Funktion oder Definition `test_lit_planner_repairs_incomplete_json_object` dieses Moduls.
- `test_lit_planner_retries_with_compact_prompt_on_context_overflow(tmp_path)`: Funktion oder Definition `test_lit_planner_retries_with_compact_prompt_on_context_overflow` dieses Moduls.
- `test_lit_planner_normalizes_send_message_target_agent_name(tmp_path)`: Funktion oder Definition `test_lit_planner_normalizes_send_message_target_agent_name` dieses Moduls.
- `test_lit_planner_falls_back_to_only_message_target_for_unknown_name(tmp_path)`: Funktion oder Definition `test_lit_planner_falls_back_to_only_message_target_for_unknown_name` dieses Moduls.
- `test_lit_planner_omits_send_message_when_no_communication_target_exists(tmp_path)`: Funktion oder Definition `test_lit_planner_omits_send_message_when_no_communication_target_exists` dieses Moduls.
- `test_semantic_firewall_rejects_cyclic_flow(tmp_path)`: Funktion oder Definition `test_semantic_firewall_rejects_cyclic_flow` dieses Moduls.
- `test_semantic_firewall_rejects_external_http_request(tmp_path)`: Funktion oder Definition `test_semantic_firewall_rejects_external_http_request` dieses Moduls.
- `test_semantic_firewall_blocks_send_message_endpoint_override(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_send_message_endpoint_override` dieses Moduls.
- `test_semantic_firewall_rejects_unknown_send_message_target_agent_name(tmp_path)`: Funktion oder Definition `test_semantic_firewall_rejects_unknown_send_message_target_agent_name` dieses Moduls.
- `test_semantic_firewall_blocks_external_rest_agent_registration(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_external_rest_agent_registration` dieses Moduls.
- `test_semantic_firewall_blocks_sensitive_memory_exfiltration(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_sensitive_memory_exfiltration` dieses Moduls.
- `test_semantic_firewall_blocks_template_context_escape(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_template_context_escape` dieses Moduls.
- `test_untrusted_handler_requires_manual_approval_override(tmp_path)`: Funktion oder Definition `test_untrusted_handler_requires_manual_approval_override` dieses Moduls.
- `test_planner_status_endpoint_exposes_lit_configuration(tmp_path)`: Funktion oder Definition `test_planner_status_endpoint_exposes_lit_configuration` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import json`
- `import threading`
- `from pathlib import Path`
- `import pytest`
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

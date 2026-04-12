# `tests/test_orchestrator.py`

- Quellpfad: [tests/test_orchestrator.py](../../../tests/test_orchestrator.py)
- Kategorie: `Tests`

## Aufgabe der Datei

Regressionstests fuer Backend, Planner, WebSocket-Livebetrieb und Semantic-Firewall.

## Wann du diese Datei bearbeitest

Wenn neue Features abgesichert, Sicherheitsregeln erweitert oder Fehler reproduzierbar getestet werden.

## Funktionen

- `build_settings(tmp_path)`: Funktion oder Definition `build_settings` dieses Moduls.
- `test_resolve_lit_cli_path_prefers_lit_directory_for_plain_filename(tmp_path)`: Funktion oder Definition `test_resolve_lit_cli_path_prefers_lit_directory_for_plain_filename` dieses Moduls.
- `test_build_cli_settings_applies_lit_model_override(tmp_path)`: Funktion oder Definition `test_build_cli_settings_applies_lit_model_override` dieses Moduls.
- `test_end_to_end_flow_with_vector_memory_and_message_queue(tmp_path)`: Funktion oder Definition `test_end_to_end_flow_with_vector_memory_and_message_queue` dieses Moduls.
- `test_generate_flow_with_llm_bootstraps_agent_and_memory_catalog(tmp_path)`: Funktion oder Definition `test_generate_flow_with_llm_bootstraps_agent_and_memory_catalog` dieses Moduls.
- `test_fallback_resource_strategy_switches_to_secondary_resource(tmp_path)`: Funktion oder Definition `test_fallback_resource_strategy_switches_to_secondary_resource` dieses Moduls.
- `test_fastapi_flow_execution_endpoint(tmp_path)`: Funktion oder Definition `test_fastapi_flow_execution_endpoint` dieses Moduls.
- `test_handlers_endpoint_exposes_trust_metadata(tmp_path)`: Funktion oder Definition `test_handlers_endpoint_exposes_trust_metadata` dieses Moduls.
- `test_manual_approval_endpoint_enables_execution(tmp_path)`: Funktion oder Definition `test_manual_approval_endpoint_enables_execution` dieses Moduls.
- `test_preapproved_manual_approval_in_flow_request_runs_after_save(tmp_path)`: Funktion oder Definition `test_preapproved_manual_approval_in_flow_request_runs_after_save` dieses Moduls.
- `test_websocket_flow_updates_stream_runtime_events(tmp_path)`: Funktion oder Definition `test_websocket_flow_updates_stream_runtime_events` dieses Moduls.
- `test_lit_planner_normalizes_graph_output(tmp_path)`: Funktion oder Definition `test_lit_planner_normalizes_graph_output` dieses Moduls.
- `test_lit_planner_repairs_common_malformed_json_patterns(tmp_path)`: Funktion oder Definition `test_lit_planner_repairs_common_malformed_json_patterns` dieses Moduls.
- `test_lit_planner_repairs_incomplete_json_object(tmp_path)`: Funktion oder Definition `test_lit_planner_repairs_incomplete_json_object` dieses Moduls.
- `test_lit_planner_repairs_missing_commas_and_single_quoted_strings(tmp_path)`: Funktion oder Definition `test_lit_planner_repairs_missing_commas_and_single_quoted_strings` dieses Moduls.
- `test_lit_planner_extracts_single_quoted_json_with_braces_inside_strings(tmp_path)`: Funktion oder Definition `test_lit_planner_extracts_single_quoted_json_with_braces_inside_strings` dieses Moduls.
- `test_lit_planner_retries_with_compact_prompt_on_context_overflow(tmp_path)`: Funktion oder Definition `test_lit_planner_retries_with_compact_prompt_on_context_overflow` dieses Moduls.
- `test_lit_planner_normalizes_send_message_target_agent_name(tmp_path)`: Funktion oder Definition `test_lit_planner_normalizes_send_message_target_agent_name` dieses Moduls.
- `test_lit_planner_falls_back_to_only_message_target_for_unknown_name(tmp_path)`: Funktion oder Definition `test_lit_planner_falls_back_to_only_message_target_for_unknown_name` dieses Moduls.
- `test_lit_planner_omits_send_message_when_no_communication_target_exists(tmp_path)`: Funktion oder Definition `test_lit_planner_omits_send_message_when_no_communication_target_exists` dieses Moduls.
- `test_lit_planner_repairs_agent_name_used_as_handler(tmp_path)`: Funktion oder Definition `test_lit_planner_repairs_agent_name_used_as_handler` dieses Moduls.
- `test_lit_planner_repairs_filesystem_security_audit_flow(tmp_path)`: Funktion oder Definition `test_lit_planner_repairs_filesystem_security_audit_flow` dieses Moduls.
- `test_lit_planner_local_llm_text_defaults_upstream_data_even_when_prompt_exists(tmp_path)`: Funktion oder Definition `test_lit_planner_local_llm_text_defaults_upstream_data_even_when_prompt_exists` dieses Moduls.
- `test_lit_planner_repairs_topic_split_and_write_csv_upstream_references(tmp_path)`: Funktion oder Definition `test_lit_planner_repairs_topic_split_and_write_csv_upstream_references` dieses Moduls.
- `test_lit_planner_replaces_placeholder_write_csv_fieldnames_for_topic_split(tmp_path)`: Funktion oder Definition `test_lit_planner_replaces_placeholder_write_csv_fieldnames_for_topic_split` dieses Moduls.
- `test_lit_planner_rewires_write_csv_from_generate_embedding_back_to_topic_split_csv_rows(tmp_path)`: Funktion oder Definition `test_lit_planner_rewires_write_csv_from_generate_embedding_back_to_topic_split_csv_rows` dieses Moduls.
- `test_lit_planner_repairs_generate_embedding_and_vector_memory_store_inputs(tmp_path)`: Funktion oder Definition `test_lit_planner_repairs_generate_embedding_and_vector_memory_store_inputs` dieses Moduls.
- `test_lit_planner_replaces_placeholder_vector_payload_shells_with_upstream_references(tmp_path)`: Funktion oder Definition `test_lit_planner_replaces_placeholder_vector_payload_shells_with_upstream_references` dieses Moduls.
- `test_lit_planner_tolerates_ellipsis_placeholder_in_literal_repair(tmp_path)`: Funktion oder Definition `test_lit_planner_tolerates_ellipsis_placeholder_in_literal_repair` dieses Moduls.
- `test_lit_planner_retries_after_quarantining_stale_xnnpack_cache(tmp_path)`: Funktion oder Definition `test_lit_planner_retries_after_quarantining_stale_xnnpack_cache` dieses Moduls.
- `test_lit_planner_surfaces_clear_engine_error_after_cache_retry_fails(tmp_path)`: Funktion oder Definition `test_lit_planner_surfaces_clear_engine_error_after_cache_retry_fails` dieses Moduls.
- `test_semantic_firewall_rejects_cyclic_flow(tmp_path)`: Funktion oder Definition `test_semantic_firewall_rejects_cyclic_flow` dieses Moduls.
- `test_semantic_firewall_rejects_external_http_request(tmp_path)`: Funktion oder Definition `test_semantic_firewall_rejects_external_http_request` dieses Moduls.
- `test_semantic_firewall_blocks_send_message_endpoint_override(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_send_message_endpoint_override` dieses Moduls.
- `test_semantic_firewall_rejects_unknown_send_message_target_agent_name(tmp_path)`: Funktion oder Definition `test_semantic_firewall_rejects_unknown_send_message_target_agent_name` dieses Moduls.
- `test_semantic_firewall_blocks_external_rest_agent_registration(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_external_rest_agent_registration` dieses Moduls.
- `test_semantic_firewall_blocks_sensitive_memory_exfiltration(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_sensitive_memory_exfiltration` dieses Moduls.
- `test_semantic_firewall_blocks_template_context_escape(tmp_path)`: Funktion oder Definition `test_semantic_firewall_blocks_template_context_escape` dieses Moduls.
- `test_untrusted_handler_requires_manual_approval_override(tmp_path)`: Funktion oder Definition `test_untrusted_handler_requires_manual_approval_override` dieses Moduls.
- `test_planner_status_endpoint_exposes_lit_configuration(tmp_path)`: Funktion oder Definition `test_planner_status_endpoint_exposes_lit_configuration` dieses Moduls.
- `test_accounts_receivable_workflow_from_csv_generates_letters(tmp_path)`: Funktion oder Definition `test_accounts_receivable_workflow_from_csv_generates_letters` dieses Moduls.
- `test_news_search_topic_split_and_write_csv_workflow(tmp_path)`: Funktion oder Definition `test_news_search_topic_split_and_write_csv_workflow` dieses Moduls.
- `test_news_search_topic_split_generate_embedding_and_vector_store_workflow(tmp_path)`: Funktion oder Definition `test_news_search_topic_split_generate_embedding_and_vector_store_workflow` dieses Moduls.
- `test_memory_store_runtime_repairs_placeholder_vector_payload_from_upstream_embedding(tmp_path)`: Funktion oder Definition `test_memory_store_runtime_repairs_placeholder_vector_payload_from_upstream_embedding` dieses Moduls.
- `test_write_csv_runtime_replaces_placeholder_fieldnames_with_detected_columns(tmp_path)`: Funktion oder Definition `test_write_csv_runtime_replaces_placeholder_fieldnames_with_detected_columns` dieses Moduls.
- `test_accounts_receivable_workflow_from_sqlite_generates_letters(tmp_path)`: Funktion oder Definition `test_accounts_receivable_workflow_from_sqlite_generates_letters` dieses Moduls.
- `test_accounts_receivable_workflow_can_generate_letter_text_with_local_llm(tmp_path)`: Funktion oder Definition `test_accounts_receivable_workflow_can_generate_letter_text_with_local_llm` dieses Moduls.
- `test_accounts_receivable_preview_endpoint_returns_llm_draft(tmp_path)`: Funktion oder Definition `test_accounts_receivable_preview_endpoint_returns_llm_draft` dieses Moduls.
- `test_local_llm_text_handler_generates_text_from_instruction_and_data(tmp_path)`: Funktion oder Definition `test_local_llm_text_handler_generates_text_from_instruction_and_data` dieses Moduls.
- `test_local_llm_text_handler_uses_prompt_and_data_without_follow_up_requests(tmp_path)`: Funktion oder Definition `test_local_llm_text_handler_uses_prompt_and_data_without_follow_up_requests` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import argparse`
- `import json`
- `import subprocess`
- `import sqlite3`
- `import threading`
- `import zipfile`
- `from pathlib import Path`
- `from unittest.mock import patch`
- `import httpx`
- `import pytest`
- `from fastapi.testclient import TestClient`
- `from nova_synesis.api.app import create_app`
- `from nova_synesis.cli import _build_settings as build_cli_settings`
- `from nova_synesis.cli import _resolve_lit_cli_path`
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

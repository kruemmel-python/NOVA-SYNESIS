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

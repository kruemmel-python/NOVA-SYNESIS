# `src/nova_synesis/security/policy.py`

- Quellpfad: [src/nova_synesis/security/policy.py](../../../../../src/nova_synesis/security/policy.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Semantische Firewall fuer Flow- und Agent-Validierung vor Planung, Speicherung und Ausfuehrung.

## Wann du diese Datei bearbeitest

Wenn Sicherheitsregeln, Allowlists oder die Graph-Absichtspruefung veraendert werden muessen.

## Klassen

### `SecurityFinding`

Klasse `SecurityFinding` dieses Moduls.

Methoden:

- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.

### `FlowSecurityReport`

Strukturiertes Ergebnis einer Policy-Pruefung mit Fehlern und Warnungen.

Methoden:

- `add_violation(self, code, message, node_id, field)`: Funktion oder Definition `add_violation` dieses Moduls.
- `add_warning(self, code, message, node_id, field)`: Funktion oder Definition `add_warning` dieses Moduls.
- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.
- `ensure_allowed(self)`: Bricht den aktuellen Vorgang ab, wenn Regelverletzungen gefunden wurden.

### `SemanticFirewall`

Semantische Sicherheitspruefung fuer Flows, Agenten und aus Planner-Graphen abgeleitete Absichten.

Methoden:

- `__init__(self, settings)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `validate_agent_registration(self, name, capabilities, communication, existing_agents)`: Prueft Agent-Registrierung auf riskante Capabilities und unerlaubte Endpunkte.
- `validate_flow_request(self, nodes, edges, metadata, handlers, agents, resources, memory_systems, planner_generated, phase)`: Prueft Graph-Struktur, Expressions, Egress und Memory-Fluesse vor der Ausfuehrung.
- `_validate_handler_definition(self, node_id, handler_name, handler_index, node, phase, report)`: Funktion oder Definition `_validate_handler_definition` dieses Moduls.
- `_report_pending_manual_approval(node_id, phase, report)`: Funktion oder Definition `_report_pending_manual_approval` dieses Moduls.
- `_collect_edges(self, node_index, edges, report)`: Funktion oder Definition `_collect_edges` dieses Moduls.
- `_validate_acyclic(self, node_index, edges, report)`: Funktion oder Definition `_validate_acyclic` dieses Moduls.
- `_validate_http_request(self, node_id, node, input_payload, resource_index, report)`: Funktion oder Definition `_validate_http_request` dieses Moduls.
- `_validate_send_message(self, node_id, input_payload, agent_index, report)`: Funktion oder Definition `_validate_send_message` dieses Moduls.
- `_resolve_target_agent(agent_index, input_payload)`: Funktion oder Definition `_resolve_target_agent` dieses Moduls.
- `_validate_file_handler(self, node_id, input_payload, report)`: Funktion oder Definition `_validate_file_handler` dieses Moduls.
- `_validate_expression_container(self, node_id, field, value, allowed_names, report)`: Funktion oder Definition `_validate_expression_container` dieses Moduls.
- `_validate_expression_map(self, node_id, field, expressions, allowed_names, report)`: Funktion oder Definition `_validate_expression_map` dieses Moduls.
- `_validate_template_string(self, node_id, field, template, allowed_names, report)`: Funktion oder Definition `_validate_template_string` dieses Moduls.
- `_validate_expression(self, node_id, field, expression, allowed_names, report)`: Funktion oder Definition `_validate_expression` dieses Moduls.
- `_detect_sensitive_exfiltration(self, node_index, edges, agent_index, memory_index, report)`: Funktion oder Definition `_detect_sensitive_exfiltration` dieses Moduls.
- `_detect_memory_poisoning(self, node_index, edges, memory_index, report)`: Funktion oder Definition `_detect_memory_poisoning` dieses Moduls.
- `_build_upstream_map(node_index, edges)`: Funktion oder Definition `_build_upstream_map` dieses Moduls.
- `_is_allowed_host(self, host)`: Funktion oder Definition `_is_allowed_host` dieses Moduls.
- `_is_loopback_host(host)`: Funktion oder Definition `_is_loopback_host` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import ast`
- `import ipaddress`
- `from collections import deque`
- `from dataclasses import dataclass, field`
- `from typing import Any`
- `from urllib.parse import urlparse`
- `from nova_synesis.config import Settings`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)
- [src/nova_synesis/config.py](../config.py.md)
- [tests/test_orchestrator.py](../../../tests/test_orchestrator.py.md)

# `src/nova_synesis/services/orchestrator.py`

- Quellpfad: [src/nova_synesis/services/orchestrator.py](../../../../../src/nova_synesis/services/orchestrator.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Zentrale Service-Fassade des Backends inklusive Security-Gates, Flow-Versionierung, HITL-Resume, Planner-Katalog, RBAC und Lifecycle-Management.

## Wann du diese Datei bearbeitest

Wenn Systemkomposition, Registrierungen, Versionssteuerung, Policy-Durchsetzung, Metriken oder Lifecycle-Management geaendert werden.

## Klassen

### `OrchestratorService`

Zentrale Fassade, die alle Backend-Bausteine zusammenhaelt.

Methoden:

- `__init__(self, settings, repository, planner, resource_manager, memory_manager, handler_registry)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register_handler(self, name, handler, *, certificate)`: Registriert Verhalten oder Objekte fuer `register_handler`.
- `list_handlers(self)`: Gibt eine Liste von Daten fuer `list_handlers` zurueck.
- `issue_handler_certificate(self, handler_name, expires_in_hours)`: Funktion oder Definition `issue_handler_certificate` dieses Moduls.
- `register_memory_system(self, memory_id, memory_type, backend, config)`: Registriert Verhalten oder Objekte fuer `register_memory_system`.
- `register_agent(self, name, role, capabilities, communication, memory_ids)`: Registriert Verhalten oder Objekte fuer `register_agent`.
- `register_resource(self, resource_type, endpoint, metadata)`: Registriert Verhalten oder Objekte fuer `register_resource`.
- `create_intent(self, goal, constraints, priority)`: Funktion oder Definition `create_intent` dieses Moduls.
- `create_flow(self, nodes, edges, metadata, *, created_by, change_reason, planner_generated, security_report)`: Funktion oder Definition `create_flow` dieses Moduls.
- `save_flow_version(self, flow_id, nodes, edges, metadata, *, created_by, change_reason, planner_generated)`: Persistiert aus dem aktuellen Editorgraphen eine neue Version zu einem bestehenden Flow-Container.
- `plan_intent(self, goal, constraints, priority)`: Funktion oder Definition `plan_intent` dieses Moduls.
- `execute_intent(self, goal, constraints, priority)`: Fuehrt die Kernarbeit von `execute_intent` aus.
- `run_flow(self, flow_id, version_id)`: Steuert den Ablauf von `run_flow`.
- `pause_flow(self, flow_id)`: Funktion oder Definition `pause_flow` dieses Moduls.
- `get_flow(self, flow_id)`: Liest Daten fuer `get_flow` aus einem Speicher oder einer Laufzeitquelle.
- `list_flow_versions(self, flow_id)`: Liefert die Versionstabelle eines Flows fuer UI und API.
- `get_flow_version(self, flow_id, version_id)`: Liest Daten fuer `get_flow_version` aus einem Speicher oder einer Laufzeitquelle.
- `activate_flow_version(self, flow_id, version_id)`: Aktiviert eine vorhandene Version fuer spaetere Runs und Ladeoperationen.
- `list_agents(self)`: Gibt eine Liste von Daten fuer `list_agents` zurueck.
- `list_resources(self)`: Gibt eine Liste von Daten fuer `list_resources` zurueck.
- `list_memory_systems(self)`: Gibt eine Liste von Daten fuer `list_memory_systems` zurueck.
- `list_executions(self)`: Gibt eine Liste von Daten fuer `list_executions` zurueck.
- `list_execution_metrics(self)`: Gibt eine Liste von Daten fuer `list_execution_metrics` zurueck.
- `summarize_execution_metrics(self)`: Aggregiert Handler- und Flow-Metriken fuer das Analytics-Panel.
- `get_llm_planner_status(self)`: Liest Daten fuer `get_llm_planner_status` aus einem Speicher oder einer Laufzeitquelle.
- `approve_flow_node(self, flow_id, node_id, approved_by, reason, actor_roles)`: Funktion oder Definition `approve_flow_node` dieses Moduls.
- `revoke_flow_node_approval(self, flow_id, node_id, revoked_by, reason, actor_roles)`: Funktion oder Definition `revoke_flow_node_approval` dieses Moduls.
- `get_node_input_request(self, flow_id, node_id)`: Liest die offene HITL-Anforderung eines WAITING_FOR_INPUT-Nodes aus.
- `resume_flow_node(self, flow_id, node_id, value, submitted_by, metadata, *, auto_run, actor_roles)`: Nimmt Operator-Eingaben entgegen und setzt einen pausierten Node fort.
- `generate_flow_with_llm(self, prompt, current_flow, max_nodes)`: Funktion oder Definition `generate_flow_with_llm` dieses Moduls.
- `_ensure_llm_planner_bootstrap(self)`: Funktion oder Definition `_ensure_llm_planner_bootstrap` dieses Moduls.
- `validate_flow_request(self, nodes, edges, metadata, planner_generated, phase)`: Funktion oder Definition `validate_flow_request` dieses Moduls.
- `preview_accounts_receivable_draft(self, extract_input, generate_input, customer_index)`: Funktion oder Definition `preview_accounts_receivable_draft` dieses Moduls.
- `shutdown(self)`: Funktion oder Definition `shutdown` dieses Moduls.
- `subscribe_flow(self, flow_id)`: Funktion oder Definition `subscribe_flow` dieses Moduls.
- `unsubscribe_flow(self, flow_id, queue)`: Funktion oder Definition `unsubscribe_flow` dieses Moduls.
- `publish_flow_event(self, flow_id, event_type, snapshot)`: Funktion oder Definition `publish_flow_event` dieses Moduls.
- `_persist_flow(self, flow)`: Funktion oder Definition `_persist_flow` dieses Moduls.
- `_persist_flow_version(self, flow, *, created_by, change_reason, parent_version_id, planner_generated, security_report)`: Funktion oder Definition `_persist_flow_version` dieses Moduls.
- `_ensure_loaded_flow(self, flow_id, version_id)`: Funktion oder Definition `_ensure_loaded_flow` dieses Moduls.
- `_build_flow_from_request(self, *, flow_id, nodes, edges, metadata, goal)`: Funktion oder Definition `_build_flow_from_request` dieses Moduls.
- `_hydrate_flow_from_snapshot(self, flow_id, snapshot)`: Funktion oder Definition `_hydrate_flow_from_snapshot` dieses Moduls.
- `run_subflow(self, *, target_flow_id, target_version_id, input_mapping, parent_stack)`: Fuehrt einen Child-Flow isoliert gegen eine gepinnte Version aus.
- `_schedule_publish(self, flow_id, event_type, snapshot)`: Funktion oder Definition `_schedule_publish` dieses Moduls.
- `_build_planner_catalog(self)`: Funktion oder Definition `_build_planner_catalog` dieses Moduls.
- `_ensure_actor_role(self, required_role, actor_roles, message)`: Funktion oder Definition `_ensure_actor_role` dieses Moduls.
- `_snapshot_nodes_to_specs(flow_snapshot)`: Funktion oder Definition `_snapshot_nodes_to_specs` dieses Moduls.
- `_default_memory_backend(self, memory_type)`: Funktion oder Definition `_default_memory_backend` dieses Moduls.
- `_serialize_agent(agent)`: Funktion oder Definition `_serialize_agent` dieses Moduls.
- `_serialize_resource(resource)`: Funktion oder Definition `_serialize_resource` dieses Moduls.
- `_serialize_memory_system(system)`: Funktion oder Definition `_serialize_memory_system` dieses Moduls.
- `_serialize_flow(self, flow)`: Funktion oder Definition `_serialize_flow` dieses Moduls.

## Funktionen

- `create_orchestrator(settings)`: Factory fuer ein komplett verdrahtetes Orchestrator-System.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import json`
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
- `from nova_synesis.runtime.handlers import (`
- `from nova_synesis.security import SemanticFirewall`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/api/app.py](../api/app.py.md)
- [src/nova_synesis/runtime/engine.py](../runtime/engine.py.md)

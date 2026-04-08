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

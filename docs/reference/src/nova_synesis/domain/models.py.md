# `src/nova_synesis/domain/models.py`

- Quellpfad: [src/nova_synesis/domain/models.py](../../../../../src/nova_synesis/domain/models.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Kern-Domaenenmodell mit Agenten, Ressourcen, Tasks, Bedingungen und ExecutionFlow.

## Wann du diese Datei bearbeitest

Wenn das fachliche Laufzeitmodell des Systems veraendert wird.

## Klassen

### `AgentState`

Klasse `AgentState` dieses Moduls.

### `ProtocolType`

Klasse `ProtocolType` dieses Moduls.

### `MemoryType`

Klasse `MemoryType` dieses Moduls.

### `TaskStatus`

Klasse `TaskStatus` dieses Moduls.

### `ExecutionStatus`

Klasse `ExecutionStatus` dieses Moduls.

### `RollbackStrategy`

Klasse `RollbackStrategy` dieses Moduls.

### `ResourceType`

Klasse `ResourceType` dieses Moduls.

### `ResourceState`

Klasse `ResourceState` dieses Moduls.

### `FlowState`

Klasse `FlowState` dieses Moduls.

### `Capability`

Klasse `Capability` dieses Moduls.

### `RetryPolicy`

Klasse `RetryPolicy` dieses Moduls.

Methoden:

- `next_delay(self, attempt)`: Funktion oder Definition `next_delay` dieses Moduls.

### `ErrorEvent`

Klasse `ErrorEvent` dieses Moduls.

Methoden:

- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.

### `SafeExpressionEvaluator`

Klasse `SafeExpressionEvaluator` dieses Moduls.

Methoden:

- `__init__(self, context)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `evaluate(self, expression)`: Funktion oder Definition `evaluate` dieses Moduls.
- `visit_Name(self, node)`: AST-Besuchsmethode fuer `Name`-Knoten.
- `visit_Constant(self, node)`: AST-Besuchsmethode fuer `Constant`-Knoten.
- `visit_List(self, node)`: AST-Besuchsmethode fuer `List`-Knoten.
- `visit_Tuple(self, node)`: AST-Besuchsmethode fuer `Tuple`-Knoten.
- `visit_Dict(self, node)`: AST-Besuchsmethode fuer `Dict`-Knoten.
- `visit_BoolOp(self, node)`: AST-Besuchsmethode fuer `BoolOp`-Knoten.
- `visit_UnaryOp(self, node)`: AST-Besuchsmethode fuer `UnaryOp`-Knoten.
- `visit_BinOp(self, node)`: AST-Besuchsmethode fuer `BinOp`-Knoten.
- `visit_Compare(self, node)`: AST-Besuchsmethode fuer `Compare`-Knoten.
- `visit_Subscript(self, node)`: AST-Besuchsmethode fuer `Subscript`-Knoten.
- `visit_Call(self, node)`: AST-Besuchsmethode fuer `Call`-Knoten.
- `generic_visit(self, node)`: Funktion oder Definition `generic_visit` dieses Moduls.

### `Condition`

Klasse `Condition` dieses Moduls.

Methoden:

- `evaluate(self, context)`: Funktion oder Definition `evaluate` dieses Moduls.

### `Resource`

Klasse `Resource` dieses Moduls.

Methoden:

- `__post_init__(self)`: Funktion oder Definition `__post_init__` dieses Moduls.
- `capacity(self)`: Funktion oder Definition `capacity` dieses Moduls.
- `acquire(self, timeout)`: Funktion oder Definition `acquire` dieses Moduls.
- `release(self)`: Funktion oder Definition `release` dieses Moduls.
- `health_check(self)`: Funktion oder Definition `health_check` dieses Moduls.

### `Agent`

Klasse `Agent` dieses Moduls.

Methoden:

- `capability_index(self)`: Funktion oder Definition `capability_index` dieses Moduls.
- `can_execute(self, required_capabilities)`: Funktion oder Definition `can_execute` dieses Moduls.
- `perceive(self, input_data)`: Funktion oder Definition `perceive` dieses Moduls.
- `decide(self, context)`: Funktion oder Definition `decide` dieses Moduls.
- `act(self, task)`: Funktion oder Definition `act` dieses Moduls.
- `communicate(self, message, target, protocol)`: Funktion oder Definition `communicate` dieses Moduls.

### `Task`

Klasse `Task` dieses Moduls.

Methoden:

- `execute(self)`: Fuehrt die Kernarbeit von `execute` aus.
- `validate(self, result)`: Funktion oder Definition `validate` dieses Moduls.
- `complete(self, output)`: Funktion oder Definition `complete` dieses Moduls.
- `reset(self)`: Funktion oder Definition `reset` dieses Moduls.

### `TaskExecution`

Klasse `TaskExecution` dieses Moduls.

Methoden:

- `start(self)`: Funktion oder Definition `start` dieses Moduls.
- `finish(self, result)`: Funktion oder Definition `finish` dieses Moduls.
- `record_error(self, error)`: Funktion oder Definition `record_error` dieses Moduls.
- `rollback(self, strategy)`: Funktion oder Definition `rollback` dieses Moduls.
- `retry(self)`: Funktion oder Definition `retry` dieses Moduls.

### `Intent`

Klasse `Intent` dieses Moduls.

Methoden:

- `refine(self, updates)`: Funktion oder Definition `refine` dieses Moduls.
- `plan(self, planner, agents, resources, task_id_allocator, flow_id_allocator)`: Funktion oder Definition `plan` dieses Moduls.
- `promote_to_task(self, planner, agents, resources, task_id_allocator)`: Funktion oder Definition `promote_to_task` dieses Moduls.

### `FlowNode`

Klasse `FlowNode` dieses Moduls.

### `FlowEdge`

Klasse `FlowEdge` dieses Moduls.

### `ExecutionFlow`

Graph-Modell des ausfuehrbaren Workflows.

Methoden:

- `add_node(self, node)`: Funktion oder Definition `add_node` dieses Moduls.
- `add_edge(self, edge)`: Funktion oder Definition `add_edge` dieses Moduls.
- `incoming_edges(self, node_id)`: Funktion oder Definition `incoming_edges` dieses Moduls.
- `outgoing_edges(self, node_id)`: Funktion oder Definition `outgoing_edges` dieses Moduls.
- `run(self, executor)`: Steuert den Ablauf von `run`.
- `pause(self)`: Funktion oder Definition `pause` dieses Moduls.
- `observe(self)`: Erzeugt den serialisierbaren Zustand eines Flows fuer API und UI.

## Funktionen

- `utcnow()`: Funktion oder Definition `utcnow` dieses Moduls.
- `maybe_await(value)`: Funktion oder Definition `maybe_await` dieses Moduls.
- `safe_evaluate(expression, context)`: Funktion oder Definition `safe_evaluate` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import ast`
- `import asyncio`
- `import sqlite3`
- `from dataclasses import dataclass, field`
- `from datetime import datetime, timezone`
- `from enum import StrEnum`
- `from pathlib import Path`
- `from random import uniform`
- `from typing import TYPE_CHECKING, Any, Callable`
- `import httpx`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/engine.py](../runtime/engine.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)

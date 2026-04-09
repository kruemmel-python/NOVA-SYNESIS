# `src/nova_synesis/memory/systems.py`

- Quellpfad: [src/nova_synesis/memory/systems.py](../../../../../src/nova_synesis/memory/systems.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Implementierungen fuer Kurzzeit-, Langzeit- und Vektor-Speicher.

## Wann du diese Datei bearbeitest

Wenn Speicherverhalten, Suche oder Persistenz geaendert werden.

## Klassen

### `MemorySearchHit`

Klasse `MemorySearchHit` dieses Moduls.

Methoden:

- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.

### `MemorySystem`

Klasse `MemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, memory_type, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `ShortTermMemorySystem`

Klasse `ShortTermMemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_load_from_disk(self)`: Funktion oder Definition `_load_from_disk` dieses Moduls.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `_score_value(self, value, query)`: Funktion oder Definition `_score_value` dieses Moduls.
- `_extract_embedding(value)`: Funktion oder Definition `_extract_embedding` dieses Moduls.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `LongTermMemorySystem`

Klasse `LongTermMemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `VectorMemorySystem`

Klasse `VectorMemorySystem` dieses Moduls.

Methoden:

- `__init__(self, memory_id, backend, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `store(self, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, query, limit)`: Sucht passende Daten fuer `search`.
- `persist(self)`: Schreibt Daten fuer `persist` in einen dauerhaften Speicher.

### `MemorySystemFactory`

Factory-Klasse `MemorySystemFactory` zum Erzeugen passender Objekte.

Methoden:

- `create(memory_id, memory_type, backend, config)`: Funktion oder Definition `create` dieses Moduls.

### `MemoryManager`

Koordinationsklasse `MemoryManager` fuer mehrere Instanzen oder Zustandsobjekte.

Methoden:

- `__init__(self)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register(self, system)`: Registriert Verhalten oder Objekte fuer `register`.
- `get(self, memory_id)`: Funktion oder Definition `get` dieses Moduls.
- `list(self)`: Funktion oder Definition `list` dieses Moduls.
- `store(self, memory_id, key, value)`: Funktion oder Definition `store` dieses Moduls.
- `retrieve(self, memory_id, key)`: Liests Daten fuer `retrieve` aus einem Speicher zurueck.
- `search(self, memory_id, query, limit)`: Sucht passende Daten fuer `search`.
- `persist_all(self)`: Schreibt Daten fuer `persist_all` in einen dauerhaften Speicher.

## Funktionen

- `utcnow_iso()`: Funktion oder Definition `utcnow_iso` dieses Moduls.
- `cosine_similarity(left, right)`: Funktion oder Definition `cosine_similarity` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import json`
- `import math`
- `import sqlite3`
- `from abc import ABC, abstractmethod`
- `from collections import OrderedDict`
- `from dataclasses import dataclass, field`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import Any`
- `from nova_synesis.domain.models import MemoryType`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/handlers.py](../runtime/handlers.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)

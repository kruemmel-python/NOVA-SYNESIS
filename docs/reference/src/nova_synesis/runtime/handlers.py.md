# `src/nova_synesis/runtime/handlers.py`

- Quellpfad: [src/nova_synesis/runtime/handlers.py](../../../../../src/nova_synesis/runtime/handlers.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Eingebaute Handler fuer HTTP, Memory, Messaging, Dateien und Serialisierung.

## Wann du diese Datei bearbeitest

Wenn neue Arbeitsbausteine hinzugefuegt oder bestehende Handler verbessert werden.

## Klassen

### `TaskHandlerRegistry`

Registry der registrierten Runtime-Handler.

Methoden:

- `__init__(self, settings)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `register(self, name, handler, *, certificate, built_in)`: Registriert Verhalten oder Objekte fuer `register`.
- `get(self, name)`: Funktion oder Definition `get` dieses Moduls.
- `get_record(self, name)`: Liest Daten fuer `get_record` aus einem Speicher oder einer Laufzeitquelle.
- `names(self, trusted_only)`: Funktion oder Definition `names` dieses Moduls.
- `describe(self)`: Funktion oder Definition `describe` dieses Moduls.
- `issue_certificate(self, name, *, expires_in_hours)`: Erzeugt ein digitales Zertifikat fuer einen bereits registrierten Handler.
- `execute(self, name, context)`: Fuehrt die Kernarbeit von `execute` aus.

## Funktionen

- `_resolve_working_path(working_directory, raw_path, allow_outside_workdir)`: Funktion oder Definition `_resolve_working_path` dieses Moduls.
- `_primary_resource_endpoint(context, resource_type)`: Funktion oder Definition `_primary_resource_endpoint` dieses Moduls.
- `http_request_handler(context)`: Funktion oder Definition `http_request_handler` dieses Moduls.
- `memory_store_handler(context)`: Funktion oder Definition `memory_store_handler` dieses Moduls.
- `memory_retrieve_handler(context)`: Funktion oder Definition `memory_retrieve_handler` dieses Moduls.
- `memory_search_handler(context)`: Funktion oder Definition `memory_search_handler` dieses Moduls.
- `send_message_handler(context)`: Funktion oder Definition `send_message_handler` dieses Moduls.
- `resource_health_check_handler(context)`: Funktion oder Definition `resource_health_check_handler` dieses Moduls.
- `template_render_handler(context)`: Funktion oder Definition `template_render_handler` dieses Moduls.
- `merge_payloads_handler(context)`: Funktion oder Definition `merge_payloads_handler` dieses Moduls.
- `read_file_handler(context)`: Funktion oder Definition `read_file_handler` dieses Moduls.
- `write_file_handler(context)`: Funktion oder Definition `write_file_handler` dieses Moduls.
- `json_serialize_handler(context)`: Funktion oder Definition `json_serialize_handler` dieses Moduls.
- `register_default_handlers(registry)`: Registriert alle eingebauten Handler.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import inspect`
- `import json`
- `from datetime import datetime, timezone`
- `from pathlib import Path`
- `from typing import Any, Awaitable, Callable`
- `import httpx`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import ResourceType`
- `from nova_synesis.security import HandlerCertificate, HandlerTrustAuthority, HandlerTrustRecord`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/engine.py](engine.py.md)
- [frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx.md)

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
- `_parse_iso_datetime(value)`: Funktion oder Definition `_parse_iso_datetime` dieses Moduls.
- `_parse_bool(value)`: Funktion oder Definition `_parse_bool` dieses Moduls.
- `_parse_float(value)`: Funktion oder Definition `_parse_float` dieses Moduls.
- `_format_currency(amount)`: Funktion oder Definition `_format_currency` dieses Moduls.
- `_ascii_slug(value)`: Funktion oder Definition `_ascii_slug` dieses Moduls.
- `_with_extension(file_name, extension)`: Funktion oder Definition `_with_extension` dieses Moduls.
- `_build_docx_document_xml(content)`: Funktion oder Definition `_build_docx_document_xml` dieses Moduls.
- `_write_simple_docx(path, *, content, title)`: Funktion oder Definition `_write_simple_docx` dieses Moduls.
- `_serialize_invoice_record(record, *, index, as_of)`: Funktion oder Definition `_serialize_invoice_record` dieses Moduls.
- `_load_orders_from_csv(path, *, as_of)`: Funktion oder Definition `_load_orders_from_csv` dieses Moduls.
- `_load_orders_from_sqlite(path, *, table, as_of)`: Funktion oder Definition `_load_orders_from_sqlite` dieses Moduls.
- `_group_receivables(invoices, *, as_of)`: Funktion oder Definition `_group_receivables` dieses Moduls.
- `http_request_handler(context)`: Funktion oder Definition `http_request_handler` dieses Moduls.
- `memory_store_handler(context)`: Funktion oder Definition `memory_store_handler` dieses Moduls.
- `memory_retrieve_handler(context)`: Funktion oder Definition `memory_retrieve_handler` dieses Moduls.
- `memory_search_handler(context)`: Funktion oder Definition `memory_search_handler` dieses Moduls.
- `send_message_handler(context)`: Funktion oder Definition `send_message_handler` dieses Moduls.
- `resource_health_check_handler(context)`: Funktion oder Definition `resource_health_check_handler` dieses Moduls.
- `template_render_handler(context)`: Funktion oder Definition `template_render_handler` dieses Moduls.
- `accounts_receivable_extract_handler(context)`: Funktion oder Definition `accounts_receivable_extract_handler` dieses Moduls.
- `accounts_receivable_generate_letters_handler(context)`: Funktion oder Definition `accounts_receivable_generate_letters_handler` dieses Moduls.
- `accounts_receivable_write_letters_handler(context)`: Funktion oder Definition `accounts_receivable_write_letters_handler` dieses Moduls.
- `merge_payloads_handler(context)`: Funktion oder Definition `merge_payloads_handler` dieses Moduls.
- `read_file_handler(context)`: Funktion oder Definition `read_file_handler` dieses Moduls.
- `write_file_handler(context)`: Funktion oder Definition `write_file_handler` dieses Moduls.
- `json_serialize_handler(context)`: Funktion oder Definition `json_serialize_handler` dieses Moduls.
- `register_default_handlers(registry)`: Registriert alle eingebauten Handler.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import csv`
- `import inspect`
- `import json`
- `import re`
- `import sqlite3`
- `import unicodedata`
- `import zipfile`
- `from collections import defaultdict`
- `from datetime import datetime, timedelta, timezone`
- `from pathlib import Path`
- `from typing import Any, Awaitable, Callable`
- `from xml.sax.saxutils import escape as xml_escape`
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

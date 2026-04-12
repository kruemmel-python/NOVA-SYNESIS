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
- `_invoice_summary_lines(customer)`: Funktion oder Definition `_invoice_summary_lines` dieses Moduls.
- `_render_receivable_template_letter(*, customer, sender_company, sender_email, sender_phone, sender_address, due_date_text, settle_by_text)`: Funktion oder Definition `_render_receivable_template_letter` dieses Moduls.
- `_render_receivable_llm_prompt(*, prompt_template, user_instruction, customer, sender_company, sender_email, sender_phone, sender_address, due_date_text, settle_by_text)`: Funktion oder Definition `_render_receivable_llm_prompt` dieses Moduls.
- `_sanitize_llm_letter_output(raw_text)`: Funktion oder Definition `_sanitize_llm_letter_output` dieses Moduls.
- `_generate_local_text(prompt, settings, *, timeout_s)`: Funktion oder Definition `_generate_local_text` dieses Moduls.
- `_draft_receivable_letter(*, customer, sender_company, sender_email, sender_phone, sender_address, due_date_text, settle_by_text, use_local_llm, settings, prompt_template, user_instruction, fallback_to_template_on_error, customer_label, llm_timeout_s)`: Funktion oder Definition `_draft_receivable_letter` dieses Moduls.
- `preview_accounts_receivable_letter_draft(*, settings, working_directory, extract_input, generate_input, customer_index)`: Erzeugt serverseitig einen einzelnen Beispielbrief fuer den Forderungs-Workflow, ohne den ganzen Flow auszufuehren.
- `_build_docx_document_xml(content)`: Funktion oder Definition `_build_docx_document_xml` dieses Moduls.
- `_write_simple_docx(path, *, content, title)`: Funktion oder Definition `_write_simple_docx` dieses Moduls.
- `_serialize_invoice_record(record, *, index, as_of)`: Funktion oder Definition `_serialize_invoice_record` dieses Moduls.
- `_load_orders_from_csv(path, *, as_of)`: Funktion oder Definition `_load_orders_from_csv` dieses Moduls.
- `_load_orders_from_sqlite(path, *, table, as_of)`: Funktion oder Definition `_load_orders_from_sqlite` dieses Moduls.
- `_group_receivables(invoices, *, as_of)`: Funktion oder Definition `_group_receivables` dieses Moduls.
- `_normalized_match_text(value)`: Funktion oder Definition `_normalized_match_text` dieses Moduls.
- `_strip_html(value)`: Funktion oder Definition `_strip_html` dieses Moduls.
- `_topic_keyword_map(raw_topics)`: Funktion oder Definition `_topic_keyword_map` dieses Moduls.
- `_csv_safe_value(value)`: Funktion oder Definition `_csv_safe_value` dieses Moduls.
- `_csv_has_content(value)`: Funktion oder Definition `_csv_has_content` dieses Moduls.
- `_detect_csv_columns(rows)`: Funktion oder Definition `_detect_csv_columns` dieses Moduls.
- `_is_placeholder_input_shell(value)`: Funktion oder Definition `_is_placeholder_input_shell` dieses Moduls.
- `_has_valid_embedding_payload(value)`: Funktion oder Definition `_has_valid_embedding_payload` dieses Moduls.
- `_resolve_upstream_embedding_result(context)`: Funktion oder Definition `_resolve_upstream_embedding_result` dieses Moduls.
- `_normalize_memory_store_value(context, payload)`: Funktion oder Definition `_normalize_memory_store_value` dieses Moduls.
- `_extract_google_news_items(feed_xml, *, max_items)`: Funktion oder Definition `_extract_google_news_items` dieses Moduls.
- `http_request_handler(context)`: Funktion oder Definition `http_request_handler` dieses Moduls.
- `memory_store_handler(context)`: Funktion oder Definition `memory_store_handler` dieses Moduls.
- `memory_retrieve_handler(context)`: Funktion oder Definition `memory_retrieve_handler` dieses Moduls.
- `memory_search_handler(context)`: Funktion oder Definition `memory_search_handler` dieses Moduls.
- `send_message_handler(context)`: Funktion oder Definition `send_message_handler` dieses Moduls.
- `resource_health_check_handler(context)`: Funktion oder Definition `resource_health_check_handler` dieses Moduls.
- `news_search_handler(context)`: Funktion oder Definition `news_search_handler` dieses Moduls.
- `topic_split_handler(context)`: Funktion oder Definition `topic_split_handler` dieses Moduls.
- `template_render_handler(context)`: Funktion oder Definition `template_render_handler` dieses Moduls.
- `generate_embedding_handler(context)`: Funktion oder Definition `generate_embedding_handler` dieses Moduls.
- `accounts_receivable_extract_handler(context)`: Funktion oder Definition `accounts_receivable_extract_handler` dieses Moduls.
- `accounts_receivable_generate_letters_handler(context)`: Funktion oder Definition `accounts_receivable_generate_letters_handler` dieses Moduls.
- `accounts_receivable_write_letters_handler(context)`: Funktion oder Definition `accounts_receivable_write_letters_handler` dieses Moduls.
- `merge_payloads_handler(context)`: Funktion oder Definition `merge_payloads_handler` dieses Moduls.
- `read_file_handler(context)`: Funktion oder Definition `read_file_handler` dieses Moduls.
- `write_file_handler(context)`: Funktion oder Definition `write_file_handler` dieses Moduls.
- `write_csv_handler(context)`: Funktion oder Definition `write_csv_handler` dieses Moduls.
- `json_serialize_handler(context)`: Funktion oder Definition `json_serialize_handler` dieses Moduls.
- `generate_embedding_handler(context)`: Funktion oder Definition `generate_embedding_handler` dieses Moduls.
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
- `from urllib.parse import urlencode`
- `from xml.etree import ElementTree`
- `from xml.sax.saxutils import escape as xml_escape`
- `import httpx`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import ResourceType`
- `from nova_synesis.planning.lit_planner import LiteRTPlanner`
- `from nova_synesis.security import HandlerCertificate, HandlerTrustAuthority, HandlerTrustRecord`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/engine.py](engine.py.md)
- [frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx.md)

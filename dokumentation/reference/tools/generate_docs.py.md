# `tools/generate_docs.py`

- Quellpfad: [tools/generate_docs.py](../../../tools/generate_docs.py)
- Kategorie: `Werkzeug`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Funktionen

- `rel(path)`: Funktion oder Definition `rel` dieses Moduls.
- `read_text(path)`: Funktion oder Definition `read_text` dieses Moduls.
- `excluded(path)`: Funktion oder Definition `excluded` dieses Moduls.
- `project_files()`: Funktion oder Definition `project_files` dieses Moduls.
- `doc_path(source)`: Funktion oder Definition `doc_path` dieses Moduls.
- `rlink(base, target)`: Funktion oder Definition `rlink` dieses Moduls.
- `source_link(doc, source)`: Funktion oder Definition `source_link` dieses Moduls.
- `doc_link(doc, source)`: Funktion oder Definition `doc_link` dieses Moduls.
- `category(r)`: Funktion oder Definition `category` dieses Moduls.
- `generic_purpose(path)`: Funktion oder Definition `generic_purpose` dieses Moduls.
- `generic_edit(path)`: Funktion oder Definition `generic_edit` dieses Moduls.
- `symbol_desc(name, kind, parent)`: Funktion oder Definition `symbol_desc` dieses Moduls.
- `imports_for(path)`: Funktion oder Definition `imports_for` dieses Moduls.
- `py_args(node)`: Funktion oder Definition `py_args` dieses Moduls.
- `py_symbols(path)`: Funktion oder Definition `py_symbols` dieses Moduls.
- `ts_symbols(path)`: Funktion oder Definition `ts_symbols` dieses Moduls.
- `symbol_block(path)`: Funktion oder Definition `symbol_block` dieses Moduls.
- `write_reference(files)`: Funktion oder Definition `write_reference` dieses Moduls.
- `write_guides(files)`: Funktion oder Definition `write_guides` dieses Moduls.
- `main()`: Funktion oder Definition `main` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import ast`
- `import os`
- `import re`
- `import shutil`
- `import subprocess`
- `from collections import defaultdict`
- `from pathlib import Path`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

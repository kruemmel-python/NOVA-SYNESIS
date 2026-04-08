# `src/nova_synesis/cli.py`

- Quellpfad: [src/nova_synesis/cli.py](../../../../src/nova_synesis/cli.py)
- Kategorie: `Backend`

## Aufgabe der Datei

CLI-Einstiegspunkt fuer API-Start, Flow-Ausfuehrung und lokale Hilfsaufgaben.

## Wann du diese Datei bearbeitest

Wenn neue CLI-Kommandos oder Startoptionen hinzukommen.

## Funktionen

- `build_parser()`: Funktion oder Definition `build_parser` dieses Moduls.
- `_build_settings(args)`: Funktion oder Definition `_build_settings` dieses Moduls.
- `_execute_intent_from_file(file_path, settings)`: Funktion oder Definition `_execute_intent_from_file` dieses Moduls.
- `_run_flow_spec_from_file(file_path, settings)`: Funktion oder Definition `_run_flow_spec_from_file` dieses Moduls.
- `main()`: Funktion oder Definition `main` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import argparse`
- `import asyncio`
- `import json`
- `from pathlib import Path`
- `from typing import Any`
- `import uvicorn`
- `from nova_synesis.api.app import create_app`
- `from nova_synesis.config import Settings`
- `from nova_synesis.services.orchestrator import create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [run-backend.ps1](../../run-backend.ps1.md)
- [pyproject.toml](../../pyproject.toml.md)

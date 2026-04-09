# `src/nova_synesis/config.py`

- Quellpfad: [src/nova_synesis/config.py](../../../../src/nova_synesis/config.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Zentrale Laufzeitkonfiguration des Backends inklusive LiteRT- und Semantic-Firewall-Settings.

## Wann du diese Datei bearbeitest

Wenn neue Settings, Standardpfade, Planner-Optionen oder Policy-Grenzen benoetigt werden.

## Klassen

### `Settings`

Dataklasse fuer die Backend-Laufzeitkonfiguration.

Methoden:

- `from_env(cls)`: Laedt Settings aus Umgebungsvariablen mit sicheren Defaults.
- `ensure_directories(self)`: Erzeugt benoetigte Daten- und Arbeitsverzeichnisse.

## Funktionen

- `_env(primary, legacy, default)`: Funktion oder Definition `_env` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import os`
- `from dataclasses import dataclass`
- `from pathlib import Path`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [.env.example](../../.env.example.md)
- [src/nova_synesis/cli.py](cli.py.md)

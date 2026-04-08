# `src/nova_synesis/planning/__init__.py`

- Quellpfad: [src/nova_synesis/planning/__init__.py](../../../../../src/nova_synesis/planning/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from nova_synesis.planning.planner import IntentPlanner`
- `from nova_synesis.planning.lit_planner import LiteRTPlanner, PlannerCatalog, PlannerGraphResult`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

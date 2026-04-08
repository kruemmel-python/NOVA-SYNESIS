# `src/nova_synesis/security/__init__.py`

- Quellpfad: [src/nova_synesis/security/__init__.py](../../../../../src/nova_synesis/security/__init__.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Paketexporte fuer die semantische Sicherheitspruefung.

## Wann du diese Datei bearbeitest

Wenn Security-Klassen neu exportiert oder das Security-Paket umstrukturiert werden soll.

## Code-Inhalt

Diese Datei enthaelt keine eigenen Klassen oder Funktionen, sondern primar Paket-Exporte.

## Abhaengigkeiten

- `from .policy import FlowSecurityReport, SecurityFinding, SemanticFirewall`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/security/policy.py](policy.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)

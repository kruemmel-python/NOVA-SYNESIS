# `src/nova_synesis/security/trust.py`

- Quellpfad: [src/nova_synesis/security/trust.py](../../../../../src/nova_synesis/security/trust.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Digitale Handler-Zertifikate, Fingerprints und Trust-Validierung fuer Runtime-Handler.

## Wann du diese Datei bearbeitest

Wenn Handler-Zertifikate, Fingerprinting oder der Signaturmechanismus angepasst werden muessen.

## Klassen

### `HandlerCertificate`

Signierte Beschreibung eines vertrauenswuerdigen Handlers inklusive Fingerprint und Ablaufdatum.

Methoden:

- `payload(self)`: Funktion oder Definition `payload` dieses Moduls.
- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.
- `from_dict(cls, payload)`: Wandelt externe Daten fuer `from_dict` in das interne Format um.

### `HandlerTrustRecord`

Serialisierbare Trust-Sicht auf einen registrierten Handler fuer API und UI.

Methoden:

- `as_dict(self)`: Funktion oder Definition `as_dict` dieses Moduls.

### `HandlerTrustAuthority`

Signiert und validiert Handler-Zertifikate gegen den aktuellen Code-Fingerprint.

Methoden:

- `__init__(self, settings)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `fingerprint_handler(self, name, handler)`: Funktion oder Definition `fingerprint_handler` dieses Moduls.
- `issue_certificate(self, name, handler, *, built_in, expires_in_hours)`: Funktion oder Definition `issue_certificate` dieses Moduls.
- `validate_certificate(self, name, handler, raw_certificate)`: Funktion oder Definition `validate_certificate` dieses Moduls.
- `_sign_payload(self, payload)`: Funktion oder Definition `_sign_payload` dieses Moduls.

## Funktionen

- `_utcnow()`: Funktion oder Definition `_utcnow` dieses Moduls.
- `_parse_timestamp(value)`: Funktion oder Definition `_parse_timestamp` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import base64`
- `import hashlib`
- `import hmac`
- `import inspect`
- `import json`
- `from dataclasses import dataclass`
- `from datetime import datetime, timedelta, timezone`
- `from typing import Any, Callable`
- `from nova_synesis.config import Settings`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/runtime/handlers.py](../runtime/handlers.py.md)
- [src/nova_synesis/config.py](../config.py.md)
- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)

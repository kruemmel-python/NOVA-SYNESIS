# `src/nova_synesis/communication/adapters.py`

- Quellpfad: [src/nova_synesis/communication/adapters.py](../../../../../src/nova_synesis/communication/adapters.py)
- Kategorie: `Backend`

## Aufgabe der Datei

Python-Modul des Projekts.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Klassen

### `CommunicationAdapter`

Klasse `CommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, protocol, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.
- `close(self)`: Funktion oder Definition `close` dieses Moduls.

### `RestCommunicationAdapter`

Klasse `RestCommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_get_client(self)`: Funktion oder Definition `_get_client` dieses Moduls.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.
- `close(self)`: Funktion oder Definition `close` dieses Moduls.

### `WebSocketCommunicationAdapter`

Klasse `WebSocketCommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_get_connection(self)`: Funktion oder Definition `_get_connection` dieses Moduls.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.
- `close(self)`: Funktion oder Definition `close` dieses Moduls.

### `MessageQueueCommunicationAdapter`

Klasse `MessageQueueCommunicationAdapter` dieses Moduls.

Methoden:

- `__init__(self, endpoint, config)`: Konstruktor, der Abhaengigkeiten und Ausgangszustand vorbereitet.
- `_get_queue(self, endpoint)`: Funktion oder Definition `_get_queue` dieses Moduls.
- `send(self, message)`: Funktion oder Definition `send` dieses Moduls.
- `receive(self)`: Funktion oder Definition `receive` dieses Moduls.

### `CommunicationAdapterFactory`

Factory-Klasse `CommunicationAdapterFactory` zum Erzeugen passender Objekte.

Methoden:

- `create(protocol, endpoint, config)`: Funktion oder Definition `create` dieses Moduls.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `import json`
- `from typing import Any`
- `import httpx`
- `import websockets`
- `from nova_synesis.domain.models import ProtocolType`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

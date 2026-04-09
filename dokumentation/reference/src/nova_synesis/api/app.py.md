# `src/nova_synesis/api/app.py`

- Quellpfad: [src/nova_synesis/api/app.py](../../../../../src/nova_synesis/api/app.py)
- Kategorie: `Backend`

## Aufgabe der Datei

FastAPI- und WebSocket-Schicht des Backends inklusive Request-Modelle, Flow-Validierung und Live-Streaming.

## Wann du diese Datei bearbeitest

Wenn API-Endpunkte, Schemafelder, Sicherheitspruefung oder Live-Streaming erweitert werden.

## Klassen

### `CapabilityModel`

Datenmodell `CapabilityModel` fuer validierte Schichtgrenzen.

### `CommunicationModel`

Datenmodell `CommunicationModel` fuer validierte Schichtgrenzen.

### `AgentCreateRequest`

Datenmodell `AgentCreateRequest` fuer validierte Schichtgrenzen.

### `MemorySystemCreateRequest`

Datenmodell `MemorySystemCreateRequest` fuer validierte Schichtgrenzen.

### `ResourceCreateRequest`

Datenmodell `ResourceCreateRequest` fuer validierte Schichtgrenzen.

### `RetryPolicyModel`

Datenmodell `RetryPolicyModel` fuer validierte Schichtgrenzen.

### `ManualApprovalModel`

Datenmodell `ManualApprovalModel` fuer validierte Schichtgrenzen.

### `TaskSpecModel`

Datenmodell `TaskSpecModel` fuer validierte Schichtgrenzen.

### `EdgeModel`

Datenmodell `EdgeModel` fuer validierte Schichtgrenzen.

### `FlowCreateRequest`

Datenmodell `FlowCreateRequest` fuer validierte Schichtgrenzen.

### `IntentRequest`

Datenmodell `IntentRequest` fuer validierte Schichtgrenzen.

### `LLMPlannerRequest`

Datenmodell `LLMPlannerRequest` fuer validierte Schichtgrenzen.

### `NodeApprovalRequest`

Datenmodell `NodeApprovalRequest` fuer validierte Schichtgrenzen.

### `NodeApprovalRevokeRequest`

Datenmodell `NodeApprovalRevokeRequest` fuer validierte Schichtgrenzen.

## Funktionen

- `create_app(settings, orchestrator)`: Erzeugt die FastAPI-Anwendung und registriert ihre Endpunkte.

## Abhaengigkeiten

- `from __future__ import annotations`
- `import asyncio`
- `from contextlib import asynccontextmanager`
- `from typing import Any`
- `from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect`
- `from fastapi.middleware.cors import CORSMiddleware`
- `from pydantic import BaseModel, Field`
- `from nova_synesis.config import Settings`
- `from nova_synesis.domain.models import MemoryType, ProtocolType, ResourceType, RollbackStrategy`
- `from nova_synesis.services.orchestrator import OrchestratorService, create_orchestrator`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

## Verwandte Dateien

- [src/nova_synesis/services/orchestrator.py](../services/orchestrator.py.md)
- [frontend/src/lib/apiClient.ts](../../../frontend/src/lib/apiClient.ts.md)
- [frontend/src/types/api.ts](../../../frontend/src/types/api.ts.md)

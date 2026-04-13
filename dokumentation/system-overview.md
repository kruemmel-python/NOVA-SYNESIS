# Systemueberblick

## Schichten

- Domaene: `src/nova_synesis/domain/models.py`
- Planung: `planning/planner.py` und `planning/lit_planner.py`
- Sicherheitspruefung: `security/policy.py` und `security/trust.py`
- Runtime: `runtime/engine.py` und `runtime/handlers.py`
- Persistenz: `persistence/sqlite_repository.py`
- API: `api/app.py`
- UI: `frontend/src/`

## Hauptdatenfluss

1. Graph im Frontend erstellen oder ueber den LiteRT-Planer generieren
2. `toFlowRequest()` erzeugt das Backend-Schema
3. `POST /flows/validate` prueft Graph, Expressions, Handler-Trust, Egress und Memory-Fluesse
4. `POST /flows` legt einen Flow-Container mit initialer Version an
5. spaetere Speicherungen erzeugen ueber `POST /flows/{id}/versions` neue unveraenderliche Versionen
6. optionale manuelle Freigaben oder HITL-Eingaben werden node-spezifisch gesetzt
7. `POST /flows/{id}/run` startet die aktive oder explizit angegebene Version
8. `FlowExecutor` verarbeitet den Graphen Node fuer Node und kann kontrolliert auf `WAITING_FOR_INPUT` pausieren
9. `/ws/flows/{flow_id}` uebertraegt Snapshots, Waiting-Zustaende und Resume-Ereignisse an die UI
10. `GET /flows/{flow_id}` bleibt die kanonische Wahrheit fuer Laufzeitstand und aktive Version

## Betriebsachsen seit Phase 1 bis 5

- `Flow Versioning`: ein Flow ist jetzt ein Container mit historisierten Versionen statt ein einzelner ueberschriebener Snapshot
- `Human in the Loop`: Nodes koennen kontrolliert auf menschliche Eingabe warten und spaeter fortgesetzt werden
- `Observability`: jeder Task-Lauf kann Telemetriedaten fuer Handler- und Flow-Analytics erzeugen
- `RBAC`: Freigaben und HITL-Resumes koennen an Rollen wie `approver` gebunden werden
- `Sub-Flows`: wiederverwendbare Child-Workflows laufen als eigener Handler in isoliertem Unterkontext

## Was dieses System bewusst ist

- graphbasiert statt chatbasiert
- zustandsbehaftet statt nur requestbasiert
- planner-unterstuetzt, aber nicht planner-abhaengig
- sicherheitsgefiltert, bevor Seiteneffekte entstehen
- handler-vertrauensbasiert statt nur handler-namensbasiert

# Systemueberblick

## Schichten

- Domaene: `src/nova_synesis/domain/models.py`
- Planung: `planning/planner.py` und `planning/lit_planner.py`
- Runtime: `runtime/engine.py` und `runtime/handlers.py`
- Persistenz: `persistence/sqlite_repository.py`
- API: `api/app.py`
- UI: `frontend/src/`

## Hauptdatenfluss

1. Graph im Frontend erstellen oder generieren
2. `toFlowRequest()` erzeugt das Backend-Schema
3. `POST /flows` speichert den Graphen
4. `POST /flows/{id}/run` startet die Ausfuehrung
5. `FlowExecutor` verarbeitet den Graphen
6. `/ws/flows/{flow_id}` uebertraegt Snapshots an die UI

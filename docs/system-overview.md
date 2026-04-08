# Systemueberblick

## Schichten

- Domaene: `src/nova_synesis/domain/models.py`
- Planung: `planning/planner.py` und `planning/lit_planner.py`
- Sicherheitspruefung: `security/policy.py`
- Runtime: `runtime/engine.py` und `runtime/handlers.py`
- Persistenz: `persistence/sqlite_repository.py`
- API: `api/app.py`
- UI: `frontend/src/`

## Hauptdatenfluss

1. Graph im Frontend erstellen oder ueber den LiteRT-Planer generieren
2. `toFlowRequest()` erzeugt das Backend-Schema
3. `POST /flows/validate` prueft Graph, Expressions, Egress und Memory-Fluesse
4. `POST /flows` speichert den Graphen
5. `POST /flows/{id}/run` startet die Ausfuehrung
6. `FlowExecutor` verarbeitet den Graphen Node fuer Node
7. `/ws/flows/{flow_id}` uebertraegt Snapshots an die UI
8. `GET /flows/{flow_id}` bleibt die kanonische Wahrheit fuer den Laufzeitstand

## Was dieses System bewusst ist

- graphbasiert statt chatbasiert
- zustandsbehaftet statt nur requestbasiert
- planner-unterstuetzt, aber nicht planner-abhaengig
- sicherheitsgefiltert, bevor Seiteneffekte entstehen

# Aenderungsleitfaden

## Neuer Handler

1. Handler in `runtime/handlers.py` implementieren und registrieren
2. Tests erweitern
3. UI laedt den Handler automatisch ueber `/handlers`

## Neues Node-Feld

1. Backend-Schema in `api/app.py`
2. TypeScript-Typen in `frontend/src/types/api.ts`
3. Serialisierung in `frontend/src/lib/flowSerialization.ts`
4. Inspector in `frontend/src/components/layout/InspectorPanel.tsx`

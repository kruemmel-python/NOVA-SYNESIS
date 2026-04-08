# Aenderungsleitfaden

## Neuer Handler

1. Handler in `runtime/handlers.py` implementieren und registrieren
2. entscheiden, ob der Handler ein digitales Zertifikat erhalten soll oder bewusst untrusted bleibt
3. pruefen, ob der Handler im Planner sichtbar sein soll
4. Security-Regeln fuer Egress, Templates oder Seiteneffekte in `security/policy.py` bewerten
5. Tests in `tests/test_orchestrator.py` erweitern
6. Frontend prueft den Handler automatisch ueber `/handlers`
7. `tools/generate_docs.py` und danach `docs/` neu erzeugen

## Neues Node-Feld

1. Backend-Schema in `api/app.py`
2. Domaenenmodell und Snapshot in `domain/models.py`
3. TypeScript-Typen in `frontend/src/types/api.ts`
4. Serialisierung in `frontend/src/lib/flowSerialization.ts`
5. Inspector in `frontend/src/components/layout/InspectorPanel.tsx`
6. Validierung und Security-Auswirkungen pruefen
7. Tests und Dokumentation nachziehen

## Neue Security-Regel

1. Policy in `security/policy.py` erweitern
2. Settings in `config.py` und `.env.example` nachziehen
3. API- und Planner-Auswirkungen pruefen
4. mindestens einen positiven und einen negativen Testfall schreiben
5. `tools/generate_docs.py` ausfuehren und `docs/` neu erzeugen

## Neuer Trust- oder Approval-Pfad

1. Zertifikats- oder Approval-Logik in `security/trust.py`, `runtime/handlers.py` oder `domain/models.py` anpassen
2. `services/orchestrator.py` und `api/app.py` auf neue Operator-Aktionen abstimmen
3. Frontend-Inspector und Typen synchronisieren
4. mindestens einen positiven und einen negativen Security-Test ergaenzen
5. danach Referenzdoku und Betriebsdoku neu erzeugen

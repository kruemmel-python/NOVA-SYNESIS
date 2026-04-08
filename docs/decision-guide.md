# Decision Guide

Diese Seite dokumentiert Entscheidungslogik. Genau dieses Wissen fehlt oft, wenn ein System zwar sauber gebaut, aber noch nicht betriebssicher uebergeben wurde.

## 1. Wann Planner, wann manuell?

Nutze den LiteRT-Planer, wenn:

- du aus einer fachlichen Beschreibung schnell einen ersten Graphen ableiten willst
- du eine komplexe Kette mit mehreren Handlern skizzieren musst
- du anschliessend im visuellen Editor nacharbeiten willst

Baue den Flow lieber manuell, wenn:

- die exakte Kantenlogik bereits feststeht
- du einen Produktionsfehler analysierst
- du ein sehr kleines, deterministisches Setup mit 1 bis 3 Nodes hast

## 2. Neuer Handler oder bestehenden Handler erweitern?

Erweitere einen bestehenden Handler, wenn:

- dieselbe Grundoperation bleibt
- Ein- und Ausgabeform nur optional waechst
- Fehlerbild und Retry-Verhalten gleich bleiben

Baue einen neuen Handler, wenn:

- eine neue Nebenwirkung entsteht
- eine andere externe Abhaengigkeit angebunden wird
- der Inputvertrag fachlich anders ist
- der Nutzer den Baustein im Editor als eigenstaendige Aktion verstehen soll

## 3. Flow, einzelne Task oder Agent?

- Verwende einen Flow, wenn Reihenfolge, Verzweigung oder Fehlerbehandlung sichtbar modelliert werden muessen.
- Verwende nur eine einzelne Task, wenn genau ein isolierter Arbeitsschritt existiert.
- Verwende einen Agenten, wenn Faehigkeiten, Kommunikationsadapter oder eine feste Verantwortlichkeit wichtig sind.

Ein Agent ersetzt keinen Flow. Der Flow modelliert den Prozess. Der Agent modelliert, wer oder was eine Task ausfuehren darf.

## 4. Wann ist eine Resource wirklich notwendig?

Nutze eine Resource, wenn der Schritt an ein echtes externes Ziel oder eine limitierte Kapazitaet gebunden ist:

- API-Endpunkt
- Modellinstanz
- Datenbank
- Dateiablage
- GPU

Nutze keine Resource, wenn der Schritt rein lokal und transformativ ist:

- `template_render`
- `merge_payloads`
- `json_serialize`

## 5. Konkrete Resource-ID oder nur Resource-Type?

- `required_resource_ids`: wenn exakt ein bestimmtes System getroffen werden muss
- `required_resource_types`: wenn jeder passende Vertreter einer Kategorie ausreicht oder Fallback sinnvoll ist

Faustregel: feste Kern-API per ID, austauschbare Replikate oder GPUs per Typ.

## 6. Welche Rollback-Strategie ist die richtige?

- `FAIL_FAST`: wenn Folgeschritte ohne Erfolg des Nodes keinen Sinn ergeben
- `RETRY`: bei transienten Netz- oder Dienstfehlern
- `FALLBACK_RESOURCE`: wenn mehrere Ressourcen gleicher Art vorhanden sind
- `COMPENSATE`: wenn ein Fehler nach einer Nebenwirkung aktiv bereinigt werden muss

## 7. Wann musst du `POST /flows/validate` aktiv nutzen?

Immer vor produktivem Speichern oder Ausfuehren, wenn:

- ein Flow durch den Planner erzeugt wurde
- neue Templates, Conditions oder Validator-Ausdruecke eingebaut wurden
- neue Ressourcen, Agenten oder Memory-Systeme beteiligt sind
- du Security-Grenzen geaendert hast

## 8. Wie klassifizierst du Memory-Systeme?

- `sensitive = true`: fuer vertrauliche Inhalte, die nicht in Planner oder externe Sinks gelangen sollen
- `planner_visible = false`: wenn ein Memory manuell nutzbar, aber nicht planner-sichtbar sein soll
- `allow_untrusted_ingest = true`: nur wenn bewusst Daten aus HTTP, Messaging oder Dateiquellen in planner-sichtbares Wissen einfliessen duerfen

Wenn du unsicher bist, starte konservativ: `sensitive = true` oder `planner_visible = false`.

## 9. Wann soll eine Condition auf eine Edge?

Eine Edge-Condition ist richtig, wenn du einen fachlichen Branch modellierst:

- Erfolgspfad vs Fehlerpfad
- weitere Verarbeitung nur bei gueltigem Ergebnis
- optionale Folgeaktionen

Eine Edge-Condition ist falsch, wenn du damit Daten umbauen oder fehlende Vorverarbeitung verstecken willst. Dann fehlt meist ein eigener Node.

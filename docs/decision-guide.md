# Decision Guide

Diese Seite dokumentiert keine Syntax, sondern Entscheidungslogik. Genau dieses Wissen fehlt oft, wenn ein System zwar sauber gebaut, aber noch nicht betriebssicher uebergeben wurde.

## 1. Warum dieser Planner der Standard ist

Der lokale LiteRT-Planer ist hier die richtige Standardwahl, weil er vier Anforderungen gleichzeitig erfuellt:

- lokal und ohne Cloud-Abhaengigkeit
- auf den echten Handler-, Agenten- und Ressourcenkatalog begrenzt
- normalisiert auf das reale `FlowRequest`-Schema
- fuer manuelle Nachbearbeitung im visuellen Editor geeignet

Nutze den Planner, wenn:

- du einen Workflow schnell aus einer fachlichen Beschreibung ableiten willst
- du eine erste Graph-Struktur brauchst
- du vorhandene Flows mit neuen Ideen erweitern willst

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

Praktische Regel:

- `http_request` mit neuen optionalen Headern: bestehenden Handler erweitern
- Dateischreiben plus Upload zu einem Fremddienst: neuer Handler

Vermeide absichtlich einen Mega-Handler, der viele unverbundene Modi mit einem einzigen Namen abdeckt. Solche Handler sind schwer zu testen, schwer zu dokumentieren und fuehren im Planner schnell zu unsauberen Flows.

## 3. Flow, einzelne Task oder Agent?

### Verwende einen Flow, wenn

- Reihenfolge wichtig ist
- Verzweigungen oder Bedingungen existieren
- mehrere Nebenwirkungen koordiniert werden muessen
- Fehlerbehandlung ueber mehrere Schritte sichtbar sein soll

### Verwende nur eine einzelne Task, wenn

- genau ein Arbeitsschritt benoetigt wird
- keine Verzweigung und keine nachgelagerten Schritte existieren

### Verwende einen Agenten, wenn

- eine Task bewusst an einen bestimmten Faehigkeitstraeger gebunden sein soll
- Kommunikationsadapter benoetigt werden
- Capability-Gating fachlich wichtig ist

Wichtig:

Ein Agent ersetzt keinen Flow. Der Flow modelliert den Prozess. Der Agent modelliert, wer eine Task uebernehmen darf oder wie eine Task in ein Kommunikationsnetz eingebettet ist.

Viele sinnvolle Flows brauchen ueberhaupt keinen Agenten. Ein deterministischer `http_request -> memory_store`-Flow ist dafuer das beste Beispiel.

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

Nutze `required_resource_ids`, wenn:

- exakt ein bestimmter Endpunkt oder ein bestimmtes System getroffen werden muss
- Compliance, Umgebung oder Datenlokalitaet fest vorgegeben sind

Nutze `required_resource_types`, wenn:

- jeder passende Vertreter einer Kategorie ausreicht
- Fallback zwischen Ressourcen gleicher Art sinnvoll ist

Praxis:

- produktive Kern-API mit fester URL: konkrete Resource-ID
- beliebige freie GPU oder alternatives API-Replica: Resource-Type

## 6. Welche Rollback-Strategie ist die richtige?

- `FAIL_FAST`: bei irreversiblen Fehlern oder wenn Folgeschritte keinen Sinn mehr ergeben
- `RETRY`: bei transienten Netz- oder Dienstfehlern
- `FALLBACK_RESOURCE`: wenn mehrere Ressourcen gleicher Art vorhanden sind
- `COMPENSATE`: wenn ein Fehler nach einer Nebenwirkung aktiv bereinigt werden muss

Die Standardwahl fuer reine Infrastrukturprobleme ist meist `RETRY` oder `FALLBACK_RESOURCE`, nicht `COMPENSATE`.

## 7. Wann soll eine Condition auf eine Edge?

Eine Edge-Condition ist richtig, wenn du einen fachlichen Branch modellierst:

- Erfolgspfad vs Fehlerpfad
- weitere Verarbeitung nur bei gueltigem Ergebnis
- optionale Folgeaktionen

Eine Edge-Condition ist falsch, wenn du damit versuchst, Daten umzubauen oder fehlende Vorverarbeitung zu kompensieren. Dann fehlt meist ein eigener Node.

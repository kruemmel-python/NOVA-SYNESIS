# Ausfuehrliche Dokumentation: Accounts Receivable Reminder

## Zweck dieser Datei

Diese Datei ist die technische Tiefendokumentation fuer den Use-Case `accounts_receivable_reminder`.
Sie richtet sich an Entwickler, die den Ordner zum ersten Mal oeffnen und verstehen wollen:

- welche Dateien im Ordner existieren
- wie der Graph fachlich und technisch arbeitet
- welche Eingabedaten erwartet werden
- welche Handler verwendet werden
- welche Ausgaben entstehen
- wo der lokale LLM-Pfad in den Prozess eingreift
- wie die Varianten `csv`, `db` und `web_ui` zusammenhaengen
- an welchen Stellen man den Ablauf sicher anpassen kann
- welche Fehlerbilder wahrscheinlich sind und wie man sie behebt

Wenn das kurze [README.md](./README.md) der schnelle Einstieg ist, dann ist diese Datei das technische Handbuch.

## Kurzueberblick

Der Use-Case liest Bestelldaten aus `data/orders.csv` oder `data/orders.db`, filtert alle noch nicht bezahlten Rechnungen heraus, aggregiert diese pro Kunde und erzeugt daraus Serienanschreiben zur Zahlungserinnerung.

Der Ablauf ist bewusst lokal und deterministisch aufgebaut:

- keine externen APIs
- keine registrierten Agenten
- keine Memory-Systeme
- keine Resources
- keine semantische Firewall-Probleme durch Netzwerkzugriffe

Der Graph nutzt nur lokale Built-in-Handler:

- `accounts_receivable_extract`
- `json_serialize`
- `write_file`
- `accounts_receivable_generate_letters`
- `accounts_receivable_write_letters`

Wichtig:

- Der Use-Case funktioniert vollstaendig ohne LLM.
- Der lokale LLM ist eine optionale Textgenerierungsschicht nur fuer die Formulierung der Briefe.
- Die Extraktion offener Forderungen und die betriebswirtschaftlichen Zahlen bleiben immer deterministisch.

## Was liegt in diesem Ordner?

### Kern-Dateien

- `README.md`
  Kurzer Einstieg, Schnellstart, erwartete Artefakte.
- `AUSFUEHRLICHE_DOKUMENTATION.md`
  Diese Datei mit dem kompletten technischen Hintergrund.
- `setup.ps1`
  Prueft den laufenden Backend-Prozess auf die benoetigten Handler und legt die Ausgabeordner unter `billing/` an.
- `run.ps1`
  Fuehrt Setup, Flow-Erstellung und Flow-Ausfuehrung gegen das echte Backend aus.

### Flow-Definitionen

- `flow.orders_csv.json`
  Produktive Flow-Definition fuer `data/orders.csv`.
- `flow.orders_db.json`
  Produktive Flow-Definition fuer `data/orders.db`.
- `flow.web_ui.orders_csv.json`
  Inhaltlich dieselbe CSV-Variante, aber mit `metadata.ui` fuer Titel, Beschreibungen und Positionen im visuellen Editor.
- `flow.web_ui.orders_db.json`
  Inhaltlich dieselbe SQLite-Variante, ebenfalls mit `metadata.ui`.

### Laufzeit-Artefakte

- `output/csv/...`
  JSON-Report, Manifest und Zusammenfassung fuer den CSV-Lauf.
- `output/db/...`
  JSON-Report, Manifest und Zusammenfassung fuer den SQLite-Lauf.

Wichtig:

- Die eigentlichen Anschreiben liegen nicht unter `output/`, sondern unter `billing/csv` oder `billing/db`.
- Das ist absichtlich so getrennt: `output/` ist die technische Nachvollziehbarkeit, `billing/` ist die operative Ausgabe.

## Wie ist der Use-Case fachlich aufgebaut?

Der Use-Case folgt einem sehr klaren 5-Stufen-Modell:

1. Rechnungsdaten einlesen
2. Offene Forderungen pro Kunde aggregieren
3. Technischen JSON-Report schreiben
4. Schreiben pro Kunde generieren
5. Schreiben als `.docx` persistieren

Das ist keine lose Skriptsammlung, sondern ein echter Flow in der Orchestrierungs-Engine. Jeder Schritt ist ein Node im Graphen.

## Der Graph im Detail

Alle Varianten verwenden dieselbe fachliche Topologie:

1. `extract_open_receivables`
2. `serialize_receivables`
3. `write_receivables_report`
4. `generate_reminder_letters`
5. `persist_reminder_letters`

### Node 1: `extract_open_receivables`

Handler:

- `accounts_receivable_extract`

Aufgabe:

- liest die Quelldatei
- normalisiert Datensaetze
- markiert Rechnungen als `PAID`, `OPEN` oder `OVERDUE`
- gruppiert alle unbezahlten Rechnungen pro Kunde
- berechnet Summen und Statistiken

CSV-Variante:

- `path = data/orders.csv`
- `source_type = csv`

SQLite-Variante:

- `path = data/orders.db`
- `source_type = sqlite`
- `table = orders`

Die Ausgabe dieses Nodes ist bereits ein fachlich aufbereitetes Objekt und nicht nur ein Rohimport.

### Node 2: `serialize_receivables`

Handler:

- `json_serialize`

Aufgabe:

- serialisiert das Ergebnis von `extract_open_receivables` als gut lesbares JSON

Warum gibt es diesen Schritt?

- weil der technische Forderungsstand als Artefakt abgelegt werden soll
- weil der Report fuer Revision, Debugging und manuelle Kontrolle direkt lesbar sein soll

### Node 3: `write_receivables_report`

Handler:

- `write_file`

Aufgabe:

- schreibt den serialisierten JSON-Bericht unter `Use_Cases/accounts_receivable_reminder/output/...`

Dieser Node ist fachlich optional, aber operativ sehr wertvoll. Ohne ihn gaebe es zwar Briefe, aber keinen klaren Zwischenstand darueber, welche Forderungen genau in die Verarbeitung eingeflossen sind.

### Node 4: `generate_reminder_letters`

Handler:

- `accounts_receivable_generate_letters`

Aufgabe:

- erzeugt pro Kunde einen Briefinhalt
- uebernimmt Absenderdaten
- setzt eine Zahlungsfrist
- listet pro Kunde alle offenen Rechnungen im Anschreiben auf

Dieser Node kennt jetzt zwei Betriebsmodi:

- `template`
  eingebautes Python-Template, schnell und deterministisch
- `llm`
  das lokale LiteRT-Modell formuliert den Brieftext pro Kunde anhand eines Benutzerprompts

Wichtig:

- Dieser Node schreibt noch keine Dateien.
- Er erzeugt eine Liste von Briefobjekten im Speicher.

### Wo greift der lokale LLM ein?

Nur in Node `generate_reminder_letters`.

Der Ablauf ist dann:

1. `extract_open_receivables` liefert die fachlich korrekten Kundendaten
2. `generate_reminder_letters` baut daraus pro Kunde einen Prompt
3. dieser Prompt wird lokal an das konfigurierte LiteRT-Modell gesendet
4. das Modell liefert den finalen Brieftext
5. `persist_reminder_letters` schreibt diesen Text als `.docx`

Das ist die zentrale Architekturentscheidung:

- Das LLM entscheidet nicht, welche Kunden offen sind.
- Das LLM entscheidet nicht, welche Summen oder Fristen gelten.
- Das LLM formuliert nur den sprachlichen Inhalt des Anschreibens.

### Node 5: `persist_reminder_letters`

Handler:

- `accounts_receivable_write_letters`

Aufgabe:

- schreibt die generierten Briefe als `.docx`
- schreibt ein Manifest aller erzeugten Briefe
- schreibt eine kurze Textzusammenfassung

Technische Ausgaben:

- `billing/csv/*.docx` oder `billing/db/*.docx`
- `Use_Cases/accounts_receivable_reminder/output/.../letters-manifest.json`
- `Use_Cases/accounts_receivable_reminder/output/.../letters-summary.txt`

## Welche Edges steuern die Ausfuehrung?

Die Flows haben vier Kanten:

1. `extract_open_receivables -> serialize_receivables`
   Bedingung: `True`
2. `serialize_receivables -> write_receivables_report`
   Bedingung: `True`
3. `extract_open_receivables -> generate_reminder_letters`
   Bedingung: `results['extract_open_receivables']['customer_count'] > 0`
4. `generate_reminder_letters -> persist_reminder_letters`
   Bedingung: `results['generate_reminder_letters']['letter_count'] > 0`

Warum ist das wichtig?

- Es wird immer ein JSON-Report geschrieben, auch wenn keine offenen Forderungen gefunden werden.
- Briefe werden nur erzeugt, wenn wirklich mindestens ein betroffener Kunde vorhanden ist.
- Das vermeidet leere operative Outputs.

## Welche Eingabedaten werden erwartet?

### CSV-Schema

Der CSV-Import erwartet Spalten mit mindestens diesen Namen:

- `customer_name`
- `email`
- `address`
- `product`
- `quantity`
- `price_per_unit`
- `total_price`
- `order_date`
- `delivery_date`
- `invoice_due_date`
- `invoice_paid`

Optional bzw. alternativ:

- `id` oder `invoice_id`
  fuer eine lesbare Rechnungsreferenz

Wenn `id` oder `invoice_id` fehlen, wird intern automatisch ein technischer Bezeichner wie `invoice-0001` erzeugt.

### SQLite-Schema

Die SQLite-Variante erwartet eine Tabelle mit denselben logischen Feldern:

- `id`
- `customer_name`
- `email`
- `address`
- `product`
- `quantity`
- `price_per_unit`
- `total_price`
- `order_date`
- `delivery_date`
- `invoice_due_date`
- `invoice_paid`

Die Standardtabelle ist `orders`.

Wichtig:

- Der Tabellenname wird serverseitig nur akzeptiert, wenn er auf das Muster `[A-Za-z_][A-Za-z0-9_]*` passt.
- Das ist eine bewusste Schutzmassnahme gegen unsaubere dynamische SQL-Namen.

## Wie erkennt der Handler, was offen ist?

Die Logik sitzt in `accounts_receivable_extract_handler` und den Hilfsfunktionen in [handlers.py](../../../src/nova_synesis/runtime/handlers.py).

Pro Datensatz passiert Folgendes:

1. Datumsfelder werden geparst.
2. `invoice_paid` wird in einen echten Bool-Wert ueberfuehrt.
3. `total_price` wird als Zahl normalisiert.
4. Wenn `invoice_paid = true`, ist der Datensatz `PAID`.
5. Wenn `invoice_paid = false`, ist der Datensatz mindestens `OPEN`.
6. Wenn das Faelligkeitsdatum vor dem Auswertungsdatum liegt, wird der Status `OVERDUE`.
7. `days_overdue` wird berechnet.

Danach werden alle unbezahlten Rechnungen pro Kunde gruppiert. Der Gruppierungsschluessel ist:

- `customer_name`
- `email`
- `address`

Das bedeutet:

- Mehrere offene Rechnungen desselben Kunden landen in einem gemeinsamen Anschreiben.
- Ein Kunde mit unterschiedlichen Adressen oder E-Mail-Adressen wird als unterschiedliche Gruppe behandelt.

## Welche Daten liefert `extract_open_receivables` zurueck?

Die Rueckgabe ist kein beliebiges Objekt, sondern ein fachliches Summary mit:

- `as_of`
- `customer_count`
- `invoice_count`
- `overdue_count`
- `total_outstanding`
- `currency`
- `customers`
- `source_path`
- `source_type`
- `table`

Jeder Eintrag in `customers` enthaelt unter anderem:

- `customer_id`
- `customer_name`
- `email`
- `address`
- `invoice_count`
- `overdue_invoice_count`
- `max_days_overdue`
- `total_outstanding`
- `currency`
- `invoices`

Die `customers` werden sortiert nach:

1. Anzahl ueberfaelliger Rechnungen absteigend
2. Offener Gesamtsumme absteigend
3. Kundenname alphabetisch

Dadurch stehen die kritischsten Faelle fachlich vorne.

## Wie werden die Briefe erzeugt?

`accounts_receivable_generate_letters` nimmt das Summary von `extract_open_receivables` und formuliert daraus Serienkorrespondenz.

Konfigurierbare Werte im Flow:

- `sender_company`
- `sender_email`
- `sender_phone`
- `sender_address`
- `payment_deadline_days`

Der Node baut pro Kunde:

- Betreff
- Absenderblock
- Kundenanschrift
- Liste aller offenen Rechnungen
- Gesamtbetrag
- Zahlungsfrist
- Schlussformel

Wichtig:

- Die Briefe referenzieren alle offenen Rechnungen eines Kunden gesammelt.
- Der Node vergibt auch Dateinamen und einen `file_stem`.
- Umlaute und Sonderzeichen in Namen werden fuer Dateinamen in einen ASCII-Slug ueberfuehrt.

### Zusatzfelder fuer den LLM-Modus

Wenn `generation_mode = llm` gesetzt ist, kennt der Node zusaetzlich:

- `user_instruction`
  fachliche Schreibanweisung des Benutzers
- `prompt_template`
  Promptstruktur fuer das lokale Modell
- `fallback_to_template_on_error`
  faellt bei Modellfehlern auf das eingebaute Template zurueck

### Verfuegbare Platzhalter im Prompt

Das Prompt-Template kann diese Felder verwenden:

- `{sender_company}`
- `{sender_email}`
- `{sender_phone}`
- `{sender_address}`
- `{customer_name}`
- `{customer_email}`
- `{customer_address}`
- `{invoice_count}`
- `{overdue_invoice_count}`
- `{max_days_overdue}`
- `{total_outstanding}`
- `{currency}`
- `{as_of_date}`
- `{settle_by_date}`
- `{invoice_lines}`
- `{invoices_json}`
- `{customer_json}`
- `{user_instruction}`

### Was ist `user_instruction`?

`user_instruction` ist die eigentliche unternehmerische Entscheidung darueber, wie das Anschreiben formuliert werden soll.

Beispiele:

- freundlich und serviceorientiert
- formal und bestimmt
- kulant mit Hinweis auf Teilzahlungsmoeglichkeit
- deutlich, aber deeskalierend

Damit ist der Schreibstil nicht hart im Code festgelegt, sondern durch den Benutzer steuerbar.

## Wie werden die `.docx`-Dateien geschrieben?

`accounts_receivable_write_letters` ist der Persistenz-Node fuer die operative Ausgabe.

Eingaben:

- `letters`
- `output_directory`
- `manifest_path`
- `summary_path`
- `encoding`
- `output_format`

Aktuell unterstuetzte Formate:

- `txt`
- `docx`

Der Use-Case nutzt absichtlich `docx`, damit die Buchhaltung sofort mit Word-kompatiblen Dateien arbeiten kann.

Der Handler macht drei Dinge:

1. Er schreibt fuer jeden Brief eine Datei in den Zielordner.
2. Er schreibt ein JSON-Manifest mit allen geschriebenen Dateien.
3. Er schreibt eine Textzusammenfassung mit Anzahl und Zielpfaden.

Rueckgabe des Nodes:

- `written`
- `letter_count`
- `output_directory`
- `letters`
- `manifest_path`
- `summary_path`

## Warum gibt es zwei Arten von Flow-Dateien?

### Produktive Flows

- `flow.orders_csv.json`
- `flow.orders_db.json`

Diese Dateien sind minimal, sauber und direkt gegen die API lauffaehig.

### Web-UI-Flows

- `flow.web_ui.orders_csv.json`
- `flow.web_ui.orders_db.json`

Diese Dateien enthalten zusaetzlich `metadata.ui`:

- `title`
- `summary`
- `description`
- `notes`
- `position`

Das ist keine fachliche Laufzeitlogik, sondern reine Editor-Unterstuetzung.

Der Inhalt ist deshalb in zwei Schichten getrennt:

- fachliche Ausfuehrung in `node_id`, `handler_name`, `input`, `edges`
- visuelle Hilfen in `metadata.ui`

In der Web-UI ist fuer `accounts_receivable_generate_letters` ausserdem ein spezieller Inspector-Bereich vorhanden:

- `LLM Letter Drafting`
- Aktivierung des lokalen LLM
- Preview fuer einen einzelnen Beispielkunden
- Bearbeitung von `Business instruction`
- Bearbeitung von `Prompt template`
- optionaler Fallback auf das Standardtemplate

## Wie funktioniert `setup.ps1`?

`setup.ps1` macht bewusst nur zwei Dinge:

1. Es fragt `GET /handlers` am laufenden Backend ab.
2. Es legt die Ausgabeordner unter `billing/csv` und `billing/db` an.

Es registriert nichts am Backend, weil dieser Use-Case nur bereits eingebaute Handler verwendet.

Wenn Handler fehlen, bricht `setup.ps1` sofort mit einer klaren Fehlermeldung ab:

- Das ist fast immer ein Zeichen dafuer, dass der Backend-Prozess noch vor Einfuehrung der neuen Built-ins gestartet wurde.
- Die Loesung ist dann ein Backend-Neustart.

## Wie funktioniert `run.ps1`?

`run.ps1` ist der bequeme Endpunkt fuer den ganzen Use-Case.

Ablauf:

1. `setup.ps1` ausfuehren
2. passende Flow-Datei waehlen
3. `POST /flows`
4. `POST /flows/{flow_id}/run`
5. Ergebnisobjekt in PowerShell ausgeben

Waehlbare Varianten:

- `-Source csv`
- `-Source db`

Die Ausgabe von `run.ps1` zeigt unter anderem:

- `flow_id`
- `flow_url`
- erwartete Ausgabedateien
- Rueckgabe des Run-Endpunkts

## Wo landen die Ergebnisse genau?

### CSV-Variante

- `Use_Cases/accounts_receivable_reminder/output/csv/open-receivables.json`
- `Use_Cases/accounts_receivable_reminder/output/csv/letters-manifest.json`
- `Use_Cases/accounts_receivable_reminder/output/csv/letters-summary.txt`
- `billing/csv/*.docx`

### SQLite-Variante

- `Use_Cases/accounts_receivable_reminder/output/db/open-receivables.json`
- `Use_Cases/accounts_receivable_reminder/output/db/letters-manifest.json`
- `Use_Cases/accounts_receivable_reminder/output/db/letters-summary.txt`
- `billing/db/*.docx`

## Welche Dateien sollte ein Entwickler zuerst lesen?

Wenn du den Ordner neu oeffnest, ist diese Reihenfolge sinnvoll:

1. `README.md`
2. `flow.orders_csv.json` oder `flow.orders_db.json`
3. `run.ps1`
4. `setup.ps1`
5. `flow.web_ui.orders_csv.json` oder `flow.web_ui.orders_db.json`
6. diese Datei

Wenn du tiefer in die Laufzeitlogik gehen willst:

1. [src/nova_synesis/runtime/handlers.py](../../../src/nova_synesis/runtime/handlers.py)
2. [tests/test_orchestrator.py](../../../tests/test_orchestrator.py)

## Welche Pfade sind relativ wozu?

Das ist eine der wichtigsten praktischen Fragen.

Die Flow-Dateien enthalten relative Pfade wie:

- `data/orders.csv`
- `Use_Cases/accounts_receivable_reminder/output/csv/open-receivables.json`
- `billing/csv`

Diese Pfade werden zur `working_directory` des Backend-Prozesses aufgeloest. Im Normalfall ist das das Projektwurzelverzeichnis `D:\Agenten_UML`.

Deshalb funktionieren die im Flow eingetragenen relativen Pfade genau dann korrekt, wenn das Backend aus dem Projektroot gestartet wurde.

## Welche Teile sind datumsabhaengig?

Wenn im Flow kein `as_of` gesetzt ist, verwendet `accounts_receivable_extract` die aktuelle Zeit des Laufes.

Das bedeutet:

- `OVERDUE` und `days_overdue` haengen vom Ausfuehrungszeitpunkt ab.
- Die Formulierung im Anschreiben verwendet dieses Datum ebenfalls.

In den produktiven Use-Case-Dateien ist absichtlich kein fixes `as_of` gesetzt, damit der Lauf immer den aktuellen Stand verwendet.

In Tests wird `as_of` dagegen explizit gesetzt, damit das Ergebnis reproduzierbar bleibt.

## Warum braucht dieser Use-Case keine Agenten, Resources oder Memory-Systeme?

Weil der gesamte Ablauf lokal ueber Dateien und Built-in-Handler geloest wird.

Das hat mehrere Vorteile:

- kein Setup fuer Agentenregistrierung
- keine Kommunikationsadapter
- keine Message-Targets
- keine Memory-Policies
- keine semantische Firewall fuer externe Hosts

Fuer diesen konkreten Geschaeftsprozess ist das absichtlich einfacher und robuster als ein agentischer Flow.

## Typische Anpassungen

### 1. Andere Quelldatei

CSV:

- `extract_open_receivables.input.path` aendern

SQLite:

- `extract_open_receivables.input.path` aendern
- bei Bedarf `extract_open_receivables.input.table` aendern

### 2. Anderes Erscheinungsbild der Briefe

Im Node `generate_reminder_letters` anpassen:

- `sender_company`
- `sender_email`
- `sender_phone`
- `sender_address`
- `payment_deadline_days`

Wenn du die Textstruktur selbst aendern willst, musst du den Python-Handler `accounts_receivable_generate_letters_handler` anpassen.

Wenn du statt des festen Templates das lokale Modell formulieren lassen willst, musst du den Handler nicht aendern.
Dann reicht in der Web-UI:

- den Node `Generate Reminder Letters` auszuwaehlen
- `Use local LLM to draft the letter text` zu aktivieren
- optional `Preview customer index` fuer einen Beispielkunden zu setzen
- `Preview Draft` zu klicken, um sofort einen Testbrief zu erzeugen
- `Business instruction` und `Prompt template` anzupassen

### Was macht `Preview Draft` genau?

`Preview Draft` fuehrt nicht den ganzen Flow aus.

Stattdessen passiert serverseitig:

1. der zugehoerige `accounts_receivable_extract`-Node wird mit der aktuellen Quelldatei ausgefuehrt
2. genau ein Kunde aus dem Ergebnis wird ueber `customer_index` ausgewaehlt
3. fuer diesen Kunden wird der aktuelle Prompt aufgebaut
4. das lokale LiteRT-Modell erzeugt einen Beispielbrief
5. Prompt und Brieftext werden an die Web-UI zurueckgegeben

Dadurch kann der Benutzer den Schreibstil pruefen, ohne:

- den ganzen Flow zu speichern
- alle Briefe neu zu erzeugen
- sofort `.docx`-Dateien zu schreiben

Wichtig ist der Unterschied zwischen Vorschau und Produktivlauf:

- `Preview Draft` nutzt die aktuellen Inspector-Einstellungen unmittelbar
- `Preview Draft` aendert weder gespeicherte Flows noch erzeugte Serienbriefe
- erst nach `Save Flow` und `Run Flow` verwendet NOVA-SYNESIS dieselbe LLM-Konfiguration fuer jeden Kunden im gesamten Datenbestand
- wenn das lokale LiteRT-Modell fuer die Vorschau nicht rechtzeitig antwortet, beendet NOVA-SYNESIS den Vorschau-Request kontrolliert und meldet den Timeout im Inspector

### 3. Nur ueberfaellige Rechnungen statt aller offenen Rechnungen

Das ist aktuell nicht als Flow-Option eingebaut. Die Logik sitzt im Extract-Handler.

Dafuer gibt es zwei saubere Wege:

- Filter direkt in `accounts_receivable_extract_handler` ergaenzen
- oder einen neuen nachgelagerten Filter-Handler einfuehren

Wenn du die bestehende Standardlogik nicht global aendern willst, ist ein neuer Handler die bessere Wahl.

### 4. Andere Ausgabeformate

Moeglichkeiten:

- `output_format` auf `txt` setzen
- weiteren Report-Node nach `serialize_receivables` ergaenzen
- eigenen Handler fuer PDF oder zusaetzliche Briefvorlagen einfuehren

### 5. Andere Ordnerstruktur

Im Node `persist_reminder_letters` anpassen:

- `output_directory`
- `manifest_path`
- `summary_path`

## Haeufige Fragen

### Warum wird kein Brief erzeugt, obwohl die Quelldatei existiert?

Moegliche Gruende:

- alle Rechnungen sind bereits bezahlt
- `invoice_paid` wird in der Quelle unerwartet formatiert
- `customer_count` ist `0`, daher wird die Edge zu `generate_reminder_letters` nicht aktiviert

Pruefe zuerst:

- `open-receivables.json`

### Warum wird nur ein Kunde statt mehrerer angeschrieben?

Weil nach `(customer_name, email, address)` gruppiert wird. Mehrere Rechnungen desselben Kunden werden absichtlich zu einem Schreiben zusammengefasst.

### Warum liegen die Briefe in `billing/` und nicht im Use-Case-Ordner?

Weil `billing/` der operative Zielordner ist. Der Use-Case-Ordner enthaelt Doku, Definitionen und technische Reports. Die Serienanschreiben sollen separat fuer die Buchhaltung bereitliegen.

### Warum gibt es sowohl Manifest als auch Summary?

Weil beide unterschiedliche Zwecke haben:

- `letters-manifest.json` ist maschinenlesbar
- `letters-summary.txt` ist fuer schnelle menschliche Kontrolle

### Warum ist `json_serialize` ein eigener Node statt direkt im Write-Node?

Weil dadurch die Datenkonvertierung explizit sichtbar ist. Das macht den Flow im Editor lesbarer und erleichtert spaetere Erweiterungen.

### Was ist der Unterschied zwischen `OPEN` und `OVERDUE`?

- `OPEN`: Rechnung unbezahlt, aber noch nicht ueberfellig
- `OVERDUE`: Rechnung unbezahlt und Faelligkeit liegt vor `as_of`

### Wo genau entsteht im LLM-Modus der Brieftext?

Im Backend im Handler `accounts_receivable_generate_letters_handler`.

Der Unterschied ist:

- im Modus `template` wird der Text direkt in Python zusammengesetzt
- im Modus `llm` wird zuerst ein Prompt aus den Kundendaten gebaut und danach vom lokalen LiteRT-Modell beantwortet

### Muss ich vor dem UI-Import `setup.ps1` ausfuehren?

Ja, das ist empfehlenswert.

Nicht weil der Flow Registrierungen braucht, sondern weil:

- `setup.ps1` den laufenden Backend-Prozess auf die benoetigten Handler prueft
- `setup.ps1` die Zielordner vorbereitet

## Typische Fehlerbilder und Loesungen

### Fehler: Handler unbekannt

Ursache:

- Backend lief noch mit einem alten Prozessstand

Loesung:

- Backend neu starten
- `setup.ps1` erneut ausfuehren

### Fehler: Pfad nicht gefunden

Ursache:

- Backend wurde nicht vom Projektroot gestartet
- Eingabedatei existiert nicht
- Flow-Pfade wurden falsch angepasst

Loesung:

- Backend aus `D:\Agenten_UML` starten
- `path` im Extract-Node pruefen

### Fehler: SQLite-Tabelle wird nicht akzeptiert

Ursache:

- Tabellenname enthaelt ungueltige Zeichen

Loesung:

- einfachen alphanumerischen Namen mit Unterstrichen verwenden

### Fehler: Es entstehen keine `.docx`-Dateien

Ursache:

- `generate_reminder_letters` hat `letter_count = 0`
- Edge zu `persist_reminder_letters` wurde nicht aktiviert
- Zielordner falsch gesetzt

Loesung:

- `open-receivables.json` und Flow-Status pruefen
- `output_directory` kontrollieren

## Wie ist der Use-Case getestet?

Die zentrale End-to-End-Absicherung liegt in [tests/test_orchestrator.py](../../../tests/test_orchestrator.py).

Abgedeckt sind:

- CSV-Lauf
- SQLite-Lauf
- Schreiben echter `.docx`-Dateien
- Manifest- und Summary-Erzeugung
- inhaltliche Pruefung der erzeugten Dokumente

Die Tests sind wichtig, weil sie den kompletten Pfad pruefen:

- Daten lesen
- offene Forderungen bestimmen
- Briefe generieren
- Dateien schreiben

## Wie erweitert man den Use-Case sauber?

Wenn du nur einen Ablaufparameter aendern willst:

- Flow-Datei anpassen

Wenn du fachliche Textlogik aendern willst:

- `accounts_receivable_generate_letters_handler` anpassen

Wenn du das Dateiformat oder die Persistenz aendern willst:

- `accounts_receivable_write_letters_handler` anpassen

Wenn du die fachliche Definition offener Posten aendern willst:

- `accounts_receivable_extract_handler` anpassen

Wenn du eine neue fachliche Phase einfuehren willst:

- neuen Handler bauen
- neuen Node in den Flow aufnehmen

Gute Kandidaten fuer Erweiterungen:

- Eskalationsstufen je Mahnstufe
- separates Filtern nur ueberfaelliger Forderungen
- Segmentierung nach Kundentyp
- PDF-Ausgabe
- Versand ueber Kommunikationsagenten
- Ablage in Memory oder DMS

## Die wichtigste Designentscheidung in einem Satz

Dieser Use-Case ist absichtlich kein agentischer Demonstrator, sondern ein klar nachvollziehbarer, lokal ausfuehrbarer Produktions-Flow fuer einen konkreten Geschaeftsprozess.

Genau deshalb ist er fuer neue Entwickler gut geeignet:

- wenig versteckte Magie
- klare Node-Grenzen
- lokale Artefakte
- nachvollziehbare Datenfluesse
- sauber testbar

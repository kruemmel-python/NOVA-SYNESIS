# Accounts Receivable Reminder

## Ziel

Dieser Use-Case filtert aus `data/orders.csv` oder `data/orders.db` alle Kunden mit offenen Rechnungen
und erzeugt pro Kunde ein professionelles Anschreiben zur Bereinigung der offenen Verbindlichkeiten.

Der Workflow arbeitet vollstaendig lokal auf den Projektdateien und nutzt reale Built-in-Handler:

- `accounts_receivable_extract`
- `json_serialize`
- `write_file`
- `accounts_receivable_generate_letters`
- `accounts_receivable_write_letters`

## Varianten

- `flow.orders_csv.json`: liest `data/orders.csv`
- `flow.orders_db.json`: liest `data/orders.db`
- `flow.web_ui.orders_csv.json`: dieselbe CSV-Variante mit vorbelegten `metadata.ui` Informationen fuer den visuellen Editor
- `flow.web_ui.orders_db.json`: dieselbe SQLite-Variante mit vorbelegten `metadata.ui` Informationen fuer den visuellen Editor

Beide Flows erzeugen:

- einen strukturierten JSON-Report ueber alle offenen Forderungen
- einzelne Anschreiben je betroffenem Kunden als `.docx`
- ein Manifest aller geschriebenen Schreiben
- eine kurze Zusammenfassung als Textdatei

## Voraussetzung

Der Backend-Server muss laufen, zum Beispiel:

```powershell
.\run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

Wichtig: Die neuen Rechnungs-Handler sind Built-ins. Wenn der Backend-Prozess noch vor ihrer Einfuehrung gestartet wurde,
muss er einmal neu gestartet werden. `setup.ps1` prueft genau das.

## Schnellstart

CSV-Variante:

```powershell
.\Use_Cases\accounts_receivable_reminder\run.ps1 -ApiBaseUrl http://127.0.0.1:8552 -Source csv
```

SQLite-Variante:

```powershell
.\Use_Cases\accounts_receivable_reminder\run.ps1 -ApiBaseUrl http://127.0.0.1:8552 -Source db
```

Optional kann das Setup separat ausgefuehrt werden:

```powershell
.\Use_Cases\accounts_receivable_reminder\setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

## Ablauf im Graphen

- `extract_open_receivables`: liest die Quelldatei und gruppiert alle unbezahlten Rechnungen nach Kunde
- `serialize_receivables`: serialisiert das Ergebnis als JSON
- `write_receivables_report`: schreibt den Forderungsreport in den Use-Case-Ordner
- `generate_reminder_letters`: erzeugt pro Kunde ein Anschreiben
- `persist_reminder_letters`: schreibt alle Anschreiben als `.docx` in `billing/` sowie Manifest und Zusammenfassung

## Erwartete Artefakte

CSV-Lauf:

- `Use_Cases/accounts_receivable_reminder/output/csv/open-receivables.json`
- `Use_Cases/accounts_receivable_reminder/output/csv/letters-manifest.json`
- `Use_Cases/accounts_receivable_reminder/output/csv/letters-summary.txt`
- `billing/csv/*.docx`

SQLite-Lauf:

- `Use_Cases/accounts_receivable_reminder/output/db/open-receivables.json`
- `Use_Cases/accounts_receivable_reminder/output/db/letters-manifest.json`
- `Use_Cases/accounts_receivable_reminder/output/db/letters-summary.txt`
- `billing/db/*.docx`

## Verwendung in der Web UI

Die beiden `flow.*.json` Dateien koennen direkt in die Web UI importiert werden.
Es muessen davor keine Agents, Resources oder Memory-Systeme registriert werden, weil der Use-Case nur Built-in-Handler nutzt.

Wenn du im visuellen Editor bereits Titel, Positionen und Kurzbeschreibungen pro Node sehen willst, importiere bevorzugt:

- `flow.web_ui.orders_csv.json`
- `flow.web_ui.orders_db.json`

`setup.ps1` ist dennoch sinnvoll, weil es:

- prueft, ob der laufende Backend-Prozess die erforderlichen Handler bereits kennt
- die Ausgabeordner unter `billing/` anlegt

## Typische Anpassungen

- Absenderdaten aendern: Werte im Node `generate_reminder_letters` anpassen
- Andere Quelldatei verwenden: `path` im Node `extract_open_receivables` aendern
- Andere SQLite-Tabelle verwenden: `table` in `flow.orders_db.json` anpassen
- Weitere Ausgabeformate erzeugen: nach `serialize_receivables` weitere `write_file`-Nodes ergaenzen

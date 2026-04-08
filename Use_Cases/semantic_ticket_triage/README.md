# Semantic Ticket Triage

## Ziel

Dieser Use-Case zeigt einen komplexeren, realen Graphen:

1. Zwei Routing-Referenzen werden in Vector Memory gespeichert.
2. Ein eingehender Ticket-Vektor wird semantisch gesucht.
3. Aus dem besten Treffer wird eine Triage-Zusammenfassung erzeugt.
4. Der Graph brancht je nach Treffer nach `support` oder `sales`.
5. Die gewaehlte Route wird ueber Message Queue dispatcht und als Datei nachgewiesen.

Damit dient der Flow als Vorlage fuer semantisches Routing, Work Queues und Assistenz-Systeme.

## Verwendete Handler

- `memory_store`
- `memory_search`
- `template_render`
- `write_file`
- `send_message`

## Voraussetzung

Der Backend-Server muss laufen, zum Beispiel:

```powershell
.\run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

## Schnellstart

```powershell
.\Use_Cases\semantic_ticket_triage\run.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

Optional kann das Setup auch separat ausgefuehrt werden:

```powershell
.\Use_Cases\semantic_ticket_triage\setup.ps1 -ApiBaseUrl http://127.0.0.1:8552
```

## Ablauf im Graphen

- `store_support_reference`: legt einen Support-Referenzfall in Vector Memory ab
- `store_sales_reference`: legt einen Sales-Referenzfall in Vector Memory ab
- `search_ticket`: sucht den aehnlichsten Fall
- `render_triage_summary`: baut eine lesbare Zusammenfassung
- `write_triage_summary`: schreibt die Triage-Datei
- `route_to_support` oder `route_to_sales`: brancht anhand des Suchergebnisses
- `write_support_dispatch` oder `write_sales_dispatch`: schreibt den Branch-Nachweis

`flow.json` verwendet stabile Agentennamen ueber `target_agent_name`.
Wenn `setup.ps1` einmal gelaufen ist und die Agents `support-sink` und `sales-sink` existieren, kann derselbe Flow direkt ueber die Web UI importiert, gespeichert und gestartet werden.

## Erwartete Artefakte

Nach einem erfolgreichen Lauf existiert immer:

- `Use_Cases/semantic_ticket_triage/output/latest-triage-summary.txt`

Zusätzlich existiert genau eine der beiden Branch-Dateien:

- `Use_Cases/semantic_ticket_triage/output/dispatch-support.txt`
- `Use_Cases/semantic_ticket_triage/output/dispatch-sales.txt`

Im Standard-Flow ist die Query auf einen Support-Fall ausgelegt. Deshalb wird standardmaessig der Support-Branch aktiv.

## Branch wechseln

Wenn du stattdessen den Sales-Branch demonstrieren willst, aendere in `flow.json` die Query des Nodes `search_ticket` von:

```json
[0.94, 0.06]
```

auf zum Beispiel:

```json
[0.08, 0.92]
```

## Typische Anpassungen

- Weitere Referenzfaelle in Vector Memory aufnehmen
- `queue://support` und `queue://sales` spaeter durch REST- oder WebSocket-Endpunkte ersetzen
- Zusaetzliche Branches wie `billing`, `security` oder `priority-escalation` ergaenzen

# LLM-Planer und LiteRT

Der Planner erzeugt keine Mock-Graphen. Er nutzt die lokale `lit`-Binary und das Gemma-Modell im `LIT/`-Ordner, extrahiert JSON und normalisiert das Resultat auf das echte `FlowRequest`-Schema.

## Ablauf

1. `LiteRTPlanner._build_prompt()` baut den Prompt aus Benutzerziel und echtem Katalog.
2. `_invoke_model()` ruft `lit.windows_x86_64.exe` mit `gemma-4-E2B-it.litertlm` auf.
3. `_parse_model_output_with_warnings()` extrahiert genau ein JSON-Objekt und repariert haeufige Formfehler aus LLM-Antworten wie Single Quotes, Bare Keys, fehlende Kommata, unvollstaendige Objekte und gemischte JSON/Python-Literale.
4. `_normalize_flow_request()` korrigiert IDs, Defaults, Abhaengigkeiten, Handler-Inputs und ersetzt offensichtliche Platzhalter-Shells im Embedding- und Memory-Pfad durch echte Upstream-Referenzen.
5. `OrchestratorService.generate_flow_with_llm()` laesst den Graphen anschliessend noch durch die Semantic Firewall laufen.

## Modellwechsel beim Serverstart

- `run-backend.ps1` akzeptiert `-LitModel`, `-LitBinary` und `-LitBackend`
- `python -m nova_synesis.cli run-api` akzeptiert `--lit-model`, `--lit-binary` und `--lit-backend`
- wenn bei `--lit-model` oder `-LitModel` nur ein Dateiname uebergeben wird, sucht NOVA-SYNESIS automatisch im Ordner `LIT/`
- `GET /planner/status` zeigt danach das aktiv verwendete Modell und Backend an
- multimodale `.litertlm`-Modelle koennen als Textmodell gestartet werden, Bild-Inputs sind damit aber noch nicht automatisch in Planner oder Web-UI verdrahtet
- wenn LiteRT beim Modellwechsel mit `failed to create engine` oder einem XNNPACK-Cache-Fehler scheitert, quarantaint NOVA-SYNESIS den modellbezogenen Cache automatisch und versucht einen Retry
- wenn auch der Retry scheitert, ist die Modell-/Binary-/Backend-Kombination wahrscheinlich nicht kompatibel
- bei freien Prompts bootstrappt der Planner automatisch `nova-system-agent`, `planner-scratch` und `planner-vector`, falls diese Objekte noch nicht existieren
- freie Web- oder CSV-Workflows koennen auf die Built-ins `news_search`, `topic_split` und `write_csv` zurueckgreifen
- lokale Datei- und Audit-Workflows koennen auf `filesystem_read`, `local_llm_text` und `filesystem_write` geplant werden
- wenn das Modell im Vector-Pfad nur Platzhalter wie `{"embedding":"..."}` liefert, repariert der Planner neue Flows auf echte `generate_embedding`-Result-Referenzen
- bereits gespeicherte Alt-Flows mit demselben Platzhalterfehler werden zur Laufzeit im `memory_store`-Handler auf das echte Upstream-Embedding umgebogen
- wenn das Modell bei `topic_split`, `write_csv`, `filesystem_read`, `filesystem_write` oder `local_llm_text` Aliasfelder, falsche Referenzformen oder Agentennamen als Handler liefert, normalisiert der Planner diese Inputs und Handler-Namen auf die echten Built-ins
- wenn ein Audit- oder Review-Node bereits einen Prompt besitzt, sorgt die Planner-Normalisierung trotzdem dafuer, dass die Upstream-Daten als `data` in den Node wandern
- der lokale Text-Handler erzwingt im Zusammenspiel mit dem Planner eine finale Antwort und verhindert Folgefragen wie `Please provide ...`, sobald ein Prompt und echte Eingangsdaten vorliegen
- neue Graphen koennen spaeter als eigene Flow-Version gespeichert werden; der Planner selbst schreibt aber nie direkt an einer bestehenden Version vorbei

## Wichtige Sicherheitsgrenzen

- Ressourcen und Memories mit `sensitive = true` oder `planner_visible = false` werden aus dem Planner-Katalog herausgefiltert.
- untrusted Handler werden komplett aus dem Planner-Katalog entfernt.
- `send_message` darf nur auf registrierte Kommunikationsziele zeigen. Wenn keins existiert, wird der Node aus dem Planner-Graphen entfernt und als Warnung gemeldet.
- Die Antwort enthaelt `security_report`, damit UI und Betreiber sehen, ob der generierte Graph policy-konform war.
- Planner-Warnungen bedeuten: der Graph wurde normalisiert, aber nicht stillschweigend erweitert.
- `requires_manual_approval` wird standardmaessig auf `false` normalisiert und nur uebernommen, wenn es explizit im Graphen gesetzt ist.
- freie Prompts duerfen weiterhin keine beliebigen neuen Fachhandler oder unbekannte Infrastruktur herbeifantasieren; sie bleiben an den echten Katalog gebunden

## Betriebsregel fuer echte Planner-Beispiele

- `AI Plan` kann nur mit dem arbeiten, was im laufenden Backend registriert ist.
- Deshalb muessen `Use_Cases/**/setup.ps1` oder andere Registrierungswege zuerst ausgefuehrt werden.
- Der Ordner `Use_Cases/LLM_Planer` enthaelt nur verifizierte Prompts fuer den jeweils registrierten Live-Katalog.
- Wenn Agenten, Ressourcen oder Memories nicht registriert sind, kann der Planner sie nicht sicher verwenden und entfernt betroffene Nodes oder die Semantic Firewall blockiert den Flow.

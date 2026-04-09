# LLM-Planer und LiteRT

Der Planner erzeugt keine Mock-Graphen. Er nutzt die lokale `lit`-Binary und das Gemma-Modell im `LIT/`-Ordner, extrahiert JSON und normalisiert das Resultat auf das echte `FlowRequest`-Schema.

## Ablauf

1. `LiteRTPlanner._build_prompt()` baut den Prompt aus Benutzerziel und echtem Katalog.
2. `_invoke_model()` ruft `lit.windows_x86_64.exe` mit `gemma-4-E2B-it.litertlm` auf.
3. `_parse_model_output_with_warnings()` extrahiert genau ein JSON-Objekt und repariert haeufige Formfehler aus LLM-Antworten.
4. `_normalize_flow_request()` korrigiert IDs, Defaults, Abhaengigkeiten und Handler-Inputs.
5. `OrchestratorService.generate_flow_with_llm()` laesst den Graphen anschliessend noch durch die Semantic Firewall laufen.

## Wichtige Sicherheitsgrenzen

- Ressourcen und Memories mit `sensitive = true` oder `planner_visible = false` werden aus dem Planner-Katalog herausgefiltert.
- untrusted Handler werden komplett aus dem Planner-Katalog entfernt.
- `send_message` darf nur auf registrierte Kommunikationsziele zeigen. Wenn keins existiert, wird der Node aus dem Planner-Graphen entfernt und als Warnung gemeldet.
- Die Antwort enthaelt `security_report`, damit UI und Betreiber sehen, ob der generierte Graph policy-konform war.
- Planner-Warnungen bedeuten: der Graph wurde normalisiert, aber nicht stillschweigend erweitert.
- `requires_manual_approval` wird standardmaessig auf `false` normalisiert und nur uebernommen, wenn es explizit im Graphen gesetzt ist.

## Betriebsregel fuer echte Planner-Beispiele

- `AI Plan` kann nur mit dem arbeiten, was im laufenden Backend registriert ist.
- Deshalb muessen `Use_Cases/**/setup.ps1` oder andere Registrierungswege zuerst ausgefuehrt werden.
- Der Ordner `Use_Cases/LLM_Planer` enthaelt nur verifizierte Prompts fuer den jeweils registrierten Live-Katalog.
- Wenn Agenten, Ressourcen oder Memories nicht registriert sind, kann der Planner sie nicht sicher verwenden und entfernt betroffene Nodes oder die Semantic Firewall blockiert den Flow.

# LIT Runtime

Server nutzt standardmaessig LiteRT-LM aus diesem Ordner.

Offizielle Herkunft der `lit`-Binary:
- `https://github.com/google-ai-edge/LiteRT-LM`

Erwartete Inhalte:
- Windows: `lit.windows_x86_64.exe`
- Linux/macOS: eine passende native `lit`-Binary
- ein lokales `.litertlm`-Modell, z. B. `gemma-3n-E4B-it-int4.litertlm`

## Modell beim Serverstart wechseln

Der Backend-Start kann das zu verwendende Modell direkt ueberschreiben.

Beispiele:

```powershell
.\run-backend.ps1 -BindHost 127.0.0.1 -Port 8552 -LitModel gemma-4-E2B-it.litertlm
.\run-backend.ps1 -BindHost 127.0.0.1 -Port 8552 -LitModel model_multimodal.litertlm
python -m nova_synesis.cli run-api --host 127.0.0.1 --port 8552 --lit-model model_multimodal.litertlm
```

Regeln:

- ein nackter Dateiname wird automatisch unter `LIT/` aufgeloest
- ein relativer Pfad wird relativ zum Arbeitsverzeichnis aufgeloest
- ein absoluter Pfad wird direkt verwendet
- `GET /planner/status` zeigt danach das aktiv verwendete Modell an
- wenn LiteRT beim Modellwechsel mit `failed to create engine` oder einem XNNPACK-Cache-Fehler scheitert, quarantaint NOVA-SYNESIS automatisch `<modell>.xnnpack_cache` und versucht genau einen Retry

Wichtig:

- NOVA-SYNESIS verwendet im Planner und in der Briefvorschau aktuell nur Textprompts
- ein multimodales Modell kann deshalb als Textmodell gestartet werden, Bild-Inputs sind damit aber noch nicht automatisch in der UI oder API verdrahtet
- wenn auch nach dem automatischen Retry weiter `failed to create engine` erscheint, pruefe die Kompatibilitaet von Modell, `lit`-Binary und Backend-Kombination

Externer Downloadpfad fuer das empfohlene Modell:
- `https://huggingface.co/google/gemma-3n-E4B-it-litert-lm/tree/main`

Hinweis:
- das Hugging-Face-Repository ist gated
- vor dem Download muessen Anmeldung und Gemma-Lizenzfreigabe erfolgt sein

Die Release-Pakete enthalten diesen Ordner absichtlich leer, damit keine mehrgigabytegrossen Modelle oder maschinenspezifischen Binaries in jedem ZIP mitgeliefert werden.

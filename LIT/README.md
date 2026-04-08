# LIT Runtime

Server nutzt standardmaessig LiteRT-LM aus diesem Ordner.

Offizielle Herkunft der `lit`-Binary:
- `https://github.com/google-ai-edge/LiteRT-LM`

Erwartete Inhalte:
- Windows: `lit.windows_x86_64.exe`
- Linux/macOS: eine passende native `lit`-Binary
- ein lokales `.litertlm`-Modell, z. B. `gemma-3n-E4B-it-int4.litertlm`

Externer Downloadpfad fuer das empfohlene Modell:
- `https://huggingface.co/google/gemma-3n-E4B-it-litert-lm/tree/main`

Hinweis:
- das Hugging-Face-Repository ist gated
- vor dem Download muessen Anmeldung und Gemma-Lizenzfreigabe erfolgt sein

Die Release-Pakete enthalten diesen Ordner absichtlich leer, damit keine mehrgigabytegrossen Modelle oder maschinenspezifischen Binaries in jedem ZIP mitgeliefert werden.

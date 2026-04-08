# LLM-Planer und LiteRT

Der Planner erzeugt keine Mock-Graphen. Er nutzt die lokale `lit`-Binary und das Gemma-Modell im `LIT/`-Ordner, extrahiert JSON und validiert das Resultat gegen den echten Backend-Katalog.

Wenn du Planner-Qualitaet verbesserst, arbeite primär in `src/nova_synesis/planning/lit_planner.py`.

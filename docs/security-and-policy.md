# Security und Policy

NOVA-SYNESIS sichert nicht nur Code, sondern die Absicht eines Graphen. Diese Aufgabe uebernimmt die Semantic Firewall in `src/nova_synesis/security/policy.py`.

## Wann die Policy greift

- bei Agent-Registrierung
- bei `POST /flows/validate`
- bei `POST /flows`
- vor `POST /flows/{flow_id}/run`
- nach einer Planner-Generierung, bevor der Graph an die UI zurueckgeht

## Was geprueft wird

- Graph-Struktur: keine Zyklen, keine Selbstkanten, keine unbekannten Nodes
- Retry-Budget und maximale Graphgroesse
- Expressions und Templates: nur erlaubte Symbole und AST-Knoten
- HTTP-Egress: nur erlaubte Hosts oder Loopback
- Messaging: nur erlaubte Protokolle und kein Endpoint-Override im Payload
- Dateioperationen: kein `allow_outside_workdir`
- Sensitive Memories: kein Abfluss in `http_request` oder externe Nachrichtenziele
- Planner-visible Memories: kein untrusted Ingest ohne explizites Opt-in
- Agent-Registrierung: keine unerlaubten REST/WebSocket-Endpunkte und keine blockierten Capability-Profile

## Bedeutende Felder

- `sensitive = true`
- `planner_visible = false`
- `allow_untrusted_ingest = true`

## Wichtige Settings

- `NS_SECURITY_ENABLED`
- `NS_SECURITY_MAX_NODES`
- `NS_SECURITY_MAX_EDGES`
- `NS_SECURITY_MAX_TOTAL_ATTEMPTS`
- `NS_SECURITY_MAX_EXPRESSION_LENGTH`
- `NS_SECURITY_MAX_EXPRESSION_NODES`
- `NS_SECURITY_HTTP_ALLOWED_HOSTS`
- `NS_SECURITY_SEND_PROTOCOLS`

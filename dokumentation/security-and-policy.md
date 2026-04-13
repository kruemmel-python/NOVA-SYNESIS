# Security und Policy

NOVA-SYNESIS sichert nicht nur Code, sondern die Absicht eines Graphen. Diese Aufgabe uebernimmt die Semantic Firewall in `src/nova_synesis/security/policy.py`.

## Wann die Policy greift

- bei Agent-Registrierung
- bei `POST /flows/validate`
- bei `POST /flows`
- bei `POST /flows/{flow_id}/versions`
- vor `POST /flows/{flow_id}/run`
- nach einer Planner-Generierung, bevor der Graph an die UI zurueckgeht
- bei serverseitigen Approval- und HITL-Resume-Entscheidungen ueber Rollen

## Was geprueft wird

- Graph-Struktur: keine Zyklen, keine Selbstkanten, keine unbekannten Nodes
- Retry-Budget und maximale Graphgroesse
- Handler-Trust: unbekannte, untrusted oder abgelaufene Handler-Zustaende
- Expressions und Templates: nur erlaubte Symbole und AST-Knoten
- HTTP-Egress: nur erlaubte Hosts oder Loopback
- Messaging: nur erlaubte Protokolle und kein Endpoint-Override im Payload
- Dateioperationen: kein `allow_outside_workdir`
- Sensitive Memories: kein Abfluss in `http_request` oder externe Nachrichtenziele
- Planner-visible Memories: kein untrusted Ingest ohne explizites Opt-in
- Agent-Registrierung: keine unerlaubten REST/WebSocket-Endpunkte und keine blockierten Capability-Profile
- `execute_subflow`: `target_flow_id` muss gesetzt sein; fehlende `target_version_id` fuehrt bewusst zu einer Warnung gegen unscharfe Child-Runs

## Digitale Handler-Zertifikate

- `HandlerTrustAuthority` signiert interne Handler-Zertifikate mit HMAC ueber einen kanonischen Payload.
- Der Fingerprint wird aus Handlername, Modul, Qualname und Quellcode abgeleitet.
- Built-in-Handler koennen automatisch signiert werden.
- Custom Handler bleiben ohne Zertifikat sichtbar, aber sie gelten als untrusted.
- `GET /handlers` ist die Betriebsansicht fuer `trusted`, `trust_reason`, `fingerprint` und `certificate`.

## Manuelle Freigabe

- Ein Node kann `requires_manual_approval = true` tragen.
- Die Freigabe liegt in `manual_approval`.
- Im Create- und Validate-Pfad wird das als Warnung behandelt.
- Im Run-Pfad blockiert die Policy den Start, solange keine gueltige Freigabe mit `approved_by` vorliegt.
- Wenn `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS=true` aktiv ist, kann eine explizite Node-Freigabe einen untrusted Handler fuer genau diesen Flow-Node erlauben.

## Rollen und Identity-Header

- wenn `NS_SECURITY_RBAC_ENABLED=true` aktiv ist, wertet die API standardmaessig `X-NOVA-User` und `X-NOVA-Roles` aus
- die Default-Rolle fuer Freigaben ist `approver`, solange der Node keine spezifischere Rolle vorgibt
- dieselbe Rollenpruefung gilt fuer `POST /flows/{flow_id}/nodes/{node_id}/resume`, wenn eine offene HITL-Anforderung ein `required_role` enthaelt
- die UI kann Rollenhints anzeigen, aber die eigentliche Erlaubnis wird nur serverseitig entschieden

## Bedeutende Felder

- `sensitive = true`
- `planner_visible = false`
- `allow_untrusted_ingest = true`
- `requires_manual_approval = true`
- `manual_approval.approved = true`
- `manual_approval.required_role = "approver"`
- `input_request.required_role = "approver"`

## Wichtige Settings

- `NS_HANDLER_CERTIFICATE_SECRET`
- `NS_HANDLER_CERTIFICATE_ISSUER`
- `NS_HANDLER_CERTIFICATE_TTL_HOURS`
- `NS_SECURITY_ENABLED`
- `NS_SECURITY_AUTO_ISSUE_BUILTIN_HANDLER_CERTIFICATES`
- `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS`
- `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS`
- `NS_SECURITY_RBAC_ENABLED`
- `NS_SECURITY_DEFAULT_APPROVER_ROLE`
- `NS_SECURITY_IDENTITY_HEADER_USER`
- `NS_SECURITY_IDENTITY_HEADER_ROLES`
- `NS_SECURITY_MAX_NODES`
- `NS_SECURITY_MAX_EDGES`
- `NS_SECURITY_MAX_TOTAL_ATTEMPTS`
- `NS_SECURITY_MAX_EXPRESSION_LENGTH`
- `NS_SECURITY_MAX_EXPRESSION_NODES`
- `NS_SECURITY_HTTP_ALLOWED_HOSTS`
- `NS_SECURITY_SEND_PROTOCOLS`

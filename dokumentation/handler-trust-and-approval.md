# Handler Trust und Freigaben

Diese Seite beschreibt die zweite Sicherheitslinie nach der Semantic Firewall: vertrauenswuerdige Handler und die explizite manuelle Node-Freigabe.

## 1. Was ein Handler-Zertifikat hier bedeutet

NOVA-SYNESIS nutzt kein externes X.509-PKI, sondern ein internes, signiertes Handler-Zertifikat:

- der Fingerprint wird aus Modul, Qualname und Quellcode des Handlers abgeleitet
- `HandlerTrustAuthority` signiert diesen Fingerprint per HMAC
- das Zertifikat enthaelt `issuer`, `issued_at`, `expires_at`, `fingerprint` und `built_in`
- bei jeder Registrierung wird geprueft, ob Zertifikat und aktueller Handler-Code noch zusammenpassen

## 2. Trust-Lebenszyklus

1. Ein Handler wird registriert.
2. Built-in-Handler erhalten automatisch ein Zertifikat, wenn `NS_SECURITY_AUTO_ISSUE_BUILTIN_HANDLER_CERTIFICATES=true` ist.
3. Custom Handler koennen beim Registrieren ein Zertifikat mitgeben oder spaeter ueber `TaskHandlerRegistry.issue_certificate()` signiert werden.
4. `GET /handlers` liefert den aktuellen Trust-Status inklusive Zertifikat an UI und Betrieb.
5. Der LiteRT-Planer sieht nur trusted Handler im Katalog.

## 3. API und UI

- `GET /handlers`: liefert `handlers` und `details`
- `POST /flows/{flow_id}/nodes/{node_id}/approval`: setzt eine manuelle Freigabe
- `DELETE /flows/{flow_id}/nodes/{node_id}/approval`: hebt sie wieder auf
- `GET /flows/{flow_id}/nodes/{node_id}/input-request`: liest eine offene HITL-Anforderung
- `POST /flows/{flow_id}/nodes/{node_id}/resume`: setzt einen wartenden Node mit Benutzereingaben fort

Im `InspectorPanel` sieht der Betreiber:

- ob der aktuelle Handler trusted oder untrusted ist
- warum der Handler so eingestuft wurde
- Zertifikatsdetails wie Issuer, Fingerprint und Ablaufdatum
- ob fuer den Node eine manuelle Freigabe erforderlich oder bereits gesetzt ist
- ob fuer einen WAITING_FOR_INPUT-Node eine Rolle verlangt wird und welche Eingaben erwartet werden

## 4. Wann die Ausfuehrung blockiert wird

- unbekannter Handler: immer blockiert
- untrusted Handler bei `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS=true`: spaetestens beim Run blockiert
- `requires_manual_approval=true`, aber keine Freigabe gesetzt: beim Run blockiert
- Freigabe ohne `approved_by`: ebenfalls blockiert
- Resume ohne erforderliche Rolle: serverseitig mit `403` blockiert

## 5. Operator-Regeln

- Built-in-Handler bleiben der Normalfall.
- Eigene Handler nur dann trusten, wenn Codequelle und Seiteneffektprofil klar sind.
- Manuelle Freigaben sind flow-spezifisch, nicht global.
- Eine Freigabe ersetzt kein Zertifikat; sie ist eine bewusste Ausnahme fuer einen konkreten Node.
- Freigaben und HITL-Resumes sollten im RBAC-Betrieb immer mit `X-NOVA-User` und `X-NOVA-Roles` nachvollziehbar gemacht werden.

## 6. Relevante Settings

- `NS_HANDLER_CERTIFICATE_SECRET`
- `NS_HANDLER_CERTIFICATE_ISSUER`
- `NS_HANDLER_CERTIFICATE_TTL_HOURS`
- `NS_SECURITY_AUTO_ISSUE_BUILTIN_HANDLER_CERTIFICATES`
- `NS_SECURITY_REQUIRE_TRUSTED_HANDLERS`
- `NS_SECURITY_ALLOW_MANUAL_APPROVAL_FOR_UNTRUSTED_HANDLERS`
- `NS_SECURITY_RBAC_ENABLED`
- `NS_SECURITY_DEFAULT_APPROVER_ROLE`

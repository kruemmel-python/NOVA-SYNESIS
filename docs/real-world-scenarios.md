# Real World Scenarios

Diese Seite enthaelt bewusst nur drei End-to-End-Beispiele. Ziel ist nicht Vollstaendigkeit, sondern sichere Anwendbarkeit mit dem echten Backend und der aktiven Security-Policy.

## Szenario 1: Einfacher Betriebsflow "Platform Health Snapshot"

Referenz: `Use_Cases/platform_health_snapshot/`

### Ziel

Die lokale Plattform pruefen, einen Snapshot speichern und daraus eine Textzusammenfassung schreiben.

### Warum dieser Flow produktionsnah ist

- nutzt nur echte Built-in-Handler
- benoetigt keinen Mock-Service
- zeigt HTTP, Memory, Serialisierung und Dateiablage in einer kleinen, gut kontrollierbaren Kette

### Typischer Ablauf

1. `http_request` gegen einen lokalen oder allowlist-konformen Health-Endpunkt
2. `json_serialize` fuer den Snapshot
3. `write_file` fuer Rohdaten
4. `template_render` fuer die Zusammenfassung
5. `write_file` fuer den lesbaren Report
6. optional `memory_store` fuer den letzten Snapshot-Key

## Szenario 2: Komplexer Flow mit Branching "Semantic Ticket Triage"

Referenz: `Use_Cases/semantic_ticket_triage/`

### Ziel

Tickets semantisch bewerten, Wissen aus Memory laden und je nach Ergebnis an unterschiedliche interne Queue-Agenten dispatchen.

### Warum dieser Flow produktionsnah ist

- kombiniert Vector Memory, Planner-verwertbares Wissen und Messaging
- nutzt Branching ueber Edge-Conditions
- bleibt policy-konform, weil `send_message` auf interne Message Queues begrenzt bleibt

### Typischer Ablauf

1. Ticketdaten laden oder als Input entgegennehmen
2. `memory_search` in einem Vector-Memory
3. `template_render` fuer die Triage-Zusammenfassung
4. Branching auf `dispatch-support` oder `dispatch-sales`
5. `send_message` an registrierte Queue-Agenten

## Szenario 3: Fehlerfall mit Retry und Fallback "API-Replica uebernimmt"

### Ziel

Ein fragiler Infrastrukturzugriff soll auch dann stabil laufen, wenn die bevorzugte Ressource kurzzeitig ausfaellt.

### Beispielstruktur

```json
{
  "nodes": [
    {
      "node_id": "fetch-primary-or-fallback",
      "handler_name": "http_request",
      "input": { "method": "GET", "timeout_s": 8 },
      "required_resource_types": ["API"],
      "retry_policy": {
        "max_retries": 3,
        "backoff_ms": 500,
        "exponential": true,
        "max_backoff_ms": 5000,
        "jitter_ratio": 0.1
      },
      "rollback_strategy": "FALLBACK_RESOURCE",
      "validator_rules": {
        "required_keys": ["status_code", "body"],
        "expression": "result['status_code'] < 500"
      }
    },
    {
      "node_id": "store-result",
      "handler_name": "memory_store",
      "input": {
        "memory_id": "working-memory",
        "key": "resilient-fetch-result",
        "value": "{{ results['fetch-primary-or-fallback']['body'] }}"
      },
      "dependencies": ["fetch-primary-or-fallback"],
      "conditions": { "fetch-primary-or-fallback": "source_result['status_code'] < 400" }
    }
  ],
  "edges": [
    {
      "from_node": "fetch-primary-or-fallback",
      "to_node": "store-result",
      "condition": "source_result['status_code'] < 400"
    }
  ]
}
```

### Sichere Betriebsreihenfolge

1. zuerst `POST /flows/validate`
2. danach speichern
3. Laufzeit ueber `GET /flows/{flow_id}` beobachten
4. bei Auffaelligkeiten pruefen, ob wirklich Retry oder bereits Resource-Fallback greift

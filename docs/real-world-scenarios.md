# Real World Scenarios

Diese Seite enthaelt bewusst nur drei End-to-End-Beispiele. Ziel ist nicht Vollstaendigkeit, sondern sichere Anwendbarkeit.

## Szenario 1: Einfacher Flow "API abrufen und Ergebnis merken"

### Ziel

Remote-Daten laden und in einem vorhandenen Memory-System speichern.

### Voraussetzungen

- mindestens eine API-Ressource ist registriert
- ein Memory-System mit passender `memory_id` existiert

### Ablauf

1. API-Ressource pruefen
2. Daten abrufen
3. Antwort bei Erfolg im Memory sichern

### Beispielstruktur

```json
{
  "nodes": [
    {
      "node_id": "check-api",
      "handler_name": "resource_health_check",
      "input": { "resource_ids": [1] },
      "dependencies": []
    },
    {
      "node_id": "fetch-data",
      "handler_name": "http_request",
      "input": { "method": "GET", "timeout_s": 10 },
      "required_resource_ids": [1],
      "validator_rules": {
        "required_keys": ["status_code", "body"],
        "expression": "result['status_code'] < 400"
      },
      "dependencies": ["check-api"],
      "conditions": { "check-api": "True" }
    },
    {
      "node_id": "store-result",
      "handler_name": "memory_store",
      "input": {
        "memory_id": "working-memory",
        "key": "latest-api-result",
        "value": "{{ results['fetch-data']['body'] }}"
      },
      "dependencies": ["fetch-data"],
      "conditions": { "fetch-data": "source_result['status_code'] < 400" }
    }
  ],
  "edges": [
    { "from_node": "check-api", "to_node": "fetch-data", "condition": "True" },
    { "from_node": "fetch-data", "to_node": "store-result", "condition": "source_result['status_code'] < 400" }
  ]
}
```

### Warum dieses Beispiel wichtig ist

- nutzt nur reale Built-in-Handler
- zeigt Resource-Einsatz, Validierung und Template-Zugriff
- ist klein genug, um die komplette Lebenslinie des Systems zu verstehen

## Szenario 2: Komplexer Flow mit Branching "Erfolgspfad und Fehlerpfad trennen"

### Ziel

Eine API-Antwort soll unterschiedlich weiterverarbeitet werden, je nachdem ob der HTTP-Status erfolgreich ist oder nicht.

### Ablauf

1. Daten abrufen
2. bei Erfolg eine Zusammenfassung schreiben und speichern
3. bei Fehler einen Fehlerbericht rendern und separat persistieren

### Beispielstruktur

```json
{
  "nodes": [
    {
      "node_id": "fetch-data",
      "handler_name": "http_request",
      "input": { "url": "https://example.invalid/data", "method": "GET", "timeout_s": 10 },
      "dependencies": []
    },
    {
      "node_id": "render-success",
      "handler_name": "template_render",
      "input": {
        "template": "Fetch succeeded with status {status}",
        "values": { "status": "{{ results['fetch-data']['status_code'] }}" }
      },
      "dependencies": ["fetch-data"],
      "conditions": { "fetch-data": "source_result['status_code'] < 400" }
    },
    {
      "node_id": "store-success",
      "handler_name": "memory_store",
      "input": {
        "memory_id": "working-memory",
        "key": "last-success-summary",
        "value": "{{ results['render-success']['rendered'] }}"
      },
      "dependencies": ["render-success"],
      "conditions": { "render-success": "True" }
    },
    {
      "node_id": "render-error",
      "handler_name": "template_render",
      "input": {
        "template": "Fetch failed with status {status}",
        "values": { "status": "{{ results['fetch-data']['status_code'] }}" }
      },
      "dependencies": ["fetch-data"],
      "conditions": { "fetch-data": "source_result['status_code'] >= 400" }
    },
    {
      "node_id": "write-error-report",
      "handler_name": "write_file",
      "input": {
        "path": "reports/fetch-error.txt",
        "content": "{{ results['render-error']['rendered'] }}",
        "append": false
      },
      "dependencies": ["render-error"],
      "conditions": { "render-error": "True" }
    }
  ],
  "edges": [
    { "from_node": "fetch-data", "to_node": "render-success", "condition": "source_result['status_code'] < 400" },
    { "from_node": "render-success", "to_node": "store-success", "condition": "True" },
    { "from_node": "fetch-data", "to_node": "render-error", "condition": "source_result['status_code'] >= 400" },
    { "from_node": "render-error", "to_node": "write-error-report", "condition": "True" }
  ]
}
```

### Warum dieses Beispiel wichtig ist

- zeigt echtes Branching statt linearer Demo-Flows
- benutzt Kantenbedingungen korrekt fuer fachliche Entscheidungen
- trennt Erfolgspfad und Fehlerpfad sauber

## Szenario 3: Fehler plus Retry / Fallback "API-Replica uebernimmt bei Ausfall"

### Ziel

Eine Anfrage soll nicht sofort scheitern, wenn die bevorzugte API-Ressource nicht nutzbar ist.

### Voraussetzungen

- mindestens zwei Ressourcen vom Typ `API` sind registriert
- die Node verwendet `rollback_strategy = FALLBACK_RESOURCE`

### Ablauf

1. Daten ueber eine API-Ressource abrufen
2. bei transientem Fehler erneut versuchen
3. wenn noetig auf eine andere API-Ressource gleicher Art wechseln
4. nur bei Erfolg das Ergebnis speichern

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
      },
      "dependencies": []
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
    { "from_node": "fetch-primary-or-fallback", "to_node": "store-result", "condition": "source_result['status_code'] < 400" }
  ]
}
```

### Warum dieses Beispiel wichtig ist

- zeigt den Unterschied zwischen Retry und Fallback
- bildet ein realistisches Produktionsmuster fuer fragile Infrastruktur ab
- ist direkt mit den vorhandenen Built-in-Handlern und Runtime-Regeln vereinbar

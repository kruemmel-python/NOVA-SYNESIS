# Schnellstart

## 1. Backend starten

```powershell
./run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

Wichtige URLs:

- `GET /docs`
- `GET /health`
- `GET /planner/status`
- `POST /flows/validate`

## 2. Frontend starten

`frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8552
```

Dann:

```powershell
cd frontend
npm run dev
```

## 3. Minimaler Arbeitsablauf

1. Handler, Agenten und Ressourcen im Frontend laden.
2. Einen Graphen im Canvas zeichnen oder ueber den Planner erzeugen.
3. Vor dem Speichern `POST /flows/validate` verwenden oder die UI-Validierung ausloesen.
4. Den Flow ueber `POST /flows` speichern.
5. Den Flow ueber `POST /flows/{flow_id}/run` ausfuehren.
6. Laufzeit und Status ueber `GET /flows/{flow_id}` oder `/ws/flows/{flow_id}` beobachten.

## 4. Wichtige Umgebungsvariablen

- `NS_API_HOST`, `NS_API_PORT`: FastAPI-Bindung
- `NS_LIT_BINARY_PATH`, `NS_LIT_MODEL_PATH`, `NS_LIT_TIMEOUT_S`: lokaler Planner
- `NS_SECURITY_ENABLED`: Semantic Firewall global ein- oder ausschalten
- `NS_SECURITY_HTTP_ALLOWED_HOSTS`: erlaubte HTTP-Zielhosts
- `NS_SECURITY_SEND_PROTOCOLS`: erlaubte Kommunikationsprotokolle fuer `send_message`
- `NS_CORS_ORIGINS`: erlaubte Frontend-Urspruenge

## 5. Mentales Modell

- Das Frontend bearbeitet einen gerichteten Graphen aus Nodes und Edges.
- `toFlowRequest()` wandelt den Editorgraphen in das Backend-Schema.
- Das Backend validiert Struktur, Expressions und Sicherheitsregeln.
- Erst danach wird gespeichert oder ausgefuehrt.
- Die Runtime fuehrt nur DAGs aus und meldet Snapshots laufend an UI und Persistenz zurueck.

# Schnellstart

## Backend

```powershell
./run-backend.ps1 -BindHost 127.0.0.1 -Port 8552
```

Wichtige URLs:

- `/docs`
- `/health`
- `/planner/status`

## Frontend

`frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8552
```

Dann:

```powershell
cd frontend
npm run dev
```

## Mentales Modell

- Das Frontend baut einen gerichteten Graphen.
- Das Backend speichert ihn als `FlowRequest`.
- Die Runtime fuehrt Knoten gemaess ihren Abhaengigkeiten aus.
- Live-Snapshots fliessen per WebSocket zur UI zurueck.

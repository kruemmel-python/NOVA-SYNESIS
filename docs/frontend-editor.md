# Frontend-Editor

Die UI besteht aus `App.tsx`, dem Zustand-Store `useFlowStore.ts`, der Zeichenflaeche `FlowCanvas.tsx`, der linken `Sidebar.tsx`, dem `InspectorPanel.tsx` und der `TopBar.tsx`.

Die kritischste Integrationsdatei ist `frontend/src/lib/flowSerialization.ts`. Wenn dort Felder falsch gemappt werden, speichert die UI keinen korrekten Backend-Flow.

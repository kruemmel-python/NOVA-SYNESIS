# `frontend/src/components/common/JsonEditor.tsx`

- Quellpfad: [frontend/src/components/common/JsonEditor.tsx](../../../../../../frontend/src/components/common/JsonEditor.tsx)
- Kategorie: `Frontend`

## Aufgabe der Datei

TypeScript-Modul des Frontends.

## Wann du diese Datei bearbeitest

Wenn Verhalten, API, UI oder Architektur angepasst werden muessen.

## Exporte und oeffentliche Definitionen

- `JsonEditor`: Funktion oder Definition `JsonEditor` dieses Moduls.

## Abhaengigkeiten

- `import { useEffect, useMemo, useState } from "react";`
- `import { prettyJson, safeJsonParse } from "../../lib/json";`

## Aenderungshinweise

- Aendere Vertrage nie isoliert, wenn dieselben Felder in API, UI und Persistenz verwendet werden.
- Pruefe nach Veraenderungen immer die benachbarten Dateien derselben Verantwortungskette.
- Bei Runtime- oder API-Aenderungen die Tests erneut ausfuehren.

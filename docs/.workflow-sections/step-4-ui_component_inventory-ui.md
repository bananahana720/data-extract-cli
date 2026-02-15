# Component Inventory - UI

## Layout and Navigation

- `ui/src/App.tsx`
  - App shell, top navigation, route mounting.
- `ui/src/main.tsx`
  - Root bootstrap and router provider.

## Page Components

- `ui/src/pages/NewRunPage.tsx` (run submission form and upload workflow)
- `ui/src/pages/JobsPage.tsx` (job list, filtering, polling)
- `ui/src/pages/JobDetailPage.tsx` (job insights, artifacts, retries)
- `ui/src/pages/SessionsPage.tsx` (session summaries)
- `ui/src/pages/ConfigPage.tsx` (auth and preset management)

## Reusable UI Patterns

- Card, alert, pill/status, table, timeline patterns defined by class conventions in `ui/src/styles.css`.
- API layer reused across pages via `ui/src/api/client.ts`.

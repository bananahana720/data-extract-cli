# Development Guide - UI

## Prerequisites

- Node.js 20+
- npm

## Setup

1. `cd ui`
2. `npm install`
3. `npm run build`

## Core Commands

- Local dev server: `npm run dev`
- Backend-integrated UI dev (default backend host expected): `npm run dev -- --host`
- Production build: `npm run build`
- Build preview: `npm run preview`
- Unit tests: `npm run test:unit`
- Watch-mode unit tests: `npm run test:unit:watch`
- Critical e2e lifecycle: `npm run e2e:gui`

## UI Architecture Anchors

- App bootstrap/theme: `ui/src/main.tsx`, `ui/src/theme/*`
- Route shell: `ui/src/App.tsx`
- API boundary: `ui/src/api/client.ts`
- Feature workflows: `ui/src/pages/*`
- Reusable UI system: `ui/src/components/*`

## Local Development Flow

1. From repository root, ensure backend dependencies are healthy:
   - `python -m data_extract.api.main --help` or equivalent startup path
2. From `ui/`:
   - `npm install`
   - `npm run dev`
3. Optional API-bound smoke flow:
   - start API endpoint in a second terminal
   - open `http://localhost:5173` and verify run list/job detail rendering
4. Run focused verification:
   - `npm run test:unit`
   - `npm run e2e:gui`
5. Before release:
   - `npm run build`
   - capture any visual or interaction regression notes if UI behavior changes

## Component and routing map

- Operator pages:
  - `NewRun`, `Jobs`, `JobDetail`, `Sessions`, `Config`
- Workflow state and evidence features:
  - `state-management-patterns-ui.md` and `integrity` feature domains
- API types and payload mapping:
  - `ui/src/types.ts`, especially run/session/job status models

## UX validation checklist

- Verify run creation prevents invalid submissions.
- Validate readiness checks (dependencies, config, input constraints) before submit.
- Confirm failure states show actionable remediation guidance.
- Confirm session/job completion states display evidence artifacts and downloadable outputs.

## Build and quality quality

- For UI-only edits, run:
  - `npm run test:unit`
  - `npm run test:unit:watch` for iterative changes
- For flow-level edits, run:
  - `npm run e2e:gui`
  - `npm run e2e:gui:slo` for longer scenarios
- For final validation:
  - `npm run build`

## Browser/runtime notes

- Keep API client path configurable for test and production targets.
- Preserve accessibility labels and stable selectors used by Playwright tests.
- Ensure long list rendering and table views preserve deterministic row keys.

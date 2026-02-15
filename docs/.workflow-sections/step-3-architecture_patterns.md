# Architecture Patterns

## Per-Part Patterns

- `backend`: **Modular Pipeline + Service/API Layer**
  - Extract/Normalize/Chunk/Semantic/Output stages live in dedicated modules under `src/data_extract/`.
  - API adapters (`src/data_extract/api/`) and CLI adapters (`src/data_extract/cli/`) expose shared core logic.

- `ui`: **React SPA with API Client Layer**
  - Route-driven client app in `ui/src/App.tsx` and `ui/src/pages/`.
  - API boundary centralized in `ui/src/api/client.ts` and proxied in dev by `ui/vite.config.ts`.

## Overall System Pattern

- **Client-Server, API-Driven Orchestration**
  - `ui/` operates as a browser client for job/session/config workflows.
  - `backend` exposes REST endpoints and execution/state services.
  - Integration is HTTP/JSON across `/api/*` routes.

## Constraints and Risks

- Long-running jobs can create UI staleness without event streaming.
- Shared contracts between UI client and API endpoints need explicit version discipline.
- Pipeline changes must preserve test coverage and stage interfaces.

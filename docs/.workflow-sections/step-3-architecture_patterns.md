# Architecture Patterns

## Per-Part Patterns

- `backend`: **Modular Pipeline + Service/API Adapter Pattern**
  - Stage modules (`extract`, `normalize`, `chunk`, `semantic`, `output`) isolate processing responsibilities.
  - Service layer (`src/data_extract/services/`) coordinates runtime, persistence, retry, and workflow orchestration.
  - API (`src/data_extract/api/`) and CLI (`src/data_extract/cli/`) expose shared domain capabilities.

- `ui`: **Guided Workflow SPA + Shared Pattern Layer**
  - Route shell with focused page workflows (`NewRunPage`, `JobsPage`, `JobDetailPage`, `SessionsPage`, `ConfigPage`).
  - Theme/token foundation (`ui/src/theme/*`, `ui/src/components/foundation/*`) standardizes status semantics and layout.
  - Task-specific component domains (`run-builder`, `integrity`, `control-tower`, `evidence`, `patterns`) reduce page complexity.

## Overall System Pattern

- **Client-Server, API-Driven Orchestration**
  - UI handles user decision flows and stateful guidance.
  - Backend exposes operational contracts over `/api/v1/*`.
  - Shared behavior depends on stable typed contracts in `ui/src/types.ts` and backend response models.

## Key Constraints and Risks

- Long-running jobs still rely primarily on polling; stale UI state must be surfaced explicitly.
- Contract changes between backend and UI must stay synchronized.
- Integrity and readiness signals must stay explicit to avoid silent failure modes.

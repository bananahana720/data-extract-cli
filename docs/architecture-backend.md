# Architecture - Backend

## Executive Summary

The backend is a Python service that combines a Typer CLI and FastAPI API surface over a modular processing pipeline (extract -> normalize -> chunk -> semantic -> output), with persistent job/session state and runtime queue orchestration.

## Technology Stack

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy + Alembic (SQLite default path)
- Typer CLI + Rich
- spaCy/scikit-learn/text tooling

## Architecture Pattern

- Modular pipeline core with adapter surfaces:
  - CLI adapter: `src/data_extract/cli/`
  - API adapter: `src/data_extract/api/`
  - Shared services/core pipeline: `src/data_extract/services/` and stage modules

## Data Architecture

- ORM models in `src/data_extract/api/models.py`
- Migration history in `alembic/versions/`
- Runtime schema checks in `src/data_extract/api/database.py`
- Major tables: jobs, job_files, job_events, sessions, retry_runs, app_settings

## API Design

- REST routers under `src/data_extract/api/routers/`:
  - auth, config, health, jobs, sessions
- Base prefix: `/api/v1`
- Contract coverage documented in `docs/api-contracts-backend.md`

## Component Overview

- `src/data_extract/api/`: HTTP layer and runtime hooks
- `src/data_extract/services/`: orchestration and business logic
- `src/data_extract/{extract,normalize,chunk,semantic,output}/`: pipeline stages
- `src/data_extract/runtime/`: queue worker runtime

## Source Tree

See `docs/source-tree-analysis.md` for annotated structure.

## Development Workflow

See `docs/development-guide-backend.md`.

## Deployment Architecture

- Backend can serve UI static assets from `ui/dist`.
- CI/CD checks defined in `.github/workflows/*.yml`.
- See `docs/deployment-guide.md`.

## Testing Strategy

- Unit/integration/performance/UAT suites under `tests/`
- API-focused tests in `tests/unit/data_extract/api/`
- Lint/type/test gates in CI and quality scripts

# Architecture - Backend

## Executive Summary

The backend is a Python service that combines FastAPI and Typer over a modular extraction pipeline. It manages queueing, retries, artifacts, and persistence for run/session lifecycle tracking.

## Technology Stack

- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy + Alembic
- Typer + Rich
- spaCy and scikit-learn for semantic processing

## Architecture Pattern

- **Modular pipeline core** (`extract -> normalize -> chunk -> semantic -> output`)
- **Adapter surfaces**
  - API adapter: `src/data_extract/api/`
  - CLI adapter: `src/data_extract/cli/`
- **Service orchestration layer**
  - `src/data_extract/services/`

## Data Architecture

- ORM models in `src/data_extract/api/models.py`
- Migration history in `alembic/versions/`
- Core entities: jobs, job_files, job_events, sessions, retry_runs, app_settings

## API Design

- REST routers in `src/data_extract/api/routers/`
  - auth, jobs, sessions, config, health
- Base prefix: `/api/v1`
- Contract details: `docs/api-contracts-backend.md`

## Component Overview

- Runtime queue and readiness signals: `src/data_extract/api/state.py`, `src/data_extract/runtime/queue.py`
- Persistence and lock-safe DB operations: `src/data_extract/api/database.py`
- Service orchestration for status/retry/session projections: `src/data_extract/services/*`

## Source Tree and Dev Flow

- Structure reference: `docs/source-tree-analysis.md`
- Developer setup: `docs/development-guide-backend.md`

## Deployment and Operations

- FastAPI can serve built UI assets in integrated deployments.
- CI/CD checks and quality gates: `docs/deployment-guide.md`

## Testing Strategy

- Python test scopes under `tests/`
- API/service-focused tests under `tests/unit/data_extract/`
- Quality/lint/type checks enforced by scripts and CI

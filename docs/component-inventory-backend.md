# Component Inventory - Backend

## API Layer

- `src/data_extract/api/main.py` - FastAPI app setup, middleware, static asset serving
- `src/data_extract/api/routers/auth.py` - API key/session auth contract
- `src/data_extract/api/routers/jobs.py` - job intake/detail/retry/artifact endpoints
- `src/data_extract/api/routers/sessions.py` - session list/detail endpoints
- `src/data_extract/api/routers/config.py` - effective config and preset operations
- `src/data_extract/api/routers/health.py` - readiness and runtime signal endpoint

## Service and Runtime Layer

- `src/data_extract/services/job_service.py`
- `src/data_extract/services/session_service.py`
- `src/data_extract/services/retry_service.py`
- `src/data_extract/services/status_service.py`
- `src/data_extract/runtime/queue.py`

## Pipeline Stage Modules

- `src/data_extract/extract/*`
- `src/data_extract/normalize/*`
- `src/data_extract/chunk/*`
- `src/data_extract/semantic/*`
- `src/data_extract/output/*`

## Persistence Components

- ORM models: `src/data_extract/api/models.py`
- DB + retry helper: `src/data_extract/api/database.py`
- Migrations: `alembic/versions/*`

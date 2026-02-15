# API Contracts - Backend

Base path: `/api/v1`

## Auth

- `POST /auth/session`
  - Purpose: create API-key-backed session
  - Handler: `src/data_extract/api/routers/auth.py`
- `GET /auth/session`
  - Purpose: fetch session status
  - Handler: `src/data_extract/api/routers/auth.py`
- `DELETE /auth/session`
  - Purpose: revoke current session
  - Handler: `src/data_extract/api/routers/auth.py`

## Jobs

- `POST /jobs/process`
  - Purpose: start extraction job (path or upload)
  - Handler: `src/data_extract/api/routers/jobs.py`
- `GET /jobs`
  - Purpose: list jobs with filters and pagination
  - Handler: `src/data_extract/api/routers/jobs.py`
- `GET /jobs/{job_id}`
  - Purpose: job detail and status
  - Handler: `src/data_extract/api/routers/jobs.py`
- `POST /jobs/{job_id}/retry-failures`
  - Purpose: retry failed file units
  - Handler: `src/data_extract/api/routers/jobs.py`
- `GET /jobs/{job_id}/artifacts`
  - Purpose: list artifact entries for job
  - Handler: `src/data_extract/api/routers/jobs.py`
- `DELETE /jobs/{job_id}/artifacts`
  - Purpose: clean artifacts for job
  - Handler: `src/data_extract/api/routers/jobs.py`
- `GET /jobs/{job_id}/artifacts/{artifact_path}`
  - Purpose: resolve/download artifact
  - Handler: `src/data_extract/api/routers/jobs.py`

## Sessions

- `GET /sessions`
  - Purpose: list processing sessions
  - Handler: `src/data_extract/api/routers/sessions.py`
- `GET /sessions/{session_id}`
  - Purpose: session detail
  - Handler: `src/data_extract/api/routers/sessions.py`

## Config

- `GET /config/effective`
- `GET /config/current-preset`
- `GET /config/presets`
- `GET /config/presets/{name}/preview`
- `POST /config/presets/{name}/apply`
- Handler: `src/data_extract/api/routers/config.py`

## Health

- `GET /health`
  - Purpose: service readiness and runtime counters
  - Handler: `src/data_extract/api/routers/health.py`

## Security Notes

- API key/session middleware enforced in `src/data_extract/api/main.py`.
- Session TTL and cookie policy in `src/data_extract/api/routers/auth.py`.

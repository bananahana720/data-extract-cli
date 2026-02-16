# API Contracts - Backend

Base path: `/api/v1`

## Auth (`src/data_extract/api/routers/auth.py`)

- `POST /auth/session`
  - Request: `{ api_key }`
  - Response: `SessionStatusResponse`
  - Purpose: create signed cookie session
- `GET /auth/session`
  - Response: `SessionStatusResponse`
  - Purpose: current auth/session status
- `DELETE /auth/session`
  - Response: `SessionStatusResponse`
  - Purpose: clear session cookie

## Jobs (`src/data_extract/api/routers/jobs.py`)

- `POST /jobs/process`
  - Request: `ProcessJobRequest` JSON or multipart upload form
  - Response: `EnqueueJobResponse`
  - Purpose: queue new processing job
- `GET /jobs`
  - Query: `limit`, `offset`
  - Response: `JobSummary[]`
- `GET /jobs/{job_id}`
  - Query: `file_limit`, `event_limit`
  - Response: job detail with files/events payloads
- `POST /jobs/{job_id}/retry-failures`
  - Response: `EnqueueJobResponse`
  - Purpose: requeue failed file units
- `DELETE /jobs/{job_id}/artifacts`
  - Response: `CleanupResponse`
  - Purpose: delete persisted artifacts and log cleanup event
- `GET /jobs/{job_id}/artifacts`
  - Response: `ArtifactListResponse`
  - Purpose: list artifact metadata for job
- `GET /jobs/{job_id}/artifacts/{artifact_path}`
  - Response: file stream
  - Purpose: download artifact with path traversal guard

## Sessions (`src/data_extract/api/routers/sessions.py`)

- `GET /sessions`
  - Response: `SessionSummary[]`
  - Purpose: list sessions from DB projection with filesystem fallback
- `GET /sessions/{session_id}`
  - Response: detailed session payload
  - Purpose: fetch session details

## Config (`src/data_extract/api/routers/config.py`)

- `GET /config/effective`
- `GET /config/current-preset`
- `GET /config/presets`
- `GET /config/presets/{name}/preview`
- `POST /config/presets/{name}/apply`

## Health (`src/data_extract/api/routers/health.py`)

- `GET /health`
  - Query: `detailed`
  - Purpose: runtime readiness, queue, and security posture summary

## Security Notes

- Session auth uses signed, short-lived cookies (`SESSION_COOKIE_NAME`) and API key validation.
- Router-level operations rely on middleware/auth checks configured in `src/data_extract/api/main.py`.
- Artifact download endpoint validates resolved path to prevent traversal.

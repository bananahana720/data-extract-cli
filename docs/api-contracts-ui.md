# API Contracts - UI Client

Client implementation: `ui/src/api/client.ts`

## Auth Session

- `GET /api/v1/auth/session` -> `getAuthSessionStatus`
- `POST /api/v1/auth/session` -> `loginAuthSession`
- `DELETE /api/v1/auth/session` -> `logoutAuthSession`

## Job Intake and Operations

- `POST /api/v1/jobs/process` -> `createProcessJob`, `createProcessJobWithFiles`
- `GET /api/v1/jobs` -> `listJobs`
- `GET /api/v1/jobs/{job_id}` -> `getJob`
- `POST /api/v1/jobs/{job_id}/retry-failures` -> `retryJobFailures`
- `DELETE /api/v1/jobs/{job_id}/artifacts` -> `cleanupJobArtifacts`
- `GET /api/v1/jobs/{job_id}/artifacts` -> `listJobArtifacts`
- `GET /api/v1/jobs/{job_id}/artifacts/{artifact_path}` -> `getJobArtifactDownloadUrl`

## Session and Config

- `GET /api/v1/sessions` -> `listSessions`
- `GET /api/v1/config/effective` -> `getEffectiveConfig`
- `GET /api/v1/config/current-preset` -> `getCurrentPreset`
- `GET /api/v1/config/presets` -> `listConfigPresets`
- `GET /api/v1/config/presets/{name}/preview` -> `previewConfigPreset`
- `POST /api/v1/config/presets/{name}/apply` -> `applyConfigPreset`

## Client Resilience and Integrity Behavior

- Read requests retry with bounded backoff (`READ_REQUEST_ATTEMPTS=3`).
- Write requests are single-attempt by default (`WRITE_REQUEST_ATTEMPTS=1`).
- Requests enforce timeout (`REQUEST_TIMEOUT_MS=15000`) with `AbortController`.
- Same-origin credentials are used for session-backed auth.
- `Retry-After` and DB lock responses are interpreted for retry timing.

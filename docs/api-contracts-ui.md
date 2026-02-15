# API Contracts - UI Client

Client implementation: `ui/src/api/client.ts`

## Auth Session

- `GET /api/v1/auth/session` -> `getAuthSessionStatus`
- `POST /api/v1/auth/session` -> `loginAuthSession`
- `DELETE /api/v1/auth/session` -> `logoutAuthSession`

## Jobs

- `POST /api/v1/jobs/process` -> `processPath` / `processUpload`
- `GET /api/v1/jobs` -> `listJobs`
- `GET /api/v1/jobs/{job_id}` -> `getJobDetail`
- `POST /api/v1/jobs/{job_id}/retry-failures` -> `retryFailedItems`
- `GET /api/v1/jobs/{job_id}/artifacts` -> `listJobArtifacts`
- `DELETE /api/v1/jobs/{job_id}/artifacts` -> `clearJobArtifacts`
- `GET /api/v1/jobs/{job_id}/artifacts/{artifact_path}` -> `buildArtifactDownloadUrl`

## Sessions and Config

- `GET /api/v1/sessions` -> `listSessions`
- `GET /api/v1/config/effective` -> `getEffectiveConfig`
- `GET /api/v1/config/current-preset` -> `getCurrentPreset`
- `GET /api/v1/config/presets` -> `listConfigPresets`
- `GET /api/v1/config/presets/{name}/preview` -> `previewConfigPreset`
- `POST /api/v1/config/presets/{name}/apply` -> `applyConfigPreset`

## Client Contract Behavior

- Typed responses mapped in `ui/src/types.ts`.
- Request retry and timeout in `apiFetch`/`apiGetWithRetry`.
- Credentials mode set to `same-origin` for session auth flow.

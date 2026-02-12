# UI Runtime Guide

## Overview

The UI runtime is a local-first stack:
- FastAPI backend (`src/data_extract/api`)
- In-process worker queue (`src/data_extract/runtime/queue.py`)
- SQLite metadata store (`~/.data-extract-ui/app.db`)
- React/Vite frontend (`ui/`)

## Start Modes

### Full runtime

```bash
data-extract ui
```

### Startup checks only

```bash
data-extract ui --check
```

If the default app home is not writable in your environment, set:

```bash
export DATA_EXTRACT_UI_HOME="$(pwd)/.ui-home"
data-extract ui --check
```

`scripts/validate_installation.py` now defaults to a temporary runtime home when
`DATA_EXTRACT_UI_HOME` is unset, so validation does not depend on repo-tracked state.
`.ui-home/` is ignored by git for local runtime hygiene.

Checks include:
- Required backend dependencies (`fastapi`, `uvicorn`, `sqlalchemy`)
- Writable app directory
- spaCy model availability warning

## API Contract (v1)

- `POST /api/v1/jobs/process`
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/jobs/{job_id}/retry-failures`
- `DELETE /api/v1/jobs/{job_id}/artifacts`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `GET /api/v1/config/effective`
- `GET /api/v1/config/current-preset`
- `POST /api/v1/config/presets/{name}/apply`
- `GET /api/v1/health`

Preset behavior notes:
- `POST /api/v1/config/presets/{name}/apply` persists `last_preset` in app settings.
- `GET /api/v1/config/current-preset` returns the persisted default preset (`null` when unset).
- `POST /api/v1/jobs/process` applies the persisted default preset only when request `preset` is omitted.
- If request `preset` is provided, that explicit value overrides the persisted default.

Semantic compatibility notes:
- Semantic processing requires `output_format=json` for chunk loading.
- For non-JSON outputs with semantic requested, job results include `semantic.status="skipped"` and `semantic.reason_code="semantic_output_format_incompatible"`.
- UI job detail renders the semantic reason code so skipped semantic outcomes are explainable.

## Job Storage Layout

`~/.data-extract-ui/jobs/<job_id>/`
- `inputs/`: uploaded files
- `outputs/`: processing outputs
- `logs/events.log`: append-only runtime log lines

## Frontend Development

```bash
cd ui
npm install
npm run dev
```

The Vite dev server proxies `/api/*` requests to `http://127.0.0.1:8765`.
New Run UI behavior:
- Explicit source mode (`Local Path` or `Upload Files/Folder`)
- Both source sections visible; selected mode determines submitted payload
- Inline validation for required source and minimum chunk size (`>= 32`)
- Submission summary card (source, format, chunk size, discovery/incremental flags)
- Upload list controls include per-file remove and clear-all actions

Job Detail UI behavior:
- Action-first summary with next-action guidance
- Progress bar + runtime metadata (created/started/finished/elapsed)
- Lifecycle timeline sourced from job events
- Structured failure diagnostics and clipboard status feedback
- Retry/Cleanup actions stay disabled while job is queued/running

Jobs UI behavior:
- Live status summary cards (`Total`, `Running`, `Needs Attention`, `Completed`)
- Search + status filters with empty-state reset actions
- Manual refresh control and last-updated indicator

Build for backend serving:

```bash
npm run build
```

Then start backend:

```bash
data-extract ui --no-open
```

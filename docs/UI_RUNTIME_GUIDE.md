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
- `POST /api/v1/config/presets/{name}/apply`
- `GET /api/v1/health`

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

Build for backend serving:

```bash
npm run build
```

Then start backend:

```bash
data-extract ui --no-open
```

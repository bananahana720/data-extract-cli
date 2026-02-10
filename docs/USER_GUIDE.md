# User Guide

## What This Tool Does

`data-extract` processes business documents into structured outputs for downstream analytics and retrieval systems.

Pipeline stages:
1. Extract
2. Normalize
3. Chunk
4. Optional semantic stage
5. Output

## Core Commands

### Process

```bash
data-extract process <input_path> [--output <dir>] [--format json|csv|txt]
```

Important flags:
- `--recursive`: recurse into subdirectories
- `--incremental`: process only new/modified files
- `--force`: reprocess all files even in incremental mode
- `--resume`: resume an incomplete session
- `--resume-session <id>`: resume a specific session
- `--chunk-size <n>`: chunk size control
- `--preset <name>`: apply a configuration preset

### Extract

```bash
data-extract extract <input_path> [--output <dir>] [--recursive]
```

Runs a lightweight extraction-focused path and writes JSON outputs.

### Retry

```bash
data-extract retry --last
data-extract retry --session <session_id>
data-extract retry --file <path>
```

Retries failed files from prior session state.

### Status

```bash
data-extract status [input_path] [--output <dir>] [--json] [--cleanup]
```

Shows source/output sync state, change counts, and orphaned outputs.

### UI

```bash
data-extract ui [--host 127.0.0.1] [--port 8765] [--no-open] [--reload]
```

Starts the local FastAPI backend and serves the React UI.

## UI Workflow

1. Open `data-extract ui`
2. Create a run from:
   - Drag/drop or file/folder upload
   - Or a local input path
3. Track job progress on `/jobs`
4. Inspect job details on `/jobs/:job_id`
5. Retry failed files with one click
6. Use `Cleanup Artifacts` on a job when you want to remove persisted job files
7. Review sessions on `/sessions`

## Data Locations

UI runtime data:
- SQLite DB: `~/.data-extract-ui/app.db`
- Job artifacts: `~/.data-extract-ui/jobs/<job_id>/`
  - `inputs/`
  - `outputs/`
  - `logs/`

CLI session state:
- `<work_dir>/.data-extract-session/`

## Migration Notes (CLI-only to CLI+UI)

- Existing CLI commands remain available.
- New command: `data-extract ui`.
- API/UI jobs are persisted in `~/.data-extract-ui`.
- Retry now resolves failed sessions from active and archived session state.

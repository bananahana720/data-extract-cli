# Data Models - Backend

Primary ORM models: `src/data_extract/api/models.py`
Migration history: `alembic/versions/*.py`

## Core Tables

- `jobs`
  - Primary execution record and lifecycle state
  - Key fields: status, request/dispatch/result payloads, idempotency hash, dispatch sync fields, artifact sync fields, session linkage, timestamps
- `job_files`
  - Per-file processing outcomes
  - Key fields: source/output path, status, chunk_count, retry_count, normalized path, error type/message
- `job_events`
  - Append-only event timeline
  - Key fields: event_type, message, payload, event_time
- `sessions`
  - Session projection for UI queries
  - Key fields: source_directory, status, total/processed/failed counts, archive and reconciliation fields
- `retry_runs`
  - Retry operation audit history
  - Key fields: job_id, source_session_id, status, requested/completed timestamps
- `app_settings`
  - Key-value runtime settings (for example `last_preset`)

## Relationships and Constraints

- `jobs` -> `job_files` (one-to-many)
- `jobs` -> `job_events` (one-to-many)
- `job_files` unique constraint on (`job_id`, `normalized_source_path`)
- Composite/operational indexes for idempotency, dispatch scheduling, artifact sync, and event timeline scans

## Schema Evolution Highlights

- `20260210_0001_create_ui_tables.py`
- `20260210_0002_refactor_persistence_unification.py`
- `20260214_0003_schema_persistence_hardening.py`

# Data Models - Backend

Primary ORM model definitions: `src/data_extract/api/models.py`
Migrations: `alembic/versions/*.py`

## Tables

- `jobs`
  - Key fields: `id`, `status`, `requested_at`, `started_at`, `finished_at`, `options_json`, `session_id`, `root_path`
  - Role: execution lifecycle and run metadata

- `job_files`
  - Key fields: `id`, `job_id`, `path`, `status`, `error`, `record_count`, `artifact_relpath`, `checksum`
  - Role: per-file processing outcomes

- `job_events`
  - Key fields: `id`, `job_id`, `ts`, `level`, `message`, `payload_json`
  - Role: timeline/event log for jobs

- `sessions`
  - Key fields: `id`, `started_at`, `completed_at`, `status`, `processed_file_count`, `failed_file_count`
  - Role: aggregated batch/session summaries

- `retry_runs`
  - Key fields: `id`, `job_id`, `created_at`, `summary_json`
  - Role: tracks retry attempts and outcomes

- `app_settings`
  - Key fields: `key`, `value_json`, `updated_at`
  - Role: persisted UI/config settings and preset state

## Relationships and Indexing

- `jobs` -> `job_files` (one-to-many)
- `jobs` -> `job_events` (one-to-many)
- Session and dispatch/idempotency indexes are hardened in latest migrations.

## Schema Evolution Notes

- `20260210_0001_create_ui_tables.py`: initial UI persistence tables.
- `20260210_0002_refactor_persistence_unification.py`: unified persistence refactor.
- `20260214_0003_schema_persistence_hardening.py`: compatibility/index hardening.

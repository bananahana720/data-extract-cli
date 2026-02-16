# Comprehensive Analysis - Backend

## Configuration and Entry Patterns

- Entrypoints: `src/data_extract/__main__.py`, `src/data_extract/app.py`, `src/data_extract/api/main.py`
- Runtime config is influenced by CLI config, environment variables, and persisted app settings.

## API and Security

- Router partitions: auth, jobs, config, sessions, health.
- Session auth uses API-key validation and signed cookie tokens.
- Health endpoint can expose readiness/security posture when `detailed=true`.

## Persistence and Orchestration

- Core workflow records: jobs, files, events, sessions, retry runs.
- Service layer (`src/data_extract/services/`) handles orchestration, retry, and status projections.
- Runtime queue/state in `src/data_extract/api/state.py` and `src/data_extract/runtime/queue.py`.

## Async and Reliability Signals

- Queue capacity control and retry-after behavior are first-class in job enqueue/retry routes.
- DB lock retry helper guards write-sensitive operations.
- Artifact cleanup/download operations include explicit guardrails and event logging.

## Quality and Operational Guardrails

- CI checks in `.github/workflows/*.yml` enforce tests, security, performance, and UAT.
- Repository security/contribution policy anchored in `AGENTS.md`.

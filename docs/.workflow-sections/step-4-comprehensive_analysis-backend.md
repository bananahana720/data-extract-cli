# Comprehensive Analysis - Backend

## Configuration and Entry Patterns

- Entry points: `src/data_extract/__main__.py`, `src/data_extract/app.py`, `src/data_extract/api/main.py`.
- Runtime/config knobs in `src/data_extract/cli/base.py` and `config.yaml.example`.
- Preset config management in `src/data_extract/cli/config/`.

## Security and Auth

- API-key/session middleware flow implemented in `src/data_extract/api/main.py` and `src/data_extract/api/routers/auth.py`.
- Session signing/TTL controls via environment variables.

## Shared and Service Layers

- Shared service layer under `src/data_extract/services/` for job orchestration, retry logic, session projections, and status rollups.
- Pipeline modules under `src/data_extract/{extract,normalize,chunk,semantic,output}/`.

## Async/Event and Runtime

- `ApiRuntime` + `LocalJobQueue` for dispatch/workers in `src/data_extract/api/state.py` and `src/data_extract/runtime/queue.py`.
- Queue throttling and health counters surfaced through API health endpoints.

## Tests and CI

- API-focused unit tests under `tests/unit/data_extract/api/`.
- CI workflows under `.github/workflows/` enforce lint, type-check, tests, performance, security, and UAT.

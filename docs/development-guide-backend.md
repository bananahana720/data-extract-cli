# Development Guide - Backend

## Prerequisites

- Python 3.11+
- `uv` package manager
- Optional OCR toolchain when OCR workflows are required
- PostgreSQL/SQLite-compatible environment (default uses SQLite for local development)

## Environment Setup

1. `uv venv --seed`
2. `source .venv/bin/activate`
3. `uv pip install -e ".[dev]"`
4. `python -m spacy download en_core_web_md`
5. `data-extract --version` to confirm CLI entrypoint

## Core Commands

- Full tests: `pytest -v`
- Fast local unit pass: `pytest -m "unit and not slow"`
- Quality gate (pre-commit profile): `python scripts/run_quality_gates.py --pre-commit`
- CI-style quality gate: `python scripts/run_quality_gates.py --ci-mode`
- Performance smoke suite: `python scripts/run_performance_suite.py --suites extractors pipeline cli api_runtime --output-json tests/performance/performance_suite_report.json`
- Security scans (pre-commit): `python scripts/scan_security.py --secrets-only --pre-commit`
- Smoke semantic pipeline: `python scripts/smoke_test_semantic.py`

## Backend Entry Points

- CLI: `src/data_extract/__main__.py`, `src/data_extract/app.py`
- API: `src/data_extract/api/main.py`

## Local Development Workflow

1. Activate environment and install dependencies.
2. Validate installation and CLI wiring with `data-extract --help`.
3. Run a targeted test set before code changes:
   - `pytest -m "unit and not slow" -v`
4. Run smoke checks relevant to changed modules:
   - semantic path: `python scripts/smoke_test_semantic.py`
   - core CLI sanity: `data-extract --help` and `data-extract status`
5. Run quality gates for scope:
   - changed files: `python scripts/run_quality_gates.py --changed-only`
6. For broader changes, run full pre-commit gate:
   - `python scripts/run_quality_gates.py --pre-commit`

## Service and pipeline expectations

- Keep configuration loading centralized and deterministic.
- Preserve stage boundaries (`extract`, `normalize`, `chunk`, `semantic`, `output`).
- Maintain explicit job state transitions for status/health observability.
- Use `src/data_extract/services/` for orchestration, not direct DB calls in ad-hoc modules.

## Async and I/O guidance

- Evaluate independent asynchronous operations in parallel where possible.
- Prefer explicit error propagation over swallow-and-continue patterns.
- Add context-rich logging for retryable and terminal failures.

## Data and migration operations

- Apply migrations where schema-related logic is changed:
  - `alembic revision --autogenerate -m "description"`
  - `alembic upgrade head`
- Validate migration targets in a clean DB before merging migration-heavy changes.
- Keep model changes aligned with `src/data_extract/api/models.py` and `src/data_extract/api/schemas.py`.

## Debug and diagnostics

- API startup logs:
  - `python -m data_extract.api.main` (or service runner for your platform)
- Runtime status:
  - `data-extract status`
- Job/session recovery checks:
  - `data-extract session list`
  - `data-extract session show <id>`
  - `data-extract retry --session <id>`

## Common command map

- `data-extract ui --check` validates runtime dependencies used by the integrated UI path.
- `data-extract process` runs the end-to-end backend pipeline.
- `data-extract semantic analyze` and `data-extract semantic deduplicate` execute dedicated semantic operations.
- `data-extract config validate` ensures environment and YAML layers are coherent.

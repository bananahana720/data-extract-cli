# Repository Guidelines

## Project Structure & Module Organization
- `src/data_extract/` contains production Python code: `extract/`, `normalize/`, `chunk/`, `semantic/`, `output/`, `api/`, `cli/`, and `services/`.
- `tests/` is organized by scope: `tests/unit/`, `tests/integration/`, `tests/behavioral/`, `tests/uat/`, and `tests/performance/`.
- `ui/` is the React + Vite frontend with Playwright E2E tests.
- `scripts/` contains automation utilities (quality gates, performance runs, security scans).
- `config/` stores YAML configuration defaults/templates; `alembic/` stores DB migrations.

## Environment Setup
```bash
uv venv --seed && source .venv/bin/activate
uv pip install -e ".[dev]"
python -m spacy download en_core_web_md
```
- If `python` is not on `PATH`, use `.venv/bin/python ...` and `.venv/bin/data-extract ...`.

## Development Workflows

### Backend Daily Loop
1. `pytest -m "unit and not slow" -v`
2. `python scripts/smoke_test_semantic.py`
3. `python scripts/run_quality_gates.py --pre-commit`

### Full CI-Style Validation
1. `python scripts/run_quality_gates.py --ci-mode`
2. `python scripts/scan_security.py --secrets-only --pre-commit`
3. `coverage report --fail-under=60`

### Local Runtime (API + UI via CLI)
1. `data-extract ui --check`
2. `data-extract ui --reload --port 8765`
3. Optional processing smoke test:
   - `data-extract validate ./tests/fixtures -r`
   - `data-extract process "./tests/fixtures/**/*.txt" --format json --output ./output --recursive`

### UI Development Loop
1. `cd ui && npm install`
2. `cd ui && npm run dev`
3. `cd ui && npm run test:unit`
4. `cd ui && npm run build`
5. `cd ui && npm run e2e:gui`
6. `cd ui && npm run e2e:gui:slo`

### Performance Workflow
1. `python -m scripts.create_performance_batch`
2. `python scripts/run_performance_suite.py --suites extractors pipeline cli api_runtime --output-json tests/performance/performance_suite_report.json`
3. `python scripts/validate_performance.py --ci-mode --run-api-runtime --api-base-url http://127.0.0.1:8765`
4. Baseline refresh (updates `tests/performance/baselines.json`):
   - `python scripts/refresh_performance_baselines.py`

### Security Workflow
1. `python scripts/scan_security.py --secrets-only --format markdown --output security-report-secrets.md`
2. `python scripts/scan_security.py --deps-only --format markdown --output security-report-deps.md`
3. `python scripts/scan_security.py --history --max-commits 500 --format markdown --output security-report-history.md`

### Refactor Gate Workflow
1. `python scripts/run_refactor_gates.py`
2. `python scripts/validate_installation.py`

## Command Reference
- Tests:
  - `pytest -v`
  - `pytest -m "unit and not slow"`
  - `pytest -m "not performance and not slow"`
- Quality gates:
  - `python scripts/run_quality_gates.py --pre-commit`
  - `python scripts/run_quality_gates.py --ci-mode`
  - `python scripts/run_quality_gates.py --changed-only`
- API load/performance:
  - `python scripts/run_api_load.py --base-url http://127.0.0.1:8765 --endpoint /api/v1/health --concurrency 8 --duration-seconds 15 --output-json tests/performance/api_runtime_health.json`
  - `python scripts/run_performance_suite.py --suites api_runtime --api-base-url http://127.0.0.1:8765`
- Dependency/testing utilities:
  - `python scripts/audit_dependencies.py --output markdown`
  - `python scripts/generate_tests.py --story <path-to-story.md> --markers auto`
  - `python scripts/generate_docs.py --api --coverage --architecture --format markdown`
- Story/sprint utilities:
  - `python scripts/generate_story_template.py --story-number 4.1 --epic 4 --title "Story title" --with-tests --with-fixtures`
  - `python scripts/manage_sprint_status.py --status --verbose`
- CLI:
  - `data-extract --help`
  - `data-extract process --help`
  - `data-extract batch --help`
  - `data-extract validate --help`
  - `data-extract ui --help`

## Coding Style & Naming Conventions
- Python uses 4-space indentation, type hints, and 100-character max line length.
- Formatting/linting/type-checking are enforced with `black`, `ruff`, and `mypy`.
- Run `pre-commit run --all-files` before opening a PR.
- Use `snake_case` for modules/functions, `PascalCase` for classes, and `test_<behavior>.py` for test files.

## Testing Guidelines
- Test framework: `pytest` with markers (`unit`, `integration`, `performance`, `uat`, etc.).
- Coverage baseline is enforced at 60% overall.
- Mirror source paths when adding tests (example: `src/data_extract/services/job_service.py` -> `tests/unit/data_extract/services/test_job_service.py`).
- For bug fixes, add a regression test with meaningful assertions (not only exit code checks).

## Commit & Pull Request Guidelines
- Follow concise, imperative commit messages. Common patterns in this repo include `fix:`, `feat(ui):`, `ci:`, `docs:`, `test:`, and `chore:`.
- Keep each commit focused on one logical change.
- PRs should include: summary, affected paths, test evidence (commands run), linked issue/story, and screenshots for `ui/` changes.
- Explicitly call out schema, migration, or API contract changes.

## Security & Configuration Tips
- Never commit secrets or `.env` files; keep local config in untracked files.
- Use `config.yaml.example` as the safe template for configuration.
- Run `python scripts/scan_security.py --secrets-only` before release-sensitive changes.

# Repository Guidelines

## Project Structure & Module Organization
- `src/data_extract/` contains production Python code: `extract/`, `normalize/`, `chunk/`, `semantic/`, `output/`, `api/`, `cli/`, and `services/`.
- `tests/` is organized by scope: `tests/unit/`, `tests/integration/`, `tests/behavioral/`, `tests/uat/`, and `tests/performance/`.
- `ui/` is the React + Vite frontend with Playwright E2E tests.
- `scripts/` contains automation utilities (quality gates, performance runs, security scans).
- `config/` stores YAML configuration defaults/templates; `alembic/` stores DB migrations.

## Build, Test, and Development Commands
```bash
uv venv --seed && source .venv/bin/activate
uv pip install -e ".[dev]"
python -m spacy download en_core_web_md
```
- `pytest -v`: run full Python test suite.
- `pytest -m "unit and not slow"`: quick local validation.
- `python scripts/run_quality_gates.py --pre-commit`: Black + Ruff + Mypy checks.
- `python scripts/run_quality_gates.py --ci-mode`: CI-like checks (includes tests/coverage path).
- `cd ui && npm install && npm run dev`: run frontend locally.
- `cd ui && npm run build`: TypeScript build + production bundle.
- `cd ui && npm run e2e:gui`: run UI lifecycle E2E tests.

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

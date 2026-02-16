---
project_name: 'data-extraction-tool-main'
user_name: 'Andrewhana'
date: '2026-02-15T23:11:41Z'
sections_completed:
  ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'quality_rules', 'workflow_rules', 'anti_patterns']
existing_patterns_found: 17
status: 'complete'
rule_count: 25
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- Python 3.11+ with project package `data-extract` (`src` layout, package metadata in `pyproject.toml`).
- Backend: FastAPI 0.111+, Uvicorn 0.30+, SQLAlchemy 2.x, Alembic 1.13+, Pydantic 2.x.
- CLI: Typer 0.9+, Rich 13+, InquirerPy 0.3.x for interactive flows.
- NLP/analysis: spaCy 3.7.2+, lxml 5+, BeautifulSoup 4.12+, scikit-learn 1.3+, textstat 0.7+.
- Document IO: pypdf 3.x, python-docx 0.8+, openpyxl 3.0+, python-pptx 0.6+, pdfplumber 0.10+.
- OCR optional: pytesseract 0.3.10+, pdf2image 1.16+ (feature-gated).
- DB/runtime: SQLite (WAL + lock-retry helper in `src/data_extract/api/database.py`), pathlib-based artifact directories.
- Frontend: React 18.3.1, TypeScript 5.6.3, React Router DOM 6.30.1, Vite 5.4.10.
- Testing/build tooling: `pytest` (with extensive markers), `ruff`, `black`, `mypy`, and Playwright 1.52.0.

## Critical Implementation Rules

### Language-Specific Rules

- Keep Python code typed and explicit. New functions should include type hints and avoid broad `Any` unless validated.
- Use the repository's lock/retry DB wrapper for SQLite writes and reads that can conflict: `with_sqlite_lock_retry` in `src/data_extract/api/database.py`.
- Do not create ad-hoc database sessions outside the established persistence pathway without justification.
- Maintain module-level constants for environment-based knobs (for example queue sizing and retry timing) and parse them defensively with bounded defaults.
- Handle errors with context and persistence side effects: persist terminal events/errors for operational failures in runtime paths.
- Use centralized config objects and models for structured payloads instead of loose dicts.
- For frontend API calls, use typed responses (`ui/src/types.ts`) and narrow request/response contracts before touching pages.
- Keep React/TypeScript strict mode compliance; avoid implicit `any` and prefer `Record<string, unknown>` only at external boundaries.

### Framework-Specific Rules

- Backend routers are grouped by resource (`jobs`, `sessions`, `config`, `auth`, `health`) and mounted from `src/data_extract/api/main.py` under `/api/v1`.
- API auth logic in middleware allows exceptions only for defined session endpoints; do not bypass API key/session guards.
- Runtime startup/shutdown is handled through FastAPI event hooks; avoid introducing startup side effects outside startup/shutdown functions.
- UI follows route-driven SPA composition in `ui/src/App.tsx`; add routes/pages through this shell.
- Keep API transport behavior centralized in `ui/src/api/client.ts`; add API calls there or through equivalent centralized wrapper.
- Use conservative retries for writes and idempotent behavior for GET requests and safe polling paths.

### Testing Rules

- Mirror source structure in tests (`tests/unit`, `tests/integration`, `tests/performance`, `tests/uat`, `tests/behavioral`).
- Use markers from `pytest.ini` (`unit`, `integration`, `performance`, `uat`, `story_*`, `P0`/`P1`/`P2`) and keep strict marker mode clean.
- Name tests with meaningful assertions (not just exit code checks).
- Add regression tests for bug fixes and edge cases that alter behavior.
- Maintain coverage policy with `coverage fail_under=60` and the stricter repo quality expectations.
- For API/runtime changes, include tests for queue states, recovery behavior, and auth/permission flows.

### Code Quality & Style Rules

- Run formatting and linting gates: `black` (line length 100), `ruff`, and `mypy` (`disallow_untyped_defs=true`).
- Keep code size and complexity controlled; split large files/functions when they exceed repo policy thresholds.
- Do not leave placeholder TODOs in production paths.
- Keep error messages actionable for operators and observability.
- Prefer structured logging and event persistence for job lifecycle transitions.

### Development Workflow Rules

- Run quality gates before PRs (pre-commit, ruff, mypy, scoped tests).
- Use conventional commit prefixes (`fix:`, `feat:`, `test:`, `ci:`, `docs:`, `chore:`).
- Never commit `.env` files or secrets. Use local environment files only.
- Run `python scripts/scan_security.py --secrets-only` (or project equivalent) before release-sensitive changes.
- Do not deploy to production without explicit user approval.

### Critical Don't-Miss Rules

- Do not bypass queue internals without validating effects on `ApiRuntime`, backlog, dispatching, and artifact sync paths.
- Do not bypass SQLite lock/retry protections in API and persistence operations.
- Keep OCR and spaCy optionality intact: degraded readiness mode is valid unless strict mode is explicitly required.
- Preserve migration-safe schema evolution with backward-compatible upgrades.
- Avoid changing security policy env flags (`DATA_EXTRACT_API_REMOTE_BIND`, `DATA_EXTRACT_API_REQUIRE_SESSION_SECRET_REMOTE`) without contract/tests updates.
- Do not broaden write retries beyond idempotent scope.
- Keep terminal states/events consistent when adding new job statuses.
- Do not break `/api/v1` contract paths used by the UI.

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code.
- Follow all rules exactly as written.
- Prefer the stricter option when behavior is ambiguous.
- Update this document when project-critical patterns change.

**For Humans:**

- Keep this file focused on rules that reduce implementation ambiguity.
- Refresh when stack versions or core architecture changes.
- Remove rules that no longer provide signal.

Last Updated: 2026-02-15

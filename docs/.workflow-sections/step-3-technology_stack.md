# Technology Stack

## Backend (`backend`, type: `backend`)

| Category | Technology | Version | Justification |
|---|---|---|---|
| Language/Runtime | Python | `>=3.11` | Declared in `pyproject.toml` (`requires-python`). |
| API Framework | FastAPI | `>=0.111.0,<1.0` | Backend API entrypoint in `src/data_extract/api/main.py`. |
| ASGI Server | Uvicorn | `>=0.30.0,<1.0` | Declared in `pyproject.toml` for API serving. |
| CLI Framework | Typer | `>=0.9.0,<1.0` | CLI entrypoint via `data_extract.app:app` and `src/data_extract/cli/`. |
| Database/ORM | SQLAlchemy + Alembic | `>=2.0.0,<3.0` / `>=1.13.0,<2.0` | `alembic/`, `alembic.ini`, and API DB modules under `src/data_extract/api/`. |
| Data/ML Tooling | spaCy, scikit-learn | `>=3.7.2,<4.0` / `>=1.3.0,<2.0` | Semantic pipeline modules under `src/data_extract/semantic/`. |
| Packaging | setuptools | `>=68.0.0` | Build backend in `pyproject.toml`. |
| Test/Quality | pytest, black, ruff, mypy | see `pyproject.toml` | Quality gates and lint/type/test stack. |

## UI (`ui`, type: `web`)

| Category | Technology | Version | Justification |
|---|---|---|---|
| Framework | React + React DOM | `^18.3.1` | Declared in `ui/package.json`; bootstrapped in `ui/src/main.tsx`. |
| Language | TypeScript | `^5.6.3` | `ui/tsconfig*.json` and TS source in `ui/src/`. |
| Router | React Router DOM | `^6.30.1` | `BrowserRouter` usage in `ui/src/main.tsx`. |
| Build Tool | Vite + plugin-react | `5.4.10` / `4.3.2` | `ui/vite.config.ts` with build/dev proxy settings. |
| E2E Testing | Playwright Test | `^1.52.0` | `ui/playwright.config.ts` and `npm run e2e:gui`. |
| State/HTTP | fetch-based API client | app code | Centralized API calls in `ui/src/api/client.ts`. |

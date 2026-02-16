# Technology Stack

## Backend (`backend`, type: `backend`)

| Category | Technology | Version | Justification |
|---|---|---|---|
| Language/Runtime | Python | `>=3.11` | Declared in `pyproject.toml` (`requires-python`). |
| API Framework | FastAPI | `>=0.111.0,<1.0` | API entrypoint and routers in `src/data_extract/api/`. |
| ASGI Server | Uvicorn | `>=0.30.0,<1.0` | Declared backend runtime dependency. |
| CLI Framework | Typer + Rich | `>=0.9.0` / `>=13.0.0` | CLI workflow in `src/data_extract/cli/`. |
| ORM/Migrations | SQLAlchemy + Alembic | `>=2.0.0,<3.0` / `>=1.13.0,<2.0` | ORM models and migration history under `src/data_extract/api/` + `alembic/`. |
| NLP/Semantic | spaCy + scikit-learn | `>=3.7.2,<4.0` / `>=1.3.0,<2.0` | Semantic enrichment and scoring in `src/data_extract/semantic/`. |
| Test/Quality | pytest, black, ruff, mypy | see `pyproject.toml` | Standard quality gates and CI checks. |

## UI (`ui`, type: `web`)

| Category | Technology | Version | Justification |
|---|---|---|---|
| Framework | React + React DOM | `^18.3.1` | SPA runtime in `ui/src/main.tsx`. |
| Language | TypeScript | `^5.6.3` | TS contracts and page/component implementation. |
| Routing | React Router DOM | `^6.30.1` | Route composition in `ui/src/App.tsx`. |
| Design System | MUI + Emotion | `^7.3.8` / `^11.14.x` | Theme/tokenized UI primitives in `ui/src/theme/` and `ui/src/components/foundation/`. |
| Build Tooling | Vite + plugin-react | `5.4.10` / `4.3.2` | Dev/build pipeline in `ui/vite.config.ts`. |
| Unit Testing | Vitest + RTL + jsdom | `^4.0.18` / `^16.3.2` / `^28.1.0` | Component and gating tests under `ui/src/**/*.test.tsx`. |
| E2E Testing | Playwright Test | `^1.52.0` | Lifecycle tests under `ui/e2e/`. |
| API Layer | fetch-based typed client | app code | `ui/src/api/client.ts` with retry/timeout/auth handling. |

# Source Tree Analysis

## Repository Structure

```text
data-extraction-tool-main/
├── src/data_extract/                    # Backend Python package
│   ├── __main__.py                      # Python module entrypoint
│   ├── app.py                           # CLI app export (`data-extract` script)
│   ├── api/                             # FastAPI app, routers, DB/runtime integration
│   │   ├── main.py                      # API entrypoint; serves UI build assets
│   │   ├── routers/                     # auth, jobs, sessions, config, health routes
│   │   ├── database.py                  # DB setup and lock-retry helper integration
│   │   ├── models.py                    # SQLAlchemy ORM models
│   │   └── state.py                     # Runtime queue integration and readiness
│   ├── services/                        # Job/session/retry/status orchestration
│   ├── extract/                         # Content extraction stage
│   ├── normalize/                       # Text/entity normalization stage
│   ├── chunk/                           # Chunking and structure stage
│   ├── semantic/                        # Semantic scoring/reporting stage
│   ├── output/                          # Output formatting and validation
│   ├── runtime/                         # Queue/worker runtime primitives
│   └── cli/                             # Operator CLI command tree and presets
├── ui/                                  # React + Vite frontend
│   ├── src/
│   │   ├── main.tsx                     # ThemeProvider + router bootstrap
│   │   ├── App.tsx                      # Desktop route shell and navigation
│   │   ├── api/client.ts                # Shared API contract layer with retries/timeouts
│   │   ├── theme/                       # Design tokens + MUI theme config
│   │   ├── pages/                       # NewRun, Jobs, JobDetail, Sessions, Config
│   │   ├── components/
│   │   │   ├── foundation/              # Core cards/headers/status/guidance primitives
│   │   │   ├── run-builder/             # Guided run shell + verify-before-run gate
│   │   │   ├── integrity/               # Integrity timeline and remediation mapping
│   │   │   ├── control-tower/           # Signal console and operational summary cards
│   │   │   ├── evidence/                # Evidence handoff/readiness cards
│   │   │   └── patterns/                # Shared loading/feedback/filter/empty patterns
│   │   ├── test/                        # Vitest setup/bootstrap
│   │   └── types.ts                     # UI contract and view-model typing
│   ├── e2e/                             # Playwright lifecycle tests
│   ├── vitest.config.ts                 # Unit test runner config
│   ├── playwright.config.ts             # Browser E2E config
│   └── vite.config.ts                   # Dev proxy/build setup
├── tests/                               # Python tests by scope (unit/integration/uat/perf)
├── scripts/                             # Quality, security, and automation scripts
├── config/                              # YAML defaults/templates and governance policies
├── alembic/                             # Migration history and DB migration config
├── docs/                                # Generated project documentation outputs
└── .github/workflows/                   # CI workflows (test/security/perf/UAT)
```

## Critical Folders and Purpose

- `src/data_extract/api/`: production REST endpoints, auth session policy, readiness reporting.
- `src/data_extract/services/`: business orchestration and persistence-facing logic.
- `src/data_extract/{extract,normalize,chunk,semantic,output}/`: pipeline stages and quality logic.
- `src/data_extract/cli/`: operator commands and preset orchestration.
- `ui/src/pages/`: user workflows for config/input/run/results lifecycle.
- `ui/src/components/`: reusable UX systems (foundation/run-builder/integrity/control-tower/evidence/patterns).
- `ui/src/theme/`: design tokens and MUI theme semantics.
- `ui/e2e/`: lifecycle and regression journeys.

## Entry Points

- Backend CLI: `src/data_extract/__main__.py`, `src/data_extract/app.py`
- Backend API: `src/data_extract/api/main.py`
- Frontend app: `ui/src/main.tsx`

## Integration Paths

- `ui/src/api/client.ts` consumes backend REST contracts under `/api/v1/*`.
- `src/data_extract/api/main.py` serves both API and built `ui/dist` assets.
- Shared run state and artifacts flow across API routers, service layer, and runtime queue.

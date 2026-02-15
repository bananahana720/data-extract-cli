# Source Tree Analysis

## Repository Structure

```text
data-extraction-tool-main/
├── src/data_extract/                 # Backend Python package
│   ├── __main__.py                   # Python module entrypoint
│   ├── app.py                        # CLI app export (`data-extract` script)
│   ├── api/                          # FastAPI app, routers, DB/runtime glue
│   │   ├── main.py                   # API entrypoint; serves UI assets
│   │   ├── routers/                  # auth, jobs, sessions, config, health
│   │   ├── database.py               # DB/session and schema compatibility
│   │   └── models.py                 # SQLAlchemy models
│   ├── cli/                          # Typer command tree and operational commands
│   ├── services/                     # Job/session/retry/pipeline services
│   ├── extract/                      # Extraction stage
│   ├── normalize/                    # Normalization stage
│   ├── chunk/                        # Chunking stage
│   ├── semantic/                     # Semantic analysis stage
│   ├── output/                       # Output formatting stage
│   └── runtime/                      # Worker queue and runtime helpers
├── ui/                               # React/Vite frontend part
│   ├── src/
│   │   ├── main.tsx                  # UI entrypoint
│   │   ├── App.tsx                   # Route shell
│   │   ├── api/client.ts             # API integration layer
│   │   ├── types.ts                  # Shared UI contracts
│   │   └── pages/                    # Feature pages (jobs, runs, config, sessions)
│   ├── vite.config.ts                # Dev server/proxy/build config
│   ├── playwright.config.ts          # E2E config
│   └── e2e/                          # Playwright UI suites
├── tests/                            # Python test suites by scope
├── scripts/                          # Quality/perf/security/utility scripts
├── config/                           # Governance and normalization templates
├── alembic/                          # DB migration history
└── .github/workflows/                # CI pipelines
```

## Critical Folders and Purpose

- `src/data_extract/api/`: production HTTP API surface and runtime lifecycle.
- `src/data_extract/services/`: shared orchestration/business logic.
- `src/data_extract/{extract,normalize,chunk,semantic,output}/`: core processing pipeline.
- `src/data_extract/cli/`: operator-facing command entrypoints.
- `ui/src/`: frontend feature implementation and API client contracts.
- `tests/`: unit/integration/behavioral/performance/UAT verification.
- `scripts/`: automation utilities used in CI and local quality gates.

## Entry Points

- Backend CLI: `src/data_extract/__main__.py`, `src/data_extract/app.py`
- Backend API: `src/data_extract/api/main.py`
- Frontend UI: `ui/src/main.tsx`

## Integration Paths

- `ui/src/api/client.ts` -> backend REST endpoints under `/api/v1/*`.
- `src/data_extract/api/main.py` serves bundled `ui/dist` assets.
- Shared operational flows use backend services and runtime queue.

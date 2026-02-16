# Data Extraction Tool Main

Data Extraction Tool Main is a Python + TypeScript platform for turning mixed-format documents into structured, AI-ready outputs.
It combines:

- A modular backend pipeline (`src/data_extract`) with CLI/API control
- A guided React operator UI (`ui/`)
- A semantic analysis layer for clustering, deduplication, and topic workflows

The repository is designed for both scripting-heavy automation and manual validation workflows.

## What the tool does

- Extract content from supported formats (PDF, DOCX, XLSX/XLS, PPTX, CSV, TXT, images, and more).
- Normalize and structure output into typed JSON/CSV/TXT artifacts.
- Create semantically meaningful chunks for retrieval or downstream analytics.
- Run optional semantic passes (similarity, dedupe, clusters, quality metrics).
- Track jobs and sessions with resumable, retryable execution.
- Expose behavior through both CLI and API (`/api/v1`).

## Repository map

- `src/data_extract/`: Backend production code (pipeline, API, CLI, services)
- `ui/`: Operator web console (Vite + React + TypeScript)
- `docs/`: Product docs, architecture, API contracts, and guides
- `scripts/`: Smoke tests, quality gates, performance, and security scripts
- `tests/`: Unit/integration/uat/performance suites
- `alembic/`: Database migration definitions

## Prerequisites

- Python 3.11+
- `uv`
- Node.js 20+ and `npm`
- Optional: OCR stack (for image/PDF OCR workflows)

## Quick start (backend + CLI)

1. Create and activate a Python environment.

```bash
uv venv --seed
source .venv/bin/activate
```

2. Install backend dependencies.

```bash
uv pip install -e ".[dev]"
python -m spacy download en_core_web_md
```

3. Run CLI smoke checks.

```bash
data-extract --version
data-extract --help
data-extract validate ./tests/fixtures -r
```

4. Process sample content.

```bash
data-extract process ./tests/fixtures --format json --output ./output
```

## Quick start (UI)

1. Install frontend dependencies.

```bash
cd ui
npm install
npm run build
```

2. Start the API/CLI dependency check flow and serve the UI.

```bash
cd /home/andrewhana/projects/codex-fun/data-extraction-tool-main
data-extract ui --check
data-extract ui --reload --port 8765
```

3. Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

## Core command map

- `data-extract process <path>`: run full extraction pipeline
- `data-extract extract <path>`: extract-only mode
- `data-extract validate <path>`: pre-run validation
- `data-extract batch <path>`: batch-oriented workflows and incremental runs
- `data-extract semantic analyze|deduplicate|cluster|topics <path>`
- `data-extract cache status|clear|warm|metrics`
- `data-extract config show|set|init|validate|presets`
- `data-extract session list|show|resume|clean`
- `data-extract retry --last` for failure recovery
- `data-extract ui --check|--reload`: UI bootstrap path

## Typical workflows

### 1) One-shot processing

1. `data-extract validate`
2. `data-extract process`
3. inspect output files in the configured `--output` path

### 2) Large corpus processing

1. Use `--recursive` for directory trees
2. Save presets for repeatable runs
3. Use resume/retry for long-running job continuity

### 3) Semantic analysis workflows

1. Run standard processing with semantic output
2. Analyze artifacts using `semantic analyze`
3. Run dedupe/cluster/topic jobs when needed

## Configuration hierarchy

The effective configuration order is:

1. CLI arguments
2. Environment variables (`DATA_EXTRACT_*`)
3. Session config
4. User config (`~/.config/data-extract/config.yaml` or legacy path)
5. Project config (`.data-extract.yaml`)
6. Defaults

Initialize and validate config:

```bash
data-extract config init
data-extract config validate
```

## Documentation index

- Product docs: `docs/product-documentation.md`
- User guide: `docs/user-guide.md`
- Deployment guide: `docs/deployment-guide.md`
- Contribution guide: `docs/contribution-guide.md`
- Backend/architecture: `docs/architecture-backend.md`
- UI architecture: `docs/architecture-ui.md`
- API contracts:
  - Backend: `docs/api-contracts-backend.md`
  - UI: `docs/api-contracts-ui.md`
- Source structure: `docs/source-tree-analysis.md`

## Development workflows

- Backend quality loop:
  - `pytest -m "unit and not slow" -v`
  - `python scripts/smoke_test_semantic.py`
  - `python scripts/run_quality_gates.py --pre-commit`
- UI quality loop:
  - `cd ui && npm install`
  - `npm run test:unit`
  - `npm run build`
  - `npm run e2e:gui`
- Repository docs/build checks:
  - `python scripts/generate_docs.py`
  - `python scripts/run_quality_gates.py --changed-only`

## Troubleshooting

- `Command not found: data-extract`
  - Recreate the virtualenv and reinstall with `uv pip install -e ".[dev]"`
- `No valid files found`
  - Verify path and recursive flag usage (`--recursive`)
- `OCR not available`
  - Install OCR dependencies and rerun OCR-reliant commands
- `Session missing` / `Retry unavailable`
  - Verify `.data-extract-session` and use `data-extract session list`
- `UI check fails`
  - Run `data-extract ui --check`, then follow listed dependency fixes

## Security and contribution

- Do not commit secrets or `.env` files.
- Use environment variables for credentials.
- Prefer incremental, scoped changes with test evidence in PRs.
- Follow conventions in `AGENTS.md` and `docs/contribution-guide.md`.

## Links

- Repository: [GitHub](https://github.com/bananahana720/data-extraction-tool-main) *(update if this is a fork/private mirror)*
- Issue tracking: use the repository’s configured issue tracker.

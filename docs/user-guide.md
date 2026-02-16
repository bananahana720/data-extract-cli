# Data Extraction Tool User Guide

## What this product does

The Data Extraction Tool converts incoming documents into structured, downstream-ready output.
It supports a modular path:

- **extract**: parse source files and normalize content
- **normalize**: clean text and standardize metadata
- **chunk**: split into semantically meaningful sections
- **semantic**: optional NLP analysis (TF-IDF, similarity, topics, clustering)
- **output**: render JSON, CSV, or TXT artifacts for AI, compliance, or reporting teams

## Quick start

### 1) Prepare your environment

```bash
uv venv --seed
source .venv/bin/activate
uv pip install -e ".[dev]"
python -m spacy download en_core_web_md
data-extract --version
```

### 2) Start with a smoke run

```bash
data-extract validate ./tests/fixtures -r
data-extract process ./tests/fixtures/sample.pdf --format json --output ./output
```

### 3) Start the guided UI (optional)

```bash
data-extract ui --check
data-extract ui --reload --port 8765
```

Then open `http://127.0.0.1:8765`.

## Core CLI workflows

### File processing

- Validate input before processing:
  - `data-extract validate <path> [--recursive]`
- Extract only:
  - `data-extract extract <path> --output ./output --format json`
- Run full pipeline:
  - `data-extract process <path> --output ./output --format json`
- Re-process failed or interrupted work:
  - `data-extract retry --last`
  - `data-extract process <path> --resume`

### Session management

- List recent sessions:
  - `data-extract session list`
- Resume a prior run:
  - `data-extract session resume <session_id>`
- Inspect a session:
  - `data-extract session show <session_id>`
- Clean stale sessions:
  - `data-extract session clean`

### Semantic analysis

- Analyze chunks:
  - `data-extract semantic analyze ./chunks/ -o ./analysis.json`
- Deduplicate near-duplicates:
  - `data-extract semantic deduplicate ./chunks/ --threshold 0.9`
- Cluster and topic models:
  - `data-extract semantic cluster ./chunks/ -k 10 -f json`
  - `data-extract semantic topics ./chunks/ -n 20 -t 15`

### Cache and performance

- Check cache health:
  - `data-extract cache status`
- Preload cache artifacts:
  - `data-extract cache warm ./chunks/`
- Remove stale cache:
  - `data-extract cache clear`

## Configuration

Configuration files are loaded in precedence order:

1. CLI arguments
2. Environment variables
3. Session config
4. User config (`~/.config/data-extract/config.yaml`)
5. Project config (`.data-extract.yaml`)
6. Defaults

Useful commands:

- Initialize project config:
  - `data-extract config init`
- Show effective config:
  - `data-extract config show`
- Validate config:
  - `data-extract config validate`
- Save a preset:
  - `data-extract config presets save <name>`
- Load a preset:
  - `data-extract config presets load <name>`

## Troubleshooting

### Common command symptoms

- `No files found` → confirm the path is correct and add `--recursive` for nested directories.
- `Unsupported file format` → verify supported formats in your file list.
- `OCR unavailable` → install OCR dependencies before processing scanned documents or image-based inputs.
- `Session not found` → run `data-extract session list` and copy a valid session ID.
- `UI check failed` → run `data-extract ui --check` and resolve missing Node/runtime dependencies.

### API and security errors

- If backend rejects remote host requests, confirm API key/session secret values are set in environment and your host binding strategy is correct.
- If startup is blocked by migration/version issues, run migrations from the backend entry path and restart the API worker.

For local recovery, run a small sample path first and inspect the most recent log context.

## Next steps

- For product-level context, see [Product Documentation](product-documentation.md).
- For onboarding and architecture, see [Project Overview](project-overview.md), [Architecture - Backend](architecture-backend.md), [Architecture - UI](architecture-ui.md).
- For API-specific behavior, see [API Contracts - Backend](api-contracts-backend.md) and [API Contracts - UI](api-contracts-ui.md).

## Journey and acceptance mapping

Behavior coverage references map to journey tests in `tests/uat/journeys/`.

- Journey 1 (first-time setup): `tests/uat/journeys/test_journey_1_first_time_setup.py`
- Journey 2 (batch processing): `tests/uat/journeys/test_journey_2_batch_processing.py`
- Journey 3 (semantic analysis): `tests/uat/journeys/test_journey_3_semantic_analysis.py`
- Journey 4 (learning mode): `tests/uat/journeys/test_journey_4_learning_mode.py`
- Journey 5 (preset configuration): `tests/uat/journeys/test_journey_5_preset_configuration.py`
- Journey 6 (error recovery): `tests/uat/journeys/test_journey_6_error_recovery.py`
- Journey 7 (incremental + batch): `tests/uat/journeys/test_journey_7_incremental_batch.py`

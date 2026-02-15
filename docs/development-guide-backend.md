# Development Guide - Backend

## Prerequisites

- Python 3.11+
- `uv` package manager
- Optional: OCR tooling if using OCR extras

## Environment Setup

1. `uv venv --seed`
2. `source .venv/bin/activate`
3. `uv pip install -e ".[dev]"`
4. `python -m spacy download en_core_web_md`

## Common Commands

- Run tests: `pytest -v`
- Run fast tests: `pytest -m "unit and not slow"`
- Run quality gates: `python scripts/run_quality_gates.py --pre-commit`
- CI-style checks: `python scripts/run_quality_gates.py --ci-mode`

## Key Backend Entry Points

- CLI: `src/data_extract/__main__.py`, `src/data_extract/app.py`
- API: `src/data_extract/api/main.py`

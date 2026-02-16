# Development Guide - Backend

## Prerequisites

- Python 3.11+
- `uv` package manager
- Optional OCR toolchain when OCR workflows are required

## Environment Setup

1. `uv venv --seed`
2. `source .venv/bin/activate`
3. `uv pip install -e ".[dev]"`
4. `python -m spacy download en_core_web_md`

## Core Commands

- Full tests: `pytest -v`
- Fast local unit pass: `pytest -m "unit and not slow"`
- Quality gate (pre-commit profile): `python scripts/run_quality_gates.py --pre-commit`
- CI-style quality gate: `python scripts/run_quality_gates.py --ci-mode`

## Backend Entry Points

- CLI: `src/data_extract/__main__.py`, `src/data_extract/app.py`
- API: `src/data_extract/api/main.py`

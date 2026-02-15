# Development Instructions

## Backend Setup

- `uv venv --seed && source .venv/bin/activate`
- `uv pip install -e ".[dev]"`
- `python -m spacy download en_core_web_md`

## Backend Quality and Tests

- `pytest -v`
- `pytest -m "unit and not slow"`
- `python scripts/run_quality_gates.py --pre-commit`
- `python scripts/run_quality_gates.py --ci-mode`

## Frontend Setup

- `cd ui && npm install`
- `cd ui && npm run dev`
- `cd ui && npm run build`
- `cd ui && npm run e2e:gui`

## Configuration

- Use `config.yaml.example` as the template for `config.yaml`.
- Environment overrides use `DATA_EXTRACTOR_*` variables.
- Do not commit `.env` or secret config files.

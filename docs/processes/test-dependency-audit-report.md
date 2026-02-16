# Test Dependency Audit Report

**Generated:** 2026-02-15T21:42:46.445333

## Summary

- **Test Files Scanned:** 324
- **Total Imports Found:** 404
- **Declared Dependencies:** 0
- **Missing Dependencies:** 32
- **Potentially Unused:** 0

## ⚠️ Missing Dependencies

These packages are imported in tests but not declared in pyproject.toml:

- `click`
- `download_ocr_dependencies`
- `fastapi`
- `generate_story_template`
- `joblib`
- `jsonschema`
- `measure_progress_overhead`
- `numpy`
- `openpyxl`
- `packaging`
- `pandas`
- `performance_catalog`
- `pptx`
- `psutil`
- `pydantic`
- `pytest`
- `python_docx`
- `pyyaml`
- `refresh_performance_baselines`
- `reportlab`
- `rich`
- `run_performance_suite`
- `scikit_learn`
- `scipy`
- `setup_environment`
- `spacy`
- `sqlalchemy`
- `starlette`
- `structlog`
- `textstat`
- `typer`
- `validate_performance`

## 💡 Recommendations

Add 32 missing dependencies to pyproject.toml [dev] section
  - Add: click
  - Add: download_ocr_dependencies
  - Add: fastapi
  - Add: generate_story_template
  - Add: joblib
  ... and 27 more

# Build & Deployment

## Package Distribution

**Current Status:** Development-only (Epic 5 implements full distribution)

## Build Process

```bash
# Install build dependencies
pip install build twine

# Build distribution
python -m build

# This creates:
# - dist/data-extraction-tool-0.1.0.tar.gz (source)
# - dist/data_extraction_tool-0.1.0-py3-none-any.whl (wheel)

# Verify build
twine check dist/*
```

## CLI Entry Point

```bash
# Verify CLI is installed
which data-extract  # macOS/Linux
where data-extract  # Windows

# Test CLI
data-extract --help
data-extract --version

# The CLI loads from: src/data_extract/cli.py
# Entry point defined in: pyproject.toml [project.scripts]
```

## Local Installation for Testing

```bash
# Install package in development mode (already done with -e)
pip install -e .

# Reinstall if modified
pip install -e . --force-reinstall

# Uninstall
pip uninstall data-extraction-tool
```

## Virtual Environment Management

### Create backup of current environment

```bash
# Generate requirements file
pip freeze > requirements.txt

# Later: recreate from requirements
pip install -r requirements.txt
```

### Reset virtual environment

```bash
# Remove venv
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows

# Recreate and reinstall
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate
pip install -e ".[dev]"
python -m spacy download en_core_web_md
pre-commit install
```

---

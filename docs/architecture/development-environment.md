# Development Environment

## Prerequisites

**Required:**
- Python 3.12.x (enterprise requirement - must be exact version)
- Git (for version control)
- Tesseract OCR engine 5.x (system-level dependency)

**Recommended:**
- VS Code or PyCharm (Python IDE)
- Windows Terminal or iTerm2 (modern terminal for Rich UI)
- 16GB RAM (for processing large batches)
- SSD (faster file I/O)

## Setup Commands

```bash
# Clone repository
git clone <repository-url>
cd data-extraction-tool

# Create Python 3.12 virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Verify Python version
python --version  # Should show Python 3.12.x

# Install dependencies (development mode with dev tools)
pip install -e ".[dev]"

# Download spaCy language model
python -m spacy download en_core_web_md

# Install pre-commit hooks (enforces code quality)
pre-commit install

# Verify installation
python -m data_extract --help

# Run tests to verify setup
pytest tests/ -v

# Check code quality
ruff check src/
mypy src/
black --check src/
```

## IDE Configuration (VS Code)

**`.vscode/settings.json`:**
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"]
}
```

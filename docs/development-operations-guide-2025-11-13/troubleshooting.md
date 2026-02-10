# Troubleshooting

## Common Setup Issues

### "python not found" or "python --version shows 2.x"

```bash
# Check if Python 3.12+ is installed
python3 --version
python3.12 --version

# If 3.12+ found, use explicitly
python3.12 -m venv venv
python3.12 -m pip install -e ".[dev]"
```

### "venv not found" after activation

```bash
# Windows: venv not created
python -m venv venv

# macOS/Linux: venv not created
python3 -m venv venv

# Make sure you're in project root
cd data-extraction-tool
```

### "pip: command not found"

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Or use python -m pip instead of pip
python -m pip install -e ".[dev]"
```

### "ImportError: No module named spacy"

```bash
# Install spaCy with specific version
pip install "spacy>=3.7.2,<4.0"

# Download model
python -m spacy download en_core_web_md

# Verify
python -c "import spacy; print(spacy.__version__)"
```

## spaCy Model Issues

See `docs/troubleshooting-spacy.md` for comprehensive spaCy troubleshooting.

**Quick fixes:**

```bash
# Model not found
python -m spacy download en_core_web_md

# Version mismatch
pip install --upgrade "spacy>=3.7.2,<4.0"
python -m spacy download en_core_web_md

# Validation
python -m spacy validate

# Manual installation if download fails
# Download from: https://github.com/explosion/spacy-models/releases
# Then: pip install path/to/en_core_web_md-3.8.0-py3-none-any.whl
```

## Code Quality Issues

### "ruff check" reports errors

```bash
# Auto-fix most issues
ruff check src/ tests/ --fix

# Manually fix remaining issues
# See ruff output for line numbers and descriptions
```

### "mypy" reports type errors

```bash
# Type errors must be fixed manually
mypy src/data_extract/
# See output, then fix type hints in code

# Ignore specific errors (not recommended)
# Add '# type: ignore' on problematic lines
```

### "black" reports formatting issues

```bash
# Auto-fix formatting
black src/ tests/

# Check without fixing
black --check src/ tests/
```

## Test Issues

### "pytest: command not found"

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Or run as module
python -m pytest
```

### "Tests hang or timeout"

```bash
# Run with timeout
pytest --timeout=30

# Run specific test
pytest tests/unit/ -v

# Skip performance tests (they may hang)
pytest -m "not performance"

# See tests/performance/README.md for known issues
```

### "ImportError: cannot import from src"

```bash
# Make sure you're in project root
cd data-extraction-tool

# Verify package is installed
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

### "Coverage below threshold"

```bash
# Generate detailed coverage report
pytest --cov=src --cov-report=term-missing

# Identify which modules need coverage
coverage report | grep -v "100%"

# Add missing tests
# Tests should mirror src/ structure in tests/
```

## Pre-commit Hook Issues

### "Pre-commit hook failed"

```bash
# Check which hook failed
pre-commit run --all-files -v

# Fix the issue (usually code formatting)
black src/ tests/

# Run hooks again
pre-commit run --all-files

# Retry commit
git add .
git commit -m "message"
```

### "Hook timeout or hangs"

```bash
# Increase timeout in .pre-commit-config.yaml if needed
# Or skip hooks temporarily (not recommended)
git commit --no-verify
```

## Platform-Specific Issues

### Windows Path Issues

```bash
# Use forward slashes in Python code
Path("src/data_extract/core.py")  # OK
Path("src\data_extract\core.py")  # Avoid in code

# On command line, backslashes are fine
cd src\data_extract
```

### macOS/Linux Permission Denied

```bash
# Use user-level installation
pip install --user -e ".[dev]"

# Or use sudo (not recommended)
sudo pip install -e ".[dev]"
```

### Network/Proxy Issues (spaCy Download)

```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Then download model
python -m spacy download en_core_web_md

# Alternative: manual download
# See docs/troubleshooting-spacy.md for links
```

---

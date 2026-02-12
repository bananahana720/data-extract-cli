# UV Package Manager Migration Guide

## Overview

This project has migrated from `pip` and `python -m venv` to **uv**, a blazingly fast Python package installer and resolver written in Rust.

**Migration Date:** 2025-11-29
**Reason:** 10-100x faster than pip, better dependency resolution, unified tooling

## What is UV?

[uv](https://github.com/astral-sh/uv) is a drop-in replacement for pip and pip-tools, offering:
- **Speed:** 10-100x faster than pip
- **Reliability:** Better dependency resolution algorithm
- **Compatibility:** Drop-in replacement for pip commands
- **Lock files:** Deterministic builds with `uv.lock`
- **Single tool:** Replaces pip, pip-tools, virtualenv, and more

## Installation

### Install UV

```bash
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip (if you still have it):
pip install uv

# Verify installation:
uv --version
```

### Quick Start (New Setup)

```bash
# 1. Create virtual environment
uv venv

# 2. Activate virtual environment
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

# 3. Install project dependencies
uv pip install -e ".[dev]"

# 4. Download spaCy model
python -m spacy download en_core_web_md

# 5. Setup pre-commit hooks
pre-commit install

# 6. Verify installation
python scripts/smoke_test_semantic.py
pytest
```

## Migration from Existing pip/venv Setup

### Option 1: Clean Migration (Recommended)

```bash
# 1. Remove old virtual environment
rm -rf venv  # or venv312, .venv, etc.

# 2. Create new environment with uv
uv venv

# 3. Activate and install
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"

# 4. Setup spaCy and pre-commit
python -m spacy download en_core_web_md
pre-commit install

# 5. Run tests to verify
pytest
```

### Option 2: In-Place Migration (Keep Existing venv)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Activate your existing venv
source venv/bin/activate  # adjust path as needed

# Install uv in the venv (optional, for local use)
pip install uv

# Now use uv commands instead of pip
uv pip install <package>
uv pip freeze
uv pip list
```

## Command Reference

### pip → uv Command Mapping

| Old (pip)                      | New (uv)                       | Notes                          |
|--------------------------------|--------------------------------|--------------------------------|
| `python -m venv venv`          | `uv venv`                      | Creates .venv by default       |
| `pip install <pkg>`            | `uv pip install <pkg>`         | Much faster                    |
| `pip install -e .`             | `uv pip install -e .`          | Editable install               |
| `pip install -e ".[dev]"`      | `uv pip install -e ".[dev]"`   | With extras                    |
| `pip freeze`                   | `uv pip freeze`                | List installed packages        |
| `pip list`                     | `uv pip list`                  | Show packages                  |
| `pip install -r requirements.txt` | `uv pip install -r requirements.txt` | From requirements file |
| `pip install --upgrade <pkg>`  | `uv pip install --upgrade <pkg>` | Upgrade package            |
| `pip uninstall <pkg>`          | `uv pip uninstall <pkg>`       | Remove package                 |

### New UV-Specific Commands

```bash
# Compile dependencies to requirements.txt
uv pip compile pyproject.toml -o requirements.txt

# Sync environment to exact dependencies (like pip-sync)
uv pip sync requirements.txt

# Install from pyproject.toml with lock file
uv pip install -r pyproject.toml --generate-hashes
```

## Project-Specific Changes

### Updated Scripts

The following scripts have been updated to use `uv`:

1. **scripts/setup_environment.py**
   - Now uses `uv venv` instead of `python -m venv`
   - Uses `uv pip install` instead of `pip install`
   - Falls back to pip if uv not available

2. **scripts/init_claude_session.py**
   - Uses `uv pip` for dependency installation
   - Checks for uv availability

3. **GitHub Actions (.github/workflows/*.yml)**
   - Updated to install and use uv
   - Caches uv installations for speed

4. **CLAUDE.md**
   - Documentation updated with uv commands
   - Setup instructions now use uv

### Automation Scripts

All automation scripts in `scripts/` directory have been updated to:
- Use `uv pip` instead of `pip` where possible
- Fall back gracefully to `pip` if `uv` is not available
- Print warnings if using legacy pip

## Frequently Asked Questions

### Q: Do I need to uninstall pip?
**A:** No! uv works alongside pip. You can keep pip installed for compatibility.

### Q: Will my existing venv work with uv?
**A:** Yes! uv can work with existing virtual environments. Just use `uv pip` instead of `pip`.

### Q: What about requirements.txt files?
**A:** uv works with requirements.txt files. Use `uv pip install -r requirements.txt`.

### Q: Does uv work with pyproject.toml?
**A:** Yes! uv fully supports PEP 621 (pyproject.toml dependencies).

### Q: Is uv compatible with all pip packages?
**A:** Yes! uv uses the same PyPI index and is fully compatible with pip.

### Q: What about pre-commit hooks?
**A:** Pre-commit hooks use their own Python environments. No changes needed for .pre-commit-config.yaml.

### Q: Does this affect CI/CD?
**A:** GitHub Actions workflows have been updated to use uv. Local development can use either uv or pip.

### Q: What if I encounter issues with uv?
**A:** Fall back to pip temporarily:
```bash
pip install -e ".[dev]"
```
Then report the issue to the team.

## Performance Comparison

### Dependency Installation Speed

```
# pip (baseline)
$ time pip install -e ".[dev]"
real    2m 15s

# uv (10-100x faster)
$ time uv pip install -e ".[dev]"
real    0m 8s

# Speed improvement: ~16x faster
```

### Lock File Generation

```
# pip-compile (from pip-tools)
$ time pip-compile pyproject.toml
real    45s

# uv
$ time uv pip compile pyproject.toml
real    2s

# Speed improvement: ~22x faster
```

## Troubleshooting

### Issue: "uv: command not found"

**Solution:**
```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.cargo/bin:$PATH"

# Reload shell
source ~/.bashrc
```

### Issue: "Failed to create virtual environment"

**Solution:**
```bash
# Remove corrupted venv
rm -rf .venv venv

# Create fresh environment
uv venv

# Activate
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

### Issue: "Package not found" or resolution errors

**Solution:**
```bash
# Clear uv cache
uv cache clean

# Retry installation
uv pip install -e ".[dev]"
```

### Issue: Scripts still using pip

**Solution:**
Some scripts may still reference pip for backwards compatibility. This is expected and harmless.

## Additional Resources

- **UV Documentation:** https://github.com/astral-sh/uv
- **UV Installation Guide:** https://github.com/astral-sh/uv#installation
- **UV vs pip Benchmark:** https://github.com/astral-sh/uv#benchmarks
- **Project pyproject.toml:** `<project-root>/pyproject.toml`

## Rollback Instructions

If you need to roll back to pip:

```bash
# Deactivate current environment
deactivate

# Remove uv-created venv
rm -rf .venv

# Create classic venv
python -m venv venv

# Activate
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install with pip
pip install --upgrade pip
pip install -e ".[dev]"

# Setup spaCy
python -m spacy download en_core_web_md

# Setup pre-commit
pre-commit install
```

## Migration Checklist

- [ ] Install uv package manager
- [ ] Remove old virtual environment (optional)
- [ ] Create new environment with `uv venv`
- [ ] Install dependencies with `uv pip install -e ".[dev]"`
- [ ] Download spaCy model
- [ ] Setup pre-commit hooks
- [ ] Run smoke tests: `python scripts/smoke_test_semantic.py`
- [ ] Run full test suite: `pytest`
- [ ] Update team documentation
- [ ] Update CI/CD pipelines (if not already done)

## Support

For questions or issues with the migration:
1. Check this guide's Troubleshooting section
2. Review UV documentation: https://github.com/astral-sh/uv
3. Ask the team on Slack/Teams
4. Create an issue in the project repository

---

**Last Updated:** 2025-11-29
**Migration Status:** ✅ Complete

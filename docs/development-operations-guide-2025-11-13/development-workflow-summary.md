# Development Workflow Summary

## Daily Development Cycle

```bash
# 1. Start work (one-time setup)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"

# 2. Before each coding session
source venv/bin/activate
git pull origin main

# 3. Create feature branch
git checkout -b story/X-Y-name

# 4. Develop and test (repeat)
# ... write code ...
black src/ tests/
ruff check src/ tests/ --fix
mypy src/data_extract/
pytest -m "not performance"

# 5. Before committing
pre-commit run --all-files

# 6. Commit changes
git add .
git commit -m "Descriptive message"

# 7. Push to remote
git push origin story/X-Y-name

# 8. Create pull request on GitHub
# ... tests run automatically ...
```

## Quality Gates Checklist

Before committing, verify:

- [ ] Code formatted: `black src/ tests/` ✓
- [ ] Linting passes: `ruff check src/ tests/` ✓
- [ ] Types checked: `mypy src/data_extract/` ✓
- [ ] Tests pass: `pytest -m "not performance"` ✓
- [ ] Pre-commit hooks pass: `pre-commit run --all-files` ✓
- [ ] Coverage maintained: `pytest --cov=src` > 60% ✓

**Zero violations required. No exceptions.**

---

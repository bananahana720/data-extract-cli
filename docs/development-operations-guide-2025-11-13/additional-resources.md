# Additional Resources

## Documentation

- **Architecture**: `docs/architecture/index.md` - System design and ADRs
- **PRD**: `docs/PRD/index.md` - Product requirements
- **Tech Spec**: `docs/tech-spec-epic-1.md` - Epic 1 technical specification
- **Epics & Stories**: `docs/epics.md`, `docs/tech-spec-epic-*/` - Implementation roadmap
- **CI/CD**: `docs/ci-cd-pipeline.md` - Detailed CI/CD documentation
- **Testing**: `docs/TESTING-README.md` - Comprehensive test guide
- **spaCy**: `docs/troubleshooting-spacy.md` - spaCy troubleshooting
- **Performance**: `docs/architecture/epic-4-performance-baselines.md` - Performance metrics

## Quick Reference

### Common Commands Cheat Sheet

```bash
# Setup
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -e ".[dev]"
python -m spacy download en_core_web_md
pre-commit install

# Development
black src/ tests/
ruff check src/ tests/ --fix
mypy src/data_extract/
pytest -m "not performance"
pre-commit run --all-files

# Testing
pytest                              # All tests
pytest -m unit                      # Unit only
pytest -m integration               # Integration only
pytest --cov=src --cov-report=html  # With coverage
pytest -x                           # Stop on first failure
pytest -n auto                      # Parallel
pytest tests/unit/test_extract/test_pdf.py::test_name  # Specific test

# Debugging
pytest --pdb tests/                 # Drop to debugger
pytest -vv --showlocals tests/      # Verbose with locals
pytest -s tests/                    # Show print statements
pytest --tb=long tests/             # Full tracebacks

# CI/CD Local
pre-commit run --all-files
pytest --cov=src -m "not performance"

# Cleanup
rm -rf venv __pycache__ .pytest_cache htmlcov *.egg-info
```

### File Locations

- **Main Code**: `src/data_extract/`
- **Legacy Code**: `src/{cli,core,extractors,processors,formatters,infrastructure,pipeline}/`
- **Tests**: `tests/`
- **Configuration**: `pyproject.toml`, `pytest.ini`, `.pre-commit-config.yaml`
- **CI/CD**: `.github/workflows/`
- **Documentation**: `docs/`
- **Fixtures**: `tests/fixtures/`
- **Scripts**: `scripts/`

## External Resources

- [Python 3.12 Docs](https://docs.python.org/3.12/)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [mypy Type Checker](https://mypy.readthedocs.io/)
- [Pre-commit Framework](https://pre-commit.com/)
- [spaCy Documentation](https://spacy.io/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Pydantic v2 Docs](https://docs.pydantic.dev/latest/)

## Getting Help

1. **Setup Issues**: Review prerequisites and installation steps above
2. **Test Failures**: Check `docs/TESTING-README.md`
3. **spaCy Problems**: See `docs/troubleshooting-spacy.md`
4. **Architecture Questions**: Review `docs/architecture/index.md` and CLAUDE.md
5. **Story Context**: Check `docs/epics.md` and `docs/tech-spec-epic-*/`
6. **Performance**: See `docs/architecture/epic-4-performance-baselines.md`

---

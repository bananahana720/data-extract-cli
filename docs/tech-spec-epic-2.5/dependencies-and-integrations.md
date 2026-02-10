# Dependencies and Integrations

## New Dependencies (Added in Epic 2.5)

**NLP Processing:**
- **spaCy** >= 3.7.2, < 4.0 - Industrial-strength NLP library for sentence segmentation
- **en_core_web_md** model - Medium-sized English language model (43MB download)
- **Rationale:** Required for Epic 3 Story 3.1 semantic chunking, classical NLP approach (no transformers)
- **Installation:** `pip install spacy && python -m spacy download en_core_web_md`

**Performance Profiling:**
- **psutil** >= 5.9.0, < 6.0 - Cross-platform process and system utilities
- **cProfile** - Built-in Python profiler (standard library, no install needed)
- **memory_profiler** >= 0.61.0, < 1.0 - Line-by-line memory consumption profiling
- **Rationale:** Identify performance bottlenecks, validate NFR-P1 and NFR-P2 compliance
- **Scope:** Development/testing only (not runtime dependencies)

## Existing Dependencies (No Changes)

All dependencies from Epic 1 and Epic 2 remain unchanged:
- pydantic >= 2.0.0 - Data validation
- pytest >= 8.0.0 - Testing framework
- black, ruff, mypy - Code quality tools
- PyMuPDF, python-docx, openpyxl, pytesseract - Document extraction
- structlog - Structured logging

## System Requirements

**Python Version:**
- Python 3.12.x (mandatory enterprise requirement)
- spaCy 3.7.2 verified compatible with Python 3.12

**Disk Space:**
- spaCy en_core_web_md model: ~43MB
- Large test fixtures: ~50MB (tests/fixtures/large/)
- Profile data: ~10MB per profiling session

**Memory:**
- spaCy model loading: ~150MB baseline memory increase
- Negligible impact on <2GB overall budget

## Integration Points

**Epic 3 Preparation:**
- `get_sentence_boundaries()` function provides sentence-level chunking for Story 3.1
- spaCy NLP pipeline ready for semantic analysis integration
- Performance baselines enable regression detection in Epic 3

**CI/CD Integration:**
- Performance tests run weekly (not every commit - too slow)
- pytest markers separate performance tests: `pytest -m "not performance"`
- Coverage tracking includes new test modules

**Documentation Updates:**
- CLAUDE.md: spaCy setup instructions, Epic 2 lessons learned
- README.md: Model download step in setup section
- tests/fixtures/README.md: Large fixture creation process

## Dependency Security

**Verification Steps:**
1. Check spaCy 3.7.2 for known CVEs before installation
2. Verify psutil, memory_profiler from official PyPI (no typosquatting)
3. Pin all versions in pyproject.toml
4. Enable Dependabot alerts for new vulnerabilities
5. Review dependency licenses (all MIT/BSD/Apache 2.0 compatible)

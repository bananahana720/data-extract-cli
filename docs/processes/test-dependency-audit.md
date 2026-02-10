# Test Dependency Audit Process

This document defines the systematic process for validating new library dependencies before epic development starts. Follow this checklist when adding new libraries or upgrading major versions.

## When to Use This Process

This audit is **REQUIRED** when:
- Adding a new library to `pyproject.toml` (not previously used in the project)
- Upgrading a library to a new major version (e.g., 2.x → 3.x)
- Adding libraries with external dependencies (models, data files, binaries)
- Adding libraries that affect performance-critical paths
- Adding libraries with security implications (network access, file system access)

This audit is **OPTIONAL** for:
- Minor/patch version updates (e.g., 1.2.3 → 1.2.4)
- Development-only dependencies (unless they affect CI/CD)
- Documentation-only dependencies

## Step-by-Step Dependency Audit Checklist

### Phase 1: Pre-Installation Validation

#### 1.1 Security Assessment
- [ ] **Check for CVEs**: Search for known vulnerabilities in the target version
  ```bash
  # Check vulnerability databases
  pip-audit [package-name]==[version]
  # Or manually check: https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=[package-name]
  ```
- [ ] **Review dependencies**: Check what transitive dependencies will be installed
  ```bash
  pip show [package-name] --verbose  # After test installation
  ```
- [ ] **License compatibility**: Verify license aligns with project requirements

#### 1.2 Version Selection
- [ ] **Specify version constraints** in `pyproject.toml`:
  ```toml
  [project]
  dependencies = [
      "package-name>=X.Y.Z,<X+1.0",  # Story Y.Z - Brief reason
  ]
  ```
- [ ] **Document the story/epic** that required this dependency (inline comment)
- [ ] **Use semantic versioning** constraints to prevent breaking changes

### Phase 2: Installation & Basic Validation

#### 2.1 Local Installation
- [ ] **Create test environment**:
  ```bash
  python -m venv test-env
  source test-env/bin/activate  # or test-env\Scripts\activate on Windows
  pip install -e ".[dev]"
  ```
- [ ] **Verify installation**:
  ```bash
  python -c "import [package_name]; print([package_name].__version__)"
  ```
- [ ] **Run existing tests** to check for conflicts:
  ```bash
  pytest -xvs  # Stop on first failure with verbose output
  ```

#### 2.2 Model/Data Downloads (if applicable)
- [ ] **Document download commands** (like spaCy's model download):
  ```bash
  # Example: python -m spacy download en_core_web_md
  ```
- [ ] **Verify download success**:
  ```bash
  # Example: python -m spacy validate
  ```
- [ ] **Document model size and version** for CI caching

### Phase 3: Smoke Tests & Performance Baselines

#### 3.1 Create Smoke Test Script
- [ ] **Create `scripts/smoke-test-[package].py`** with basic functionality tests
- [ ] **Include performance benchmarks**:
  ```python
  import time
  start = time.perf_counter()
  # ... operation ...
  duration_ms = (time.perf_counter() - start) * 1000
  assert duration_ms < THRESHOLD, f"Too slow: {duration_ms:.2f}ms"
  ```
- [ ] **Test critical APIs** used by the project
- [ ] **Include error handling** validation

**Example Structure (from spaCy integration):**
```python
#!/usr/bin/env python3
"""Smoke test for [package] dependency."""

def test_basic_functionality():
    """Validate basic [package] operations work."""
    # Import and basic operation
    pass

def test_performance():
    """Validate performance meets requirements."""
    # Measure and assert thresholds
    pass

def test_error_handling():
    """Validate error conditions handled gracefully."""
    # Test missing data, invalid input, etc.
    pass

if __name__ == "__main__":
    test_basic_functionality()
    test_performance()
    test_error_handling()
    print("✅ All smoke tests passed")
```

#### 3.2 Establish Performance Baselines
- [ ] **Document baseline metrics**:
  - Load/initialization time
  - Operation throughput (ops/sec or words/sec)
  - Memory footprint
  - Disk usage (if caching)
- [ ] **Compare against NFRs** (Non-Functional Requirements)
- [ ] **Add to `docs/performance-baselines-epic-X.md`**

### Phase 4: CI/CD Integration

#### 4.1 CI Configuration
- [ ] **Update CI workflow** (`.github/workflows/test.yml`):
  ```yaml
  - name: Install [package] dependencies
    run: |
      pip install -e ".[dev]"
      # Additional setup commands if needed
      python scripts/smoke-test-[package].py
  ```

#### 4.2 Caching Strategy
- [ ] **Configure CI cache** for downloaded models/data:
  ```yaml
  - name: Cache [package] models
    uses: actions/cache@v3
    with:
      path: ~/.cache/[package]
      key: ${{ runner.os }}-[package]-${{ hashFiles('**/pyproject.toml') }}
  ```
- [ ] **Document cache paths** and invalidation strategy
- [ ] **Test cache effectiveness** (check CI logs for cache hits)

### Phase 5: Documentation Updates

#### 5.1 Installation Documentation
- [ ] **Update CLAUDE.md** with setup instructions:
  ```markdown
  ### [Package] Setup (Required for Epic X)
  \```bash
  pip install -e ".[dev]"
  # Additional setup commands
  python scripts/smoke-test-[package].py  # Verify installation
  \```
  ```
- [ ] **Update README.md** if user-facing changes

#### 5.2 Troubleshooting Guide
- [ ] **Create/update troubleshooting doc** (`docs/troubleshooting-[package].md`) covering:
  - Common installation issues
  - Model/data download problems
  - Version compatibility
  - Performance issues
  - Network/proxy configuration
  - Error messages and solutions

#### 5.3 Story Template Integration
- [ ] **Link from story template wiring checklist** (coordinate with Story 3.5.1):
  - Add to BOM section if new dependency
  - Reference this audit process in dev notes

### Phase 6: Integration Testing

#### 6.1 Create Integration Tests
- [ ] **Add integration tests** to `tests/integration/test_[package]_integration.py`
- [ ] **Test with real project data** (use fixtures from `tests/fixtures/`)
- [ ] **Validate error handling** for missing dependencies
- [ ] **Test performance under load** (if applicable)

#### 6.2 Cross-Module Testing
- [ ] **Test interaction** with existing modules
- [ ] **Verify no regressions** in existing functionality
- [ ] **Check memory usage** doesn't exceed limits

### Phase 7: Final Validation

#### 7.1 Quality Gates
- [ ] **Run full quality check suite**:
  ```bash
  black src/ tests/
  ruff check src/ tests/
  mypy src/data_extract/
  pytest --cov=src
  ```
- [ ] **All tests passing** (including new integration tests)
- [ ] **Coverage maintained** (≥80% for greenfield code)

#### 7.2 Documentation Review
- [ ] **All documentation updated** and accurate
- [ ] **Troubleshooting guide tested** by following it
- [ ] **Performance baselines documented** and within limits

## Common Pitfalls to Avoid

### Installation Issues
- **Pitfall**: Not specifying upper version bounds → future breaking changes
- **Solution**: Always use `>=X.Y.Z,<X+1.0` format

- **Pitfall**: Missing transitive dependencies in restricted environments
- **Solution**: Test in clean virtual environment, document all requirements

### Performance Issues
- **Pitfall**: Not establishing baselines → performance degradation goes unnoticed
- **Solution**: Always measure and document baseline metrics

- **Pitfall**: Loading models/data on every operation
- **Solution**: Implement lazy loading with module-level caching (see spaCy example)

### CI/CD Issues
- **Pitfall**: CI fails due to missing models/data
- **Solution**: Include download steps in CI workflow or use pre-cached images

- **Pitfall**: Cache invalidation causes flaky tests
- **Solution**: Use deterministic cache keys based on dependency versions

### Documentation Issues
- **Pitfall**: Setup instructions scattered across multiple files
- **Solution**: Centralize in CLAUDE.md with references from other docs

- **Pitfall**: No troubleshooting guide → repeated support requests
- **Solution**: Create comprehensive troubleshooting doc with common issues

## Epic 2.5 spaCy Integration Example

Story 2.5.2 provides a complete example of this process:

### What Was Done
1. **Security Check**: Verified no CVEs in spaCy 3.7.2
2. **Installation**: Added `spacy>=3.7.2,<4.0` to `pyproject.toml` with story reference
3. **Model Download**: Documented `python -m spacy download en_core_web_md`
4. **Validation**: Created `python -m spacy validate` check
5. **Smoke Test**: Built `scripts/smoke-test-semantic.py` (referenced in Story 3.5.4)
6. **Performance**: Established baselines (1.2s load, 4850 words/sec)
7. **CI Integration**: Added model caching at `~/.cache/spacy`
8. **Documentation**: Updated CLAUDE.md, README.md, created troubleshooting guide
9. **Integration Tests**: 13 tests in `tests/integration/test_spacy_integration.py`
10. **Accuracy Validation**: 100% accuracy on 55-case gold standard corpus

### Key Lessons
- **Lazy loading pattern** prevented repeated model loading (100x performance gain)
- **Comprehensive error messages** helped users self-diagnose issues
- **Gold standard corpus** enabled regression testing
- **CI caching** saved ~2 seconds per test run

## Process Ownership

- **Owner**: Development Team (coordinate with Story Owner)
- **Review**: Technical Lead or Architect
- **Updates**: This process should be updated when new patterns emerge

## Related Documents

- [Epic 3.5 Technical Specification](../tech-spec-epic-3.5.md)
- [Story 2.5.2: spaCy Integration](../stories/2.5-2-spacy-integration-and-end-to-end-testing.md)
- [Troubleshooting spaCy Guide](../troubleshooting-spacy.md)
- [CLAUDE.md Development Guidelines](../../.claude/CLAUDE.md)

---

*Last Updated: 2025-11-18*
*Process Version: 1.0*

# Epic 3.5 Test Priorities - Quick Reference

**Generated:** 2025-11-17
**Source:** Epic 3.5 Test Design Assessment
**Owner:** TEA Agent (Master Test Architect)

## P0 - CRITICAL (Block Epic 4) - Complete Day 1

### 1. Template Generator Tests (Story 3.5.1)
**File:** `tests/unit/test_scripts/test_template_generator.py`
**Owner:** Elena
**Time:** 3h

```python
def test_cli_argument_parsing():
    """Verify --id, --title, --owner, --hours parameters"""

def test_jinja2_template_rendering():
    """Verify template variables substitution"""

def test_story_file_output_structure():
    """Verify markdown structure matches expected format"""

def test_ac_table_generation():
    """Verify acceptance criteria table format"""

def test_pre_commit_hook_validation():
    """Verify hook rejects incomplete AC tables"""
```

### 2. Semantic Smoke Test Validation (Story 3.5.4)
**File:** `tests/integration/test_scripts/test_smoke_semantic.py`
**Owner:** Charlie
**Time:** 3h

```python
def test_smoke_script_execution():
    """Verify scripts/smoke-test-semantic.py runs successfully"""

def test_tfidf_performance_baseline():
    """Verify TF-IDF <100ms on 1k-word document"""

def test_dependency_import():
    """Verify scikit-learn, joblib, textstat import"""

def test_ci_integration():
    """Verify GitHub Actions workflow integration"""

def test_failure_mode():
    """Verify non-zero exit code on test failure"""
```

### 3. QA Fixtures Validation (Story 3.5.6)
**File:** `tests/integration/test_fixtures/test_semantic_corpus.py`
**Owner:** Dana
**Time:** 2h

```python
def test_corpus_size_requirements():
    """Verify ≥50 docs, ≥250k words total"""

def test_gold_standard_format():
    """Verify expected TF-IDF/LSA annotations"""

def test_pii_sanitization():
    """Verify no SSN, names, account numbers"""

def test_comparison_harness():
    """Verify regression test scripts function"""
```

## P1 - IMPORTANT (Quality Risk) - Complete Day 2

### 4. Scripts Test Infrastructure
**Owner:** Winston
**Time:** 3h

- Create `tests/unit/test_scripts/` directory
- Add `conftest.py` with script fixtures
- Create test stubs for 18 existing scripts
- Setup parametrized test patterns

### 5. Activate Semantic Tests
**Owner:** Charlie
**Time:** 2h

- Remove skip decorators from `test_tfidf_vectorizer.py`
- Remove skip decorators from `test_quality_metrics.py`
- Run tests to establish baselines
- Add to CI pipeline

### 6. Process Documentation Tests
**File:** `tests/integration/test_documentation/test_process_docs.py`
**Owner:** Bob
**Time:** 1h

```python
def test_claude_md_lessons_structure():
    """Verify ≤100 lines, all sections present"""

def test_dependency_audit_completeness():
    """Verify process doc includes checklist"""

def test_adr_template_compliance():
    """Verify ADR-012 follows template"""
```

## P2 - MINOR (Nice to Have) - Complete Day 3

### 7. Performance Baselines
**Owner:** Charlie
**Time:** 2h

- Create `tests/performance/test_semantic/`
- Add TF-IDF scaling tests
- Add cache performance tests
- Document baselines

### 8. UAT Test Cases
**Owner:** Elena
**Time:** 2h

- Create UAT test cases from story ACs
- Document manual validation steps
- Add to `docs/uat/test-cases/`

## Test Execution Checklist

### Day 1
- [ ] Create template generator tests (P0)
- [ ] Create smoke test validation (P0)
- [ ] Create QA fixtures validation (P0)
- [ ] Setup scripts test infrastructure (P1)

### Day 2
- [ ] Activate semantic tests (P1)
- [ ] Create process documentation tests (P1)
- [ ] Run all tests, fix failures
- [ ] Generate coverage reports

### Day 3
- [ ] Create performance baselines (P2)
- [ ] Document UAT test cases (P2)
- [ ] Final validation and sign-off
- [ ] Update sprint status

## Success Metrics

| Metric | Target | Priority |
|--------|--------|----------|
| P0 Tests Created | 23 test cases | CRITICAL |
| P1 Tests Created | 15 test cases | HIGH |
| Test Coverage | ≥80% | HIGH |
| CI Integration | All tests in pipeline | CRITICAL |
| Performance Baseline | <100ms TF-IDF | CRITICAL |

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|------------|-------|
| No template tests → Epic 4 quality issues | Implement P0.1 immediately | Elena |
| No smoke validation → Epic 4 blocked | Implement P0.2 immediately | Charlie |
| No fixture tests → No regression testing | Implement P0.3 immediately | Dana |

---

**Action Required:** Begin P0 test implementation immediately to unblock Epic 4.

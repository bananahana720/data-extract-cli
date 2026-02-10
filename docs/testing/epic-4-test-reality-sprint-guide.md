# Epic 4: Test Reality Sprint - Quick Reference Guide

Date: 2025-11-20
Sprint Lead: Murat (Master Test Architect)
Sprint Duration: 2 Weeks

---

## 🚀 SPRINT MISSION

Transform Epic 4 from 0% behavioral test coverage to production-ready validation through 5 critical behavioral tests that prove semantic correctness.

## 📋 THE 5 CRITICAL BEHAVIORAL TESTS

| Priority | Test | What It Validates | Success Metric |
|----------|------|-------------------|----------------|
| **P0** | BT-001: Duplicate Detection | Finds near-duplicate audit docs | Precision ≥85%, Recall ≥80% |
| **P0** | BT-002: Cluster Coherence | Groups related documents | Silhouette ≥0.65 |
| **P0** | BT-003: RAG Improvement | Better retrieval than baseline | ≥25% precision gain |
| **P1** | BT-004: Scale Performance | Handles 10K docs | <60s, <500MB |
| **P1** | BT-005: Determinism | Same input = same output | 100% identical |

## 🎯 WEEK 1: CORE BEHAVIORAL VALIDATION

### Day 1-2: Duplicate Detection (BT-001)
```bash
# Location
tests/behavioral/test_semantic/test_duplicate_detection.py

# Key Implementation
- Load 45 golden duplicate pairs
- Process through SimilarityAnalyzer
- Calculate precision/recall
- Assert ≥85% precision, ≥80% recall

# Run Test
pytest tests/behavioral/test_semantic/test_duplicate_detection.py -v
```

### Day 3-4: Cluster Coherence (BT-002)
```bash
# Location
tests/behavioral/test_semantic/test_cluster_coherence.py

# Key Implementation
- Load labeled document clusters
- Apply LSA + K-means clustering
- Calculate silhouette score
- Assert score ≥0.65

# Run Test
pytest tests/behavioral/test_semantic/test_cluster_coherence.py -v
```

### Day 5: RAG Improvement (BT-003)
```bash
# Location
tests/behavioral/test_semantic/test_rag_improvement.py

# Key Implementation
- Compare baseline vs TF-IDF retrieval
- Measure precision@5 for test queries
- Calculate improvement percentage
- Assert ≥25% improvement

# Run Test
pytest tests/behavioral/test_semantic/test_rag_improvement.py -v
```

## 📊 WEEK 2: SCALE & DETERMINISM

### Day 1-2: Scale Performance (BT-004)
```bash
# Location
tests/behavioral/test_semantic/test_scale_performance.py

# Key Implementation
- Generate 10K document corpus
- Measure processing time and memory
- Assert <60 seconds, <500MB RAM

# Run Test
pytest tests/behavioral/test_semantic/test_scale_performance.py -v --benchmark-only
```

### Day 3: Determinism (BT-005)
```bash
# Location
tests/behavioral/test_semantic/test_determinism.py

# Key Implementation
- Process same input 3 times
- Hash outputs for comparison
- Assert 100% identical results

# Run Test
pytest tests/behavioral/test_semantic/test_determinism.py -v
```

### Day 4-5: CI Integration
```bash
# Add markers to pytest.ini
[pytest]
markers =
    behavioral: Behavioral validation tests
    semantic: Semantic analysis tests
    epic4: Epic 4 specific tests

# Run full behavioral suite
pytest tests/behavioral/ -m "behavioral and semantic" --behavioral-report=results.json
```

## 🏗️ TEST INFRASTRUCTURE SETUP

### 1. Create Directory Structure
```bash
mkdir -p tests/behavioral/test_semantic
touch tests/behavioral/__init__.py
touch tests/behavioral/test_semantic/__init__.py
touch tests/behavioral/test_semantic/conftest.py
```

### 2. Install Golden Dataset
```bash
# Copy from Story 3.5-6 fixtures
cp fixtures/semantic_corpus_264k.json tests/fixtures/
cp fixtures/golden_annotations.yaml tests/fixtures/

# Verify PII-free status
python scripts/verify_pii_free.py tests/fixtures/
```

### 3. Configure Test Runner
```python
# tests/behavioral/test_semantic/conftest.py

import pytest
from pathlib import Path

@pytest.fixture
def golden_dataset():
    """Load golden dataset for behavioral validation."""
    return load_yaml(Path(__file__).parent / "../../fixtures/golden_dataset.yaml")

@pytest.fixture
def semantic_corpus():
    """Load 264K word semantic corpus."""
    return load_json(Path(__file__).parent / "../../fixtures/semantic_corpus_264k.json")
```

## ✅ DAILY CHECKLIST

### Before Starting Each Day
- [ ] Pull latest changes
- [ ] Verify test environment (spaCy, scikit-learn installed)
- [ ] Check golden dataset integrity
- [ ] Review previous day's test results

### During Implementation
- [ ] Write test first (TDD approach)
- [ ] Focus on behavioral outcomes, not implementation
- [ ] Log all metrics for diagnostics
- [ ] Document any deviations from spec

### End of Day
- [ ] Run implemented tests
- [ ] Update behavioral metrics dashboard
- [ ] Commit with descriptive message
- [ ] Update sprint status in YAML

## 📈 SUCCESS METRICS TRACKING

```python
# scripts/track_behavioral_metrics.py

DAILY_TARGETS = {
    "Day 1-2": {"tests_implemented": 1, "coverage": "BT-001"},
    "Day 3-4": {"tests_implemented": 2, "coverage": "BT-001, BT-002"},
    "Day 5": {"tests_implemented": 3, "coverage": "BT-001, BT-002, BT-003"},
    "Week 2": {"tests_implemented": 5, "coverage": "All behavioral tests"}
}

def check_progress(day):
    """Verify we're on track for sprint success."""
    implemented = count_implemented_tests()
    target = DAILY_TARGETS[day]["tests_implemented"]

    if implemented < target:
        print(f"⚠️ Behind schedule: {implemented}/{target} tests")
    else:
        print(f"✅ On track: {implemented}/{target} tests")
```

## 🚨 COMMON PITFALLS TO AVOID

1. **DON'T test structure** - Test outcomes and behaviors
2. **DON'T mock core components** - Use real semantic pipeline
3. **DON'T skip golden dataset validation** - Verify annotations first
4. **DON'T optimize prematurely** - Correctness before performance
5. **DON'T ignore determinism** - Fix random seeds everywhere

## 🛠️ TROUBLESHOOTING GUIDE

### Test Failures

```bash
# Debug duplicate detection issues
pytest tests/behavioral/test_semantic/test_duplicate_detection.py -v --pdb

# Profile memory usage
pytest tests/behavioral/test_semantic/test_scale_performance.py --memprof

# Check determinism with detailed logging
PYTHONHASHSEED=0 pytest tests/behavioral/test_semantic/test_determinism.py -v -s
```

### Performance Issues

```python
# Profile slow tests
import cProfile
import pstats

def profile_test():
    profiler = cProfile.Profile()
    profiler.enable()

    # Run test
    test_bt004_scale_performance_10k_documents()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

## 🎉 SPRINT COMPLETION CRITERIA

### Must Have (P0)
- [x] BT-001: Duplicate detection test passing
- [x] BT-002: Cluster coherence test passing
- [x] BT-003: RAG improvement test passing
- [x] All tests integrated into CI
- [x] Golden dataset validated

### Should Have (P1)
- [x] BT-004: Scale performance test passing
- [x] BT-005: Determinism test passing
- [x] Behavioral metrics dashboard
- [x] Diagnostic reporting

### Definition of Done
- [ ] All 5 behavioral tests passing
- [ ] CI pipeline green
- [ ] Test documentation complete
- [ ] Sprint retrospective conducted
- [ ] Epic 4 marked "test-ready" in sprint-status.yaml

## 📞 ESCALATION PATHS

| Issue | Contact | Action |
|-------|---------|--------|
| Golden dataset questions | Dana (QA Lead) | Review annotations together |
| Performance bottlenecks | Charlie (Lead Dev) | Profile and optimize |
| CI integration issues | Andrew (Tech Lead) | Debug pipeline config |
| Sprint blockers | Bob (SM) | Re-scope if needed |

## 🔗 REFERENCE LINKS

- [Epic 4 Behavioral Test Strategy](/docs/testing/epic-4-behavioral-test-strategy.md)
- [Test Implementation Specs](/docs/testing/epic-4-behavioral-test-implementations.md)
- [Semantic Corpus Documentation](/docs/qa-fixtures-maintenance-guide.md)
- [Epic 4 Integration Test Design](/docs/epic-4-integration-test-design.md)

---

**REMEMBER**: We're not testing code coverage or structure. We're validating that Epic 4 delivers its promised value: accurate duplicate detection, coherent clustering, and improved RAG retrieval. Focus on behavioral correctness!

**Sprint Motto**: "Behavior > Coverage, Correctness > Speed"

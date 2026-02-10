# Epic 3.5 Technical Specification · Tooling & Semantic Prep (Bridge Epic)

**Epic ID**: Epic 3.5
**Epic Type**: Bridge Epic (Infrastructure & Preparation)
**Dependencies**: Epic 3 (complete), Epic 4 (blocks)
**Owner**: SM (Bob) + Dev (Charlie, Elena, Winston)
**Status**: Backlog
**Created**: 2025-11-17
**Last Updated**: 2025-11-17

---

## 1. Overview & Purpose

### 1.1 Epic Goal

Epic 3.5 is a **bridge epic** that prepares the codebase and development processes for Epic 4 (Semantic Analysis) by:

1. **Closing Process Gaps**: Implement tooling to enforce story/review quality standards identified in Epic 3 retrospective
2. **Installing Semantic Dependencies**: Add and validate classical NLP libraries (scikit-learn, textstat, joblib)
3. **Creating Semantic Test Infrastructure**: Build QA fixtures and validation harnesses for TF-IDF/LSA
4. **Documenting Semantic Patterns**: Create playbooks and ADRs for semantic analysis implementation

### 1.2 Why This Epic Exists

**Retrospective Findings (Epic 3 - 2025-11-16):**

The Epic 3 retrospective identified critical blockers for Epic 4:

- **Missing provenance/metadata reminders** in story templates caused AC failures (AC 3.4-6, 3.5-7)
- **AC evidence added post-review** due to no tooling to enforce completion before status changes
- **Dependency audit doc absent** - deferred from Epic 2, no owner assigned
- **Semantic toolchain not installed** - Epic 4 requires scikit-learn, joblib, textstat validation
- **No semantic test corpus** - Cannot validate TF-IDF/LSA without gold-standard fixtures
- **Junior devs lack semantic context** - Need playbooks/notebooks for TF-IDF/LSA patterns

### 1.3 Bridge Epic Pattern

Like Epic 2.5 (performance/spaCy prep), Epic 3.5:

- ✅ **No Production Features** - Pure infrastructure and process improvements
- ✅ **Unblocks Next Epic** - Epic 4 cannot start without semantic dependencies + QA fixtures
- ✅ **Short Duration** - Focused scope for quick completion
- ✅ **Process + Technical** - Combines developer tooling with library validation
- ✅ **Quality Gates** - Smoke tests, baselines, documentation requirements

---

## 2. Scope & Deliverables

### 2.1 In Scope

**Process/Tooling Improvements (Action Plan Items):**

1. **Story/Review Template Generator** (`scripts/new-story`)
   - Jinja2-based story markdown generator with AC tables, wiring checklists, submission summaries
   - Pre-commit hook integration for template validation
   - CLI interface for story creation

2. **CLAUDE.md Lessons Section** (≤100 lines)
   - Consolidated lessons from Epic 1-3 retrospectives
   - Guidelines visible every AI session
   - Referenced by template scripts for enforced compliance

3. **Test Dependency Audit Documentation**
   - Process doc: `docs/processes/test-dependency-audit.md`
   - Automated checklist hook for dependency validation
   - Examples from Epic 2.5 spaCy integration

**Semantic Preparation (Preparation Sprint Tasks):**

4. **Semantic Dependencies + Smoke Test**
   - Install scikit-learn, joblib, textstat in pyproject.toml
   - Smoke test script validating TF-IDF + LSA + textstat APIs
   - CI cache updates for semantic libraries
   - Performance baseline: TF-IDF fit/transform <100ms on 1k-word doc

5. **Model/Similarity Cache ADR**
   - Architecture Decision Record for semantic model storage
   - Defines cache paths, versioning strategy, CLI integration
   - Addresses joblib persistence, cache invalidation, size limits

6. **Semantic QA Fixtures**
   - 50+ document test corpus (250k+ words) for semantic validation
   - Gold-standard TF-IDF/LSA expected outputs
   - Comparison harness scripts for regression testing
   - Annotated entity references for semantic entity extraction

7. **TF-IDF/LSA Playbook**
   - Jupyter notebook with TF-IDF/LSA examples
   - Vocabulary management patterns
   - Joblib persistence examples
   - Tuning guidance for junior devs

### 2.2 Out of Scope

- ❌ Production semantic analysis features (deferred to Epic 4)
- ❌ Transformer/embedding models (enterprise constraint - classical NLP only)
- ❌ Automated story generation from PRDs (future Epic 6+ consideration)
- ❌ Full CI/CD pipeline overhaul (Epic 2.5.4 complete, no gaps identified)

### 2.3 Success Criteria

Epic 3.5 is complete when:

1. ✅ All 7 stories delivered and passing quality gates (Black/Ruff/Mypy/pytest)
2. ✅ Story 4.1 (first Epic 4 story) uses new template generator successfully
3. ✅ Semantic dependencies smoke test passes in CI with <100ms TF-IDF baseline
4. ✅ Semantic QA fixtures repository contains ≥50 documents with gold annotations
5. ✅ Epic 4 developers can reference playbook/ADR without asking questions
6. ✅ Zero new technical debt items added to `docs/backlog.md`

---

## 3. Architecture & Design

### 3.1 Story/Review Template Architecture

**Components:**

```
scripts/
└── new-story                    # CLI entry point
    ├── templates/
    │   ├── story.md.j2          # Jinja2 story template
    │   ├── ac-table.md.j2       # AC evidence table template
    │   └── wiring-checklist.md.j2  # Integration checklist
    ├── generator.py             # Template rendering logic
    └── validators.py            # Pre-commit validation hooks
```

**Template Variables:**

- `{{story_id}}` - e.g., "3.5.1", "4.1"
- `{{story_title}}` - e.g., "Story Review Template Generator"
- `{{epic_id}}` - e.g., "Epic 3.5"
- `{{owner}}` - e.g., "Elena"
- `{{acceptance_criteria}}` - List of AC objects with ID, description, evidence fields

**Workflow:**

```bash
# Developer creates new story
scripts/new-story --id 4.1 --title "TF-IDF Vectorization Engine" --owner Charlie

# Generator outputs:
# - docs/stories/4-1-tf-idf-vectorization-engine.md (with AC table)
# - Pre-commit hook validates AC table completeness before commit
```

### 3.2 CLAUDE.md Lessons Section Structure

**Format:**

```markdown
## Lessons & Reminders (Epics 1-3)

### Story Development
- Always fill AC evidence table before changing status to "review"
- Include BOM (Bill of Materials) section for new dependencies
- Add structured logging for all pipeline stages (AC requirement)
- Wire CLI flags before marking story complete

### Code Quality
- Run `mypy src/data_extract/` from project root (not module subdirectory)
- Fix Black/Ruff/Mypy violations immediately (don't defer tech debt)
- Include integration tests for NFR validation (unit tests miss memory issues)
- Profile before optimizing (establish baselines first)

### Testing
- Mirror src/ structure exactly in tests/
- Use pytest markers for selective execution
- Coverage requirements: greenfield ≥80%, critical paths ≥90%
- Integration tests catch cross-module issues missed by unit tests

### Documentation
- ADRs are code - require owners and deadlines
- Update CLAUDE.md when adding new patterns
- Performance baselines go in docs/performance-baselines-epic-X.md
- Examples/samples in docs/examples/ for downstream teams
```

**Word Count**: Target ≤100 lines, actual ~60 lines

### 3.3 Semantic Dependencies Installation

**pyproject.toml Updates:**

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "scikit-learn>=1.3.0,<2.0.0",  # TF-IDF, LSA, cosine similarity
    "joblib>=1.3.0",                # Model persistence
    "textstat>=0.7.3",              # Readability metrics
]
```

**Smoke Test Script** (`scripts/smoke-test-semantic.py`):

```python
#!/usr/bin/env python3
"""Smoke test for semantic analysis dependencies."""

import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import textstat

def test_tfidf_performance():
    """Validate TF-IDF fit/transform <100ms on 1k-word document."""
    corpus = ["word " * 1000 for _ in range(10)]  # 10 docs, 1k words each

    start = time.perf_counter()
    vectorizer = TfidfVectorizer()
    vectorizer.fit(corpus)
    vectors = vectorizer.transform(corpus)
    duration_ms = (time.perf_counter() - start) * 1000

    assert duration_ms < 100, f"TF-IDF too slow: {duration_ms:.2f}ms > 100ms"
    print(f"✓ TF-IDF: {duration_ms:.2f}ms")

def test_lsa():
    """Validate LSA (TruncatedSVD) produces expected dimensionality."""
    # ... implementation ...
    print("✓ LSA: dimensionality reduction working")

def test_textstat():
    """Validate textstat readability metrics."""
    text = "The quick brown fox jumps over the lazy dog."
    score = textstat.flesch_reading_ease(text)
    assert 0 <= score <= 100
    print(f"✓ textstat: Flesch score = {score:.1f}")

if __name__ == "__main__":
    test_tfidf_performance()
    test_lsa()
    test_textstat()
    print("\n✅ All semantic dependencies validated")
```

**CI Integration** (`.github/workflows/test.yml`):

```yaml
- name: Install semantic dependencies
  run: |
    pip install -e ".[dev]"
    python scripts/smoke-test-semantic.py
```

### 3.4 Model/Cache ADR Structure

**ADR Template** (`docs/architecture/adr-012-semantic-model-cache.md`):

```markdown
# ADR-012: Semantic Model Cache & Persistence Strategy

## Context
Epic 4 semantic analysis requires caching TF-IDF vectorizers, LSA models,
and similarity matrices to avoid recomputation on every run. Models can be
large (10-100 MB for 10k-document corpus) and expensive to recompute.

## Decision
Use joblib for model persistence with hash-based cache invalidation.

**Cache Locations:**
- Development: `.data-extract-cache/models/` (gitignored)
- CI: `~/.cache/data-extract/models/` (GitHub Actions cache)
- Production: User-configurable via `DATA_EXTRACT_CACHE_DIR` env var

**Cache Keys:**
- TF-IDF: `tfidf_v{version}_{corpus_hash}.joblib`
- LSA: `lsa_v{version}_{corpus_hash}_{num_topics}.joblib`
- Similarity: `similarity_v{version}_{query_hash}_{corpus_hash}.joblib`

**Invalidation:**
- Hash corpus content with SHA-256
- Include model version in cache key
- CLI flag `--clear-cache` for manual invalidation

**Size Limits:**
- Max 500 MB total cache size
- LRU eviction when limit exceeded
- Warning logged when cache >80% full

## Consequences
- Positive: 10-100x speedup on repeated analysis (0.1s vs. 10s for TF-IDF fit)
- Positive: Deterministic model versioning prevents drift
- Negative: Disk usage increases (mitigated by size limits)
- Negative: Cache invalidation complexity (mitigated by hash-based keys)

## Alternatives Considered
- SQLite cache: Overkill for simple key-value storage
- No caching: Unacceptable performance for batch processing
- In-memory only: Requires recomputation on every CLI invocation
```

### 3.5 Semantic QA Fixtures Repository

**Structure:**

```
tests/fixtures/semantic/
├── corpus/
│   ├── audit-reports/          # 20 audit documents
│   ├── risk-matrices/          # 15 risk assessment docs
│   ├── compliance-docs/        # 15 regulatory documents
│   └── metadata.json           # Corpus statistics
├── gold-standard/
│   ├── tfidf-expected.json     # Expected TF-IDF vectors
│   ├── lsa-expected.json       # Expected LSA topics
│   └── entities-expected.json  # Gold-standard entity annotations
├── harness/
│   ├── compare-tfidf.py        # TF-IDF regression test
│   ├── compare-lsa.py          # LSA regression test
│   └── compare-entities.py     # Entity extraction regression test
└── README.md                   # Corpus documentation
```

**Corpus Requirements:**

- ≥50 documents total
- ≥250,000 words total
- Covers 3+ document types (audit reports, risk matrices, compliance)
- PII sanitized (no real names, SSNs, account numbers)
- Representative of production audit document characteristics

**Gold-Standard Annotations:**

```json
{
  "document_id": "audit-001.pdf",
  "entities": [
    {"type": "RISK", "text": "RISK-001", "start": 127, "end": 135},
    {"type": "CONTROL", "text": "CTRL-042", "start": 458, "end": 466}
  ],
  "tfidf_top_terms": ["audit", "compliance", "risk", "control", "assessment"],
  "lsa_primary_topic": 2,
  "readability_score": 45.3
}
```

### 3.6 TF-IDF/LSA Playbook Structure

**Jupyter Notebook** (`docs/playbooks/semantic-analysis-intro.ipynb`):

**Cells:**

1. **Introduction** - Classical NLP overview, enterprise constraints (no transformers)
2. **TF-IDF Basics** - Vectorization, vocabulary, IDF weighting
3. **LSA Basics** - Dimensionality reduction, topic extraction, TruncatedSVD
4. **Similarity Scoring** - Cosine similarity, top-k retrieval
5. **Joblib Persistence** - Saving/loading models, cache patterns
6. **Tuning & Best Practices** - Vocabulary size, n-grams, stopwords, stemming
7. **Performance Considerations** - Batch processing, memory limits, sparse matrices
8. **Examples** - Real corpus analysis with visualizations

**Companion Markdown** (`docs/playbooks/semantic-analysis-reference.md`):

- Quick reference for TF-IDF/LSA APIs
- Common pitfalls (vocabulary drift, cache invalidation)
- Troubleshooting guide
- Links to scikit-learn docs

---

## 4. Story Breakdown

| Story ID | Title | Owner | Dependencies |
|----------|-------|-------|--------------|
| 3.5.1 | Story/Review Template Generator | Elena | None |
| 3.5.2 | CLAUDE.md Lessons Section | Bob | Epic 1-3 retros |
| 3.5.3 | Test Dependency Audit Documentation | Winston | Epic 2.5 examples |
| 3.5.4 | Semantic Dependencies + Smoke Test | Charlie | None |
| 3.5.5 | Model/Cache ADR | Winston | Story 3.5.4 |
| 3.5.6 | Semantic QA Fixtures | Dana | Story 3.5.4 |
| 3.5.7 | TF-IDF/LSA Playbook | Charlie + Elena | Story 3.5.4, 3.5.6 |

**Critical Path**: 3.5.4 → 3.5.5/3.5.6 → 3.5.7

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Requirement | Target | Validation |
|-------------|--------|------------|
| **NFR-P1**: TF-IDF fit/transform latency | <100ms per 1k-word document | Smoke test script |
| **NFR-P2**: LSA fit/transform latency | <200ms per 1k-word document | Smoke test script |
| **NFR-P3**: Textstat scoring latency | <10ms per 1k-word document | Smoke test script |
| **NFR-P4**: Cache write/read latency | <50ms for 10 MB model | Integration test |

### 5.2 Quality

| Requirement | Target | Validation |
|-------------|--------|------------|
| **NFR-Q1**: Code quality gates | Black/Ruff/Mypy 0 violations | Pre-commit + CI |
| **NFR-Q2**: Test coverage | ≥80% for new semantic utils | pytest --cov |
| **NFR-Q3**: Documentation completeness | All 7 stories have AC tables + evidence | Template validator |
| **NFR-Q4**: Semantic corpus quality | ≥50 docs, ≥250k words, PII-free | Fixture validation script |

### 5.3 Usability

| Requirement | Target | Validation |
|-------------|--------|------------|
| **NFR-U1**: Template generator CLI | <5 min to create new story | Manual test |
| **NFR-U2**: Playbook readability | Junior dev understands TF-IDF in <30 min | QA review |
| **NFR-U3**: ADR discoverability | Findable via `docs/architecture/` | File naming convention |

---

## 6. Dependencies & Prerequisites

### 6.1 Epic Dependencies

**Depends On:**
- ✅ Epic 3 (complete) - Chunk metadata provides input for semantic analysis
- ✅ Epic 2.5 (complete) - CI/CD infrastructure, quality gates established
- ✅ Epic 1 (complete) - Project infrastructure, testing framework

**Blocks:**
- ⚠️ Epic 4 (Semantic Analysis) - Cannot start without semantic dependencies + QA fixtures

### 6.2 Library Dependencies

**New Dependencies:**

```toml
scikit-learn = ">=1.3.0,<2.0.0"  # TF-IDF, LSA, cosine similarity
joblib = ">=1.3.0"                # Model persistence
textstat = ">=0.7.3"              # Readability metrics
```

**Existing Dependencies:**
- pytest (testing)
- black, ruff, mypy (quality gates)
- Jinja2 (template rendering)

### 6.3 Data Dependencies

**Required:**
- Epic 1-3 retrospective documents (action plan source)
- Epic 2.5 spaCy integration examples (test dependency audit template)
- Audit document samples (semantic corpus - may require sourcing/generation)

**Optional:**
- Existing test fixtures from `tests/fixtures/` (reusable for semantic tests)

---

## 7. Acceptance Criteria (Epic-Level)

| AC ID | Description | Validation |
|-------|-------------|------------|
| **AC-3.5-1** | Story template generator creates valid markdown with AC tables, wiring checklists, submission summaries | `scripts/new-story --id 4.1 ...` outputs valid story file |
| **AC-3.5-2** | CLAUDE.md contains ≤100-line "Lessons & Reminders" section consolidating Epic 1-3 learnings | Section exists, word count ≤100 lines, referenced by scripts |
| **AC-3.5-3** | Test dependency audit process doc exists with automated checklist hook | `docs/processes/test-dependency-audit.md` committed, hook functional |
| **AC-3.5-4** | Semantic dependencies installed and smoke tested with <100ms TF-IDF baseline | `scripts/smoke-test-semantic.py` passes in CI |
| **AC-3.5-5** | Model/cache ADR defines storage paths, versioning, CLI integration, size limits | ADR-012 committed, reviewed by architect |
| **AC-3.5-6** | Semantic QA fixtures contain ≥50 documents with gold annotations for TF-IDF/LSA/entities | `tests/fixtures/semantic/corpus/` validated |
| **AC-3.5-7** | TF-IDF/LSA playbook (Jupyter notebook + markdown) enables junior devs to understand patterns in <30 min | Playbook reviewed by QA, feedback positive |
| **AC-3.5-8** | Zero new technical debt items added during Epic 3.5 | `docs/backlog.md` unchanged or items closed |

---

## 8. Traceability Matrix

### 8.1 Retrospective → Stories

| Retrospective Item | Type | Story |
|--------------------|------|-------|
| Action #1: Story/review template generator | Action Plan | 3.5.1 |
| Action #2: CLAUDE.md lessons section | Action Plan | 3.5.2 |
| Action #3: Test dependency audit doc | Action Plan | 3.5.3 |
| Prep Task #1: scikit-learn + smoke test | Prep Sprint | 3.5.4 |
| Prep Task #2: Model/cache ADR | Prep Sprint | 3.5.5 |
| Prep Task #3: Semantic QA fixtures | Prep Sprint | 3.5.6 |
| Prep Task #4: TF-IDF/LSA playbook | Prep Sprint | 3.5.7 |

### 8.2 Epic 4 Blockers → Stories

| Epic 4 Blocker | Resolved By |
|----------------|-------------|
| Missing scikit-learn/textstat | Story 3.5.4 |
| No TF-IDF/LSA performance baselines | Story 3.5.4, 3.5.7 |
| No semantic test corpus | Story 3.5.6 |
| No model cache strategy | Story 3.5.5 |
| Junior devs lack semantic context | Story 3.5.7 |
| Missing story quality enforcement | Story 3.5.1 |
| Incomplete dependency audit process | Story 3.5.3 |

---

## 9. Risks & Mitigations

| Risk ID | Description | Probability | Impact | Mitigation |
|---------|-------------|-------------|--------|------------|
| **R-3.5-1** | Semantic corpus unavailable (no real audit docs) | Medium | High | Generate synthetic docs + validate with domain expert |
| **R-3.5-2** | TF-IDF baseline exceeds 100ms (large corpus) | Low | Medium | Profile and optimize, or adjust baseline |
| **R-3.5-3** | Template generator over-engineered (scope creep) | Medium | Low | Limit to Jinja2 + basic validation, defer advanced features |
| **R-3.5-4** | Playbook too advanced for junior devs | Low | Medium | QA review for readability, simplify examples |
| **R-3.5-5** | Cache ADR conflicts with Epic 5 config system | Low | Medium | Coordinate with Epic 5 architect, align on paths |

---

## 10. Implementation Strategy

### 10.1 Phases

**Phase 1: Process/Tooling (Stories 3.5.1-3.5.3) - Day 1**

- Parallel execution: Elena (3.5.1), Bob (3.5.2), Winston (3.5.3)
- No cross-dependencies, can run concurrently
- Unblocks story quality enforcement for Epic 4

**Phase 2: Semantic Dependencies (Story 3.5.4) - Day 1-2**

- Charlie installs libraries, writes smoke test
- Blocks Phase 3 (cannot write ADR/fixtures without validated dependencies)
- Critical path item

**Phase 3: Semantic Infrastructure (Stories 3.5.5-3.5.7) - Day 2-3**

- Winston writes ADR (3.5.5) in parallel with Dana creating fixtures (3.5.6)
- Charlie + Elena write playbook (3.5.7) after fixtures available for examples
- Sequential: 3.5.4 → (3.5.5 || 3.5.6) → 3.5.7

### 10.2 Quality Gates (Per Story)

**RED Phase** (TDD):
1. Write failing tests for story requirements
2. Verify tests fail as expected

**GREEN Phase** (Implementation):
1. Implement minimum code to pass tests
2. Run pytest suite (target: all tests pass)

**BLUE Phase** (Refinement):
1. Run Black/Ruff/Mypy (target: 0 violations)
2. Add integration tests if needed
3. Update documentation (ADRs, CLAUDE.md, README)
4. Peer review

**DONE Criteria**:
- ✅ All tests pass (pytest)
- ✅ Quality gates green (Black/Ruff/Mypy)
- ✅ AC evidence table filled
- ✅ Documentation updated
- ✅ Peer review approved

---

## 11. Test Strategy

### 11.1 Story-Level Testing

| Story | Test Type | Coverage Target | Key Tests |
|-------|-----------|-----------------|-----------|
| 3.5.1 | Unit + Integration | ≥80% | Template rendering, CLI args, file output, validation hooks |
| 3.5.2 | Manual Review | N/A | Readability, completeness, referenced by scripts |
| 3.5.3 | Manual Review | N/A | Process clarity, examples accuracy, hook functionality |
| 3.5.4 | Integration | ≥70% | TF-IDF smoke test, LSA smoke test, textstat smoke test, CI integration |
| 3.5.5 | Manual Review | N/A | ADR clarity, technical accuracy, stakeholder alignment |
| 3.5.6 | Unit + Integration | ≥80% | Corpus validation (doc count, word count, PII check), gold-standard comparison harness |
| 3.5.7 | Manual Review | N/A | Playbook readability, code examples execute, junior dev feedback |

### 11.2 Epic-Level Testing

**Integration Tests:**
1. **End-to-End Story Creation**: Run `scripts/new-story`, verify output, commit, validate pre-commit hook
2. **Semantic Pipeline Smoke Test**: Fit TF-IDF → transform → LSA → similarity scoring on real corpus
3. **Cache Persistence**: Save model → clear memory → load model → verify identical output

**Performance Tests:**
1. TF-IDF baseline: 1k-word doc <100ms
2. LSA baseline: 1k-word doc <200ms
3. Textstat baseline: 1k-word doc <10ms

**Regression Tests:**
1. Existing Epic 1-3 tests still pass (no brownfield breakage)
2. Pre-commit hooks don't block valid commits

---

## 12. Definition of Done (Epic)

Epic 3.5 is **DONE** when:

### 12.1 Code Complete
- ✅ All 7 stories implemented and committed
- ✅ All quality gates pass (Black/Ruff/Mypy 0 violations)
- ✅ All tests pass (pytest suite green)

### 12.2 Documentation Complete
- ✅ CLAUDE.md "Lessons & Reminders" section added (≤100 lines)
- ✅ Test dependency audit process doc (`docs/processes/test-dependency-audit.md`)
- ✅ Model/cache ADR (`docs/architecture/adr-012-semantic-model-cache.md`)
- ✅ TF-IDF/LSA playbook (`docs/playbooks/semantic-analysis-intro.ipynb`)
- ✅ All 7 story files have AC tables filled with evidence

### 12.3 Infrastructure Validated
- ✅ Semantic dependencies smoke test passes in CI
- ✅ Semantic QA fixtures validated (≥50 docs, ≥250k words, PII-free)
- ✅ Template generator creates valid story files
- ✅ Pre-commit hooks enforce story quality standards

### 12.4 Epic 4 Unblocked
- ✅ Story 4.1 can use template generator successfully
- ✅ Semantic libraries installed and performance baselined
- ✅ QA fixtures available for TF-IDF/LSA regression tests
- ✅ Playbook/ADR referenced by Epic 4 developers

### 12.5 Retrospective Complete
- ✅ Epic 3.5 retrospective document created
- ✅ Action items tracked (or marked "not applicable" for bridge epics)
- ✅ Lessons learned documented in CLAUDE.md

---

## 13. Appendix

### 13.1 References

**Retrospective Documents:**
- `docs/retrospectives/epic-3-retro-2025-11-16.md` (source of action plan)
- `docs/retrospectives/epic-2-retro-*.md` (dependency audit examples)
- `docs/retrospectives/epic-1-retro-*.md` (lessons learned)

**Related Specs:**
- `docs/tech-spec-epic-1.md` (project foundation)
- `docs/archive/tech-spec-epic-2.5.md` (bridge epic pattern)
- `docs/PRD/index.md` (product vision)

**Architecture Docs:**
- `docs/architecture.md` (ADR repository)
- `docs/CLAUDE.md` (development guidelines)

### 13.2 Glossary

- **Bridge Epic**: Short infrastructure/process epic between feature epics
- **Smoke Test**: Basic validation that a library/feature is functional
- **Gold-Standard**: Manually validated expected outputs for regression testing
- **AC Table**: Acceptance Criteria evidence table embedded in story docs
- **TF-IDF**: Term Frequency-Inverse Document Frequency (vectorization algorithm)
- **LSA**: Latent Semantic Analysis (dimensionality reduction for topics)

### 13.3 Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-17 | 1.0 | Initial tech spec created from Epic 3 retrospective | Claude |

---

**Epic Owner Approval**: _Pending_
**Architect Review**: _Pending_
**Stakeholder Sign-Off**: _Pending_

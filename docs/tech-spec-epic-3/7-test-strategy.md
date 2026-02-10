# 7. Test Strategy

## 7.1 Test Strategy Overview

Epic 3 test strategy follows the approved 10-step UAT workflow and Murat's hybrid benchmarking approach, balancing comprehensive coverage with efficient execution.

**Strategic Principles:**
1. **Shift-Left Testing**: Run pre-commit hooks (0 violations gate) before CI
2. **Hybrid Benchmarking**: Measure critical paths (Stories 3-1, 3-4/5/6, 3-7), skip negligible overhead (Stories 3-2, 3-3)
3. **UAT Selective Application**: Not all ACs require UAT (see Section 5.1)
4. **Dev-Driven Test Execution**: Dev runs automated tests + manual UAT, SM reviews results
5. **Performance Baseline Tracking**: Document in `docs/performance-baselines-epic-3.md` (created Story 3-1)

## 7.2 Test Categories and Coverage

### Unit Tests (~79 tests)

**Scope:** Component-level logic, edge cases, data model validation

**Coverage Requirements:**
- All public methods in ChunkingEngine, EntityPreserver, MetadataEnricher
- All output formatters (JsonFormatter, TxtFormatter, CsvFormatter)
- All data models (Chunk, ChunkMetadata, QualityScore, EntityReference)
- Edge cases: very long sentences, short sections, empty entities, malformed metadata

**Test Organization:**
```
tests/unit/test_chunk/
├── test_engine.py              # ChunkingEngine tests (15 tests)
├── test_entity_preserver.py    # EntityPreserver tests (12 tests)
├── test_metadata.py            # MetadataEnricher tests (18 tests)
└── test_models.py              # Data model tests (5 tests)

tests/unit/test_output/
├── test_json_formatter.py      # JsonFormatter tests (10 tests)
├── test_txt_formatter.py       # TxtFormatter tests (8 tests)
├── test_csv_formatter.py       # CsvFormatter tests (9 tests)
└── test_organization.py        # Organizer tests (7 tests)
```

**Key Unit Test Patterns:**

```python
# Example: ChunkingEngine determinism test
def test_chunking_determinism():
    """Verify same input produces identical chunks (NFR-P4)."""
    engine = ChunkingEngine(segmenter=mock_segmenter)

    # Process same document 10 times
    results = [
        list(engine.chunk_document(processing_result))
        for _ in range(10)
    ]

    # All runs should produce identical chunks
    for i in range(1, 10):
        assert results[i] == results[0], "Chunking must be deterministic"

# Example: Entity preservation test
def test_entity_preservation_rate():
    """Verify >95% entities kept intact within chunks (AC-3.2-1)."""
    preserver = EntityPreserver()
    entities = create_test_entities(count=100)

    chunks = list(engine.chunk_document(processing_result_with_entities))

    preserved = sum(1 for e in entities if entity_intact_in_chunk(e, chunks))
    preservation_rate = preserved / len(entities)

    assert preservation_rate >= 0.95, f"Only {preservation_rate:.1%} entities preserved"
```

### Integration Tests (~48 tests)

**Scope:** Multi-component workflows, end-to-end processing, Epic 2 → Epic 3 integration

**Coverage Requirements:**
- Full pipeline: ProcessingResult → Chunks → Enriched Chunks → Outputs
- All output organization strategies (by_document, by_entity, flat)
- Error handling and graceful degradation
- Parallel output write coordination

**Test Organization:**
```
tests/integration/test_pipeline/
├── test_chunking_pipeline.py       # Epic 2 → Epic 3 integration (8 tests)
├── test_output_pipeline.py         # Chunking → Output formats (10 tests)
├── test_organization_strategies.py # All 3 organization modes (9 tests)
└── test_error_handling.py          # Continue-on-error, degradation (6 tests)

tests/integration/test_formats/
├── test_json_integration.py        # JSON output validation (5 tests)
├── test_txt_integration.py         # TXT output validation (4 tests)
└── test_csv_integration.py         # CSV output validation (6 tests)
```

**Key Integration Test Patterns:**

```python
# Example: Full pipeline integration test
def test_epic2_to_epic3_pipeline():
    """Verify Epic 2 output flows correctly through Epic 3 chunking."""
    # Epic 2 output (normalized document)
    processing_result = normalize_document(sample_pdf)

    # Epic 3 chunking
    engine = ChunkingEngine(segmenter=SentenceSegmenter())
    chunks = list(engine.chunk_document(processing_result))

    # Verify chunks preserve Epic 2 metadata
    assert all(c.metadata.source_file == processing_result.source_file for c in chunks)
    assert all(c.entities <= processing_result.entities for c in chunks)  # Subset

    # Verify output generation succeeds
    writer = ParallelWriter()
    results = writer.write_all_formats(iter(chunks), output_dir)

    assert results["json"].chunk_count == len(chunks)
    assert results["txt"].chunk_count == len(chunks)
    assert results["csv"].chunk_count == len(chunks)

# Example: Organization strategy integration test
def test_by_entity_organization():
    """Verify by_entity strategy groups chunks correctly (AC-3.7-3)."""
    chunks = create_test_chunks_with_entities()  # Mix of risks, controls, policies

    organizer = Organizer()
    manifest_path = organizer.organize(
        chunks,
        output_dir,
        OrganizationStrategy.BY_ENTITY
    )

    # Verify directory structure
    assert (output_dir / "risks").exists()
    assert (output_dir / "controls").exists()
    assert (output_dir / "policies").exists()

    # Verify traceability
    manifest = json.loads(manifest_path.read_text())
    for chunk_id, metadata in manifest["chunks"].items():
        assert metadata["source_file"] in manifest["sources"]
```

### Performance Tests (~5 tests)

**Scope:** NFR validation, baseline establishment, regression detection

**Coverage Requirements:**
- NFR-P1-E3: <10 min for 100 PDFs (epic-end integration test)
- NFR-P2-E3: <5.5GB memory for batch (memory profiling)
- NFR-P3: <2 sec per 10k words chunking (Story 3-1 baseline)
- NFR-P4: 100% determinism (repeated runs)
- Output format overhead (Stories 3-4/5/6)

**Test Organization:**
```
tests/performance/
├── test_chunking_performance.py    # Story 3-1 baseline (NFR-P3)
├── test_output_performance.py      # Stories 3-4/5/6 overhead
├── test_memory_profiling.py        # NFR-P2-E3 validation
├── test_determinism.py             # NFR-P4 validation
└── test_epic_integration.py        # NFR-P1-E3 full pipeline
```

**Performance Baseline Tracking:**

All performance tests log results to `docs/performance-baselines-epic-3.md`:

```markdown
# Epic 3 Performance Baselines

# Story 3-1: Chunking Engine Baseline
- **Date:** 2025-11-15
- **Test Corpus:** 100 PDFs, 800,000 words total
- **Chunking Time:** 1.23 minutes (82.5 seconds)
- **Per-Document:** 0.825 seconds average
- **Per-10k-Words:** 1.03 seconds ✅ (target: <2 seconds)
- **Memory Usage:** 342MB peak ✅ (target: <500MB)

# Story 3-4/5/6: Output Format Overhead
- **JSON Generation:** 0.42 minutes (25.2 seconds)
- **TXT Generation:** 0.31 minutes (18.6 seconds)
- **CSV Generation:** 0.38 minutes (22.8 seconds)
- **Parallel Total:** 0.47 minutes (28.2 seconds) ✅ (target: <1 minute)
- **Speedup:** 2.9x vs sequential (25.2 + 18.6 + 22.8 = 66.6 seconds)

# Epic-End Integration Test
- **Full Pipeline:** 9.12 minutes ✅ (target: <10 minutes)
  - Extract + Normalize: 6.86 minutes (Epic 2 baseline)
  - Chunking: 1.23 minutes
  - Metadata Enrichment: 0.56 minutes
  - Output Generation: 0.47 minutes
- **Memory Peak:** 5.31GB ✅ (target: <5.5GB)
```

**Hybrid Benchmarking Strategy (Murat):**

| Story | Benchmark | Rationale |
|-------|-----------|-----------|
| 3-1 | Full benchmark (chunking critical path) | Establishes baseline, validates NFR-P3 |
| 3-2 | Skip micro-benchmark | Entity analysis overhead <0.1s per doc (negligible) |
| 3-3 | Skip micro-benchmark | Metadata enrichment overhead <0.1s per doc (negligible) |
| 3-4 | Benchmark JSON generation | Measures output format overhead |
| 3-5 | Benchmark TXT generation | Measures output format overhead |
| 3-6 | Benchmark CSV generation | Measures output format overhead |
| 3-7 | Benchmark organization | Measures file organization overhead |
| Epic-end | Full integration benchmark | Validates NFR-P1-E3 (<10 min target) |

### UAT Tests (~25 manual/automated validations)

**Scope:** End-user workflows, format validation, downstream tool integration

**Coverage Requirements:**
- Manual review of 20 sample chunks (semantic coherence, quality)
- LLM upload testing (ChatGPT/Claude) - Story 3-5 critical UAT
- Excel/Google Sheets import - Story 3-6 critical UAT
- JSON schema validation - Story 3-4 critical UAT
- Organization strategy correctness - Story 3-7 critical UAT

**UAT Execution Method:**

**Automated UAT (pytest + tmux-cli for CLI tests):**
```bash
# SM runs workflow (after Dev marks story ready-for-review)
/bmad:bmm:workflows:create-test-cases story_key=3-1
/bmad:bmm:workflows:build-test-context story_key=3-1

# Dev executes UAT tests
/bmad:bmm:workflows:execute-tests test_execution_mode=hybrid

# Example tmux-cli test for Story 3-5 (TXT format LLM upload)
tmux-cli launch "bash"
tmux-cli send "data-extract process sample.pdf --format txt --organization flat" --pane=2
tmux-cli wait_idle --pane=2 --idle-time=2.0
tmux-cli capture --pane=2  # Verify output path

# Manual step: Upload output/sample_chunk_001.txt to ChatGPT
# Verify: No formatting artifacts, chunks readable, context preserved
```

**Manual UAT (SM-driven review):**
1. **Sample chunk review** (Story 3-1, 3-2): Read 20 chunks, assess semantic coherence
2. **LLM upload test** (Story 3-5): Upload TXT chunks to ChatGPT/Claude, verify usability
3. **Spreadsheet import** (Story 3-6): Import CSV to Excel/Sheets, verify no corruption
4. **Organization validation** (Story 3-7): Inspect output directory structure, verify traceability

**UAT Pass/Fail Criteria:**
- **90% pass rate overall** (approved in party-mode discussion)
- **100% pass rate for critical ACs** (marked "Yes - Critical" in Section 5.1)
- **Manual review**: <10% chunks flagged as incoherent
- **LLM upload**: Chunks usable without post-processing
- **Spreadsheet import**: All rows import correctly, no escaping issues

## 7.3 Quality Gates

Epic 3 enforces three quality gates aligned with the 10-step UAT workflow:

### Gate 1: Pre-Commit (0 Violations)

**Trigger:** Before `git commit` (automated via pre-commit hooks)

**Checks:**
```bash
# Formatting (black)
black --line-length 100 src/ tests/

# Linting (ruff)
ruff check src/ tests/

# Type checking (mypy) - strict mode, excludes brownfield
mypy src/data_extract/
```

**Pass Criteria:**
- Black: 0 formatting violations
- Ruff: 0 linting violations
- Mypy: 0 type errors (in greenfield code)

**Enforcement:** Pre-commit hook blocks commit if violations detected

### Gate 2: CI (60% Coverage)

**Trigger:** On push to main or PR creation (GitHub Actions)

**Checks:**
```yaml
# .github/workflows/ci.yml
- name: Run tests with coverage
  run: |
    pytest --cov=src --cov-report=term-missing --cov-fail-under=60

- name: Run performance regression tests
  run: |
    pytest tests/performance/ -v --benchmark-compare
```

**Pass Criteria:**
- All unit tests pass (pytest exit code 0)
- All integration tests pass
- Code coverage ≥60% (aggregate greenfield + brownfield)
- Performance regression <10% vs baseline

**Enforcement:** CI blocks merge if tests fail or coverage <60%

### Gate 3: UAT (90% Pass Rate)

**Trigger:** After Dev marks story "ready-for-review"

**Workflow:**
1. SM creates test cases (`/bmad:bmm:workflows:create-test-cases`)
2. SM builds test context (`/bmad:bmm:workflows:build-test-context`)
3. Dev executes tests (`/bmad:bmm:workflows:execute-tests`)
4. SM reviews results (`/bmad:bmm:workflows:review-uat-results`)

**Pass Criteria:**
- 90% test pass rate overall
- 100% critical ACs pass (marked "Yes - Critical" in Section 5.1)
- Manual review: <10% chunks flagged as problematic
- No blocking issues (format validation, downstream tool compatibility)

**Enforcement:** SM approves/requests changes, story marked DONE or returned to Dev

## 7.4 Test Data and Fixtures

### Test Corpus Requirements

**Sample Documents (Sanitized Audit Docs):**
- 10 PDFs (diverse types: reports, matrices, exports)
- 5 Word documents (with tables, headings, entity mentions)
- 3 Excel files (control matrices, risk registers)
- 2 PowerPoint files (audit presentations)

**Total Size:** <100MB (stored in `tests/fixtures/`)

**Entity Coverage:**
- At least 50 entity mentions across 6 types (processes, risks, controls, regulations, policies, issues)
- At least 10 entity relationships (e.g., "Risk X mitigated by Control Y")
- Mix of simple and complex entity definitions

**Edge Cases:**
- Very long sentence (>100 words)
- Very short section (<50 words)
- Document with no entities
- Document with 100+ entities
- Malformed metadata (missing fields)

**Synthetic Data Generation:**

```python
# tests/fixtures/generate_test_data.py
def generate_audit_report(
    num_sections: int = 5,
    words_per_section: int = 500,
    entity_density: float = 0.1  # 10% of sentences mention entities
) -> str:
    """Generate synthetic audit report for testing."""
    # Uses reportlab to create PDF with realistic structure
```

**Regeneration Script:**
```bash
# Recreate test fixtures from scratch
python tests/fixtures/generate_test_data.py --output tests/fixtures/

# Verify fixtures
pytest tests/test_fixtures.py -v
```

## 7.5 Test Execution Workflow

### Local Development (Dev)

```bash
# 1. Run tests during development
pytest tests/unit/test_chunk/test_engine.py -v

# 2. Run all unit tests
pytest tests/unit/ -v

# 3. Run integration tests
pytest tests/integration/ -v

# 4. Run with coverage
pytest --cov=src --cov-report=html

# 5. Run pre-commit checks before commit
pre-commit run --all-files

# 6. Commit only if pre-commit passes
git add .
git commit -m "feat(chunk): implement ChunkingEngine"
```

### CI Execution (Automated)

```yaml
# .github/workflows/ci.yml (excerpt)
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          python -m spacy download en_core_web_md

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Run performance tests
        run: pytest tests/performance/ -v --benchmark-only

      - name: Check coverage threshold
        run: coverage report --fail-under=60

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

### UAT Execution (Dev + SM)

**Dev Workflow:**
```bash
# After completing Story 3-1 implementation

# 1. Run pre-commit
pre-commit run --all-files  # Must pass (0 violations)

# 2. Push to CI
git push origin story-3-1

# 3. Verify CI passes
# (GitHub Actions runs automatically)

# 4. Mark story ready for review
# Update docs/sprint-status.yaml: story-3-1: in_progress → ready_for_review

# 5. Notify SM
# SM creates test cases and builds test context

# 6. Execute UAT tests (when SM ready)
/bmad:bmm:workflows:execute-tests story_key=3-1 test_execution_mode=hybrid

# 7. Review results
cat docs/uat/test-results/3-1-test-results.md

# 8. Fix issues if needed, re-run UAT
# Otherwise, wait for SM approval
```

**SM Workflow:**
```bash
# After Dev marks story ready-for-review

# 1. Create test cases
/bmad:bmm:workflows:create-test-cases story_key=3-1
# Generates: docs/uat/test-cases/3-1-test-cases.md

# 2. Build test context
/bmad:bmm:workflows:build-test-context story_key=3-1
# Generates: docs/uat/test-context/3-1-test-context.xml

# 3. Notify Dev to execute tests
# Dev runs /bmad:bmm:workflows:execute-tests

# 4. Review UAT results
/bmad:bmm:workflows:review-uat-results story_key=3-1 quality_gate_level=standard
# Generates: docs/uat/reviews/3-1-uat-review.md

# 5. Approve or request changes
# If approved: Update docs/sprint-status.yaml: story-3-1: ready_for_review → done
# If changes needed: Return to Dev with feedback
```

## 7.6 Performance Baseline Documentation

All performance measurements documented in `docs/performance-baselines-epic-3.md`:

**Template:**
```markdown
# Epic 3 Performance Baselines

**Created:** 2025-11-15
**Last Updated:** 2025-11-20
**Status:** Baseline established, tracking ongoing

# Baseline Environment
- **Hardware:** 16GB RAM, 8-core CPU (Intel i7 or equivalent)
- **OS:** Windows 11 / Ubuntu 22.04
- **Python:** 3.12.1
- **Dependencies:** spaCy 3.7.2, textstat 0.7.3

# Story 3-1: Chunking Engine Baseline
[Measurements from test_chunking_performance.py]

# Stories 3-4/5/6: Output Format Overhead
[Measurements from test_output_performance.py]

# Story 3-7: Organization Overhead
[Measurements from test_organization_performance.py]

# Epic-End Integration Test
[Measurements from test_epic_integration.py]

# Performance Regression Log
| Date | Story | Metric | Baseline | Current | Delta | Status |
|------|-------|--------|----------|---------|-------|--------|
| 2025-11-20 | 3-1 | Chunking time | 82.5s | 85.2s | +3.3% | ✅ Pass (<10% regression) |
| 2025-11-21 | 3-4 | JSON generation | 25.2s | 26.1s | +3.6% | ✅ Pass |
```

## 7.7 Test Strategy Summary

| Test Type | Count | Coverage | Automation | Owner | Quality Gate |
|-----------|-------|----------|------------|-------|--------------|
| Unit | ~79 | Component logic, edge cases | 100% automated (pytest) | Dev | Pre-commit |
| Integration | ~48 | Multi-component workflows | 100% automated (pytest) | Dev | CI |
| Performance | ~5 | NFR validation, baselines | 100% automated (pytest + profiling) | Dev | CI |
| UAT | ~25 | End-user workflows, manual review | 60% automated, 40% manual | Dev executes, SM reviews | UAT (90% pass) |
| **Total** | **~157** | **Epic 3 complete coverage** | **85% automated** | **Dev + SM** | **3-gate process** |

**Test Strategy Alignment:**
- ✅ Shift-left: Pre-commit enforced before CI
- ✅ Hybrid benchmarking: Critical paths measured, micro-benchmarks skipped
- ✅ Selective UAT: Only critical ACs require manual validation
- ✅ Dev-driven execution: Dev runs tests, SM reviews results
- ✅ Continuous tracking: Performance baselines documented and monitored

---

**Epic 3 Technical Specification - Complete**

**Document Version:** 1.0
**Status:** Ready for Story Generation
**Created:** 2025-11-13
**Last Updated:** 2025-11-13
**Approved By:** User (Section 1), Party-Mode Discussion (Operational Requirements)

**Next Steps:**
1. Update `docs/sprint-status.yaml`: epic-3 status from `backlog` → `contexted`
2. Generate individual stories using `/bmad:bmm:workflows:create-story` workflow
3. Begin Story 3-1 implementation (Semantic Boundary-Aware Chunking Engine)

# Test Remediation - Quick Start Guide

**Goal**: 100% Test Pass Rate (929/929 tests)
**Current**: 872/929 passing (93.9%)
**Timeline**: 12-15 hours (wall time with parallelization)

---

## TL;DR

**3 parallel workstreams** → **20 tests fixed** → **100% coverage achieved**

```
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ npl-integrator  │  │  npl-tdd-builder │  │  npl-validator  │
│                 │  │                  │  │                 │
│ • TXT Pipeline  │  │ • ChunkedText    │  │ • Quality       │
│   (3 tests)     │  │   Formatter      │  │   Scoring       │
│ • QV Pipeline   │  │   (7 tests)      │  │   (8 tests)     │
│   (2 tests)     │  │                  │  │                 │
└─────────────────┘  └──────────────────┘  └─────────────────┘
        ↓                    ↓                      ↓
    5-7 hours            8-12 hours             6-8 hours
        └────────────────────┴──────────────────────┘
                             ↓
                  ┌──────────────────────┐
                  │  Integration Test    │
                  │     (3-5 hours)      │
                  └──────────────────────┘
                             ↓
                  ✅ 100% Test Coverage
```

---

## Phase 1: Agent Assignments (DO THIS FIRST)

### Assign Agents to Workstreams

**Option A: 3 Agents (Fastest - 12-15 hours wall time)**
```
Agent 1 (@npl-integrator): Workstreams 1A + 1B (both pipeline integrations)
Agent 2 (@npl-tdd-builder): Workstream 2 (ChunkedTextFormatter)
Agent 3 (@npl-validator + @npl-thinker): Workstream 3 (QualityValidator)
```

**Option B: 2 Agents (Medium - 18-22 hours wall time)**
```
Agent 1 (@npl-integrator): Workstreams 1A + 1B
Agent 2 (@npl-tdd-builder + @npl-validator): Workstreams 2 + 3 (sequential)
```

**Option C: 1 Agent (Slowest - 19-27 hours wall time)**
```
Agent 1: All workstreams sequentially
```

**Recommendation**: **Option A** (3 agents, fully parallelized)

---

## Phase 2: Execution Commands

### Agent 1: npl-integrator

**Start Here**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"

# Read orchestration plan
cat docs/planning/v1_0_6-planning/TEST_REMEDIATION_ORCHESTRATION_PLAN.md | grep -A 200 "AGENT 1: npl-integrator"

# Workstream 1A: TXT Pipeline (2.5 hours)
# Step 1: Reproduce failures
python -m pytest tests/integration/test_end_to_end.py -k "txt" -v

# Step 2: Check TXT extractor export
cat src/extractors/__init__.py | grep TextFileExtractor

# Step 3: Register in CLI (add after line ~50 where other extractors registered)
# Edit: src/cli/main.py
# Add: from src.extractors import TextFileExtractor
# Add: pipeline.register_extractor("txt", TextFileExtractor())

# Step 4: Test
python -m pytest tests/integration/test_end_to_end.py::test_full_pipeline_extraction[txt-json] -v
# Expected: PASS

# Workstream 1B: QualityValidator Pipeline (3-4 hours)
# Step 1: Reproduce failures
python -m pytest tests/integration/test_pipeline_orchestration.py::test_po_004_full_pipeline_end_to_end -v

# Step 2: Add QualityValidator dependency
# Edit: src/processors/quality_validator.py line 79
# Change: return []
# To:     return ["MetadataAggregator"]

# Step 3: Test
python -m pytest tests/integration/test_pipeline_orchestration.py::test_po_004_full_pipeline_end_to_end -v
# Expected: PASS
```

**Success Criteria**: 5 tests now passing (3 TXT + 2 QV pipeline)

---

### Agent 2: npl-tdd-builder

**Start Here**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"

# Read orchestration plan
cat docs/planning/v1_0_6-planning/TEST_REMEDIATION_ORCHESTRATION_PLAN.md | grep -A 300 "Workstream 2: ChunkedTextFormatter"

# Step 1: Reproduce failures (expect JSON format, not text)
python -m pytest tests/test_formatters/test_formatter_edge_cases.py::TestChunkedTextFormatterEdgeCases::test_token_limit_minimum -v

# Step 2: Review current implementation
cat src/formatters/chunked_text_formatter.py

# Step 3: Refactor to JSON output (3-4 hours)
# Key changes:
# - Config key: token_limit → max_tokens_per_chunk
# - Output: Plain text → JSON with chunks array
# - format_type: "chunked" → "chunked_text"
# - Add: _create_chunks() returns list[dict]
# - Add: Token limit validation

# Step 4: Test incrementally
python -m pytest tests/test_formatters/test_formatter_edge_cases.py::TestChunkedTextFormatterEdgeCases::test_token_limit_minimum -v
# Fix until passes, then next test...

# Step 5: All tests
python -m pytest tests/test_formatters/test_formatter_edge_cases.py::TestChunkedTextFormatterEdgeCases -v
python -m pytest tests/test_formatters/test_formatter_edge_cases.py::TestCrossFormatterEdgeCases::test_same_input_all_formatters -v
```

**Success Criteria**: 7 tests now passing (all ChunkedTextFormatter edge cases)

---

### Agent 3: npl-validator

**Start Here**:
```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"

# Read orchestration plan
cat docs/planning/v1_0_6-planning/TEST_REMEDIATION_ORCHESTRATION_PLAN.md | grep -A 300 "Workstream 3: QualityValidator Scoring"

# Step 1: Reproduce failures (expect per-block quality_score in metadata)
python -m pytest tests/test_processors/test_processor_edge_cases.py::TestQualityValidatorEdgeCases::test_perfect_quality_content -v

# Step 2: Review current implementation
cat src/processors/quality_validator.py | grep -A 50 "def process"

# Current: Document-level scoring only
# Needed: Per-block scoring in block.metadata["quality_score"]

# Step 3: Refactor process() method (3-4 hours)
# Key changes:
# - Add: _score_block() method (returns score + issues per block)
# - Change: Enrich each block with quality_score and quality_issues in metadata
# - Keep: Document-level score as average of block scores

# Step 4: Test incrementally
python -m pytest tests/test_processors/test_processor_edge_cases.py::TestQualityValidatorEdgeCases::test_perfect_quality_content -v

# Step 5: All tests
python -m pytest tests/test_processors/test_processor_edge_cases.py::TestQualityValidatorEdgeCases -v
python -m pytest tests/test_processors/test_processor_edge_cases.py::TestCrossProcessorEdgeCases::test_single_block_through_all_processors -v
```

**Success Criteria**: 8 tests now passing (all QualityValidator edge cases)

---

## Phase 3: Integration & Verification

**After all agents complete their workstreams**:

```bash
cd "C:\Users\Andrew\Documents\AI ideas for fun and work\Prompt Research\Data Extraction\data-extractor-tool"

# Step 1: Run all previously failing tests
python -m pytest \
  tests/integration/test_end_to_end.py::test_full_pipeline_extraction[txt-json] \
  tests/integration/test_end_to_end.py::test_full_pipeline_extraction[txt-markdown] \
  tests/integration/test_end_to_end.py::test_full_pipeline_extraction[txt-chunked] \
  tests/integration/test_pipeline_orchestration.py::test_po_004_full_pipeline_end_to_end \
  tests/integration/test_pipeline_orchestration.py::test_po_005_pipeline_processor_dependency_ordering \
  tests/test_formatters/test_formatter_edge_cases.py::TestChunkedTextFormatterEdgeCases \
  tests/test_formatters/test_formatter_edge_cases.py::TestCrossFormatterEdgeCases::test_same_input_all_formatters \
  tests/test_processors/test_processor_edge_cases.py::TestQualityValidatorEdgeCases \
  tests/test_processors/test_processor_edge_cases.py::TestCrossProcessorEdgeCases::test_single_block_through_all_processors \
  -v

# Expected: 20/20 tests PASS ✅

# Step 2: Full regression test
python -m pytest tests/ -v

# Expected: 929/929 tests PASS ✅ (or 1016 if v1.0.6 tests included)

# Step 3: Code quality
python -m pylint src/pipeline/extraction_pipeline.py src/processors/quality_validator.py src/formatters/chunked_text_formatter.py

# Expected: Score >9.0

# Step 4: Coverage report
python -m pytest tests/ --cov=src --cov-report=html

# Expected: >85% coverage
```

---

## Phase 4: Release Preparation

```bash
# Update version
# Edit: setup.py, src/__init__.py
# Change: 1.0.6 → 1.0.7

# Update CHANGELOG
cat >> CHANGELOG.md << 'EOF'
## [1.0.7] - 2025-11-XX

### Added
- TXT pipeline integration (full support for .txt files)
- Per-block quality scoring in QualityValidator

### Changed
- ChunkedTextFormatter output format (text → JSON)
- QualityValidator dependency (now depends on MetadataAggregator)

### Fixed
- 20 edge case test failures (100% test coverage achieved)
- TXT extractor not registered in pipeline
- ChunkedTextFormatter fails on empty content
- QualityValidator missing per-block scores
EOF

# Build wheel
python -m build

# Test wheel in clean environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate
pip install dist/ai_data_extractor-1.0.7-py3-none-any.whl
python -c "from src.pipeline import ExtractionPipeline; print('Import OK')"
deactivate
rm -rf test_env

# Tag release
git add .
git commit -m "Release v1.0.7: 100% test coverage"
git tag v1.0.7
git push origin main --tags
```

---

## Troubleshooting

### Issue: Tests still failing after implementation

**Diagnosis**:
```bash
# Run test with verbose output
python -m pytest <failing_test> -v -s

# Check test expectations
cat tests/<test_file>.py | grep -A 20 "def <test_name>"

# Compare with implementation
cat src/<modified_file>.py | grep -A 20 "<method_name>"
```

**Common Fixes**:
1. **Config key mismatch**: Check test uses correct config key
2. **Output format mismatch**: Check test expects JSON vs text
3. **Metadata location mismatch**: Check test looks in right place (block.metadata vs result.metadata)
4. **Threshold mismatch**: Adjust scoring thresholds to match test expectations

---

### Issue: Regression in previously passing tests

**Diagnosis**:
```bash
# Identify which tests regressed
python -m pytest tests/ -v | grep FAILED

# Run just the regressed test
python -m pytest <regressed_test> -v

# Check what changed
git diff HEAD~1 src/<modified_file>.py
```

**Common Causes**:
1. **Changed API**: Restored backward compatibility
2. **Broken dependency**: Check processor ordering
3. **Modified defaults**: Restore original defaults

**Rollback**:
```bash
git revert HEAD
python -m pytest tests/ -v  # Verify rollback fixes regression
```

---

### Issue: Circular dependency in processors

**Symptom**: `ValueError: Circular dependency detected`

**Fix**:
```python
# Check dependencies
from src.processors import ContextLinker, MetadataAggregator, QualityValidator

print("ContextLinker deps:", ContextLinker().get_dependencies())
print("MetadataAggregator deps:", MetadataAggregator().get_dependencies())
print("QualityValidator deps:", QualityValidator().get_dependencies())

# Expected:
# ContextLinker deps: []
# MetadataAggregator deps: ['ContextLinker']
# QualityValidator deps: ['MetadataAggregator']

# If circular, fix dependency chain
```

---

## Success Checklist

### Agent 1 (npl-integrator)
- [ ] TXT extractor registered in CLI
- [ ] 3 TXT pipeline tests passing
- [ ] QualityValidator dependency added
- [ ] 2 QV pipeline tests passing
- [ ] No regressions in integration tests

### Agent 2 (npl-tdd-builder)
- [ ] ChunkedTextFormatter outputs JSON
- [ ] Config key `max_tokens_per_chunk` supported
- [ ] format_type = "chunked_text"
- [ ] 7 edge case tests passing
- [ ] No regressions in formatter tests

### Agent 3 (npl-validator)
- [ ] Per-block quality scores in metadata
- [ ] Per-block quality issues in metadata
- [ ] Document-level score computed
- [ ] 8 scoring tests passing
- [ ] No regressions in processor tests

### Integration
- [ ] All 20 previously failing tests now passing
- [ ] All 872+ previously passing tests still passing
- [ ] Total: 929/929 tests passing (100%)
- [ ] Code quality >9.0
- [ ] Coverage >85%

### Release
- [ ] Version bumped to v1.0.7
- [ ] CHANGELOG updated
- [ ] Release notes written
- [ ] Wheel built and tested
- [ ] Git tagged
- [ ] Deployed

---

## Quick Reference Card

### File Locations

```
Modified Files:
├── src/pipeline/extraction_pipeline.py        (Agent 1)
├── src/processors/quality_validator.py        (Agent 1 + 3)
├── src/formatters/chunked_text_formatter.py   (Agent 2)
├── src/cli/main.py                            (Agent 1)
└── src/extractors/__init__.py                 (Agent 1)

Documentation:
├── docs/planning/v1_0_6-planning/
│   ├── TEST_REMEDIATION_ORCHESTRATION_PLAN.md (Master plan)
│   └── QUICK_START_GUIDE.md                   (This file)
└── docs/RELEASE_NOTES_v1_0_7.md               (Generated)
```

### Test Commands

```bash
# Individual categories
pytest tests/integration/test_end_to_end.py -k "txt" -v                      # TXT (3)
pytest tests/integration/test_pipeline_orchestration.py::test_po_004 -v      # QV (2)
pytest tests/test_formatters/test_formatter_edge_cases.py::TestChunked* -v   # Chunked (7)
pytest tests/test_processors/test_processor_edge_cases.py::TestQuality* -v   # Quality (8)

# All previously failing
pytest tests/ -k "txt-json or txt-markdown or txt-chunked or test_po_004 or test_po_005 or TestChunkedText or TestQualityValidator" -v

# Full suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Key Configuration Changes

| Component | Old | New |
|-----------|-----|-----|
| ChunkedTextFormatter config key | `token_limit` | `max_tokens_per_chunk` |
| ChunkedTextFormatter output | Plain text | JSON |
| ChunkedTextFormatter format_type | `"chunked"` | `"chunked_text"` |
| QualityValidator scoring | Document-level only | Per-block + document-level |
| QualityValidator dependencies | `[]` | `["MetadataAggregator"]` |
| Pipeline TXT support | Not registered | Auto-registered |

---

## Emergency Contacts

**If stuck**, post in coordination channel:
```
🆘 HELP NEEDED

Agent: @<your-agent-name>
Workstream: <1A/1B/2/3>
Issue: <brief description>
Already tried: <troubleshooting steps>
Blocking: <yes/no - how many other agents>

Request: <sync call / async advice / code review>
```

**Escalation Path**:
1. Check orchestration plan (detailed steps)
2. Check troubleshooting section (common issues)
3. Post in coordination channel (async help)
4. Schedule sync call (15 min max)
5. Escalate to @project-coordinator (decisions needed)

---

## Time Tracking Template

```
Agent: @<agent-name>
Date: 2025-11-XX

Phase 1 - Discovery: X hours
├── Test reproduction: X min
├── Root cause analysis: X min
└── Spec creation: X min

Phase 2 - Implementation: X hours
├── Code changes: X min
├── Testing: X min
└── Fixes: X min

Phase 3 - Verification: X hours
├── Unit tests: X min
├── Regression tests: X min
└── Documentation: X min

Total: X hours
Blockers: <count>
Regressions: <count>
```

---

**READY TO START?**

1. ✅ Read full orchestration plan
2. ✅ Assign agents to workstreams
3. ✅ Each agent reads their section
4. ✅ Start Phase 1 (discovery) in parallel
5. ✅ Daily async standups
6. ✅ Handoff at phase boundaries
7. ✅ Celebrate 100% coverage!

**Questions?** See orchestration plan or post in #test-remediation

**Let's ship v1.0.7! 🚀**

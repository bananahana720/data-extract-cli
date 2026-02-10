# Test Design: Epic 5 - Enhanced CLI UX & Batch Processing

**Date:** 2025-11-25
**Author:** Murat (TEA Agent) + Andrew
**Status:** Draft
**Orchestration:** 8 agents across 2 phases (Context Discovery + Risk Analysis)

---

## Executive Summary

**Scope:** Full test design for Epic 5 with focus on Story 5-0 (UAT Testing Framework)

**Risk Summary:**
- Total risks identified: 10
- High-priority risks (≥6): 5
- Critical risk: R-001 tmux-cli timing sensitivity (Score 9)
- Top categories: TEST (4), TECH (3), CI (1), PERF (1), UX (1)

**Coverage Summary:**
- P0 scenarios: 24 (must pass every PR)
- P1 scenarios: 22 (run on merge to main)
- P2 scenarios: 12 (nightly/weekly)
- **Total scenarios**: 56 across 4 journeys
- **Estimated runtime**: 8-10 minutes (P0+P1)

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Prob | Impact | Score | Mitigation | Owner | Timeline |
|---------|----------|-------------|------|--------|-------|------------|-------|----------|
| R-001 | TEST | tmux-cli `wait_idle()` timing sensitivity - Rich progress bars animate continuously, causing false "not idle" detection | 3 | 3 | **9** | Implement `TEST_SYNC_COMPLETE` output markers; use `wait_for_marker()` instead of `wait_idle()` | TEA | Story 5-0 |
| R-002 | TECH | Rich ANSI escape code parsing fragility - escape sequences vary by terminal/version | 2 | 3 | 6 | Pin Rich ≥13.0,<14.0; use semantic assertions (check "green color" not raw codes) | TEA | Story 5-0 |
| R-003 | TEST | Singleton state pollution (CacheManager, ConfigManager) causes cross-test failures | 2 | 3 | 6 | Isolated `$HOME` per test; `reset_semantic_cache()` autouse fixture | TEA | Story 5-0 |
| R-004 | TEST | Journey test flakiness from timing variance between local/CI environments | 2 | 3 | 6 | Output stability checks; set timeouts at 2x baseline; retry logic | TEA | Story 5-0 |
| R-005 | CI | GitHub Actions environment constraints (TERM, tmux availability) | 2 | 3 | 6 | Verify tmux installed; set `TERM=xterm-256color`; document Ubuntu runner requirements | TEA | Story 5-0 |

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Prob | Impact | Score | Mitigation | Owner |
|---------|----------|-------------|------|--------|-------|------------|-------|
| R-006 | PERF | Performance regression during CLI operations | 2 | 2 | 4 | Maintain baselines: <2s startup, <100ms response, <50MB overhead | Dev |
| R-007 | TECH | Configuration cascade complexity (6 levels) | 2 | 2 | 4 | Unit tests for each cascade level; integration test for full precedence | Dev |
| R-008 | TECH | Rich library API changes in future versions | 2 | 2 | 4 | Pin version range; abstract assertions behind UXAssertion layer | TEA |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Prob | Impact | Score | Action |
|---------|----------|-------------|------|--------|-------|--------|
| R-009 | UX | Terminal width <60 columns causes layout issues | 1 | 2 | 2 | Implement compact layout fallback; test at 80 columns minimum |
| R-010 | PERF | Memory pressure on large batches (500+ files) | 1 | 2 | 2 | Chunked processing; monitor in regression suite |

### Risk Category Legend

- **TEST**: Test infrastructure and reliability
- **TECH**: Technical/Architecture complexity
- **CI**: CI/CD pipeline constraints
- **PERF**: Performance and scalability
- **UX**: User experience edge cases

---

## Test Coverage Plan

### P0 (Critical) - Run on every PR

**Criteria**: Blocks user journey + High risk (≥6) + No workaround

| Journey | Scenario | Test Level | Risk Link | UX Assertions | Notes |
|---------|----------|------------|-----------|---------------|-------|
| J1 | Welcome panel displays on first run | E2E | R-002 | `assert_panel_displayed("Welcome")` | Entry point validation |
| J1 | Mode selection prompt appears | E2E | R-002 | `assert_panel_displayed("mode")` | Guided mode interaction |
| J1 | Enterprise mode saves preference | E2E | R-003 | `assert_color_present("green")` | Config persistence |
| J1 | Hobbyist mode saves preference | E2E | R-003 | `assert_color_present("green")` | Both mode paths |
| J1 | Tutorial offer prompt appears | E2E | - | `assert_learning_tip()` | Educational UX |
| J1 | Sample processing completes | E2E | R-001 | `assert_progress_bar_shown()` | Core functionality |
| J1 | Success summary with next steps | E2E | R-002 | `assert_panel_displayed("Success")` | Completion feedback |
| J2 | File selection shows count/types | E2E | - | Pre-flight panel | Express mode entry |
| J2 | Pre-flight validation passes | E2E | R-002 | `assert_panel_displayed("Pre-flight")` | Happy path |
| J2 | Process continues with flagged issues | E2E | R-004 | Progress bar + error count | Resilience |
| J2 | Progress bar updates during processing | E2E | R-001 | `assert_progress_bar_shown()` | Core UX feature |
| J2 | Quality summary displays | E2E | R-002 | `assert_panel_displayed("Quality")` | Results presentation |
| J2 | Output files exist in expected location | E2E | - | File system check | Functional validation |
| J3 | Analyze command launches pipeline | E2E | R-001 | Spinner shown | Command entry |
| J3 | TF-IDF stage displays with timing | E2E | R-002 | "[✓] TF-IDF" pattern | Stage 1 |
| J3 | Similarity analysis stage displays | E2E | R-002 | "[✓] Similarity" pattern | Stage 2 |
| J3 | LSA reduction stage displays | E2E | R-002 | "[✓] LSA" pattern | Stage 3 |
| J3 | Quality metrics stage displays | E2E | R-002 | "[✓] Quality" pattern | Stage 4 |
| J3 | All 4 stages complete in <30s | E2E | R-006 | Timing check | Performance SLA |
| J4 | --learn flag activates learning mode | E2E | - | `assert_learning_tip()` | Mode activation |
| J4 | Step 1 explanation shown | E2E | R-002 | "📖 Step 1" header | Educational content |
| J4 | Continue prompt after each step | E2E | - | "[Continue]" option | Interactivity |
| J4 | All 5 pipeline steps show explanations | E2E | R-001 | 5 learning panels | Full journey |
| J4 | Insights summary at end | E2E | R-002 | `assert_panel_displayed("learned")` | Learning aggregation |

**Total P0**: 24 scenarios, ~5-6 minutes

### P1 (High) - Run on merge to main

**Criteria**: Important features + Medium risk (3-4) + Common workflows

| Journey | Scenario | Test Level | Risk Link | Notes |
|---------|----------|------------|-----------|-------|
| J1 | Tutorial starts sample walkthrough | E2E | - | Full tutorial flow |
| J1 | Declining tutorial skips to processing | E2E | - | Conditional branching |
| J1 | Invalid mode selection shows error | E2E | R-007 | Error recovery |
| J2 | Pre-flight detects files with warnings | E2E | - | Detection accuracy |
| J2 | Incremental saves shown in progress | E2E | R-001 | Feedback frequency |
| J2 | Duplicate detection suggestion | E2E | - | Semantic callout |
| J2 | Ctrl+C interruption saves progress | E2E | R-004 | Error handling |
| J2 | Single corrupted file skips gracefully | E2E | - | Partial failure |
| J2 | Mixed format batch processing | E2E | - | Format diversity |
| J3 | Quality distribution bars render | E2E | R-002 | Visualization |
| J3 | Category percentages shown | E2E | - | Data accuracy |
| J3 | Top topics extracted and displayed | E2E | - | LSA validation |
| J3 | Duplicate pair suggestion | E2E | - | Feature integration |
| J3 | Report generation with --report | E2E | - | Report functionality |
| J3 | Empty corpus handled gracefully | E2E | R-007 | Error handling |
| J4 | Show raw output displays data | E2E | - | Debug feature |
| J4 | Learn more deepens explanation | E2E | - | Deep learning |
| J4 | Step timing shown | E2E | - | Quantitative feedback |
| J4 | Learning tips are accurate | E2E | - | Content validation |
| J4 | Error shows educational context | E2E | - | Pedagogical errors |

**Total P1**: 22 scenarios, ~3-4 minutes

### P2 (Low) - Run nightly/weekly

**Criteria**: Edge cases + Exploratory + Performance benchmarks

| Journey | Scenario | Test Level | Notes |
|---------|----------|------------|-------|
| J1 | Missing sample corpus handled | E2E | Robustness |
| J1 | Terminal width <60 compact layout | E2E | Accessibility |
| J1 | NO_COLOR monochrome output | E2E | Accessibility |
| J2 | Glob pattern file selection | E2E | Power user |
| J2 | Batch >100 files memory handling | E2E | Scalability |
| J2 | Very large single file chunking | E2E | Performance |
| J3 | Verbose mode shows details | E2E | Developer feature |
| J3 | Dry-run preview mode | E2E | Preview functionality |
| J3 | Large corpus (500+ docs) | E2E | Scalability |
| J4 | Parameter adjustment suggestion | E2E | Interactive learning |
| J4 | NO_COLOR learning content | E2E | Accessibility |
| J4 | Large file paging | E2E | Long content |

**Total P2**: 12 scenarios, ~5-8 minutes

---

## Execution Order

### Smoke Tests (<2 min)

**Purpose**: Fast feedback, catch infrastructure issues

- [ ] tmux-cli available and functional (10s)
- [ ] CLI module invocable: `data-extract --help` (5s)
- [ ] Sample corpus accessible (5s)
- [ ] Rich console rendering works (10s)

**Total**: 4 scenarios, ~30 seconds

### P0 Tests (<6 min)

**Purpose**: Critical path validation - blocks PR merge

- [ ] J1: Welcome + Mode Selection (60s)
- [ ] J1: Tutorial Offer + Sample Processing (90s)
- [ ] J2: Pre-flight + Progress + Summary (120s)
- [ ] J3: All 4 Semantic Stages (90s)
- [ ] J4: Learning Mode Full Journey (120s)

**Total**: 24 scenarios, ~5-6 minutes

### P1 Tests (<4 min)

**Purpose**: Important feature coverage - run on merge

- [ ] J1: Error handling + Edge paths (45s)
- [ ] J2: Error recovery + Format diversity (90s)
- [ ] J3: Visualizations + Reports (60s)
- [ ] J4: Advanced features (45s)

**Total**: 22 scenarios, ~3-4 minutes

### P2 Tests (<8 min)

**Purpose**: Full regression - nightly/weekly

- [ ] Accessibility tests (NO_COLOR, narrow terminal) (90s)
- [ ] Scalability tests (large batches, big files) (180s)
- [ ] Edge cases and exploratory (90s)

**Total**: 12 scenarios, ~5-8 minutes

---

## Resource Estimates

### Test Development Effort

| Component | Count | Hours/Item | Total Hours | Notes |
|-----------|-------|------------|-------------|-------|
| TmuxSession wrapper | 1 class | 4.0 | 4 | Core infrastructure |
| UXAssertion engine | 8 functions | 0.5 | 4 | Assertion helpers |
| Journey 1 tests | 13 scenarios | 0.25 | 3 | First-time setup |
| Journey 2 tests | 15 scenarios | 0.25 | 4 | Batch processing |
| Journey 3 tests | 15 scenarios | 0.25 | 4 | Semantic analysis |
| Journey 4 tests | 15 scenarios | 0.25 | 4 | Learning mode |
| Sample corpus | 12 files | 0.1 | 1 | Test data setup |
| Expected outputs | 21 baselines | 0.1 | 2 | Golden outputs |
| CI integration | 1 workflow | 2.0 | 2 | GitHub Actions |
| **Total** | **-** | **-** | **28 hours** | **~3.5 days** |

### Prerequisites

**Test Data:**
- Sample corpus: 10-12 files (<5 MB) from `tests/fixtures/real_world_files/`
- Expected outputs: 21 baseline captures (ANSI, JSON, TXT)
- Synthetic docs: CorruptPDFFactory, SyntheticDocFactory

**Tooling:**
- tmux-cli: `uv tool install tmux-cli`
- pytest markers: `@pytest.mark.uat`, `@pytest.mark.journey_N`
- Rich: pinned ≥13.0,<14.0

**Environment:**
- Ubuntu runner (GitHub Actions) with tmux pre-installed
- `TERM=xterm-256color` for color support
- Python 3.11+ (project minimum)

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions - blocks PR)
- **P1 pass rate**: ≥95% (waivers require TEA approval)
- **P2 pass rate**: ≥90% (informational, tracked for trends)
- **High-risk mitigations**: 100% complete before Story 5-0 closure

### Coverage Targets

- **Journey paths**: 100% (all 4 journeys tested)
- **UX assertions**: 100% (all 8 assertion functions exercised)
- **Error scenarios**: ≥80% (graceful degradation validated)
- **Edge cases**: ≥60% (accessibility, scalability)

### Non-Negotiable Requirements

- [ ] All P0 tests pass on every PR
- [ ] No high-risk (≥6) items unmitigated
- [ ] R-001 (timing) mitigation validated: 20x local + 20x CI runs
- [ ] tmux-cli integration stable in GitHub Actions
- [ ] Quality gates pass: Black/Ruff/Mypy with 0 violations

---

## Mitigation Plans

### R-001: tmux-cli Timing Sensitivity (Score: 9)

**Mitigation Strategy:**
1. Instrument CLI with `TEST_SYNC_COMPLETE` output markers after each operation
2. Implement `TmuxSession.wait_for_marker(marker: str, timeout: float)` method
3. Replace `wait_idle()` with `wait_for_marker()` in all journey tests
4. Set timeouts at 2x observed baseline (local: 30s, CI: 60s)

**Owner:** TEA
**Timeline:** Story 5-0 implementation
**Status:** Planned
**Verification:**
- Run each journey test 20x locally - 100% pass required
- Run each journey test 20x in CI - 100% pass required
- Document baseline timings in `tests/uat/TIMING_BASELINE.md`

### R-002: Rich ANSI Escape Code Parsing (Score: 6)

**Mitigation Strategy:**
1. Pin Rich version: `rich>=13.0,<14.0` in pyproject.toml
2. Create abstraction layer: `UXAssertion` functions hide raw ANSI parsing
3. Use semantic checks: "panel with green border" not raw escape codes
4. Test assertions against actual Rich output samples (captured golden outputs)

**Owner:** TEA
**Timeline:** Story 5-0 implementation
**Status:** Planned
**Verification:**
- All 8 UXAssertion functions have unit tests
- Assertions work with/without color (NO_COLOR respected)
- No raw escape code literals in journey test assertions

### R-003: Singleton State Pollution (Score: 6)

**Mitigation Strategy:**
1. Isolated `$HOME` per test via fixture: `env['HOME'] = str(tmp_path / 'home')`
2. `reset_semantic_cache()` autouse fixture clears CacheManager between tests
3. ConfigManager reset in `journey_context` fixture
4. No shared state between journey test classes

**Owner:** TEA
**Timeline:** Story 5-0 implementation
**Status:** Planned
**Verification:**
- Run journey tests in random order (`pytest --random-order`) - 100% pass
- Run each journey test 3x consecutively - no state leakage
- Verify config files isolated per test via file system checks

---

## Test Framework Architecture

### Directory Structure

```
tests/uat/
├── __init__.py
├── conftest.py                           # UAT fixtures
├── README.md                             # Usage documentation
├── TIMING_BASELINE.md                    # Performance baselines
├── framework/
│   ├── __init__.py
│   ├── tmux_wrapper.py                   # TmuxSession class
│   ├── ux_assertions.py                  # Assertion helpers
│   └── journey_runner.py                 # JourneyStep, JourneyRunner
├── journeys/
│   ├── __init__.py
│   ├── test_journey_1_first_time_setup.py
│   ├── test_journey_2_batch_processing.py
│   ├── test_journey_3_semantic_analysis.py
│   └── test_journey_4_learning_mode.py
└── fixtures/
    ├── sample_corpus/                    # 10+ test documents
    │   ├── 01-cobit-intro.pdf
    │   ├── 02-iso27001.pdf
    │   ├── ... (12 files total)
    │   └── MANIFEST.json
    ├── expected_outputs/                 # Golden baselines
    │   ├── journey-1-welcome.ansi
    │   ├── journey-2-preflight.ansi
    │   ├── ... (21 files total)
    │   └── BASELINE_VERSIONS.json
    ├── factories.py                      # Synthetic data generation
    └── README.md
```

### Core Components

**TmuxSession** (`tests/uat/framework/tmux_wrapper.py`):
```python
@dataclass
class TmuxSession:
    pane_id: str | None = None

    def __enter__(self) -> "TmuxSession": ...
    def __exit__(self, *args) -> None: ...
    def launch(command: str) -> str: ...
    def send(text: str, enter: bool = True) -> None: ...
    def capture() -> str: ...
    def wait_idle(idle_time: float, timeout: float) -> None: ...
    def wait_for_marker(marker: str, timeout: float) -> None: ...  # R-001 mitigation
    def kill() -> None: ...
```

**UXAssertion** (`tests/uat/framework/ux_assertions.py`):
```python
def assert_panel_displayed(output: str, title: str) -> None: ...
def assert_progress_bar_shown(output: str) -> None: ...
def assert_table_rendered(output: str, headers: list) -> None: ...
def assert_color_present(output: str, color: str) -> None: ...
def assert_quality_distribution(output: str, categories: list) -> None: ...
def assert_error_guide_shown(output: str) -> None: ...
def assert_learning_tip(output: str) -> None: ...
def normalize_output(output: str) -> str: ...  # Strip timestamps, paths
```

---

## Assumptions and Dependencies

### Assumptions

1. tmux is pre-installed on Ubuntu GitHub Actions runners
2. Rich version 13.x maintains backward-compatible escape code patterns
3. CLI commands produce deterministic output for same input
4. Sample corpus files are PII-free and deterministic

### Dependencies

| Dependency | Source | Required By | Status |
|------------|--------|-------------|--------|
| tmux | System | Story 5-0 start | Pre-installed on Ubuntu |
| tmux-cli | PyPI | Story 5-0 start | `uv tool install tmux-cli` |
| Rich ≥13.0 | PyPI | Story 5-0 start | Already in dependencies |
| pytest | PyPI | Story 5-0 start | Already in dev dependencies |
| Sample corpus | Git | Story 5-0 start | Create from real_world_files |

### Risks to Plan

- **Risk**: tmux-cli has breaking changes
  - **Impact**: All journey tests fail
  - **Contingency**: Pin tmux-cli version; maintain fallback subprocess approach

- **Risk**: Rich output format changes
  - **Impact**: UX assertions fail
  - **Contingency**: Abstraction layer isolates changes; update assertions only

---

## Story 5-0 Acceptance Criteria Mapping

| AC ID | Criterion | Test Coverage | Scenarios |
|-------|-----------|---------------|-----------|
| AC-5.0-1 | UAT scaffold at `tests/uat/` | Directory structure exists | Smoke test |
| AC-5.0-2 | TmuxSession wrapper | All journey tests use wrapper | 56 scenarios |
| AC-5.0-3 | UXAssertion engine | All assertions exercised | 56 scenarios |
| AC-5.0-4 | Journey 1 test | J1-S1 through J1-S13 | 13 scenarios |
| AC-5.0-5 | Journey 2 test | J2-S1 through J2-S15 | 15 scenarios |
| AC-5.0-6 | Journey 3 test | J3-S1 through J3-S15 | 15 scenarios |
| AC-5.0-7 | Journey 4 test | J4-S1 through J4-S15 | 15 scenarios |
| AC-5.0-8 | CI integration | GitHub Actions workflow | P0 tests in CI |
| AC-5.0-9 | Sample corpus | 12 files in sample_corpus/ | Fixture validation |
| AC-5.0-10 | Quality gates pass | Black/Ruff/Mypy | All test code |

---

## Appendix

### Knowledge Base References

- Epic 4 Retrospective: Verification Loop, Behavioral Testing, Singleton Reset patterns
- BMAD TEA Agent: Risk governance, probability-impact scoring
- UX Design Specification: 7 user journeys with UAT assertions

### Related Documents

- PRD: `docs/prd.md`
- Epic 5 Tech Spec: `docs/tech-spec-epic-5.md`
- Story 5-0: `docs/stories/5-0-uat-testing-framework.md`
- UX Design: `docs/ux-design-specification.md`
- Test Fixtures Catalog: `docs/test-fixtures-catalog.md`

### Agent Orchestration Summary

**Phase 1: Context Discovery (5 agents)**
- 1A: Epic 5 Tech Spec analysis
- 1B: Story 5-0 requirements extraction
- 1C: 7 User Journeys mapping
- 1D: Test architecture patterns
- 1E: Real-world fixtures catalog

**Phase 2: Risk Assessment (3 agents)**
- 2A: Testability risk matrix
- 2B: Test scenario mapping
- 2C: Test data requirements

**Total agents**: 8
**Execution pattern**: Parallel non-destructive, sequential document generation

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: Multi-agent orchestration with Wave-based execution
**Version**: Epic 5 / Story 5-0 Test Design v1.0

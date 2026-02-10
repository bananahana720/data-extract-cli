# Epic Technical Specification: Extract & Normalize - Validation & Integration

Date: 2025-11-11
Author: andrew
Epic ID: 2.5
Status: Draft

---

## Overview

Epic 2.5 is a **bridge epic** created during the Epic 2 retrospective to address critical gaps and technical debt before starting Epic 3 (Intelligent Chunking). After completing Epic 2's normalization and validation features, the retrospective identified three critical blockers: (1) performance validation with large documents, (2) spaCy integration and testing required for Story 3.1's semantic chunking, and (3) comprehensive large document test fixtures missing from the test suite.

This epic ensures the Extract & Normalize pipeline is production-ready by validating performance against NFRs, integrating spaCy for downstream semantic analysis, and establishing a UAT framework for systematic acceptance testing. Without these foundations, Epic 3 would face integration issues, performance bottlenecks, and insufficient testing infrastructure.

## Objectives and Scope

**In Scope:**
- Performance validation and optimization for 100-file batches (<10 min, <2GB memory per NFR-P1, NFR-P2)
- Profiling and bottleneck identification in extraction and normalization stages
- spaCy 3.7.2 installation and `en_core_web_md` model integration
- spaCy sentence segmentation testing and validation (95%+ accuracy)
- Utility function for Epic 3: `get_sentence_boundaries()` for semantic chunking
- Large document test fixtures: 50+ page PDF, 10K+ row Excel, scanned PDF
- Integration tests for large file processing and memory monitoring
- UAT testing workflow creation for systematic acceptance criteria validation
- CLAUDE.md documentation updates with Epic 2 lessons learned
- Resolution of Story 2.5 code review blockers (Mypy violations, unused variables)

**Out of Scope:**
- Actual semantic chunking implementation (Epic 3, Story 3.1)
- Advanced spaCy features beyond sentence segmentation (entity recognition covered in Epic 2)
- Performance optimization beyond critical bottlenecks (diminishing returns)
- GUI or web interface for testing
- Production deployment configuration

## System Architecture Alignment

Epic 2.5 validates and strengthens the architectural foundations established in Epics 1-2:

**Architectural Patterns Validated:**
- **ADR-005 (Streaming Pipeline)**: Performance tests verify constant memory usage (<2GB) for large document batches, validating the streaming architecture's effectiveness
- **ADR-006 (Continue-On-Error)**: Integration tests confirm graceful degradation when individual files fail in batch processing
- **NFR-R2 (Graceful Degradation)**: Completeness validation ensures no silent failures - all extraction gaps are flagged and logged
- **NFR-A2 (Logging)**: Performance profiling validates structured logging provides actionable audit trails

**Components Strengthened:**
- `src/data_extract/utils/nlp.py` - New spaCy integration utilities for sentence boundary detection
- `tests/performance/test_throughput.py` - Performance regression detection suite
- `tests/integration/test_spacy_integration.py` - NLP pipeline integration validation
- `tests/integration/test_large_files.py` - Large document processing validation
- `tests/fixtures/` - Comprehensive test fixture library with large documents

**Preparation for Epic 3:**
- spaCy sentence segmentation provides the foundation for semantic chunking (Story 3.1)
- Performance baselines enable Epic 3 to detect regressions when adding chunking overhead
- Large document fixtures support Epic 3's chunk quality validation

**Constraints Addressed:**
- Python 3.12 compatibility validated for spaCy 3.7.2 and dependencies
- Classical NLP approach confirmed (spaCy sentence segmentation, no transformers)
- Enterprise security requirements: all dependencies from official PyPI with pinned versions

## Detailed Design

### Services and Modules

| Module | Responsibility | Inputs | Outputs | Owner |
|--------|---------------|---------|---------|-------|
| **tests/performance/test_throughput.py** | Benchmark pipeline throughput and memory usage | Test fixture batches (10, 50, 100, 500 files) | Performance metrics, baseline documentation | Story 2.5.1 |
| **tests/integration/test_spacy_integration.py** | Validate spaCy installation and sentence segmentation | Text samples, spaCy model | Sentence boundaries, accuracy metrics | Story 2.5.2 |
| **tests/integration/test_large_files.py** | Test large document processing without memory spikes | Large PDF/Excel fixtures | Memory profiles, processing results | Story 2.5.3 |
| **src/data_extract/utils/nlp.py** | spaCy utility functions for semantic analysis | Raw text | Sentence boundaries, linguistic features | Story 2.5.2 |
| **tests/fixtures/pdfs/large/** | Large PDF test fixtures (50+ pages) | N/A | Test documents for validation | Story 2.5.3 |
| **tests/fixtures/xlsx/large/** | Large Excel test fixtures (10K+ rows) | N/A | Test spreadsheets for validation | Story 2.5.3 |
| **tests/fixtures/pdfs/scanned/** | Scanned PDF fixtures requiring OCR | N/A | Test documents for OCR validation | Story 2.5.3 |
| **bmad:bmm:workflows:create-test-cases** | UAT workflow for systematic AC testing | Story markdown files | Test scenarios, execution framework | Story 2.5.3 |

**Note:** Epic 2.5 focuses on **validation, testing infrastructure, and preparation** for Epic 3. No production code changes except spaCy utilities and bug fixes.

### Data Models and Contracts

**Existing Models Used** (no new models added in Epic 2.5):

```python
# From src/data_extract/core/models.py (Epic 1, Epic 2)
class ValidationReport(BaseModel):
    """Completeness validation results from Story 2.5"""
    document_id: str
    missing_images: List[ImageReference]
    complex_objects: List[ComplexObject]
    extraction_confidence: float = Field(ge=0.0, le=1.0)
    content_gaps: List[ContentGap]
    quality_flags: List[str]
    document_average_confidence: Optional[float] = None  # Fix from code review
    scanned_pdf_detected: Optional[bool] = None  # Fix from code review
```

**New Utility Functions** (Story 2.5.2):

```python
# src/data_extract/utils/nlp.py
from typing import List
import spacy
from spacy.language import Language

def get_sentence_boundaries(text: str, nlp: Language = None) -> List[int]:
    """
    Extract sentence boundary positions from text using spaCy.

    Prepares for Epic 3 Story 3.1 (Semantic Chunking).

    Args:
        text: Raw text to segment
        nlp: spaCy Language model (loads en_core_web_md if None)

    Returns:
        List of character positions where sentences end

    Raises:
        ValueError: If text is empty or model fails to load

    Example:
        >>> boundaries = get_sentence_boundaries("First sentence. Second one.")
        >>> boundaries
        [15, 27]  # Character positions of sentence ends
    """
    if not nlp:
        nlp = spacy.load("en_core_web_md")

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    doc = nlp(text)
    return [sent.end_char for sent in doc.sents]
```

**Performance Measurement Data** (Story 2.5.1):

```python
# tests/performance/test_throughput.py
class PerformanceMetrics(BaseModel):
    """Performance test results"""
    batch_size: int
    total_time_seconds: float
    files_per_minute: float
    peak_memory_mb: float
    avg_memory_mb: float
    cpu_utilization_percent: float
    bottlenecks: List[str]  # Identified via profiling
```

**Contract Validation:** All existing contracts from Epic 1/2 remain unchanged. Epic 2.5 validates these contracts work correctly under stress (large documents, high volume).

### APIs and Interfaces

**Performance Testing Interface** (Story 2.5.1):

```python
# tests/performance/test_throughput.py
import pytest
from pathlib import Path
import psutil
import time
from typing import List

@pytest.mark.performance
def test_batch_throughput_100_files(benchmark_fixtures: List[Path]):
    """
    Validate NFR-P1: Process 100 mixed-format files in <10 minutes
    """
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()

    # Process batch through pipeline
    results = process_batch(benchmark_fixtures)

    end_time = time.time()
    peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    # Assertions
    elapsed_minutes = (end_time - start_time) / 60
    assert elapsed_minutes < 10, f"Processing took {elapsed_minutes:.2f} min (max: 10)"
    assert peak_memory < 2048, f"Peak memory {peak_memory:.0f}MB (max: 2048MB)"
```

**spaCy Integration Interface** (Story 2.5.2):

```python
# tests/integration/test_spacy_integration.py
import pytest
import spacy
from data_extract.utils.nlp import get_sentence_boundaries

def test_spacy_model_loads():
    """Validate spaCy en_core_web_md model loads successfully"""
    nlp = spacy.load("en_core_web_md")
    assert nlp is not None
    assert nlp.meta["lang"] == "en"
    assert "core_web_md" in nlp.meta["name"]

def test_sentence_segmentation_accuracy():
    """Validate 95%+ accuracy on sentence boundary detection"""
    test_cases = load_segmentation_test_cases()  # Gold standard annotations
    correct = 0
    total = len(test_cases)

    for text, expected_boundaries in test_cases:
        actual_boundaries = get_sentence_boundaries(text)
        if actual_boundaries == expected_boundaries:
            correct += 1

    accuracy = correct / total
    assert accuracy >= 0.95, f"Segmentation accuracy {accuracy:.2%} (required: 95%)"
```

**Large File Testing Interface** (Story 2.5.3):

```python
# tests/integration/test_large_files.py
@pytest.mark.integration
def test_large_pdf_memory_usage(large_pdf_fixture: Path):
    """Validate streaming processing maintains <2GB memory for large files"""
    initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
    max_memory = initial_memory

    # Monitor memory during processing
    result = process_document_with_monitoring(large_pdf_fixture)

    assert max_memory < 2048, f"Memory spiked to {max_memory:.0f}MB"
    assert result.is_valid(), "Processing failed for large document"
```

**Bug Fix Interface** (Story 2.5 Code Review Blockers):

```python
# src/data_extract/normalize/validation.py:694, 719, 736
# Fix Mypy violations by adding missing optional fields:
report = ValidationReport(
    document_id=doc_id,
    missing_images=images,
    complex_objects=objects,
    extraction_confidence=confidence,
    content_gaps=gaps,
    quality_flags=flags,
    document_average_confidence=None,  # ADD THIS
    scanned_pdf_detected=None  # ADD THIS
)
```

### Workflows and Sequencing

**Story 2.5.1: Performance Validation & Optimization** (4 hours)
1. Install profiling tools: `pip install cProfile memory_profiler psutil`
2. Create 100-file test batch (mix of PDFs, DOCX, XLSX from existing fixtures)
3. Run baseline performance test: measure throughput and memory
4. Profile pipeline execution: `python -m cProfile -o profile.stats pipeline_script.py`
5. Analyze profile data: identify top 10 slowest functions
6. Optimize critical bottlenecks (e.g., replace full-file reads with streaming)
7. Re-run performance test: validate improvements
8. Create `tests/performance/test_throughput.py` with automated tests
9. Add performance CI job (run weekly, not on every commit)
10. Document baseline metrics in test docstrings

**Story 2.5.2: spaCy Integration & Validation** (4 hours)
1. Add spaCy to pyproject.toml: `spacy = "^3.7.2"`
2. Install: `pip install spacy`
3. Download model: `python -m spacy download en_core_web_md`
4. Verify installation: `python -m spacy validate`
5. Create `src/data_extract/utils/nlp.py` with `get_sentence_boundaries()`
6. Write unit tests for utility function (edge cases: empty text, single sentence, etc.)
7. Create `tests/integration/test_spacy_integration.py`
8. Test sentence segmentation accuracy on gold standard corpus
9. Update CLAUDE.md with spaCy setup instructions
10. Update README.md with model download step

**Story 2.5.3: Large Document Fixtures & UAT Framework** (4 hours)
1. Create large test fixtures:
   - Generate or source 50+ page PDF
   - Generate 10K+ row Excel file with audit data structure
   - Source scanned PDF requiring OCR
2. Sanitize fixtures (remove sensitive data, preserve structure)
3. Add fixtures to `tests/fixtures/large/` with README.md
4. Create `tests/integration/test_large_files.py`
5. Test memory monitoring during large file processing
6. Design UAT workflow structure (inputs: story markdown, outputs: test cases)
7. Create `bmad:bmm:workflows:create-test-cases` workflow stub
8. Update CLAUDE.md with "Lessons from Epic 2" section
9. Document quality gate best practices
10. Fix Story 2.5 code review blockers (Mypy, Ruff violations)

**Code Review Blocker Resolution** (Embedded in Story 2.5.3):
- Fix validation.py:694, 719, 736 - Add `document_average_confidence=None, scanned_pdf_detected=None`
- Remove unused variable at validation.py:697 (`ocr_validation_performed`)
- Re-run quality gates: `black src/ tests/ && ruff check src/ tests/ && mypy src/data_extract/`
- Verify 0 violations, document proof in Story 2.5.3 completion notes

### UAT Workflow Framework

**Overview:**
Epic 2.5 introduces a comprehensive UAT (User Acceptance Testing) workflow framework to systematically validate story acceptance criteria. The framework consists of four integrated workflows that transform story requirements into executable test cases, prepare test infrastructure, execute tests with AI assistance, and provide senior QA review with approval gates.

**Purpose:**
- Ensure systematic validation of all acceptance criteria
- Provide repeatable testing process across all stories
- Enable AI-assisted test execution with human oversight
- Establish quality gates for UAT approval
- Generate stakeholder-friendly test reports

#### UAT Workflow Pipeline

The UAT framework follows a linear 4-stage pipeline:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        UAT Workflow Pipeline                             │
└─────────────────────────────────────────────────────────────────────────┘

     ┌──────────────────────┐
     │ 1. create-test-cases │
     │ Story → Test Cases   │
     │                      │
     │ Input: Story.md      │
     │ Output: test-cases.md│
     └──────────┬───────────┘
                │
                ↓ Test cases generated
                │
     ┌──────────────────────┐
     │ 2. build-test-context│
     │ Gather Test Fixtures │
     │                      │
     │ Input: test-cases.md │
     │ Output: test-context.xml
     └──────────┬───────────┘
                │
                ↓ Fixtures and helpers assembled
                │
     ┌──────────────────────┐
     │ 3. execute-tests     │
     │ Run Tests with AI    │
     │                      │
     │ Input: test-context  │
     │ Output: test-results.md
     └──────────┬───────────┘
                │
                ↓ All tests executed
                │
     ┌──────────────────────┐
     │ 4. review-uat-results│
     │ QA Approval Decision │
     │                      │
     │ Input: test-results  │
     │ Output: uat-review.md│
     └──────────┬───────────┘
                │
                ↓
         ┌──────┴──────┐
         │   APPROVED   │ → Story Done
         ├──────────────┤
         │   CHANGES    │ → Fix Issues → Re-run execute-tests
         │  REQUESTED   │
         ├──────────────┤
         │   BLOCKED    │ → Resolve Blockers → Re-run execute-tests
         └──────────────┘
```

#### Workflow Descriptions

##### 1. Create Test Cases Workflow

**Location:** `bmad/bmm/workflows/4-implementation/create-test-cases/`

**Purpose:** Generate comprehensive test case specifications from story acceptance criteria with scenarios and expected outcomes.

**Workflow Type:** Document workflow (generates test-cases.md)

**Key Features:**
- Analyzes story acceptance criteria (AC-X-Y-Z format)
- Generates structured test cases covering:
  - Happy path scenarios
  - Edge cases
  - Error scenarios
  - Integration points
- Classifies tests by type: unit, integration, CLI, manual, performance
- Provides implementation guidance (fixtures, helpers, pytest markers)
- Supports configurable coverage levels: minimal/standard/comprehensive

**Input:**
- Story markdown file with acceptance criteria
- Optional: Epic technical specification (for context and NFRs)
- Optional: Test coverage level preference

**Output:**
- File: `docs/uat/test-cases/{story_key}-test-cases.md`
- Contents:
  - Structured test cases with preconditions, steps, expected results
  - Test coverage matrix showing AC → test mapping
  - Test type distribution (unit, integration, CLI, manual, performance)
  - Implementation notes (fixtures, helpers, pytest markers)
  - Risk areas and recommendations

**Usage Examples:**

```bash
# Basic usage with auto-discovery
workflow create-test-cases

# Specify story and coverage level
workflow create-test-cases \
  story_path=docs/stories/2.5-3.1-uat-workflow-framework.md \
  test_coverage_level=comprehensive

# Minimal coverage for quick validation
workflow create-test-cases test_coverage_level=minimal
```

**Test Case Structure:**

Each generated test case follows this format:

```markdown
### Test Case TC-{story_key}-{ac_num}-{scenario_num}

**Acceptance Criterion**: AC-{id}
**Test Type**: [Unit|Integration|CLI|Manual|Performance]
**Scenario**: [Happy Path|Edge Case|Error Case|Integration|Performance|Security]

**Objective**: What this test validates

**Preconditions**:
- Setup requirement 1
- Setup requirement 2

**Test Steps**:
1. Action 1
2. Action 2

**Expected Results**:
- Expected outcome 1
- Expected outcome 2

**Test Data** (if applicable):
- Input: test data description
- Expected Output: expected output description

**Dependencies** (if applicable):
- Fixtures: required test fixtures
- Helpers: required test helpers
- Configuration: required config
```

##### 2. Build Test Context Workflow

**Location:** `bmad/bmm/workflows/4-implementation/build-test-context/`

**Purpose:** Assemble test context XML with relevant fixtures, helpers, and configuration for test execution.

**Workflow Type:** Document workflow (generates test-context.xml)

**Key Features:**
- Discovers test fixtures in `tests/fixtures/` directory structure
- Loads helper functions from conftest.py files
- Parses pytest configuration and markers
- Identifies code under test (source files, modules)
- Maps test cases to required fixtures
- Identifies missing fixtures that need creation
- Provides setup recommendations and commands
- Can reuse story context XML to avoid duplication

**Input:**
- Test cases file (from create-test-cases workflow)
- Story markdown file
- Optional: Story context XML (reuses development context if available)

**Output:**
- File: `docs/uat/test-context/{story_key}-test-context.xml`
- Contents:
  - Test fixtures inventory with paths and descriptions
  - Helper functions from conftest.py files
  - pytest configuration and markers
  - Source code files under test
  - Integration points and setup requirements
  - Missing fixtures that need creation
  - Setup recommendations and commands

**Discovery Process:**

1. **Test Fixtures** - Scans `tests/fixtures/` directory:
   ```
   tests/fixtures/
   ├── pdfs/           # PDF test files (small/, large/)
   ├── xlsx/           # Excel test files
   ├── docx/           # Word test files
   ├── images/         # Image test files
   ├── csv/            # CSV test files
   └── json/           # JSON test files
   ```

2. **Test Helpers** - Loads conftest files:
   - `tests/conftest.py` - Global fixtures
   - `tests/integration/conftest.py` - Integration fixtures
   - Extracts shared fixtures, setup/teardown, factory functions

3. **pytest Configuration** - Parses `pytest.ini`:
   - Test markers (unit, integration, performance, etc.)
   - Timeout settings, coverage configuration

4. **Code Under Test** - Maps test cases to source files:
   - Identifies modules being tested
   - Documents function/class signatures
   - Notes dependencies and imports

5. **Integration Points** - Identifies external dependencies:
   - File system requirements
   - External commands (CLI tools)
   - Environment variables

**Usage Examples:**

```bash
# Basic usage with auto-discovery
workflow build-test-context

# Specify test cases file
workflow build-test-context \
  test_cases_file=docs/uat/test-cases/2.5-3.1-test-cases.md

# Include story context
workflow build-test-context include_story_context=true

# Standalone context (no story context)
workflow build-test-context include_story_context=false
```

**Test Context XML Structure:**

```xml
<test-context>
  <metadata>
    <!-- Story and test case metadata -->
  </metadata>

  <testCases>
    <!-- Summary and list of test cases -->
  </testCases>

  <fixtures>
    <!-- Available fixtures and generation scripts -->
    <!-- Missing fixtures that need creation -->
  </fixtures>

  <helpers>
    <!-- conftest fixtures and utility functions -->
  </helpers>

  <configuration>
    <!-- pytest settings and markers -->
    <!-- Environment variables -->
  </configuration>

  <codeUnderTest>
    <!-- Source files being tested -->
  </codeUnderTest>

  <integrationPoints>
    <!-- External dependencies and setup -->
  </integrationPoints>

  <storyContext>
    <!-- Development context (if included) -->
  </storyContext>

  <setupRequirements>
    <!-- Prerequisites and setup steps -->
  </setupRequirements>
</test-context>
```

##### 3. Execute Tests Workflow

**Location:** `bmad/bmm/workflows/4-implementation/execute-tests/`

**Purpose:** AI-driven test execution with pass/fail/blocked status, tmux-cli integration for CLI tests, and structured result capture.

**Workflow Type:** Document workflow (generates test-results.md)

**Key Features:**
- Executes all test types: pytest, CLI (via tmux-cli), manual
- Supports execution modes: automated, manual, hybrid (default)
- Captures comprehensive evidence: logs, output, screenshots
- Maps test results to acceptance criteria
- Identifies blocked tests (missing prerequisites)
- Provides pass/fail/blocked status with rationale
- Continues on failure (by default) for complete validation

**Input:**
- Test cases file (from create-test-cases workflow)
- Test context XML (from build-test-context workflow)
- Optional: Story markdown file
- Optional: Execution mode preference (automated/manual/hybrid)
- Optional: Screenshot capture setting for CLI tests

**Output:**
- File: `docs/uat/test-results/{story_key}-test-results.md`
- Contents:
  - Execution summary with pass/fail/blocked counts
  - Acceptance criteria validation status
  - Detailed results for all test types (pytest, CLI, manual)
  - Evidence for failed and blocked tests (logs, output, screenshots)
  - Performance observations
  - Recommendations for next steps

**Test Execution Types:**

1. **Automated Tests (pytest)**
   - Unit, Integration, Performance tests
   - Builds pytest command with markers and timeout
   - Captures output and parses results
   - Maps pytest tests to test case IDs
   - Records PASS/FAIL/ERROR with evidence

   Example:
   ```bash
   pytest -v --tb=short -m "unit or integration" --timeout=300
   ```

2. **CLI Tests (tmux-cli)**
   - CLI command tests, interactive application tests
   - Launches shell in tmux: `tmux-cli launch "zsh"`
   - Sends commands: `tmux-cli send "data-extract process test.pdf"`
   - Waits for completion: `tmux-cli wait_idle`
   - Captures output: `tmux-cli capture`
   - Verifies expected results
   - Records PASS/FAIL with output evidence

   **tmux-cli Integration Pattern:**
   ```bash
   # Launch shell
   tmux-cli launch "zsh"  # Returns pane ID

   # Run test command
   tmux-cli send "data-extract process test.pdf" --pane=2
   tmux-cli wait_idle --pane=2 --idle-time=2.0 --timeout=60

   # Capture and verify
   tmux-cli capture --pane=2
   ```

   **⚠️ Windows Users**: tmux-cli requires tmux (Unix/Linux only). On Windows, run execute-tests workflow from WSL:
   ```bash
   wsl
   cd /mnt/c/Users/{username}/projects/data-extraction-tool
   workflow execute-tests
   ```

   See `docs/tmux-cli-instructions.md` for full tmux-cli reference and `docs/uat/tmux-cli-windows-setup.md` for Windows setup.

3. **Manual Tests**
   - Tests requiring human verification
   - Displays test case with instructions to user
   - Prompts for result (pass/fail/blocked)
   - Captures failure description or notes
   - Records status with user-provided evidence

**Execution Modes:**

- **Automated Mode**: Runs only pytest tests, no user interaction, fast execution
- **Manual Mode**: Guides through manual tests only, requires user interaction
- **Hybrid Mode (Default)**: Runs automated tests first, then guides through manual tests

**Test Result Status Values:**

- **PASS**: Test executed successfully, met expected results
- **FAIL**: Test executed but did not meet expected results
- **BLOCKED**: Test could not execute due to missing prerequisite
- **SKIPPED**: Test was intentionally skipped (pytest only)
- **ERROR**: Test execution encountered an error (pytest only)

**Usage Examples:**

```bash
# Basic hybrid execution
workflow execute-tests

# Automated tests only (CI/CD)
workflow execute-tests test_execution_mode=automated

# With screenshot capture for CLI tests
workflow execute-tests capture_screenshots=true

# Stop on first failure
workflow execute-tests continue_on_failure=false

# Specific test files
workflow execute-tests \
  test_cases_file=docs/uat/test-cases/2.5-2-test-cases.md \
  test_context_file=docs/uat/test-context/2.5-2-test-context.xml
```

##### 4. Review UAT Results Workflow

**Location:** `bmad/bmm/workflows/4-implementation/review-uat-results/`

**Purpose:** AI-assisted QA review of test execution results with gap analysis, approval/changes-requested decision, and stakeholder summary.

**Workflow Type:** Document workflow (generates uat-review.md)

**Key Features:**
- Senior QA review with configurable quality gates
- Analyzes pass/fail ratios against thresholds
- Identifies coverage gaps (missing tests)
- Evaluates edge case and error scenario coverage
- Assesses evidence quality (logs, screenshots, reproduction steps)
- Generates review findings with severity (critical/major/minor)
- Makes approval decision: APPROVED, CHANGES REQUESTED, or BLOCKED
- Provides stakeholder summary (non-technical)
- Requires human review confirmation or override

**Input:**
- Test execution results file (from execute-tests workflow)
- Optional: Test cases file (derived from test results if not provided)
- Optional: Story markdown file (derived from test results if not provided)
- Optional: Quality gate level (minimal/standard/strict)
- Optional: Reviewer name (defaults to config user_name)

**Output:**
- File: `docs/uat/reviews/{story_key}-uat-review.md`
- Contents:
  - UAT status (APPROVED, CHANGES REQUESTED, BLOCKED)
  - Pass/fail ratio analysis with quality gate comparison
  - Coverage gap analysis identifying missing tests
  - Edge case and error scenario analysis
  - Evidence quality assessment
  - Review findings with severity (critical/major/minor)
  - Approval decision with rationale
  - Stakeholder summary (non-technical)
  - Required changes or blockers
  - Next steps

**Quality Gate Levels:**

1. **Minimal Gate**
   - Use Case: Early development, exploratory testing
   - Pass rate ≥ 80%
   - Critical ACs 100% passed
   - No critical findings

2. **Standard Gate (Default)**
   - Use Case: Standard UAT for most stories
   - Pass rate ≥ 90%
   - Critical ACs 100% passed
   - Edge case coverage ≥ 70%
   - No critical findings
   - ≤ 2 major findings

3. **Strict Gate**
   - Use Case: Production-critical features, security stories
   - Pass rate ≥ 95%
   - Critical ACs 100% passed
   - Edge case coverage ≥ 85%
   - No critical or major findings
   - All evidence high quality

**Review Process:**

1. Load test artifacts (results, test cases, story)
2. Analyze pass/fail ratio (overall, by test type, by AC)
3. Identify coverage gaps (missing tests, failed ACs)
4. Analyze edge cases and error scenarios
5. Check evidence quality (descriptive failures, logs, screenshots)
6. Generate review findings (failures, gaps, blockers, quality issues)
7. Provide approval decision (evaluate against quality gate)
8. Prompt human reviewer to confirm or override
9. Create stakeholder summary (non-technical)

**UAT Status Values:**

- **APPROVED**: All quality gate criteria met, ready for production
  - Next Steps: Mark story as done, prepare for deployment

- **CHANGES REQUESTED**: Quality gate criteria not met, specific changes needed
  - Next Steps: Review required changes, fix issues, re-run execute-tests

- **BLOCKED**: Critical blockers prevent AC validation
  - Next Steps: Resolve blockers (fixtures, setup, dependencies), re-run execute-tests

**Finding Severity Criteria:**

- **Critical**: Failure in critical AC, no tests for critical AC, data corruption, security issue
- **Major**: Failure in standard AC, no tests for standard AC, missing error coverage
- **Minor**: Edge case failure, non-critical scenario gap, evidence quality issues

**Usage Examples:**

```bash
# Standard review
workflow review-uat-results

# Strict review for critical feature
workflow review-uat-results quality_gate_level=strict

# Minimal review for early testing
workflow review-uat-results quality_gate_level=minimal

# Specific test results with auto-approval
workflow review-uat-results \
  test_results_file=docs/uat/test-results/2.5-2-test-results.md \
  auto_approve_if_all_pass=true
```

**Stakeholder Summary Example:**

```markdown
## Stakeholder Summary

**What We Tested**: UAT Workflow Framework with 4 workflows

**Results**: 92% of tests passed (23/25)

**Acceptance Criteria Status**:
- 5 of 6 ACs fully validated ✓
- 1 AC partially validated ⚠️

**Bottom Line**: Story nearly complete, 2 minor issues to address

**What Happens Next**: Fix minor issues, re-test, expected approval in 1-2 days
```

#### Workflow Sequence and Handoff Points

**1. Story Creation → Test Case Generation**
- Trigger: Story file created with acceptance criteria
- Handoff: Story markdown file path
- Handoff Point: Story file contains structured ACs (AC-X-Y-Z format)

**2. Test Case Generation → Test Context Building**
- Trigger: Test cases file generated
- Handoff: Test cases markdown file path
- Handoff Point: Test cases file complete with all scenarios

**3. Test Context Building → Test Execution**
- Trigger: Test context XML generated
- Handoff: Test context XML file path + test cases file path
- Handoff Point: Test context complete, fixtures available or identified as missing

**4. Test Execution → UAT Review**
- Trigger: Test execution complete
- Handoff: Test results markdown file path
- Handoff Point: All tests executed (pass/fail/blocked status recorded)

**5. UAT Review → Story Completion**
- Trigger: UAT status = APPROVED
- Handoff: UAT review markdown file path
- Handoff Point: Quality gates met, human reviewer approved

**Iteration Loops:**

```
execute-tests → review-uat-results → CHANGES REQUESTED → fix code → execute-tests
execute-tests → review-uat-results → BLOCKED → resolve blockers → execute-tests
```

#### Integration with Existing Story Development Workflows

The UAT framework complements the existing BMM story development workflow:

```
Story Creation (create-story)
    ↓
Story Context (story-context) ← Development focus
    ↓                            ↓
Test Cases (create-test-cases) ← Testing focus (UAT Framework)
    ↓                            ↓
Development (dev-story)      Test Context (build-test-context)
    ↓                            ↓
Code Review (code-review)    Test Execution (execute-tests)
    ↓                            ↓
Story Done (story-done) ← UAT Review (review-uat-results)
```

**Parallel Workflows:**
- **story-context**: Generates development context XML with code artifacts
- **create-test-cases**: Generates testing context with test scenarios
- Both workflows can run independently or leverage each other's outputs

**Quality Gates:**
- **Code Review**: Technical code quality gate (Senior Developer review)
- **UAT Review**: Functional quality gate (QA approval with acceptance criteria validation)

#### Output Locations and File Structure

```
docs/
└── uat/
    ├── test-cases/
    │   ├── 2.5-3.1-test-cases.md
    │   ├── 2.5-2-test-cases.md
    │   └── ...
    │
    ├── test-context/
    │   ├── 2.5-3.1-test-context.xml
    │   ├── 2.5-2-test-context.xml
    │   └── ...
    │
    ├── test-results/
    │   ├── 2.5-3.1-test-results.md
    │   ├── 2.5-2-test-results.md
    │   └── ...
    │
    └── reviews/
        ├── 2.5-3.1-uat-review.md
        ├── 2.5-2-uat-review.md
        └── ...
```

**Naming Convention:**
- Test cases: `{story_key}-test-cases.md`
- Test context: `{story_key}-test-context.xml`
- Test results: `{story_key}-test-results.md`
- UAT review: `{story_key}-uat-review.md`

**File Lifecycle:**
1. Test cases file: Created once, may be updated if ACs change
2. Test context file: Regenerated when fixtures or helpers change
3. Test results file: Created per execution run, timestamped if multiple runs
4. UAT review file: Created per review, timestamped if multiple reviews

#### Usage Examples

**Example 1: Complete UAT Flow for New Story**

```bash
# Step 1: Generate test cases from story
workflow create-test-cases \
  story_path=docs/stories/2.5-3.1-uat-workflow-framework.md \
  test_coverage_level=standard

# Output: docs/uat/test-cases/2.5-3.1-test-cases.md

# Step 2: Build test context
workflow build-test-context

# Output: docs/uat/test-context/2.5-3.1-test-context.xml

# Step 3: Execute tests
workflow execute-tests test_execution_mode=hybrid

# Output: docs/uat/test-results/2.5-3.1-test-results.md

# Step 4: Review UAT results
workflow review-uat-results quality_gate_level=standard

# Output: docs/uat/reviews/2.5-3.1-uat-review.md
# Status: APPROVED / CHANGES REQUESTED / BLOCKED
```

**Example 2: CI/CD Automated Testing**

```bash
# Automated tests only (no manual tests, no user interaction)
workflow create-test-cases test_coverage_level=minimal
workflow build-test-context include_story_context=false
workflow execute-tests test_execution_mode=automated
workflow review-uat-results quality_gate_level=minimal auto_approve_if_all_pass=true
```

**Example 3: Re-test After Changes**

```bash
# After fixing issues from UAT review, re-run execution and review
workflow execute-tests
workflow review-uat-results
```

**Example 4: Comprehensive Testing for Critical Feature**

```bash
# Maximum coverage and strict quality gates
workflow create-test-cases test_coverage_level=comprehensive
workflow build-test-context
workflow execute-tests capture_screenshots=true
workflow review-uat-results quality_gate_level=strict
```

#### Configuration and Customization

**BMM Config (`bmad/bmm/config.yaml`):**
- `dev_story_location`: Where to find story files
- `output_folder`: Where to save UAT artifacts (docs/)
- `user_name`: Document author / test executor / reviewer
- `communication_language`: Workflow interaction language

**Workflow-Specific Config (`workflow.yaml` in each workflow directory):**

- **create-test-cases**:
  - `default_coverage_level`: minimal/standard/comprehensive
  - `test_case_template`: Template for test case structure

- **build-test-context**:
  - `fixture_root`: Path to tests/fixtures/
  - `conftest_paths`: List of conftest.py locations
  - `pytest_ini_path`: Path to pytest.ini

- **execute-tests**:
  - `pytest_args`: Default pytest arguments (-v --tb=short)
  - `pytest_timeout`: Test timeout in seconds (300)
  - `tmux_idle_time`: Seconds to wait for CLI idle (2.0)
  - `tmux_timeout`: Timeout for tmux operations (60)
  - `continue_on_failure`: true (default) / false

- **review-uat-results**:
  - `default_quality_gate`: minimal/standard/strict
  - `auto_approve_threshold`: Pass rate for auto-approval (100%)
  - `require_human_review`: true (default) / false

#### Benefits and Value Proposition

**For Developers:**
- Clear test requirements upfront (shift-left testing)
- Automated test execution reduces manual effort
- Immediate feedback on implementation vs. acceptance criteria
- Reduced rework from catching issues early

**For QA:**
- Systematic validation of all acceptance criteria
- Consistent quality gates across all stories
- Evidence-based approval decisions
- Stakeholder-friendly reporting
- Reduced manual test documentation effort

**For Product Owners:**
- Transparent acceptance criteria validation
- Non-technical stakeholder summaries
- Clear approval/changes-requested/blocked status
- Traceability from requirements to test results

**For the Team:**
- Repeatable process across all stories
- Reduced context switching between dev and test
- AI-assisted execution reduces cognitive load
- Comprehensive audit trail for compliance

#### Lessons Learned and Best Practices

**Best Practices (Established in Story 2.5.3.1):**

1. **Run create-test-cases early**: Generate test cases before or during development to understand requirements
2. **Use standard coverage**: Comprehensive coverage is overkill for most stories, minimal coverage misses edge cases
3. **Leverage test context**: Reuse story context XML to avoid duplication in test context
4. **Review test cases before execution**: Validate test scenarios cover all ACs before investing in execution
5. **Continue on failure (default)**: Get complete picture of failures, don't stop at first issue
6. **Require human review**: Never auto-approve without human oversight (even if all tests pass)
7. **Use appropriate quality gate**: Match quality gate to story criticality (standard for most, strict for security/data)

**Common Pitfalls:**

1. **Skipping test case generation**: Jumping straight to execute-tests without test cases loses structure
2. **Missing fixtures**: Not running build-test-context leads to blocked tests during execution
3. **Ignoring CHANGES REQUESTED**: Marking story done before resolving UAT review findings
4. **Over-reliance on manual tests**: Use automated tests (pytest, CLI) when possible for repeatability
5. **Poor evidence capture**: Not capturing logs/screenshots makes debugging failures difficult

#### Future Enhancements (Out of Scope for Epic 2.5)

- **Test case templates**: Industry-specific test case templates (audit, compliance, security)
- **Fixture generation**: Automated fixture generation based on test case requirements
- **Parallel execution**: Execute multiple test suites in parallel for faster results
- **Historical trending**: Track UAT pass rates over time, identify flaky tests
- **Integration with CI/CD**: Trigger UAT workflows on commit/merge
- **Test case reuse**: Library of reusable test scenarios for common patterns

## Non-Functional Requirements

### Performance

**NFR-P1: Batch Processing Throughput** (VALIDATE)
- **Target:** 100 mixed-format files processed in <10 minutes
- **Current State:** Unknown - Story 2.5.1 establishes baseline
- **Validation:** Automated performance tests in CI (weekly runs)
- **Measurement:** `tests/performance/test_throughput.py` with psutil monitoring

**NFR-P2: Memory Footprint** (VALIDATE)
- **Target:** Peak memory usage <2GB during batch processing
- **Current State:** Unknown - Story 2.5.1 validates streaming architecture
- **Validation:** Memory profiling during large document processing
- **Measurement:** psutil memory monitoring in integration tests

**NFR-P3: Individual File Processing** (INHERITED from PRD)
- **Target:** <5 seconds per document (excluding OCR), <10 seconds per scanned page
- **Current State:** Assumed compliant from Epic 2 - Story 2.5.1 confirms
- **Validation:** Per-file timing in performance tests

**spaCy Performance** (NEW for Epic 2.5.2):
- **Model Load Time:** <5 seconds for en_core_web_md initial load
- **Sentence Segmentation:** <100ms for 1000-word document
- **Validation:** Unit tests measure execution time

**Performance Regression Detection:**
- Baseline metrics documented in Story 2.5.1
- Future epics must not degrade throughput >10% without justification
- CI pipeline tracks performance trends (weekly reports)

### Security

**NFR-S1: Dependency Security** (STRENGTHEN)
- **spaCy 3.7.2:** Verify no known CVEs before installation
- **Profiling Tools:** psutil, cProfile, memory_profiler from official PyPI only
- **Pinned Versions:** All new dependencies locked in pyproject.toml
- **Validation:** Dependabot alerts monitored, no HIGH/CRITICAL vulnerabilities

**NFR-S2: Test Fixture Security** (Story 2.5.3)
- **Sanitization:** All large document fixtures must have sensitive data removed
- **No PII:** Test PDFs/Excel files contain synthetic audit data only
- **Repository Safety:** Fixtures committed to version control must be publicly safe
- **Validation:** Manual review of each fixture before commit

**NFR-S3: Code Quality Security** (Code Review Blockers)
- **Type Safety:** Fix all Mypy violations (strict mode compliance)
- **Linting:** Ruff checks must pass with 0 errors
- **Pre-commit Hooks:** Enforce quality gates before commit
- **Validation:** CI pipeline blocks merges on quality gate failures

### Reliability/Availability

**NFR-R1: Deterministic Performance** (VALIDATE)
- **Consistency:** Same 100-file batch produces identical throughput metrics across runs
- **Reproducibility:** Performance tests run on same hardware/config produce <5% variance
- **Validation:** Run performance suite 3x, verify standard deviation <5%

**NFR-R2: Graceful Degradation** (VALIDATE)
- **Large Files:** Pipeline continues processing batch even if one large file fails
- **Memory Spikes:** No OOM crashes on 50+ page PDFs or 10K+ row Excel files
- **Error Recovery:** Failed files logged with actionable error messages
- **Validation:** Integration tests with intentionally problematic fixtures

**NFR-R3: spaCy Model Availability** (Story 2.5.2)
- **Offline Support:** en_core_web_md model bundled or downloadable during setup
- **Fallback:** Clear error message if model missing (not silent failure)
- **Validation:** Tests check model existence before attempting to load
- **Documentation:** Setup instructions include model download step

**NFR-R4: Test Infrastructure Reliability**
- **CI Stability:** Performance tests must not flake (false positives/negatives)
- **Fixture Integrity:** Large test fixtures validated with checksums
- **Isolation:** Performance tests don't interfere with unit/integration tests
- **Validation:** CI runs performance suite separately, weekly schedule

### Observability

**NFR-O1: Performance Metrics Tracking** (Story 2.5.1)
- **Metrics Collected:** Throughput (files/min), memory (peak/avg), CPU utilization, bottleneck locations
- **Storage:** Performance test results logged to CI artifacts, trends tracked over time
- **Visibility:** CI dashboard shows performance trends (green if <10% degradation from baseline)
- **Validation:** Weekly performance CI job publishes metrics report

**NFR-O2: Profiling Data Analysis** (Story 2.5.1)
- **Tool:** cProfile generates detailed call graphs and timing data
- **Output:** Profile stats saved to `profile.stats`, analyzed with pstats or snakeviz
- **Actionable:** Top 10 bottlenecks identified with line-level precision
- **Documentation:** Profiling results documented in Story 2.5.1 completion notes

**NFR-O3: Test Execution Reporting**
- **Coverage:** pytest-cov reports coverage for new test modules
- **Test Times:** pytest reports execution time per test (identify slow tests)
- **CI Integration:** Test results published to CI dashboard with pass/fail status
- **Markers:** Performance tests tagged with `@pytest.mark.performance` for selective execution

**NFR-O4: spaCy Integration Visibility** (Story 2.5.2)
- **Model Info:** Log spaCy model version, language, and size on load
- **Segmentation Stats:** Log sentence count, avg sentence length for processed documents
- **Error Logging:** spaCy failures logged with context (input text snippet, stack trace)
- **Validation:** Integration tests verify logging output contains expected fields

## Dependencies and Integrations

### New Dependencies (Added in Epic 2.5)

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

### Existing Dependencies (No Changes)

All dependencies from Epic 1 and Epic 2 remain unchanged:
- pydantic >= 2.0.0 - Data validation
- pytest >= 8.0.0 - Testing framework
- black, ruff, mypy - Code quality tools
- PyMuPDF, python-docx, openpyxl, pytesseract - Document extraction
- structlog - Structured logging

### System Requirements

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

### Integration Points

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

### Dependency Security

**Verification Steps:**
1. Check spaCy 3.7.2 for known CVEs before installation
2. Verify psutil, memory_profiler from official PyPI (no typosquatting)
3. Pin all versions in pyproject.toml
4. Enable Dependabot alerts for new vulnerabilities
5. Review dependency licenses (all MIT/BSD/Apache 2.0 compatible)

## Acceptance Criteria (Authoritative)

### Story 2.5.1: Performance Validation & Optimization

**AC-2.5.1.1:** 100-file batch processes within NFR-P1 target
- 100 mixed-format files (PDFs, DOCX, XLSX) process in <10 minutes
- Measured with real timer, not estimates
- Test batch includes variety of file sizes and formats

**AC-2.5.1.2:** Memory usage stays within NFR-P2 limits
- Peak memory <2GB during 100-file batch processing
- Measured with psutil process monitoring
- No memory leaks detected (memory returns to baseline after batch)

**AC-2.5.1.3:** Performance bottlenecks identified and documented
- cProfile run generates profile.stats file
- Top 10 slowest functions identified with line numbers
- Bottlenecks documented in Story 2.5.1 completion notes

**AC-2.5.1.4:** Critical bottlenecks optimized
- Slowest operation(s) improved by measurable amount
- Performance improvement validated with before/after benchmarks
- No regressions introduced in optimization (tests still pass)

**AC-2.5.1.5:** Automated performance test suite created
- tests/performance/test_throughput.py exists and runs successfully
- Tests validate NFR-P1 (throughput) and NFR-P2 (memory)
- Performance CI job configured (weekly schedule)

**AC-2.5.1.6:** Baseline metrics documented
- Throughput (files/min), memory (peak/avg), CPU utilization recorded
- Baseline documented in test docstrings or separate metrics file
- Future epics can compare against baseline to detect regressions

### Story 2.5.2: spaCy Integration & Validation

**AC-2.5.2.1:** spaCy 3.7.2 installed and validated
- `python -m spacy validate` succeeds
- spaCy version check returns 3.7.2
- Installation documented in pyproject.toml

**AC-2.5.2.2:** en_core_web_md model downloaded and loadable
- `python -m spacy download en_core_web_md` completes successfully
- Model loads in Python: `nlp = spacy.load("en_core_web_md")` works
- Model version and size logged on load

**AC-2.5.2.3:** Sentence segmentation accuracy validated
- Accuracy ≥95% on gold standard test corpus
- Test corpus includes edge cases (abbreviations, acronyms, complex punctuation)
- Accuracy metric documented in test results

**AC-2.5.2.4:** get_sentence_boundaries() utility function implemented
- Function exists in src/data_extract/utils/nlp.py
- Signature: `get_sentence_boundaries(text: str, nlp: Language = None) -> List[int]`
- Returns character positions of sentence ends
- Handles edge cases: empty text (raises ValueError), single sentence, multi-paragraph

**AC-2.5.2.5:** Unit tests cover utility function edge cases
- Test empty/whitespace-only text (expect ValueError)
- Test single sentence (returns one boundary)
- Test multi-sentence text (returns multiple boundaries)
- Test with/without provided nlp model parameter

**AC-2.5.2.6:** Integration tests validate spaCy pipeline
- tests/integration/test_spacy_integration.py exists and passes
- Tests model loading, sentence segmentation, error handling
- Tests run in CI pipeline

**AC-2.5.2.7:** Documentation updated with spaCy setup
- CLAUDE.md includes spaCy installation steps
- README.md mentions model download requirement
- Troubleshooting guide created for common spaCy issues

### Story 2.5.3: Large Document Fixtures & UAT Framework

**AC-2.5.3.1:** Large PDF fixture created (50+ pages)
- PDF with ≥50 pages added to tests/fixtures/pdfs/large/
- Content sanitized (no PII or sensitive audit data)
- Structure preserved (headings, tables, images representative of audit docs)

**AC-2.5.3.2:** Large Excel fixture created (10K+ rows)
- Excel file with ≥10,000 rows added to tests/fixtures/xlsx/large/
- Simulates audit data structure (risks, controls, policies, etc.)
- Content synthetic, no real organization data

**AC-2.5.3.3:** Scanned PDF fixture created (OCR required)
- Scanned/image-based PDF added to tests/fixtures/pdfs/scanned/
- Tests OCR pipeline end-to-end
- Representative of real-world scanned audit documents

**AC-2.5.3.4:** Fixture creation process documented
- tests/fixtures/README.md describes how fixtures were created
- Includes sanitization steps and tools used
- Enables future contributors to add more fixtures

**AC-2.5.3.5:** Integration tests for large files passing
- tests/integration/test_large_files.py exists and passes
- Tests process large PDF without memory spike
- Tests process large Excel without timeout
- Tests scanned PDF OCR completes successfully

**AC-2.5.3.6:** Memory monitoring validates NFR-P2 for large files
- psutil tracks memory during large file processing
- Peak memory <2GB for individual large files
- No OOM crashes on large documents

**AC-2.5.3.7:** UAT workflow structure designed
- Design documented for bmad:bmm:workflows:create-test-cases
- Input: Story markdown files with acceptance criteria
- Output: Test scenarios and execution framework
- Integration with tmux-cli for CLI testing considered

**AC-2.5.3.8:** CLAUDE.md updated with Epic 2 lessons
- "Lessons from Epic 2" section added to CLAUDE.md
- Documents quality gate patterns (Black/Ruff/Mypy first)
- Documents PipelineStage protocol scaling lessons
- Documents anti-patterns to avoid

**AC-2.5.3.9:** Code review blockers resolved
- validation.py:694, 719, 736 fixed (add document_average_confidence, scanned_pdf_detected)
- validation.py:697 unused variable removed (ocr_validation_performed)
- Quality gates re-run: `black && ruff && mypy` all pass with 0 violations
- Proof of 0 violations documented in completion notes

## Traceability Mapping

| Acceptance Criteria | Spec Section | Component | Test Approach |
|---------------------|--------------|-----------|---------------|
| AC-2.5.1.1: 100-file batch <10 min | Performance / NFR-P1 | tests/performance/test_throughput.py | Automated test with timer |
| AC-2.5.1.2: Memory <2GB | Performance / NFR-P2 | tests/performance/test_throughput.py | psutil memory monitoring |
| AC-2.5.1.3: Bottlenecks identified | Detailed Design / Workflows | cProfile output analysis | Manual profile review |
| AC-2.5.1.4: Bottlenecks optimized | Performance / NFR-P1 | Pipeline code optimizations | Before/after benchmarks |
| AC-2.5.1.5: Performance test suite | Services and Modules | tests/performance/test_throughput.py | Test execution verification |
| AC-2.5.1.6: Baseline documented | Observability / NFR-O1 | Test docstrings / metrics file | Documentation review |
| AC-2.5.2.1: spaCy installed | Dependencies | pyproject.toml, spaCy CLI | `python -m spacy validate` |
| AC-2.5.2.2: Model downloaded | Dependencies | en_core_web_md | Model load test |
| AC-2.5.2.3: 95%+ accuracy | APIs and Interfaces | Sentence segmentation tests | Gold standard corpus test |
| AC-2.5.2.4: get_sentence_boundaries() | Data Models / APIs | src/data_extract/utils/nlp.py | Function implementation review |
| AC-2.5.2.5: Unit tests | APIs and Interfaces | tests/unit/test_nlp.py | Unit test execution |
| AC-2.5.2.6: Integration tests | APIs and Interfaces | tests/integration/test_spacy_integration.py | Integration test execution |
| AC-2.5.2.7: Documentation updated | Dependencies | CLAUDE.md, README.md | Documentation review |
| AC-2.5.3.1: Large PDF fixture | Services and Modules | tests/fixtures/pdfs/large/ | Fixture file verification |
| AC-2.5.3.2: Large Excel fixture | Services and Modules | tests/fixtures/xlsx/large/ | Fixture file verification |
| AC-2.5.3.3: Scanned PDF fixture | Services and Modules | tests/fixtures/pdfs/scanned/ | Fixture file verification |
| AC-2.5.3.4: Fixture docs | Services and Modules | tests/fixtures/README.md | Documentation review |
| AC-2.5.3.5: Large file tests | APIs and Interfaces | tests/integration/test_large_files.py | Integration test execution |
| AC-2.5.3.6: Memory monitoring | Reliability / NFR-R2 | psutil integration | Memory spike detection test |
| AC-2.5.3.7: UAT workflow design | Services and Modules | bmad:bmm:workflows:create-test-cases | Design document review |
| AC-2.5.3.8: CLAUDE.md lessons | System Architecture | CLAUDE.md | Documentation review |
| AC-2.5.3.9: Code review blockers | APIs and Interfaces | src/data_extract/normalize/validation.py | Quality gate execution |

**Epic 2.5 → PRD Traceability:**
- **NFR-P1 (Performance)** → Story 2.5.1 → Validates 100-file batch throughput
- **NFR-P2 (Memory)** → Story 2.5.1 → Validates streaming architecture memory limits
- **NFR-R2 (Graceful Degradation)** → Story 2.5.3 → Large file processing without crashes
- **NFR-M4 (Testability)** → All Stories → Comprehensive test coverage expansion
- **NFR-C1 (Python 3.12)** → Story 2.5.2 → spaCy compatibility validation

**Epic 2.5 → Epic 3 Preparation:**
- Story 2.5.2 → Epic 3 Story 3.1 → `get_sentence_boundaries()` enables semantic chunking
- Story 2.5.1 → Epic 3 → Performance baselines detect chunking overhead
- Story 2.5.3 → Epic 3 → Large fixtures support chunk quality validation

## Risks, Assumptions, Open Questions

### Risks

**Risk-1: Performance targets may not be achievable without major refactoring**
- **Description:** Current pipeline may have fundamental bottlenecks preventing NFR-P1 (<10 min for 100 files)
- **Impact:** HIGH - Would require Epic 1/2 code rework
- **Likelihood:** LOW - Epic 2 designed with performance in mind
- **Mitigation:** Story 2.5.1 identifies bottlenecks early. If major refactoring needed, escalate to product owner for timeline adjustment vs. relaxed NFR.

**Risk-2: spaCy model download fails in enterprise environment**
- **Description:** Corporate firewall may block model downloads, or no internet access
- **Impact:** MEDIUM - Blocks Story 2.5.2 and Epic 3
- **Likelihood:** MEDIUM (enterprise environment restrictions)
- **Mitigation:** Document offline model installation process. Bundle model with repository if allowed. Request IT exception for spaCy model downloads.

**Risk-3: Large test fixtures difficult to sanitize**
- **Description:** Real audit documents contain sensitive data, synthetic data may not represent complexity
- **Impact:** MEDIUM - Test fixtures may not catch real-world edge cases
- **Likelihood:** MEDIUM
- **Mitigation:** Use publicly available audit reports (government disclosures, public companies). Generate synthetic data with realistic structure. Accept some trade-off between sanitization and realism.

**Risk-4: Code review blockers indicate deeper technical debt**
- **Description:** Mypy/Ruff violations may be symptoms of broader code quality issues
- **Impact:** MEDIUM - May require more extensive refactoring than Story 2.5.3 scope
- **Likelihood:** LOW - Violations are minor (missing optional fields, unused variable)
- **Mitigation:** Fix immediate blockers in Story 2.5.3. Document any deeper issues found for future tech debt epic.

### Assumptions

**Assumption-1:** Current pipeline architecture supports performance targets
- **Validation:** Story 2.5.1 performance tests will confirm
- **If False:** May need ADR revision or NFR adjustment

**Assumption-2:** spaCy en_core_web_md is sufficient for sentence segmentation
- **Validation:** Story 2.5.2 accuracy tests (95%+ target)
- **If False:** May need larger model (en_core_web_lg) or custom training

**Assumption-3:** 100-file test batch is representative of production workloads
- **Validation:** Compare test batch diversity to actual audit document corpus
- **If False:** Adjust test batch composition to better match production

**Assumption-4:** Developer has access to create/source large test fixtures
- **Validation:** Check availability of public audit documents or synthetic data generators
- **If False:** Request samples from stakeholders (sanitized) or use generic large documents

### Open Questions

**Question-1:** Should performance tests run on every commit or weekly?
- **Context:** Performance tests are slow (10+ minutes), may slow CI pipeline
- **Decision Needed By:** Story 2.5.1
- **Recommendation:** Weekly schedule in CI, developers can run manually as needed. Track trends, alert on >10% degradation.

**Question-2:** What sentence segmentation accuracy is acceptable?
- **Context:** 95% is target, but 100% may be impossible (NLP inherent ambiguity)
- **Decision Needed By:** Story 2.5.2
- **Recommendation:** Accept 95%+ as success. Document known failure modes (e.g., abbreviations). Perfect accuracy not required for RAG chunking.

**Question-3:** Should UAT workflow be implemented now or deferred?
- **Context:** Story 2.5.3 includes UAT workflow design, but implementation may be extensive
- **Decision Needed By:** Story 2.5.3
- **Recommendation:** Design only in Epic 2.5. Implement in future epic if UAT automation proves valuable after Epic 2/3.

**Question-4:** How should performance baselines be stored long-term?
- **Context:** Baselines needed for trend analysis, but test docstrings may not be sufficient
- **Decision Needed By:** Story 2.5.1
- **Recommendation:** Store in separate `docs/performance-baselines.md` or CI artifact storage. Include timestamp, hardware specs, Epic/Story context.

## Test Strategy Summary

### Test Levels

**Performance Tests** (tests/performance/) - NEW in Epic 2.5
- **Scope:** Validate NFR-P1 (throughput) and NFR-P2 (memory usage) under load
- **Coverage Target:** 100-file batch, large individual files (50+ pages, 10K+ rows)
- **Approach:** Real processing with psutil monitoring, cProfile profiling, before/after benchmarks
- **Execution:** Weekly in CI (too slow for every commit), manual runs by developers
- **Success Criteria:** <10 min for 100 files, <2GB peak memory, baseline documented

**Integration Tests** (tests/integration/) - EXPANDED in Epic 2.5
- **Scope:** spaCy integration, large file processing, end-to-end pipeline validation
- **Coverage Target:** All new integration points (spaCy model loading, sentence segmentation, large file streaming)
- **Approach:** Real fixtures, real spaCy model, memory monitoring during execution
- **Execution:** Every commit in CI (alongside existing integration tests)
- **Success Criteria:** All integration tests pass, no memory spikes, 95%+ spaCy accuracy

**Unit Tests** (tests/unit/) - NEW for Epic 2.5.2
- **Scope:** get_sentence_boundaries() utility function edge cases
- **Coverage Target:** 100% coverage of nlp.py utility functions
- **Approach:** Mock spaCy model where appropriate, test edge cases (empty text, single sentence, etc.)
- **Execution:** Every commit in CI (fast tests)
- **Success Criteria:** All unit tests pass, edge cases handled correctly

**Manual Testing** (Story 2.5.1 Profiling)
- **Scope:** cProfile analysis, bottleneck identification, optimization validation
- **Coverage Target:** Entire pipeline execution flow
- **Approach:** Run cProfile, analyze output with pstats/snakeviz, document top 10 bottlenecks
- **Execution:** Once during Story 2.5.1, repeat after optimizations
- **Success Criteria:** Bottlenecks identified with line-level precision, documented

### Test Frameworks and Tools

- **pytest:** Primary test framework (existing)
- **pytest-cov:** Coverage measurement (existing)
- **pytest.mark.performance:** New marker for performance tests
- **psutil:** Memory and CPU monitoring (new)
- **cProfile:** Performance profiling (built-in, no install)
- **memory_profiler:** Line-by-line memory profiling (new, optional)
- **spaCy test utilities:** Model validation and accuracy testing (new)

### Coverage Strategy

**Epic 2.5 Coverage Targets:**
- Performance tests: 100% of NFR-P1, NFR-P2 validation scenarios
- spaCy integration: 100% of model loading, segmentation, error handling paths
- Large file processing: 100% of large fixture types (PDF, Excel, scanned)
- Utility functions: 100% of get_sentence_boundaries() code paths
- Code review fixes: 100% of validation.py bug fixes validated by type checker

**Overall Project Coverage:**
- Baseline established in Epic 1: ~60%
- After Epic 2: ~75% (target from PRD)
- After Epic 2.5: ~78% (incremental improvement with test infrastructure)
- Target for Epic 3+: >80%

### Edge Cases and Error Conditions

**Performance Edge Cases:**
- Very large files (100+ pages, 50K+ rows) - ensure no OOM
- Mixed batch with some corrupted files - ensure batch continues
- Rapid successive batches - ensure no memory leaks between runs
- Cold start vs. warm start - document model loading overhead

**spaCy Edge Cases:**
- Empty text input - expect ValueError with clear message
- Single sentence - return single boundary position
- Text with complex punctuation (abbreviations, acronyms) - measure accuracy
- Model not installed - graceful error with setup instructions
- Model load failure - clear error message, not silent failure

**Large File Edge Cases:**
- Streaming processing maintains constant memory (not batch load)
- Progress reporting accurate for large files
- Timeout handling for extremely slow OCR processing
- Corrupted large files don't crash entire batch

### Acceptance Criteria Validation

**Story 2.5.1 Validation:**
1. Automated: pytest performance tests assert <10 min, <2GB
2. Manual: cProfile output reviewed, bottlenecks documented
3. Automated: Baseline metrics written to file/docstrings, CI job configured

**Story 2.5.2 Validation:**
1. Automated: `python -m spacy validate` in CI
2. Automated: pytest integration tests for model loading, segmentation accuracy
3. Automated: pytest unit tests for get_sentence_boundaries()
4. Manual: Documentation review (CLAUDE.md, README.md updates)

**Story 2.5.3 Validation:**
1. Manual: Fixture file review (sanitization, structure)
2. Automated: pytest integration tests process fixtures without errors
3. Automated: psutil monitoring asserts <2GB for large files
4. Manual: Documentation review (tests/fixtures/README.md, CLAUDE.md lessons)
5. Automated: Black, Ruff, Mypy run with 0 violations (CI enforcement)

### Definition of Done for Epic 2.5

- [ ] All story acceptance criteria validated (18 ACs across 3 stories)
- [ ] Performance baseline documented (<10 min for 100 files confirmed)
- [ ] spaCy 3.7.2 installed, en_core_web_md model validated, 95%+ accuracy achieved
- [ ] Large test fixtures added (50+ page PDF, 10K+ row Excel, scanned PDF)
- [ ] Integration tests passing for spaCy and large files
- [ ] Code review blockers resolved (validation.py Mypy/Ruff clean)
- [ ] Documentation updated (CLAUDE.md, README.md, fixtures README)
- [ ] CI pipeline green (all tests pass, no quality gate violations)
- [ ] Epic 2.5 marked as "contexted" in sprint-status.yaml
- [ ] Ready for Epic 3 Story 3.1 (semantic chunking with spaCy)

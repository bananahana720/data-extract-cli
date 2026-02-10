# Detailed Design

## Services and Modules

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

## Data Models and Contracts

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

## APIs and Interfaces

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

## Workflows and Sequencing

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

## UAT Workflow Framework

**Overview:**
Epic 2.5 introduces a comprehensive UAT (User Acceptance Testing) workflow framework to systematically validate story acceptance criteria. The framework consists of four integrated workflows that transform story requirements into executable test cases, prepare test infrastructure, execute tests with AI assistance, and provide senior QA review with approval gates.

**Purpose:**
- Ensure systematic validation of all acceptance criteria
- Provide repeatable testing process across all stories
- Enable AI-assisted test execution with human oversight
- Establish quality gates for UAT approval
- Generate stakeholder-friendly test reports

### UAT Workflow Pipeline

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

### Workflow Descriptions

#### 1. Create Test Cases Workflow

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
## Test Case TC-{story_key}-{ac_num}-{scenario_num}

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

#### 2. Build Test Context Workflow

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

#### 3. Execute Tests Workflow

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

#### 4. Review UAT Results Workflow

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
# Stakeholder Summary

**What We Tested**: UAT Workflow Framework with 4 workflows

**Results**: 92% of tests passed (23/25)

**Acceptance Criteria Status**:
- 5 of 6 ACs fully validated ✓
- 1 AC partially validated ⚠️

**Bottom Line**: Story nearly complete, 2 minor issues to address

**What Happens Next**: Fix minor issues, re-test, expected approval in 1-2 days
```

### Workflow Sequence and Handoff Points

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

### Integration with Existing Story Development Workflows

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

### Output Locations and File Structure

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

### Usage Examples

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

### Configuration and Customization

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

### Benefits and Value Proposition

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

### Lessons Learned and Best Practices

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

### Future Enhancements (Out of Scope for Epic 2.5)

- **Test case templates**: Industry-specific test case templates (audit, compliance, security)
- **Fixture generation**: Automated fixture generation based on test case requirements
- **Parallel execution**: Execute multiple test suites in parallel for faster results
- **Historical trending**: Track UAT pass rates over time, identify flaky tests
- **Integration with CI/CD**: Trigger UAT workflows on commit/merge
- **Test case reuse**: Library of reusable test scenarios for common patterns

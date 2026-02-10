# Create Test Cases Workflow

**Purpose**: Generate comprehensive test case specifications from story acceptance criteria with scenarios and expected outcomes.

**Type**: Document workflow (generates test-cases.md)

**Part of**: BMad UAT Workflow Framework (Story 2.5.3.1)

---

## Overview

The `create-test-cases` workflow analyzes story acceptance criteria and generates structured test cases covering happy path, edge cases, error scenarios, and integration points. It classifies tests by type (unit, integration, CLI, manual, performance) and provides implementation guidance.

## When to Use

- **After story creation**: When a story has been drafted and is ready for development
- **Before implementation**: To understand testing requirements upfront
- **For test planning**: To estimate test effort and identify fixture needs
- **UAT preparation**: As the first step in the UAT workflow pipeline

## Input Requirements

**Required**:
- Story markdown file with acceptance criteria (AC-X-Y-Z format)

**Optional**:
- Epic technical specification (for context and NFRs)
- Test coverage level preference (minimal/standard/comprehensive)

## Output

**File**: `docs/uat/test-cases/{story_key}-test-cases.md`

**Contents**:
- Structured test cases with preconditions, steps, expected results
- Test coverage matrix showing AC → test mapping
- Test type distribution (unit, integration, CLI, manual, performance)
- Implementation notes (fixtures, helpers, pytest markers)
- Risk areas and recommendations

## Usage

### Basic Usage

```bash
workflow create-test-cases
```

The workflow will:
1. Find the first story with status "ready-for-dev"
2. Use standard test coverage level
3. Generate test cases automatically

### Specify Story Path

```bash
workflow create-test-cases story_path=docs/stories/2.5-3.1-uat-workflow-framework.md
```

### Set Coverage Level

```bash
workflow create-test-cases test_coverage_level=comprehensive
```

**Coverage Levels**:
- `minimal`: Happy path only (1 test per AC)
- `standard`: Happy path + edge cases + error cases (3-4 tests per AC) *[default]*
- `comprehensive`: All scenarios + integration + performance (5-8 tests per AC)

## Workflow Pipeline Position

This is **Step 1** in the UAT workflow pipeline:

```
┌─────────────────────┐
│ create-test-cases   │ ← YOU ARE HERE
│ (Story → Test Cases)│
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ build-test-context  │
│ (Gather fixtures)   │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ execute-tests       │
│ (Run tests)         │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ review-uat-results  │
│ (QA approval)       │
└─────────────────────┘
```

## Test Case Structure

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

## Test Type Classification

Tests are automatically classified by execution type:

- **Unit**: Isolated component testing (pytest)
- **Integration**: Multi-component testing (pytest with fixtures)
- **CLI**: Command-line interface testing (tmux-cli integration)
- **Manual**: Human-executed verification
- **Performance**: Benchmarking and NFR validation

## Next Steps After Generation

1. **Review test cases**: Validate coverage and scenarios
2. **Run build-test-context**: Gather fixtures and helpers
   ```bash
   workflow build-test-context
   ```
3. **Implement missing fixtures**: Create any required test data
4. **Execute tests**: Run via execute-tests workflow
5. **QA review**: Run review-uat-results workflow

## Configuration

The workflow uses BMM config values from `bmad/bmm/config.yaml`:

- `dev_story_location`: Where to find story files
- `output_folder`: Where to save test cases (docs/)
- `user_name`: Document author
- `communication_language`: Workflow interaction language

## Examples

### Example 1: Standard Coverage for Current Story

```bash
workflow create-test-cases
```

Output: `docs/uat/test-cases/2.5-3.1-test-cases.md` with 3-4 tests per AC

### Example 2: Comprehensive Coverage for Specific Story

```bash
workflow create-test-cases \
  story_path=docs/stories/2.5-2-spacy-integration.md \
  test_coverage_level=comprehensive
```

Output: `docs/uat/test-cases/2.5-2-test-cases.md` with 5-8 tests per AC

### Example 3: Minimal Coverage for Quick Validation

```bash
workflow create-test-cases test_coverage_level=minimal
```

Output: Test cases with happy path only (1 test per AC)

## Troubleshooting

**Issue**: "No story found with status ready-for-dev"
**Solution**: Provide explicit story_path or update story status

**Issue**: "Epic file not found"
**Solution**: This is optional - workflow continues without epic context

**Issue**: "Output directory doesn't exist"
**Solution**: Workflow creates docs/uat/test-cases/ automatically

## Related Workflows

- **build-test-context**: Gathers fixtures and helpers for test execution
- **execute-tests**: Runs the generated test cases
- **review-uat-results**: QA review and approval of test results
- **story-context**: Generates development context (parallel workflow)

## Integration with Story Development

The UAT workflows complement the story development workflow:

```
Story Creation (create-story)
    ↓
Story Context (story-context) ← Development focus
    ↓                            ↓
Test Cases (create-test-cases) ← Testing focus
    ↓                            ↓
Development (dev-story) + Test Context (build-test-context)
    ↓                            ↓
Code Review (code-review) + Test Execution (execute-tests)
    ↓                            ↓
Story Done (story-done) ← UAT Review (review-uat-results)
```

## Author

Created as part of Epic 2.5 - Testing Infrastructure (Story 2.5.3.1)

## Version

1.0.0 - Initial release

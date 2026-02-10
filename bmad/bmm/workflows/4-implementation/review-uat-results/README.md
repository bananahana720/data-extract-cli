# Review UAT Results Workflow

**Purpose**: AI-assisted QA review of test execution results with gap analysis, approval/changes-requested decision, and stakeholder summary.

**Type**: Document workflow (generates uat-review.md)

**Part of**: BMad UAT Workflow Framework (Story 2.5.3.1)

---

## Overview

The `review-uat-results` workflow provides senior QA review and approval of test execution results. It analyzes pass/fail ratios, identifies coverage gaps, evaluates edge case testing, checks evidence quality, and makes an approval decision based on configurable quality gates. The workflow includes AI-assisted analysis with human review override.

## When to Use

- **After test execution**: When execute-tests workflow has completed
- **For UAT approval**: To validate story meets acceptance criteria
- **Before story completion**: As final gate before marking story done
- **For stakeholder reporting**: To provide executive summary of UAT results

## Input Requirements

**Required**:
- Test execution results file (from execute-tests workflow)

**Optional**:
- Test cases file (derived from test results if not provided)
- Story markdown file (derived from test results if not provided)
- Quality gate level (minimal/standard/strict)
- Reviewer name (defaults to config user_name)

## Output

**File**: `docs/uat/reviews/{story_key}-uat-review.md`

**Contents**:
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

## Usage

### Basic Usage (Standard Quality Gate)

```bash
workflow review-uat-results
```

The workflow will:
1. Load latest test results
2. Analyze with standard quality gate
3. Generate review findings
4. Make approval decision with human review
5. Create comprehensive UAT review report

### Specify Test Results File

```bash
workflow review-uat-results test_results_file=docs/uat/test-results/2.5-3.1-test-results.md
```

### Set Quality Gate Level

```bash
workflow review-uat-results quality_gate_level=strict
```

**Quality Gate Levels**:

- **minimal**: 80% pass rate, critical ACs 100%, no critical findings
- **standard**: 90% pass rate, critical ACs 100%, 70% edge case coverage, ≤2 major findings *[default]*
- **strict**: 95% pass rate, critical ACs 100%, 85% edge case coverage, no major findings, high evidence quality

### Enable Auto-Approval (Not Recommended)

```bash
workflow review-uat-results auto_approve_if_all_pass=true
```

Auto-approves if all tests passed (still generates review report).

## Workflow Pipeline Position

This is **Step 4** (Final Step) in the UAT workflow pipeline:

```
┌─────────────────────┐
│ create-test-cases   │
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
│ review-uat-results  │ ← YOU ARE HERE
│ (QA approval)       │
└─────────────────────┘
           ↓
      Story Done
```

## Review Process

### 1. Load Test Artifacts

Loads:
- Test execution results (pass/fail/blocked counts, evidence)
- Test cases (coverage matrix, scenario types)
- Story (acceptance criteria, objectives)

### 2. Analyze Pass/Fail Ratio

Calculates:
- Overall pass rate
- Pass rate by test type (unit, integration, CLI, manual, performance)
- Critical AC pass rate
- Comparison to quality gate thresholds

### 3. Identify Coverage Gaps

Analyzes:
- ACs with no tests (major gap)
- ACs with only failed/blocked tests (critical gap)
- Missing scenario types (happy path, edge cases, error cases)
- Gaps categorized by severity (critical/major/minor)

### 4. Analyze Edge Cases and Error Scenarios

Evaluates:
- Edge case coverage percentage
- Edge case pass rate
- Error scenario coverage
- Missing boundary conditions and error paths

### 5. Check Evidence Quality

Reviews:
- Failure messages (descriptive?)
- Logs and output (included?)
- Screenshots (for CLI tests)
- Reproduction steps (documented?)
- Root cause (identifiable?)

Rates each piece of evidence as high/medium/low quality.

### 6. Generate Review Findings

Documents:
- **Test Failures** (F-1, F-2, ...): Failed tests with severity and recommendations
- **Coverage Gaps** (G-1, G-2, ...): Missing tests with AC impact
- **Blockers** (B-1, B-2, ...): Tests that couldn't execute
- **Quality Issues** (Q-1, Q-2, ...): Evidence quality, test design problems

Each finding includes:
- Unique ID
- Severity (critical/major/minor)
- AC impact
- Description
- Evidence reference
- Recommendation

### 7. Provide Approval Decision

**Decision Logic**:

1. Check auto-approval (if enabled and all tests passed)
2. Evaluate against quality gate criteria
3. Determine status: APPROVED, CHANGES REQUESTED, or BLOCKED
4. Prompt human reviewer to confirm or override
5. Document rationale

**Approval Criteria**:
- All quality gate thresholds met
- No critical findings
- Major findings within limit
- Evidence quality adequate

### 8. Create Stakeholder Summary

Generates executive summary:
- What was tested
- Results at a glance (percentages)
- AC validation status
- Bottom line recommendation
- Next steps in plain language

## Quality Gate Thresholds

### Minimal Gate

**Use Case**: Early development, exploratory testing

**Criteria**:
- Pass rate ≥ 80%
- Critical ACs 100% passed
- No critical findings

### Standard Gate (Default)

**Use Case**: Standard UAT for most stories

**Criteria**:
- Pass rate ≥ 90%
- Critical ACs 100% passed
- Edge case coverage ≥ 70%
- No critical findings
- ≤ 2 major findings

### Strict Gate

**Use Case**: Production-critical features, security stories

**Criteria**:
- Pass rate ≥ 95%
- Critical ACs 100% passed
- Edge case coverage ≥ 85%
- No critical findings
- No major findings
- All evidence high quality

## UAT Status Values

### APPROVED

All quality gate criteria met. Story is ready for production.

**Next Steps**:
- Mark story as done via story-done workflow
- Prepare for deployment
- Close related tickets

### CHANGES REQUESTED

Quality gate criteria not met. Specific changes needed before approval.

**Next Steps**:
- Review required changes (prioritized list)
- Fix issues in code
- Re-run execute-tests workflow
- Re-run review-uat-results workflow

### BLOCKED

Critical blockers prevent AC validation.

**Next Steps**:
- Resolve blockers (missing fixtures, setup issues, dependencies)
- Re-run execute-tests workflow
- Re-run review-uat-results workflow

## Finding Severity Criteria

### Critical

- Failure in critical AC (security, data integrity, core functionality)
- No tests for critical AC
- Data corruption or security issue
- Blocker preventing validation

### Major

- Failure in standard AC
- No tests for standard AC
- Missing error scenario coverage
- Functional gap

### Minor

- Edge case failure
- Non-critical scenario gap
- Evidence quality issues
- Test design improvements

## Human Review and Override

The workflow always prompts the human reviewer:

```
Review the AI-generated decision. Do you agree with the status: APPROVED?
[approve/request-changes/blocked/override]
```

**Override Options**:
- **approve**: Confirm AI decision
- **request-changes**: Override to request changes with rationale
- **blocked**: Override to blocked status with rationale
- **override**: Change status with custom rationale

All overrides are documented with user rationale.

## Configuration

The workflow uses BMM config values from `bmad/bmm/config.yaml`:

- `dev_story_location`: Where to find story files
- `output_folder`: Where to save UAT reviews (docs/)
- `user_name`: Default reviewer name
- `communication_language`: Workflow interaction language

Quality gate thresholds configured in workflow.yaml.

## Examples

### Example 1: Standard Review

```bash
workflow review-uat-results
```

Output: `docs/uat/reviews/2.5-3.1-uat-review.md`
- Analyzes with standard quality gate (90% pass, 70% edge cases)
- Human review required
- Comprehensive findings and recommendations

### Example 2: Strict Review for Critical Feature

```bash
workflow review-uat-results quality_gate_level=strict
```

Output: Strict quality gate applied (95% pass, 85% edge cases, no major findings)

### Example 3: Minimal Review for Early Testing

```bash
workflow review-uat-results quality_gate_level=minimal
```

Output: Minimal quality gate applied (80% pass, critical ACs only)

### Example 4: Specific Test Results with Auto-Approval

```bash
workflow review-uat-results \
  test_results_file=docs/uat/test-results/2.5-2-test-results.md \
  auto_approve_if_all_pass=true
```

Output: Auto-approves if all tests passed (still generates full review)

## Troubleshooting

**Issue**: "Test results file not found"
**Solution**: Run execute-tests workflow first or provide explicit path

**Issue**: "Quality gate not met"
**Solution**: Review findings, address issues, re-run tests, re-review

**Issue**: "Critical ACs not 100% passed"
**Solution**: Fix critical AC failures (highest priority), re-test

**Issue**: "Evidence quality too low"
**Solution**: Enhance test execution evidence capture, re-run tests

## Next Steps After Review

### If APPROVED

1. **Celebrate**: UAT passed! 🎉
2. **Mark story done**: Run story-done workflow
   ```bash
   workflow story-done
   ```
3. **Prepare deployment**: Follow deployment procedures
4. **Close tickets**: Update issue tracker

### If CHANGES REQUESTED

1. **Review findings**: Read all findings with critical/major priority
2. **Fix issues**: Address root causes in code
3. **Re-run tests**: Execute execute-tests workflow
   ```bash
   workflow execute-tests
   ```
4. **Re-review**: Run review-uat-results workflow again
5. **Iterate**: Repeat until approved

### If BLOCKED

1. **Review blockers**: Read all blocker findings
2. **Resolve blockers**: Generate fixtures, fix setup, resolve dependencies
3. **Re-run tests**: Execute execute-tests workflow
   ```bash
   workflow execute-tests
   ```
4. **Re-review**: Run review-uat-results workflow again

## Integration with Story Development

```
Development (dev-story)
    ↓
Code Review (code-review)
    ↓
Test Execution (execute-tests)
    ↓
UAT Review (review-uat-results) ← YOU ARE HERE
    ↓
    ├─ APPROVED → Story Done (story-done) → Deployment
    ├─ CHANGES REQUESTED → Fix → Re-test → Re-review
    └─ BLOCKED → Resolve → Re-test → Re-review
```

## Stakeholder Communication

The stakeholder summary section is designed for non-technical audiences:

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

## Related Workflows

- **execute-tests**: Provides test results that this workflow reviews
- **create-test-cases**: Provides test coverage reference
- **build-test-context**: Provides test infrastructure reference
- **story-done**: Next workflow if approved

## Quality Assurance Philosophy

The review-uat-results workflow embodies these principles:

- **AI-Assisted, Human-Approved**: AI analyzes, human decides
- **Evidence-Based**: All decisions backed by test evidence
- **Transparent**: Clear rationale for all decisions
- **Actionable**: Specific next steps, not vague recommendations
- **Stakeholder-Friendly**: Technical and non-technical summaries

## Author

Created as part of Epic 2.5 - Testing Infrastructure (Story 2.5.3.1)

## Version

1.0.0 - Initial release

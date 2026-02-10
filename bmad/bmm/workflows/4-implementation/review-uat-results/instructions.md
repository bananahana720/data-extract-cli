# Review UAT Results - Workflow Instructions

<critical>The workflow execution engine is governed by: {project-root}/bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/bmad/bmm/workflows/4-implementation/review-uat-results/workflow.yaml</critical>
<critical>Communicate in {communication_language} throughout the process</critical>

<workflow>

<step n="1" goal="Load test artifacts and results">
<action>If test_results_file not provided, locate latest test results file in {output_folder}/uat/test-results/</action>
<action>If test_cases_file not provided, derive from test results file or find matching test cases</action>
<action>If story_path not provided, derive from test results or find story with matching key</action>

<action>Load test results document and extract:</action>
- Execution summary (total, pass, fail, blocked counts and percentages)
- AC validation status for each acceptance criterion
- Detailed test results by type (pytest, CLI, manual)
- Failed tests with evidence
- Blocked tests with blockers
- Performance observations
- Recommendations from test execution

<action>Load test cases document and extract:</action>
- Test coverage matrix
- Test scenarios and expected outcomes
- Test type distribution
- Original test case objectives

<action>Load story file and extract:</action>
- Story key for output filename
- All acceptance criteria with descriptions
- Story objectives and context
- Any NFRs or quality requirements

<template-output>artifacts_loaded</template-output>
</step>

<step n="2" goal="Analyze test pass/fail ratio">
<action>Calculate key metrics from test results:</action>

**Pass Rate Analysis:**
- Overall pass rate: {pass_count} / {total_count} = {pass_percentage}%
- Pass rate by test type:
  - Unit tests: {unit_pass_rate}%
  - Integration tests: {integration_pass_rate}%
  - CLI tests: {cli_pass_rate}%
  - Manual tests: {manual_pass_rate}%
  - Performance tests: {performance_pass_rate}%

**Compare to quality gate thresholds:**
<action>Load threshold for {quality_gate_level} from quality_thresholds</action>
<action>Check if pass_rate meets threshold</action>
<action>Flag any test types with significantly lower pass rates</action>

**Critical AC Analysis:**
<action>Identify critical acceptance criteria (typically AC-X-Y-1, security, data integrity)</action>
<action>Calculate critical AC pass rate</action>
<action>Check if critical_ac_pass_rate meets threshold (must be 100% for most gates)</action>

<template-output>pass_rate_analysis</template-output>
</step>

<step n="3" goal="Identify gaps in test coverage vs acceptance criteria">
<action>Map test results back to acceptance criteria from story</action>

**Coverage Gap Analysis:**

**Step 3.1: Verify all ACs have test coverage**
<action>For each acceptance criterion in story:</action>
- Count test cases covering this AC
- Check if at least one test passed
- Identify ACs with no tests (critical gap)
- Identify ACs with only failed/blocked tests

**Step 3.2: Identify missing scenario types**
<action>For each AC, check scenario coverage:</action>
- Happy path: At least one happy path test?
- Edge cases: Edge cases covered? (required for standard+ quality gate)
- Error cases: Error scenarios tested?
- Integration points: Cross-component tests?

**Step 3.3: Document coverage gaps**
<action>List gaps by severity:</action>
- **Critical**: ACs with no passing tests
- **Major**: ACs with no tests at all
- **Minor**: Missing edge case or error scenario coverage

<template-output>coverage_gaps</template-output>
</step>

<step n="4" goal="Analyze edge cases and error scenarios coverage">
<action>Focus on non-happy-path testing quality</action>

**Edge Case Analysis:**
<action>From test cases, identify all edge case tests</action>
<action>Calculate edge case pass rate</action>
<action if="quality_gate_level in ['standard', 'strict']">Compare to edge_case_coverage threshold</action>

**Failing edge cases:**
- Which edge cases failed?
- Do failures indicate implementation gaps?
- Are edge cases properly defined in test cases?

**Error Scenario Analysis:**
<action>From test cases, identify all error case tests</action>
<action>Verify error handling is tested (invalid inputs, exceptions, etc.)</action>

**Missing coverage:**
- Boundary conditions not tested
- Unusual inputs not covered
- Error paths not validated

<template-output>edge_case_analysis</template-output>
</step>

<step n="5" goal="Check evidence quality">
<action>Review evidence captured for failed and blocked tests</action>

**Evidence Quality Criteria:**

**For Failed Tests:**
- Failure message present and descriptive
- Logs or output included
- Screenshots included (for CLI tests)
- Reproduction steps documented
- Root cause identifiable from evidence

**For Blocked Tests:**
- Blocker clearly identified (missing fixture, setup issue, etc.)
- Resolution steps provided
- Impact on AC validation documented

**Quality Assessment:**
<action>For each failed/blocked test, rate evidence quality:</action>
- **High**: All criteria met, actionable information
- **Medium**: Some criteria met, mostly actionable
- **Low**: Minimal information, hard to debug

<action if="quality_gate_level is 'strict'">Require all evidence to be high quality</action>
<action if="quality_gate_level is 'standard'">Require >80% high/medium quality evidence</action>

<template-output>evidence_quality_check</template-output>
</step>

<step n="6" goal="Generate review findings with severity">
<action>Compile all issues discovered during review</action>

**Finding Categories:**

**Category 1: Test Failures**
<action>For each failed test:</action>
- Finding ID: F-{number}
- Severity: Critical / Major / Minor
- AC Impact: Which ACs are affected
- Description: What failed and why
- Evidence: Reference to test results evidence
- Recommendation: Suggested fix or next steps

**Severity Criteria:**
- **Critical**: Failure in critical AC, data corruption, security issue
- **Major**: Failure in standard AC, functional gap
- **Minor**: Edge case failure, non-critical scenario

**Category 2: Coverage Gaps**
<action>For each coverage gap:</action>
- Finding ID: G-{number}
- Severity: Critical / Major / Minor
- AC Impact: Which ACs lack coverage
- Description: What's missing
- Recommendation: Tests to add

**Severity Criteria:**
- **Critical**: No tests for critical AC
- **Major**: No tests for standard AC, missing error scenarios
- **Minor**: Missing edge cases

**Category 3: Blocked Tests**
<action>For each blocker:</action>
- Finding ID: B-{number}
- Severity: Based on impacted ACs
- Blocker Description: What's preventing execution
- Resolution Steps: How to unblock
- AC Impact: Which ACs cannot be validated

**Category 4: Quality Issues**
<action>For quality concerns:</action>
- Finding ID: Q-{number}
- Severity: Based on impact
- Issue Description: Evidence quality, test design, setup problems
- Recommendation: Improvements needed

<template-output>review_findings</template-output>
</step>

<step n="7" goal="Provide approval decision or required changes">
<action>Determine overall UAT status based on findings and quality gate</action>

**Decision Logic:**

**Step 7.1: Check auto-approval criteria**
<check if="auto_approve_if_all_pass is true AND all tests passed">
  <action>Status: APPROVED (auto-approved)</action>
  <action>Rationale: All tests passed, auto-approval enabled</action>
  <action>Skip to Step 8</action>
</check>

**Step 7.2: Evaluate against quality gate**
<action>Check quality gate requirements for {quality_gate_level}:</action>

**Minimal Gate:**
- Pass rate ≥ 80%
- Critical ACs 100% passed
- No critical findings

**Standard Gate:**
- Pass rate ≥ 90%
- Critical ACs 100% passed
- Edge case coverage ≥ 70%
- No critical findings, ≤2 major findings

**Strict Gate:**
- Pass rate ≥ 95%
- Critical ACs 100% passed
- Edge case coverage ≥ 85%
- No critical findings, no major findings
- All evidence high quality

**Step 7.3: Determine decision**

<check if="all quality gate criteria met">
  <action>Status: APPROVED</action>
  <action>Rationale: All quality gate criteria met for {quality_gate_level} level</action>
  <action>Note any minor findings for future improvement</action>
</check>

<check if="quality gate criteria not met">
  <action>Status: CHANGES REQUESTED</action>
  <action>Rationale: Quality gate criteria not met - list specific failures</action>
  <action>List required changes by priority (critical → major → minor)</action>
  <action>Provide specific next steps to achieve approval</action>
</check>

<check if="critical failures or blockers prevent validation">
  <action>Status: BLOCKED</action>
  <action>Rationale: Critical blockers prevent AC validation</action>
  <action>List blockers that must be resolved</action>
  <action>Cannot proceed to approval until blockers resolved</action>
</check>

**Step 7.4: Human review override**
<ask>Review the AI-generated decision. Do you agree with the status: {status}? [approve/request-changes/blocked/override]</ask>

<action if="user agrees">Confirm decision with user rationale if provided</action>
<action if="user overrides">Update status and capture user's rationale for override</action>

<template-output>approval_decision</template-output>
</step>

<step n="8" goal="Create stakeholder summary">
<action>Generate executive summary for non-technical stakeholders</action>

**Stakeholder Summary Format:**

**Overview:**
- Story: {story_title}
- UAT Status: {status}
- Test Execution Date: {execution_date}
- Review Date: {review_date}
- Reviewer: {reviewer_name}

**Results at a Glance:**
- ✅ {pass_count} tests passed
- ❌ {fail_count} tests failed
- 🚫 {blocked_count} tests blocked
- Overall: {pass_percentage}% success rate

**Acceptance Criteria Status:**
- Total ACs: {total_ac_count}
- Fully Validated: {validated_ac_count}
- Partially Validated: {partial_ac_count}
- Not Validated: {not_validated_ac_count}

**Key Findings:**
- Critical issues: {critical_findings_count}
- Major issues: {major_findings_count}
- Minor issues: {minor_findings_count}

**Recommendation:**
- If APPROVED: Story meets acceptance criteria and is ready for production
- If CHANGES REQUESTED: Specific changes needed (list top 3)
- If BLOCKED: Cannot validate until blockers resolved (list blockers)

**Next Steps:**
- If APPROVED: Mark story as done, prepare for deployment
- If CHANGES REQUESTED: Address findings, re-run tests, re-review
- If BLOCKED: Resolve blockers, re-execute tests

<template-output>stakeholder_summary</template-output>
</step>

<step n="9" goal="Finalize UAT review document">
<action>Ensure output directory exists: {output_folder}/uat/reviews/</action>
<action>Verify all sections complete with findings and decision</action>
<action>Confirm approval decision is clear and actionable</action>
<action>Save complete UAT review document to: {default_output_file}</action>

<action>Display review summary to user:</action>
- UAT Status: {status}
- Pass Rate: {pass_percentage}%
- Critical Findings: {critical_findings_count}
- Major Findings: {major_findings_count}
- Quality Gate: {quality_gate_level}
- Decision Rationale: {rationale_summary}

<action if="status is APPROVED">Recommend marking story as done via story-done workflow</action>
<action if="status is CHANGES REQUESTED">Recommend addressing findings and re-running execute-tests</action>
<action if="status is BLOCKED">Recommend resolving blockers and re-running execute-tests</action>

<template-output>final_document</template-output>
</step>

</workflow>

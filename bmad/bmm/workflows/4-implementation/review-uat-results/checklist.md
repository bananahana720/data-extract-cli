# Review UAT Results - Validation Checklist

## Input Loading

- [ ] **Test results loaded**: Test execution results file loaded and parsed successfully
- [ ] **Test cases loaded**: Test cases file loaded for coverage reference
- [ ] **Story loaded**: Story file loaded with all ACs extracted
- [ ] **Story key extracted**: Story key available for output filename

## Pass/Fail Ratio Analysis

- [ ] **Overall pass rate calculated**: Total pass/fail/blocked counts and percentages computed
- [ ] **Pass rate by type calculated**: Unit, integration, CLI, manual, performance pass rates computed
- [ ] **Quality gate comparison**: Pass rate compared to quality_gate_level threshold
- [ ] **Critical AC pass rate calculated**: Critical acceptance criteria pass rate computed
- [ ] **Critical AC threshold check**: Critical AC pass rate compared to threshold (should be 100%)
- [ ] **Low pass rate flags**: Test types with significantly lower pass rates flagged

## Coverage Gap Analysis

- [ ] **All ACs mapped**: Every AC from story mapped to test results
- [ ] **Test count per AC**: Number of tests per AC calculated
- [ ] **Passing tests per AC**: At least one passing test per AC verified
- [ ] **No-test ACs identified**: ACs with no tests flagged as major gaps
- [ ] **Failed-only ACs identified**: ACs with only failed/blocked tests flagged
- [ ] **Scenario coverage checked**: Happy path, edge cases, error cases coverage verified per AC
- [ ] **Gaps by severity**: Coverage gaps categorized as critical/major/minor

## Edge Case and Error Scenario Analysis

- [ ] **Edge cases identified**: All edge case tests extracted from test cases
- [ ] **Edge case pass rate calculated**: Percentage of edge cases that passed
- [ ] **Edge case threshold check**: Compared to quality gate threshold (standard/strict only)
- [ ] **Failed edge cases analyzed**: Failing edge cases evaluated for implementation gaps
- [ ] **Error scenarios identified**: All error case tests extracted
- [ ] **Error handling verified**: Error paths and exception handling validated
- [ ] **Missing coverage noted**: Boundary conditions, unusual inputs, error paths gaps identified

## Evidence Quality Check

- [ ] **Failed test evidence reviewed**: Evidence for each failed test evaluated
- [ ] **Blocked test evidence reviewed**: Evidence for each blocked test evaluated
- [ ] **Evidence quality rated**: Each piece of evidence rated as high/medium/low quality
- [ ] **High quality criteria**: Failure message, logs, screenshots, reproduction steps, root cause
- [ ] **Quality gate compliance**: Evidence quality meets quality_gate_level requirements
- [ ] **Low quality evidence flagged**: Poor evidence identified as quality issues

## Review Findings

- [ ] **All findings documented**: Failures, coverage gaps, blockers, quality issues captured
- [ ] **Unique finding IDs**: Each finding has unique ID (F-, G-, B-, Q- prefix)
- [ ] **Severity assigned**: Each finding rated as critical/major/minor
- [ ] **AC impact documented**: Which ACs are affected by each finding
- [ ] **Evidence referenced**: Findings reference test results evidence
- [ ] **Recommendations provided**: Specific next steps for each finding
- [ ] **Severity criteria applied**: Consistent severity assignment based on AC impact

## Approval Decision

- [ ] **Auto-approval checked**: Auto-approval criteria evaluated if enabled
- [ ] **Quality gate evaluated**: All quality gate criteria for quality_gate_level checked
- [ ] **Decision determined**: APPROVED, CHANGES REQUESTED, or BLOCKED status assigned
- [ ] **Rationale documented**: Clear explanation of decision provided
- [ ] **Human review performed**: User prompted to confirm or override AI decision
- [ ] **Override captured**: User override rationale captured if applicable
- [ ] **Required changes listed**: Specific changes prioritized (if CHANGES REQUESTED)
- [ ] **Blockers listed**: Specific blockers documented (if BLOCKED)

## Quality Gate Compliance

- [ ] **Minimal gate (if applicable)**: Pass rate ≥ 80%, critical ACs 100%, no critical findings
- [ ] **Standard gate (if applicable)**: Pass rate ≥ 90%, critical ACs 100%, edge cases ≥ 70%, ≤2 major findings
- [ ] **Strict gate (if applicable)**: Pass rate ≥ 95%, critical ACs 100%, edge cases ≥ 85%, no major findings, high evidence quality

## Stakeholder Summary

- [ ] **Executive overview**: Non-technical summary of results provided
- [ ] **Results at a glance**: Pass/fail/blocked counts in simple terms
- [ ] **AC status summary**: Total, validated, partially validated, not validated ACs
- [ ] **Key findings summary**: Count of critical/major/minor issues
- [ ] **Recommendation clear**: Clear bottom line for stakeholders
- [ ] **Next steps actionable**: Clear guidance on what happens next

## Document Completeness

- [ ] **All sections populated**: No placeholder text remaining
- [ ] **Findings detailed**: Each finding has complete information
- [ ] **Metrics accurate**: All calculations verified
- [ ] **AC status complete**: Every AC has validation status
- [ ] **Next steps clear**: Specific, actionable next steps provided

## Output Quality

- [ ] **File saved**: UAT review document saved to docs/uat/reviews/
- [ ] **Filename correct**: Follows pattern {story_key}-uat-review.md
- [ ] **Formatting consistent**: Markdown formatting clean and consistent
- [ ] **Summary displayed**: UAT status and key metrics shown to user

## Workflow Integration

- [ ] **Status clear**: APPROVED, CHANGES REQUESTED, or BLOCKED status unambiguous
- [ ] **Next workflow identified**: story-done (if approved) or execute-tests (if changes/blocked)
- [ ] **Traceability maintained**: Links to test results, test cases, and story preserved
- [ ] **Approval ready**: Document ready for stakeholder review and sign-off

## Decision Consistency

- [ ] **Decision matches findings**: Approval status consistent with findings severity
- [ ] **Thresholds applied correctly**: Quality gate thresholds applied as configured
- [ ] **Critical issues block approval**: Critical findings prevent approval
- [ ] **Human override documented**: User override clearly documented with rationale

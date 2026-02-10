# Execute Tests - Validation Checklist

## Input Loading

- [ ] **Test cases loaded**: Test cases file loaded and parsed successfully
- [ ] **Test context loaded**: Test context XML loaded with fixtures and helpers
- [ ] **Story loaded**: Story file loaded for AC mapping
- [ ] **Story key extracted**: Story key available for output filename

## Test Categorization

- [ ] **Tests grouped by type**: Unit, integration, CLI, manual, performance categorized
- [ ] **Execution plan created**: Plan matches test_execution_mode setting
- [ ] **Test counts accurate**: Total tests per category calculated correctly

## Environment Verification

- [ ] **Fixtures verified**: All required fixtures exist at documented paths
- [ ] **Helpers verified**: conftest files and helper functions available
- [ ] **pytest config verified**: pytest.ini loaded and valid
- [ ] **Environment variables set**: Required env vars configured (if needed)
- [ ] **Dependencies available**: External dependencies accessible (if needed)
- [ ] **Blockers identified**: Missing prerequisites documented

## Automated Test Execution (pytest)

- [ ] **pytest command built**: Command includes markers, args, timeout
- [ ] **Tests executed**: pytest ran successfully
- [ ] **Output captured**: stdout and stderr captured completely
- [ ] **Results parsed**: Test outcomes (PASSED, FAILED, SKIPPED, ERROR) extracted
- [ ] **Execution time recorded**: Time per test and total time captured
- [ ] **Coverage captured**: Coverage data included (if applicable)
- [ ] **Failures documented**: Failure messages and tracebacks captured

## CLI Test Execution (tmux-cli)

- [ ] **tmux session initialized**: Shell launched successfully via tmux-cli
- [ ] **Pane ID stored**: Pane identifier captured for subsequent commands
- [ ] **Commands executed**: All CLI test commands sent and executed
- [ ] **Idle wait applied**: wait_idle used to ensure command completion
- [ ] **Output captured**: CLI output captured via tmux-cli capture
- [ ] **Expected results verified**: Output compared to test case expectations
- [ ] **Interactive prompts handled**: User input sent for interactive tests (if applicable)
- [ ] **Screenshots captured**: Screenshots taken (if capture_screenshots enabled)
- [ ] **Session cleaned up**: tmux pane killed after tests complete

## Manual Test Execution

- [ ] **Test cases displayed**: Each manual test shown to user with clear instructions
- [ ] **User input collected**: Pass/fail/blocked status captured from user
- [ ] **Failure descriptions captured**: Failure/blocker descriptions documented
- [ ] **Notes captured**: User observations and notes recorded as evidence

## Results Aggregation

- [ ] **All results compiled**: pytest + CLI + manual results combined
- [ ] **Metrics calculated**: Pass/fail/blocked counts and percentages computed
- [ ] **AC mapping complete**: Test results mapped to acceptance criteria
- [ ] **AC status determined**: Overall status per AC (PASS/FAIL/BLOCKED)
- [ ] **Critical failures flagged**: Blocker tests identified
- [ ] **Evidence complete**: All failures have failure messages and evidence

## Evidence Capture

- [ ] **Pytest failures**: Failure messages and tracebacks included
- [ ] **CLI output**: Command output captured for failed CLI tests
- [ ] **Screenshots**: Screenshots included (if applicable)
- [ ] **Logs**: Relevant log excerpts included
- [ ] **Reproduction steps**: Steps to reproduce failures documented

## Recommendations

- [ ] **Pass scenario**: Recommendations for successful tests (proceed to review)
- [ ] **Fail scenario**: Root causes identified, fixes suggested, priorities assigned
- [ ] **Block scenario**: Blockers identified, resolution steps provided
- [ ] **Performance observations**: Performance notes included (if applicable)
- [ ] **Coverage gaps**: Test coverage improvements suggested

## Test Result Quality

- [ ] **All tests have status**: Every test has PASS, FAIL, or BLOCKED status
- [ ] **All tests have evidence**: Every test has execution evidence (output/logs/notes)
- [ ] **Timestamps recorded**: Execution times captured for all tests
- [ ] **Failure messages clear**: Failure descriptions are actionable and specific

## Output Quality

- [ ] **File saved**: Test results document saved to docs/uat/test-results/
- [ ] **Filename correct**: Follows pattern {story_key}-test-results.md
- [ ] **Formatting consistent**: Markdown formatting clean and consistent
- [ ] **Summary displayed**: Pass/fail/blocked counts shown to user

## Workflow Integration

- [ ] **AC validation complete**: All ACs have test coverage assessment
- [ ] **Review readiness**: Results ready for review-uat-results workflow
- [ ] **Next steps clear**: Guidance for UAT review or fix/rerun provided
- [ ] **Traceability maintained**: Links to test cases and test context preserved

## Error Handling

- [ ] **Continue on failure**: continue_on_failure setting respected
- [ ] **Timeout handling**: Test timeouts handled gracefully
- [ ] **Missing fixtures**: Blocked status assigned to tests with missing fixtures
- [ ] **tmux errors**: tmux-cli errors captured and reported
- [ ] **pytest errors**: pytest execution errors documented

## Execution Mode Compliance

- [ ] **Automated mode**: Only pytest tests executed (if mode=automated)
- [ ] **Manual mode**: Only manual tests executed (if mode=manual)
- [ ] **Hybrid mode**: All test types executed (if mode=hybrid)

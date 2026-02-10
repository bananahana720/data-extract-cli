# Execute Tests - Workflow Instructions

<critical>The workflow execution engine is governed by: {project-root}/bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/bmad/bmm/workflows/4-implementation/execute-tests/workflow.yaml</critical>
<critical>Communicate in {communication_language} throughout the process</critical>
<critical>Reference tmux-cli documentation: {project-root}/docs/tmux-cli-instructions.md</critical>

<workflow>

<step n="1" goal="Load test artifacts">
<action>If test_cases_file not provided, locate latest test cases file in {output_folder}/uat/test-cases/</action>
<action>If test_context_file not provided, locate corresponding test context file in {output_folder}/uat/test-context/</action>
<action>If story_path not provided, derive from test cases file or find story with matching key</action>

<action>Load test cases document and extract:</action>
- All test case IDs and types
- Test case objectives and expected results
- Test data requirements
- Preconditions for each test

<action>Load test context XML and extract:</action>
- Available fixtures and paths
- Helper functions and conftest details
- pytest configuration and markers
- Setup requirements

<action>Load story file and extract:</action>
- Story key for output filename
- Acceptance criteria for result mapping

<template-output>artifacts_loaded</template-output>
</step>

<step n="2" goal="Categorize tests by execution type">
<action>Group test cases by test type from test cases file:</action>

**Automated Tests (pytest):**
- Unit tests
- Integration tests
- Performance tests

**CLI Tests (tmux-cli):**
- Command-line interface tests
- Interactive application tests

**Manual Tests:**
- Human verification required
- Tests that cannot be automated

<action>Create execution plan based on test_execution_mode:</action>
- **automated**: Run only pytest tests
- **manual**: Guide user through manual tests only
- **hybrid**: Run automated tests, then guide manual tests

<action>Calculate total test count per category</action>

<template-output>execution_plan</template-output>
</step>

<step n="3" goal="Verify test environment setup">
<action>Check setup requirements from test context:</action>

**Prerequisites check:**
- Required fixtures exist at documented paths
- Helper functions available in conftest files
- pytest configuration valid
- Environment variables set (if needed)
- External dependencies available (if needed)

<action>For each missing prerequisite:</action>
- Document the gap
- Provide setup guidance
- Mark affected tests as BLOCKED

<action if="critical prerequisites missing">Recommend resolving setup issues before execution</action>

<template-output>environment_verified</template-output>
</step>

<step n="4" goal="Execute automated tests (pytest)">
<action if="{test_execution_mode} in ['automated', 'hybrid']">Execute pytest tests</action>

**Step 4.1: Prepare pytest execution**
<action>Build pytest command with:</action>
- Test markers from test cases (unit, integration, performance)
- pytest arguments from execution_settings
- Timeout from execution_settings
- Coverage options (if desired)

Example command:
```bash
pytest {pytest_args} -m "unit or integration" --timeout={pytest_timeout}
```

**Step 4.2: Execute tests**
<action>Run pytest command</action>
<action>Capture stdout and stderr</action>
<action>Monitor execution progress</action>

**Step 4.3: Parse pytest results**
<action>Extract from pytest output:</action>
- Test results (PASSED, FAILED, SKIPPED, ERROR)
- Failure messages and tracebacks
- Execution time per test
- Coverage data (if available)

**Step 4.4: Map results to test cases**
<action>For each test case (Unit/Integration/Performance type):</action>
- Match pytest test to test case ID
- Record status: PASS, FAIL, or BLOCKED
- Capture failure message if applicable
- Note execution time
- Include evidence (output snippet, logs)

<action if="{continue_on_failure} is false and failures exist">Stop execution and report failures</action>

<template-output>pytest_results</template-output>
</step>

<step n="5" goal="Execute CLI tests (tmux-cli)">
<action if="CLI tests exist and {test_execution_mode} in ['automated', 'hybrid']">Execute CLI tests using tmux-cli</action>

**⚠️ Windows Users**: tmux-cli requires tmux (Unix/Linux only). On Windows, either:
- Run this workflow from WSL: `wsl` → `cd /mnt/c/Users/{user}/projects/{project}` → `workflow execute-tests`
- Mark CLI tests as BLOCKED with note: "Requires WSL execution on Windows"
- See `docs/uat/tmux-cli-windows-setup.md` for detailed setup

**Step 5.1: Initialize tmux session**
<action>Launch shell for CLI testing:</action>
```bash
tmux-cli launch "zsh"
```
<action>Store pane ID for subsequent commands</action>

**Step 5.2: For each CLI test case**
<action>Execute the following pattern:</action>

1. **Setup**: Send setup commands if needed
   ```bash
   tmux-cli send "cd {project-root}" --pane={pane_id}
   tmux-cli wait_idle --pane={pane_id} --idle-time={tmux_idle_time}
   ```

2. **Execute test command**: Send the CLI command from test case
   ```bash
   tmux-cli send "{cli_command}" --pane={pane_id}
   tmux-cli wait_idle --pane={pane_id} --idle-time={tmux_idle_time} --timeout={tmux_timeout}
   ```

3. **Capture output**: Get command results
   ```bash
   tmux-cli capture --pane={pane_id}
   ```

4. **Verify expected results**: Compare output to test case expected results
   - Check for expected text patterns
   - Verify exit codes if applicable
   - Validate output format

5. **Record result**: Document PASS/FAIL/BLOCKED with evidence
   - Status based on verification
   - Captured output as evidence
   - Execution time

   <action if="{capture_screenshots} is true">Capture screenshot of CLI output for visual evidence</action>
   <action if="{capture_screenshots} is true">Include screenshot reference in test result evidence</action>

6. **Handle interactive prompts**: If test requires input
   ```bash
   tmux-cli send "{user_input}" --pane={pane_id}
   ```

<action if="test fails and {continue_on_failure} is false">Clean up and stop execution</action>
<action if="test passes or {continue_on_failure} is true">Continue to next test</action>

**Step 5.3: Cleanup tmux session**
<action>After all CLI tests complete:</action>
```bash
tmux-cli kill --pane={pane_id}
```

<template-output>cli_test_results</template-output>
</step>

<step n="6" goal="Guide manual test execution">
<action if="Manual tests exist and {test_execution_mode} in ['manual', 'hybrid']">Guide user through manual tests</action>

**For each manual test case:**

<action>Display test case to user:</action>
- Test case ID and objective
- Preconditions
- Step-by-step instructions
- Expected results

<ask>Have you completed this manual test? What was the result? [pass/fail/blocked]</ask>

<action>If result is FAIL or BLOCKED:</action>
<ask>Please describe the failure/blocker:</ask>
<action>Capture failure description</action>

<action>If result is PASS:</action>
<ask>Any notes or observations?</ask>
<action>Capture notes as evidence</action>

<action>Record manual test result with user-provided status and notes</action>

<template-output>manual_test_results</template-output>
</step>

<step n="7" goal="Aggregate results and generate report">
<action>Compile all test results (pytest + CLI + manual)</action>

**Calculate metrics:**
- Total tests executed: {total_count}
- Passed: {pass_count} ({pass_percentage}%)
- Failed: {fail_count} ({fail_percentage}%)
- Blocked: {blocked_count} ({blocked_percentage}%)
- Execution time: {total_time}

**Group results by acceptance criterion:**
<action>For each AC, show:</action>
- AC ID and description
- Test cases covering this AC
- Pass/fail status for each test
- Overall AC status (PASS if all tests pass, FAIL if any fail, BLOCKED if any blocked)

**Identify critical failures:**
<action>Flag tests that are blockers:</action>
- Tests for critical acceptance criteria
- Tests that failed with exceptions
- Tests that indicate data corruption or security issues

**Capture evidence:**
<action>For each failed or blocked test:</action>
- Include failure message
- Include relevant logs or output
- Include screenshot if available (CLI tests)
- Include reproduction steps

<template-output>aggregated_results</template-output>
</step>

<step n="8" goal="Generate recommendations">
<action>Based on test results, provide recommendations:</action>

**If all tests passed:**
- Note successful validation of all acceptance criteria
- Recommend proceeding to UAT review (review-uat-results workflow)

**If tests failed:**
- Identify root causes where possible
- Suggest fixes for failed tests
- Prioritize by impact (critical vs minor)
- Recommend re-running failed tests after fixes

**If tests blocked:**
- Identify blockers (missing fixtures, setup issues, etc.)
- Provide resolution steps
- Recommend addressing blockers before re-execution

**General recommendations:**
- Performance observations (if performance tests ran)
- Test coverage gaps identified during execution
- Improvements to test cases or fixtures

<template-output>recommendations</template-output>
</step>

<step n="9" goal="Finalize test results document">
<action>Ensure output directory exists: {output_folder}/uat/test-results/</action>
<action>Verify all test results documented with evidence</action>
<action>Confirm AC coverage mapping complete</action>
<action>Save complete test results document to: {default_output_file}</action>

<action>Display execution summary to user:</action>
- Total tests: {total_count}
- Passed: {pass_count} ({pass_percentage}%)
- Failed: {fail_count}
- Blocked: {blocked_count}
- Execution time: {total_time}
- Next step: Review results via review-uat-results workflow

<template-output>final_document</template-output>
</step>

</workflow>

# Create Test Cases - Workflow Instructions

<critical>The workflow execution engine is governed by: {project-root}/bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/bmad/bmm/workflows/4-implementation/create-test-cases/workflow.yaml</critical>
<critical>Communicate in {communication_language} throughout the process</critical>

<workflow>

<step n="1" goal="Load and parse story file">
<action>If story_path not provided, find first story with status "ready-for-dev" in {story_dir}</action>
<action>Load the complete story markdown file</action>
<action>Parse and extract:</action>
- Story ID/key (from filename or header)
- Story title
- User story (As a / I want / So that)
- All acceptance criteria (AC-X-Y-Z format)
- Any existing test notes from Dev Notes section

<action>Store story_key for output filename</action>
<action>Store epic number from story_key (e.g., "2.5-3.1" → epic_num=2.5)</action>

<template-output>story_parsed</template-output>
</step>

<step n="2" goal="Load epic context (optional)">
<action if="epic_file provided or epic_num extracted">Load epic technical specification for additional context</action>
<action if="epic loaded">Extract relevant information:</action>
- Technical constraints
- NFRs (Non-Functional Requirements)
- Architecture patterns
- Testing strategies mentioned

<template-output>epic_context</template-output>
</step>

<step n="3" goal="Analyze acceptance criteria and determine test scenarios">
<action>For each acceptance criterion in the story:</action>

**Step 3.1: Identify test scenario types**
<action>Determine which scenario types apply:</action>
- **Happy Path**: Standard successful execution
- **Edge Cases**: Boundary conditions, unusual inputs, limits
- **Error Cases**: Invalid inputs, failures, exceptions
- **Integration Points**: Dependencies, external systems, APIs
- **Performance**: Speed, memory, throughput (if NFRs exist)
- **Security**: Auth, permissions, data validation

**Step 3.2: Generate test scenarios per AC**
<action>Based on test_coverage_level:</action>

- **Minimal**: Happy path only (1 test per AC)
- **Standard**: Happy path + 1-2 edge cases + 1 error case (3-4 tests per AC)
- **Comprehensive**: Happy path + multiple edge cases + error cases + integration (5-8 tests per AC)

**Step 3.3: Map scenarios to test types**
<action>Classify each test scenario by execution type:</action>
- **Unit**: Isolated component testing (pytest)
- **Integration**: Multi-component testing (pytest)
- **CLI**: Command-line interface testing (tmux-cli)
- **Manual**: Human-executed verification
- **Performance**: Benchmarking (pytest with profiling)

<template-output>test_scenarios_analysis</template-output>
</step>

<step n="4" goal="Generate structured test cases">
<action>For each test scenario identified, create a structured test case with:</action>

**Test Case Structure:**
```
### Test Case TC-{story_key}-{ac_num}-{scenario_num}

**Acceptance Criterion**: AC-{id}
**Test Type**: [Unit|Integration|CLI|Manual|Performance]
**Scenario**: [Happy Path|Edge Case|Error Case|Integration|Performance|Security]

**Objective**: {What this test validates}

**Preconditions**:
- {Setup requirement 1}
- {Setup requirement 2}

**Test Steps**:
1. {Action 1}
2. {Action 2}
3. {Action 3}

**Expected Results**:
- {Expected outcome 1}
- {Expected outcome 2}

**Test Data** (if applicable):
- Input: {test data description}
- Expected Output: {expected output description}

**Dependencies** (if applicable):
- Fixtures: {required test fixtures}
- Helpers: {required test helpers}
- Configuration: {required config}
```

<action>Generate all test cases following this structure</action>

<template-output>test_cases_generated</template-output>
</step>

<step n="5" goal="Add test coverage summary">
<action>Generate test coverage matrix showing:</action>

**Coverage Matrix:**
```
| AC ID | Description | Happy Path | Edge Cases | Error Cases | Integration | Total Tests |
|-------|-------------|------------|------------|-------------|-------------|-------------|
| AC-X-Y-1 | ... | ✓ | ✓ (2) | ✓ (1) | - | 4 |
| AC-X-Y-2 | ... | ✓ | ✓ (1) | ✓ (1) | ✓ (1) | 5 |
```

**Test Type Distribution:**
- Unit tests: {count}
- Integration tests: {count}
- CLI tests: {count}
- Manual tests: {count}
- Performance tests: {count}
- **Total test cases**: {total}

**Coverage Level**: {test_coverage_level}

<template-output>coverage_summary</template-output>
</step>

<step n="6" goal="Add testing notes and recommendations">
<action>Based on the story and generated test cases, provide:</action>

**Testing Recommendations:**
- Suggested test execution order
- Critical tests that must pass (blockers)
- Tests that can run in parallel
- Estimated test execution time
- Any special setup requirements

**Implementation Notes:**
- Suggested pytest markers to use
- Fixture requirements
- Helper functions needed
- Integration points to mock/stub

**Risk Areas:**
- Complex scenarios requiring extra attention
- Potential failure points
- Performance bottlenecks
- Security considerations

<template-output>testing_notes</template-output>
</step>

<step n="7" goal="Finalize test cases document">
<action>Ensure output file directory exists: {output_folder}/uat/test-cases/</action>
<action>Verify all test cases follow consistent structure</action>
<action>Confirm all ACs have corresponding test cases</action>
<action>Save complete test cases document to: {default_output_file}</action>

<template-output>final_document</template-output>
</step>

</workflow>

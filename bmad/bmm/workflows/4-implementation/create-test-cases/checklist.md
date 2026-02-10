# Create Test Cases - Validation Checklist

## Completeness

- [ ] **All ACs covered**: Every acceptance criterion has at least one test case
- [ ] **Story context loaded**: Story file parsed with all ACs extracted
- [ ] **Epic context loaded**: Epic tech spec loaded (if available)
- [ ] **Test coverage level applied**: Minimal/standard/comprehensive coverage achieved

## Test Case Quality

- [ ] **Structured format**: All test cases follow standard structure (TC-{id}, Objective, Preconditions, Steps, Expected Results)
- [ ] **Happy path coverage**: At least one happy path test per AC
- [ ] **Edge case coverage**: Boundary conditions and unusual inputs covered (standard+ level)
- [ ] **Error case coverage**: Invalid inputs and failure scenarios covered (standard+ level)
- [ ] **Integration coverage**: Cross-component interactions tested where applicable

## Test Type Distribution

- [ ] **Unit tests identified**: Isolated component tests marked as Unit
- [ ] **Integration tests identified**: Multi-component tests marked as Integration
- [ ] **CLI tests identified**: Command-line tests marked as CLI (if applicable)
- [ ] **Manual tests identified**: Human verification tests marked as Manual (if applicable)
- [ ] **Performance tests identified**: NFR validation tests marked as Performance (if applicable)

## Test Case Structure

- [ ] **Unique IDs**: Each test case has unique identifier (TC-{story_key}-{ac_num}-{scenario_num})
- [ ] **Clear objectives**: Each test clearly states what it validates
- [ ] **Actionable steps**: Test steps are clear and executable
- [ ] **Measurable outcomes**: Expected results are specific and verifiable
- [ ] **Dependencies listed**: Required fixtures, helpers, and config identified

## Coverage Matrix

- [ ] **Matrix complete**: Coverage matrix shows all ACs with test counts
- [ ] **Test type distribution**: Summary shows breakdown by test type
- [ ] **Total count accurate**: Total test count matches individual test cases

## Testing Recommendations

- [ ] **Execution order**: Suggested test execution sequence provided
- [ ] **Critical tests**: Blocker tests that must pass identified
- [ ] **Parallel execution**: Tests that can run in parallel noted
- [ ] **Time estimate**: Estimated test execution time provided
- [ ] **Setup requirements**: Special setup needs documented

## Implementation Guidance

- [ ] **Pytest markers**: Suggested markers for test organization
- [ ] **Fixture requirements**: Required test fixtures identified
- [ ] **Helper functions**: Needed helper functions listed
- [ ] **Mock/stub points**: Integration points to mock documented

## Risk Analysis

- [ ] **Complex scenarios**: High-complexity tests flagged
- [ ] **Failure points**: Potential failure areas identified
- [ ] **Performance risks**: Performance bottlenecks noted
- [ ] **Security considerations**: Security test requirements documented

## Output Quality

- [ ] **File saved**: Test cases document saved to docs/uat/test-cases/
- [ ] **Filename correct**: Follows pattern {story_key}-test-cases.md
- [ ] **Formatting consistent**: Markdown formatting clean and consistent
- [ ] **Next steps clear**: Guidance for next workflow (build-test-context) provided

## Workflow Integration

- [ ] **Story key captured**: Story key available for downstream workflows
- [ ] **Epic number extracted**: Epic number available for context loading
- [ ] **Test data identified**: Test data requirements noted for context building
- [ ] **Fixture paths noted**: Required fixture paths documented for build-test-context workflow

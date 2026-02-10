# Build Test Context - Validation Checklist

## Input Loading

- [ ] **Test cases loaded**: Test cases file loaded and parsed successfully
- [ ] **Story loaded**: Story file loaded with AC and context extracted
- [ ] **Story context loaded**: Existing story context XML loaded (if available)
- [ ] **Story key extracted**: Story key available for file naming

## Fixture Discovery

- [ ] **Fixtures scanned**: tests/fixtures/ directory scanned completely
- [ ] **Fixtures categorized**: Fixtures organized by type (PDF, Excel, images, etc.)
- [ ] **Fixtures matched**: Test cases mapped to available fixtures
- [ ] **Missing fixtures identified**: Gaps in fixture coverage documented
- [ ] **Generation scripts noted**: Fixture generation scripts referenced where applicable
- [ ] **Fixture README included**: tests/fixtures/README.md path included

## Helper Discovery

- [ ] **Global conftest loaded**: tests/conftest.py parsed for shared fixtures
- [ ] **Integration conftest loaded**: tests/integration/conftest.py parsed for integration fixtures
- [ ] **Fixtures categorized**: Helper fixtures categorized by test type (unit, integration, CLI, performance)
- [ ] **Utility functions identified**: Shared utility functions documented

## Configuration Discovery

- [ ] **pytest.ini loaded**: Configuration file parsed successfully
- [ ] **Markers extracted**: Test markers documented (unit, integration, performance, etc.)
- [ ] **Settings extracted**: Timeout, coverage, and plugin settings noted
- [ ] **Environment variables identified**: Required env vars documented

## Code Under Test

- [ ] **Source files identified**: Files being tested mapped from test cases
- [ ] **Paths validated**: Source file paths are correct and accessible
- [ ] **Functions/classes noted**: Key functions and classes under test documented
- [ ] **Dependencies tracked**: Module dependencies and imports noted
- [ ] **Story context leveraged**: Code artifacts from story context reused (if available)

## Integration Points

- [ ] **File system requirements**: Required directories and permissions documented
- [ ] **External commands**: CLI tools and system utilities identified
- [ ] **Environment variables**: Configuration via env vars documented
- [ ] **Network resources**: API endpoints and external services noted (if applicable)
- [ ] **Database requirements**: Database setup and migrations documented (if applicable)
- [ ] **Mock/stub strategies**: Integration point mocking approaches noted

## XML Structure

- [ ] **Valid XML**: XML structure is well-formed and valid
- [ ] **Metadata complete**: Epic ID, story ID, story key, title, date populated
- [ ] **Test cases summary**: Test counts by type included
- [ ] **Test case list**: Individual test cases with IDs and types listed
- [ ] **Fixtures section**: All discovered fixtures documented with paths
- [ ] **Helpers section**: All helper fixtures and utilities documented
- [ ] **Configuration section**: pytest and environment config included
- [ ] **Code section**: Source files under test included
- [ ] **Integration section**: Integration points and setup documented
- [ ] **Story context section**: Development context included (if available)

## Setup Requirements

- [ ] **Prerequisites listed**: Setup requirements clearly documented
- [ ] **Fixture generation steps**: Scripts to run for fixture creation
- [ ] **Environment setup steps**: Configuration and environment preparation documented
- [ ] **Validation commands**: Commands to verify setup provided

## Path References

- [ ] **Absolute paths**: All paths use {project-root} or absolute references
- [ ] **Paths accessible**: All referenced files and directories exist or are marked as missing
- [ ] **Relative paths avoided**: No relative paths that could break in different contexts

## Completeness

- [ ] **All test types covered**: Unit, integration, CLI, manual, performance tests all have context
- [ ] **Dependencies complete**: All dependencies identified and documented
- [ ] **Setup complete**: All setup requirements captured
- [ ] **Next steps provided**: Clear guidance for next workflow (execute-tests)

## Output Quality

- [ ] **File saved**: Test context XML saved to docs/uat/test-context/
- [ ] **Filename correct**: Follows pattern {story_key}-test-context.xml
- [ ] **XML formatting**: Clean, indented, readable XML
- [ ] **Summary displayed**: Fixture/helper/code counts displayed to user

## Workflow Integration

- [ ] **Test cases reference**: Test cases file path included for traceability
- [ ] **Story reference**: Source story path included for context
- [ ] **Execute-tests ready**: Test context includes all data needed for test execution
- [ ] **Fixture gaps noted**: Missing fixtures clearly identified for creation before execution

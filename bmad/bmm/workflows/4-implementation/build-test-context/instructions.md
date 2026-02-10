# Build Test Context - Workflow Instructions

<critical>The workflow execution engine is governed by: {project-root}/bmad/core/tasks/workflow.xml</critical>
<critical>You MUST have already loaded and processed: {project-root}/bmad/bmm/workflows/4-implementation/build-test-context/workflow.yaml</critical>
<critical>Communicate in {communication_language} throughout the process</critical>

<workflow>

<step n="1" goal="Load test cases and story">
<action>If test_cases_file not provided, locate test cases file in {output_folder}/uat/test-cases/ matching story</action>
<action>If story_path not provided, derive from test_cases_file or find first story with status "ready-for-dev"</action>
<action>Load test cases document from {test_cases_file} and extract:</action>
- Test case IDs and types
- Required fixtures mentioned in test data sections
- Helper functions referenced
- Configuration requirements
- Test dependencies

<action>Load story file from {story_path} and extract:</action>
- Story key
- Epic number
- Acceptance criteria
- Dev notes with technical context

<template-output>inputs_loaded</template-output>
</step>

<step n="2" goal="Load story context (optional)">
<action if="include_story_context is true">Check for existing story context XML: {story_dir}/{{story_key}}.context.xml</action>

<check if="story context exists">
  <action>Load story context XML</action>
  <action>Extract relevant sections:</action>
  - Code artifacts referenced
  - Documentation links
  - Dependencies and interfaces
  <action>Store for inclusion in test context</action>
</check>

<check if="no story context">
  <action>Note that test context will be built from scratch</action>
  <action>Will discover test infrastructure independently</action>
</check>

<template-output>story_context_loaded</template-output>
</step>

<step n="3" goal="Discover test fixtures">
<action>Search {fixtures_root} for relevant test fixtures based on test cases</action>

**Step 3.1: Categorize fixtures by type**
<action>Scan fixtures directory structure:</action>
```
tests/fixtures/
├── pdfs/           # PDF test files
├── xlsx/           # Excel test files
├── docx/           # Word test files
├── images/         # Image test files
├── csv/            # CSV test files
└── json/           # JSON test files
```

**Step 3.2: Match fixtures to test requirements**
<action>For each test case requiring test data:</action>
- Identify fixture type needed (PDF, Excel, etc.)
- Search relevant subdirectory
- Check for large/ and small/ variants
- Note fixture file paths and descriptions

**Step 3.3: Identify missing fixtures**
<action>For test cases without matching fixtures:</action>
- Note required fixture characteristics
- Suggest fixture generation approach
- Reference existing generation scripts if applicable

<template-output>fixtures_discovered</template-output>
</step>

<step n="4" goal="Discover test helpers and configuration">
<action>Load global conftest.py: {conftest_global}</action>
<action>Extract shared fixtures and helper functions</action>

<action>Load integration conftest.py: {conftest_integration}</action>
<action>Extract integration-specific fixtures</action>

<action>Load pytest configuration: {pytest_config}</action>
<action>Extract relevant settings:</action>
- Test markers
- Timeout configurations
- Coverage settings
- Plugin configurations

**Step 4.1: Map helpers to test types**
<action>For unit tests: Identify mock helpers, factory functions</action>
<action>For integration tests: Identify setup/teardown fixtures, database helpers</action>
<action>For CLI tests: Identify CLI fixture patterns, output capture utilities</action>
<action>For performance tests: Identify profiling fixtures, memory monitoring helpers</action>

<template-output>helpers_discovered</template-output>
</step>

<step n="5" goal="Identify code under test">
<action>Based on test cases and story context, identify source files being tested</action>

**Step 5.1: Map test types to source locations**
<action>For each test case:</action>
- Extract module/class/function being tested
- Locate source file path
- Note line numbers if specific functions referenced

**Step 5.2: Include relevant source context**
<action>For each source file identified:</action>
- Include file path
- Include key function/class signatures
- Note dependencies and imports
- Reference related modules

<action if="story context exists">Leverage code artifacts from story context to avoid duplication</action>

<template-output>code_identified</template-output>
</step>

<step n="6" goal="Gather integration points">
<action>Identify external dependencies and integration points from test cases</action>

**Integration Categories:**
- **File System**: Required directories, file permissions
- **External Commands**: CLI tools, system utilities
- **Environment Variables**: Configuration via env vars
- **Network Resources**: APIs, external services (if applicable)
- **Database**: Database setup, migrations (if applicable)

<action>For each integration point:</action>
- Document setup requirements
- Identify mock/stub strategies
- Note configuration needed

<template-output>integrations_identified</template-output>
</step>

<step n="7" goal="Build test context XML">
<action>Assemble complete test context XML using template</action>

**XML Structure:**
```xml
<test-context>
  <metadata>Story and test case metadata</metadata>
  <testCases>Summary of test cases from create-test-cases</testCases>
  <fixtures>Test data files and generation scripts</fixtures>
  <helpers>conftest fixtures and utility functions</helpers>
  <configuration>pytest settings and markers</configuration>
  <codeUnderTest>Source files being tested</codeUnderTest>
  <integrationPoints>External dependencies and setup</integrationPoints>
  <storyContext>Development context (if available)</storyContext>
</test-context>
```

<action>Populate all sections with discovered information</action>
<action>Ensure all paths are absolute or project-relative</action>
<action>Validate XML structure</action>

<template-output>test_context_built</template-output>
</step>

<step n="8" goal="Add setup recommendations">
<action>Based on discovered fixtures and helpers, provide setup guidance:</action>

**Setup Checklist:**
- Required fixture files (existing vs need to create)
- Helper functions to implement
- Configuration changes needed
- Environment setup steps
- Test execution prerequisites

**Fixture Generation:**
- Scripts to run for fixture creation
- Manual setup steps if required
- Fixture validation commands

<template-output>setup_recommendations</template-output>
</step>

<step n="9" goal="Finalize test context document">
<action>Ensure output directory exists: {output_folder}/uat/test-context/</action>
<action>Validate XML structure and completeness</action>
<action>Verify all file paths are accessible</action>
<action>Save test context XML to: {default_output_file}</action>

<action>Display summary:</action>
- Total fixtures discovered: {fixture_count}
- Helper functions available: {helper_count}
- Code files under test: {code_file_count}
- Integration points: {integration_count}
- Missing fixtures to create: {missing_fixture_count}

<template-output>final_document</template-output>
</step>

</workflow>

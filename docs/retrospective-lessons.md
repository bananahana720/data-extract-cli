# Retrospective Lessons - Complete Reference

Consolidated lessons from Epics 1-3 retrospectives to prevent repeating past mistakes.

## Story Development Lessons

### AC Evidence and Review Process
- **Fill AC evidence table BEFORE marking review status** - AC matrices with test locations and perf numbers
- **Include BOM/logging/CLI wiring sections** - Never omit provenance, metadata, or integration points
- **Document Debug Log during implementation** - Write brief plan, capture approaches and decisions
- **Update File List immediately** - Track every changed file as you work, not retrospectively
- **Verify all tasks/subtasks checked [x]** - Story isn't complete if any checkbox remains [ ]

### Story Structure Requirements
- Always include all 14 standard sections in story markdown
- AC evidence table must have test file locations AND performance measurements
- Debug log should capture key decisions and approach changes
- File list must be comprehensive - include test files, fixtures, docs
- Implementation notes should explain WHY, not just WHAT

## Code Quality Lessons

### Quality Gate Enforcement
- **Run Black → Ruff → Mypy BEFORE marking task complete** - Never defer quality gate fixes
- **Fix violations immediately when discovered** - Don't accumulate tech debt
- **mypy must run from project root** - Use `mypy src/data_extract/` not relative paths
- **Zero violations required for greenfield** - `src/data_extract/` must be clean
- **Brownfield violations tracked separately** - Don't mix legacy issues with new code

### Code Style and Standards
- Black formatting with 100 char line limit is non-negotiable
- Ruff replaces flake8 + isort - use it for all linting
- Type hints required on ALL public functions
- Google-style docstrings for public APIs
- Import order: stdlib → third-party → local (enforced by Ruff)

### Technical Debt Management
- Tag TODOs with story numbers for tracking
- Create tech debt stories for deferred work
- Never commit commented-out code
- Remove debug print statements before commit
- Update deprecated patterns immediately

## Testing Lessons

### Test Organization
- **Mirror src/ structure exactly** - `tests/unit/test_extract/` mirrors `src/data_extract/extract/`
- **Write integration tests for NFR validation** - Memory, throughput, latency must be measured
- **Coverage targets: 80% greenfield, 60% overall** - Enforce in CI, measure before claiming done
- **Use Path(__file__).parent for fixtures** - Never hardcode relative paths like `tests/fixtures/`
- **Test edge cases comprehensively** - Boundary values, error conditions, missing data

### Test Implementation Patterns
- Use pytest fixtures for shared test data
- Parametrize tests for multiple input scenarios
- Mock external dependencies consistently
- Integration tests should use real file I/O when possible
- Performance tests must establish baselines first

### Test Naming and Markers
- Test files: `test_{module_name}.py`
- Test classes: `Test{ClassName}`
- Test methods: `test_{scenario}_{expected_result}`
- Use markers consistently: @pytest.mark.unit, @pytest.mark.integration
- Skip slow tests in quick validation runs

## Documentation Lessons

### Documentation Standards
- **ADRs need owners and deadlines** - Documentation is a deliverable, not "nice to have"
- **Performance baselines required for optimization claims** - Measure first, optimize second
- **CLAUDE.md is for essential guidance only** - Keep under 100 lines per section, link to detailed docs
- **Retrospectives capture action items** - Track completion in sprint-status.yaml
- **README files only when explicitly requested** - Don't create documentation proactively

### Documentation Structure
- Keep CLAUDE.md concise - link to detailed docs
- Epic tech specs contain detailed requirements
- Story docs contain implementation details
- Performance docs must include methodology
- API docs generated from docstrings

### Documentation Maintenance
- Update docs in same commit as code changes
- Review docs during code review
- Validate example code still works
- Keep cross-references current
- Archive outdated documentation

## Architecture Lessons

### Design Patterns
- **Protocol-based design > ABC inheritance** - PipelineStage pattern scales without friction
- **Continue-on-error for batch processing** - ProcessingError (recoverable) vs CriticalError (halt)
- **Adapter pattern for brownfield integration** - Wrap legacy code, don't modify it
- **Profile-driven optimization** - cProfile data beats assumptions every time
- **Validate architecture BEFORE implementation** - Confirm brownfield vs greenfield usage upfront

### Data Model Design
- Frozen dataclasses prevent state mutations
- Pydantic for runtime validation
- Type hints on all models
- Optional fields explicit with Optional[T]
- Validation in __post_init__ when needed

### Pipeline Architecture
- Each stage independent and replaceable
- Clear interfaces between stages
- Streaming for memory efficiency
- Batch processing with error recovery
- Deterministic output (same input → same output)

## Process Lessons

### Development Workflow
- **Automation > Memory** - Encode guidelines in scripts so they can't be skipped
- **Code review cycles are teaching moments** - First 2-3 stories have more findings, that's expected
- **Bridge epics prevent downstream blockers** - 1-2 day infrastructure investment saves week of debugging
- **UAT framework for systematic validation** - Use create-test-cases → execute-tests → review workflows
- **Sprint status is authoritative** - Update immediately when story status changes

### Epic Planning
- Break epics into 5-8 stories max
- Each story 0.5-2 days of work
- Dependencies explicit in epic tech spec
- Infrastructure stories come first
- Reserve time for integration testing

### Sprint Execution
- Daily updates to sprint-status.yaml
- Block time for code reviews
- Run quality gates before review request
- Document blockers immediately
- Retrospective after each epic

## Common Pitfalls to Avoid

### Implementation Pitfalls
1. Starting implementation before reading full story spec
2. Skipping quality gates "just this once"
3. Deferring test writing until end
4. Not profiling before optimization
5. Modifying brownfield code directly

### Review Pitfalls
1. Marking story complete with unchecked tasks
2. Missing AC evidence in review
3. Submitting with quality violations
4. Incomplete test coverage
5. No integration tests for new features

### Documentation Pitfalls
1. Creating README files proactively
2. Verbose CLAUDE.md sections
3. Outdated code examples
4. Missing performance baselines
5. No ADR for architecture changes

## Success Patterns

### What Works Well
1. P0 automation scripts save 75% time
2. TDD with RED→GREEN→BLUE cycle
3. Quality gates catch issues early
4. Structured story templates
5. Epic bridge stories prevent blockers

### Metrics of Success
- 80%+ test coverage on greenfield
- <2 review cycles per story
- 0 quality violations in CI
- 90%+ AC completion rate
- <1 day story cycle time

## Action Items from Retrospectives

### Completed Actions
- ✅ Created P0 automation scripts
- ✅ Implemented UAT framework
- ✅ Standardized story templates
- ✅ Added quality gate runner
- ✅ Documented spaCy setup

### Ongoing Improvements
- Refine code review checklist
- Expand performance baselines
- Improve error messages
- Document edge cases better
- Automate more workflows

## Quick Reference Checklist

Before starting a story:
- [ ] Run session initializer
- [ ] Read complete story spec
- [ ] Review epic context
- [ ] Check dependencies

During implementation:
- [ ] Update file list as you work
- [ ] Run quality gates frequently
- [ ] Write tests alongside code
- [ ] Document debug decisions

Before review:
- [ ] All tasks checked
- [ ] AC evidence complete
- [ ] Quality gates pass
- [ ] Coverage targets met
- [ ] Integration tests written

After review:
- [ ] Address all feedback
- [ ] Re-run quality gates
- [ ] Update documentation
- [ ] Mark story complete
- [ ] Update sprint status

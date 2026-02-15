# AI Development Guidelines - Data Extraction Tool

## Purpose
These guidelines are designed to help AI agents make consistent, high-quality decisions when developing code for the Data Extraction Tool project. By following these patterns, AI agents can minimize token consumption on boilerplate decisions and focus resources on critical architectural choices.

## Project Context
- **Project**: Enterprise document processing pipeline for RAG workflows
- **Language**: Python 3.12+ (mandatory enterprise requirement)
- **Architecture**: Five-stage pipeline (Extract → Normalize → Chunk → Semantic → Output)
- **Status**: Epic 3 complete, Epic 4 upcoming

## Code Quality Standards

### Required for ALL Code
1. **Type Hints**: Every function/method must have complete type hints
2. **Docstrings**: Google-style docstrings for all public APIs
3. **Error Handling**: Comprehensive try/except with structlog
4. **Testing**: Minimum 90% coverage for new code
5. **Formatting**: Black (100 char lines), Ruff linting, Mypy strict

### Import Order
```python
#!/usr/bin/env python3
"""Module docstring."""

# Standard library
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Third-party
import structlog
import pytest

# Local
from data_extract.core import models
```

## Design Patterns

### Script Structure Pattern
All scripts follow this standard structure:
1. Shebang and module docstring
2. Imports (standard → third-party → local)
3. Constants (UPPER_SNAKE_CASE)
4. Classes (PascalCase, with __init__ first)
5. Functions (snake_case, type-hinted)
6. Argument parser
7. Main function with error handling
8. `if __name__ == "__main__":` guard

### Error Handling Pattern
```python
try:
    # Operation
    result = perform_operation()
    logger.info("operation_success", result=result)
except SpecificError as e:
    logger.error("operation_failed", error=str(e))
    # Handle gracefully
except Exception as e:
    logger.error("unexpected_error", error=str(e))
    raise  # Re-raise unexpected errors
```

### Testing Pattern
```python
class TestComponent:
    """Test suite for Component."""

    @pytest.fixture
    def instance(self):
        """Create instance for testing."""
        return Component()

    def test_success_case(self, instance):
        """Test successful operation."""
        result = instance.method()
        assert result == expected

    def test_error_case(self, instance):
        """Test error handling."""
        with pytest.raises(ExpectedException):
            instance.method_that_fails()
```

## File Organization

### Directory Structure
```
src/data_extract/
├── extract/       # Stage 1: Extractors
├── normalize/     # Stage 2: Normalizers
├── chunk/         # Stage 3: Chunking
├── semantic/      # Stage 4: Analysis (upcoming)
├── output/        # Stage 5: Formatters
└── core/          # Shared models

tests/
├── unit/          # Mirrors src/ structure
├── integration/   # End-to-end tests
├── performance/   # Performance benchmarks
└── fixtures/      # Shared test data
    └── greenfield/  # Standardized fixtures
```

### Naming Conventions
- **Files**: `snake_case.py` (e.g., `pdf_extractor.py`)
- **Classes**: `PascalCase` (e.g., `PdfExtractor`)
- **Functions**: `snake_case` (e.g., `extract_content`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_CHUNK_SIZE`)
- **Tests**: `test_` prefix (e.g., `test_pdf_extractor.py`)

## Performance Requirements

### Latency Targets
- Small files (<1MB): <100ms
- Medium files (<10MB): <500ms
- Large files (<100MB): <2s
- Memory usage: <500MB peak

### Optimization Guidelines
1. Profile before optimizing
2. Use generators for memory efficiency
3. Batch operations when possible
4. Cache expensive computations
5. Document performance baselines

## Documentation Standards

### Code Comments
- Explain WHY, not WHAT
- Complex algorithms need inline comments
- TODO comments must include owner and date
- Reference tickets/stories for context

### Docstring Format
```python
def process_document(
    input_path: Path,
    config: Dict[str, Any],
    validate: bool = True
) -> ProcessingResult:
    """
    Process a document through the extraction pipeline.

    Args:
        input_path: Path to input document
        config: Processing configuration
        validate: Whether to validate output

    Returns:
        ProcessingResult containing extracted data

    Raises:
        FileNotFoundError: If input file doesn't exist
        ValidationError: If validation fails
    """
```

## Testing Requirements

### Test Categories
1. **Unit Tests** (`-m unit`): Test individual components
2. **Integration Tests** (`-m integration`): Test component interactions
3. **Performance Tests** (`-m performance`): Verify speed/memory
4. **Edge Cases**: Special characters, empty inputs, large files

### Coverage Targets
- New code: >90% coverage
- Critical paths: >95% coverage
- Overall project: >80% coverage

### Test File Structure
Tests must mirror source structure exactly:
- `src/data_extract/extract/pdf.py` → `tests/unit/test_extract/test_pdf.py`
- One test file per source file
- Group related tests in classes

## Common Pitfalls to Avoid

### DO NOT:
1. Use relative imports in scripts
2. Catch generic Exception without re-raising
3. Use mutable default arguments
4. Skip type hints or docstrings
5. Create files without explicit user request
6. Use print() instead of logger
7. Hard-code paths or credentials
8. Ignore pre-commit failures

### ALWAYS:
1. Use Path from pathlib (never string paths)
2. Handle errors gracefully
3. Validate inputs
4. Write tests for new code
5. Run quality checks before committing
6. Document architectural decisions
7. Profile performance-critical code
8. Follow existing patterns in codebase

## Decision Framework

When making architectural decisions:

1. **Check existing patterns**: Look for similar code in the codebase
2. **Prefer composition**: Use dependency injection over hard coupling
3. **Design for testability**: Make components mockable
4. **Optimize readability**: Clear code > clever code
5. **Document decisions**: Add comments explaining non-obvious choices

## BMAD Method Integration

This project follows BMAD (Business Method for AI Development) practices:

### Story Development
- Stories follow template from `scripts/generate_story_template.py`
- Acceptance criteria must be verifiable
- Include wiring checklist (BOM, logging, CLI, testing)
- Document completion evidence

### Quality Gates
All code must pass:
1. `black src/ tests/` - Formatting
2. `ruff check src/ tests/` - Linting
3. `mypy src/data_extract/` - Type checking
4. `pytest` - All tests passing
5. Pre-commit hooks - All checks green

### Epic Development Flow
1. Story creation (use template generator)
2. Implementation with TDD
3. Integration testing
4. Performance validation
5. Documentation updates
6. UAT execution
7. Review and merge

## Efficiency Optimizations

### Token-Saving Patterns
1. **Use fixtures**: Import from `tests.fixtures.greenfield` instead of recreating
2. **Follow schemas**: Validate against `schemas/*.yaml` for structure
3. **Reuse patterns**: Copy from similar existing code
4. **Batch operations**: Combine related changes
5. **Skip obvious**: Don't explain basic Python concepts

### Quick Decisions
For these common scenarios, use the standard pattern without deliberation:
- **Logging**: Always use structlog with structured fields
- **Paths**: Always use pathlib.Path
- **Config**: Always use Pydantic models for validation
- **Testing**: Always use pytest with fixtures
- **Errors**: Always log before raising/handling

## Integration Points

### CLI (Epic 5)
- Use Typer for CLI framework
- Support both single and batch processing
- Provide progress indicators with Rich
- Support dry-run mode

### Configuration
Four-tier cascade (Epic 5):
1. CLI flags (highest priority)
2. Environment variables (`DATA_EXTRACT_*`)
3. YAML config file
4. Hardcoded defaults (lowest)

### Pipeline Stages
Each stage must:
- Implement base ABC interface
- Use frozen dataclasses for data
- Support streaming/generators
- Handle errors gracefully
- Log structured events

## Success Criteria

Code is considered production-ready when:
1. All tests pass (>90% coverage)
2. Quality gates pass (black, ruff, mypy)
3. Performance targets met
4. Documentation complete
5. Integration tests verify end-to-end flow
6. Code review approved
7. No TODO comments remain

## References

- Project Documentation: `docs/`
- Architecture Decisions: `docs/architecture/index.md`
- Epic Specifications: `docs/tech-spec-epic-*/`
- Story Templates: `docs/tech-spec-drafts/`
- Performance Baselines: `docs/architecture/epic-4-performance-baselines.md`

---

**Remember**: These guidelines enable deterministic quality. When in doubt, check existing code patterns or ask for clarification rather than making assumptions.

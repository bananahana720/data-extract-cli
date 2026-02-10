# QA Fixtures Maintenance Guide

## Overview

This guide provides comprehensive instructions for maintaining and updating the QA fixtures infrastructure used for Epic 4 semantic analysis testing and beyond. The fixtures provide validated, PII-free test data with documented quality baselines.

## Fixture Architecture

### Core Components

```
tests/fixtures/
├── semantic_corpus.py         # Main corpus generators
├── greenfield/
│   ├── test_fixtures.py      # Reusable test patterns
│   └── pii_scanner.py        # PII detection utility
└── __pycache__/               # Cached bytecode
```

### Validation Infrastructure

```
tests/integration/test_fixtures/
├── test_semantic_corpus.py    # Pytest-based validation (8 test cases)
└── validate_qa_fixtures.py    # Standalone validation runner
```

## Adding New Test Data

### 1. Adding to Existing Corpora

To add new documents to an existing corpus:

```python
# In tests/fixtures/semantic_corpus.py

def get_technical_corpus() -> List[str]:
    return [
        # Existing documents...

        # Add new document
        """Your new technical document content here.
        Ensure it follows the corpus theme and maintains
        quality characteristics.""",
    ]
```

**Requirements:**
- Minimum 20 words per document
- No PII (names, emails, SSNs, etc.)
- Synthetic content only (no real company data)
- Maintain corpus theme (technical, business, etc.)

### 2. Creating New Corpus Types

To add a new corpus type (e.g., legal documents):

```python
def get_legal_corpus() -> List[str]:
    """
    Generate legal document corpus.

    Returns:
        List of legal-themed documents for testing
    """
    return [
        """Legal document content focusing on contracts,
        agreements, and regulatory compliance...""",
        # Add more documents...
    ]

# Update CORPUS_CHARACTERISTICS
CORPUS_CHARACTERISTICS["legal"] = {
    "size": 5,
    "avg_words": 50,
    "vocabulary": "legal, contracts, compliance",
    "diversity": "medium",
}
```

### 3. Adding Edge Cases

Edge cases test boundary conditions:

```python
def get_edge_case_corpus() -> List[str]:
    return [
        # Existing edge cases...

        # Add new edge case with comment
        # Test case: Nested quotes and escapes
        'Test "nested \'quotes\'" and escape\\ncharacters.',
    ]
```

## Quality Requirements

### Minimum Standards

All fixtures must meet these requirements:

| Metric | Requirement | How to Measure |
|--------|-------------|----------------|
| **Corpus Size** | ≥5 documents per corpus | `len(get_corpus())` |
| **Word Count** | ≥200 total words per corpus | `sum(len(doc.split()) for doc in corpus)` |
| **Vocabulary Diversity** | ≥0.3 (unique/total) | `len(unique_words) / len(total_words)` |
| **PII Compliance** | Zero PII violations | `PIIScanner.scan_corpus()` |
| **Load Time** | <100ms for all fixtures | `time.perf_counter()` |
| **Memory Usage** | <10MB per corpus | `sys.getsizeof()` |

### PII Compliance

**Never include:**
- Real person names (use Alice, Bob, Test User)
- Email addresses (except test@example.com)
- Phone numbers (except 555-XXXX)
- SSNs, credit cards, passport numbers
- Real company names (Microsoft, Google, etc.)
- API keys, passwords, tokens
- Private IP addresses

**Validation:**
```bash
# Run PII scan on fixtures
python -c "
from tests.fixtures.greenfield.pii_scanner import PIIScanner
from tests.fixtures.semantic_corpus import get_technical_corpus

scanner = PIIScanner()
results = scanner.scan_corpus(get_technical_corpus(), 'technical')
print('Clean' if results['is_clean'] else f'Violations: {results[\"violations\"]}')
"
```

## Testing Changes

### Quick Validation

After making changes, run the standalone validator:

```bash
# No pytest required
python tests/integration/test_fixtures/validate_qa_fixtures.py
```

Expected output:
```
✅ ALL VALIDATION TESTS PASSED!
Epic 4 has validated, reliable test data foundation.
```

### Full Test Suite

With pytest installed:

```bash
# Run all fixture validation tests
pytest tests/integration/test_fixtures/test_semantic_corpus.py -v

# Run specific test case
pytest tests/integration/test_fixtures/test_semantic_corpus.py::TestCorpusSize -v

# Run with coverage
pytest tests/integration/test_fixtures/ --cov=tests/fixtures --cov-report=html
```

### Performance Testing

```bash
# Test load times
pytest tests/integration/test_fixtures/test_semantic_corpus.py::TestPerformanceCharacteristics -v

# Profile fixture loading
python -m cProfile -s cumtime tests/fixtures/semantic_corpus.py
```

## Versioning Strategy

### Schema Versions

Fixtures follow Epic-based versioning:

- **Epic 3.5**: Initial QA fixtures (semantic_corpus v1.0)
- **Epic 4**: Enhanced with gold standards (semantic_corpus v1.1)
- **Epic 5**: [Future] Batch processing fixtures

### Backward Compatibility

**Always maintain:**
1. Function signatures (don't change parameters)
2. Return types (always List[str] for corpora)
3. Default behavior (generate_large_corpus() defaults)

**Safe changes:**
- Adding new documents to existing corpora
- Creating new corpus types
- Adding optional parameters with defaults

**Breaking changes (require version bump):**
- Removing/renaming functions
- Changing return types
- Modifying required parameters

### Deprecation Process

```python
def old_corpus_function():
    """
    DEPRECATED: Use get_new_corpus() instead.
    Will be removed in Epic 6.
    """
    import warnings
    warnings.warn(
        "old_corpus_function is deprecated, use get_new_corpus",
        DeprecationWarning,
        stacklevel=2
    )
    return get_new_corpus()
```

## Maintenance Checklist

### Weekly Tasks
- [ ] Run validation suite
- [ ] Check for PII violations
- [ ] Review performance metrics

### Per-Epic Tasks
- [ ] Update corpus content for new requirements
- [ ] Add test cases for new features
- [ ] Document changes in CORPUS_CHARACTERISTICS
- [ ] Update this maintenance guide

### Before Release
- [ ] All validation tests passing (8/8)
- [ ] PII scan clean
- [ ] Performance within limits
- [ ] Documentation updated
- [ ] Backward compatibility verified

## Troubleshooting

### Common Issues

**Issue: PII violation detected**
```python
# Debug which document has PII
from tests.fixtures.greenfield.pii_scanner import PIIScanner

scanner = PIIScanner()
for idx, doc in enumerate(corpus):
    violations = scanner.scan_text(doc, f"doc_{idx}")
    if violations:
        print(f"Document {idx} has PII: {violations}")
```

**Issue: Low vocabulary diversity**
```python
# Analyze vocabulary
import re

words = re.findall(r'\b\w+\b', ' '.join(corpus).lower())
unique = set(words)
print(f"Diversity: {len(unique)}/{len(words)} = {len(unique)/len(words):.2f}")
```

**Issue: Performance degradation**
```python
# Profile loading time
import time

start = time.perf_counter()
corpus = get_technical_corpus()
elapsed = (time.perf_counter() - start) * 1000
print(f"Load time: {elapsed:.1f}ms")
```

## Integration with Epic 4

### Semantic Analysis Requirements

Epic 4 semantic analysis expects:
- Diverse vocabulary for TF-IDF testing
- Multiple document types for clustering
- Edge cases for boundary testing
- Gold standard pairs for similarity validation

### Usage in Tests

```python
# Example: Testing semantic similarity
from tests.fixtures.semantic_corpus import get_similarity_test_pairs
from data_extract.semantic import SemanticAnalyzer

analyzer = SemanticAnalyzer()
for pair in get_similarity_test_pairs():
    similarity = analyzer.calculate_similarity(pair["doc1"], pair["doc2"])
    min_expected, max_expected = pair["expected_similarity"]
    assert min_expected <= similarity <= max_expected
```

## Best Practices

### Content Guidelines

1. **Keep it realistic but synthetic**
   - Use industry terminology
   - Maintain professional tone
   - Avoid obvious test patterns

2. **Ensure diversity**
   - Mix sentence lengths
   - Vary vocabulary
   - Include different document structures

3. **Document edge cases**
   - Comment what each edge case tests
   - Explain expected behavior
   - Reference related issues/stories

### Code Organization

```python
# Group related fixtures
class TechnicalFixtures:
    @staticmethod
    def get_api_docs():
        return [...]

    @staticmethod
    def get_architecture_docs():
        return [...]

# Use clear naming
def get_malformed_json_corpus():  # Clear purpose
    """Corpus with intentionally malformed JSON."""
    return [...]
```

### Testing Philosophy

- **Test the validators**: Ensure validation tests catch real issues
- **Automate everything**: No manual verification steps
- **Fail fast**: Detect issues early in development
- **Document baselines**: Track metrics over time

## Future Enhancements

### Planned for Epic 5
- Streaming corpus generators for large-scale testing
- Parameterized corpus generation
- Multi-language support
- Domain-specific corpora (medical, legal, financial)

### Proposed Improvements
- Automatic corpus generation from templates
- Integration with external data sources
- Smart PII redaction (replace, don't remove)
- Corpus quality scoring system

## References

- [Epic 3.5 Story Documentation](../docs/stories/story-3.5-*.md)
- [Epic 4 Semantic Analysis Spec](../docs/tech-spec-epic-4.md)
- [PII Detection Standards](https://www.privacy.gov/pii)
- [Test Data Management Best Practices](https://www.testingstandards.org)

## Contact

For questions or issues with QA fixtures:
- Create issue in project repository
- Tag with `qa-fixtures` and `epic-4`
- Include validation test output in issue description

---

*Last Updated: November 2024*
*Version: 1.1 (Epic 4 Release)*

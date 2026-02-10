# Semantic QA Fixtures

## Overview

This directory contains a comprehensive semantic test corpus with gold-standard annotations for validating Epic 4 semantic analysis features. The corpus meets all requirements from Story 3.5-6-semantic-qa-fixtures.

## Corpus Statistics

- **Total Documents**: 55
- **Total Word Count**: 264,025 words
- **Average Words per Document**: 4,800 words
- **Document Types**: 3 (Audit Reports, Risk Matrices, Compliance Documents)
- **PII Status**: ✅ Fully sanitized (no real names, SSNs, or personal data)
- **Gold-Standard Annotations**: 45 documents (exceeds 40+ requirement)

### Document Distribution

| Document Type | Count | Total Words | Avg Words/Doc |
|--------------|-------|-------------|---------------|
| Audit Reports | 20 | 96,660 | 4,833 |
| Risk Matrices | 18 | 86,598 | 4,811 |
| Compliance Documents | 17 | 80,767 | 4,751 |

## Directory Structure

```
tests/fixtures/semantic/
├── corpus/                        # Document corpus
│   ├── audit-reports/             # Audit report documents
│   ├── risk-matrices/             # Risk assessment matrices
│   ├── compliance-docs/           # Compliance documents
│   └── metadata.json              # Corpus metadata
├── gold-standard/                 # Gold-standard annotations
│   ├── gold_standard_annotations.json  # Complete annotations
│   ├── tfidf_annotations.json    # TF-IDF annotations
│   ├── lsa_annotations.json      # LSA topic annotations
│   ├── entity_annotations.json   # Entity extraction annotations
│   ├── readability_annotations.json # Readability scores
│   ├── tfidf_vectorizer.joblib   # Pre-fitted TF-IDF model
│   └── lsa_model.joblib          # Pre-fitted LSA model
├── harness/                       # Comparison harness scripts
│   ├── compare-tfidf.py          # TF-IDF regression test
│   ├── compare-lsa.py            # LSA regression test
│   └── compare-entities.py       # Entity extraction test
└── README.md                      # This documentation
```

## Annotation Format

### Gold-Standard Schema

Each annotated document contains four types of annotations:

#### 1. TF-IDF Annotations
```json
{
  "top_terms": [
    {"term": "control", "score": 0.2845},
    {"term": "risk assessment", "score": 0.2134},
    ...
  ],
  "num_unique_terms": 187,
  "max_tfidf_score": 0.2845
}
```

#### 2. LSA Topic Annotations
```json
{
  "primary_topic": 3,
  "top_topics": [
    {"topic_id": 3, "weight": 0.6234},
    {"topic_id": 1, "weight": 0.2145},
    {"topic_id": 7, "weight": 0.0987}
  ],
  "topic_diversity": 0.1823
}
```

#### 3. Entity Annotations
```json
{
  "entities": [
    "RISK-001-01",
    "CTRL-001-02",
    "REQ-001-003",
    ...
  ],
  "entity_count": 45,
  "unique_entity_types": 4
}
```

#### 4. Readability Annotations
```json
{
  "flesch_reading_ease": 35.67,
  "flesch_kincaid_grade": 14.2,
  "gunning_fog": 16.8,
  "smog_index": 15.3,
  "coleman_liau_index": 14.5,
  "automated_readability_index": 15.1,
  "text_standard": "15th and 16th grade"
}
```

## Entity Patterns

The corpus contains the following synthetic entity patterns:

| Pattern | Description | Example |
|---------|-------------|---------|
| `RISK-XXX-XX` | Risk identifiers | RISK-001-01 |
| `CTRL-XXX-XX` | Control identifiers | CTRL-002-03 |
| `REQ-XXX-XXX` | Requirement identifiers | REQ-001-002 |
| `ACTION-XXX-XXX` | Action item identifiers | ACTION-003-001 |
| `KRI-XXX` | Key Risk Indicators | KRI-001 |
| `COMP-XXXX` | Compliance references | COMP-0001 |
| `TECH-CTRL-XXX-XXX` | Technical controls | TECH-CTRL-001-002 |
| `ADMIN-CTRL-XXX-XXX` | Administrative controls | ADMIN-CTRL-001-001 |

## Comparison Harness Usage

### Running TF-IDF Comparison

```bash
# Test all documents with default 80% tolerance
python harness/compare-tfidf.py

# Test with custom tolerance (e.g., 90%)
python harness/compare-tfidf.py 0.9

# Test specific documents
python harness/compare-tfidf.py 0.8 audit-report-0001 risk-matrix-0005
```

**Tolerance**: Minimum term overlap ratio (default: 0.8 = 80%)
- Compares top 10 TF-IDF terms
- Calculates term overlap and score similarity
- Success requires 90% of documents to pass tolerance

### Running LSA Comparison

```bash
# Test all documents with default 70% tolerance
python harness/compare-lsa.py

# Test with custom tolerance
python harness/compare-lsa.py 0.75

# Test specific documents
python harness/compare-lsa.py 0.7 audit-report-0001 compliance-doc-0003
```

**Tolerance**: Minimum similarity score (default: 0.7 = 70%)
- Compares primary topic assignment
- Validates top 3 topics
- Calculates cosine similarity of topic weights
- Success requires 90% of documents to pass

### Running Entity Extraction Comparison

```bash
# Test all documents with default 80% F1 score tolerance
python harness/compare-entities.py

# Test with custom tolerance
python harness/compare-entities.py 0.85

# Test specific documents
python harness/compare-entities.py 0.8 risk-matrix-0001 compliance-doc-0002
```

**Tolerance**: Minimum F1 score (default: 0.8 = 80%)
- Calculates precision, recall, and F1 score
- Reports missing and extra entities
- Provides aggregate metrics across all documents
- Success requires 90% of documents to pass

## Corpus Creation Process

The corpus was generated through the following process:

1. **Document Generation** (`generate_full_corpus.py`)
   - Created synthetic audit-domain documents using templates
   - Ensured balanced distribution across document types
   - Generated entity references following consistent patterns

2. **PII Sanitization** (`validate_pii.py`)
   - Scanned all documents with PIIScanner utility
   - Verified no real names, SSNs, or personal data
   - Confirmed synthetic entity patterns are safe

3. **Gold-Standard Generation** (`generate_gold_standard.py`)
   - Applied validated TF-IDF vectorizer from Story 3.5-4
   - Generated LSA topic assignments with 10 topics
   - Extracted entity references using regex patterns
   - Calculated readability metrics using textstat

4. **Harness Creation**
   - Implemented comparison scripts for each annotation type
   - Defined tolerance thresholds based on expected variance
   - Added pytest integration capability

## Integration with Epic 4 (COMPLETE - V1.0)

This test corpus is now in production use for Epic 4 semantic analysis validation:

1. **TF-IDF Vectorization Engine** (Story 4.1 - COMPLETE)
   - Corpus used for performance benchmarking (10ms vs 100ms requirement)
   - Validated against gold-standard TF-IDF annotations with 100% pass rate

2. **Document Similarity Analysis** (Story 4.2 - COMPLETE)
   - Tested similarity calculations on diverse document pairs
   - Verified cosine similarity implementations (4.8ms vs 200ms requirement)

3. **LSA Implementation** (Story 4.3 - COMPLETE)
   - Validated topic modeling against gold-standard
   - Tested dimensionality reduction effectiveness (98.5% average similarity)

4. **Quality Metrics** (Story 4.4 - COMPLETE)
   - Compared readability scores with gold-standard
   - Validated textstat integration (0.12ms vs 10ms requirement)

5. **CLI and Reporting** (Story 4.5 - COMPLETE)
   - Used corpus for end-to-end testing
   - Generated sample reports for validation

## Quality Assurance

### Validation Performed

- ✅ Document count: 55 documents (exceeds 50+ requirement)
- ✅ Word count: 264,025 words (exceeds 250,000+ requirement)
- ✅ Document types: 3 types with balanced distribution
- ✅ PII sanitization: 100% clean (verified by PIIScanner)
- ✅ Gold-standard coverage: 45 documents annotated (exceeds 40+)
- ✅ Comparison harness: All 3 scripts operational
- ✅ Documentation: Comprehensive README with usage instructions

### Test Results

All comparison harness scripts pass with 100% success rate when run against gold-standard:

- TF-IDF Comparison: 100% term overlap (10/10 documents)
- LSA Comparison: 98.5% average similarity (10/10 documents)
- Entity Extraction: 100% F1 score (10/10 documents)

## Maintenance

### Adding New Documents

1. Generate documents using `generate_full_corpus.py` as template
2. Validate PII-free status with `validate_pii.py`
3. Regenerate gold-standard annotations with `generate_gold_standard.py`
4. Test comparison harness scripts to ensure compatibility

### Updating Gold-Standard

1. Modify annotation generation logic in `generate_gold_standard.py`
2. Re-run to generate new annotations
3. Update harness scripts if annotation schema changes
4. Document changes in this README

## Related Documentation

- Story specification: `docs/stories/3.5-6-semantic-qa-fixtures.md`
- Story context: `docs/stories/3.5-6-semantic-qa-fixtures.context.xml`
- Tech spec: `docs/tech-spec-epic-3.5.md`
- Semantic smoke test: `scripts/smoke_test_semantic.py`
- PII scanner utility: `tests/fixtures/greenfield/pii_scanner.py`

## Version History

- **V1.0 (2025-12-01)**: Production release - Epic 4 complete, all fixtures in active use
- **Initial Release (2025-11-18)**: Created for Epic 3.5 (Bridge Epic - Tooling & Semantic Prep)

Epic: 3.5 (Bridge Epic - Tooling & Semantic Prep)
Status: Production - Used in Epic 4 semantic analysis validation

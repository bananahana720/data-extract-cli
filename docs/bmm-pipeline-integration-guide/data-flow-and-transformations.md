# Data Flow and Transformations

## Data Structure Evolution

```
INPUT: document.docx
    │
    │ ┌─────────────────────────────────────┐
    ├─► EXTRACTION STAGE                    │
    │ └─────────────────────────────────────┘
    ▼
ExtractionResult(
    content_blocks=(
        ContentBlock(
            block_id="abc123",
            block_type=ContentType.PARAGRAPH,
            content="This is a paragraph.",
            metadata={},  # Empty metadata
            parent_id=None,  # No hierarchy yet
        ),
        ...
    ),
    document_metadata=DocumentMetadata(...),
    images=(...),
    tables=(...),
)
    │
    │ ┌─────────────────────────────────────┐
    ├─► PROCESSING: ContextLinker           │
    │ └─────────────────────────────────────┘
    ▼
ProcessingResult(
    content_blocks=(
        ContentBlock(
            block_id="abc123",  # Same ID
            content="This is a paragraph.",  # Same content
            metadata={
                "depth": 2,  # NEW: Hierarchy depth
                "document_path": ["Chapter 1", "Section 1.1"],  # NEW: Breadcrumb
            },
            parent_id="heading123",  # NEW: Parent reference
        ),
        ...
    ),
)
    │
    │ ┌─────────────────────────────────────┐
    ├─► PROCESSING: MetadataAggregator      │
    │ └─────────────────────────────────────┘
    ▼
ProcessingResult(
    content_blocks=(
        ContentBlock(
            block_id="abc123",
            content="This is a paragraph.",
            metadata={
                "depth": 2,  # Preserved
                "document_path": ["Chapter 1", "Section 1.1"],  # Preserved
                "word_count": 4,  # NEW: Word count
                "char_count": 19,  # NEW: Character count
            },
            parent_id="heading123",  # Preserved
        ),
        ...
    ),
    stage_metadata={
        "total_words": 1234,
        "average_words_per_block": 42.3,
        ...
    },
)
    │
    │ ┌─────────────────────────────────────┐
    ├─► PROCESSING: SemanticAnalyzer        │ ← YOUR PROCESSOR
    │ └─────────────────────────────────────┘
    ▼
ProcessingResult(
    content_blocks=(
        ContentBlock(
            block_id="abc123",
            content="This is a paragraph.",
            metadata={
                "depth": 2,  # Preserved
                "document_path": ["Chapter 1", "Section 1.1"],  # Preserved
                "word_count": 4,  # Preserved
                "char_count": 19,  # Preserved
                "entities": ["example entity"],  # NEW: Extracted entities
                "semantic_tags": ["process", "control"],  # NEW: Domain tags
                "entity_types": {"example entity": "process"},  # NEW: Entity classification
                "domain_classification": "cybersecurity_audit",  # NEW: Domain
            },
            parent_id="heading123",  # Preserved
        ),
        ...
    ),
    stage_metadata={
        "entities_found": 42,
        "unique_entities": 28,
        ...
    },
)
    │
    │ ┌─────────────────────────────────────┐
    ├─► PROCESSING: QualityValidator        │
    │ └─────────────────────────────────────┘
    ▼
ProcessingResult(
    content_blocks=(...),  # All metadata preserved + quality_checked flag
    quality_score=85.2,  # NEW: Quality score
    quality_issues=(...),  # NEW: Quality issues
    needs_review=False,  # NEW: Review flag
)
    │
    │ ┌─────────────────────────────────────┐
    ├─► FORMATTING: JsonFormatter           │
    │ └─────────────────────────────────────┘
    ▼
FormattedOutput(
    content='{"content_blocks": [...], ...}',  # JSON string
    format_type="json",
)
    │
    ▼
OUTPUT: document.json (with all enriched metadata)
```

## Metadata Preservation Pattern

**Critical Rule**: Each processor must preserve metadata from previous processors

```python
# ✅ CORRECT: Preserve existing metadata
enriched_metadata = {
    **block.metadata,  # Spread existing metadata
    "new_field": new_value,  # Add new fields
}

# ❌ WRONG: Overwrites existing metadata
enriched_metadata = {
    "new_field": new_value,  # Loses all previous enrichments!
}
```

---

# Data Enrichment Patterns

## Pattern 1: Metadata Preservation (CRITICAL)

**Rule**: Always preserve existing metadata from previous processors

```python
# ✅ CORRECT: Spread existing metadata, add new fields
enriched_metadata = {
    **block.metadata,  # Preserve all existing fields
    "entities": extracted_entities,  # Add new field
    "semantic_tags": tags,  # Add new field
}

# ❌ WRONG: Overwrites all existing metadata
enriched_metadata = {
    "entities": extracted_entities,  # Loses depth, document_path, word_count, etc.!
}
```

**Why This Matters**: Each processor builds on previous enrichments. If you overwrite metadata, you break the chain.

## Pattern 2: Immutable Block Creation

**Rule**: Never modify existing ContentBlocks, always create new ones

```python
# ✅ CORRECT: Create new ContentBlock
enriched_block = ContentBlock(
    block_id=block.block_id,  # Same ID (preserve reference)
    block_type=block.block_type,  # Same type
    content=block.content,  # Same content
    raw_content=block.raw_content,  # Same raw content
    position=block.position,  # Same position
    parent_id=block.parent_id,  # Same parent
    related_ids=block.related_ids,  # Same relations
    metadata=enriched_metadata,  # ENRICHED metadata
    confidence=block.confidence,  # Same confidence
    style=block.style,  # Same style
)

# ❌ WRONG: Modify existing block (ContentBlock is frozen dataclass)
block.metadata["entities"] = extracted_entities  # ERROR: frozen instance
```

## Pattern 3: Media Asset Preservation (CRITICAL)

**Rule**: Always pass through images and tables unchanged

```python
# ✅ CORRECT: Preserve media assets
return ProcessingResult(
    content_blocks=tuple(enriched_blocks),
    document_metadata=extraction_result.document_metadata,
    images=extraction_result.images,  # PRESERVE
    tables=extraction_result.tables,  # PRESERVE
    processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
    stage_metadata={...},
    success=True,
)

# ❌ WRONG: Drop media assets
return ProcessingResult(
    content_blocks=tuple(enriched_blocks),
    document_metadata=extraction_result.document_metadata,
    # Missing images and tables! They're lost forever!
    processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
    stage_metadata={...},
    success=True,
)
```

**Why This Matters**: Images and tables are extracted by extractors (DOCX, PDF, etc.). If processors don't preserve them, they're lost from the output.

## Pattern 4: Empty Input Handling

**Rule**: Gracefully handle empty content blocks

```python
def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
    """Process extracted content."""

    # Handle empty input
    if not extraction_result.content_blocks:
        return ProcessingResult(
            content_blocks=tuple(),
            document_metadata=extraction_result.document_metadata,
            images=extraction_result.images,
            tables=extraction_result.tables,
            processing_stage=ProcessingStage.SEMANTIC_ANALYSIS,
            stage_metadata={"entities_found": 0},
            success=True,  # Empty is not an error
        )

    # Normal processing
    ...
```

## Pattern 5: Partial Processing (Best Effort)

**Rule**: Process as many blocks as possible, don't fail entire pipeline on single block error

```python
def process(self, extraction_result: ExtractionResult) -> ProcessingResult:
    """Process with best-effort approach."""

    enriched_blocks = []
    errors = []

    for block in extraction_result.content_blocks:
        try:
            # Try to enrich this block
            enriched_block = self._enrich_block(block)
            enriched_blocks.append(enriched_block)
        except Exception as e:
            # Log error but continue
            self.logger.warning(f"Failed to enrich block {block.block_id}: {e}")
            errors.append(f"Block {block.block_id}: {str(e)}")
            # Add original block (no enrichment for this one)
            enriched_blocks.append(block)

    return ProcessingResult(
        content_blocks=tuple(enriched_blocks),
        ...,
        success=True,  # Overall success (partial processing)
        errors=tuple(errors),  # But log errors for debugging
    )
```

---

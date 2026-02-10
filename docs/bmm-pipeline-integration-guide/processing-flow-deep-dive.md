# Processing Flow Deep Dive

## Validation Stage (Lines 334-395)

**Purpose**: Ensure file can be processed before attempting extraction

**Checks Performed**:
1. File exists (`file_path.exists()`)
2. Format detected from extension
3. Extractor registered for format

**Failure Handling**:
- Returns `PipelineResult` with `success=False`
- Sets `failed_stage=ProcessingStage.VALIDATION`
- Includes descriptive error messages

**Integration Note**: Validation stage is complete and rarely needs modification.

## Extraction Stage (Lines 397-434)

**Purpose**: Extract raw content from document

**Process**:
1. Get registered extractor for detected format
2. Call `extractor.extract(file_path)`
3. Collect errors and warnings
4. Return `ExtractionResult` with content blocks

**Data Structures Created**:
```python
ExtractionResult(
    content_blocks=(ContentBlock, ...),  # Extracted content
    document_metadata=DocumentMetadata(...),  # File properties
    images=(ImageMetadata, ...),  # Extracted images
    tables=(TableMetadata, ...),  # Extracted tables
    success=True,
    errors=(),
    warnings=()
)
```

**Integration Note**: Extractors are stable. For semantic analysis, focus on processing stage.

## Processing Stage (Lines 436-550) ⭐ PRIMARY INTEGRATION POINT

**Purpose**: Enrich extracted content with hierarchy, metadata, and quality scores

**Process**:
1. Order processors by dependencies (topological sort)
2. Run each processor in sequence
3. Each processor transforms `ExtractionResult` → `ProcessingResult`
4. Output of one processor becomes input of next

**Current Processor Chain**:

```python
# Automatic ordering based on dependencies
ordered_processors = self._order_processors()  # Returns:
# [ContextLinker, MetadataAggregator, QualityValidator]

for processor in ordered_processors:
    # Convert ExtractionResult to ProcessingResult (first processor)
    if isinstance(current_input, ExtractionResult):
        processing_result = processor.process(current_input)
    else:
        # Adapt ProcessingResult to ExtractionResult (subsequent processors)
        pseudo_extraction = ExtractionResult(
            content_blocks=current_input.content_blocks,
            document_metadata=current_input.document_metadata,
            images=current_input.images,
            tables=current_input.tables,
            success=True
        )
        processing_result = processor.process(pseudo_extraction)

    # Check success
    if not processing_result.success:
        if processor.is_optional():
            # Continue if processor is optional
            pass
        else:
            # Fail pipeline if processor is required
            return PipelineResult(success=False, ...)

    # Use output as input for next processor
    current_input = processing_result
```

**Media Asset Preservation** (Lines 469-477):
- **Critical**: Images and tables must be preserved through processor chain
- Each processor receives and returns media assets unchanged
- Processors enrich `content_blocks` but preserve `images` and `tables`

**Where Semantic Analyzer Fits**:
```python
# After MetadataAggregator, before QualityValidator
pipeline.add_processor(ContextLinker())       # Dependency 1
pipeline.add_processor(MetadataAggregator()) # Dependency 2
pipeline.add_processor(SemanticAnalyzer())   # NEW ← Your processor
pipeline.add_processor(QualityValidator())   # Runs after semantic analysis
```

## Formatting Stage (Lines 552-591)

**Purpose**: Generate output in multiple formats (parallel execution)

**Process**:
1. Loop through all registered formatters
2. Call `formatter.format(processing_result)` for each
3. Collect `FormattedOutput` from successful formatters
4. Continue even if some formatters fail (best effort)

**Data Structures Created**:
```python
FormattedOutput(
    content=str,  # Formatted content (JSON, Markdown, etc.)
    format_type=str,  # "json", "markdown", "chunked_text"
    source_document=Path,
    success=True,
    errors=(),
    warnings=()
)
```

**Integration Note**: Add `RagOptimizedFormatter` here for RAG-specific output.

---

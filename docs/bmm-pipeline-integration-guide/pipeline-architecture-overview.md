# Pipeline Architecture Overview

## Design Philosophy

The extraction pipeline follows a **staged processing architecture** with clear separation of concerns:

1. **Validation Stage**: File exists, format detected, extractor available
2. **Extraction Stage**: Format-specific content extraction
3. **Processing Stage**: Content enrichment (hierarchy, metadata, quality)
4. **Formatting Stage**: Output generation (JSON, Markdown, etc.)

**Key Principles**:
- **Immutability**: Each stage creates new data structures (no mutations)
- **Composability**: Components are independent and composable
- **Error Isolation**: Errors in one stage don't corrupt others
- **Progressive Enhancement**: Each stage adds value to previous stage's output

## Pipeline State Machine

```
┌──────────────┐
│ VALIDATION   │  Check file exists, detect format, verify extractor
└──────┬───────┘
       │ ✓ File valid
       ▼
┌──────────────┐
│ EXTRACTION   │  Extract content blocks from document
└──────┬───────┘
       │ ✓ ExtractionResult
       ▼
┌──────────────┐
│ PROCESSING   │  Enrich content blocks (hierarchy, metadata, quality)
│              │  → ContextLinker (build hierarchy)
│              │  → MetadataAggregator (compute statistics)
│              │  → QualityValidator (score quality)
│              │  **→ SemanticAnalyzer** ← INTEGRATION POINT
└──────┬───────┘
       │ ✓ ProcessingResult
       ▼
┌──────────────┐
│ FORMATTING   │  Generate output formats (parallel execution)
│              │  → JsonFormatter
│              │  → MarkdownFormatter
│              │  → ChunkedTextFormatter
│              │  **→ RagOptimizedFormatter** ← INTEGRATION POINT
└──────┬───────┘
       │ ✓ FormattedOutput[]
       ▼
┌──────────────┐
│   COMPLETE   │  Return PipelineResult
└──────────────┘
```

---

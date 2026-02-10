# JSON Schema Reference – JsonFormatter (Story 3.4)

This document describes the canonical JSON output produced by `JsonFormatter` (`src/data_extract/output/formatters/json_formatter.py`) and enforced by the Draft 7 schema stored at `src/data_extract/output/schemas/data-extract-chunk.schema.json`.

## Overview

- **Root object** – A single JSON document (not JSON Lines) with two keys:
  - `metadata`: document-level processing information.
  - `chunks`: array of serialized `Chunk` objects with embedded metadata, entities, and quality scores.
- **Validation** – `jsonschema` Draft 7. Unit + integration suites (`tests/unit/test_output/test_json_schema.py`, `tests/integration/test_output/test_json_output_pipeline.py`) verify compliance.
- **Encoding** – UTF-8 (pretty-printed with 2-space indentation). Paths and datetimes are serialized as strings (ISO 8601).

## Root Structure

| Field | Type | Description |
|-------|------|-------------|
| `metadata` | object | See table below. Captures versioning, configuration, provenance. |
| `chunks` | array\<Chunk\> | Ordered list of enriched chunks; each entry follows the schema described later. Minimum length: 0. |

## Metadata Object

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `processing_version` | string (semver) | ✅ | Tool version, e.g., `1.0.0-epic3`. Regex `^[0-9]+\.[0-9]+\.[0-9]+(-.+)?$`. |
| `processing_timestamp` | string (ISO 8601) | ✅ | UTC timestamp such as `2025-11-15T04:30:56Z`. |
| `configuration` | object | ✅ | Chunking parameters – see below. |
| `source_documents` | array\<string\> | ✅ | Absolute/relative paths of processed files (deduplicated). |
| `chunk_count` | integer ≥ 0 | ✅ | Total chunks written to `chunks`. |

**Configuration Object**

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `chunk_size` | integer | 128–2048 | Target chunk size in tokens. |
| `overlap_pct` | number | 0.0–0.5 | Overlap percentage (fractional). |
| `entity_aware` | boolean | — | Whether entity-aware chunking was active. |
| `quality_enrichment` | boolean | — | Whether quality scoring was active. |

## Chunk Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chunk_id` | string (^[A-Za-z0-9_-]+$) | ✅ | Stable identifier (`{source}_{index:03d}`). |
| `text` | string, minLength 1 | ✅ | Chunk content. |
| `metadata` | ChunkMetadata | ✅ | See table below. |
| `entities` | array\<EntityReference\> | ✅ | Derived entity references (may be empty). |
| `quality` | QualityScore | ✅ | Composite quality metrics. |

## ChunkMetadata Object

| Field | Type | Notes |
|-------|------|-------|
| `entity_tags` | array\<EntityReference\> | Entities preserved within the chunk. |
| `section_context` | string | Breadcrumb describing document section. |
| `entity_relationships` | array\<array\<str\>\> | Triples `(entity1_id, relation_type, entity2_id)`. |
| `source_metadata` | object \| null | Raw Metadata snapshot (optional). |
| `quality` | QualityScore \| null | Nested quality metrics; may be null if enrichment disabled. |
| `source_hash` | string \| null | 12–64 hex characters (SHA-256 or truncated). |
| `document_type` | string \| null | Enum: `pdf`, `docx`, `xlsx`, `pptx`, `csv`, `image`, `report`, `matrix`, `export`. |
| `word_count` | integer ≥ 0 | Chunk word count. |
| `token_count` | integer ≥ 0 | Estimated token count. |
| `created_at` | string (date-time) \| null | ISO 8601 timestamp of chunk enrichment. |
| `processing_version` | string | Tool version used for enrichment. |

## QualityScore Object

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `readability_flesch_kincaid` | number | 0.0–30.0 | FK Grade Level. |
| `readability_gunning_fog` | number | 0.0–30.0 | Gunning Fog Index. |
| `ocr_confidence` | number | 0.0–1.0 | OCR confidence propagated from normalization stage. |
| `completeness` | number | 0.0–1.0 | Entity preservation/completeness score. |
| `coherence` | number | 0.0–1.0 | Lexical overlap indicator. |
| `overall` | number | 0.0–1.0 | Weighted composite. |
| `flags` | array\<string\> | Enum values: `low_ocr`, `incomplete_extraction`, `high_complexity`, `gibberish`. |

## EntityReference Object

| Field | Type | Description |
|-------|------|-------------|
| `entity_type` | string | Enum: `risk`, `control`, `policy`, `process`, `regulation`, `issue`. |
| `entity_id` | string | Canonical identifier (`RISK-001`, etc.). |
| `start_pos` | integer ≥ 0 | Start offset (characters). |
| `end_pos` | integer ≥ 0 | End offset (characters). |
| `is_partial` | boolean | True if chunk split the entity. |
| `context_snippet` | string | ±20 chars around entity mention. |

## Example (Truncated)

```json
{
  "metadata": {
    "processing_version": "1.0.0-epic3",
    "processing_timestamp": "2025-11-15T04:30:56Z",
    "configuration": {"chunk_size": 512, "overlap_pct": 0.15, "entity_aware": false, "quality_enrichment": true},
    "source_documents": ["docs/input/test_document.txt"],
    "chunk_count": 1
  },
  "chunks": [
    {
      "chunk_id": "test_document_chunk_000",
      "text": "Introduction...",
      "metadata": {
        "entity_tags": [],
        "section_context": "Introduction",
        "entity_relationships": [],
        "source_metadata": null,
        "quality": {
          "readability_flesch_kincaid": 8.5,
          "readability_gunning_fog": 10.2,
          "ocr_confidence": 0.99,
          "completeness": 0.95,
          "coherence": 0.88,
          "overall": 0.93,
          "flags": []
        },
        "source_hash": null,
        "document_type": "report",
        "word_count": 150,
        "token_count": 200,
        "created_at": "2025-11-15T04:30:56Z",
        "processing_version": "1.0.0-epic3"
      },
      "entities": [],
      "quality": {
        "readability_flesch_kincaid": 8.5,
        "readability_gunning_fog": 10.2,
        "ocr_confidence": 0.99,
        "completeness": 0.95,
        "coherence": 0.88,
        "overall": 0.93,
        "flags": []
      }
    }
  ]
}
```

## Validation Workflow

1. **Unit tests** – `pytest tests/unit/test_output/test_json_schema.py tests/unit/test_output/test_json_formatter.py`
2. **Integration tests** – `pytest tests/integration/test_output/test_json_output_pipeline.py tests/integration/test_output/test_json_compatibility.py`
3. **Performance tests** – `pytest tests/performance/test_json_performance.py`
4. **Manual checks** – Inspect pretty-printed JSON output in `output/` (ensure indentation, ordering).

When the schema changes, update:
- `src/data_extract/output/schemas/data-extract-chunk.schema.json`
- This reference file (field definitions, enums, example)
- Schema validation tests (unit + integration)
- Downstream consumers (docs, SDKs) as needed.

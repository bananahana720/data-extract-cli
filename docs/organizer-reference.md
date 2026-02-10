# Output Organization Reference

**Story**: 3.7 - Configurable Output Organization Strategies
**Status**: Complete
**Version**: 1.0
**Last Updated**: 2025-11-16

## Overview

The Organizer coordinates output file placement across multiple formats (JSON, TXT, CSV) using configurable organization strategies. It supports three layout modes (BY_DOCUMENT, BY_ENTITY, FLAT) and generates comprehensive manifests for traceability and audit compliance.

## Organization Strategies

### BY_DOCUMENT Strategy

**Purpose:** Group all outputs by source document

**Use Cases:**
- Preserving document-level context
- Parallel processing of independent documents
- Document-specific quality analysis
- Audit workflows requiring per-document deliverables

**Structure:**
```
output/
├── audit_report/
│   ├── chunks.json         ← JSON format
│   ├── chunks.txt          ← TXT format
│   ├── chunks.csv          ← CSV format
│   └── manifest.json       ← Traceability metadata
├── risk_matrix/
│   ├── chunks.json
│   ├── chunks.txt
│   ├── chunks.csv
│   └── manifest.json
└── compliance_policy/
    ├── chunks.json
    ├── chunks.txt
    ├── chunks.csv
    └── manifest.json
```

**Folder Naming:**
- Derived from source filename (stem only, no extension)
- Special characters sanitized: `Risk Matrix (2024).pdf` → `risk_matrix_2024/`
- Collision handling: Append suffix if folder exists (`audit_report_2/`)

**Manifest Content:**
```json
{
  "organization_strategy": "by_document",
  "generated_at": "2025-11-16T10:30:45Z",
  "config_snapshot": {
    "chunk_size": 512,
    "overlap_pct": 0.15,
    "entity_aware": true
  },
  "total_chunks": 42,
  "folders": {
    "audit_report": {
      "chunk_count": 42,
      "chunk_ids": ["audit_report_001", "audit_report_002", ...]
    }
  },
  "source_hashes": {
    "audit_report.pdf": "a3f5e8c2d1b9..."
  },
  "entity_summary": {
    "total_entities": 18,
    "entity_types": {
      "RISK": 7,
      "CTRL": 9,
      "PROC": 2
    },
    "unique_entity_ids": ["RISK-001", "RISK-023", "CTRL-042", ...]
  },
  "quality_summary": {
    "avg_quality_score": 0.94,
    "min_quality_score": 0.78,
    "max_quality_score": 0.99,
    "chunks_with_quality": 42,
    "quality_flags": {
      "low_ocr": 1,
      "high_complexity": 3
    }
  }
}
```

### BY_ENTITY Strategy

**Purpose:** Group outputs by entity type (risks, controls, processes, etc.)

**Use Cases:**
- Entity-specific analysis workflows
- Cross-document entity aggregation
- Compliance reporting by entity category
- Targeted retrieval for specific entity types

**Structure:**
```
output/
├── risks/
│   ├── chunks.json         ← All RISK entity chunks
│   ├── chunks.txt
│   ├── chunks.csv
│   └── manifest.json
├── controls/
│   ├── chunks.json         ← All CTRL entity chunks
│   ├── chunks.txt
│   ├── chunks.csv
│   └── manifest.json
├── processes/
│   ├── chunks.json         ← All PROC entity chunks
│   ├── chunks.txt
│   ├── chunks.csv
│   └── manifest.json
└── unclassified/
    ├── chunks.json         ← Chunks with no entity tags
    ├── chunks.txt
    ├── chunks.csv
    └── manifest.json
```

**Entity Type Mapping:**

| Entity Pattern | Folder Name | Description |
|----------------|-------------|-------------|
| `RISK-*` | `risks/` | Risk entities |
| `CTRL-*` | `controls/` | Control entities |
| `PROC-*` | `processes/` | Process entities |
| `REG-*` | `regulations/` | Regulation entities |
| `POL-*` | `policies/` | Policy entities |
| `ISSUE-*` | `issues/` | Issue entities |
| (none) | `unclassified/` | Chunks without entity tags |

**Multi-Entity Chunks:**
- Chunks with multiple entity types assigned to **primary entity** (first tag)
- Example: `["RISK-001", "CTRL-042"]` → placed in `risks/` folder
- Traceability preserved in manifest cross-reference

**Manifest Content:**
```json
{
  "organization_strategy": "by_entity",
  "generated_at": "2025-11-16T10:35:22Z",
  "total_chunks": 156,
  "folders": {
    "risks": {
      "chunk_count": 47,
      "chunk_ids": ["audit_report_003", "risk_matrix_012", ...]
    },
    "controls": {
      "chunk_count": 83,
      "chunk_ids": ["audit_report_007", "compliance_policy_005", ...]
    },
    "processes": {
      "chunk_count": 14,
      "chunk_ids": ["process_doc_001", ...]
    },
    "unclassified": {
      "chunk_count": 12,
      "chunk_ids": ["intro_001", "summary_042", ...]
    }
  },
  "source_hashes": {
    "audit_report.pdf": "a3f5e8c2...",
    "risk_matrix.xlsx": "b9d7c1a5...",
    "compliance_policy.docx": "e2f8a3c9..."
  }
}
```

### FLAT Strategy

**Purpose:** Place all outputs in single directory with prefixed filenames

**Use Cases:**
- Simple batch processing
- Legacy system integration (single-folder requirement)
- Quick exploratory analysis
- Minimal folder structure preference

**Structure:**
```
output/
├── audit_report_001.json
├── audit_report_001.txt
├── audit_report_001.csv
├── risk_matrix_002.json
├── risk_matrix_002.txt
├── risk_matrix_002.csv
├── compliance_policy_003.json
├── compliance_policy_003.txt
├── compliance_policy_003.csv
└── manifest.json           ← Single manifest for all files
```

**Filename Pattern:**
- `{source_stem}_{chunk_id}.{extension}`
- Example: `audit_report_001.json`, `risk_matrix_042.csv`
- Guaranteed uniqueness via chunk_id

**Manifest Content:**
```json
{
  "organization_strategy": "flat",
  "generated_at": "2025-11-16T10:40:15Z",
  "total_chunks": 156,
  "folders": {
    ".": {
      "chunk_count": 156,
      "chunk_ids": ["audit_report_001", "audit_report_002", ...]
    }
  },
  "source_hashes": {
    "audit_report.pdf": "a3f5e8c2...",
    "risk_matrix.xlsx": "b9d7c1a5...",
    "compliance_policy.docx": "e2f8a3c9..."
  }
}
```

## Programmatic API

### Organizer Class

```python
from data_extract.output.organization import Organizer, OrganizationStrategy
from pathlib import Path

# Initialize organizer
organizer = Organizer()

# Organize chunks with BY_DOCUMENT strategy
result = organizer.organize(
    chunks=my_chunks,
    output_dir=Path("output/"),
    strategy=OrganizationStrategy.BY_DOCUMENT,
    config_snapshot={"chunk_size": 512, "overlap_pct": 0.15}
)

# Access result
print(f"Organized {result.total_chunks} chunks")
print(f"Folders created: {list(result.folder_map.keys())}")
print(f"Manifest path: {result.manifest_path}")
```

### OutputWriter Integration (Recommended)

```python
from data_extract.output.writer import OutputWriter
from data_extract.output.organization import OrganizationStrategy

writer = OutputWriter()

# Organized output with multiple formats
result = writer.write(
    chunks=my_chunks,
    output_path=Path("output/"),
    format_type="json",  # or "txt", "csv"
    organize=True,
    strategy=OrganizationStrategy.BY_DOCUMENT,
    config_snapshot={"chunk_size": 512},
    validate=True
)
```

## CLI Usage

### Basic Organization

```bash
# BY_DOCUMENT organization
data-extract process input.pdf --format json --output output/ \
  --organize --strategy by_document

# BY_ENTITY organization
data-extract process input.pdf --format csv --output output/ \
  --organize --strategy by_entity

# FLAT organization
data-extract process input.pdf --format txt --output output/ \
  --organize --strategy flat
```

### Multi-Format Output

```bash
# Generate all three formats with BY_DOCUMENT organization
for format in json txt csv; do
  data-extract process input.pdf --format $format --output output/ \
    --organize --strategy by_document
done
```

### Environment Variable Configuration

```bash
# Set default organization strategy
export DATA_EXTRACT_ORGANIZATION_STRATEGY=by_document

# Run without --strategy flag (uses env var)
data-extract process input.pdf --format json --output output/ --organize
```

## Manifest Schema

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `organization_strategy` | string | ✅ | One of: `by_document`, `by_entity`, `flat` |
| `generated_at` | string (ISO 8601) | ✅ | Timestamp of manifest generation |
| `config_snapshot` | object | ✅ | Chunking/formatter configuration |
| `total_chunks` | integer | ✅ | Total chunks organized |
| `folders` | object | ✅ | Folder → chunk mapping |
| `source_hashes` | object | ✅ | Source file → SHA-256 hash |
| `entity_summary` | object | ✅ | Entity statistics and counts |
| `quality_summary` | object | ✅ | Quality score aggregations |

### Config Snapshot Object

Preserves chunking and formatter configuration for reproducibility:

```json
{
  "chunk_size": 512,
  "overlap_pct": 0.15,
  "entity_aware": true,
  "quality_enrichment": true,
  "max_text_length": null,
  "include_metadata": false,
  "delimiter": "━━━ CHUNK {{n}} ━━━"
}
```

### Entity Summary Object

```json
{
  "total_entities": 42,
  "entity_types": {
    "RISK": 15,
    "CTRL": 20,
    "PROC": 7
  },
  "unique_entity_ids": [
    "RISK-001",
    "RISK-023",
    "CTRL-042",
    "PROC-105"
  ]
}
```

### Quality Summary Object

```json
{
  "avg_quality_score": 0.94,
  "min_quality_score": 0.78,
  "max_quality_score": 0.99,
  "chunks_with_quality": 156,
  "quality_flags": {
    "low_ocr": 3,
    "incomplete_extraction": 1,
    "high_complexity": 7
  }
}
```

## Logging & Audit Trail

### Structured Logging

The Organizer emits structured logs (via structlog) for all operations:

**Organization Start:**
```json
{
  "event": "organization_start",
  "timestamp": "2025-11-16T10:30:45Z",
  "strategy": "by_document",
  "output_dir": "/path/to/output",
  "chunk_count": 156
}
```

**Folder Creation:**
```json
{
  "event": "folder_created",
  "timestamp": "2025-11-16T10:30:46Z",
  "folder": "audit_report",
  "chunk_count": 42
}
```

**Manifest Generation:**
```json
{
  "event": "manifest_generated",
  "timestamp": "2025-11-16T10:30:47Z",
  "manifest_path": "/path/to/output/manifest.json",
  "total_chunks": 156,
  "folder_count": 3
}
```

**Organization Complete:**
```json
{
  "event": "organization_complete",
  "timestamp": "2025-11-16T10:30:48Z",
  "duration_ms": 1250,
  "files_written": 468,
  "strategy": "by_document"
}
```

### Log Configuration

```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

# Enable organization logging
from data_extract.output.organization import Organizer
organizer = Organizer()  # Logging enabled by default
```

## Performance Characteristics

Based on integration tests and performance profiling:

- **Folder creation:** <1ms per folder (OS-dependent)
- **Manifest generation:** <10ms for 1000 chunks
- **Organization overhead:** <50ms total for typical batches (10-100 chunks)
- **Memory:** Constant ~5MB (independent of chunk count)
- **Determinism:** Same chunks + strategy → identical folder structure

## Error Handling & Edge Cases

### Path Sanitization

**Special Characters:**
- Spaces → underscores: `Risk Matrix.pdf` → `risk_matrix/`
- Parentheses removed: `Report (2024).pdf` → `report_2024/`
- Unicode preserved: `Política de Riesgo.pdf` → `política_de_riesgo/`

**Collision Handling:**
- Append numeric suffix: `audit_report/`, `audit_report_2/`, `audit_report_3/`
- Guaranteed uniqueness within output directory

### Entity Type Fallback

**Unknown Entity Patterns:**
- Unrecognized prefixes → `unclassified/` folder
- Example: `CUSTOM-042` → `unclassified/` (unless explicitly mapped)

**Empty Entity Tags:**
- Chunks with `entity_tags=[]` → `unclassified/` folder

### Continue-On-Error Behavior (ADR-006)

**Per-Chunk Errors:**
- Malformed metadata → skip chunk, log warning, continue processing
- Invalid entity tags → place in `unclassified/`, log warning
- Missing source file → use placeholder hash, continue

**Batch Resilience:**
- One chunk failure does **not** block entire batch
- Partial results written to manifest with error annotations

## Integration with Formatters

### JSON Formatter

```python
# Organized JSON output
writer.write(
    chunks=chunks,
    output_path=Path("output/"),
    format_type="json",
    organize=True,
    strategy=OrganizationStrategy.BY_DOCUMENT,
    validate=True  # JSON-specific kwarg
)
```

### TXT Formatter

```python
# Organized TXT output with metadata
writer.write(
    chunks=chunks,
    output_path=Path("output/"),
    format_type="txt",
    organize=True,
    strategy=OrganizationStrategy.BY_ENTITY,
    include_metadata=True,  # TXT-specific kwarg
    delimiter="--- CHUNK {{n}} ---"
)
```

### CSV Formatter

```python
# Organized CSV output with truncation
writer.write(
    chunks=chunks,
    output_path=Path("output/"),
    format_type="csv",
    organize=True,
    strategy=OrganizationStrategy.FLAT,
    max_text_length=500,  # CSV-specific kwarg
    validate=True
)
```

## Best Practices

### Strategy Selection

| Use Case | Recommended Strategy | Rationale |
|----------|---------------------|-----------|
| Document-specific analysis | BY_DOCUMENT | Preserves document context |
| Entity-focused retrieval | BY_ENTITY | Optimizes entity aggregation |
| Simple batch processing | FLAT | Minimal folder complexity |
| Multi-document RAG corpus | BY_DOCUMENT or BY_ENTITY | Depends on retrieval pattern |
| Audit trail requirements | BY_DOCUMENT | Document-level traceability |

### Manifest Usage

1. **Reproducibility:** Store `config_snapshot` with outputs for exact reproduction
2. **Traceability:** Use `source_hashes` to verify source file integrity
3. **Quality Monitoring:** Track `quality_summary` trends across batches
4. **Entity Analysis:** Leverage `entity_summary` for cross-document entity counts

### Performance Optimization

1. **Batch Size:** Organize 10-100 documents per batch (optimal folder count)
2. **Parallel Processing:** Organize independent batches in parallel
3. **Validation:** Disable formatter validation (`validate=False`) for trusted pipelines
4. **Logging:** Set log level to WARNING for production (reduce I/O overhead)

## Limitations & Future Enhancements

### Current Limitations

1. **Single manifest:** One manifest per output directory (not per-folder manifests)
2. **Entity mapping:** Fixed entity type → folder mapping (not user-configurable)
3. **Folder depth:** Single-level folders only (no nested hierarchies)
4. **Cross-references:** Multi-entity chunks placed in single folder (no duplicates)

### Future Enhancements (Epic 5+)

1. **Custom entity mappings:** User-defined entity type → folder mappings
2. **Hierarchical organization:** Nested folders (e.g., `risks/high/`, `risks/medium/`)
3. **Per-folder manifests:** Individual manifests for each organized folder
4. **Symlink support:** Multi-entity chunks visible in multiple folders (Linux/macOS)
5. **Incremental organization:** Append to existing organized output (batch updates)

## Related Documentation

- **CSV Format:** See `docs/csv-format-reference.md`
- **JSON Format:** See `docs/json-schema-reference.md`
- **TXT Format:** See `docs/txt-format-reference.md`
- **Performance:** See `docs/performance-baselines-epic-3.md`
- **Architecture:** See `docs/architecture/architecture-decision-records-adrs.md` (ADR-005, ADR-006)

## Testing

- **Unit Tests:** `tests/unit/test_output/test_organization.py`
- **Integration Tests:** `tests/integration/test_output/test_by_entity_organization.py`, `test_csv_organization.py`, `test_manifest_validation.py`
- **Performance Tests:** `tests/performance/test_organization_performance.py`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-16 | Initial release (Story 3.7) with BY_DOCUMENT, BY_ENTITY, FLAT strategies and comprehensive manifest generation |

---

**Maintainers:** Data Extraction Tool Team
**Contact:** See project README for support channels

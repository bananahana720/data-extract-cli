# CSV Output Format Reference

**Story**: 3.6 - CSV Output Format for Analysis and Tracking
**Status**: Complete
**Version**: 1.0
**Last Updated**: 2025-11-16

## Overview

The CsvFormatter produces RFC 4180 compliant CSV output optimized for spreadsheet analysis (Excel, Google Sheets) and programmatic processing (pandas, csvkit). Output includes comprehensive chunk metadata with configurable text truncation for readability.

## Output Structure

### CSV Schema (10 Columns)

The canonical CSV schema includes these columns in order:

| Column | Type | Description |
|--------|------|-------------|
| `chunk_id` | string | Stable chunk identifier (e.g., `audit_report_001`) |
| `source_file` | string | Source document path (relative or absolute) |
| `section_context` | string | Document section breadcrumb (e.g., `Introduction > Risk Overview`) |
| `chunk_text` | string | Full chunk content (truncated if configured) |
| `entity_tags` | string | Semicolon-delimited entity list (e.g., `RISK-001;CTRL-042;PROC-123`) |
| `quality_score` | float | Overall quality score (0.0-1.0) |
| `word_count` | integer | Chunk word count |
| `token_count` | integer | Estimated token count |
| `processing_version` | string | Tool version (e.g., `1.0.0-epic3`) |
| `warnings` | string | Semicolon-delimited warning flags (e.g., `low_ocr;incomplete_extraction`) |

### Example Output

```csv
chunk_id,source_file,section_context,chunk_text,entity_tags,quality_score,word_count,token_count,processing_version,warnings
audit_report_001,audit_report.pdf,"Introduction > Risk Overview","This document summarizes the key compliance risks identified...",RISK-001;RISK-023,0.96,42,56,1.0.0-epic3,
audit_report_002,audit_report.pdf,"Section 2 > Control Framework","The control framework consists of...",CTRL-042;CTRL-105,0.92,38,51,1.0.0-epic3,
audit_report_003,audit_report.pdf,"Section 3 > Findings","Critical finding: OCR confidence low in this section...",ISSUE-007,0.78,29,39,1.0.0-epic3,low_ocr
```

## Configuration Options

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_text_length` | `int \| None` | `None` | Maximum characters for chunk_text (None = unlimited) |
| `validate` | `bool` | `True` | Enable multi-engine CSV validation (Python csv + pandas + csvkit) |

### Usage Examples

```python
# Default configuration (unlimited text, validation enabled)
formatter = CsvFormatter()

# Enable text truncation for spreadsheet readability
formatter = CsvFormatter(max_text_length=200)

# Disable validation for high-throughput production
formatter = CsvFormatter(validate=False)

# Both options
formatter = CsvFormatter(max_text_length=500, validate=True)
```

## Data Encoding & Escaping

### RFC 4180 Compliance

The CsvFormatter strictly follows RFC 4180 for maximum compatibility:

- **Delimiter:** Comma (`,`)
- **Quote Character:** Double quote (`"`)
- **Escape Sequence:** Double double-quote (`""`) for embedded quotes
- **Line Endings:** `\r\n` (CRLF) per RFC 4180
- **Encoding:** UTF-8-sig (with BOM for Windows Excel compatibility)

### Special Character Handling

| Content Type | Encoding Example |
|-------------|------------------|
| **Embedded commas** | `"Smith, John"` → quoted field |
| **Embedded quotes** | `She said "hello"` → `"She said ""hello"""` |
| **Embedded newlines** | `Line1\nLine2` → `"Line1\nLine2"` (quoted) |
| **Empty fields** | Empty string → `,` (unquoted) |
| **Null values** | `None` → `` (empty string, not "None") |
| **Semicolons** | Entity/warning delimiters → `RISK-001;CTRL-042` |

### Text Truncation

When `max_text_length` is set, long chunk text is truncated with ellipsis:

```
Original (250 chars): "This is a very long chunk of text that exceeds the configured maximum length and will be truncated to fit within the specified character limit while preserving readability and indicating truncation with an ellipsis marker..."

Truncated (200 chars): "This is a very long chunk of text that exceeds the configured maximum length and will be truncated to fit within the specified character limit while preserving readability and indicating trun..."
```

**Notes:**
- Truncation applied **only** to `chunk_text` column
- All other columns preserved at full length
- Ellipsis (`...`) NOT added (clean truncation for post-processing)

## Validation

### Multi-Engine Validation (When `validate=True`)

The CsvFormatter uses CsvParserValidator to validate output with three independent engines:

| Engine | Validation | Catches |
|--------|-----------|---------|
| **Python csv module** | Dialect detection, quote escaping, line parsing | Malformed CSV, encoding issues, delimiter problems |
| **pandas** | DataFrame loading, type inference | Column misalignment, data type issues, corrupt rows |
| **csvkit (csvstat)** | Field statistics, null detection | Empty columns, unexpected nulls, schema violations |

**Performance Impact:**
- Validation adds ~50-100ms overhead for typical documents (10-100 chunks)
- Recommended for development/testing, optional for production

**Failure Behavior:**
- Validation errors raise `ValueError` with detailed diagnostic message
- Invalid CSV is **not written** to disk (fail-fast behavior)
- Set `validate=False` to disable validation for trusted pipelines

### Manual Validation

For offline validation of existing CSV files:

```python
from data_extract.output.validation import CsvParserValidator

validator = CsvParserValidator()
validator.validate_csv(Path("output.csv"))  # Raises ValueError if invalid
```

## Integration with Organization Strategies

### BY_DOCUMENT Organization

```
output/
├── audit_report/
│   ├── chunks.csv          ← CSV output for this document
│   ├── chunks.json
│   ├── chunks.txt
│   └── manifest.json
└── risk_matrix/
    ├── chunks.csv
    ├── chunks.json
    ├── chunks.txt
    └── manifest.json
```

### BY_ENTITY Organization

```
output/
├── risks/
│   ├── chunks.csv          ← CSV with RISK entities
│   ├── chunks.json
│   ├── chunks.txt
│   └── manifest.json
├── controls/
│   ├── chunks.csv          ← CSV with CTRL entities
│   ├── chunks.json
│   ├── chunks.txt
│   └── manifest.json
└── unclassified/
    └── chunks.csv          ← CSV with no entity tags
```

### FLAT Organization

```
output/
├── audit_report_001.csv
├── risk_matrix_002.csv
├── combined_chunks.csv     ← Optional concatenated output
└── manifest.json           ← Traceability for all files
```

## Programmatic Usage

### Basic Formatting

```python
from data_extract.output.formatters import CsvFormatter
from pathlib import Path

# Create formatter
formatter = CsvFormatter()

# Format chunks
result = formatter.format_chunks(chunks, Path("output.csv"))

# Check result
print(f"Wrote {result.chunks_written} chunks")
print(f"Output: {result.output_path}")
```

### With OutputWriter (Recommended)

```python
from data_extract.output.writer import OutputWriter
from data_extract.output.organization import OrganizationStrategy

writer = OutputWriter()

# CSV output with BY_DOCUMENT organization
result = writer.write(
    chunks=my_chunks,
    output_path=Path("output/"),
    format_type="csv",
    organize=True,
    strategy=OrganizationStrategy.BY_DOCUMENT,
    max_text_length=500,  # Formatter-specific kwargs
    validate=True
)
```

### CLI Usage

```bash
# Basic CSV output
data-extract process input.pdf --format csv --output output.csv

# With organization strategy
data-extract process input.pdf --format csv --output output/ \
  --organize --strategy by_document

# Custom text truncation (via config file or future CLI extension)
# Note: max_text_length currently configurable only via Python API
```

## Performance Characteristics

Based on `tests/performance/test_csv_performance.py`:

- **Small documents (10 chunks):** ~0.01s (100x faster than target)
- **Large documents (100 chunks):** ~0.05s (20x faster than target)
- **Memory:** Constant ~5MB peak (independent of batch size)
- **Determinism:** Same input → byte-identical output

## Downstream Consumer Integration

### Excel / Google Sheets

**Import Steps:**
1. Open Excel/Sheets
2. File → Import → CSV
3. **Encoding:** UTF-8 (BOM auto-detected by Excel)
4. **Delimiter:** Comma
5. **Text Qualifier:** Double quote

**Known Issues:**
- Long text fields may be truncated in cell display (use text wrapping or adjust column width)
- Entity tags display as raw semicolon-delimited strings (consider post-processing or pivot tables)

### pandas

```python
import pandas as pd

# Load CSV
df = pd.read_csv("output.csv")

# Access columns
print(df["chunk_text"].head())
print(df["entity_tags"].unique())

# Filter by quality score
high_quality = df[df["quality_score"] > 0.9]

# Normalize entity tags (split semicolons)
df["entities"] = df["entity_tags"].str.split(";")
```

### csvkit

```bash
# Display statistics
csvstat output.csv

# Preview with column alignment
csvlook output.csv | head -20

# Filter high-quality chunks
csvgrep -c quality_score -r "0\.[89].*" output.csv > high_quality.csv

# Convert to JSON
csvjson output.csv > output.json
```

## Limitations & Considerations

### Current Limitations

1. **No JSON Lines support:** Single CSV file output only (multi-file support via organization strategies)
2. **Entity tag format:** Semicolon-delimited strings (not structured arrays)
3. **Quality flags:** Semicolon-delimited strings (not separate columns)
4. **max_text_length:** Python API only (not yet exposed in CLI)

### Future Enhancements (Epic 5+)

1. **Configurable delimiters:** Support TSV, pipe-delimited, or custom separators
2. **Wide format option:** Expand entity tags into separate columns (RISK-001, RISK-002, ...)
3. **Streaming writes:** Handle extremely large chunk sets (>10k chunks) without memory materialization
4. **CLI truncation flag:** Expose `--max-text-length` in CLI for quick truncation

## Related Documentation

- **JSON Format:** See `docs/json-schema-reference.md`
- **TXT Format:** See `docs/txt-format-reference.md`
- **Organization:** See `docs/organizer-reference.md`
- **Performance:** See `docs/performance-baselines-epic-3.md`
- **Testing:** See `tests/unit/test_output/test_csv_formatter.py`, `tests/integration/test_output/test_csv_pipeline.py`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-16 | Initial release (Story 3.6) with 10-column schema, RFC 4180 compliance, multi-engine validation |

---

**Maintainers:** Data Extraction Tool Team
**Contact:** See project README for support channels

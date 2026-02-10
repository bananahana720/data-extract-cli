# CsvFormatter Sample Outputs

This directory contains sample CSV outputs demonstrating the CSV formatter capabilities.

## Files

| File | Description | Features |
|------|-------------|----------|
| `sample-basic.csv` | Basic CSV output | Full 10-column schema, no truncation, validation enabled |
| `sample-truncated.csv` | Truncated text output | 200-character text limit for spreadsheet readability |
| `sample-organized-by-document.csv` | Organized by document | BY_DOCUMENT strategy with manifest |
| `sample-organized-by-entity.csv` | Organized by entity | BY_ENTITY strategy (risks folder example) |

## How These Were Generated

```python
from data_extract.output.formatters import CsvFormatter
from data_extract.output.writer import OutputWriter
from data_extract.output.organization import OrganizationStrategy
from pathlib import Path

# sample-basic.csv
formatter = CsvFormatter()
result = formatter.format_chunks(chunks, Path("sample-basic.csv"))

# sample-truncated.csv
formatter = CsvFormatter(max_text_length=200)
result = formatter.format_chunks(chunks, Path("sample-truncated.csv"))

# sample-organized-by-document.csv
writer = OutputWriter()
result = writer.write(
    chunks=chunks,
    output_path=Path("output/"),
    format_type="csv",
    organize=True,
    strategy=OrganizationStrategy.BY_DOCUMENT
)

# sample-organized-by-entity.csv
writer = OutputWriter()
result = writer.write(
    chunks=chunks,
    output_path=Path("output/"),
    format_type="csv",
    organize=True,
    strategy=OrganizationStrategy.BY_ENTITY
)
```

## CSV Schema

All samples follow the canonical 10-column schema:

1. `chunk_id` - Stable chunk identifier
2. `source_file` - Source document path
3. `section_context` - Document section breadcrumb
4. `chunk_text` - Chunk content (truncated if configured)
5. `entity_tags` - Semicolon-delimited entity list
6. `quality_score` - Overall quality score (0.0-1.0)
7. `word_count` - Chunk word count
8. `token_count` - Estimated token count
9. `processing_version` - Tool version
10. `warnings` - Semicolon-delimited warning flags

## Validation

All samples have been validated for:
- ✅ RFC 4180 compliance (Python csv module)
- ✅ UTF-8-sig encoding with BOM (Excel compatibility)
- ✅ pandas DataFrame loading (no data loss)
- ✅ csvkit validation (csvstat, csvlook)
- ✅ Proper escaping (commas, quotes, newlines)
- ✅ Excel/Google Sheets import (manual UAT)

## Usage

### Excel

1. Open Excel
2. Data → From Text/CSV → Select sample file
3. Encoding: UTF-8 (auto-detected via BOM)
4. Delimiter: Comma
5. Import and analyze

### Google Sheets

1. File → Import → Upload → Select sample file
2. Import location: Replace current sheet
3. Separator type: Comma
4. Convert text to numbers: Off
5. Import and analyze

### pandas

```python
import pandas as pd

# Load CSV
df = pd.read_csv("sample-basic.csv")

# Display summary
print(df.info())
print(df.describe())

# Filter by quality
high_quality = df[df["quality_score"] > 0.9]
print(f"High quality chunks: {len(high_quality)}")
```

### csvkit

```bash
# Display statistics
csvstat sample-basic.csv

# Preview with column alignment
csvlook sample-basic.csv | head -20

# Filter by quality score
csvgrep -c quality_score -r "0\.[89].*" sample-basic.csv > high_quality.csv
```

## Organization Examples

See `docs/examples/manifest-samples/` for corresponding manifest.json files demonstrating traceability metadata for organized outputs.

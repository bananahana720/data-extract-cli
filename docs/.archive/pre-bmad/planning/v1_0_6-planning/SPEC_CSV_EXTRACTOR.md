# CSV Extractor Technical Specification

## 1. Overview

**Feature**: CSV Extractor
**Version**: v1.0.6
**Priority**: HIGH
**Type**: New extractor component

Implements extraction of CSV/TSV files into ContentBlock structures following the single TABLE ContentBlock pattern established by the Excel extractor.

## 2. Requirements

### 2.1 Functional Requirements

- Extract CSV files (.csv) into structured ContentBlock format
- Extract TSV files (.tsv) into structured ContentBlock format
- Auto-detect CSV delimiter (comma, semicolon, tab, pipe)
- Auto-detect file encoding (UTF-8, Latin-1, CP1252)
- Auto-detect presence of header row
- Support configuration overrides for delimiter, encoding, header
- Generate TableMetadata with full grid structure
- Preserve empty cells and whitespace
- Handle quoted and escaped fields

### 2.2 File Format Support

| Format | Extension | Delimiter | Support Level |
|--------|-----------|-----------|---------------|
| CSV | .csv | comma | Primary |
| TSV | .tsv | tab | Primary |
| CSV (semicolon) | .csv | semicolon | Auto-detect |
| CSV (pipe) | .csv | pipe | Auto-detect |

### 2.3 Non-Functional Requirements

- **Performance**: Extract 1K rows in <1s
- **Memory**: Use <50MB for 10K rows
- **Accuracy**:
  - Delimiter detection ≥95%
  - Encoding detection ≥90%
  - Header detection ≥95%
- **Reliability**: Handle malformed data gracefully
- **Compatibility**: Work with all existing formatters without modification

### 2.4 Configuration Requirements

```python
{
    "csv": {
        "delimiter": None,           # None = auto-detect, or ",", "\t", ";", "|"
        "encoding": None,            # None = auto-detect, or "utf-8", "latin-1", etc.
        "has_header": None,          # None = auto-detect, or True/False
        "max_rows": None,            # None = unlimited, or integer limit
        "skip_rows": 0,              # Number of rows to skip at start
        "quotechar": '"',            # Character for quoted fields
        "strict": False              # Strict parsing mode
    }
}
```

## 3. Technical Approach

### 3.1 Design: Single TABLE ContentBlock

**Pattern**: One ContentBlock(type=TABLE) per CSV file

```python
ContentBlock(
    type="TABLE",
    content="",  # Empty - data in metadata
    metadata={
        "source_type": "csv",
        "file_path": "/path/to/file.csv",
        "encoding": "utf-8",
        "delimiter": ",",
        "has_header": True,
        "row_count": 100,
        "column_count": 5
    },
    table_metadata=TableMetadata(
        rows=100,
        columns=5,
        has_header=True,
        header_labels=["Name", "Age", "City", "Score", "Date"],
        cells=[
            ["Alice", "30", "NYC", "95", "2024-01-15"],
            ["Bob", "25", "LA", "87", "2024-01-16"],
            # ... 98 more rows
        ]
    )
)
```

### 3.2 Comparison with Excel Extractor

| Aspect | Excel Extractor | CSV Extractor | Status |
|--------|----------------|---------------|--------|
| ContentBlock type | TABLE | TABLE | ✓ Match |
| Blocks per file | 1 per sheet | 1 per file | ✓ Analogous |
| Metadata structure | TableMetadata | TableMetadata | ✓ Identical |
| Cell storage | 2D array in cells | 2D array in cells | ✓ Identical |
| Header handling | Auto-detect | Auto-detect | ✓ Match |
| Formatter support | All | All | ✓ Zero changes |

### 3.3 Why Option B (Single TABLE ContentBlock)

**Scores**: Option A (3.5/10), Option B (9.0/10), Option C (7.0/10)

**Option B Advantages**:
- Perfect alignment with Excel extractor pattern
- 1 ContentBlock per file vs 10,000+ for row-per-block
- Works with existing formatters (zero code changes)
- Efficient memory usage
- Simple mental model: CSV file = TABLE ContentBlock
- Consistent with established data extraction patterns

**Rejected Alternatives**:
- **Option A** (Row-per-block): 10K+ ContentBlocks for large files, formatter breakage
- **Option C** (Hybrid): Artificial chunking complexity, inconsistent with Excel pattern

## 4. Implementation Details

### 4.1 File Structure

**New File**: `src/extractors/csv_extractor.py`

```python
from typing import Optional, Dict, Any, List, Tuple
import csv
import chardet
from pathlib import Path
from .base_extractor import BaseExtractor
from ..models import ExtractionResult, ContentBlock, TableMetadata


class CSVExtractor(BaseExtractor):
    """
    Extracts CSV/TSV files into single TABLE ContentBlock per file.

    Follows Excel extractor pattern: one ContentBlock with TableMetadata
    containing full grid in cells array.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.csv_config = config.get("csv", {}) if config else {}

    def extract(self, file_path: str) -> ExtractionResult:
        """Extract CSV file to ExtractionResult with single TABLE ContentBlock."""

    def _detect_delimiter(self, file_path: str, encoding: str) -> str:
        """Detect CSV delimiter using csv.Sniffer with fallback."""

    def _detect_encoding(self, file_path: str) -> str:
        """Detect file encoding with UTF-8 → Latin-1 → CP1252 cascade."""

    def _detect_header(self, rows: List[List[str]]) -> bool:
        """Detect header presence using multi-check heuristic."""

    def _normalize_row(self, row: List[str], expected_columns: int) -> List[str]:
        """Normalize row length by padding or truncating."""

    def _read_csv_file(
        self,
        file_path: str,
        encoding: str,
        delimiter: str
    ) -> Tuple[List[List[str]], Dict[str, Any]]:
        """Read CSV file and return rows + metadata."""
```

### 4.2 Method: `extract(file_path) -> ExtractionResult`

```python
def extract(self, file_path: str) -> ExtractionResult:
    """
    Extract CSV file to ExtractionResult.

    Returns:
        ExtractionResult with single ContentBlock(type=TABLE)
    """
    path = Path(file_path)

    # Detect encoding
    encoding = self.csv_config.get("encoding") or self._detect_encoding(file_path)

    # Detect delimiter
    delimiter = self.csv_config.get("delimiter") or self._detect_delimiter(file_path, encoding)

    # Read CSV file
    rows, read_metadata = self._read_csv_file(file_path, encoding, delimiter)

    if not rows:
        return ExtractionResult(
            source_file=file_path,
            content_blocks=[],
            metadata={"error": "empty_file"}
        )

    # Detect header
    has_header_config = self.csv_config.get("has_header")
    has_header = has_header_config if has_header_config is not None else self._detect_header(rows)

    # Extract header labels
    header_labels = None
    data_rows = rows
    if has_header and rows:
        header_labels = rows[0]
        data_rows = rows[1:]

    # Normalize row lengths
    column_count = len(header_labels) if header_labels else max(len(row) for row in data_rows)
    normalized_rows = [self._normalize_row(row, column_count) for row in data_rows]

    # Create TableMetadata
    table_metadata = TableMetadata(
        rows=len(normalized_rows),
        columns=column_count,
        has_header=has_header,
        header_labels=header_labels,
        cells=normalized_rows
    )

    # Create ContentBlock
    block = ContentBlock(
        type="TABLE",
        content="",
        metadata={
            "source_type": "csv",
            "file_path": file_path,
            "encoding": encoding,
            "delimiter": delimiter,
            "has_header": has_header,
            "row_count": len(normalized_rows),
            "column_count": column_count,
            **read_metadata
        },
        table_metadata=table_metadata
    )

    return ExtractionResult(
        source_file=file_path,
        content_blocks=[block],
        metadata={
            "encoding": encoding,
            "delimiter": delimiter,
            "has_header": has_header,
            "row_count": len(normalized_rows),
            "column_count": column_count
        }
    )
```

### 4.3 Method: `_detect_delimiter(file_path, encoding) -> str`

```python
def _detect_delimiter(self, file_path: str, encoding: str) -> str:
    """
    Detect CSV delimiter using csv.Sniffer with fallback.

    Algorithm:
    1. Read first 8KB of file
    2. Try csv.Sniffer.sniff()
    3. If fails, count delimiter candidates
    4. Return most common valid delimiter
    5. Default to comma if all fail

    Returns:
        Detected delimiter: ",", "\t", ";", "|"
    """
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            sample = f.read(8192)

        # Try csv.Sniffer
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=',\t;|')
            return dialect.delimiter
        except csv.Error:
            pass

        # Fallback: count delimiter candidates
        delimiter_counts = {
            ',': sample.count(','),
            '\t': sample.count('\t'),
            ';': sample.count(';'),
            '|': sample.count('|')
        }

        # Return most common delimiter
        max_delimiter = max(delimiter_counts, key=delimiter_counts.get)
        if delimiter_counts[max_delimiter] > 0:
            return max_delimiter

        # Default to comma
        return ','

    except Exception:
        return ','
```

### 4.4 Method: `_detect_encoding(file_path) -> str`

```python
def _detect_encoding(self, file_path: str) -> str:
    """
    Detect file encoding with UTF-8 → Latin-1 → CP1252 cascade.

    Algorithm:
    1. Try UTF-8 (most common)
    2. Use chardet on first 100KB
    3. Fallback to Latin-1 (always works)

    Returns:
        Detected encoding name
    """
    # Try UTF-8 first
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return 'utf-8'
    except UnicodeDecodeError:
        pass

    # Use chardet
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(102400)  # 100KB

        detection = chardet.detect(raw_data)
        if detection['confidence'] > 0.7:
            return detection['encoding'].lower()
    except Exception:
        pass

    # Fallback to Latin-1 (always works)
    return 'latin-1'
```

### 4.5 Method: `_detect_header(rows) -> bool`

```python
def _detect_header(self, rows: List[List[str]]) -> bool:
    """
    Detect header presence using multi-check heuristic.

    Algorithm:
    1. Check if first row has different data types than second row
    2. Check if first row values are unique
    3. Check if first row has longer strings (typical header pattern)
    4. Combine checks with weighted scoring

    Target accuracy: ≥95%

    Returns:
        True if header detected
    """
    if len(rows) < 2:
        return False

    first_row = rows[0]
    second_row = rows[1]

    score = 0.0

    # Check 1: Type consistency (headers are usually all strings)
    first_numeric = sum(1 for cell in first_row if cell.strip().replace('.', '').replace('-', '').isdigit())
    second_numeric = sum(1 for cell in second_row if cell.strip().replace('.', '').replace('-', '').isdigit())

    if first_numeric < second_numeric:
        score += 0.4

    # Check 2: Uniqueness (headers are usually unique)
    if len(first_row) == len(set(first_row)):
        score += 0.3

    # Check 3: Length patterns (headers often longer, more descriptive)
    first_avg_len = sum(len(str(cell)) for cell in first_row) / len(first_row) if first_row else 0
    second_avg_len = sum(len(str(cell)) for cell in second_row) / len(second_row) if second_row else 0

    if first_avg_len > second_avg_len * 1.2:
        score += 0.3

    # Threshold: 0.5 = has header
    return score >= 0.5
```

### 4.6 Method: `_normalize_row(row, expected_columns) -> List[str]`

```python
def _normalize_row(self, row: List[str], expected_columns: int) -> List[str]:
    """
    Normalize row length by padding or truncating.

    Args:
        row: Input row
        expected_columns: Target column count

    Returns:
        Row with exactly expected_columns elements
    """
    if len(row) == expected_columns:
        return row
    elif len(row) < expected_columns:
        # Pad with empty strings
        return row + [''] * (expected_columns - len(row))
    else:
        # Truncate (log warning in production)
        return row[:expected_columns]
```

## 5. Data Structures

### 5.1 ContentBlock Structure for CSV

```python
ContentBlock(
    type="TABLE",
    content="",  # Empty - data in table_metadata
    metadata={
        "source_type": "csv",
        "file_path": "/data/sales_2024.csv",
        "encoding": "utf-8",
        "delimiter": ",",
        "has_header": True,
        "row_count": 1523,
        "column_count": 8,
        "file_size_bytes": 245678,
        "detection_confidence": {
            "encoding": 0.95,
            "delimiter": 1.0,
            "header": 0.82
        }
    },
    table_metadata=TableMetadata(...)
)
```

### 5.2 TableMetadata Structure

```python
TableMetadata(
    rows=1523,
    columns=8,
    has_header=True,
    header_labels=["Date", "Product", "Quantity", "Price", "Customer", "Region", "Status", "Notes"],
    cells=[
        ["2024-01-15", "Widget A", "100", "9.99", "Acme Corp", "West", "Shipped", ""],
        ["2024-01-15", "Widget B", "50", "14.99", "Beta Inc", "East", "Processing", "Rush order"],
        # ... 1521 more rows
    ]
)
```

### 5.3 Output Format Example

**Input**: `products.csv`
```csv
Product,SKU,Price,Stock
Widget,W001,9.99,100
Gadget,G002,14.99,50
```

**Output**: ExtractionResult
```python
ExtractionResult(
    source_file="products.csv",
    content_blocks=[
        ContentBlock(
            type="TABLE",
            content="",
            metadata={
                "source_type": "csv",
                "encoding": "utf-8",
                "delimiter": ",",
                "has_header": True,
                "row_count": 2,
                "column_count": 4
            },
            table_metadata=TableMetadata(
                rows=2,
                columns=4,
                has_header=True,
                header_labels=["Product", "SKU", "Price", "Stock"],
                cells=[
                    ["Widget", "W001", "9.99", "100"],
                    ["Gadget", "G002", "14.99", "50"]
                ]
            )
        )
    ],
    metadata={
        "encoding": "utf-8",
        "delimiter": ",",
        "has_header": True,
        "row_count": 2,
        "column_count": 4
    }
)
```

## 6. Edge Case Handling

### 6.1 Large Files (>100MB)

**Problem**: Memory exhaustion on large CSVs

**Solution**: `max_rows` configuration
```python
# Config
{"csv": {"max_rows": 10000}}

# Implementation
if self.csv_config.get("max_rows"):
    rows = rows[:self.csv_config["max_rows"]]
    metadata["truncated"] = True
    metadata["total_rows_available"] = original_row_count
```

### 6.2 Header Detection Failures

**Problem**: Ambiguous header presence (numeric headers, single row file)

**Solution**: Multi-check heuristic with 3 factors
- Type consistency (0.4 weight)
- Uniqueness (0.3 weight)
- Length patterns (0.3 weight)
- Threshold: 0.5

**Override**: `{"csv": {"has_header": false}}`

### 6.3 Delimiter Auto-Detection Failures

**Problem**: Uncommon delimiters, mixed delimiters

**Solution**: Sniffer + fallback
```python
# Priority
1. csv.Sniffer.sniff() with delimiters=',\t;|'
2. Count-based selection (most common)
3. Default to comma
```

**Override**: `{"csv": {"delimiter": ";"}}`

### 6.4 Encoding Detection Failures

**Problem**: Mixed encodings, binary data

**Solution**: Cascade strategy
```python
# Priority
1. UTF-8 validation (fast)
2. chardet on 100KB (accurate)
3. Latin-1 fallback (always works)
```

**Override**: `{"csv": {"encoding": "cp1252"}}`

### 6.5 Malformed Data (Variable Row Lengths)

**Problem**: Rows with different column counts

**Solution**: Normalize to max column count
```python
max_cols = max(len(row) for row in rows)
normalized = [pad_or_truncate(row, max_cols) for row in rows]

# Pad with empty strings
# Truncate excess (log warning)
```

**Metadata**: Track normalization
```python
metadata["row_length_variance"] = {
    "min": 5,
    "max": 8,
    "normalized_to": 8,
    "rows_modified": 12
}
```

### 6.6 Empty Files

**Problem**: Zero-byte or header-only files

**Solution**: Graceful handling
```python
if not rows:
    return ExtractionResult(
        source_file=file_path,
        content_blocks=[],
        metadata={"error": "empty_file"}
    )

if has_header and len(rows) == 1:
    return ExtractionResult(
        source_file=file_path,
        content_blocks=[],
        metadata={"error": "header_only_file", "headers": rows[0]}
    )
```

### 6.7 Single Column Files

**Problem**: Files with single column (no delimiter)

**Solution**: Treat as single-column table
```python
# Detection: no delimiters found
if column_count == 1:
    header_labels = ["Column1"] if not has_header else [rows[0][0]]
```

### 6.8 Quoted and Escaped Fields

**Problem**: Commas/quotes in data: `"Smith, John","100,000"`

**Solution**: Use csv.reader (automatic)
```python
with open(file_path, 'r', encoding=encoding) as f:
    reader = csv.reader(
        f,
        delimiter=delimiter,
        quotechar=self.csv_config.get('quotechar', '"'),
        escapechar='\\'
    )
    rows = list(reader)
```

### 6.9 Mixed Data Types

**Problem**: Numbers, dates, booleans in cells

**Solution**: Store all as strings
```python
# No type conversion
cells = [[str(cell) for cell in row] for row in rows]

# Formatters handle presentation
# Processors can parse types if needed
```

## 7. Algorithm Specifications

### 7.1 Delimiter Detection Algorithm

```
INPUT: file_path, encoding
OUTPUT: delimiter character

ALGORITHM:
1. sample ← read_first_8kb(file_path, encoding)
2. TRY:
     dialect ← csv.Sniffer.sniff(sample, delimiters=',\t;|')
     RETURN dialect.delimiter
   EXCEPT csv.Error:
     CONTINUE
3. counts ← {',': count(',', sample), '\t': count('\t', sample),
              ';': count(';', sample), '|': count('|', sample)}
4. max_delim ← argmax(counts)
5. IF counts[max_delim] > 0:
     RETURN max_delim
6. RETURN ','  // default

TIME: O(n) where n = sample size (8KB)
ACCURACY TARGET: ≥95%
```

### 7.2 Encoding Detection Algorithm

```
INPUT: file_path
OUTPUT: encoding name

ALGORITHM:
1. TRY:
     open(file_path, encoding='utf-8')
     read_test_chunk(1KB)
     RETURN 'utf-8'
   EXCEPT UnicodeDecodeError:
     CONTINUE
2. TRY:
     raw_data ← read_binary(file_path, limit=100KB)
     result ← chardet.detect(raw_data)
     IF result.confidence > 0.7:
       RETURN result.encoding.lower()
   EXCEPT:
     CONTINUE
3. RETURN 'latin-1'  // fallback (always succeeds)

TIME: O(n) where n = 100KB
ACCURACY TARGET: ≥90%
```

### 7.3 Header Detection Heuristic

```
INPUT: rows (2D array)
OUTPUT: boolean (has_header)

ALGORITHM:
1. IF len(rows) < 2:
     RETURN False
2. score ← 0.0
3. first_row ← rows[0]
4. second_row ← rows[1]

5. // Type consistency check
   first_numeric ← count_numeric_cells(first_row)
   second_numeric ← count_numeric_cells(second_row)
   IF first_numeric < second_numeric:
     score += 0.4

6. // Uniqueness check
   IF all_unique(first_row):
     score += 0.3

7. // Length pattern check
   first_avg_len ← avg_cell_length(first_row)
   second_avg_len ← avg_cell_length(second_row)
   IF first_avg_len > 1.2 * second_avg_len:
     score += 0.3

8. RETURN score ≥ 0.5

TIME: O(n) where n = columns
ACCURACY TARGET: ≥95%
```

### 7.4 Row Normalization Strategy

```
INPUT: row (array), expected_columns (int)
OUTPUT: normalized_row (array)

ALGORITHM:
1. actual_cols ← len(row)
2. IF actual_cols = expected_columns:
     RETURN row
3. ELSE IF actual_cols < expected_columns:
     padding ← [''] * (expected_columns - actual_cols)
     RETURN row + padding
4. ELSE:  // actual_cols > expected_columns
     log_warning(f"Truncating row from {actual_cols} to {expected_columns}")
     RETURN row[:expected_columns]

TIME: O(1) amortized
```

## 8. Testing Requirements

### 8.1 Unit Tests

**File**: `tests/test_extractors/test_csv_extractor.py`

```python
class TestCSVExtractor:
    """Unit tests for CSVExtractor"""

    # Core extraction
    def test_extract_basic_csv()
    def test_extract_basic_tsv()
    def test_extract_with_header()
    def test_extract_without_header()

    # Delimiter detection
    def test_detect_delimiter_comma()
    def test_detect_delimiter_tab()
    def test_detect_delimiter_semicolon()
    def test_detect_delimiter_pipe()
    def test_detect_delimiter_fallback()

    # Encoding detection
    def test_detect_encoding_utf8()
    def test_detect_encoding_latin1()
    def test_detect_encoding_cp1252()
    def test_detect_encoding_fallback()

    # Header detection
    def test_detect_header_present()
    def test_detect_header_absent()
    def test_detect_header_ambiguous()
    def test_detect_header_numeric()

    # Row normalization
    def test_normalize_row_pad()
    def test_normalize_row_truncate()
    def test_normalize_row_exact()

    # Edge cases
    def test_empty_file()
    def test_single_row()
    def test_single_column()
    def test_large_file_truncation()
    def test_malformed_rows()
    def test_quoted_fields()
    def test_escaped_quotes()
    def test_mixed_line_endings()

    # Configuration
    def test_config_override_delimiter()
    def test_config_override_encoding()
    def test_config_override_header()
    def test_config_max_rows()
    def test_config_skip_rows()
```

### 8.2 Integration Tests

**File**: `tests/integration/test_csv_integration.py`

```python
class TestCSVIntegration:
    """Integration tests for CSV extractor in pipeline"""

    def test_csv_to_json_formatter()
    def test_csv_to_markdown_formatter()
    def test_csv_to_chunked_text_formatter()
    def test_csv_pipeline_registration()
    def test_csv_batch_processing()
    def test_csv_cli_extract_command()
    def test_csv_with_context_linker()
    def test_csv_with_metadata_aggregator()
    def test_csv_with_quality_validator()
```

### 8.3 Test Fixtures

**Directory**: `tests/fixtures/csv/`

```
fixtures/csv/
├── basic.csv                    # Simple 3x3 with header
├── basic_no_header.csv          # Simple 3x3 without header
├── tsv.tsv                      # Tab-delimited
├── semicolon.csv                # Semicolon delimiter
├── pipe.csv                     # Pipe delimiter
├── quoted_fields.csv            # Contains "Smith, John" style
├── escaped_quotes.csv           # Contains \" escapes
├── empty.csv                    # Zero bytes
├── header_only.csv              # Just header row
├── single_column.csv            # One column
├── malformed.csv                # Variable row lengths
├── large.csv                    # 10K rows (generated)
├── utf8_bom.csv                 # UTF-8 with BOM
├── latin1.csv                   # Latin-1 encoded
├── mixed_types.csv              # Strings, numbers, dates
└── windows_line_endings.csv     # \r\n endings
```

### 8.4 Coverage Target

**Minimum**: 85% line coverage
**Target**: 95% line coverage

**Critical paths requiring 100% coverage**:
- Delimiter detection
- Encoding detection
- Header detection
- Row normalization
- Main extract() method

## 9. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Extraction speed (1K rows) | <1s | `pytest --durations=10` |
| Extraction speed (10K rows) | <5s | `pytest --durations=10` |
| Memory usage (10K rows) | <50MB | `memory_profiler` |
| Delimiter detection accuracy | ≥95% | Manual test on 100 samples |
| Encoding detection accuracy | ≥90% | Manual test on 50 samples |
| Header detection accuracy | ≥95% | Manual test on 100 samples |
| Pipeline throughput | 10 files/s | Batch processing benchmark |

### 9.1 Performance Testing

```python
# File: tests/performance/test_csv_performance.py

@pytest.mark.benchmark
def test_extraction_speed_1k():
    """Benchmark: Extract 1K row CSV in <1s"""
    extractor = CSVExtractor()
    start = time.time()
    result = extractor.extract("fixtures/1k_rows.csv")
    duration = time.time() - start
    assert duration < 1.0

@pytest.mark.benchmark
def test_memory_usage_10k():
    """Benchmark: Use <50MB for 10K row CSV"""
    extractor = CSVExtractor()
    mem_before = get_memory_usage()
    result = extractor.extract("fixtures/10k_rows.csv")
    mem_after = get_memory_usage()
    mem_used_mb = (mem_after - mem_before) / 1024 / 1024
    assert mem_used_mb < 50
```

## 10. Pipeline Integration

### 10.1 Registration in extraction_pipeline.py

```python
# File: src/pipeline/extraction_pipeline.py

from ..extractors.csv_extractor import CSVExtractor

class ExtractionPipeline:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.extractors = {
            '.pdf': PDFExtractor(config),
            '.docx': DocxExtractor(config),
            '.xlsx': ExcelExtractor(config),
            '.pptx': PPTXExtractor(config),
            '.txt': TextExtractor(config),
            '.csv': CSVExtractor(config),  # NEW
            '.tsv': CSVExtractor(config),  # NEW
        }
```

### 10.2 CLI Support

```bash
# Extract single CSV file
python -m cli extract sample.csv

# Extract with output format
python -m cli extract sample.csv --output json

# Extract with config override
python -m cli extract sample.csv --config '{"csv": {"delimiter": ";"}}'

# Batch extract CSV files
python -m cli batch-extract input_dir/*.csv --output-dir results/
```

### 10.3 Batch Processing Support

```python
# File: src/pipeline/batch_processor.py

class BatchProcessor:
    def process_directory(self, input_dir: str, **kwargs):
        """Process all supported files including CSV/TSV"""
        # Automatically detects .csv and .tsv files
        # Uses CSVExtractor via pipeline registration
```

### 10.4 Formatter Compatibility

**Zero formatter changes required**

| Formatter | Compatibility | Output |
|-----------|---------------|--------|
| JSONFormatter | ✓ Native | TABLE ContentBlock → JSON table object |
| MarkdownFormatter | ✓ Native | TABLE ContentBlock → Markdown table |
| ChunkedTextFormatter | ✓ Native | TABLE ContentBlock → Text chunks |

**Example: JSON Output**
```json
{
  "source_file": "data.csv",
  "content_blocks": [
    {
      "type": "TABLE",
      "content": "",
      "metadata": {
        "source_type": "csv",
        "delimiter": ",",
        "has_header": true,
        "row_count": 2,
        "column_count": 3
      },
      "table_metadata": {
        "rows": 2,
        "columns": 3,
        "has_header": true,
        "header_labels": ["Name", "Age", "City"],
        "cells": [
          ["Alice", "30", "NYC"],
          ["Bob", "25", "LA"]
        ]
      }
    }
  ]
}
```

**Example: Markdown Output**
```markdown
# data.csv

## Table

| Name | Age | City |
|------|-----|------|
| Alice | 30 | NYC |
| Bob | 25 | LA |
```

## 11. Configuration Schema

### 11.1 Full Configuration

```python
{
    "csv": {
        # Delimiter
        "delimiter": None,           # None = auto-detect
                                     # Or: ",", "\t", ";", "|", custom

        # Encoding
        "encoding": None,            # None = auto-detect
                                     # Or: "utf-8", "latin-1", "cp1252", etc.

        # Header
        "has_header": None,          # None = auto-detect
                                     # Or: True, False

        # Row limits
        "max_rows": None,            # None = unlimited
                                     # Or: integer (e.g., 10000)

        "skip_rows": 0,              # Number of rows to skip at start

        # Parsing options
        "quotechar": '"',            # Quote character for fields
        "escapechar": None,          # Escape character (None = none)
        "strict": False,             # Strict parsing mode

        # Detection tuning
        "detection_sample_size": 8192,   # Bytes to sample for detection
        "header_detection_threshold": 0.5,  # Score threshold for header

        # Performance
        "chunk_size": None,          # Future: streaming support
    }
}
```

### 11.2 Default Configuration

```python
DEFAULT_CSV_CONFIG = {
    "delimiter": None,
    "encoding": None,
    "has_header": None,
    "max_rows": None,
    "skip_rows": 0,
    "quotechar": '"',
    "escapechar": None,
    "strict": False,
    "detection_sample_size": 8192,
    "header_detection_threshold": 0.5,
    "chunk_size": None,
}
```

### 11.3 Example Configurations

**Example 1: European CSV (semicolon, Latin-1)**
```python
{
    "csv": {
        "delimiter": ";",
        "encoding": "latin-1",
        "has_header": True
    }
}
```

**Example 2: Large file processing**
```python
{
    "csv": {
        "max_rows": 50000,
        "skip_rows": 5  # Skip metadata rows
    }
}
```

**Example 3: Strict parsing**
```python
{
    "csv": {
        "strict": True,
        "delimiter": ",",
        "has_header": True
    }
}
```

## 12. Success Criteria

### 12.1 Core Functionality
- [ ] CSV files extract to single TABLE ContentBlock
- [ ] TSV files extract to single TABLE ContentBlock
- [ ] TableMetadata populated with full grid in cells array
- [ ] Delimiter auto-detection works (≥95% accuracy)
- [ ] Encoding auto-detection works (≥90% accuracy)
- [ ] Header auto-detection works (≥95% accuracy)
- [ ] Configuration overrides work (delimiter, encoding, header)
- [ ] Row normalization handles variable lengths
- [ ] Quoted fields handled correctly
- [ ] Escaped characters handled correctly

### 12.2 Edge Cases
- [ ] Empty files return empty content_blocks
- [ ] Single-row files handled gracefully
- [ ] Single-column files treated as tables
- [ ] Large files respect max_rows limit
- [ ] Malformed data normalized without crashes
- [ ] Mixed line endings handled (Unix/Windows)
- [ ] Files with BOM handled correctly
- [ ] Binary data in cells handled (as strings)

### 12.3 Integration
- [ ] Registered in extraction_pipeline.py for .csv and .tsv
- [ ] CLI extract command works: `python -m cli extract file.csv`
- [ ] CLI batch command works for CSV files
- [ ] JSONFormatter produces valid output
- [ ] MarkdownFormatter produces valid tables
- [ ] ChunkedTextFormatter produces valid chunks
- [ ] Context linker works with CSV content
- [ ] Metadata aggregator works with CSV metadata
- [ ] Quality validator works with CSV data

### 12.4 Testing
- [ ] All unit tests pass (≥85% coverage)
- [ ] All integration tests pass
- [ ] Performance benchmarks meet targets
- [ ] Manual accuracy testing complete (delimiter, encoding, header)
- [ ] Test fixtures created and checked in
- [ ] Edge case tests comprehensive

### 12.5 Quality
- [ ] No regressions in existing extractors
- [ ] No changes required to existing formatters
- [ ] No changes required to existing processors
- [ ] Code follows project style (type hints, docstrings)
- [ ] Error handling comprehensive (try/except with logging)
- [ ] Logging informative for debugging

### 12.6 Documentation
- [ ] Docstrings complete for all public methods
- [ ] README updated with CSV extractor info
- [ ] Configuration examples documented
- [ ] Edge case handling documented

## 13. Dependencies

### 13.1 Python Standard Library
- `csv` - CSV parsing (dialect detection, reader)
- `pathlib` - File path handling
- `typing` - Type annotations

### 13.2 Third-Party Libraries
- `chardet` - Character encoding detection (already in project)

### 13.3 Internal Dependencies
- `src.extractors.base_extractor.BaseExtractor` - Base class
- `src.models.ExtractionResult` - Return type
- `src.models.ContentBlock` - Data structure
- `src.models.TableMetadata` - Table structure
- `src.pipeline.extraction_pipeline.ExtractionPipeline` - Registration

### 13.4 Existing Patterns
- Excel extractor pattern (single TABLE ContentBlock)
- Pipeline registration pattern
- Configuration override pattern
- Test fixture organization
- CLI command structure

## 14. Acceptance Criteria

### 14.1 Implementation Checklist

**Code Implementation**
- [ ] Create `src/extractors/csv_extractor.py`
- [ ] Implement `CSVExtractor` class with all methods
- [ ] Register extractor in `extraction_pipeline.py`
- [ ] Add `.csv` and `.tsv` to supported extensions

**Testing Implementation**
- [ ] Create `tests/test_extractors/test_csv_extractor.py`
- [ ] Implement all unit tests (30+ tests)
- [ ] Create `tests/integration/test_csv_integration.py`
- [ ] Implement integration tests (9+ tests)
- [ ] Create all test fixtures (15+ files)
- [ ] Run coverage: `pytest --cov=src.extractors.csv_extractor`

**Performance Validation**
- [ ] Run benchmark: 1K rows in <1s
- [ ] Run benchmark: 10K rows in <5s
- [ ] Run benchmark: Memory <50MB for 10K rows
- [ ] Generate large test files (1K, 10K, 100K rows)

**Accuracy Validation**
- [ ] Test delimiter detection on 100 diverse CSVs
- [ ] Test encoding detection on 50 diverse encodings
- [ ] Test header detection on 100 diverse structures
- [ ] Document false positive/negative cases

**Integration Validation**
- [ ] Test CLI: `python -m cli extract sample.csv`
- [ ] Test CLI: `python -m cli extract sample.tsv --output json`
- [ ] Test CLI: `python -m cli batch-extract csv_files/*.csv`
- [ ] Test with each formatter (JSON, Markdown, Chunked)
- [ ] Test with each processor (Context, Metadata, Quality)

**Documentation**
- [ ] Update `README.md` with CSV extractor
- [ ] Update `docs/configuration.md` with CSV config
- [ ] Add CSV examples to docs
- [ ] Document known limitations

### 14.2 Validation Commands

```bash
# Unit tests
pytest tests/test_extractors/test_csv_extractor.py -v

# Integration tests
pytest tests/integration/test_csv_integration.py -v

# Coverage
pytest --cov=src.extractors.csv_extractor --cov-report=html

# Performance
pytest tests/performance/test_csv_performance.py --benchmark-only

# Full test suite
pytest tests/ -v --cov=src

# CLI validation
python -m cli extract tests/fixtures/csv/basic.csv
python -m cli extract tests/fixtures/csv/basic.csv --output json
python -m cli batch-extract tests/fixtures/csv/ --output-dir /tmp/csv_results/

# Manual accuracy testing
python scripts/test_csv_accuracy.py  # Generate 100 test cases and validate
```

### 14.3 Definition of Done

**Code Complete**: All methods implemented, typed, documented
**Tests Pass**: 100% of unit + integration tests pass
**Coverage Met**: ≥85% line coverage achieved
**Performance Met**: All benchmarks pass targets
**Accuracy Met**: Detection accuracy meets ≥90-95% targets
**Integration Works**: CLI commands functional, no formatter changes
**No Regressions**: All existing tests still pass
**Reviewed**: Code review complete, feedback addressed
**Documented**: README, config docs updated
**Deployed**: Merged to main branch

---

## Appendix A: Design Decision Record

**Decision**: Use Option B (Single TABLE ContentBlock)
**Date**: 2024
**Status**: Approved

**Context**: Need to extract CSV files into ContentBlock structure. Three options evaluated.

**Options**:
- Option A: Row-per-ContentBlock (Score: 3.5/10)
- Option B: Single TABLE ContentBlock (Score: 9.0/10) ← **SELECTED**
- Option C: Hybrid chunked approach (Score: 7.0/10)

**Decision**: Option B selected

**Rationale**:
1. Perfect alignment with Excel extractor (proven pattern)
2. Efficient: 1 ContentBlock vs 10,000+ for large files
3. Zero formatter changes required
4. Simple mental model
5. Handles all edge cases gracefully

**Consequences**:
- Positive: Consistency, efficiency, compatibility
- Negative: None identified
- Risks: Large files (mitigated by max_rows config)

---

## Appendix B: Open Questions

**None** - Design analysis complete, all decisions made.

---

**Document Version**: 1.0
**Last Updated**: 2024
**Author**: Technical Writer Agent
**Status**: Ready for Implementation

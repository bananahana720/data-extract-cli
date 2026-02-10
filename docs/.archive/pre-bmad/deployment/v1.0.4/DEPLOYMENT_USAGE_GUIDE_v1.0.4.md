# AI Data Extractor v1.0.4 - Deployment Usage Guide

**Version**: 1.0.4 (Production Ready)
**Date**: 2025-11-03
**Platform**: Windows, Linux, Mac
**Python**: 3.11+ required
**Status**: Production-ready | 950+ tests | 92% coverage | 0 blockers

---

## Table of Contents

1. [Quick Start (5 Minutes)](#quick-start)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Batch Processing](#batch-processing)
5. [v1.0.4 Features](#v104-features)
6. [Output Formats](#output-formats)
7. [Configuration](#configuration)
8. [Command Reference](#command-reference)
9. [Troubleshooting](#troubleshooting)
10. [Performance Tips](#performance-tips)

---

## Quick Start

Get extracting in 5 minutes.

### Windows Users

```batch
REM 1. Install the tool
pip install dist\ai_data_extractor-1.0.4-py3-none-any.whl

REM 2. Verify installation
data-extract version

REM 3. Extract a document
data-extract extract C:\Documents\sample.docx --format json --output C:\Output\sample.json

REM 4. View the result
type C:\Output\sample.json
```

### Linux/Mac Users

```bash
# 1. Install the tool
pip install dist/ai_data_extractor-1.0.4-py3-none-any.whl

# 2. Verify installation
data-extract version

# 3. Extract a document
data-extract extract ~/Documents/sample.docx --format json --output ~/output/sample.json

# 4. View the result
cat ~/output/sample.json
```

---

## Installation

### System Requirements

- **Python**: 3.11 or later
- **OS**: Windows, Linux, macOS
- **Disk Space**: 200 MB (with dependencies)
- **Memory**: Minimum 2 GB RAM (4 GB+ recommended for large batches)

### Step 1: Install from Wheel

Windows:
```bash
pip install dist\ai_data_extractor-1.0.4-py3-none-any.whl
```

Linux/Mac:
```bash
pip install dist/ai_data_extractor-1.0.4-py3-none-any.whl
```

### Step 2: Verify Installation

Check version:
```bash
data-extract version
```

Output should show:
```
Data Extraction Tool v1.0.4
Python 3.11.0 | Windows 10 (or your OS)
Status: Ready for production use
```

### Step 3: Check Available Extractors

```bash
data-extract version --verbose
```

Shows which extractors are available:
- DOCX (Word documents) ✓
- PDF (PDF files) ✓
- PPTX (PowerPoint) ✓
- XLSX (Excel workbooks) ✓
- TXT (Plain text files) ✓

### Optional: Install OCR Support

For OCR capabilities with PDFs:

```bash
pip install ai-data-extractor[ocr]
```

This adds:
- `pytesseract` for OCR processing
- `pdf2image` for PDF-to-image conversion

---

## Basic Usage

### Single File Extraction

Extract one document to JSON:

```bash
data-extract extract path\to\document.docx --format json --output output.json
```

#### Arguments

| Argument | Purpose | Required |
|----------|---------|----------|
| `extract` | Command to run | Yes |
| `path\to\document.docx` | File to extract | Yes |
| `--format json` | Output format | No (default: json) |
| `--output output.json` | Output file path | No (default: input_name.json) |

#### Format Options

- `json` - Structured JSON with metadata
- `markdown` - Readable markdown format
- `chunked` - AI-ready chunks (token-limited)

### Extract to JSON

Best for programmatic processing:

```bash
data-extract extract sales_report.xlsx --format json --output sales_output.json
```

Output includes:
- Structured blocks
- Metadata (word count, page info, quality score)
- Table data with cell positions
- Image metadata

### Extract to Markdown

Best for human review:

```bash
data-extract extract presentation.pptx --format markdown --output presentation.md
```

Output includes:
- Readable headings and sections
- Formatted lists and tables
- Slide numbers in comments

### Extract to Chunked Format

Best for LLM processing:

```bash
data-extract extract document.pdf --format chunked --output document_chunks.txt
```

Output includes:
- Sequential numbered chunks
- Token-aware splitting
- Block type indicators
- Clear section boundaries

---

## Batch Processing

Process multiple files at once with parallel workers.

### Basic Batch

Process all documents in a folder:

```bash
data-extract batch C:\Input\ --output C:\Output\ --format json
```

#### Arguments for Batch

| Argument | Purpose | Example |
|----------|---------|---------|
| `batch` | Command | `batch` |
| Input folder | Where documents are | `C:\Input\` or `./docs/` |
| `--output` | Output folder | `C:\Output\` |
| `--format` | Output format | `json` (default) |
| `--workers` | Parallel threads | `4` (default: CPU count) |
| `--pattern` | File filter | `*.pdf` (default: all) |

### Batch with Specific File Types

Only process PDF files:

```bash
data-extract batch C:\Documents\ --output C:\Results\ --format json --pattern *.pdf
```

### Batch with Worker Threads

Use 8 parallel workers for faster processing:

```bash
data-extract batch input/ output/ --format markdown --workers 8
```

#### Workers Guide

| Workers | Best For | Speed |
|---------|----------|-------|
| 1 | Testing, debugging | Slowest |
| 2-4 | Small batches (10-50 files) | Balanced |
| 4-8 | Medium batches (50-500 files) | Fast |
| 8+ | Large batches (500+ files) | Fastest |

**Rule**: Use `workers = (CPU count) / 2` for balanced system load

### Batch Progress Indicator

During batch processing, you see:
```
Processing: ████████░░ 8/10 files | 45 sec | ETA 10 sec
```

Columns mean:
- Progress bar: Visual completion
- 8/10: Files completed / Total files
- 45 sec: Elapsed time
- ETA: Estimated time remaining

---

## v1.0.4 Features

### NEW: DOCX Table Extraction

Word documents now extract full table content with cell data.

Example document (document.docx):
```
| Header 1 | Header 2 |
|----------|----------|
| Cell A1  | Cell B1  |
| Cell A2  | Cell B2  |
```

Extract:
```bash
data-extract extract document.docx --format json --output output.json
```

Result JSON includes:
```json
{
  "block_type": "TABLE",
  "content": "Header 1 | Header 2 | ...",
  "metadata": {
    "table_id": "table_1",
    "rows": 3,
    "columns": 2,
    "cells": [
      {"position": [0, 0], "content": "Header 1"},
      {"position": [0, 1], "content": "Header 2"},
      ...
    ]
  }
}
```

### NEW: PPTX Image Extraction

PowerPoint presentations now extract images with metadata.

Extract:
```bash
data-extract extract presentation.pptx --format json --output output.json
```

Result includes:
```json
{
  "block_type": "IMAGE",
  "content": "[Image: slide_1_image_1]",
  "metadata": {
    "slide_number": 1,
    "image_name": "image1.png",
    "width": 1024,
    "height": 768,
    "format": "PNG"
  }
}
```

### FIXED: Excel Multi-Sheet Support

Excel workbooks process all sheets automatically.

Example with multiple sheets:
```
Sheet1: Sales data
Sheet2: Regional breakdown
Sheet3: Summary
```

Extract:
```bash
data-extract extract workbook.xlsx --format json --output output.json
```

Result includes all sheets with sheet identifiers in metadata:
```json
{
  "block_type": "TABLE",
  "metadata": {
    "sheet_name": "Sheet1",
    "sheet_index": 0,
    "table_id": "table_sheet1_0"
  }
}
```

### System-Wide Table Preservation

Tables extracted from any format stay intact through the entire pipeline:
- Extracted as TABLE blocks
- Processed with cell position metadata
- Preserved in all output formats (JSON, Markdown, Chunked)

### System-Wide Image Preservation

Images extracted from PDF and PPTX stay intact through the entire pipeline:
- Extracted as IMAGE blocks
- Processed with dimension and format metadata
- Preserved in all output formats

---

## Output Formats

### JSON Format

Structured output with complete metadata.

```bash
data-extract extract document.pdf --format json --output output.json
```

File structure:
```json
{
  "document_metadata": {
    "file_name": "document.pdf",
    "file_size_bytes": 245000,
    "page_count": 12,
    "extraction_quality": 0.95
  },
  "blocks": [
    {
      "block_id": "block_0_1",
      "block_type": "PARAGRAPH",
      "content": "This is paragraph text...",
      "position": {
        "page": 1,
        "sequence_index": 0
      },
      "metadata": {
        "word_count": 42,
        "char_count": 215
      }
    },
    {
      "block_id": "table_1",
      "block_type": "TABLE",
      "content": "Col1 | Col2 | Col3 | ...",
      "metadata": {
        "rows": 5,
        "columns": 3,
        "cells": [...]
      }
    }
  ],
  "processing_summary": {
    "total_blocks": 125,
    "blocks_by_type": {
      "PARAGRAPH": 110,
      "TABLE": 8,
      "IMAGE": 7
    },
    "average_quality_score": 0.89
  }
}
```

#### JSON Use Cases

- Programmatic data processing
- Database imports
- API integration
- Machine learning pipelines

### Markdown Format

Human-readable format with sections.

```bash
data-extract extract document.pdf --format markdown --output output.md
```

File structure:
```markdown
# document.pdf

**Document Info**: 12 pages | Quality: 95% | Extracted: 2025-11-03

## Page 1

Paragraph text goes here...

### Section 2.1 - Table Data

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1    | Data     | Value    |
| Row 2    | Data     | Value    |

**[Image: slide_1_image_1 - PNG 1024x768]**

## Page 2

Next content...
```

#### Markdown Use Cases

- Human review and editing
- Documentation
- Version control (Git-friendly)
- Email distribution

### Chunked Format

AI-ready format with token-limited chunks.

```bash
data-extract extract document.pdf --format chunked --output output.txt
```

File structure:
```
=== CHUNK 1 (425 tokens) ===
[PARAGRAPH] Page 1, Sequence 0
This is paragraph text from the document...

[PARAGRAPH] Page 1, Sequence 1
More content...

=== CHUNK 2 (512 tokens) ===
[TABLE] Page 2, Table 1
Header1 | Header2 | Header3
Row1Data | Value | Data
...

=== CHUNK 3 (380 tokens) ===
[IMAGE] Page 3, Image metadata
Image: slide_1_image_1 (PNG 1024x768)
...
```

#### Chunked Use Cases

- LLM input preparation
- Token-limited processing
- Vector database chunking
- Semantic search indexing

---

## Configuration

### Default Behavior

By default, the tool uses built-in configuration. No setup required for basic use.

### Custom Configuration File

Create `config.yaml` for custom settings:

```yaml
# Extraction settings
extraction:
  pdf:
    enable_ocr: false           # Set to true to enable OCR
    ocr_language: "eng"         # OCR language
    min_image_size: 100         # Minimum image size in pixels

  excel:
    include_headers: true       # Include column headers
    include_empty_cells: false  # Skip empty cells

  docx:
    extract_tables: true        # NEW in v1.0.4
    extract_images: false       # DOCX images not yet supported

  pptx:
    extract_notes: true         # Extract speaker notes
    extract_images: true        # NEW in v1.0.4

# Formatter settings
formatters:
  json:
    indent: 2
    include_metadata: true

  markdown:
    include_toc: true           # Table of contents
    line_width: 80

  chunked_text:
    chunk_size: 512             # Target chunk size in tokens
    overlap: 50                 # Overlap between chunks

# Performance settings
performance:
  batch_workers: 4              # Parallel workers for batch processing
  timeout_seconds: 300          # File processing timeout
  max_memory_mb: 2048           # Memory limit

# Quality settings
quality:
  min_confidence: 0.75          # Minimum quality score (0.0-1.0)
  validate_structure: true      # Validate document structure
```

### Use Configuration File

Pass configuration file to commands:

```bash
# Single file with config
data-extract extract document.pdf --config config.yaml --format json

# Batch processing with config
data-extract batch input/ output/ --config config.yaml --workers 4
```

### View Current Configuration

```bash
data-extract config show
```

Shows active configuration for current extraction.

---

## Command Reference

### extract Command

Extract single document.

**Syntax:**
```bash
data-extract extract <file_path> [OPTIONS]
```

**Options:**

```
-f, --format TEXT           Output format: json, markdown, chunked
                            [default: json]

-o, --output PATH           Output file path
                            [default: input_name.format_extension]

-c, --config PATH           Configuration file path
                            [optional]

-v, --verbose              Show detailed output
                            [optional]

-q, --quiet                Suppress progress output
                            [optional]
```

**Examples:**

```bash
# Basic extraction
data-extract extract document.docx

# Specify output format
data-extract extract report.pdf --format markdown

# Custom output location
data-extract extract data.xlsx --output C:\Results\extracted_data.json

# With configuration and verbose output
data-extract extract presentation.pptx --config config.yaml --verbose

# Quiet mode (no progress display)
data-extract extract large_file.pdf --quiet
```

### batch Command

Process multiple documents.

**Syntax:**
```bash
data-extract batch <input_dir> <output_dir> [OPTIONS]
```

**Options:**

```
-f, --format TEXT           Output format: json, markdown, chunked
                            [default: json]

-p, --pattern TEXT          File pattern filter (e.g., *.pdf)
                            [default: *.*]

-w, --workers INTEGER       Number of parallel workers
                            [default: CPU count]

-c, --config PATH           Configuration file path
                            [optional]

-v, --verbose              Show detailed output
                            [optional]

-q, --quiet                Suppress progress output
                            [optional]
```

**Examples:**

```bash
# Process all files in folder
data-extract batch ./input_docs ./output_docs --format json

# Only PDF files
data-extract batch ./documents ./results --pattern *.pdf

# With 8 parallel workers
data-extract batch ./batch_input ./batch_output --workers 8

# Multiple output formats
data-extract batch ./docs ./out1 --format json && \
data-extract batch ./docs ./out2 --format markdown
```

### version Command

Show version information.

**Syntax:**
```bash
data-extract version [OPTIONS]
```

**Options:**

```
-v, --verbose              Show detailed information
                            [optional]
```

**Output (basic):**
```
Data Extraction Tool v1.0.4
```

**Output (verbose):**
```
Data Extraction Tool v1.0.4
Python 3.11.0
Platform: Windows 10 or Linux 5.10
Extractors: DOCX, PDF, PPTX, XLSX, TXT
Status: Production ready
```

### config Command

Manage configuration.

**Syntax:**
```bash
data-extract config show [OPTIONS]
```

**Options:**

```
show                        Display current configuration
                            [default action]
```

**Example:**
```bash
data-extract config show
```

---

## Common Workflows

### Workflow 1: Quick Document Review

1. Extract document to markdown for human review:

```bash
data-extract extract contract.pdf --format markdown --output contract_review.md
```

2. Open in text editor and review

3. Share or archive the markdown file

### Workflow 2: Batch Processing with Quality Check

1. Extract batch to JSON:

```bash
data-extract batch C:\Contracts\ C:\Extracted\ --format json --workers 4
```

2. Check output quality scores in JSON:

```bash
# View first extracted file
type C:\Extracted\contract_1.json | findstr /C:"extraction_quality"
```

3. Re-process failed files:

```bash
# If any files failed, extract individually
data-extract extract C:\Contracts\problematic.pdf --format json --verbose
```

### Workflow 3: AI Model Input Preparation

1. Extract documents in chunked format:

```bash
data-extract extract document.pdf --format chunked --output model_input.txt
```

2. Feed chunks to LLM:

```python
with open('model_input.txt', 'r') as f:
    chunks = f.read().split('=== CHUNK')
    for chunk in chunks:
        response = llm.process(chunk)
        print(response)
```

### Workflow 4: Database Import

1. Extract to JSON:

```bash
data-extract batch ./documents ./json_output --format json
```

2. Import to database:

```python
import json
import sqlite3

conn = sqlite3.connect('documents.db')
for json_file in os.listdir('./json_output'):
    with open(json_file) as f:
        data = json.load(f)
        for block in data['blocks']:
            insert_block(conn, block)
conn.commit()
```

### Workflow 5: Compliance Document Extraction

1. Extract compliance documents with metadata:

```bash
data-extract batch .\compliance_docs\ .\compliance_json\ ^
  --format json ^
  --workers 4 ^
  --pattern *.pdf
```

2. Validate extraction quality:

```bash
# Check quality scores (should be > 0.75)
data-extract extract sample.pdf --format json --verbose
```

3. Generate compliance report:

```bash
# Review extracted content and metadata
type compliance_json\sample.json | findstr /C:"quality_score"
```

---

## Troubleshooting

### Installation Issues

**Problem: "Command not found: data-extract"**

Solution:
```bash
# Verify installation
pip list | grep ai-data-extractor

# If not listed, install wheel
pip install dist\ai_data_extractor-1.0.4-py3-none-any.whl

# Try with full path
python -m cli.main extract document.pdf
```

**Problem: "ModuleNotFoundError: No module named 'python_docx'"**

Solution:
```bash
# Install dependencies
pip install python-docx>=0.8.11
pip install pypdf>=3.0.0
pip install python-pptx>=0.6.21
pip install openpyxl>=3.0.10

# Or reinstall the wheel
pip install --force-reinstall dist\ai_data_extractor-1.0.4-py3-none-any.whl
```

### Extraction Errors

**Problem: "File not found" error**

Solution:
```bash
# Check file path (use absolute paths for clarity)
data-extract extract C:\Users\YourName\Documents\file.pdf --verbose

# For Windows paths with spaces, use quotes
data-extract extract "C:\Users\Your Name\My Documents\file.pdf"
```

**Problem: "PDF extraction produces empty output"**

Solution:

PDF is image-based and needs OCR:
```bash
# Install OCR support
pip install ai-data-extractor[ocr]

# Update config.yaml
extraction:
  pdf:
    enable_ocr: true

# Try extraction again
data-extract extract image_based.pdf --config config.yaml --verbose
```

**Problem: "Excel file shows encoding error"**

Solution:
```bash
# Most common: file uses non-standard encoding
# Try extracting with verbose output to see the error
data-extract extract spreadsheet.xlsx --verbose

# Ensure file is valid Excel (.xlsx not .xls)
# Convert if needed using Excel or LibreOffice
```

**Problem: "Out of memory" during batch processing**

Solution:
```bash
# Reduce parallel workers
data-extract batch input/ output/ --workers 2

# Or process fewer files per batch
# Move some files out and process in smaller groups
```

### Output Issues

**Problem: "Output file is empty or corrupted"**

Solution:
```bash
# Check disk space
# dir C:\ to see free space

# Check file permissions
# Ensure you can write to output folder

# Try explicit output path
data-extract extract document.pdf --output C:\Temp\test.json --verbose
```

**Problem: "Unicode/special characters showing as ??? in output"**

Solution:

This is a Windows console encoding issue:

```bash
# Chcp to UTF-8 (Windows only)
chcp 65001

# Then run extraction
data-extract extract document.pdf

# To permanently fix, add to config.yaml:
extraction:
  encoding: "utf-8"
```

On Linux/Mac, UTF-8 is default.

**Problem: "JSON output is not valid JSON"**

Solution:
```bash
# Validate JSON file
# Using Python
python -m json.tool output.json

# If error, output may be truncated
# Check file size and re-extract with --verbose
```

### Performance Issues

**Problem: "Extraction is very slow"**

See [Performance Tips](#performance-tips) below.

**Problem: "Batch processing hangs on a single file"**

Solution:
```bash
# Increase timeout in config.yaml
performance:
  timeout_seconds: 600  # Default is 300

# Or extract that file individually with verbose
data-extract extract slow_file.pdf --verbose

# It may be corrupted; try processing others first
```

---

## Performance Tips

### Optimize for Speed

**1. Use Appropriate Worker Count**

```bash
# For 8-core system, use 4 workers (leave half for OS)
data-extract batch input/ output/ --workers 4
```

**2. Filter File Patterns**

```bash
# Only process PDF files instead of all files
data-extract batch input/ output/ --pattern *.pdf
```

**3. Disable Unnecessary Features**

In config.yaml:
```yaml
extraction:
  pdf:
    enable_ocr: false           # OCR is slower, disable if not needed

  pptx:
    extract_images: false       # Skip image extraction if not needed
```

### Optimize for Memory

**1. Process in Smaller Batches**

```bash
# Instead of 1000 files at once
# Process 100 files in 10 batches
for /L %i in (1,1,10) do (
  data-extract batch input_part_%i\ output_part_%i\ --workers 2
)
```

**2. Limit Chunk Size**

In config.yaml:
```yaml
formatters:
  chunked_text:
    chunk_size: 256             # Smaller chunks use less memory
```

### Typical Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Single small PDF (< 5 MB) | 2-5 sec | Depends on OCR |
| Single large PDF (50 MB) | 30-60 sec | With OCR |
| Single Excel sheet (1000 rows) | 1-2 sec | No external processing |
| Single DOCX (with tables) | 1-3 sec | v1.0.4 optimized |
| Single PPTX (50 slides) | 5-10 sec | Includes image extraction |
| Batch 100 files (4 workers) | 5-15 min | Depends on file types |

### Benchmark Your System

```bash
# Time single extraction
time data-extract extract sample.pdf

# Time batch processing
time data-extract batch input_100_files/ output/ --workers 4
```

---

## Getting Help

### Check Logs

Enable verbose output for detailed information:

```bash
data-extract extract document.pdf --verbose
```

This shows:
- Each extraction step
- Time taken for each stage
- Any warnings or issues
- Final quality score

### Verify Installation

```bash
data-extract version --verbose
```

Shows:
- Tool version
- Python version
- Available extractors
- System information

### Common Questions

**Q: What file formats are supported?**

A: DOCX, PDF, PPTX, XLSX, TXT. See `data-extract version --verbose`

**Q: Can I extract from password-protected PDFs?**

A: Not currently. You must remove protection first.

**Q: What is the file size limit?**

A: No hard limit, but performance degrades above 500 MB. Batch processing helps.

**Q: Can I use the tool programmatically in Python?**

A: Yes, it's designed for API use. See the project documentation.

**Q: Is the extracted data AI-ready?**

A: Yes, all formats are designed for LLM/ML pipelines.

**Q: How do I report a bug?**

A: Run with `--verbose` and save output. Check the main project documentation for bug report process.

---

## Version Info

**Current Version**: 1.0.4
**Release Date**: 2025-11-02
**Status**: Production Ready
**Test Coverage**: 92%
**Test Count**: 950+ passing tests

### v1.0.4 Features

- **NEW**: DOCX table extraction with full cell data
- **NEW**: PPTX image extraction with metadata
- **FIXED**: Excel multi-sheet support
- **FIXED**: PDF image metadata serialization
- **FIXED**: Batch file extension handling
- **FIXED**: System-wide table/image pipeline preservation

### Known Limitations

- DOCX image extraction (DOCX-IMAGE-001): Not yet implemented
- TXT files: Table structure not preserved (plain text format limitation)
- Some edge case tests: Pre-existing, non-critical (see gap analysis)

---

## Next Steps

1. **Start Extracting**
   - Try the quick start section
   - Extract one document to test

2. **Configure (if needed)**
   - Create config.yaml with custom settings
   - Adjust performance parameters

3. **Batch Processing (optional)**
   - Set up batch folder structure
   - Run batch extraction with appropriate workers

4. **Integration (optional)**
   - Use JSON output in your application
   - Feed chunked format to LLMs
   - Import to database

---

## Support Resources

- **Installation Issues**: Check "Installation" section
- **Extraction Problems**: Check "Troubleshooting" section
- **Slow Performance**: Check "Performance Tips" section
- **Configuration Questions**: See "Configuration" section
- **Command Help**: Run `data-extract --help` for command-line help

---

**Ready to extract? Run `data-extract version` to verify your installation.**

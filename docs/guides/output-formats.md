# Output Formats

Reference for JSON, TXT, and CSV output formats with schemas and use case guidance.

## Overview

The Data Extraction Tool produces three output formats optimized for different workflows:

| Format | Use Case | Size | Processing |
|--------|----------|------|------------|
| **JSON** | Full metadata, programmatic access | Large | Structured |
| **TXT** | LLM upload, RAG workflows | Small | Sequential |
| **CSV** | Analysis, tracking, spreadsheets | Medium | Tabular |

**Default:** All three formats are generated. Control via `--output-formats`:

```bash
# JSON only
data-extract process input.pdf --output-formats json

# TXT and CSV only
data-extract process input.pdf --output-formats txt,csv
```

## JSON Format

Full metadata with complete document structure and extraction details.

### Schema

```json
{
  "document_id": "uuid-v4",
  "filename": "example.pdf",
  "file_size": 1048576,
  "file_hash": "sha256:abc123...",
  "extraction_date": "2025-12-01T10:30:00Z",
  "processing_time_ms": 1234,

  "metadata": {
    "format": "pdf",
    "page_count": 10,
    "author": "John Doe",
    "title": "Document Title",
    "creation_date": "2025-11-01T00:00:00Z",
    "modification_date": "2025-11-15T12:00:00Z",
    "producer": "Microsoft Word",
    "custom": {}
  },

  "content": {
    "text": "Full extracted text...",
    "word_count": 5000,
    "char_count": 30000,
    "language": "en"
  },

  "extraction": {
    "extractor": "PyMuPDFExtractor",
    "ocr_used": false,
    "confidence": 0.95,
    "errors": [],
    "warnings": ["Low contrast on page 3"]
  },

  "normalization": {
    "processor": "TextNormalizer",
    "operations": [
      "whitespace_cleaning",
      "entity_standardization",
      "artifact_removal"
    ],
    "entities": {
      "urls": ["https://example.com"],
      "emails": ["user@example.com"],
      "dates": ["2025-01-01"],
      "phone_numbers": ["+1-555-0100"]
    }
  },

  "chunks": [
    {
      "chunk_id": "uuid-v4",
      "index": 0,
      "text": "Chunk text content...",
      "start_char": 0,
      "end_char": 1000,
      "word_count": 150,
      "sentence_count": 8,
      "strategy": "semantic",
      "boundary_type": "paragraph",
      "overlap_with_previous": 100,
      "metadata": {
        "heading": "Introduction",
        "page_number": 1,
        "section": "1"
      }
    }
  ],

  "semantic": {
    "enabled": true,
    "vectorizer": "TfidfVectorizer",
    "top_terms": [
      {"term": "extraction", "score": 0.45},
      {"term": "document", "score": 0.38}
    ],
    "quality_metrics": {
      "flesch_reading_ease": 65.2,
      "smog_index": 10.5,
      "avg_sentence_length": 18.3,
      "coherence_score": 0.78
    },
    "similarity": {
      "duplicate_chunks": [],
      "max_similarity": 0.42,
      "avg_similarity": 0.18
    }
  },

  "validation": {
    "status": "passed",
    "completeness": 0.98,
    "warnings": [],
    "errors": []
  }
}
```

### Field Descriptions

**Top-level fields:**
- `document_id` - Unique identifier (UUID v4)
- `filename` - Original file name
- `file_size` - File size in bytes
- `file_hash` - SHA256 hash for change detection
- `extraction_date` - ISO 8601 timestamp
- `processing_time_ms` - Total processing time

**metadata section:**
- `format` - Document format: pdf, docx, xlsx, pptx, csv
- `page_count` - Number of pages (PDF/DOCX/PPTX)
- `author` - Document author (if available)
- `title` - Document title (if available)
- `creation_date` - Original creation timestamp
- `modification_date` - Last modified timestamp
- `producer` - Software used to create document
- `custom` - Format-specific metadata

**content section:**
- `text` - Full extracted text (pre-chunking)
- `word_count` - Total word count
- `char_count` - Total character count
- `language` - Detected language code (ISO 639-1)

**extraction section:**
- `extractor` - Extractor class used
- `ocr_used` - Boolean indicating OCR usage
- `confidence` - Extraction confidence score (0.0-1.0)
- `errors` - List of extraction errors
- `warnings` - List of non-fatal warnings

**normalization section:**
- `processor` - Processor class used
- `operations` - List of normalization operations applied
- `entities` - Extracted entities by type

**chunks array:**
- `chunk_id` - Unique chunk identifier
- `index` - Sequential chunk number
- `text` - Chunk text content
- `start_char` / `end_char` - Character offsets in original text
- `word_count` - Words in chunk
- `sentence_count` - Sentences in chunk
- `strategy` - Chunking strategy used
- `boundary_type` - Boundary detection method
- `overlap_with_previous` - Overlap size in characters
- `metadata` - Chunk-specific metadata (heading, page, section)

**semantic section** (when enabled):
- `enabled` - Boolean indicating semantic analysis
- `vectorizer` - Vectorizer class used
- `top_terms` - Most significant terms with TF-IDF scores
- `quality_metrics` - Readability and quality scores
- `similarity` - Duplicate detection results

**validation section:**
- `status` - Validation status: passed, warning, failed
- `completeness` - Completeness score (0.0-1.0)
- `warnings` - Validation warnings
- `errors` - Validation errors

### Use Cases

**API Integration:**
```python
import json

with open('output.json') as f:
    doc = json.load(f)

# Access metadata
print(f"Extracted {doc['metadata']['page_count']} pages")

# Process chunks
for chunk in doc['chunks']:
    if chunk['word_count'] > 100:
        print(f"Chunk {chunk['index']}: {chunk['text'][:50]}...")
```

**Batch Analysis:**
```python
import json
from pathlib import Path

# Aggregate statistics
total_pages = 0
total_words = 0

for json_file in Path('./output').glob('*.json'):
    with open(json_file) as f:
        doc = json.load(f)
        total_pages += doc['metadata'].get('page_count', 0)
        total_words += doc['content']['word_count']

print(f"Processed {total_pages} pages, {total_words} words")
```

## TXT Format

LLM-optimized plain text for RAG workflows and context upload.

### Structure

```
Document: example.pdf
Extracted: 2025-12-01T10:30:00Z
Pages: 10 | Words: 5000 | Language: en

========================================

[Introduction]
Page 1

First paragraph of content with semantic-aware chunking.
Sentences stay together. Paragraphs preserved.

Second paragraph continues the narrative flow.

[Section 1: Background]
Page 2

Content from second section with proper heading preservation...

========================================

Extraction Metadata:
- Format: PDF
- Extractor: PyMuPDFExtractor
- Processing Time: 1.23s
- Chunks: 25
- Confidence: 95%
```

### Format Rules

**Header:**
- Document filename
- Extraction timestamp
- Key statistics (pages, words, language)
- Separator line

**Body:**
- Chunks in sequential order
- Section headings preserved in brackets
- Page numbers indicated
- Natural paragraph breaks
- No artificial line wrapping

**Footer:**
- Extraction metadata summary
- Processing details
- Quality indicators

### Use Cases

**LLM Upload:**
```bash
# Generate TXT only
data-extract process input.pdf --output-formats txt

# Upload to LLM
cat output/input.txt | llm --model gpt-4
```

**RAG Workflow:**
```python
from pathlib import Path

# Load all documents
documents = []
for txt_file in Path('./output').glob('*.txt'):
    documents.append(txt_file.read_text())

# Upload to vector database
vector_db.add_documents(documents)
```

**Context Injection:**
```python
# Load document as context
context = Path('output.txt').read_text()

prompt = f"""
Based on this document:

{context}

Answer the following question: ...
"""
```

## CSV Format

Tabular format for analysis, tracking, and spreadsheet import.

### Schema

```csv
document_id,filename,format,page_count,word_count,extraction_date,processing_time_ms,chunk_index,chunk_text,chunk_word_count,chunk_page,confidence,status,errors
uuid-v4-1,example.pdf,pdf,10,5000,2025-12-01T10:30:00Z,1234,0,"First chunk text...",150,1,0.95,success,""
uuid-v4-1,example.pdf,pdf,10,5000,2025-12-01T10:30:00Z,1234,1,"Second chunk text...",148,1,0.95,success,""
uuid-v4-1,example.pdf,pdf,10,5000,2025-12-01T10:30:00Z,1234,2,"Third chunk text...",152,2,0.95,success,""
```

### Columns

**Document-level:**
- `document_id` - Unique document identifier
- `filename` - Original file name
- `format` - Document format
- `page_count` - Total pages
- `word_count` - Total words
- `extraction_date` - ISO 8601 timestamp
- `processing_time_ms` - Processing time in milliseconds
- `confidence` - Extraction confidence score
- `status` - Processing status: success, warning, failed
- `errors` - Error messages (if any)

**Chunk-level:**
- `chunk_index` - Sequential chunk number
- `chunk_text` - Chunk text (quoted, escaped)
- `chunk_word_count` - Words in chunk
- `chunk_page` - Page number for chunk

### Use Cases

**Spreadsheet Analysis:**
```bash
# Generate CSV only
data-extract process ./docs/ --output-formats csv

# Open in Excel/Google Sheets
open output/*.csv
```

**Batch Statistics:**
```python
import pandas as pd

# Load CSV
df = pd.read_csv('output.csv')

# Aggregate by document
stats = df.groupby('filename').agg({
    'word_count': 'first',
    'processing_time_ms': 'first',
    'chunk_index': 'count'
}).rename(columns={'chunk_index': 'chunk_count'})

print(stats)
```

**Quality Tracking:**
```python
import pandas as pd

# Load batch results
df = pd.read_csv('batch_output.csv')

# Find low-confidence extractions
low_confidence = df[df['confidence'] < 0.8]
print(f"Low confidence: {len(low_confidence)} chunks")

# Find errors
errors = df[df['errors'] != '']
print(f"Errors: {len(errors)} chunks")
```

**Progress Monitoring:**
```python
import pandas as pd

# Load incremental results
df = pd.read_csv('output.csv')

# Calculate processing speed
avg_time = df['processing_time_ms'].mean()
total_docs = df['document_id'].nunique()
print(f"Processed {total_docs} docs, avg {avg_time:.0f}ms each")
```

## Format Selection

Choose format(s) based on your workflow:

### JSON

**Use when:**
- Need full metadata and structure
- Building programmatic integrations
- Require chunk-level details
- Want semantic analysis results
- Need validation information

**Don't use when:**
- File size is critical (largest format)
- Only need text content
- Working with LLMs directly

### TXT

**Use when:**
- Uploading to LLMs
- Building RAG systems
- Need human-readable output
- File size matters (smallest format)
- Want simple context injection

**Don't use when:**
- Need structured metadata
- Require chunk boundaries
- Want programmatic access
- Need quality metrics

### CSV

**Use when:**
- Analyzing batch results
- Tracking processing metrics
- Using spreadsheets
- Need tabular data
- Want to aggregate statistics

**Don't use when:**
- Need nested metadata
- Want full text (truncated in CSV)
- Require semantic analysis
- Need document structure

## Format Combinations

Common multi-format workflows:

**RAG Pipeline:**
```bash
# JSON for metadata, TXT for vectors
data-extract process ./docs/ --output-formats json,txt

# Index TXT in vector DB, store JSON metadata
```

**Quality Assurance:**
```bash
# CSV for tracking, JSON for debugging
data-extract process ./batch/ --output-formats csv,json

# Monitor CSV, investigate issues in JSON
```

**End-User Delivery:**
```bash
# TXT for reading, CSV for analysis
data-extract process ./reports/ --output-formats txt,csv

# Deliver TXT to users, CSV to analysts
```

## Output File Naming

Output files use consistent naming:

```
<input_basename>.<format>
```

**Examples:**
- `report.pdf` → `report.json`, `report.txt`, `report.csv`
- `document.docx` → `document.json`, `document.txt`, `document.csv`
- `data.xlsx` → `data.json`, `data.txt`, `data.csv`

**Directory structure:**
```
output/
├── report.json
├── report.txt
├── report.csv
├── document.json
├── document.txt
└── document.csv
```

## Configuration

Control output via config file:

```yaml
output:
  formats:
    - json
    - txt
    - csv

  json:
    indent: 2
    ensure_ascii: false
    include_metadata: true

  txt:
    include_header: true
    include_footer: true
    max_line_length: 100

  csv:
    delimiter: ","
    quoting: minimal
    encoding: utf-8
```

Or via CLI:

```bash
data-extract process input.pdf \
  --output-formats json,txt \
  --json-indent 4 \
  --txt-max-line-length 80
```

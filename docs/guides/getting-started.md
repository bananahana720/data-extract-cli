# Getting Started

Quick start guide for installing and using the Data Extraction Tool.

## Prerequisites

**Required:**
- Python 3.11 or higher
- uv package manager (recommended) or pip

**Optional:**
- spaCy model `en_core_web_md` (required for semantic chunking)
- 4GB RAM minimum, 8GB recommended for large documents

## Installation

### Using uv (Recommended)

```bash
# Install uv if not already installed
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Install spaCy model (required for chunking)
python -m spacy download en_core_web_md
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
pip install -e ".[dev]"

# Install spaCy model
python -m spacy download en_core_web_md
```

### Verify Installation

```bash
# Check CLI is available
data-extract --help

# Validate spaCy model
python -m spacy validate
```

## First Extraction

Process a single document:

```bash
data-extract process input.pdf --output-dir ./output
```

This command:
1. Extracts text from the PDF
2. Normalizes content (cleaning, entity standardization)
3. Chunks text using semantic boundaries
4. Enriches with metadata
5. Outputs JSON, TXT, and CSV formats

**Output files:**
- `output/input.json` - Full metadata and chunks
- `output/input.txt` - LLM-optimized plain text
- `output/input.csv` - Analysis-ready tabular data

## Common Workflows

### Batch Processing

Process all documents in a directory:

```bash
data-extract process ./documents/ --output-dir ./output --recursive
```

Options:
- `--recursive` - Include subdirectories
- `--patterns "*.pdf,*.docx"` - Filter by file types
- `--batch-size 10` - Process files in batches

### Incremental Processing

Skip already-processed files:

```bash
data-extract process ./documents/ --output-dir ./output --incremental
```

Uses checksums to detect changed files. Re-processes only new or modified documents.

### Semantic Analysis

Enable advanced semantic features:

```bash
data-extract process input.pdf --output-dir ./output \
  --enable-semantic \
  --similarity-threshold 0.85
```

Adds:
- TF-IDF vectorization
- Document similarity scoring
- Quality metrics (readability, coherence)
- Topic extraction

### Format-Specific Extraction

Extract without full pipeline:

```bash
# Extract only (no normalization/chunking)
data-extract extract input.pdf --output-format json

# Retry failed extractions
data-extract retry ./failed_docs/ --output-dir ./output
```

### Validation

Verify extraction quality:

```bash
# Validate outputs
data-extract validate ./output/

# Check specific file
data-extract validate ./output/input.json --verbose
```

### Progress Monitoring

Check batch processing status:

```bash
data-extract status ./output/
```

Shows:
- Files processed vs total
- Success/failure counts
- Average processing time
- Error summary

## Configuration

### Using Presets

Quick workflows with preset configurations:

```bash
# LLM upload optimization
data-extract process input.pdf --preset llm-upload

# High-quality extraction
data-extract process input.pdf --preset high-quality

# Fast batch processing
data-extract process ./docs/ --preset fast-batch
```

**Available presets:**
- `llm-upload` - Optimized for RAG workflows
- `high-quality` - Maximum accuracy, slower
- `fast-batch` - Speed over precision
- `semantic-analysis` - Full semantic enrichment

### Custom Configuration

Create `.data-extract.yaml` in project directory:

```yaml
extraction:
  ocr_fallback: true
  confidence_threshold: 0.7

chunking:
  strategy: semantic
  max_chunk_size: 1000
  overlap: 100

output:
  formats:
    - json
    - txt
  include_metadata: true
```

### Configuration Cascade

Configuration merges from 6 layers (highest priority first):

1. CLI arguments (highest)
2. Environment variables
3. Project config (`.data-extract.yaml`)
4. User config (`~/.data-extract.yaml`)
5. Preset configurations
6. System defaults (lowest)

View active configuration:

```bash
data-extract config show
```

## Session Management

### Session Recovery

Resume interrupted sessions:

```bash
# View active sessions
data-extract session list

# Resume specific session
data-extract session resume SESSION_ID

# Clean old sessions
data-extract session cleanup --days 7
```

### Cache Management

Manage extraction cache:

```bash
# View cache statistics
data-extract cache stats

# Clear cache
data-extract cache clear

# Clear cache for specific files
data-extract cache clear input.pdf
```

## Environment Variables

Configure via environment:

```bash
# Logging level
export DATA_EXTRACT_LOG_LEVEL=DEBUG

# Cache directory
export DATA_EXTRACT_CACHE_DIR=~/.cache/data-extract

# Disable progress bars (CI environments)
export DATA_EXTRACT_NO_PROGRESS=1

# Max workers for parallel processing
export DATA_EXTRACT_MAX_WORKERS=4
```

## Next Steps

**Learn more:**
- [CLI Reference](cli-reference.md) - Complete command documentation
- [Output Formats](output-formats.md) - Format schemas and use cases
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

**Advanced usage:**
- See `docs/architecture/index.md` for pipeline internals
- See `docs/ux-design-directions.html` for CLI design principles
- See `docs/automation-guide.md` for scripting and automation

## Quick Reference

```bash
# Single file
data-extract process input.pdf

# Batch with semantic analysis
data-extract process ./docs/ --enable-semantic --recursive

# Resume failed batch
data-extract retry ./docs/ --output-dir ./output

# Validate outputs
data-extract validate ./output/

# Check status
data-extract status ./output/

# Clean cache
data-extract cache clear
```

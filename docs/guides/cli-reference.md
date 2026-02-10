# CLI Reference

Complete reference for all `data-extract` commands, options, and exit codes.

## Overview

The Data Extraction Tool uses a git-style command structure:

```bash
data-extract <command> [options] [arguments]
```

**Global options** (available for all commands):
- `--verbose`, `-v` - Enable verbose output (repeatable: `-vv`, `-vvv`)
- `--learn` - Extended help with examples and best practices
- `--help`, `-h` - Show help message

**Output control:**
- `--quiet`, `-q` - Suppress non-error output
- `--no-progress` - Disable progress bars (CI environments)

## Commands

### process

Process documents through the full extraction pipeline.

**Usage:**

```bash
data-extract process INPUT [OPTIONS]
```

**Arguments:**
- `INPUT` - File path or directory to process

**Options:**

**Output:**
- `--output-dir PATH`, `-o PATH` - Output directory (default: `./output`)
- `--output-formats FORMAT[,FORMAT...]` - Output formats: json, txt, csv (default: all)

**Extraction:**
- `--ocr-fallback / --no-ocr-fallback` - Enable OCR for images/scanned PDFs (default: enabled)
- `--confidence-threshold FLOAT` - Minimum OCR confidence (0.0-1.0, default: 0.7)

**Chunking:**
- `--chunk-strategy STRATEGY` - Chunking strategy: semantic, fixed, sentence (default: semantic)
- `--max-chunk-size INT` - Maximum chunk size in characters (default: 1000)
- `--overlap INT` - Overlap between chunks in characters (default: 100)

**Semantic:**
- `--enable-semantic / --disable-semantic` - Enable semantic analysis (default: disabled)
- `--similarity-threshold FLOAT` - Similarity threshold for duplicate detection (0.0-1.0, default: 0.85)

**Batch Processing:**
- `--recursive`, `-r` - Process directories recursively
- `--patterns PATTERN[,PATTERN...]` - File patterns to include (default: `*.pdf,*.docx,*.xlsx,*.pptx,*.csv`)
- `--exclude PATTERN[,PATTERN...]` - Patterns to exclude
- `--batch-size INT` - Batch size for parallel processing (default: 10)
- `--incremental` - Skip already-processed files (checksums)
- `--max-workers INT` - Maximum parallel workers (default: CPU count)

**Presets:**
- `--preset NAME` - Load preset configuration: llm-upload, high-quality, fast-batch, semantic-analysis

**Examples:**

```bash
# Single file with default settings
data-extract process document.pdf

# Directory with semantic analysis
data-extract process ./documents/ --enable-semantic --recursive

# Batch processing with preset
data-extract process ./archive/ --preset fast-batch --batch-size 50

# Incremental processing
data-extract process ./docs/ --incremental --output-dir ./output

# Custom chunking
data-extract process report.docx --chunk-strategy fixed --max-chunk-size 500
```

**Exit codes:**
- `0` - All files processed successfully
- `1` - Partial success (some files failed)
- `2` - Complete failure
- `3` - Configuration error

### extract

Extract raw content without normalization or chunking.

**Usage:**

```bash
data-extract extract INPUT [OPTIONS]
```

**Arguments:**
- `INPUT` - File path to extract

**Options:**
- `--output-format FORMAT` - Output format: json, txt (default: json)
- `--output-file PATH`, `-o PATH` - Output file path (default: stdout)
- `--ocr-fallback / --no-ocr-fallback` - Enable OCR fallback (default: enabled)

**Examples:**

```bash
# Extract to JSON
data-extract extract document.pdf --output-file output.json

# Extract to plain text
data-extract extract scan.pdf --output-format txt --ocr-fallback

# Extract to stdout
data-extract extract report.docx
```

**Exit codes:**
- `0` - Extraction successful
- `2` - Extraction failed
- `3` - Invalid options

### retry

Retry failed extractions from a previous batch.

**Usage:**

```bash
data-extract retry INPUT [OPTIONS]
```

**Arguments:**
- `INPUT` - Directory containing failed files

**Options:**
- `--output-dir PATH`, `-o PATH` - Output directory (default: same as input)
- `--session-id ID` - Resume specific session
- `--max-retries INT` - Maximum retry attempts per file (default: 3)
- `--backoff-factor FLOAT` - Exponential backoff multiplier (default: 2.0)

**Examples:**

```bash
# Retry all failed files
data-extract retry ./failed_docs/ --output-dir ./output

# Resume specific session
data-extract retry ./docs/ --session-id abc123

# Aggressive retry strategy
data-extract retry ./docs/ --max-retries 5 --backoff-factor 1.5
```

**Exit codes:**
- `0` - All retries successful
- `1` - Some retries failed
- `2` - All retries failed

### validate

Validate extraction outputs for completeness and quality.

**Usage:**

```bash
data-extract validate INPUT [OPTIONS]
```

**Arguments:**
- `INPUT` - File or directory to validate

**Options:**
- `--format FORMAT` - Expected format: json, txt, csv (default: auto-detect)
- `--strict` - Enable strict validation (fail on warnings)
- `--report-file PATH` - Save validation report to file

**Examples:**

```bash
# Validate single file
data-extract validate output.json

# Validate directory
data-extract validate ./output/ --verbose

# Strict validation with report
data-extract validate ./output/ --strict --report-file validation.txt
```

**Exit codes:**
- `0` - Validation passed
- `1` - Warnings found (non-strict)
- `2` - Validation failed

### status

Show processing status and statistics.

**Usage:**

```bash
data-extract status INPUT [OPTIONS]
```

**Arguments:**
- `INPUT` - Output directory to analyze

**Options:**
- `--format FORMAT` - Output format: table, json (default: table)
- `--summary-only` - Show only summary statistics

**Examples:**

```bash
# Show full status
data-extract status ./output/

# JSON output for automation
data-extract status ./output/ --format json

# Quick summary
data-extract status ./output/ --summary-only
```

**Output includes:**
- Total files processed
- Success/failure counts
- Average processing time
- Format distribution
- Error summary

**Exit codes:**
- `0` - Status retrieved successfully

### semantic

Analyze semantic features of extracted documents.

**Usage:**

```bash
data-extract semantic INPUT [OPTIONS]
```

**Arguments:**
- `INPUT` - File or directory of JSON outputs

**Options:**
- `--similarity-threshold FLOAT` - Similarity threshold (0.0-1.0, default: 0.85)
- `--output-file PATH`, `-o PATH` - Save analysis results
- `--format FORMAT` - Output format: json, table (default: table)

**Examples:**

```bash
# Analyze single document
data-extract semantic output.json

# Analyze document set
data-extract semantic ./output/ --similarity-threshold 0.9

# Export analysis
data-extract semantic ./output/ --output-file analysis.json --format json
```

**Output includes:**
- TF-IDF top terms
- Document similarity matrix
- Quality metrics (readability, coherence)
- Topic distribution

**Exit codes:**
- `0` - Analysis complete
- `2` - Analysis failed
- `3` - Invalid inputs

### cache

Manage extraction cache.

**Usage:**

```bash
data-extract cache <subcommand> [OPTIONS]
```

**Subcommands:**

**stats** - Show cache statistics:

```bash
data-extract cache stats
```

**clear** - Clear cache:

```bash
# Clear all cache
data-extract cache clear

# Clear specific files
data-extract cache clear document.pdf report.docx

# Clear cache older than N days
data-extract cache clear --older-than 30
```

**Options:**
- `--older-than DAYS` - Clear cache older than N days

**Examples:**

```bash
# View cache size and hit rate
data-extract cache stats

# Clear old cache entries
data-extract cache clear --older-than 7

# Clear specific document cache
data-extract cache clear input.pdf
```

**Exit codes:**
- `0` - Cache operation successful

### config

Manage configuration settings.

**Usage:**

```bash
data-extract config <subcommand> [OPTIONS]
```

**Subcommands:**

**show** - Display active configuration:

```bash
# Show all settings
data-extract config show

# Show specific section
data-extract config show extraction
data-extract config show chunking
data-extract config show output
```

**validate** - Validate configuration files:

```bash
# Validate project config
data-extract config validate

# Validate specific file
data-extract config validate --file custom-config.yaml
```

**init** - Create template configuration:

```bash
# Create project config
data-extract config init

# Create user config
data-extract config init --user
```

**Options:**
- `--file PATH` - Configuration file to validate
- `--user` - Use user config directory (`~/.data-extract.yaml`)

**Examples:**

```bash
# View current settings
data-extract config show

# Create project config template
data-extract config init

# Validate custom config
data-extract config validate --file .data-extract.yaml
```

**Exit codes:**
- `0` - Config operation successful
- `3` - Configuration error

### session

Manage processing sessions.

**Usage:**

```bash
data-extract session <subcommand> [OPTIONS]
```

**Subcommands:**

**list** - List active and completed sessions:

```bash
data-extract session list

# Show only active sessions
data-extract session list --active

# Show only failed sessions
data-extract session list --failed
```

**resume** - Resume interrupted session:

```bash
data-extract session resume SESSION_ID
```

**cleanup** - Remove old sessions:

```bash
# Clean sessions older than 7 days
data-extract session cleanup --days 7

# Clean failed sessions only
data-extract session cleanup --failed-only
```

**Options:**
- `--active` - Filter to active sessions
- `--failed` - Filter to failed sessions
- `--days INT` - Age threshold for cleanup (default: 7)
- `--failed-only` - Clean only failed sessions

**Examples:**

```bash
# View all sessions
data-extract session list

# Resume interrupted batch
data-extract session resume abc123

# Clean old sessions
data-extract session cleanup --days 30
```

**Exit codes:**
- `0` - Session operation successful
- `2` - Session not found

## Global Configuration

### Configuration Files

Configuration cascade (highest priority first):

1. CLI arguments
2. Environment variables
3. Project config (`.data-extract.yaml`)
4. User config (`~/.data-extract.yaml`)
5. Preset configurations
6. System defaults

**Example project config:**

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

semantic:
  enabled: false
  similarity_threshold: 0.85
```

### Environment Variables

Override settings via environment:

```bash
# Logging
export DATA_EXTRACT_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR

# Cache
export DATA_EXTRACT_CACHE_DIR=~/.cache/data-extract

# Performance
export DATA_EXTRACT_MAX_WORKERS=4
export DATA_EXTRACT_NO_PROGRESS=1  # Disable progress bars

# Session
export DATA_EXTRACT_SESSION_DIR=~/.local/share/data-extract/sessions
```

## Exit Codes

All commands use consistent exit codes:

- **0** - Success (all operations completed successfully)
- **1** - Partial success (some items failed in batch operations)
- **2** - Failure (operation failed)
- **3** - Configuration error (invalid options or config)

**Automation example:**

```bash
data-extract process ./docs/ --output-dir ./output
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "All files processed successfully"
elif [ $EXIT_CODE -eq 1 ]; then
  echo "Some files failed - check logs"
  data-extract retry ./docs/ --output-dir ./output
elif [ $EXIT_CODE -eq 2 ]; then
  echo "Processing failed completely"
  exit 1
elif [ $EXIT_CODE -eq 3 ]; then
  echo "Configuration error - check settings"
  exit 1
fi
```

## Shell Completion

Enable tab completion:

```bash
# Bash
eval "$(_DATA_EXTRACT_COMPLETE=bash_source data-extract)"

# Zsh
eval "$(_DATA_EXTRACT_COMPLETE=zsh_source data-extract)"

# Fish
_DATA_EXTRACT_COMPLETE=fish_source data-extract | source
```

Add to shell config (`.bashrc`, `.zshrc`, `config.fish`) for persistence.

## Learn Mode

Extended help with examples:

```bash
# Command-specific examples
data-extract process --learn
data-extract semantic --learn

# Show all examples
data-extract --learn
```

Learn mode includes:
- Common usage patterns
- Best practices
- Performance tips
- Troubleshooting hints

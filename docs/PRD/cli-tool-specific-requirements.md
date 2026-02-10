# CLI Tool Specific Requirements

**Context:** This is a CLI-first tool designed for power users who need batch processing, scriptability, and automation. The current implementation is functional but cumbersome—these requirements define the improved experience.

## Command Structure & Interface

**Pipeline-Style Architecture:**

Commands should support **pipeline chaining** with delimiter-style composition:

```bash
# Basic processing with defaults
data-extract ./input-files | normalize | chunk | output ./processed

# Custom pipeline with options
data-extract ./audit-reports --type pdf,docx | \
  normalize --entity-types risk,control,policy | \
  chunk --size 512 --overlap 0.15 | \
  semantic --similarity | \
  output --format json,txt,csv ./results

# Single-step execution (when pipeline not needed)
data-extract process ./files --output ./processed --format json
```

**Pipeline Component Design:**
- Each component (normalize, chunk, semantic, output) is modular and optional
- Components can be reordered based on needs
- Default pipeline executes if no components specified
- Components pass structured data (not just text) through the pipeline

**Command Categories:**

1. **Processing Commands** (Most Common):
   - `data-extract process` - Full pipeline with defaults
   - `data-extract quick` - Fast processing for ChatGPT upload (optimized defaults)

2. **Analysis Commands:**
   - `data-extract similarity` - Find related documents/chunks
   - `data-extract validate` - Quality check outputs
   - `data-extract stats` - Generate processing statistics

3. **Utility Commands:**
   - `data-extract config` - Manage configuration
   - `data-extract info` - Inspect processed outputs
   - `data-extract clean` - Clear cached/temp files

## Configuration System

**Three-Tier Configuration** (with precedence: CLI flags > env vars > config file > defaults):

**1. Config File (YAML/JSON):**
```yaml
# ~/.data-extract/config.yaml or ./data-extract.config.yaml
defaults:
  chunk_size: 512
  chunk_overlap: 0.15
  output_formats: [json, txt]
  entity_types: [process, risk, control, regulation, policy, issue]

processing:
  normalize: true
  semantic_analysis: true
  ocr_confidence_threshold: 0.95

output:
  directory: ./processed
  organization: by_document  # or: by_entity, flat
```

**2. Environment Variables:**
```bash
export DATA_EXTRACT_OUTPUT_DIR=./processed
export DATA_EXTRACT_CHUNK_SIZE=512
export DATA_EXTRACT_VERBOSE=true
```

**3. Interactive Prompts:**
- When required options are missing, prompt interactively
- Option to save responses to config file: "Save these settings? (y/n)"
- Skip prompts with `--no-interactive` flag for scripting

**Configuration Management:**
```bash
# Initialize config file with defaults
data-extract config init

# Show current configuration (merged from all sources)
data-extract config show

# Edit config file in default editor
data-extract config edit

# Validate config file
data-extract config validate
```

## Output & Feedback

**Progress Indicators:**

**Batch Processing Progress Bar:**
```
Processing: [████████████░░░░░░░░] 65% (13/20 files)
Current: audit-report-2024.pdf
Elapsed: 2m 34s | Remaining: ~1m 15s
```

**Verbose Mode Levels:**
```bash
# Default (summary only)
data-extract process ./files

# Verbose (-v): Show per-file progress
data-extract process ./files -v

# Very verbose (-vv): Show component-level details
data-extract process ./files -vv

# Debug (-vvv): Full diagnostic output
data-extract process ./files -vvv

# Quiet mode (-q): Errors only
data-extract process ./files -q
```

**Summary Statistics (Always Shown at End):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files Processed: 18/20 (2 errors)
Total Chunks: 1,247
Output Formats: JSON, TXT, CSV

Quality Metrics:
  - Avg OCR Confidence: 96.3%
  - Flagged Chunks: 12 (low quality)
  - Entities Identified: 342

Time Elapsed: 3m 49s
Output Location: ./processed/

Errors (see log for details):
  - scanned-image-001.pdf: OCR confidence below threshold
  - corrupted-file.docx: Unable to extract text

Next Steps:
  - Review flagged chunks: data-extract info --flagged
  - Validate outputs: data-extract validate ./processed
  - Find similar docs: data-extract similarity ./processed
```

**Real-Time Streaming:**
- Progress bar updates in real-time during batch processing
- Verbose output streams as processing occurs (not buffered)
- Errors displayed immediately but don't halt processing

---

## V1.0 Actual Implementation (December 2025)

The implemented command structure evolved from the original design to better align with Typer/Python CLI patterns and user feedback.

### Command Structure (9 Commands)

```
data-extract
├── process    # Full pipeline execution (FR-6.1)
├── extract    # Extraction only (FR-1)
├── retry      # Resume failed/interrupted sessions
├── validate   # Pre-flight validation checks (FR-4.2)
├── status     # Corpus sync detection (FR-6.4)
├── semantic   # Semantic analysis suite (FR-5)
│   ├── tfidf      # TF-IDF vectorization
│   ├── similarity # Document similarity
│   ├── lsa        # Latent Semantic Analysis
│   └── cluster    # Semantic clustering
├── cache      # Cache management operations
├── config     # Configuration management (FR-6.3)
└── session    # Session state operations
```

### Configuration System (6-Layer Cascade)

The original 3-tier precedence was expanded to a more flexible 6-layer cascade:

| Layer | Source | Example |
|-------|--------|---------|
| 1 | CLI flags | `--chunk-size 512` |
| 2 | Environment variables | `DATA_EXTRACT_CHUNK_SIZE=512` |
| 3 | Project config | `./.data-extract.yaml` |
| 4 | User config | `~/.config/data-extract/config.yaml` |
| 5 | Preset configurations | `--preset quality` |
| 6 | Built-in defaults | Hard-coded values |

### Rich Terminal UI

Beyond basic progress indicators, V1.0 implements a full Rich terminal experience:
- **Progress bars** with percentage, file count, elapsed/remaining time
- **Panels** for structured information display
- **Tables** for data presentation
- **Trees** for hierarchical output
- **Color-coded** status messages and error highlighting

### Learning Mode

The `--learn` flag provides educational explanations during semantic analysis operations, helping users understand TF-IDF, LSA, and similarity concepts.

## Error Handling & Resilience

**Batch Processing Error Strategy:**

**Continue on Error (Default Behavior):**
- Process all files in batch even when individual files fail
- Collect errors and display summary at end
- Write detailed errors to log file
- Exit code reflects whether any errors occurred (0 = success, 1 = partial failure, 2 = complete failure)

**Error Categorization:**
```
CRITICAL: Configuration invalid, cannot proceed
ERROR: File processing failed (continue batch)
WARNING: Quality threshold not met (continue processing)
INFO: Processing decisions logged
```

**Error Reporting:**
```bash
# Errors shown in summary
Errors (2):
  1. file.pdf - OCR confidence 87% (threshold: 95%)
     → Suggestion: Review ./processed/flagged/file.pdf manually

  2. corrupted.docx - Unable to extract text
     → Suggestion: Verify file is not corrupted, try opening in Word

# Detailed error log
See: ./processed/.logs/processing-2025-11-08.log
```

**Recovery Options:**
```bash
# Retry only failed files
data-extract retry ./processed/.logs/processing-2025-11-08.log

# Process with lower quality threshold
data-extract process ./failed-files --ocr-threshold 0.85

# Skip quality checks (use with caution)
data-extract process ./files --no-validate
```

## Optimized Workflows (Most Common Use Cases)

**Use Case 1: Process with Defaults**
```bash
# Simplest command - process all files with default settings
data-extract process ./audit-files

# Equivalent to:
# data-extract ./audit-files | normalize | chunk | output ./processed
```

**Use Case 2: Custom Chunking for ChatGPT**
```bash
# Quick command optimized for ChatGPT custom GPT upload
data-extract quick ./files --chatgpt

# Equivalent to:
# data-extract ./files | normalize | chunk --size 256 --format txt | output ./chatgpt-ready
```

**Preset Configurations:**
```bash
# Use named presets for common scenarios
data-extract process ./files --preset chatgpt
data-extract process ./files --preset knowledge-graph
data-extract process ./files --preset high-accuracy
```

## CLI-Specific Non-Functional Requirements

**Performance:**
- Process 100 mixed-format files in <10 minutes on typical workstation
- Progress feedback updates at least every 2 seconds
- Minimal memory footprint (streaming processing, not loading all files into RAM)

**Usability:**
- Helpful error messages with actionable suggestions
- `--help` flag for every command with examples
- Auto-completion support for bash/zsh (optional enhancement)
- Clear distinction between user errors and system errors

**Scriptability:**
- All commands support non-interactive mode (`--no-interactive`)
- Consistent exit codes (0=success, 1=partial failure, 2=failure)
- Machine-readable output option (`--output-format json`)
- Silent mode for cron jobs (`-q`)

**Discoverability:**
- `data-extract --help` shows common workflows
- `data-extract examples` shows real-world usage patterns
- Suggest next commands in output (e.g., "Next: data-extract validate ./processed")

---

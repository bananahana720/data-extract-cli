# Data Extraction Tool UX Design Specification

_Created on 2025-11-25 by andrew_
_Generated using BMad Method - Create UX Design Workflow v1.0_

---

## Executive Summary

**Data Extraction Tool** is an enterprise document processing pipeline for RAG workflows that transforms messy corporate audit documents into AI-optimized outputs. The tool embodies a **"Tool as Teacher"** philosophy—every interaction builds user understanding of semantic analysis, NLP, and AI systems while delivering production-grade document processing.

**Core Vision:** A self-explanatory, learning-oriented CLI that grows with the user—from novice auditor to AI science professional—through layered communication, smart defaults, and quality-driven intelligence.

**Dual Identity Architecture:**
- **Enterprise Mode** - Constrained, deterministic, Python-only processing (default)
- **Hobbyist Mode** - Experimental, Ollama-integrated, transformer-enabled exploration

**Value Proposition:** 98.5% cost reduction in document processing ($1,000 → $15 per 10k docs) through intelligent classical NLP pre-filtering before LLM operations.

---

## 1. Design System Foundation

### 1.1 Design System Choice

**Primary Framework: Typer + Rich**

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **CLI Framework** | Typer | Type-safe, modern Python CLI with automatic help generation |
| **Terminal Formatting** | Rich | Colored output, tables, progress bars, panels, markdown rendering |
| **Interactive Elements** | InquirerPy | File explorer navigation, multi-select, confirmations |
| **TUI Applications** | Textual (future) | Full terminal UI for dashboard/visualization modes |

**Design System Principles:**

1. **Progressive Disclosure** - Simple by default, complexity available on demand
2. **Consistent Visual Language** - Standardized colors, icons, formatting across all commands
3. **Accessibility First** - NO_COLOR support, screen reader compatibility, Unicode fallbacks
4. **Self-Documenting** - Every command teaches through contextual help and examples

**Component Library Strategy:**

| Component | Source | Usage |
|-----------|--------|-------|
| Progress Bars | Rich | Long-running operations, batch processing |
| Tables | Rich | Results display, metrics, comparisons |
| Panels | Rich | Grouped information, status summaries |
| Trees | Rich | File structure, pipeline visualization |
| Prompts | InquirerPy | User input, confirmations, selections |
| Spinners | Rich | Brief operations, loading states |

---

## 2. Core User Experience

### 2.1 Defining Experience

**The ONE Thing:** "Process document batches through semantic analysis, getting clean RAG-ready outputs with quality metrics visibility—while learning how it all works."

**Experience Pillars:**

| Pillar | Description | Implementation |
|--------|-------------|----------------|
| **Trust** | Users trust the tool won't waste time or break data | Pre-flight validation, preview mode, progressive saves |
| **Learning** | Every operation teaches something | Layered explanations, quality insights, "why" messages |
| **Efficiency** | Minimal steps for common workflows | Smart defaults, "shut up and go" presets, repeat-last |
| **Control** | Users always know what's happening | Clear feedback, cancellation, undo capability |

**Core Interaction Pattern:**

```
┌─────────────────────────────────────────────────────────────┐
│  data-extract                                               │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   SELECT    │ →  │  VALIDATE   │ →  │   PROCESS   │     │
│  │   Files     │    │  Pre-flight │    │   Pipeline  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         ↓                  ↓                  ↓             │
│  File explorer      Config check       Progress display     │
│  Glob patterns      Quality preview    Incremental saves    │
│  Drag & drop        Fix suggestions    Quality metrics      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Novel UX Patterns

**Pattern 1: Pre-flight Validation**
Before any batch operation, the tool inspects files, validates configuration, and shows expected outcomes. Users can catch issues before wasting time.

```
╭─ Pre-flight Check ──────────────────────────────────────────╮
│ Files: 47 documents (PDF: 32, DOCX: 12, XLSX: 3)           │
│ Estimated time: ~2 minutes                                  │
│ Output: ./output/2025-11-25/                               │
│                                                             │
│ ⚠ 3 files may have issues:                                 │
│   • report-q3.pdf - Low OCR confidence expected            │
│   • data.xlsx - 15 sheets detected (large file)            │
│   • notes.docx - No text content found                     │
│                                                             │
│ [Continue] [Preview First] [Edit Selection] [Cancel]       │
╰─────────────────────────────────────────────────────────────╯
```

**Pattern 2: Quality-Driven Suggestions**
After processing, quality metrics drive contextual recommendations:

```
╭─ Quality Insights ──────────────────────────────────────────╮
│ ✓ 44/47 files processed successfully                       │
│                                                             │
│ 📊 Quality Distribution:                                    │
│   Excellent (>90): ████████████████░░░░ 34 files           │
│   Good (70-90):    ████░░░░░░░░░░░░░░░░  7 files           │
│   Needs Review:    ███░░░░░░░░░░░░░░░░░  3 files           │
│                                                             │
│ 💡 Suggestion: 12 files have similar content.              │
│    Run `data-extract dedupe` to reduce redundancy.         │
│                                                             │
│ 📖 Learn more: Semantic similarity uses TF-IDF vectors     │
│    to identify documents with overlapping concepts.        │
│    [Press 'L' for full explanation]                        │
╰─────────────────────────────────────────────────────────────╯
```

**Pattern 3: Layered Help System**

| Level | Trigger | Content |
|-------|---------|---------|
| **Tooltip** | `?` after any term | One-line definition |
| **Cheat Sheet** | `--help` | Command syntax + common examples |
| **Deep Dive** | `--explain` | Full concept explanation with examples |
| **Tutorial** | `--tutorial` | Interactive walkthrough with sample data |

---

## 3. Visual Foundation

### 3.1 Color System

**Terminal Color Palette:**

| Semantic | Color | ANSI | Usage |
|----------|-------|------|-------|
| **Success** | Green | `[green]` | Completed operations, passing checks |
| **Error** | Red | `[red]` | Failures, blocking issues |
| **Warning** | Yellow | `[yellow]` | Cautions, non-blocking issues |
| **Info** | Blue | `[blue]` | Informational, status updates |
| **Accent** | Cyan | `[cyan]` | Commands, file paths, highlights |
| **Muted** | Dim | `[dim]` | Secondary info, timestamps |
| **Learning** | Magenta | `[magenta]` | Educational content, insights |

**Accessibility Considerations:**
- Full `NO_COLOR` environment variable support
- ASCII fallbacks for Unicode symbols
- High contrast mode for visibility
- Screen reader compatible output structure

**HTML Report Theme:**

```css
/* Professional Clean Theme */
--primary: #2563eb;      /* Blue - actions, links */
--success: #16a34a;      /* Green - positive metrics */
--warning: #ca8a04;      /* Amber - cautions */
--error: #dc2626;        /* Red - failures */
--background: #f8fafc;   /* Light gray */
--surface: #ffffff;      /* White cards */
--text: #1e293b;         /* Dark slate */
--muted: #64748b;        /* Gray text */
```

**Interactive Visualizations:**

- Color Theme Explorer: [ux-color-themes.html](./ux-color-themes.html)

---

## 4. Design Direction

### 4.1 Chosen Design Approach

**Primary: Git-Style Subcommands with Rich Feedback**

The CLI follows a familiar subcommand pattern (like git, docker, npm) but with rich visual feedback and progressive disclosure.

**Command Structure:**

```bash
data-extract <command> [subcommand] [options] [files...]

# Core commands
data-extract extract    # Document extraction
data-extract analyze    # Semantic analysis
data-extract process    # Full pipeline
data-extract report     # Generate reports

# Utility commands
data-extract config     # Configuration management
data-extract cache      # Cache operations
data-extract validate   # Pre-flight checks
```

**Interaction Modes:**

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Express** | All args provided | Execute immediately with progress |
| **Guided** | No args / `--interactive` | Wizard-style prompts |
| **Preview** | `--dry-run` | Show what would happen |
| **Verbose** | `-v` / `-vv` / `-vvv` | Increasing detail levels |
| **Quiet** | `-q` | Minimal output, machine-parseable |

**Example Sessions:**

```bash
# Express mode - power user
$ data-extract process ./docs/*.pdf --output ./clean/ --format json

# Guided mode - new user
$ data-extract process
? Select files to process: [Use arrows, space to select]
  ◯ quarterly-report.pdf
  ◉ audit-findings.docx
  ◉ financial-data.xlsx

? Choose output format:
  ● JSON (RAG-optimized)
  ○ Plain Text
  ○ CSV (tabular)

# Preview mode - cautious user
$ data-extract process ./docs/ --dry-run
Would process 47 files:
  PDF: 32 files → Extract text, normalize, chunk
  DOCX: 12 files → Extract text, preserve structure
  XLSX: 3 files → Extract tables, convert to text
Estimated time: ~2 minutes
Output: ./output/2025-11-25/
```

**Interactive Mockups:**

- Design Direction Showcase: [ux-design-directions.html](./ux-design-directions.html)

---

## 5. User Journey Flows

### 5.1 Critical User Paths

#### Journey 1: First-Time Setup (Novice)

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRY: User runs `data-extract` for first time             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Welcome & Mode Selection                                │
│     ┌──────────────────────────────────────────────────┐   │
│     │ Welcome to Data Extraction Tool!                 │   │
│     │                                                   │   │
│     │ How would you like to use this tool?             │   │
│     │ ● Enterprise Mode (recommended)                  │   │
│     │   Fast, deterministic, no external dependencies  │   │
│     │ ○ Hobbyist Mode                                  │   │
│     │   Experimental features, Ollama integration      │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  2. Quick Tutorial Offer                                    │
│     "Would you like a 2-minute walkthrough? [Y/n]"         │
│                                                             │
│  3. Sample Processing                                       │
│     Process included sample files to see the tool work     │
│                                                             │
│  4. Success & Next Steps                                    │
│     Show results, explain what happened, suggest next      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ EXIT: User understands basics, config saved                 │
└─────────────────────────────────────────────────────────────┘
```

#### Journey 2: Batch Processing (Enterprise)

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRY: Monday morning, 50 audit files to process           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. File Selection                                          │
│     $ data-extract process ./audit-q3/                     │
│     Found 50 files. Analyzing...                           │
│                                                             │
│  2. Pre-flight Validation                                   │
│     ┌──────────────────────────────────────────────────┐   │
│     │ ✓ 47 files ready for processing                  │   │
│     │ ⚠ 3 files need attention:                        │   │
│     │   • scanned-doc.pdf - OCR required (slower)      │   │
│     │   • large-report.pdf - 500+ pages (memory)       │   │
│     │   • corrupted.docx - Cannot read file            │   │
│     │                                                   │   │
│     │ [Process 47] [Include all] [Review issues]       │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  3. Processing with Progress                                │
│     Processing: ████████████░░░░░░░░ 28/47 (59%)          │
│     Current: financial-analysis-q3.pdf                      │
│     Time remaining: ~45 seconds                             │
│     ✓ Saved: 28 files written to ./output/                 │
│                                                             │
│  4. Results & Quality Summary                               │
│     ┌──────────────────────────────────────────────────┐   │
│     │ ✓ Complete: 47/47 files processed                │   │
│     │                                                   │   │
│     │ Quality Score: 87/100 (Good)                     │   │
│     │ Duplicates found: 5 pairs (consider deduping)    │   │
│     │ Output: ./output/2025-11-25/ (47 files, 2.3 MB)  │   │
│     │                                                   │   │
│     │ [View Report] [Open Output] [Process More]       │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ EXIT: Files processed, quality verified, ready for RAG     │
└─────────────────────────────────────────────────────────────┘
```

#### Journey 3: Semantic Analysis (Story 4-5 Focus)

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRY: User wants to analyze processed documents           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Analysis Command                                        │
│     $ data-extract analyze ./output/ --report              │
│                                                             │
│  2. Semantic Processing                                     │
│     ┌──────────────────────────────────────────────────┐   │
│     │ Semantic Analysis Pipeline                        │   │
│     │                                                   │   │
│     │ [✓] TF-IDF Vectorization    3.2ms               │   │
│     │ [✓] Similarity Analysis     4.8ms               │   │
│     │ [✓] LSA Reduction          12.1ms               │   │
│     │ [✓] Quality Metrics         0.14ms              │   │
│     │ [→] Report Generation...                         │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  3. Results Dashboard                                       │
│     ┌──────────────────────────────────────────────────┐   │
│     │ 📊 Corpus Analysis                               │   │
│     │                                                   │   │
│     │ Documents: 47  │  Unique: 42  │  Duplicates: 5   │   │
│     │                                                   │   │
│     │ Quality Distribution:                             │   │
│     │ ███████████████████░ Excellent (89%)             │   │
│     │ ███░░░░░░░░░░░░░░░░ Good (8%)                    │   │
│     │ █░░░░░░░░░░░░░░░░░░ Review (3%)                  │   │
│     │                                                   │   │
│     │ Top Topics: audit, compliance, financial, risk   │   │
│     │                                                   │   │
│     │ 💡 5 near-duplicate pairs detected               │   │
│     │    Run `--dedupe` to consolidate                 │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  4. Report Output                                           │
│     HTML report saved: ./reports/analysis-2025-11-25.html  │
│     [Open in browser] [Export CSV] [View Details]          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ EXIT: Insights gained, report generated, next steps clear  │
└─────────────────────────────────────────────────────────────┘
```

#### Journey 4: Learning Mode (Hobbyist)

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRY: Friday night experimentation, learning mode         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Enable Learning Mode                                    │
│     $ data-extract --learn process sample.pdf              │
│                                                             │
│  2. Step-by-Step with Explanations                          │
│     ┌──────────────────────────────────────────────────┐   │
│     │ 📖 Step 1: Text Extraction                       │   │
│     │                                                   │   │
│     │ Extracting text from PDF using PyMuPDF...        │   │
│     │                                                   │   │
│     │ 💡 What's happening:                             │   │
│     │ PDFs store text in complex structures. We use    │   │
│     │ PyMuPDF to extract raw text while preserving     │   │
│     │ reading order. For scanned documents, we'd use   │   │
│     │ OCR (Optical Character Recognition) instead.     │   │
│     │                                                   │   │
│     │ ✓ Extracted 2,847 words from 12 pages           │   │
│     │                                                   │   │
│     │ [Continue] [Show raw output] [Learn more]        │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  3. Interactive Exploration                                 │
│     Allow user to adjust parameters and see effects        │
│     "Try changing chunk_size from 500 to 200 words"        │
│                                                             │
│  4. Insights Summary                                        │
│     What you learned this session:                          │
│     • PDF extraction preserves reading order                │
│     • TF-IDF measures term importance in context           │
│     • Smaller chunks = more precise but more tokens        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ EXIT: User understands pipeline, ready to experiment more  │
└─────────────────────────────────────────────────────────────┘
```

#### Journey 5: Preset Configuration (Story 5-5)

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRY: User wants to save/load processing configurations    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. List Available Presets                                  │
│     $ data-extract config presets                          │
│     ┌──────────────────────────────────────────────────┐   │
│     │ Available Presets:                                │   │
│     │                                                   │   │
│     │ Built-in:                                         │   │
│     │   • audit-standard    Audit doc processing        │   │
│     │   • rag-optimized     RAG-ready output            │   │
│     │   • quick-scan        Fast preview mode           │   │
│     │                                                   │   │
│     │ Custom:                                           │   │
│     │   • my-workflow       Created 2025-11-20          │   │
│     │                                                   │   │
│     │ [Use preset] [Create new] [Edit] [Delete]         │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  2. Create Custom Preset                                    │
│     $ data-extract config save "quarterly-audit"           │
│     ┌──────────────────────────────────────────────────┐   │
│     │ Creating preset: quarterly-audit                  │   │
│     │                                                   │   │
│     │ Capturing current settings:                       │   │
│     │   • Output format: JSON                           │   │
│     │   • Chunk size: 500 words                         │   │
│     │   • Quality threshold: 0.7                        │   │
│     │   • Dedup threshold: 0.95                         │   │
│     │                                                   │   │
│     │ ✓ Preset saved to ~/.data-extract/presets/       │   │
│     │                                                   │   │
│     │ 📖 Tip: Use with --preset=quarterly-audit        │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  3. Apply Preset to Processing                              │
│     $ data-extract process ./docs/ --preset=quarterly-audit│
│     Applying preset: quarterly-audit                        │
│     [Shows preset settings being applied]                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ EXIT: User can reproduce workflows with consistent settings │
└─────────────────────────────────────────────────────────────┘
```

**UAT Test Assertions (Journey 5):**
- Preset list displays built-in and custom presets
- Save preset captures current CLI settings
- Preset file created in expected location
- `--preset` flag applies saved configuration
- Invalid preset name shows helpful error

#### Journey 6: Error Recovery (Story 5-6)

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRY: Processing fails partway through a batch             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Partial Failure During Processing                       │
│     $ data-extract process ./large-batch/                  │
│     ┌──────────────────────────────────────────────────┐   │
│     │ Processing: ████████████░░░░░░░░ 28/50 (56%)     │   │
│     │                                                   │   │
│     │ ⚠ Error on file 29/50: corrupted-file.pdf       │   │
│     │   Cause: PDF structure invalid (no pages found)  │   │
│     │                                                   │   │
│     │ How would you like to proceed?                    │   │
│     │ ● Skip this file and continue                    │   │
│     │ ○ Stop processing (save progress)                │   │
│     │ ○ Retry with different settings                  │   │
│     │ ○ Cancel all (discard progress)                  │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  2. Progress Recovery After Interruption                    │
│     [User's terminal crashes or Ctrl+C pressed]             │
│                                                             │
│     $ data-extract process ./large-batch/                  │
│     ┌──────────────────────────────────────────────────┐   │
│     │ ⚠ Previous session detected                      │   │
│     │                                                   │   │
│     │ Found incomplete run from 2025-11-25 14:32:       │   │
│     │   • Completed: 28 files                           │   │
│     │   • Remaining: 22 files                           │   │
│     │   • Output: ./output/2025-11-25/                  │   │
│     │                                                   │   │
│     │ ● Resume from where we left off                  │   │
│     │ ○ Start fresh (keep existing output)             │   │
│     │ ○ Start fresh (overwrite existing)               │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  3. Error Summary and Recovery Report                       │
│     ┌──────────────────────────────────────────────────┐   │
│     │ ✓ Complete: 47/50 files processed                │   │
│     │                                                   │   │
│     │ ⚠ 3 files had issues:                            │   │
│     │   • corrupted-file.pdf - Skipped (invalid PDF)   │   │
│     │   • locked.docx - Skipped (password protected)   │   │
│     │   • huge.xlsx - Partial (memory limit, 10 sheets)│   │
│     │                                                   │   │
│     │ Recovery options:                                 │   │
│     │   • Fix files: data-extract validate ./issues/   │   │
│     │   • Retry failed: data-extract retry --last      │   │
│     │   • View details: data-extract log --last        │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ EXIT: User recovers gracefully, no work lost                │
└─────────────────────────────────────────────────────────────┘
```

**UAT Test Assertions (Journey 6):**
- Error prompt appears on file failure with recovery options
- Skip option continues processing remaining files
- Progress state file created for session recovery
- Resume prompt detects incomplete session
- Error summary shows actionable recovery commands
- `--retry` command re-processes only failed files

#### Journey 7: Incremental Batch Updates (Story 5-7)

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRY: User adds new files to existing processed corpus     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Incremental Processing Detection                        │
│     $ data-extract process ./audit-docs/ --output ./out/   │
│     ┌──────────────────────────────────────────────────┐   │
│     │ 📁 Analyzing ./audit-docs/                        │   │
│     │                                                   │   │
│     │ Found existing output: ./out/ (47 files)          │   │
│     │                                                   │   │
│     │ Changes detected:                                 │   │
│     │   • New files: 5                                  │   │
│     │   • Modified: 2                                   │   │
│     │   • Unchanged: 45                                 │   │
│     │   • Deleted from source: 1                        │   │
│     │                                                   │   │
│     │ ● Process only changes (7 files) - Recommended   │   │
│     │ ○ Reprocess everything (52 files)                │   │
│     │ ○ Preview changes first                          │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  2. Incremental Processing                                  │
│     ┌──────────────────────────────────────────────────┐   │
│     │ Incremental Update: ████████████████████ 7/7     │   │
│     │                                                   │   │
│     │ ✓ Added: 5 new files                             │   │
│     │ ✓ Updated: 2 modified files                       │   │
│     │ ⚠ Orphaned: 1 output has no source (kept)        │   │
│     │                                                   │   │
│     │ Time saved: ~4 minutes (vs full reprocess)        │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
│  3. Corpus Sync Status                                      │
│     $ data-extract status ./out/                           │
│     ┌──────────────────────────────────────────────────┐   │
│     │ Corpus Status: ./out/                             │   │
│     │                                                   │   │
│     │ Last updated: 2025-11-25 15:42                    │   │
│     │ Total files: 52                                   │   │
│     │ Source: ./audit-docs/                             │   │
│     │                                                   │   │
│     │ Sync status: ✓ Up to date                        │   │
│     │                                                   │   │
│     │ Cache: 47 vectorizers, 12 similarity matrices    │   │
│     │ Storage: 2.3 MB output, 45 MB cache              │   │
│     └──────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ EXIT: Corpus updated efficiently, only changes processed    │
└─────────────────────────────────────────────────────────────┘
```

**UAT Test Assertions (Journey 7):**
- Change detection identifies new/modified/unchanged files
- Incremental option processes only changed files
- Time savings displayed vs full reprocess
- `--force` flag reprocesses everything
- Status command shows sync state
- Orphaned outputs handled gracefully
- File hash comparison for modification detection

---

## 6. Component Library

### 6.1 Component Strategy

**Reusable CLI Components:**

| Component | Description | Usage |
|-----------|-------------|-------|
| `FileSelector` | Interactive file/directory picker | Input selection |
| `ProgressTracker` | Multi-file progress with ETA | Batch operations |
| `QualityPanel` | Metrics visualization | Results display |
| `PreflightCheck` | Validation summary with actions | Pre-processing |
| `LearningTip` | Contextual educational content | Learning mode |
| `ErrorGuide` | Error with suggestions | Error handling |
| `ComparisonView` | Before/after side-by-side | Preview mode |
| `ConfigEditor` | Interactive config modification | Settings |

**Component Specifications:**

```python
# Example: QualityPanel component
class QualityPanel:
    """
    Displays quality metrics in a Rich panel.

    Features:
    - Bar chart visualization
    - Color-coded thresholds
    - Expandable details
    - Action suggestions
    """

    def render(self, metrics: QualityMetrics) -> Panel:
        # Excellent: green, Good: yellow, Review: red
        # Include learning tip if --learn mode
        # Show actionable next steps
        pass
```

---

## 7. UX Pattern Decisions

### 7.1 Consistency Rules

**Command Patterns:**

| Pattern | Convention | Example |
|---------|------------|---------|
| **Subcommands** | Verb-noun or verb | `extract`, `analyze`, `validate` |
| **Options** | `--full-name` or `-x` short | `--output`, `-o` |
| **Flags** | Boolean toggles | `--verbose`, `--quiet`, `--dry-run` |
| **Arguments** | Positional for primary input | `data-extract process FILE...` |

**Feedback Patterns:**

| Event | Feedback | Duration |
|-------|----------|----------|
| Command start | Spinner + "Processing..." | Until complete |
| Progress | Bar with %, file count, ETA | During operation |
| Success | Green ✓ + summary | Persistent |
| Warning | Yellow ⚠ + suggestion | Persistent |
| Error | Red ✗ + cause + fix | Persistent |
| Learning | Magenta 📖 + explanation | On request |

**Output Patterns:**

| Verbosity | Content | Flag |
|-----------|---------|------|
| **Quiet** | Exit code only | `-q` |
| **Normal** | Summary + key metrics | (default) |
| **Verbose** | Detailed per-file info | `-v` |
| **Debug** | Full trace + timing | `-vv` |
| **Learn** | Normal + explanations | `--learn` |

**Confirmation Patterns:**

| Risk Level | Confirmation |
|------------|--------------|
| **Low** (read-only) | None |
| **Medium** (write files) | Single confirm for batch |
| **High** (overwrite/delete) | Explicit `--force` or confirm each |

**Error Message Structure:**

```
✗ Error: Could not read file 'report.pdf'

  Cause: File is password protected

  Suggestions:
    1. Provide password: --password "..."
    2. Skip this file: --skip-errors
    3. Use a different file

  📖 Learn more: data-extract help pdf-errors
```

---

## 8. Responsive Design & Accessibility

### 8.1 Responsive Strategy

**Terminal Width Adaptation:**

| Width | Behavior |
|-------|----------|
| < 60 cols | Compact mode, truncated paths, no tables |
| 60-100 cols | Standard layout, wrapped text |
| > 100 cols | Full layout, side-by-side comparisons |

**Unicode/ASCII Fallbacks:**

| Feature | Unicode | ASCII Fallback |
|---------|---------|----------------|
| Checkmark | ✓ | [OK] |
| Error | ✗ | [ERROR] |
| Warning | ⚠ | [WARN] |
| Progress | █░ | [====----] |
| Arrow | → | -> |
| Bullet | • | * |

**Accessibility Features:**

| Feature | Implementation |
|---------|----------------|
| **NO_COLOR** | Respect environment variable |
| **Screen readers** | Structured output, no decorative elements in quiet mode |
| **Machine parsing** | JSON output with `--json` flag |
| **Exit codes** | Meaningful codes for scripting |
| **Log files** | Full output available in `--log` file |

**Scripting Support:**

```bash
# Machine-readable output
$ data-extract process ./docs/ --json | jq '.files[].quality'

# Exit codes
# 0 = success
# 1 = partial success (some files failed)
# 2 = complete failure
# 3 = configuration error

# Quiet mode for scripts
$ data-extract validate ./docs/ -q && echo "Ready"
```

---

## 9. Implementation Guidance

### 9.1 Completion Summary

**Phase 1 Implementation (Story 4-5 + Epic 5 Foundation):**

| Component | Priority | Complexity | Dependencies |
|-----------|----------|------------|--------------|
| Rich output formatting | P0 | Low | Rich library |
| Subcommand structure | P0 | Low | Typer |
| Progress bars | P0 | Low | Rich |
| Pre-flight validation | P0 | Medium | Pipeline integration |
| Quality panels | P1 | Medium | Quality metrics stage |
| Error guides | P1 | Medium | Error catalog |
| Learning mode | P2 | High | Content authoring |
| Interactive file selector | P2 | Medium | InquirerPy |

**Story 4-5 Specific (CLI Integration):**

```python
# Proposed command structure
@app.command()
def analyze(
    path: Path,
    output: Path = Option(None, "--output", "-o"),
    report: bool = Option(False, "--report", "-r"),
    format: str = Option("json", "--format", "-f"),
    verbose: int = Option(0, "--verbose", "-v", count=True),
    learn: bool = Option(False, "--learn"),
):
    """
    Run semantic analysis on processed documents.

    Analyzes document corpus using TF-IDF vectorization,
    similarity detection, LSA topic modeling, and quality metrics.
    """
    pass
```

**Key Implementation Notes:**

1. **Use Rich Console** - Centralized console instance for consistent output
2. **Error Boundaries** - Wrap operations in try/except with ErrorGuide output
3. **Progress Context** - Use Rich's Progress context manager for all batch ops
4. **Config Cascade** - CLI args > env vars > config file > defaults
5. **Learning Mode** - Separate concern, inject explanations via decorator

---

## Appendix

### Related Documents

- Product Requirements: `N/A (brownfield project)`
- Product Brief: `N/A (brownfield project)`
- Brainstorming: `docs/brainstorming-session-results-2025-11-07.md`

### Core Interactive Deliverables

This UX Design Specification was created through visual collaboration:

- **Color Theme Visualizer**: [ux-color-themes.html](./ux-color-themes.html)
  - Interactive HTML showing all color theme options explored
  - Live terminal output examples in each theme
  - Side-by-side comparison and semantic color usage

- **Design Direction Mockups**: [ux-design-directions.html](./ux-design-directions.html)
  - Interactive HTML with CLI interaction pattern examples
  - Example terminal sessions for each approach
  - Design philosophy and rationale for each direction

### Optional Enhancement Deliverables

_This section will be populated if additional UX artifacts are generated through follow-up workflows._

<!-- Additional deliverables added here by other workflows -->

### Next Steps & Follow-Up Workflows

This UX Design Specification can serve as input to:

- **Story 4-5 Implementation** - CLI Integration & Reporting (immediate next)
- **Epic 5 Development** - Full CLI, batch processing, configuration cascade
- **Interactive Prototype Workflow** - Build clickable terminal demos
- **Component Showcase Workflow** - Create Rich component library
- **Documentation Generation** - User guides and tutorials

### Version History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-25 | 1.0 | Initial UX Design Specification | andrew |

---

_This UX Design Specification was created through collaborative design facilitation based on extensive brainstorming sessions and multi-agent analysis. All decisions are grounded in documented user research and project context._

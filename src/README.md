# Source Code Directory

This directory contains all implementation code for the extraction tool.

## Structure

```
src/
└── data_extract/   # Production codebase (V1.0)
    ├── extract/    # ✓ Complete - Format-specific extraction (PDF, DOCX, XLSX, PPTX, CSV, images+OCR)
    ├── normalize/  # ✓ Complete - Text cleaning, entity standardization
    ├── chunk/      # ✓ Complete - Semantic-aware chunking (spaCy-based)
    ├── semantic/   # ✓ Complete - Classical NLP analysis (TF-IDF, LSA)
    ├── output/     # ✓ Complete - Multiple formats (JSON, TXT, CSV)
    ├── cli/        # ✓ Complete - Command-line interface (9 commands)
    ├── config/     # ✓ Complete - Configuration management
    └── models/     # ✓ Complete - Data models and validation
```

## What Goes Where

### `data_extract/models/` - Data Models ✓
**Status**: Complete and stable

Core data structures and validation models used throughout the pipeline.

**Files**:
- `document.py` - Document and ContentBlock models
- `extraction.py` - Extraction result models
- `chunk.py` - Chunk models with metadata
- `semantic.py` - Semantic analysis models

**Pattern**: Immutable frozen dataclasses with Pydantic v2 validation

### `data_extract/extract/` - Format Handlers ✓
**Status**: All extractors complete

Format-specific extraction modules. Each implements `BaseExtractor` interface.

**Pattern**:
```python
from data_extract.models import Document, ExtractionResult

class DocxExtractor(BaseExtractor):
    def extract(self, file_path: Path) -> ExtractionResult:
        # DOCX-specific extraction logic
        pass
```

**Complete Extractors**:
- `pdf.py` - PDF extraction with OCR fallback (PyMuPDF)
- `docx.py` - Word document extraction (python-docx)
- `xlsx.py` - Excel spreadsheet extraction (openpyxl)
- `pptx.py` - PowerPoint extraction (python-pptx)
- `csv.py` - CSV file extraction
- `image.py` - Image extraction with OCR (Tesseract)

### `data_extract/normalize/` - Content Normalization ✓
**Status**: Complete

Text cleaning and entity standardization processors.

**Files**:
- `text_cleaner.py` - Text cleaning and artifact removal
- `entity_normalizer.py` - Entity standardization
- `schema_validator.py` - Schema validation across document types

### `data_extract/chunk/` - Semantic Chunking ✓
**Status**: Complete

Semantic-aware chunking using spaCy sentence boundaries.

**Files**:
- `semantic_chunker.py` - Main chunking engine
- `boundary_detector.py` - Sentence boundary detection
- `metadata_enricher.py` - Chunk metadata and quality scoring

### `data_extract/semantic/` - Classical NLP Analysis ✓
**Status**: Complete (Epic 4)

Classical NLP analysis using scikit-learn (TF-IDF, LSA).

**Files**:
- `tfidf_analyzer.py` - TF-IDF vectorization and analysis
- `similarity_engine.py` - Cosine similarity and duplicate detection
- `quality_scorer.py` - Readability metrics (Flesch, SMOG)
- `cache_manager.py` - Model caching and persistence

**Enterprise Constraint**: Classical NLP only - no transformer models allowed.

### `data_extract/output/` - Output Formatters ✓
**Status**: Complete

Multiple output format generators.

**Files**:
- `json_formatter.py` - JSON output with full metadata
- `txt_formatter.py` - Plain text for LLM upload
- `csv_formatter.py` - CSV for analysis and tracking

### `data_extract/cli/` - Command-Line Interface ✓
**Status**: Complete (Epic 5)

Typer-based CLI with Rich terminal UI.

**Commands**:
- `process` - Main document processing
- `extract` - Extract-only mode
- `retry` - Retry failed documents
- `validate` - Validate output
- `status` - Session status
- `semantic` - Semantic analysis
- `cache` - Cache management
- `config` - Configuration management
- `session` - Session recovery

**Features**: Real-time progress, summary statistics, preset configurations, graceful error handling

### `data_extract/config/` - Configuration Management ✓
**Status**: Complete (Epic 5)

6-layer configuration cascade system.

**Layers** (priority order):
1. CLI arguments
2. Environment variables
3. Session config
4. User config (`~/.config/data-extract/`)
5. Project config (`.data-extract.yaml`)
6. Defaults

## Pipeline Architecture

The codebase implements a five-stage modular pipeline:

```
Extract → Normalize → Chunk → Semantic → Output
```

### Design Principles

1. **Modularity** - Each stage is independent, testable, replaceable
2. **Immutability** - Frozen dataclasses prevent pipeline state mutations
3. **Type Safety** - Full type hints + Pydantic v2 validation enforced by mypy
4. **Interface-Based** - All modules implement ABCs (BaseExtractor, BaseProcessor, BaseFormatter)
5. **Determinism** - Same input always produces same output

### Adding New Modules

1. **Choose correct directory** based on pipeline stage
2. **Import from models**: `from data_extract.models import Document, ExtractionResult`
3. **Implement required interface** (BaseExtractor, BaseProcessor, or BaseFormatter)
4. **Follow naming convention**: `{format}_extractor.py`, `{name}_processor.py`, `{format}_formatter.py`
5. **Add docstrings** to all classes and public methods (Google style)
6. **Use type hints** for all function signatures

### Module Independence

Modules within a directory should be **independent**:
- `pdf.py` doesn't import from `docx.py`
- All shared code goes in `models/` or `utils/`
- Extractors only depend on `models/`

### Testing

Tests mirror `src/` structure exactly:
```
tests/
├── data_extract/
│   ├── extract/
│   │   ├── test_pdf.py
│   │   └── test_docx.py
│   ├── normalize/
│   ├── chunk/
│   ├── semantic/
│   ├── output/
│   └── cli/
```

**Coverage Requirements**:
- Baseline: >60% overall
- `src/data_extract/`: >80% coverage (production code)
- Critical paths: >90% coverage

## Quick Reference

**See**: `/home/andrew/dev/data-extraction-tool/CLAUDE.md` for project conventions
**See**: `/home/andrew/dev/data-extraction-tool/docs/architecture.md` for technical architecture
**See**: `/home/andrew/dev/data-extraction-tool/docs/ux-design-specification.md` for CLI usage

# 7. Appendices

## 7.1 Appendix A: File Tree

**Brownfield Codebase Structure:**
```
src/
├── cli/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py (150 lines) - Click entry point
│   ├── commands.py (400 lines) - Command implementations
│   └── progress_display.py (200 lines) - Rich progress
├── extractors/
│   ├── __init__.py
│   ├── pdf_extractor.py (847 lines) ⭐
│   ├── docx_extractor.py (523 lines) [SPIKE]
│   ├── excel_extractor.py (502 lines) [TDD]
│   ├── pptx_extractor.py (535 lines) [TDD]
│   ├── csv_extractor.py (400 lines) [v1.0.6]
│   └── txt_extractor.py (100 lines) [Reference]
├── processors/
│   ├── __init__.py
│   ├── metadata_aggregator.py (300 lines)
│   ├── quality_validator.py (400 lines)
│   └── context_linker.py (350 lines)
├── formatters/
│   ├── __init__.py
│   ├── json_formatter.py (350 lines)
│   ├── markdown_formatter.py (300 lines)
│   └── chunked_text_formatter.py (400 lines)
├── core/
│   ├── __init__.py
│   ├── interfaces.py (200 lines) - BaseExtractor, BaseProcessor, BaseFormatter, BasePipeline
│   └── models.py (500 lines) - ContentBlock, ExtractionResult, DocumentMetadata, etc.
├── pipeline/
│   ├── __init__.py
│   ├── extraction_pipeline.py (600 lines) - Main orchestrator
│   └── batch_processor.py (300 lines) - Parallel processing
├── infrastructure/
│   ├── __init__.py
│   ├── config_manager.py (400 lines)
│   ├── logging_framework.py (350 lines)
│   ├── error_handler.py (500 lines)
│   └── progress_tracker.py (300 lines)
└── data_extract/  # Epic 1 placeholder structure
    ├── __init__.py
    ├── core/__init__.py
    ├── extract/__init__.py
    ├── normalize/__init__.py
    ├── chunk/__init__.py
    ├── semantic/__init__.py
    ├── output/__init__.py
    ├── config/__init__.py
    ├── utils/__init__.py
    └── cli.py (placeholder)
```

**Total Lines of Code (brownfield):**
- Extractors: ~3,307 lines
- Processors: ~1,050 lines
- Formatters: ~1,050 lines
- Core: ~700 lines
- Pipeline: ~900 lines
- Infrastructure: ~1,550 lines
- CLI: ~750 lines
- **Total: ~9,307 lines** (production code only, excluding tests)

## 7.2 Appendix B: Code Samples

### Sample 1: BaseExtractor Interface

```python
# src/core/interfaces.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from .models import ExtractionResult

class BaseExtractor(ABC):
    """Abstract base class for document extractors."""

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract content from file.

        Args:
            file_path: Path to file to extract

        Returns:
            ExtractionResult with content blocks and metadata
        """
        pass

    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if extractor supports file format.

        Args:
            file_path: Path to file

        Returns:
            True if format is supported
        """
        pass

    def validate_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """Validate file before extraction.

        Args:
            file_path: Path to file

        Returns:
            (valid, error_message) tuple
        """
        if not file_path.exists():
            return False, f"File does not exist: {file_path}"
        if not file_path.is_file():
            return False, f"Not a file: {file_path}"
        return True, None

    def get_format_name(self) -> str:
        """Get human-readable format name."""
        return self.__class__.__name__.replace("Extractor", "")

    def get_supported_extensions(self) -> tuple[str, ...]:
        """Get supported file extensions."""
        return ()
```

### Sample 2: ContentBlock Model

```python
# src/core/models.py
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

@dataclass(frozen=True)
class ContentBlock:
    """Atomic unit of extracted content."""

    block_id: UUID
    block_type: ContentType
    content: str
    raw_content: Optional[str] = None
    position: Optional[Position] = None
    parent_id: Optional[UUID] = None
    metadata: dict = field(default_factory=dict)
    confidence: Optional[float] = None
    style: Optional[str] = None

    def __post_init__(self):
        """Validate content block."""
        if not isinstance(self.block_id, UUID):
            raise ValueError("block_id must be UUID")
        if not isinstance(self.block_type, ContentType):
            raise ValueError("block_type must be ContentType enum")
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
```

### Sample 3: PDF OCR Auto-Detection

```python
# src/extractors/pdf_extractor.py
def _needs_ocr(self, file_path: Path) -> bool:
    """Detect if PDF needs OCR by checking first 3 pages for text.

    Args:
        file_path: Path to PDF file

    Returns:
        True if OCR is needed (minimal native text)
    """
    try:
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            pages_to_check = min(3, len(reader.pages))

            for page_num in range(pages_to_check):
                page = reader.pages[page_num]
                text = page.extract_text() or ""

                if len(text.strip()) > self.min_text_threshold:
                    # Found native text, OCR not needed
                    return False

            # Minimal text found, OCR recommended
            return True

    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            self.logger.warning(f"Error checking for OCR need: {e}")
        return False  # Assume native text extraction will work
```

## 7.3 Appendix C: Dependency Inventory

**Complete dependency list from pyproject.toml (Story 1.1):**

```toml
[project]
dependencies = [
    "python-docx>=0.8.11",      # DOCX extraction
    "pypdf>=3.0.0",              # PDF extraction (modern pypdf, was PyPDF2)
    "python-pptx>=0.6.21",       # PPTX extraction
    "openpyxl>=3.0.10",          # Excel extraction
    "pdfplumber>=0.10.0",        # PDF table extraction
    "Pillow>=10.0.0",            # Image processing (PIL fork)
    "pydantic>=2.0.0,<3.0",      # Data models with validation (Epic 1)
    "PyYAML>=6.0.0,<7.0",        # Config loading (Epic 1)
    "structlog>=24.0.0,<25.0",   # Structured logging (Epic 1)
    "typer>=0.12.0,<0.13",       # CLI framework (Epic 5, replaces Click)
    "rich>=13.0.0",              # CLI rich output
]

[project.optional-dependencies]
ocr = [
    "pytesseract>=0.3.10",       # OCR capability
    "pdf2image>=1.16.0",         # PDF to image conversion for OCR
]
csv = [
    "chardet>=5.0.0",            # CSV encoding detection
]
dev = [
    "pytest>=8.0.0,<9.0",
    "pytest-cov>=4.0.0,<5.0",
    "black>=24.0.0,<25.0",
    "mypy>=1.11.0,<2.0",
    "ruff>=0.6.0,<0.7",
    "pre-commit>=3.5.0",
]
```

**Future dependencies (Epic 2-4):**
```toml
nlp = [
    "spacy>=3.7.0,<4.0",         # Entity extraction (Epic 2)
    "nltk>=3.8.0,<4.0",          # Sentence tokenization (Epic 3)
]
semantic = [
    "scikit-learn>=1.3.0,<2.0",  # TF-IDF, LSA (Epic 4)
    "textstat>=0.7.0,<0.8",      # Readability metrics (Epic 4)
]
```

## 7.4 Appendix D: Testing Summary

**Test Suite Overview (from Story 1.1):**
- **Total tests:** 1007
- **Passing:** 778 (77%)
- **Failing:** 229 (23%)
- **Coverage:** Unknown (never run)

**Test Structure:**
```
tests/
├── conftest.py
├── fixtures/
├── test_extractors/
│   ├── test_pdf_extractor.py
│   ├── test_docx_extractor.py
│   ├── test_excel_extractor.py
│   ├── test_pptx_extractor.py
│   ├── test_csv_extractor.py
│   └── test_txt_extractor.py
├── test_processors/
│   ├── test_metadata_aggregator.py
│   ├── test_quality_validator.py
│   └── test_context_linker.py
├── test_formatters/
│   ├── test_json_formatter.py
│   ├── test_markdown_formatter.py
│   └── test_chunked_text_formatter.py
├── test_infrastructure/
│   ├── test_config_manager.py
│   ├── test_logging_framework.py
│   ├── test_error_handler.py
│   └── test_progress_tracker.py
├── test_pipeline/
│   ├── test_extraction_pipeline.py
│   └── test_batch_processor.py
├── test_cli/
│   ├── test_main.py
│   └── test_commands.py
├── integration/
├── performance/
├── test_edge_cases/
└── validation/
```

**Test Quality Hypothesis:**
- **Excellent:** Excel, PPTX, CSV extractors (marked TDD)
- **Good:** PDF, processors, formatters
- **Poor:** TXT extractor (no integration)
- **Unknown:** Infrastructure, pipeline

**Action Required (Story 1.3):**
- Run coverage: `pytest --cov=src --cov-report=html`
- Fix 229 failing tests
- Document test quality (A/B/C/D grades)

---

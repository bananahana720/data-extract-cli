# Technology Stack Details

## Core Technologies

**Python 3.12** (Enterprise Requirement)
- Type hints with PEP 695 syntax (Python 3.12+ type parameter syntax)
- Pattern matching for document type detection
- Improved error messages for debugging
- Performance improvements over 3.11

**CLI & Terminal UI:**
- **Typer 0.12.x**: Command routing, type-safe CLI, auto-help generation
- **Rich 13.x**: Progress bars, tables, syntax highlighting, terminal formatting
- Integration: Typer for commands, Rich for output presentation

**NLP & Document Processing:**
- **spaCy 3.7.x**: Sentence segmentation, tokenization, named entity recognition (NER)
  - Model: `en_core_web_md` (50MB, includes word vectors)
  - Used for: Semantic chunking, entity detection
- **scikit-learn 1.5.x**: TF-IDF vectorization, LSA (TruncatedSVD), cosine similarity
  - Classical ML algorithms only (no deep learning)
- **gensim 4.3.x**: Word2Vec, FastText, LDA topic modeling
  - Advanced semantic analysis (post-MVP)
- **textstat 0.7.x**: Readability metrics (Flesch-Kincaid, Gunning Fog, SMOG)

**Document Extraction:**
- **PyMuPDF (fitz) 1.24.x**: PDF text/image extraction, fast, handles complex PDFs
- **python-docx 1.1.x**: Word document parsing (text, tables, comments, tracked changes)
- **openpyxl 3.1.x**: Excel reading/writing, table extraction
- **pytesseract 0.3.x**: OCR wrapper for Tesseract engine
  - Requires system Tesseract installation
- **Pillow 10.x**: Image preprocessing for OCR (deskew, denoise, contrast)
- **BeautifulSoup4 4.12.x**: HTML/XML parsing for Archer exports

**Data & Configuration:**
- **Pydantic 2.x**: Data validation, settings management, JSON schema generation
  - Replaces dataclasses for type-safe models with validation
- **PyYAML 6.0.x**: YAML configuration file parsing
- **python-dotenv 1.0.x**: Environment variable loading from .env files

**Development & Quality:**
- **pytest 8.x**: Test framework
  - **pytest-cov**: Coverage reporting
  - **pytest-xdist**: Parallel test execution
- **ruff 0.6.x**: Fast Python linter (replaces flake8, isort, etc.)
- **mypy 1.11.x**: Static type checking
- **black 24.x**: Code formatting (opinionated)
- **pre-commit 3.x**: Git hooks for quality enforcement

**Logging & Monitoring:**
- **structlog 24.x**: Structured logging with JSON output
  - Integrates with Python's logging module
  - Audit trail compliance (timestamps, processing decisions)

## Integration Points

**CLI → Pipeline Orchestration:**
```python
# cli.py routes commands to pipeline stages
@app.command()
def process(input_path: Path, output: Path = "./processed"):
    pipeline = Pipeline([
        Extractor(),
        Normalizer(),
        Chunker(),
        Analyzer(),
        Writer()
    ])
    results = pipeline.process(input_path)
```

**Extract → Normalize:**
- `Extractor` returns `Document` objects with raw text + metadata
- `Normalizer` receives `Document`, applies cleaning, returns normalized `Document`
- Data contract: `Document(text: str, metadata: Metadata, entities: List[Entity])`

**Normalize → Chunk:**
- `Normalizer` returns validated `Document` with entity tags
- `Chunker` uses entity information to determine optimal split points
- Data contract: `List[Chunk]` where each chunk has source document reference

**Chunk → Semantic:**
- `Chunker` produces `List[Chunk]` with text + metadata
- `Analyzer` vectorizes chunks (TF-IDF), computes similarity matrix
- Data contract: `SemanticAnalysis(vectors, similarity_matrix, quality_scores)`

**Semantic → Output:**
- All stages feed results to `Writer`
- `Writer` generates JSON, TXT, CSV from unified data structures
- Data contract: `ProcessingResult(documents, chunks, analysis, metadata)`

**Configuration Flow:**
```
CLI flags → Environment variables → YAML config → Hardcoded defaults
(Highest precedence)                              (Lowest precedence)
```

## Dependency Installation

**pyproject.toml dependencies:**
```toml
[project]
dependencies = [
    "typer[all]>=0.12.0,<0.13",
    "rich>=13.0.0,<14.0",
    "spacy>=3.7.0,<3.8",
    "scikit-learn>=1.5.0,<1.6",
    "gensim>=4.3.0,<4.4",
    "textstat>=0.7.0,<0.8",
    "pymupdf>=1.24.0,<1.25",
    "python-docx>=1.1.0,<1.2",
    "openpyxl>=3.1.0,<3.2",
    "pytesseract>=0.3.0,<0.4",
    "Pillow>=10.0.0,<11.0",
    "beautifulsoup4>=4.12.0,<5.0",
    "pydantic>=2.0.0,<3.0",
    "PyYAML>=6.0.0,<7.0",
    "python-dotenv>=1.0.0,<2.0",
    "structlog>=24.0.0,<25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0,<9.0",
    "pytest-cov>=5.0.0,<6.0",
    "pytest-xdist>=3.6.0,<4.0",
    "ruff>=0.6.0,<0.7",
    "mypy>=1.11.0,<2.0",
    "black>=24.0.0,<25.0",
    "pre-commit>=3.0.0,<4.0",
]

[project.scripts]
data-extract = "data_extract.cli:app"
```

**External Dependencies (System-Level):**
- Tesseract OCR engine (for pytesseract)
  - Install: `apt-get install tesseract-ocr` (Linux) or `brew install tesseract` (Mac)
  - Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki
- spaCy language model: `python -m spacy download en_core_web_md`

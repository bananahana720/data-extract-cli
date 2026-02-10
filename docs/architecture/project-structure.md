# Project Structure

```
data-extraction-tool/
├── pyproject.toml              # PEP 621 project config, dependencies, entry points
├── README.md                   # Setup instructions, quick start
├── .gitignore                  # Exclude venv, __pycache__, outputs, .env
├── .pre-commit-config.yaml     # ruff, mypy, black hooks
│
├── src/
│   └── data_extract/           # Main package
│       ├── __init__.py         # Package version, exports
│       ├── __main__.py         # Entry point for python -m data_extract
│       ├── cli.py              # Typer CLI app definition, command routing
│       │
│       ├── core/               # Core data models and interfaces
│       │   ├── __init__.py
│       │   ├── models.py       # Pydantic: Document, Chunk, Metadata, Config
│       │   ├── pipeline.py     # Pipeline interface/protocol, stage contracts
│       │   └── exceptions.py   # Custom exception hierarchy
│       │
│       ├── extract/            # Stage 1: Document extraction
│       │   ├── __init__.py
│       │   ├── extractor.py    # Main extraction orchestrator
│       │   ├── pdf.py          # PyMuPDF: PDF extraction
│       │   ├── docx.py         # python-docx: Word extraction
│       │   ├── xlsx.py         # openpyxl: Excel extraction
│       │   ├── image.py        # pytesseract: Image OCR
│       │   └── archer.py       # HTML/XML: Archer export parsing
│       │
│       ├── normalize/          # Stage 2: Text normalization
│       │   ├── __init__.py
│       │   ├── normalizer.py   # Main normalization orchestrator
│       │   ├── cleaning.py     # Artifact removal, whitespace normalization
│       │   ├── entities.py     # Entity normalization (6 audit types)
│       │   ├── schema.py       # Schema standardization across doc types
│       │   └── validation.py   # Completeness validation, quality checks
│       │
│       ├── chunk/              # Stage 3: Intelligent chunking
│       │   ├── __init__.py
│       │   ├── chunker.py      # Main chunking orchestrator
│       │   ├── semantic.py     # Semantic boundary-aware chunking (spaCy)
│       │   ├── entity_aware.py # Entity-aware chunking logic
│       │   └── metadata.py     # Chunk metadata enrichment
│       │
│       ├── semantic/           # Stage 4: Semantic analysis
│       │   ├── __init__.py
│       │   ├── analyzer.py     # Main semantic analysis orchestrator
│       │   ├── tfidf.py        # TF-IDF vectorization (scikit-learn)
│       │   ├── similarity.py   # Cosine similarity, document matching
│       │   ├── lsa.py          # Latent Semantic Analysis (TruncatedSVD)
│       │   └── quality.py      # Quality metrics (textstat)
│       │
│       ├── output/             # Stage 5: Output formatting
│       │   ├── __init__.py
│       │   ├── writer.py       # Main output orchestrator
│       │   ├── json_writer.py  # JSON format with metadata
│       │   ├── txt_writer.py   # Plain text format for LLM upload
│       │   ├── csv_writer.py   # CSV tabular format
│       │   └── organizer.py    # Output organization strategies
│       │
│       ├── config/             # Configuration management
│       │   ├── __init__.py
│       │   ├── loader.py       # Load from YAML, env vars, CLI flags
│       │   ├── presets.py      # Named presets (chatgpt, knowledge-graph, etc.)
│       │   └── defaults.yaml   # Default configuration values
│       │
│       └── utils/              # Shared utilities
│           ├── __init__.py
│           ├── logging.py      # Structured logging setup (structlog)
│           ├── progress.py     # Rich progress bar helpers
│           ├── cache.py        # File hashing, manifest management
│           └── errors.py       # Error handling, quarantine logic
│
├── tests/                      # Mirror src/ structure
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures, test configuration
│   ├── fixtures/               # Sample files for testing
│   │   ├── pdfs/
│   │   ├── docx/
│   │   ├── xlsx/
│   │   ├── images/
│   │   └── archer/
│   ├── unit/                   # Unit tests (fast, isolated)
│   │   ├── test_extract/
│   │   ├── test_normalize/
│   │   ├── test_chunk/
│   │   ├── test_semantic/
│   │   └── test_output/
│   ├── integration/            # Integration tests (full pipeline)
│   │   ├── test_pipeline_basic.py
│   │   ├── test_batch_processing.py
│   │   └── test_determinism.py
│   └── performance/            # Performance benchmarks
│       └── test_throughput.py
│
├── docs/                       # Project documentation
│   ├── architecture.md         # This file
│   ├── PRD.md                  # Product requirements
│   ├── epics.md                # Epic breakdown
│   └── brownfield-assessment.md # Brownfield codebase analysis
│
├── config/                     # Configuration templates
│   └── config.example.yaml     # Example configuration file
│
└── scripts/                    # Development/deployment scripts
    ├── setup.sh                # Development environment setup
    └── verify_install.py       # Verify installation and dependencies
```

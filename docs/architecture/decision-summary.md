# Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| -------- | -------- | ------- | ------------- | --------- |
| CLI Framework | Typer | 0.12.x (latest) | Epic 5 (CLI UX) | Modern, type-safe, less boilerplate than Click. Built on Click for compatibility. Auto-generates help text. |
| Terminal UI | Rich | 13.x (latest) | Epic 5 (Progress) | Beautiful progress bars, tables, syntax highlighting. Industry standard for modern Python CLI. |
| Project Structure | src/ layout with pipeline modules | N/A | Epic 1 (Foundation) | Clear separation: src/data_extract/{extract, normalize, chunk, semantic, output}. Follows modern Python packaging. |
| Dependency Management | pyproject.toml + pip | Python 3.12 | Epic 1 (Foundation) | PEP 621 standard. Pin all versions for reproducibility (audit requirement). |
| NLP Core | spaCy | 3.7.x (latest) | Epics 2, 3 (NLP) | Production-ready, fast, excellent sentence segmentation. Use en_core_web_md model. |
| Text Vectorization | scikit-learn | 1.5.x (latest) | Epic 4 (Semantic) | TF-IDF, LSA, cosine similarity. Industry standard for classical NLP. No transformer dependencies. |
| Topic Modeling | gensim | 4.3.x (latest) | Epic 4 (Semantic) | Word2Vec, LDA. Complements scikit-learn for advanced semantic analysis. |
| Document Extraction | PyMuPDF (fitz) | 1.24.x (latest) | Epic 1, 2 | Fast PDF processing. Better than PyPDF2. Handles both native and scanned PDFs. |
| Word Documents | python-docx | 1.1.x (latest) | Epic 1, 2 | Standard for .docx. Extracts text, tables, comments, tracked changes. |
| OCR Engine | pytesseract | 0.3.x (latest) | Epic 2 (Quality) | Tesseract wrapper. Confidence scoring. Preprocessing with Pillow for quality. |
| Data Models | Pydantic | 2.x (latest) | All Epics | Type-safe data validation. Better than dataclasses for config and API contracts. Schema validation. |
| Configuration | PyYAML + env vars | 6.0.x (latest) | Epic 5 (Config) | YAML for user config. Env vars for overrides. CLI flags highest precedence. |
| Testing Framework | pytest | 8.x (latest) | Epic 1 (Foundation) | Industry standard. Plugin ecosystem (pytest-cov, pytest-xdist for parallel). |
| Code Quality | ruff + mypy + black | Latest | Epic 1 (Foundation) | Ruff: fast linter. Mypy: type checking. Black: formatting. Pre-commit hooks enforce. |
| Progress Feedback | rich.progress | 13.x (latest) | Epic 5 (Progress) | Integrated with Rich. Real-time progress bars, elapsed/remaining time, file counts. |
| Logging | Python logging + structlog | 3.11+ / 24.x | All Epics | Structured logging for audit trail. JSON output option. Configurable levels. |
| Quality Metrics | textstat | 0.7.x (latest) | Epic 2, 4 | Readability scores (Flesch-Kincaid, Gunning Fog, SMOG). Lexical diversity. |
| Parallelization | concurrent.futures | Python stdlib | Epic 5 (Batch) | ThreadPoolExecutor for I/O-bound tasks. ProcessPoolExecutor for CPU-bound. Simpler than multiprocessing. |
| Metadata Format | JSON with schema | Python stdlib | Epic 3 (Output) | JSON for structured metadata. Include processing config, version, timestamps for audit trail. |
| Caching Strategy | SHA-256 file hashing | Python stdlib | Epic 5 (Incremental) | Detect file changes for incremental processing. Manifest file tracks processed files. |
| Error Handling | Continue-on-error + quarantine | N/A | Epic 5 (Batch) | Catch errors per file, continue batch, quarantine failures, detailed logs. No silent failures. |

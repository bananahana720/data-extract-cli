# 6. Recommendations

## 6.1 Immediate Actions (Epic 1, Stories 1.3-1.4)

### Story 1.3: Testing Framework & CI Pipeline

**Priority: 🔴 CRITICAL**

1. **Test Coverage Audit:**
   - Run: `pytest --cov=src --cov-report=html --cov-report=term-missing`
   - Analyze: Coverage per module (target: 80% for brownfield)
   - Fix: 229 failing tests (23% failure rate)
   - Document: Test quality assessment (A/B/C/D grades)

2. **CI Pipeline Setup:**
   - Configure GitHub Actions or similar
   - Run tests, linting, type checking on push/PR
   - Generate coverage reports
   - Block merges if tests fail or coverage drops

3. **Binary Dependency Documentation:**
   - Add tesseract/poppler installation to README.md
   - Add troubleshooting guide for OCR setup

**Deliverables:**
- Test coverage report (HTML + summary)
- CI pipeline configuration
- Updated README.md with OCR setup

### Story 1.4: Core Pipeline Architecture Pattern

**Priority: 🔴 CRITICAL**

1. **PipelineStage Protocol:**
   - Create `core/protocol.py` with `PipelineStage[Input, Output]` (PEP 544)
   - Replace ABC with Protocol for flexibility

2. **Pydantic Models:**
   - Convert frozen dataclasses → Pydantic BaseModel
   - Add runtime validation with Pydantic v2
   - Preserve immutability with `model_config = ConfigDict(frozen=True)`

3. **Extractor Adapter:**
   - Create `ExtractorAdapter[BaseExtractor → PipelineStage[Path, Document]]`
   - Wrap brownfield extractors with adapter pattern
   - Test adapter with all 6 extractors

4. **Error Code Registry:**
   - Create `core/error_codes.py` with constants
   - Create `error_codes.yaml` with registry
   - Update extractors to use constants

5. **Config Loading Refactor:**
   - Extract to `BaseExtractor._load_config()` helper
   - Remove duplication across extractors

**Deliverables:**
- `core/protocol.py` with PipelineStage
- `core/models.py` with Pydantic models
- `core/adapter.py` with ExtractorAdapter
- `core/error_codes.py` + `error_codes.yaml`
- Updated extractors using shared config helper

## 6.2 Epic 2 Priorities (Normalization)

**Focus: Fill critical FR gaps (FR-N1, FR-N2, FR-N3, FR-E3, FR-Q1)**

### Story 2.1: Text Normalization & Cleaning (FR-N1) ⭐

**Priority: 🔴 CRITICAL (Product Magic)**

1. **Create** `normalize/cleaning.py`:
   - OCR artifact removal (garbled characters, repeated symbols)
   - Whitespace normalization (excessive blank lines, spacing)
   - Header/footer detection and removal (page numbers, repeated headers)
   - Formatting noise removal (preserve lists, code blocks)
   - Deterministic cleaning (same input → same output)

2. **Enhance** DOCX extractor:
   - Implement image extraction (DOCX-IMAGE-001)
   - Follow PPTX pattern for ImageMetadata

3. **Rewrite** TXT extractor:
   - Add encoding detection (UTF-8, Latin-1, etc.)
   - Add markdown parsing (markdown-it-py)
   - Add log structure parsing (regex patterns)
   - Add infrastructure integration

**Deliverables:**
- `normalize/cleaning.py` with artifact removal
- Enhanced DOCX extractor with images
- Rewritten TXT extractor with markdown support

### Story 2.2: Entity Extraction & Normalization (FR-N2)

**Priority: 🔴 HIGH**

1. **Implement** entity extraction:
   - Integrate spaCy for NER
   - Support 6 audit entity types (processes, risks, controls, regulations, policies, issues)
   - Extract entities from ContentBlocks

2. **Create** `normalize/entities.py`:
   - Standardize entity formatting ("Risk #123" vs "Risk-123" → "Risk-123")
   - Apply acronym/abbreviation dictionary (configurable)
   - Consistent capitalization per entity type
   - Cross-reference resolution (link mentions to definitions)

**Deliverables:**
- `normalize/metadata.py` with spaCy integration
- `normalize/entities.py` with normalization rules

### Story 2.3: Schema Standardization (FR-N3)

**Priority: 🔴 HIGH**

1. **Create** `normalize/schema.py`:
   - Document type detection (Word report, Excel matrix, Archer export)
   - Type-specific schema transformations
   - Field name standardization across source systems
   - Relationship preservation (risk → control mappings)
   - Consistent metadata structure generation

**Deliverables:**
- `normalize/schema.py` with transformation rules

## 6.3 Epic 3 Priorities (Chunking & Output)

**Focus: Semantic chunking (FR-C1) and multiple output formats (FR-C3)**

### Story 3.1: Semantic Chunking Engine (FR-C1) ⭐

**Priority: 🔴 CRITICAL (Product Magic)**

1. **Refactor** ChunkedTextFormatter → `chunk/chunker.py`:
   - Sentence boundary detection (nltk or spaCy)
   - Section boundary respect (heading-aware chunking)
   - Configurable chunk size (256-512 tokens, default)
   - Configurable overlap (10-20%, default)
   - Deterministic algorithm

2. **Create** `chunk/entity_aware.py`:
   - Entity-aware chunking (keep entity mentions within chunks)
   - Relationship preservation across chunk boundaries
   - Structure-awareness (preserve heading context)

**Deliverables:**
- `chunk/chunker.py` with semantic boundaries
- `chunk/entity_aware.py` with entity awareness

### Story 3.2: Chunk Metadata & Quality (FR-C2)

**Priority: 🔴 HIGH**

1. **Create** `chunk/metadata.py`:
   - Attach rich metadata: source file, section context, entity tags
   - Quality score (readability, coherence)
   - Document type classification
   - Chunk position, word/token count

**Deliverables:**
- `chunk/metadata.py` with enrichment

### Story 3.4-3.6: Multiple Output Formats (FR-C3)

**Priority: 🔴 HIGH**

1. **Refactor** existing formatters:
   - `output/json.py` (adapt to Pydantic models)
   - `output/markdown.py` (complete table rendering)

2. **Create** new formatters:
   - `output/csv.py` (tabular index with chunk text + metadata)
   - `output/txt.py` (plain text, one chunk per file or concatenated)

3. **Implement** configurable output organization:
   - By document (each source → output folder)
   - By entity type (group chunks by entity)
   - Flat structure (all chunks in single directory)

**Deliverables:**
- Refactored JSON/Markdown formatters
- New CSV/TXT formatters
- Flexible output organization

## 6.4 Epic 4 Priorities (Semantic Analysis)

**Focus: Classical NLP analysis (FR-S1, FR-S2, FR-S3, FR-S4)**

### Story 4.1-4.4: Semantic Analysis Suite

**Priority: 🟡 MEDIUM (Not RAG-critical, but valuable)**

1. **Create** `semantic/tfidf.py` (FR-S1):
   - TF-IDF vectorization with scikit-learn
   - Configurable vocabulary size (10,000 features)
   - N-gram range (1-2, default)
   - Term importance rankings

2. **Create** `semantic/similarity.py` (FR-S2):
   - Cosine similarity between documents/chunks
   - Top-N most similar items
   - Similarity threshold (0.8, default)
   - Similarity matrix generation

3. **Create** `semantic/lsa.py` (FR-S3):
   - TruncatedSVD (LSA) for dimensionality reduction
   - Configurable dimensions (100-300 components)
   - Semantic clustering

4. **Create** `semantic/quality.py` (FR-S4):
   - Integrate textstat library
   - Readability scores (Flesch-Kincaid, Gunning Fog, SMOG)
   - Lexical diversity
   - Quality scores in chunk metadata

**Deliverables:**
- Complete `semantic/` module with TF-IDF, similarity, LSA, quality metrics

## 6.5 Epic 5 Priorities (CLI & Configuration)

**Focus: User experience improvements (FR-U1-U4, FR-B3-B4, FR-O1-O3)**

### Story 5.1: Refactored CLI with Typer (FR-U1)

**Priority: 🟡 MEDIUM**

1. **Migrate** Click → Typer:
   - Rewrite `cli.py` with Typer framework
   - Pipeline-style commands with pipe delimiter
   - Single-step and pipeline modes
   - Preserve Rich progress display

2. **Implement** preset configurations (FR-U4):
   - `--preset chatgpt` (256 token chunks, TXT format)
   - `--preset knowledge-graph` (entity extraction, relationship preservation)
   - `--preset high-accuracy` (max quality validation, lower throughput)
   - Custom presets in config file

**Deliverables:**
- Typer-based CLI with pipeline support
- Preset configurations

### Story 5.2: Enhanced Configuration Management (FR-B3)

**Priority: 🟡 MEDIUM**

1. **Enhance** ConfigManager:
   - Config versioning for reproducibility (FR-O2)
   - Processing metadata persistence
   - Hot-reload notifications
   - Config diff tracking

**Deliverables:**
- Enhanced ConfigManager with versioning

### Story 5.4: Batch Optimization (FR-B4)

**Priority: 🟢 LOW**

1. **Implement** incremental processing:
   - Hash-based file detection
   - Skip unchanged files
   - Processing manifest/index
   - Force re-processing option

**Deliverables:**
- Incremental processing with skip logic

## 6.6 Deprecation Plan

**Timeline:**
- **Epic 1-4:** Brownfield and new architecture coexist (parallel structures)
- **Epic 5:** Add deprecation warnings to brownfield packages
- **Post-Epic 5 (v2.0):** Remove brownfield packages

**Deprecation warnings (Epic 5):**
```python
import warnings
warnings.warn(
    "src.extractors is deprecated, use src.data_extract.extract instead",
    DeprecationWarning,
    stacklevel=2
)
```

---

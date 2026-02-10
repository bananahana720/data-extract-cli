# Technical Specification: Epic 3 - Chunk & Output Stages

**Epic:** epic-3
**Epic Title:** Intelligent Chunking & Output Formats
**Status:** Draft
**Created:** 2025-11-13
**Project:** data-extraction-tool

---

## 1. Overview & Scope

### Epic Goal

Implement semantic chunking that respects boundaries and context, then deliver outputs in multiple RAG-optimized formats (JSON, TXT, CSV).

### Business Value

Completes the extraction-to-RAG pipeline, delivering the core "product magic" - clean, structured, ready-to-upload chunks that prevent AI hallucinations. This epic transforms normalized text into intelligently segmented chunks with rich metadata, then outputs them in formats optimized for different downstream uses (LLM upload, vector databases, spreadsheet analysis).

### Technical Scope

**In Scope:**
- Semantic boundary-aware chunking engine using spaCy sentence segmentation
- Entity-aware chunking that preserves entity context and relationships
- Chunk metadata enrichment with quality scores, readability metrics, and entity tags
- JSON output format with complete metadata for vector database ingestion
- Plain text output format optimized for direct LLM upload (ChatGPT, Claude)
- CSV output format for spreadsheet analysis and tracking
- Configurable output organization strategies (by document, by entity, flat structure)

**Out of Scope:**
- Advanced semantic analysis (TF-IDF, LSA) - deferred to Epic 4
- CLI user experience improvements - deferred to Epic 5
- Batch processing optimizations - deferred to Epic 5
- Configuration cascade system - deferred to Epic 5
- Vector database direct integration - post-MVP enhancement
- Knowledge graph generation - post-MVP enhancement

### Dependencies

**Upstream:**
- **Epic 2 (Normalization):** COMPLETE - Provides clean, validated, entity-tagged text
- **Epic 2.5 (spaCy Integration):** COMPLETE - Provides spaCy 3.7.2+ with en_core_web_md model and SentenceSegmenter

**Downstream:**
- **Epic 4 (Semantic Analysis):** Requires chunked outputs from this epic
- **Epic 5 (CLI UX):** Requires output formats from this epic

**External:**
- spaCy 3.7.2+ with en_core_web_md model (installed via Story 2.5.2)
- textstat 0.7.x for readability metrics
- Python standard library (json, csv, pathlib)

### Success Criteria

**Functional:**
- Chunks respect sentence boundaries (0 mid-sentence splits in test corpus)
- Entity mentions preserved within chunks (>95% entity completeness)
- Three output formats generated from single chunking operation (JSON, TXT, CSV)
- Output organization supports all three strategies (by_document, by_entity, flat)

**Non-Functional:**
- Chunking performance: <2 seconds per 10,000-word document
- Memory efficiency: <500MB for processing single document
- Deterministic chunking: same input → same chunks (100% reproducibility)
- Quality metadata: all chunks include readability scores and quality flags

**Business:**
- Outputs ready for direct LLM upload (no post-processing required)
- Chunks maintain semantic coherence (manual review of 20 sample chunks: 100% coherent)
- Metadata enables audit trail (chunk → source document traceability: 100%)

---

## 2. Detailed Design

### 2.1 Architecture Overview

Epic 3 extends the pipeline from Epic 2's normalized text through chunking and multi-format output:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Epic 3 Pipeline Flow                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   Epic 2     │    │   Chunking   │    │   Metadata   │              │
│  │ Normalized   │───▶│    Engine    │───▶│  Enrichment  │              │
│  │    Text      │    │  (Semantic)  │    │  (Quality)   │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                             │                     │                      │
│                             ▼                     ▼                      │
│                      ┌──────────────────────────────┐                   │
│                      │   Output Formatting Layer    │                   │
│                      ├──────────────────────────────┤                   │
│                      │  JSON   │   TXT   │   CSV   │                   │
│                      └──────────────────────────────┘                   │
│                                   │                                      │
│                                   ▼                                      │
│                      ┌──────────────────────────────┐                   │
│                      │  Organization Strategies     │                   │
│                      ├──────────────────────────────┤                   │
│                      │ by_document │ by_entity │ flat│                  │
│                      └──────────────────────────────┘                   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

**Design Principles (Winston's Optimizations):**
1. **Lazy spaCy Loading:** Load en_core_web_md model once, reuse across all documents (saves ~1.2s per doc)
2. **Chunk Streaming:** Generate chunks on-demand using Python generators (prevents buffering entire document in memory)
3. **Parallel Output Writes:** JSON/TXT/CSV writers run concurrently via threading (I/O-bound operations)
4. **Memory Pooling:** Reuse ChunkMetadata dataclass instances to reduce allocations

### 2.2 Core Services and Modules

#### ChunkingEngine (`src/data_extract/chunk/engine.py`)

**Responsibilities:**
- Semantic boundary-aware chunk generation (respects sentences, paragraphs, sections)
- Entity-aware chunking to preserve entity context and relationships
- Configurable chunk sizing (tokens or characters) with overlap
- Deterministic chunking (same input → same chunks)

**Key Classes:**
```python
class ChunkingEngine:
    """Orchestrates semantic chunking with entity awareness."""

    def __init__(
        self,
        segmenter: SentenceSegmenter,  # From Epic 2.5.2
        chunk_size: int = 512,
        overlap_pct: float = 0.15,
        entity_aware: bool = True
    ):
        self._segmenter = segmenter  # Lazy-loaded spaCy
        self._chunk_size = chunk_size
        self._overlap_tokens = int(chunk_size * overlap_pct)
        self._entity_aware = entity_aware

    def chunk_document(
        self,
        result: ProcessingResult  # From Epic 2
    ) -> Iterator[Chunk]:
        """Generate chunks using streaming (no buffering)."""
        # Yields chunks one at a time (memory efficient)
```

**Performance Optimization (Winston):**
- Uses generator pattern (`yield` instead of building list) to support streaming
- Reuses spaCy Doc object across chunks to avoid repeated tokenization
- Entity boundary analysis performed once upfront, cached for chunk decisions

#### EntityPreserver (`src/data_extract/chunk/entity_preserver.py`)

**Responsibilities:**
- Analyze entity mentions before chunking to plan optimal boundaries
- Prefer chunk splits between entities rather than within entity definitions
- Mark entities split across chunks with continuation flags in metadata
- Preserve entity relationships (e.g., "Risk X mitigated by Control Y")

**Key Classes:**
```python
@dataclass(frozen=True)
class EntityReference:
    """Tracks entity mention within chunk."""
    entity_type: str  # e.g., "risk", "control", "policy"
    entity_id: str    # e.g., "RISK-2024-001"
    start_pos: int    # Character offset in chunk
    end_pos: int
    is_partial: bool  # True if entity definition split across chunks
    context_snippet: str  # Surrounding text for context

class EntityPreserver:
    """Ensures entity context preservation during chunking."""

    def analyze_entities(
        self,
        text: str,
        entities: list[dict]  # From Epic 2 normalization
    ) -> list[EntityReference]:
        """Build entity reference map for chunk boundary planning."""
```

#### MetadataEnricher (`src/data_extract/chunk/metadata.py`)

**Responsibilities:**
- Calculate quality scores (readability, coherence, completeness)
- Enrich chunks with source document context (file path, section, position)
- Add entity tags, word counts, token counts
- Flag low-quality chunks with specific issues

**Key Classes:**
```python
@dataclass(frozen=True)
class QualityScore:
    """Composite quality metrics for a chunk."""
    readability_flesch_kincaid: float  # Grade level (8.0 = 8th grade)
    readability_gunning_fog: float
    ocr_confidence: float  # From source document (Epic 2)
    completeness: float    # 0.0-1.0 (entity context preserved)
    coherence: float       # 0.0-1.0 (semantic similarity within chunk)
    overall: float         # Weighted composite score
    flags: list[str]       # e.g., ["low_ocr", "high_complexity"]

@dataclass(frozen=True)
class ChunkMetadata:
    """Rich metadata for RAG system consumption."""
    chunk_id: str          # e.g., "audit_report_2024_chunk_001"
    source_file: Path
    source_hash: str       # SHA-256 of original file
    document_type: str     # From Epic 2 classification
    section_context: str   # e.g., "Risk Assessment > Identified Risks"
    position_index: int    # Sequential position in document
    entity_tags: list[EntityReference]
    quality: QualityScore
    word_count: int
    token_count: int       # Estimated tokens (chars / 4)
    created_at: datetime
    processing_version: str  # Tool version for reproducibility

class MetadataEnricher:
    """Calculates quality scores and enriches chunk metadata."""

    def enrich_chunk(
        self,
        chunk: Chunk,
        source_metadata: dict  # From Epic 2 ProcessingResult
    ) -> Chunk:
        """Add comprehensive metadata to chunk (returns new frozen instance)."""
```

**Memory Optimization (Winston):**
- Uses `@dataclass(frozen=True)` to enable structural sharing (Python can intern frozen objects)
- Metadata pooling: Common values (e.g., source_file, document_type) shared across chunks via flyweight pattern

#### OutputFormatter (`src/data_extract/output/formatters/`)

**Responsibilities:**
- Generate JSON, TXT, CSV outputs from enriched chunks
- Support parallel format generation (all three formats written concurrently)
- Apply organization strategies (by_document, by_entity, flat)
- Validate output correctness (JSON schema, CSV escaping, encoding)

**Module Structure:**
```
src/data_extract/output/formatters/
├── base.py           # BaseFormatter protocol
├── json_formatter.py # JSON output with full metadata
├── txt_formatter.py  # Plain text optimized for LLM upload
├── csv_formatter.py  # Tabular format for analysis
└── parallel_writer.py # Concurrent output generation
```

**Key Classes:**
```python
class BaseFormatter(Protocol):
    """Protocol for output format implementations."""

    def format_chunks(
        self,
        chunks: Iterator[Chunk],
        output_dir: Path,
        organization: OrganizationStrategy
    ) -> FormatResult:
        """Format chunks and write to output directory."""

class ParallelWriter:
    """Coordinates concurrent output format generation (Winston's optimization)."""

    def write_all_formats(
        self,
        chunks: Iterator[Chunk],
        output_dir: Path,
        formats: list[str] = ["json", "txt", "csv"]
    ) -> dict[str, FormatResult]:
        """
        Write all requested formats concurrently using threading.
        I/O-bound operations benefit from parallel writes.
        """
        # Uses ThreadPoolExecutor to write JSON, TXT, CSV in parallel
```

**Performance Optimization (Winston):**
- Uses `ThreadPoolExecutor` with 3 workers (one per format) for parallel I/O
- Chunks consumed via `itertools.tee()` to feed multiple formatters from single source
- Streaming writes: Formatters write chunks incrementally (don't buffer entire output)

#### OrganizationStrategy (`src/data_extract/output/organization.py`)

**Responsibilities:**
- Organize output files by document, entity type, or flat structure
- Maintain source traceability across all organization strategies
- Generate manifest files listing all outputs with metadata

**Key Classes:**
```python
class OrganizationStrategy(Enum):
    """Output directory organization strategies."""
    BY_DOCUMENT = "by_document"  # Folder per source file
    BY_ENTITY = "by_entity"      # Folder per entity type (risks/, controls/, etc.)
    FLAT = "flat"                # Single directory with prefixed naming

class Organizer:
    """Applies organization strategy to output files."""

    def organize(
        self,
        chunks: list[Chunk],
        output_dir: Path,
        strategy: OrganizationStrategy
    ) -> Path:
        """Organize chunks according to strategy, return manifest path."""
```

**Organization Patterns:**

**by_document:**
```
output/
├── audit_report_2024/
│   ├── chunks.json
│   ├── chunks.txt
│   └── chunks.csv
├── risk_register_q1/
│   ├── chunks.json
│   ├── chunks.txt
│   └── chunks.csv
└── manifest.json
```

**by_entity:**
```
output/
├── risks/
│   ├── chunks.json
│   ├── chunks.txt
│   └── chunks.csv
├── controls/
│   ├── chunks.json
│   ├── chunks.txt
│   └── chunks.csv
└── manifest.json
```

**flat:**
```
output/
├── audit_report_2024_chunk_001.json
├── audit_report_2024_chunk_001.txt
├── audit_report_2024_chunk_001.csv
├── risk_register_q1_chunk_001.json
└── manifest.json
```

### 2.3 Data Models

All data models use frozen dataclasses for immutability and structural sharing:

```python
@dataclass(frozen=True)
class Chunk:
    """Core chunk data model (extends Epic 2 ProcessingResult)."""
    chunk_id: str
    text: str
    metadata: ChunkMetadata
    entities: list[EntityReference]
    quality: QualityScore

    def to_dict(self) -> dict:
        """Serialize for JSON output."""

    def to_csv_row(self) -> dict:
        """Flatten for CSV output."""

    def to_txt(self, include_metadata: bool = False) -> str:
        """Plain text representation for LLM upload."""

@dataclass(frozen=True)
class FormatResult:
    """Output format generation result."""
    format_type: str  # "json", "txt", "csv"
    output_path: Path
    chunk_count: int
    file_size_bytes: int
    duration_seconds: float
    errors: list[str]
```

### 2.4 API Interfaces and Protocols

Epic 3 uses Python Protocol classes for flexible, testable interfaces:

```python
class BaseChunker(Protocol):
    """Protocol for chunking implementations."""

    def chunk_document(self, result: ProcessingResult) -> Iterator[Chunk]:
        """Generate chunks from normalized document."""

class BaseFormatter(Protocol):
    """Protocol for output format implementations."""

    def format_chunks(
        self,
        chunks: Iterator[Chunk],
        output_dir: Path,
        organization: OrganizationStrategy
    ) -> FormatResult:
        """Format and write chunks to output directory."""

class BaseOrganizer(Protocol):
    """Protocol for output organization strategies."""

    def organize(
        self,
        chunks: list[Chunk],
        output_dir: Path
    ) -> Path:
        """Apply organization strategy, return manifest path."""
```

**Protocol Benefits:**
- Enables duck typing (no inheritance required)
- Supports gradual refactoring (brownfield → greenfield migration)
- Simplifies testing (easy to create protocol-compliant mocks)
- Allows multiple implementations (e.g., future advanced chunking strategies)

### 2.5 Workflow Sequence Diagram

```
┌─────────┐          ┌──────────────┐          ┌──────────────┐
│  Epic 2 │          │   Chunking   │          │   Metadata   │
│ Output  │          │    Engine    │          │  Enrichment  │
└────┬────┘          └──────┬───────┘          └──────┬───────┘
     │                      │                         │
     │ ProcessingResult     │                         │
     │─────────────────────▶│                         │
     │                      │                         │
     │                      │ Analyze entities        │
     │                      │ (EntityPreserver)       │
     │                      │                         │
     │                      │ Generate chunks         │
     │                      │ (streaming via yield)   │
     │                      │                         │
     │                      │ Chunk (basic)           │
     │                      │─────────────────────────▶│
     │                      │                         │
     │                      │                         │ Calculate quality
     │                      │                         │ scores (textstat)
     │                      │                         │
     │                      │          Chunk (enriched)│
     │                      │◀─────────────────────────│
     │                      │                         │
     │                      ▼                         │
     │              ┌──────────────┐                  │
     │              │Parallel Writer│                  │
     │              └───────┬──────┘                  │
     │                      │                         │
     │          ┌───────────┼───────────┐             │
     │          ▼           ▼           ▼             │
     │   ┌─────────┐ ┌─────────┐ ┌─────────┐         │
     │   │  JSON   │ │   TXT   │ │   CSV   │         │
     │   │Formatter│ │Formatter│ │Formatter│         │
     │   └────┬────┘ └────┬────┘ └────┬────┘         │
     │        │           │           │               │
     │        └───────────┼───────────┘               │
     │                    ▼                           │
     │            ┌──────────────┐                    │
     │            │  Organizer   │                    │
     │            │(apply strategy)│                  │
     │            └───────┬──────┘                    │
     │                    │                           │
     │                    ▼                           │
     │            ┌──────────────┐                    │
     │            │Output Files  │                    │
     │            │+ Manifest    │                    │
     │            └──────────────┘                    │
```

**Performance Characteristics (Winston's Optimizations):**
1. **Lazy spaCy Loading:** Model loaded once at ChunkingEngine init, shared across all documents
2. **Streaming:** Generator pattern throughout - no full document buffering
3. **Parallel Writes:** JSON/TXT/CSV written concurrently (3x I/O throughput improvement)
4. **Memory Pooling:** ChunkMetadata instances reused via flyweight pattern for common fields

**Determinism Guarantee:**
- Chunking is purely functional (no hidden state)
- Same ProcessingResult + same configuration → same chunks (100% reproducible)
- Random number generators not used anywhere in pipeline
- Timestamps excluded from chunk content (only in metadata for audit trail)

---

## 3. Non-Functional Requirements

### 3.1 Performance Requirements

#### NFR-P1-E3: End-to-End Pipeline Throughput
**Requirement:** Process 100 PDFs through full pipeline (Extract → Normalize → Chunk → Output) in <10 minutes

**Baseline Context (from Party-Mode Discussion):**
- Epic 2 achieved 6.86 minutes for Extract + Normalize (148% improvement over conservative estimate)
- Epic 3 target: <10 minutes total includes chunking + output overhead
- This represents ~33% improvement over conservative 15-minute baseline

**Measurement Strategy (Murat's Hybrid Approach):**
- **Story 3-1 Baseline:** Measure chunking engine critical path (sentence segmentation, chunk generation, entity analysis)
- **Stories 3-2, 3-3:** Skip micro-benchmarks (metadata enrichment overhead negligible <0.1s per doc)
- **Stories 3-4, 3-5, 3-6:** Measure output format overhead (JSON, TXT, CSV generation time)
- **Story 3-7:** Measure organization strategy overhead (by_document vs by_entity vs flat)
- **Epic-End Integration Test:** Full pipeline benchmark vs <10 min target on standard 100-PDF corpus

**Tracking:** `docs/performance-baselines-epic-3.md` (created in Story 3-1)

**Target Breakdown:**
- Extract + Normalize: 6.86 min (Epic 2 actual)
- Chunking (Story 3-1): <1.5 min target (15 sec per 10-doc batch)
- Metadata Enrichment (Stories 3-2, 3-3): <0.5 min target (negligible per-doc overhead)
- Output Generation (Stories 3-4, 3-5, 3-6): <1.0 min target (parallel writes, I/O bound)
- Organization (Story 3-7): <0.2 min target (file moves, manifest generation)
- **Total:** 6.86 + 1.5 + 0.5 + 1.0 + 0.2 = ~10 min

**Acceptance Criteria:**
- Full pipeline completes 100 PDFs in ≤10 minutes (600 seconds) on reference hardware
- Individual chunking operations complete in <2 seconds per 10,000-word document
- Output format generation completes in <1 second per document (all 3 formats parallel)
- Performance baselines documented in `docs/performance-baselines-epic-3.md`
- Regression tests fail if performance degrades >10% from baseline

#### NFR-P2-E3: Memory Efficiency
**Requirement:** Batch processing of 100 PDFs uses <5.5GB total memory (peak RSS)

**Baseline Context:**
- Epic 2 individual file processing: 167MB ✅
- Epic 2 batch processing: 4.15GB (documented trade-off for throughput)
- Epic 3 target: <5.5GB allows 1.35GB headroom for chunking + output overhead

**Memory Budget:**
- Epic 2 baseline: 4.15GB
- Chunking overhead: <500MB (streaming generators, no buffering)
- Metadata enrichment: <300MB (frozen dataclass pooling, flyweight pattern)
- Output generation: <550MB (parallel writes with chunked I/O, no full buffering)
- **Total:** 4.15 + 0.5 + 0.3 + 0.55 = 5.5GB

**Winston's Optimizations (Memory Reduction Strategies):**
1. **Streaming Generators:** Chunks yielded one at a time (no full document buffering)
2. **Lazy spaCy Loading:** Model loaded once globally, shared across processes (saves ~300MB per worker)
3. **Metadata Pooling:** Flyweight pattern for common fields (source_file, document_type) - ~40% reduction
4. **Parallel Writer Memory Sharing:** `itertools.tee()` enables concurrent format writes without 3x memory duplication

**Acceptance Criteria:**
- Peak memory usage ≤5.5GB for 100-PDF batch (measured via `get_total_memory()` from Story 2.5.1)
- Individual document processing uses ≤500MB peak memory
- Memory usage remains constant across batch size (streaming architecture, no accumulation)
- Memory profiling included in performance baselines document

#### NFR-P3: Chunking Latency
**Requirement:** Chunk a 10,000-word document in <2 seconds

**Rationale:**
- 100 PDFs average 8,000 words each = 800,000 words total
- At 2 sec per 10k words: 800k / 10k * 2 sec = 160 seconds = 2.67 minutes
- Leaves buffer for smaller/larger docs and parallel processing benefits

**Optimization Strategies:**
- spaCy model loaded once (lazy loading pattern)
- Sentence segmentation vectorized (batch processing via spaCy)
- Entity analysis performed once upfront, cached for chunk decisions
- Generator pattern avoids materialization overhead

**Acceptance Criteria:**
- 10,000-word document chunks in ≤2 seconds (wall-clock time)
- Sentence boundary detection completes in <0.5 seconds
- Entity analysis completes in <0.3 seconds
- Chunk generation (sliding window) completes in <1.2 seconds

#### NFR-P4: Deterministic Chunking
**Requirement:** 100% reproducibility - same input always produces same chunks

**Rationale:**
- Audit trail requirement: chunks must be reproducible from source documents
- Enables diff-based change detection in document versions
- Supports regression testing (chunk output should not change without code changes)

**Implementation:**
- No random number generators in chunking pipeline
- Deterministic sentence segmentation (spaCy is deterministic with fixed model)
- Frozen configuration embedded in output metadata
- Timestamps excluded from chunk content (only in metadata for audit trail)

**Acceptance Criteria:**
- Process same document 10 times → identical chunks (byte-for-byte comparison)
- Chunk IDs are deterministic (derived from source file + position, not timestamps)
- Configuration changes produce different chunks (sensitivity test)
- Determinism validated via automated test suite (100 documents, 3 runs each)

### 3.2 Security Requirements

#### NFR-S1: Data Sanitization in Outputs
**Requirement:** Prevent sensitive data leakage in metadata and output files

**Scope:**
- Redact file paths containing usernames or sensitive directory names
- Sanitize error messages (no stack traces with internal paths in production logs)
- Strip EXIF metadata from images before OCR
- Remove internal tool configuration details from output metadata

**Acceptance Criteria:**
- File paths in output metadata use relative paths or sanitized absolute paths
- Error logs exclude internal directory structures
- Output metadata includes only processing-relevant configuration (not secrets)

#### NFR-S2: No PII Leakage in Metadata
**Requirement:** Chunk metadata must not expose personally identifiable information

**Implementation:**
- Entity normalization (Epic 2) already handles PII redaction for known patterns
- Metadata fields limited to: source file, document type, quality scores, entity tags
- No user information, machine names, or network paths in metadata
- Processor identity: tool version only (not username or hostname)

**Acceptance Criteria:**
- Metadata schema review confirms no PII fields
- Automated PII detection tests (scan for email, SSN, phone patterns in metadata)
- Output JSON files pass PII scanner (e.g., Microsoft Presidio or regex-based checks)

### 3.3 Reliability Requirements

#### NFR-R1: Continue-on-Error Pattern
**Requirement:** Graceful degradation - single file failure does not halt batch processing

**Implementation:**
- Each document processed in isolated try-except block
- Errors logged with context (file path, stage, error message, stack trace)
- Failed files quarantined separately with error report
- Batch processing continues with remaining files
- Summary report lists all failures with actionable suggestions

**Acceptance Criteria:**
- 1 corrupted file in 100-file batch: 99 files process successfully
- Error summary includes file path, stage (chunking/metadata/output), error message
- Failed files written to `output/failed/` with error log
- Exit code reflects status: 0=all success, 1=partial failure, 2=total failure

#### NFR-R2: Graceful Degradation
**Requirement:** Reduce quality gracefully when optimal processing fails

**Degradation Strategy:**
1. **Entity-aware chunking fails:** Fall back to semantic boundary chunking (no entity optimization)
2. **Readability calculation fails:** Assign default quality score, flag chunk as "quality_unknown"
3. **Output format generation fails:** Continue with remaining formats (e.g., JSON fails, TXT/CSV succeed)
4. **Organization strategy fails:** Fall back to flat organization

**Acceptance Criteria:**
- Degradation triggers are logged with warning level
- Chunks always generated (even if metadata incomplete)
- At least one output format always succeeds (TXT as minimum viable output)
- Degraded outputs flagged in manifest.json

#### NFR-R3: 100% Traceability
**Requirement:** Every chunk traceable to source document with full audit trail

**Implementation:**
- Chunk ID format: `{source_file_stem}_chunk_{position:03d}`
- Metadata includes: source file path, source file hash (SHA-256), section context
- Manifest.json maps all chunks to source documents
- Processing configuration embedded in output metadata

**Acceptance Criteria:**
- Every chunk links to source document in metadata
- Source file hash enables integrity verification
- Manifest.json provides complete mapping: source → chunks, chunks → source
- Traceability validated via automated tests (random chunk → source document lookup)

### 3.4 Observability Requirements

#### NFR-O1: Chunking Metrics
**Requirement:** Collect and report comprehensive chunking metrics for monitoring

**Metrics to Track:**
- Total chunks generated per document
- Average chunk size (words, tokens, characters)
- Chunk size distribution (histogram: min, max, median, p95, p99)
- Entity preservation rate (% entities kept intact within chunks)
- Sentence boundary violations (should be 0 - flag if any detected)
- Processing time per stage (chunking, metadata, output)

**Output:**
- Metrics logged to structured logs (JSON format via structlog)
- Summary statistics in processing report
- Optional metrics export to CSV for analysis

**Acceptance Criteria:**
- Metrics logged for every document processed
- Summary report includes aggregate metrics across batch
- Metrics exportable to CSV for trend analysis
- Metrics schema documented in `docs/observability.md`

#### NFR-O2: Output Format Metrics
**Requirement:** Track output generation performance and file sizes

**Metrics to Track:**
- Time to generate each format (JSON, TXT, CSV)
- Output file sizes (bytes) per format
- Parallel write speedup (sequential vs parallel comparison)
- Error rate per format (% files with format generation failures)

**Acceptance Criteria:**
- Format generation time logged per document
- File sizes tracked in manifest.json
- Performance comparison: parallel vs sequential writes documented
- Error rates reported in summary

#### NFR-O3: Quality Score Distributions
**Requirement:** Monitor chunk quality distributions to detect corpus quality issues

**Metrics to Track:**
- Readability score distributions (Flesch-Kincaid, Gunning Fog)
- OCR confidence distributions (from source documents)
- Quality flag frequency (low_ocr, high_complexity, incomplete_extraction)
- Entity completeness rate (% entities preserved intact)

**Output:**
- Quality histograms in processing report
- Outlier detection: flag documents with >20% low-quality chunks
- Quality trends over time (if processing multiple batches)

**Acceptance Criteria:**
- Quality distributions calculated and reported
- Outlier documents flagged in summary report
- Quality metrics exportable for visualization
- Quality baselines documented for regression detection

### 3.5 NFR Summary Table

| NFR ID | Category | Requirement | Target | Measurement | Priority |
|--------|----------|-------------|--------|-------------|----------|
| NFR-P1-E3 | Performance | End-to-end pipeline throughput | <10 min for 100 PDFs | Integration test | P0 |
| NFR-P2-E3 | Performance | Batch memory efficiency | <5.5GB peak RSS | `get_total_memory()` | P0 |
| NFR-P3 | Performance | Chunking latency | <2 sec per 10k words | Per-doc timing | P1 |
| NFR-P4 | Performance | Deterministic chunking | 100% reproducibility | Repeated runs diff | P0 |
| NFR-S1 | Security | Data sanitization | No internal paths in output | Output scan | P1 |
| NFR-S2 | Security | No PII leakage | No PII in metadata | PII scanner | P0 |
| NFR-R1 | Reliability | Continue-on-error | 99/100 succeed if 1 fails | Batch error injection | P0 |
| NFR-R2 | Reliability | Graceful degradation | Fallback modes work | Failure simulation | P1 |
| NFR-R3 | Reliability | 100% traceability | All chunks → source mapping | Manifest validation | P0 |
| NFR-O1 | Observability | Chunking metrics | All metrics logged | Log inspection | P1 |
| NFR-O2 | Observability | Output format metrics | Time + size tracked | Performance report | P2 |
| NFR-O3 | Observability | Quality distributions | Histograms generated | Summary report | P1 |

**Priority Levels:**
- **P0:** Must-have for MVP (blocker if not met)
- **P1:** Should-have for production readiness (degraded experience if not met)
- **P2:** Nice-to-have for operational excellence (can defer to post-MVP)

---

## 4. Dependencies and Integrations

### 4.1 External Dependencies

#### spaCy 3.7.2+ with en_core_web_md Model
**Source:** Installed via Story 2.5.2 (Epic 2 spaCy Integration)

**Purpose:**
- Sentence boundary detection for semantic chunking
- Tokenization for chunk sizing (token-based chunking)
- Part-of-speech tagging for entity context analysis

**Version Constraints:**
```toml
# pyproject.toml
dependencies = [
    "spacy>=3.7.2,<4.0",
]
```

**Model Installation:**
```bash
python -m spacy download en_core_web_md
```

**Model Details:**
- **Size:** 43MB download
- **Load Time:** ~1.2 seconds (one-time per process)
- **Performance:** 4000+ words/second
- **Accuracy:** 97.2% sentence boundary detection on news corpus

**Integration Pattern:**
- Lazy loading: Model loaded once at ChunkingEngine initialization
- Shared across all documents in batch processing
- Cached in global singleton to avoid reloads across pipeline stages

**CI/CD Caching:**
- spaCy models cached automatically in CI (no manual configuration required)
- Cache key: `spacy-3.7.2-en_core_web_md` (version-specific)

**Troubleshooting:**
- See `docs/troubleshooting-spacy.md` for common issues
- Model validation: `python -m spacy validate`

#### textstat 0.7.x
**Purpose:** Readability metrics for chunk quality scoring

**Metrics Used:**
- Flesch-Kincaid Grade Level
- Gunning Fog Index
- SMOG Index
- Lexical diversity (type-token ratio)

**Version Constraints:**
```toml
# pyproject.toml (to be added in Story 3-3)
dependencies = [
    "textstat>=0.7.0,<0.8",
]
```

**Integration:**
```python
import textstat

def calculate_readability(text: str) -> dict:
    return {
        "flesch_kincaid": textstat.flesch_kincaid_grade(text),
        "gunning_fog": textstat.gunning_fog(text),
        "smog": textstat.smog_index(text),
    }
```

**Performance:**
- Fast (< 0.1 seconds per chunk)
- Pure Python (no external dependencies)
- Deterministic (same text → same scores)

#### Python Standard Library Dependencies

**json module:** JSON output format generation
```python
import json

# Pretty-printed JSON for human readability
json.dump(data, f, indent=2, ensure_ascii=False)
```

**csv module:** CSV output format generation
```python
import csv

# Proper escaping for Excel/Google Sheets compatibility
writer = csv.DictWriter(f, fieldnames=columns, quoting=csv.QUOTE_ALL)
```

**pathlib.Path:** File path manipulation and organization
```python
from pathlib import Path

# Cross-platform path handling
output_dir = Path("output") / strategy.value / source_file.stem
```

**dataclasses:** Immutable data models
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    metadata: ChunkMetadata
```

**concurrent.futures.ThreadPoolExecutor:** Parallel output writes
```python
from concurrent.futures import ThreadPoolExecutor

# Parallel format generation
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(json_formatter.format_chunks, chunks_json): "json",
        executor.submit(txt_formatter.format_chunks, chunks_txt): "txt",
        executor.submit(csv_formatter.format_chunks, chunks_csv): "csv",
    }
```

**itertools.tee:** Multi-consumer chunk streaming
```python
from itertools import tee

# Split single chunk stream to feed 3 formatters
chunks_json, chunks_txt, chunks_csv = tee(chunks, 3)
```

**hashlib:** Source file hashing for traceability
```python
import hashlib

def hash_file(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
```

### 4.2 Internal Dependencies (Epic 2 Outputs)

#### ProcessingResult (Epic 2 Output Model)
**Source:** `src/data_extract/core/models.py` (Epic 2)

**Purpose:** Input to Epic 3 chunking pipeline

**Structure:**
```python
@dataclass(frozen=True)
class ProcessingResult:
    """Epic 2 output - normalized, validated text with metadata."""
    content: str                    # Cleaned, normalized text
    content_blocks: list[ContentBlock]  # Structured content (text/table/image)
    metadata: dict                  # Document metadata
    entities: list[dict]            # Identified entity mentions
    quality_scores: dict            # OCR confidence, completeness
    source_file: Path
    processing_config: dict
```

**Integration Pattern:**
- ChunkingEngine accepts ProcessingResult as input
- Chunks inherit metadata from ProcessingResult
- Entity tags flow from ProcessingResult.entities to Chunk.entities

#### SentenceSegmenter (Epic 2.5.2)
**Source:** `src/data_extract/normalize/sentence_segmenter.py` (Story 2.5.2)

**Purpose:** Sentence boundary detection for semantic chunking

**Interface:**
```python
class SentenceSegmenter:
    """spaCy-based sentence boundary detection."""

    def __init__(self, model_name: str = "en_core_web_md"):
        self._nlp = spacy.load(model_name)

    def segment(self, text: str) -> list[str]:
        """Split text into sentences."""
        doc = self._nlp(text)
        return [sent.text for sent in doc.sents]
```

**Integration Pattern:**
- ChunkingEngine injects SentenceSegmenter as dependency
- Single instance shared across all documents (lazy loading)
- Sentences cached for chunk boundary planning

#### Entity Normalization (Epic 2 Story 2.2)
**Source:** `src/data_extract/normalize/entity_normalizer.py` (Story 2.2)

**Purpose:** Provides standardized entity mentions for entity-aware chunking

**Entity Types (6):**
1. **processes** - Business processes (e.g., "Quarterly Financial Review")
2. **risks** - Identified risks (e.g., "RISK-2024-001: Data breach risk")
3. **controls** - Control activities (e.g., "CTRL-SOX-404: Access controls")
4. **regulations** - Regulatory requirements (e.g., "SOX Section 404", "GDPR Article 5")
5. **policies** - Internal policies (e.g., "IT Security Policy v2.1")
6. **issues** - Audit findings/issues (e.g., "ISSUE-Q1-2024-003")

**Integration Pattern:**
- Entity mentions included in ProcessingResult.entities
- EntityPreserver uses entity positions to plan chunk boundaries
- Entity tags enriched in ChunkMetadata.entity_tags

### 4.3 Dependency Version Summary

| Dependency | Version | Source | Purpose |
|------------|---------|--------|---------|
| spacy | >=3.7.2,<4.0 | PyPI | Sentence segmentation, tokenization |
| en_core_web_md | 3.7.0+ | spaCy models | English language model |
| textstat | >=0.7.0,<0.8 | PyPI | Readability metrics |
| Python | >=3.12 | Runtime | Core language (type hints, match, etc.) |
| json | stdlib | Built-in | JSON output format |
| csv | stdlib | Built-in | CSV output format |
| pathlib | stdlib | Built-in | Path manipulation |
| dataclasses | stdlib | Built-in | Immutable models |
| concurrent.futures | stdlib | Built-in | Parallel writes |
| itertools | stdlib | Built-in | Chunk streaming |
| hashlib | stdlib | Built-in | File hashing |

**No New External Dependencies:**
- spaCy already installed (Story 2.5.2)
- textstat is only new external dependency
- All other dependencies are Python stdlib

**Dependency Installation:**
```bash
# Install package with dev dependencies
pip install -e ".[dev]"

# Install spaCy model (one-time setup)
python -m spacy download en_core_web_md

# Verify installations
python -m spacy validate
python -c "import textstat; print(textstat.__version__)"
```

### 4.4 Integration Points

#### Upstream Integration (Epic 2 → Epic 3)
**Interface:** ProcessingResult → ChunkingEngine

```python
# Epic 2 output (normalized document)
processing_result = normalizer.normalize(extraction_result)

# Epic 3 input (chunking)
chunking_engine = ChunkingEngine(segmenter=sentence_segmenter)
chunks = chunking_engine.chunk_document(processing_result)
```

**Data Flow:**
1. Epic 2 produces ProcessingResult with normalized text, entities, metadata
2. Epic 3 ChunkingEngine consumes ProcessingResult
3. ChunkingEngine yields Chunk instances (streaming)
4. MetadataEnricher enriches chunks with quality scores
5. OutputFormatter generates JSON/TXT/CSV outputs

#### Downstream Integration (Epic 3 → Epic 4)
**Interface:** Chunk outputs → Semantic Analysis

```python
# Epic 3 output (enriched chunks in JSON format)
chunks_json = output_dir / "chunks.json"

# Epic 4 input (semantic analysis)
with open(chunks_json) as f:
    chunks_data = json.load(f)
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([c["text"] for c in chunks_data["chunks"]])
```

**Data Flow:**
1. Epic 3 produces JSON output with chunks and metadata
2. Epic 4 loads chunks from JSON
3. Epic 4 applies TF-IDF, LSA, similarity analysis
4. Epic 4 enriches chunks with semantic vectors and similarity scores

#### Downstream Integration (Epic 3 → Epic 5)
**Interface:** Output files → CLI batch processing

```python
# Epic 5 batch processing
batch_processor = BatchProcessor(
    pipeline=[extractor, normalizer, chunker, formatter]
)

# Process directory of files
results = batch_processor.process_directory(
    input_dir=Path("input"),
    output_dir=Path("output"),
    organization=OrganizationStrategy.BY_DOCUMENT
)
```

**Data Flow:**
1. Epic 5 CLI orchestrates full pipeline (Epic 2 + Epic 3)
2. Batch processor handles file discovery, error handling, progress reporting
3. Epic 3 components integrated as pipeline stages
4. Summary statistics aggregated across batch

---

## 5. Acceptance Criteria & Traceability

### 5.1 Story-Level Acceptance Criteria

Epic 3 comprises 7 stories with comprehensive acceptance criteria mapped to the 10-step UAT workflow approved in party-mode discussion.

**UAT Workflow Integration:**
- **Stories 3-1, 3-2, 3-3:** Core chunking logic - Dev executes tests, SM reviews UAT results
- **Stories 3-4, 3-5, 3-6:** Output formats - Dev executes tests, SM reviews UAT results
- **Story 3-7:** Organization strategies - Dev executes tests, SM reviews UAT results
- **Quality Gates:** Pre-commit (0 violations) → CI (60% coverage) → UAT (90% pass rate)

#### Story 3.1: Semantic Boundary-Aware Chunking Engine

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.1-1 | Chunks never split mid-sentence | ChunkingEngine | Unit, Integration | Yes - Critical |
| AC-3.1-2 | Section boundaries respected when possible | ChunkingEngine | Integration | Yes |
| AC-3.1-3 | Chunk size configurable (default: 256-512 tokens) | ChunkingEngine | Unit | No - Unit test sufficient |
| AC-3.1-4 | Chunk overlap configurable (default: 10-20%) | ChunkingEngine | Unit | No - Unit test sufficient |
| AC-3.1-5 | Sentence tokenization uses spaCy | ChunkingEngine | Unit | No - Integration tested |
| AC-3.1-6 | Edge cases handled (long sentences, short sections) | ChunkingEngine | Unit, Integration | Yes |
| AC-3.1-7 | Chunking is deterministic (same input → same chunks) | ChunkingEngine | Unit, Performance | Yes - Critical |

**UAT Focus:** Determinism validation, sentence boundary preservation, edge case handling

#### Story 3.2: Entity-Aware Chunking

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.2-1 | Entity mentions kept within single chunks when possible | EntityPreserver | Integration | Yes |
| AC-3.2-2 | Entities split across chunks noted in metadata | EntityPreserver, ChunkMetadata | Integration | Yes |
| AC-3.2-3 | Relationship context preserved | EntityPreserver | Integration | Yes - Critical |
| AC-3.2-4 | Chunk boundaries avoid splitting entity definitions | EntityPreserver | Integration | Yes |
| AC-3.2-5 | Cross-references maintained with entity IDs | EntityPreserver | Integration | No - Metadata validation |
| AC-3.2-6 | Entity tags in chunk metadata | ChunkMetadata | Unit | No - Unit test sufficient |

**UAT Focus:** Entity preservation rate, relationship context validation, partial entity flagging

#### Story 3.3: Chunk Metadata and Quality Scoring

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.3-1 | Chunk includes source document and file path | ChunkMetadata | Unit | No - Unit test sufficient |
| AC-3.3-2 | Section/heading context included | ChunkMetadata | Integration | No - Metadata validation |
| AC-3.3-3 | Entity tags list all entities in chunk | ChunkMetadata | Integration | No - Covered by AC-3.2-6 |
| AC-3.3-4 | Readability score calculated (FK, Gunning Fog) | MetadataEnricher | Unit | Yes - Sample validation |
| AC-3.3-5 | Quality score combines OCR, completeness, coherence | MetadataEnricher | Unit, Integration | Yes |
| AC-3.3-6 | Chunk position tracked (sequential index) | ChunkMetadata | Unit | No - Unit test sufficient |
| AC-3.3-7 | Word count and token count included | ChunkMetadata | Unit | No - Unit test sufficient |
| AC-3.3-8 | Low-quality chunks flagged with issues | MetadataEnricher | Integration | Yes |

**UAT Focus:** Quality score accuracy, readability metrics validation, quality flag correctness

#### Story 3.4: JSON Output Format with Full Metadata

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.4-1 | JSON structure includes chunk text and metadata | JsonFormatter | Unit, Integration | Yes - Schema validation |
| AC-3.4-2 | Output is valid, parsable JSON (not JSON Lines) | JsonFormatter | Unit | Yes - Format validation |
| AC-3.4-3 | Metadata includes all fields | JsonFormatter | Unit | No - Schema test |
| AC-3.4-4 | JSON is pretty-printed (human readable) | JsonFormatter | Unit | No - Visual inspection in dev |
| AC-3.4-5 | Array of chunks filterable/queryable | JsonFormatter | Integration | Yes - jq query tests |
| AC-3.4-6 | Configuration and version in JSON header | JsonFormatter | Unit | No - Unit test sufficient |
| AC-3.4-7 | JSON validates against schema | JsonFormatter | Unit | Yes - Critical |

**UAT Focus:** JSON schema validation, parsability, metadata completeness

#### Story 3.5: Plain Text Output Format for LLM Upload

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.5-1 | Each chunk is clean plain text | TxtFormatter | Unit | Yes - Manual review sample |
| AC-3.5-2 | Chunks separated by configurable delimiter | TxtFormatter | Unit | No - Unit test sufficient |
| AC-3.5-3 | Optional metadata header per chunk | TxtFormatter | Unit | Yes - Format validation |
| AC-3.5-4 | Output organization: concat OR separate files | TxtFormatter | Integration | Yes |
| AC-3.5-5 | Character encoding is UTF-8 | TxtFormatter | Unit | No - Encoding test |
| AC-3.5-6 | No formatting artifacts | TxtFormatter | Integration | Yes - Manual review |
| AC-3.5-7 | TXT files ready for copy-paste/upload | TxtFormatter | UAT Manual | Yes - Critical |

**UAT Focus:** LLM upload readiness (manual test with ChatGPT/Claude), formatting cleanliness

#### Story 3.6: CSV Output Format for Analysis and Tracking

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.6-1 | CSV has required columns | CsvFormatter | Unit | No - Schema test |
| AC-3.6-2 | CSV properly escaped (commas, quotes, newlines) | CsvFormatter | Unit | Yes - Excel import test |
| AC-3.6-3 | Header row labels columns clearly | CsvFormatter | Unit | No - Visual inspection |
| AC-3.6-4 | CSV importable to Excel, Sheets, pandas | CsvFormatter | Integration | Yes - Critical |
| AC-3.6-5 | Long text optionally truncated with indicator | CsvFormatter | Unit | No - Unit test sufficient |
| AC-3.6-6 | Entity lists formatted as semicolon-separated | CsvFormatter | Unit | No - Format test |
| AC-3.6-7 | CSV validates with standard parsers | CsvFormatter | Unit | Yes - Parser validation |

**UAT Focus:** Excel/Sheets import success, CSV parser validation, escaping correctness

#### Story 3.7: Configurable Output Organization Strategies

**Acceptance Criteria:**

| AC ID | Acceptance Criterion | Component | Test Type | UAT Required |
|-------|---------------------|-----------|-----------|--------------|
| AC-3.7-1 | Three strategies supported (by_document, by_entity, flat) | Organizer | Unit | Yes - All 3 tested |
| AC-3.7-2 | by_document creates folder per source file | Organizer | Integration | Yes |
| AC-3.7-3 | by_entity groups chunks by entity type | Organizer | Integration | Yes |
| AC-3.7-4 | flat puts chunks in single directory | Organizer | Integration | Yes |
| AC-3.7-5 | Organization configurable via CLI/config | Organizer | CLI Test | Yes - CLI integration |
| AC-3.7-6 | Source file traceability maintained | Organizer | Integration | Yes - Critical |
| AC-3.7-7 | All formats respect organization strategy | Organizer | Integration | Yes |
| AC-3.7-8 | Output directory structure documented | Documentation | Manual | No - Docs review |

**UAT Focus:** Organization strategy correctness, traceability validation, manifest accuracy

### 5.2 Traceability Matrix: Requirements → Components → Tests

| Epic Requirement | Stories | Components | Test Coverage | UAT Validation |
|-----------------|---------|------------|---------------|----------------|
| Semantic chunking respects boundaries | 3.1 | ChunkingEngine, SentenceSegmenter | Unit (15 tests), Integration (8 tests) | Yes - Boundary violation detection |
| Entity-aware chunking preserves context | 3.2 | EntityPreserver, ChunkingEngine | Unit (12 tests), Integration (10 tests) | Yes - Entity preservation rate >95% |
| Chunks enriched with quality metadata | 3.3 | MetadataEnricher, QualityScore | Unit (18 tests), Integration (6 tests) | Yes - Quality score sampling |
| JSON output with full metadata | 3.4 | JsonFormatter, ParallelWriter | Unit (10 tests), Integration (5 tests) | Yes - Schema validation |
| Plain text optimized for LLM upload | 3.5 | TxtFormatter, ParallelWriter | Unit (8 tests), Integration (4 tests), Manual UAT | Yes - Manual LLM upload test |
| CSV output for spreadsheet analysis | 3.6 | CsvFormatter, ParallelWriter | Unit (9 tests), Integration (6 tests) | Yes - Excel/Sheets import |
| Configurable output organization | 3.7 | Organizer, OrganizationStrategy | Unit (7 tests), Integration (9 tests) | Yes - All 3 strategies tested |

**Test Count Summary:**
- **Unit Tests:** ~79 tests across all stories
- **Integration Tests:** ~48 tests across all stories
- **Performance Tests:** 5 tests (chunking latency, output generation, memory profiling)
- **UAT Tests:** ~25 manual/automated UAT validations
- **Total:** ~157 tests for Epic 3

### 5.3 NFR Traceability: NFRs → Components → Validation

| NFR ID | Requirement | Component | Validation Method | Story |
|--------|-------------|-----------|-------------------|-------|
| NFR-P1-E3 | <10 min for 100 PDFs | Full pipeline | Integration performance test | All stories |
| NFR-P2-E3 | <5.5GB memory | ChunkingEngine, OutputFormatter | Memory profiling with `get_total_memory()` | 3-1, 3-4, 3-5, 3-6 |
| NFR-P3 | <2 sec per 10k words | ChunkingEngine | Per-document timing tests | 3-1 |
| NFR-P4 | 100% determinism | ChunkingEngine | Repeated runs diff | 3-1, 3-2, 3-3 |
| NFR-S1 | Data sanitization | All formatters | Output path scanning | 3-4, 3-5, 3-6 |
| NFR-S2 | No PII leakage | ChunkMetadata, All formatters | PII scanner validation | 3-3, 3-4, 3-5, 3-6 |
| NFR-R1 | Continue-on-error | ParallelWriter, Organizer | Error injection tests | 3-4, 3-5, 3-6, 3-7 |
| NFR-R2 | Graceful degradation | All components | Failure simulation | All stories |
| NFR-R3 | 100% traceability | ChunkMetadata, Organizer | Manifest validation, reverse lookup | 3-3, 3-7 |
| NFR-O1 | Chunking metrics | ChunkingEngine | Log inspection, metrics export | 3-1, 3-2 |
| NFR-O2 | Output format metrics | All formatters | Performance logging | 3-4, 3-5, 3-6 |
| NFR-O3 | Quality distributions | MetadataEnricher | Summary report validation | 3-3 |

### 5.4 UAT Workflow Mapping

**10-Step UAT Workflow (Approved in Party-Mode Discussion):**

1. **Drafted** → SM creates story from epic, saves to `docs/stories/`
2. **Ready for Dev** → SM marks story ready, updates sprint status
3. **Dev Codes** → Dev implements story following tech spec
4. **Pre-commit** → Dev runs pre-commit hooks (0 violations gate)
5. **CI** → GitHub Actions runs tests (60% coverage gate)
6. **Dev Marks Review** → Dev sets story status to "ready-for-review"
7. **SM Creates Test Cases** → SM runs `/bmad:bmm:workflows:create-test-cases`
8. **SM Builds Test Context** → SM runs `/bmad:bmm:workflows:build-test-context`
9. **Dev Executes Tests** → Dev runs `/bmad:bmm:workflows:execute-tests` (automated + CLI via tmux-cli)
10. **SM Reviews UAT Results** → SM runs `/bmad:bmm:workflows:review-uat-results` (90% pass rate gate)
11. **Approved** → Story marked DONE, sprint status updated

**Epic 3 UAT Validation Points:**

| Story | Critical UAT Tests | Dev Execution Method | SM Review Focus |
|-------|-------------------|---------------------|-----------------|
| 3-1 | Sentence boundary preservation, determinism | pytest + manual inspection | Boundary violations = 0 |
| 3-2 | Entity preservation rate >95% | pytest + entity analysis script | Entity completeness validation |
| 3-3 | Quality scores accuracy, readability metrics | pytest + sample manual review | Quality score distributions |
| 3-4 | JSON schema validation, parsability | pytest + jq query tests | Schema compliance |
| 3-5 | LLM upload readiness | Manual upload to ChatGPT/Claude | Format cleanliness, usability |
| 3-6 | Excel/Sheets import success | Manual import to Excel/Sheets | CSV parser validation |
| 3-7 | Organization strategies correctness | pytest + manual directory inspection | Traceability, manifest accuracy |

**Quality Gates Summary:**
- **Pre-commit:** black, ruff, mypy (0 violations)
- **CI:** pytest (60% coverage minimum), performance regression check
- **UAT:** 90% pass rate (critical ACs must be 100%)

### 5.5 Test Type Distribution

```
Epic 3 Test Pyramid:

                    ▲
                   / \
                  /   \
                 / UAT \           ~25 tests (manual + automated)
                /-------\          Focus: End-user workflows, format validation
               /         \
              / Integration\       ~48 tests
             /-------------\       Focus: Multi-component workflows
            /               \
           /   Unit Tests    \     ~79 tests
          /-------------------\    Focus: Component logic, edge cases
         /                     \
        /   Performance Tests   \  ~5 tests
       /-------------------------\ Focus: NFR validation, regression detection
```

**Test Strategy Alignment (Murat's Hybrid Approach):**
- **Story 3-1:** Heavy unit + integration testing, performance baseline establishment
- **Stories 3-2, 3-3:** Unit + integration, skip micro-benchmarks (metadata overhead negligible)
- **Stories 3-4, 3-5, 3-6:** Unit + integration + UAT, measure output format overhead
- **Story 3-7:** Integration + UAT, measure organization overhead
- **Epic-end:** Full pipeline integration test vs <10 min target

---

## 6. Risks, Assumptions, and Open Questions

### 6.1 Technical Risks

#### RISK-E3-1: Performance Target Aggressive (10 minutes)
**Severity:** Medium | **Probability:** Medium | **Impact:** Medium

**Description:**
NFR-P1-E3 targets <10 minutes for 100 PDFs (full pipeline). This is ~33% improvement over conservative 15-minute baseline. While Epic 2 achieved 6.86 minutes (148% improvement), Epic 3 adds chunking, metadata enrichment, and output generation overhead.

**Mitigation Strategy:**
1. **Baseline early** (Story 3-1): Measure chunking engine performance to validate feasibility
2. **Hybrid benchmarking** (Murat's approach): Measure critical paths (Stories 3-1, 3-4/5/6, 3-7), skip micro-benchmarks
3. **Winston's optimizations**: Lazy spaCy loading, streaming generators, parallel writes, memory pooling
4. **Fallback position**: Document actual performance, adjust target if necessary (transparency over false goals)

**Indicators:**
- Story 3-1 chunking >2 minutes for 100 PDFs → Risk materializes
- Output format generation >1.5 minutes → Risk materializes

**Contingency:**
- If target missed: Document actual performance in `docs/performance-baselines-epic-3.md`
- Negotiate target adjustment with stakeholders (e.g., <12 minutes acceptable for MVP)
- Identify optimization opportunities for post-MVP (e.g., C extensions, Cython for hotspots)

#### RISK-E3-2: Chunk Quality Subjective and Hard to Validate
**Severity:** Medium | **Probability:** Low | **Impact:** High

**Description:**
Chunk quality (semantic coherence, entity preservation) is partially subjective. Automated tests can catch sentence boundary violations, but semantic coherence requires human judgment. Risk: Chunks technically correct but semantically poor for RAG retrieval.

**Mitigation Strategy:**
1. **Manual review sampling**: UAT includes manual review of 20 sample chunks (diverse document types)
2. **Entity preservation metrics**: >95% entity completeness (quantitative gate)
3. **Readability scores**: Use textstat as objective proxy for quality
4. **Dogfooding**: Dev/SM test chunks with actual LLM upload (ChatGPT/Claude) in UAT
5. **Iterative refinement**: Collect user feedback post-MVP, refine chunking heuristics

**Indicators:**
- Manual review flags >10% chunks as incoherent → Risk materializes
- Entity preservation rate <90% → Risk materializes
- LLM upload test: chunks confuse AI or lose context → Risk materializes

**Contingency:**
- Adjust chunk size defaults (e.g., increase to 768 tokens for more context)
- Enhance entity-aware chunking logic (prefer entity-boundary splits)
- Add post-processing step: merge tiny chunks, split mega-chunks

#### RISK-E3-3: spaCy Model Accuracy Insufficient for Audit Documents
**Severity:** Low | **Probability:** Low | **Impact:** Medium

**Description:**
en_core_web_md trained on news corpus (97.2% accuracy). Audit documents have different linguistic patterns (technical jargon, regulatory language, complex sentence structures). Risk: Sentence boundary detection fails on audit-specific constructs.

**Mitigation Strategy:**
1. **Early validation** (Story 3-1): Test on diverse audit document samples
2. **Edge case handling**: Detect and handle very long sentences (>100 words), micro-sections
3. **Manual review**: UAT validates sentence boundary correctness on sample corpus
4. **Fallback heuristics**: If spaCy fails, fall back to rule-based segmentation (period + capital letter)
5. **Post-MVP option**: Fine-tune spaCy model on audit corpus (requires labeled data)

**Indicators:**
- Sentence boundary violations detected in >1% of chunks → Risk materializes
- Manual review finds systematic segmentation errors → Risk materializes

**Contingency:**
- Implement hybrid segmentation: spaCy + rule-based fallback
- Add configuration option: disable spaCy, use simple period-based splitting
- Explore alternative models: en_core_web_lg (larger, more accurate)

#### RISK-E3-4: Memory Budget Exceeded (>5.5GB)
**Severity:** Low | **Probability:** Low | **Impact:** Medium

**Description:**
Epic 2 batch processing uses 4.15GB. Epic 3 budget allows 1.35GB headroom for chunking + output. Winston's optimizations (streaming, lazy loading, pooling) should prevent overrun, but risk remains if assumptions wrong.

**Mitigation Strategy:**
1. **Early profiling** (Story 3-1): Measure chunking memory overhead on single document and batch
2. **Winston's optimizations**: Streaming generators (no buffering), metadata pooling, lazy spaCy loading
3. **Continuous monitoring**: Track memory usage in performance baselines document
4. **Streaming architecture**: Generator pattern throughout (chunks yielded one at a time)

**Indicators:**
- Single-document chunking >500MB → Risk materializes
- Batch processing >5.5GB peak RSS → Risk materializes

**Contingency:**
- Reduce parallel output workers (3 → 2 or 1) to save memory
- Disable metadata pooling if it causes issues (trade memory for simplicity)
- Process documents in smaller batches (50 PDFs instead of 100)

### 6.2 Business/Operational Risks

#### RISK-E3-5: Output Formats Don't Meet User Needs
**Severity:** Medium | **Probability:** Low | **Impact:** High

**Description:**
Epic 3 delivers JSON, TXT, CSV. Risk: Users need additional formats (Parquet, Avro, JSON Lines) or different metadata structure for downstream tools (e.g., vector database expects specific schema).

**Mitigation Strategy:**
1. **UAT validation**: Test outputs with actual downstream tools (LLM upload, Excel import)
2. **Extensibility**: BaseFormatter protocol allows adding new formats post-MVP
3. **Configuration**: Output metadata structure configurable (Epic 5)
4. **User feedback**: Collect feedback post-MVP, prioritize format additions

**Indicators:**
- UAT testers request alternative formats → Risk materializes
- Downstream tools reject output format → Risk materializes

**Contingency:**
- Add requested format in Epic 5 (quick-flow story)
- Provide format conversion scripts (e.g., JSON → JSON Lines, JSON → Parquet)
- Document output schema clearly to enable user-side conversion

#### RISK-E3-6: UAT Workflow Overhead Slows Velocity
**Severity:** Low | **Probability:** Medium | **Impact:** Low

**Description:**
10-step UAT workflow (approved in party-mode) adds overhead: SM creates test cases, builds context, reviews results. Risk: Workflow slows down story completion, reduces Epic 3 velocity.

**Mitigation Strategy:**
1. **UAT selective application**: Not all ACs require UAT (see Section 5.1 UAT Required column)
2. **Automation**: Dev executes automated tests (pytest), manual UAT only for critical paths
3. **Parallel work**: SM creates test cases while Dev codes (no blocking dependency)
4. **Learning curve**: Workflow overhead reduces over time as team learns patterns

**Indicators:**
- Story completion time >2x baseline → Risk materializes
- Dev waiting on SM for test case creation → Risk materializes

**Contingency:**
- Simplify UAT for non-critical stories (unit tests sufficient)
- Batch UAT review (SM reviews multiple stories together)
- Dev creates own test cases, SM reviews (shift left)

### 6.3 Assumptions

#### ASSUMPTION-E3-1: spaCy Sentence Boundaries Sufficient
**Assumption:** spaCy's sentence segmentation is accurate enough for audit documents without custom training.

**Validation:** Story 3-1 UAT includes manual review of sentence boundaries on sample corpus.

**If False:** Implement hybrid segmentation (spaCy + rule-based fallback) or fine-tune spaCy model on audit corpus.

#### ASSUMPTION-E3-2: Three Output Formats Adequate for MVP
**Assumption:** JSON, TXT, CSV cover 90%+ of user workflows (LLM upload, vector database, spreadsheet analysis).

**Validation:** UAT testing with actual downstream tools validates format sufficiency.

**If False:** Add additional formats in Epic 5 or post-MVP (Parquet, Avro, JSON Lines, XML).

#### ASSUMPTION-E3-3: Entity-Aware Chunking Improves Quality
**Assumption:** Preserving entity context within chunks improves RAG retrieval quality vs. naive chunking.

**Validation:** UAT includes comparison test (entity-aware vs. semantic-only chunking).

**If False:** Make entity-aware chunking optional (configuration flag), default to semantic-only.

#### ASSUMPTION-E3-4: Parallel Output Writes Improve Throughput
**Assumption:** JSON/TXT/CSV generation is I/O-bound, so parallel writes improve performance.

**Validation:** Story 3-4 benchmarks parallel vs. sequential writes.

**If False:** Disable parallel writes (simpler code, easier debugging), accept slower output generation.

#### ASSUMPTION-E3-5: textstat Readability Metrics Meaningful for Audit Docs
**Assumption:** Flesch-Kincaid, Gunning Fog, SMOG index are useful quality signals for technical audit documents.

**Validation:** Story 3-3 analyzes readability score distributions on sample corpus.

**If False:** De-emphasize readability scores in quality composite, focus on OCR confidence and completeness.

#### ASSUMPTION-E3-6: Chunk Size 256-512 Tokens Optimal
**Assumption:** Default chunk size (256-512 tokens) balances context preservation vs. retrieval precision for RAG.

**Validation:** UAT includes chunk size sensitivity analysis (128, 256, 512, 1024 tokens).

**If False:** Adjust defaults based on UAT findings, make chunk size highly configurable.

### 6.4 Open Questions

#### QUESTION-E3-1: Post-MVP Vector Database Integration?
**Question:** Should Epic 3 include direct vector database integration (e.g., Pinecone, Weaviate, Chroma)?

**Context:** Current design outputs JSON files. Users manually upload to vector DBs. Direct integration would streamline workflow.

**Decision Needed By:** Epic 3 planning (before Story 3-4)

**Options:**
1. **Out of scope for MVP**: Document output format requirements for vector DBs, defer integration to post-MVP
2. **Add to Epic 3**: Create Story 3-8 for direct vector DB upload (blocks MVP timeline)
3. **Add to Epic 5**: Include in CLI enhancement epic (batch processing + vector DB integration)

**Recommendation:** Out of scope for MVP. Document JSON schema requirements for popular vector DBs (Pinecone, Weaviate, Chroma). Add integration in post-MVP if user demand high.

#### QUESTION-E3-2: JSON Schema Validation Mandatory or Optional?
**Question:** Should JSON output always validate against JSON Schema, or make validation optional?

**Context:** JSON Schema validation adds overhead (parse schema, validate every output). Benefits: guarantees correctness, enables tooling integration.

**Decision Needed By:** Story 3-4 implementation

**Options:**
1. **Always validate**: Every JSON output validated (fail if schema violation)
2. **Optional via flag**: `--validate-schema` flag enables validation (default: off for performance)
3. **Dev-mode only**: Validate in tests, skip in production (trust code correctness)

**Recommendation:** Optional via flag (default: off). Enable in CI tests and with `--strict` mode. Provides safety without performance penalty in production.

#### QUESTION-E3-3: Chunk Overlap Strategy: Sentence-Based or Token-Based?
**Question:** Should chunk overlap use sentence boundaries (complete sentences) or token count (may split sentences)?

**Context:** Sentence-based overlap is semantically cleaner but variable size. Token-based overlap is predictable but may split sentences.

**Decision Needed By:** Story 3-1 implementation

**Options:**
1. **Sentence-based**: Overlap includes complete sentences (variable overlap size)
2. **Token-based**: Fixed overlap token count (may split sentences at chunk boundaries)
3. **Hybrid**: Prefer sentence boundaries, fall back to token count if overlap too large

**Recommendation:** Hybrid approach. Prefer complete sentences in overlap region, but enforce maximum overlap token count to prevent huge overlaps.

#### QUESTION-E3-4: Organization Strategy Default: by_document or flat?
**Question:** What should be the default organization strategy if user doesn't specify?

**Context:**
- **by_document**: Most intuitive (files grouped by source), but deep directory nesting
- **flat**: Simplest (single directory), but hundreds of files in one folder
- **by_entity**: Most powerful (semantic grouping), but requires entity tagging

**Decision Needed By:** Story 3-7 implementation

**Options:**
1. **Default: by_document** (intuitive, source-centric)
2. **Default: flat** (simplest, no nesting)
3. **Default: by_entity** (most powerful, semantic)
4. **No default** (force user to choose explicitly)

**Recommendation:** Default to **by_document**. Most intuitive for first-time users, preserves source file grouping, easy to understand output structure.

#### QUESTION-E3-5: Manifest Format: JSON, YAML, or CSV?
**Question:** What format should the manifest file use (lists all outputs with metadata)?

**Context:** Manifest tracks all generated chunks, source files, organization. Needs to be human-readable and machine-parseable.

**Decision Needed By:** Story 3-7 implementation

**Options:**
1. **JSON**: Structured, parseable, consistent with JSON output format
2. **YAML**: Human-friendly, supports comments, easier to read
3. **CSV**: Tabular, Excel-friendly, but limited structure
4. **Multiple formats**: Generate all three (manifest.json, manifest.yaml, manifest.csv)

**Recommendation:** **JSON** (manifest.json). Consistent with primary output format, widely supported, programmatically queryable. Add YAML/CSV if user demand emerges.

### 6.5 Risk Summary Table

| Risk ID | Category | Severity | Probability | Mitigation Strategy | Owner |
|---------|----------|----------|-------------|---------------------|-------|
| RISK-E3-1 | Performance target aggressive | Medium | Medium | Early baseline, hybrid benchmarking, optimizations | Dev |
| RISK-E3-2 | Chunk quality subjective | Medium | Low | Manual sampling, entity metrics, dogfooding | SM |
| RISK-E3-3 | spaCy accuracy insufficient | Low | Low | Early validation, edge case handling, fallback | Dev |
| RISK-E3-4 | Memory budget exceeded | Low | Low | Early profiling, streaming architecture, monitoring | Dev |
| RISK-E3-5 | Output formats inadequate | Medium | Low | UAT validation, extensibility design | SM |
| RISK-E3-6 | UAT workflow overhead | Low | Medium | Selective UAT, automation, parallel work | SM |

**Risk Mitigation Priority:**
1. **RISK-E3-1** (Performance): Baseline early in Story 3-1, track continuously
2. **RISK-E3-2** (Quality): UAT validation critical, manual review essential
3. **RISK-E3-5** (Formats): Extensible design enables quick post-MVP additions

---

## 7. Test Strategy

### 7.1 Test Strategy Overview

Epic 3 test strategy follows the approved 10-step UAT workflow and Murat's hybrid benchmarking approach, balancing comprehensive coverage with efficient execution.

**Strategic Principles:**
1. **Shift-Left Testing**: Run pre-commit hooks (0 violations gate) before CI
2. **Hybrid Benchmarking**: Measure critical paths (Stories 3-1, 3-4/5/6, 3-7), skip negligible overhead (Stories 3-2, 3-3)
3. **UAT Selective Application**: Not all ACs require UAT (see Section 5.1)
4. **Dev-Driven Test Execution**: Dev runs automated tests + manual UAT, SM reviews results
5. **Performance Baseline Tracking**: Document in `docs/performance-baselines-epic-3.md` (created Story 3-1)

### 7.2 Test Categories and Coverage

#### Unit Tests (~79 tests)

**Scope:** Component-level logic, edge cases, data model validation

**Coverage Requirements:**
- All public methods in ChunkingEngine, EntityPreserver, MetadataEnricher
- All output formatters (JsonFormatter, TxtFormatter, CsvFormatter)
- All data models (Chunk, ChunkMetadata, QualityScore, EntityReference)
- Edge cases: very long sentences, short sections, empty entities, malformed metadata

**Test Organization:**
```
tests/unit/test_chunk/
├── test_engine.py              # ChunkingEngine tests (15 tests)
├── test_entity_preserver.py    # EntityPreserver tests (12 tests)
├── test_metadata.py            # MetadataEnricher tests (18 tests)
└── test_models.py              # Data model tests (5 tests)

tests/unit/test_output/
├── test_json_formatter.py      # JsonFormatter tests (10 tests)
├── test_txt_formatter.py       # TxtFormatter tests (8 tests)
├── test_csv_formatter.py       # CsvFormatter tests (9 tests)
└── test_organization.py        # Organizer tests (7 tests)
```

**Key Unit Test Patterns:**

```python
# Example: ChunkingEngine determinism test
def test_chunking_determinism():
    """Verify same input produces identical chunks (NFR-P4)."""
    engine = ChunkingEngine(segmenter=mock_segmenter)

    # Process same document 10 times
    results = [
        list(engine.chunk_document(processing_result))
        for _ in range(10)
    ]

    # All runs should produce identical chunks
    for i in range(1, 10):
        assert results[i] == results[0], "Chunking must be deterministic"

# Example: Entity preservation test
def test_entity_preservation_rate():
    """Verify >95% entities kept intact within chunks (AC-3.2-1)."""
    preserver = EntityPreserver()
    entities = create_test_entities(count=100)

    chunks = list(engine.chunk_document(processing_result_with_entities))

    preserved = sum(1 for e in entities if entity_intact_in_chunk(e, chunks))
    preservation_rate = preserved / len(entities)

    assert preservation_rate >= 0.95, f"Only {preservation_rate:.1%} entities preserved"
```

#### Integration Tests (~48 tests)

**Scope:** Multi-component workflows, end-to-end processing, Epic 2 → Epic 3 integration

**Coverage Requirements:**
- Full pipeline: ProcessingResult → Chunks → Enriched Chunks → Outputs
- All output organization strategies (by_document, by_entity, flat)
- Error handling and graceful degradation
- Parallel output write coordination

**Test Organization:**
```
tests/integration/test_pipeline/
├── test_chunking_pipeline.py       # Epic 2 → Epic 3 integration (8 tests)
├── test_output_pipeline.py         # Chunking → Output formats (10 tests)
├── test_organization_strategies.py # All 3 organization modes (9 tests)
└── test_error_handling.py          # Continue-on-error, degradation (6 tests)

tests/integration/test_formats/
├── test_json_integration.py        # JSON output validation (5 tests)
├── test_txt_integration.py         # TXT output validation (4 tests)
└── test_csv_integration.py         # CSV output validation (6 tests)
```

**Key Integration Test Patterns:**

```python
# Example: Full pipeline integration test
def test_epic2_to_epic3_pipeline():
    """Verify Epic 2 output flows correctly through Epic 3 chunking."""
    # Epic 2 output (normalized document)
    processing_result = normalize_document(sample_pdf)

    # Epic 3 chunking
    engine = ChunkingEngine(segmenter=SentenceSegmenter())
    chunks = list(engine.chunk_document(processing_result))

    # Verify chunks preserve Epic 2 metadata
    assert all(c.metadata.source_file == processing_result.source_file for c in chunks)
    assert all(c.entities <= processing_result.entities for c in chunks)  # Subset

    # Verify output generation succeeds
    writer = ParallelWriter()
    results = writer.write_all_formats(iter(chunks), output_dir)

    assert results["json"].chunk_count == len(chunks)
    assert results["txt"].chunk_count == len(chunks)
    assert results["csv"].chunk_count == len(chunks)

# Example: Organization strategy integration test
def test_by_entity_organization():
    """Verify by_entity strategy groups chunks correctly (AC-3.7-3)."""
    chunks = create_test_chunks_with_entities()  # Mix of risks, controls, policies

    organizer = Organizer()
    manifest_path = organizer.organize(
        chunks,
        output_dir,
        OrganizationStrategy.BY_ENTITY
    )

    # Verify directory structure
    assert (output_dir / "risks").exists()
    assert (output_dir / "controls").exists()
    assert (output_dir / "policies").exists()

    # Verify traceability
    manifest = json.loads(manifest_path.read_text())
    for chunk_id, metadata in manifest["chunks"].items():
        assert metadata["source_file"] in manifest["sources"]
```

#### Performance Tests (~5 tests)

**Scope:** NFR validation, baseline establishment, regression detection

**Coverage Requirements:**
- NFR-P1-E3: <10 min for 100 PDFs (epic-end integration test)
- NFR-P2-E3: <5.5GB memory for batch (memory profiling)
- NFR-P3: <2 sec per 10k words chunking (Story 3-1 baseline)
- NFR-P4: 100% determinism (repeated runs)
- Output format overhead (Stories 3-4/5/6)

**Test Organization:**
```
tests/performance/
├── test_chunking_performance.py    # Story 3-1 baseline (NFR-P3)
├── test_output_performance.py      # Stories 3-4/5/6 overhead
├── test_memory_profiling.py        # NFR-P2-E3 validation
├── test_determinism.py             # NFR-P4 validation
└── test_epic_integration.py        # NFR-P1-E3 full pipeline
```

**Performance Baseline Tracking:**

All performance tests log results to `docs/performance-baselines-epic-3.md`:

```markdown
# Epic 3 Performance Baselines

## Story 3-1: Chunking Engine Baseline
- **Date:** 2025-11-15
- **Test Corpus:** 100 PDFs, 800,000 words total
- **Chunking Time:** 1.23 minutes (82.5 seconds)
- **Per-Document:** 0.825 seconds average
- **Per-10k-Words:** 1.03 seconds ✅ (target: <2 seconds)
- **Memory Usage:** 342MB peak ✅ (target: <500MB)

## Story 3-4/5/6: Output Format Overhead
- **JSON Generation:** 0.42 minutes (25.2 seconds)
- **TXT Generation:** 0.31 minutes (18.6 seconds)
- **CSV Generation:** 0.38 minutes (22.8 seconds)
- **Parallel Total:** 0.47 minutes (28.2 seconds) ✅ (target: <1 minute)
- **Speedup:** 2.9x vs sequential (25.2 + 18.6 + 22.8 = 66.6 seconds)

## Epic-End Integration Test
- **Full Pipeline:** 9.12 minutes ✅ (target: <10 minutes)
  - Extract + Normalize: 6.86 minutes (Epic 2 baseline)
  - Chunking: 1.23 minutes
  - Metadata Enrichment: 0.56 minutes
  - Output Generation: 0.47 minutes
- **Memory Peak:** 5.31GB ✅ (target: <5.5GB)
```

**Hybrid Benchmarking Strategy (Murat):**

| Story | Benchmark | Rationale |
|-------|-----------|-----------|
| 3-1 | Full benchmark (chunking critical path) | Establishes baseline, validates NFR-P3 |
| 3-2 | Skip micro-benchmark | Entity analysis overhead <0.1s per doc (negligible) |
| 3-3 | Skip micro-benchmark | Metadata enrichment overhead <0.1s per doc (negligible) |
| 3-4 | Benchmark JSON generation | Measures output format overhead |
| 3-5 | Benchmark TXT generation | Measures output format overhead |
| 3-6 | Benchmark CSV generation | Measures output format overhead |
| 3-7 | Benchmark organization | Measures file organization overhead |
| Epic-end | Full integration benchmark | Validates NFR-P1-E3 (<10 min target) |

#### UAT Tests (~25 manual/automated validations)

**Scope:** End-user workflows, format validation, downstream tool integration

**Coverage Requirements:**
- Manual review of 20 sample chunks (semantic coherence, quality)
- LLM upload testing (ChatGPT/Claude) - Story 3-5 critical UAT
- Excel/Google Sheets import - Story 3-6 critical UAT
- JSON schema validation - Story 3-4 critical UAT
- Organization strategy correctness - Story 3-7 critical UAT

**UAT Execution Method:**

**Automated UAT (pytest + tmux-cli for CLI tests):**
```bash
# SM runs workflow (after Dev marks story ready-for-review)
/bmad:bmm:workflows:create-test-cases story_key=3-1
/bmad:bmm:workflows:build-test-context story_key=3-1

# Dev executes UAT tests
/bmad:bmm:workflows:execute-tests test_execution_mode=hybrid

# Example tmux-cli test for Story 3-5 (TXT format LLM upload)
tmux-cli launch "bash"
tmux-cli send "data-extract process sample.pdf --format txt --organization flat" --pane=2
tmux-cli wait_idle --pane=2 --idle-time=2.0
tmux-cli capture --pane=2  # Verify output path

# Manual step: Upload output/sample_chunk_001.txt to ChatGPT
# Verify: No formatting artifacts, chunks readable, context preserved
```

**Manual UAT (SM-driven review):**
1. **Sample chunk review** (Story 3-1, 3-2): Read 20 chunks, assess semantic coherence
2. **LLM upload test** (Story 3-5): Upload TXT chunks to ChatGPT/Claude, verify usability
3. **Spreadsheet import** (Story 3-6): Import CSV to Excel/Sheets, verify no corruption
4. **Organization validation** (Story 3-7): Inspect output directory structure, verify traceability

**UAT Pass/Fail Criteria:**
- **90% pass rate overall** (approved in party-mode discussion)
- **100% pass rate for critical ACs** (marked "Yes - Critical" in Section 5.1)
- **Manual review**: <10% chunks flagged as incoherent
- **LLM upload**: Chunks usable without post-processing
- **Spreadsheet import**: All rows import correctly, no escaping issues

### 7.3 Quality Gates

Epic 3 enforces three quality gates aligned with the 10-step UAT workflow:

#### Gate 1: Pre-Commit (0 Violations)

**Trigger:** Before `git commit` (automated via pre-commit hooks)

**Checks:**
```bash
# Formatting (black)
black --line-length 100 src/ tests/

# Linting (ruff)
ruff check src/ tests/

# Type checking (mypy) - strict mode, excludes brownfield
mypy src/data_extract/
```

**Pass Criteria:**
- Black: 0 formatting violations
- Ruff: 0 linting violations
- Mypy: 0 type errors (in greenfield code)

**Enforcement:** Pre-commit hook blocks commit if violations detected

#### Gate 2: CI (60% Coverage)

**Trigger:** On push to main or PR creation (GitHub Actions)

**Checks:**
```yaml
# .github/workflows/ci.yml
- name: Run tests with coverage
  run: |
    pytest --cov=src --cov-report=term-missing --cov-fail-under=60

- name: Run performance regression tests
  run: |
    pytest tests/performance/ -v --benchmark-compare
```

**Pass Criteria:**
- All unit tests pass (pytest exit code 0)
- All integration tests pass
- Code coverage ≥60% (aggregate greenfield + brownfield)
- Performance regression <10% vs baseline

**Enforcement:** CI blocks merge if tests fail or coverage <60%

#### Gate 3: UAT (90% Pass Rate)

**Trigger:** After Dev marks story "ready-for-review"

**Workflow:**
1. SM creates test cases (`/bmad:bmm:workflows:create-test-cases`)
2. SM builds test context (`/bmad:bmm:workflows:build-test-context`)
3. Dev executes tests (`/bmad:bmm:workflows:execute-tests`)
4. SM reviews results (`/bmad:bmm:workflows:review-uat-results`)

**Pass Criteria:**
- 90% test pass rate overall
- 100% critical ACs pass (marked "Yes - Critical" in Section 5.1)
- Manual review: <10% chunks flagged as problematic
- No blocking issues (format validation, downstream tool compatibility)

**Enforcement:** SM approves/requests changes, story marked DONE or returned to Dev

### 7.4 Test Data and Fixtures

#### Test Corpus Requirements

**Sample Documents (Sanitized Audit Docs):**
- 10 PDFs (diverse types: reports, matrices, exports)
- 5 Word documents (with tables, headings, entity mentions)
- 3 Excel files (control matrices, risk registers)
- 2 PowerPoint files (audit presentations)

**Total Size:** <100MB (stored in `tests/fixtures/`)

**Entity Coverage:**
- At least 50 entity mentions across 6 types (processes, risks, controls, regulations, policies, issues)
- At least 10 entity relationships (e.g., "Risk X mitigated by Control Y")
- Mix of simple and complex entity definitions

**Edge Cases:**
- Very long sentence (>100 words)
- Very short section (<50 words)
- Document with no entities
- Document with 100+ entities
- Malformed metadata (missing fields)

**Synthetic Data Generation:**

```python
# tests/fixtures/generate_test_data.py
def generate_audit_report(
    num_sections: int = 5,
    words_per_section: int = 500,
    entity_density: float = 0.1  # 10% of sentences mention entities
) -> str:
    """Generate synthetic audit report for testing."""
    # Uses reportlab to create PDF with realistic structure
```

**Regeneration Script:**
```bash
# Recreate test fixtures from scratch
python tests/fixtures/generate_test_data.py --output tests/fixtures/

# Verify fixtures
pytest tests/test_fixtures.py -v
```

### 7.5 Test Execution Workflow

#### Local Development (Dev)

```bash
# 1. Run tests during development
pytest tests/unit/test_chunk/test_engine.py -v

# 2. Run all unit tests
pytest tests/unit/ -v

# 3. Run integration tests
pytest tests/integration/ -v

# 4. Run with coverage
pytest --cov=src --cov-report=html

# 5. Run pre-commit checks before commit
pre-commit run --all-files

# 6. Commit only if pre-commit passes
git add .
git commit -m "feat(chunk): implement ChunkingEngine"
```

#### CI Execution (Automated)

```yaml
# .github/workflows/ci.yml (excerpt)
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          python -m spacy download en_core_web_md

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Run performance tests
        run: pytest tests/performance/ -v --benchmark-only

      - name: Check coverage threshold
        run: coverage report --fail-under=60

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

#### UAT Execution (Dev + SM)

**Dev Workflow:**
```bash
# After completing Story 3-1 implementation

# 1. Run pre-commit
pre-commit run --all-files  # Must pass (0 violations)

# 2. Push to CI
git push origin story-3-1

# 3. Verify CI passes
# (GitHub Actions runs automatically)

# 4. Mark story ready for review
# Update docs/sprint-status.yaml: story-3-1: in_progress → ready_for_review

# 5. Notify SM
# SM creates test cases and builds test context

# 6. Execute UAT tests (when SM ready)
/bmad:bmm:workflows:execute-tests story_key=3-1 test_execution_mode=hybrid

# 7. Review results
cat docs/uat/test-results/3-1-test-results.md

# 8. Fix issues if needed, re-run UAT
# Otherwise, wait for SM approval
```

**SM Workflow:**
```bash
# After Dev marks story ready-for-review

# 1. Create test cases
/bmad:bmm:workflows:create-test-cases story_key=3-1
# Generates: docs/uat/test-cases/3-1-test-cases.md

# 2. Build test context
/bmad:bmm:workflows:build-test-context story_key=3-1
# Generates: docs/uat/test-context/3-1-test-context.xml

# 3. Notify Dev to execute tests
# Dev runs /bmad:bmm:workflows:execute-tests

# 4. Review UAT results
/bmad:bmm:workflows:review-uat-results story_key=3-1 quality_gate_level=standard
# Generates: docs/uat/reviews/3-1-uat-review.md

# 5. Approve or request changes
# If approved: Update docs/sprint-status.yaml: story-3-1: ready_for_review → done
# If changes needed: Return to Dev with feedback
```

### 7.6 Performance Baseline Documentation

All performance measurements documented in `docs/performance-baselines-epic-3.md`:

**Template:**
```markdown
# Epic 3 Performance Baselines

**Created:** 2025-11-15
**Last Updated:** 2025-11-20
**Status:** Baseline established, tracking ongoing

## Baseline Environment
- **Hardware:** 16GB RAM, 8-core CPU (Intel i7 or equivalent)
- **OS:** Windows 11 / Ubuntu 22.04
- **Python:** 3.12.1
- **Dependencies:** spaCy 3.7.2, textstat 0.7.3

## Story 3-1: Chunking Engine Baseline
[Measurements from test_chunking_performance.py]

## Stories 3-4/5/6: Output Format Overhead
[Measurements from test_output_performance.py]

## Story 3-7: Organization Overhead
[Measurements from test_organization_performance.py]

## Epic-End Integration Test
[Measurements from test_epic_integration.py]

## Performance Regression Log
| Date | Story | Metric | Baseline | Current | Delta | Status |
|------|-------|--------|----------|---------|-------|--------|
| 2025-11-20 | 3-1 | Chunking time | 82.5s | 85.2s | +3.3% | ✅ Pass (<10% regression) |
| 2025-11-21 | 3-4 | JSON generation | 25.2s | 26.1s | +3.6% | ✅ Pass |
```

### 7.7 Test Strategy Summary

| Test Type | Count | Coverage | Automation | Owner | Quality Gate |
|-----------|-------|----------|------------|-------|--------------|
| Unit | ~79 | Component logic, edge cases | 100% automated (pytest) | Dev | Pre-commit |
| Integration | ~48 | Multi-component workflows | 100% automated (pytest) | Dev | CI |
| Performance | ~5 | NFR validation, baselines | 100% automated (pytest + profiling) | Dev | CI |
| UAT | ~25 | End-user workflows, manual review | 60% automated, 40% manual | Dev executes, SM reviews | UAT (90% pass) |
| **Total** | **~157** | **Epic 3 complete coverage** | **85% automated** | **Dev + SM** | **3-gate process** |

**Test Strategy Alignment:**
- ✅ Shift-left: Pre-commit enforced before CI
- ✅ Hybrid benchmarking: Critical paths measured, micro-benchmarks skipped
- ✅ Selective UAT: Only critical ACs require manual validation
- ✅ Dev-driven execution: Dev runs tests, SM reviews results
- ✅ Continuous tracking: Performance baselines documented and monitored

---

**Epic 3 Technical Specification - Complete**

**Document Version:** 1.0
**Status:** Ready for Story Generation
**Created:** 2025-11-13
**Last Updated:** 2025-11-13
**Approved By:** User (Section 1), Party-Mode Discussion (Operational Requirements)

**Next Steps:**
1. Update `docs/sprint-status.yaml`: epic-3 status from `backlog` → `contexted`
2. Generate individual stories using `/bmad:bmm:workflows:create-story` workflow
3. Begin Story 3-1 implementation (Semantic Boundary-Aware Chunking Engine)

## Post-Review Follow-ups

- **Story 3.4:** Propagate chunking configuration and source-document metadata through `ChunkMetadata` so JsonFormatter headers report real chunk_size/overlap and source paths.
- **Story 3.4:** Normalize `ChunkMetadata.to_dict()` to emit every mandated field without `null` values (source_file, created_at, quality, etc.) before schema validation.
- **Story 3.4:** Restore UTF-8 BOM support (or a configurable `utf-8-sig` option) in JsonFormatter output so Windows-compatible consumers ingest files without manual fixes.
- **Story 3.4:** Treat schema validation failures as blocking errors instead of silent `FormatResult.errors` entries to prevent invalid JSON from leaking downstream.
- **Story 3.4:** Update Story documentation/File List to capture formatter base, unit tests, and JSON schema reference updates for traceability.

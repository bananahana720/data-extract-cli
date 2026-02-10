# 2. Detailed Design

## 2.1 Architecture Overview

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

## 2.2 Core Services and Modules

### ChunkingEngine (`src/data_extract/chunk/engine.py`)

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

### EntityPreserver (`src/data_extract/chunk/entity_preserver.py`)

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

### MetadataEnricher (`src/data_extract/chunk/metadata.py`)

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

### OutputFormatter (`src/data_extract/output/formatters/`)

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

### OrganizationStrategy (`src/data_extract/output/organization.py`)

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

## 2.3 Data Models

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

## 2.4 API Interfaces and Protocols

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

## 2.5 Workflow Sequence Diagram

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

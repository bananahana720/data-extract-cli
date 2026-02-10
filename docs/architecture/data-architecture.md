# Data Architecture

## Core Data Models (Pydantic)

**Implementation:** `src/data_extract/core/models.py` (Story 1.4)

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

class Entity(BaseModel):
    """Domain entity (risk, control, policy, etc.)"""
    model_config = ConfigDict(frozen=False)

    type: str = Field(..., description="Entity type (e.g., risk, control, policy)")
    id: str = Field(..., description="Unique entity identifier")
    text: str = Field(..., description="Entity text content")
    confidence: float = Field(..., ge=0.0, le=1.0,
                             description="Confidence score (0.0-1.0)")

class Metadata(BaseModel):
    """Metadata attached to documents and chunks"""
    model_config = ConfigDict(frozen=False)

    source_file: Path = Field(..., description="Path to original source file")
    file_hash: str = Field(..., description="SHA-256 hash for integrity")
    processing_timestamp: datetime = Field(..., description="Processing timestamp")
    tool_version: str = Field(..., description="Tool version")
    config_version: str = Field(..., description="Config version")
    document_type: str = Field(..., description="Document type (pdf, docx, xlsx)")
    quality_scores: Dict[str, float] = Field(default_factory=dict,
                                             description="Quality metrics")
    quality_flags: List[str] = Field(default_factory=list,
                                     description="Quality warnings")

class Document(BaseModel):
    """Represents a processed document"""
    model_config = ConfigDict(frozen=False)

    id: str = Field(..., description="Unique document identifier")
    text: str = Field(..., description="Document text content")
    entities: List[Entity] = Field(default_factory=list,
                                   description="Extracted entities")
    metadata: Metadata = Field(..., description="Processing metadata")
    structure: Dict[str, Any] = Field(default_factory=dict,
                                      description="Document structure")

class Chunk(BaseModel):
    """Represents a semantic chunk for RAG"""
    model_config = ConfigDict(frozen=False)

    id: str = Field(..., description="Chunk ID (format: {source}_{index:03d})")
    text: str = Field(..., description="Chunk text content")
    document_id: str = Field(..., description="Parent document reference")
    position_index: int = Field(..., ge=0, description="Position in document")
    token_count: int = Field(..., ge=0, description="Token count")
    word_count: int = Field(..., ge=0, description="Word count")
    entities: List[Entity] = Field(default_factory=list,
                                   description="Entities in chunk")
    section_context: str = Field(default="", description="Section/heading context")
    quality_score: float = Field(..., ge=0.0, le=1.0,
                                 description="Quality score (0.0-1.0)")
    readability_scores: Dict[str, float] = Field(default_factory=dict,
                                                 description="Readability metrics")
    metadata: Metadata = Field(..., description="Processing metadata")

class ProcessingContext(BaseModel):
    """Shared pipeline state (Story 1.4)"""
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    config: Dict[str, Any] = Field(default_factory=dict,
                                   description="Configuration (CLI > env > YAML)")
    logger: Optional[Any] = Field(default=None,
                                 description="Structured logger instance")
    metrics: Dict[str, Any] = Field(default_factory=dict,
                                    description="Metrics accumulation")
```

**Type Contracts Between Pipeline Stages:**
- Extract → Normalize: `Document` (with raw text)
- Normalize → Chunk: `ProcessingResult` (with cleaned content blocks)
- Chunk → Semantic: `Iterator[Chunk]` or `List[Chunk]` (with metadata)
- Semantic → Output: `ProcessingResult` (with analysis results)

## ChunkingEngine Component Design (Epic 3)

**Implementation:** `src/data_extract/chunk/` (Story 3.1)

**Core Components:**

```python
from dataclasses import dataclass
from typing import Iterator

@dataclass(frozen=True)
class Chunk:
    """Immutable chunk for RAG workflows"""
    text: str                    # Chunk text content
    metadata: ChunkMetadata      # Source, position, quality
    position_index: int          # Sequential position in document
    token_count: int             # Estimated token count (GPT tokenizer)
    word_count: int              # Actual word count
    source_block_id: str         # Reference to source ContentBlock

@dataclass(frozen=True)
class ChunkMetadata:
    """Chunk-level metadata"""
    source_file: str             # Original document path
    chunk_id: str                # Unique identifier (source_position)
    source_block_id: str         # Parent ContentBlock ID

@dataclass
class ChunkingConfig:
    """Chunking configuration"""
    chunk_size: int = 512        # Target tokens (128-2048 range)
    overlap_pct: float = 0.15    # Overlap percentage (0.0-0.5 range)

class ChunkingEngine:
    """Semantic boundary-aware chunking engine"""

    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.segmenter = SentenceSegmenter()  # Lazy-loaded spaCy

    def chunk(self, result: ProcessingResult) -> Iterator[Chunk]:
        """
        Generator that yields chunks respecting sentence boundaries.

        Memory-efficient: Streams chunks without buffering entire document.
        Deterministic: Same input always produces same chunks.
        """
        for block in result.content_blocks:
            if block.block_type != ContentBlockType.TEXT:
                continue  # Only chunk text blocks

            # Segment into sentences (spaCy)
            sentences = self.segmenter.segment(block.text)

            # Build chunks respecting sentence boundaries
            current_chunk = []
            current_tokens = 0

            for sentence in sentences:
                sentence_tokens = self._estimate_tokens(sentence)

                # Yield chunk if adding sentence would exceed size
                if current_tokens + sentence_tokens > self.config.chunk_size:
                    if current_chunk:  # Yield accumulated sentences
                        yield self._build_chunk(current_chunk, block)
                        # Apply overlap (keep last N% of tokens)
                        current_chunk = self._apply_overlap(current_chunk)
                        current_tokens = sum(self._estimate_tokens(s) for s in current_chunk)

                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

            # Yield final chunk
            if current_chunk:
                yield self._build_chunk(current_chunk, block)
```

**Key Design Decisions:**

1. **Generator-Based Streaming** (ADR-005):
   - Returns `Iterator[Chunk]` instead of `List[Chunk]`
   - Constant memory usage (doesn't buffer all chunks)
   - Enables progressive output writing

2. **Sentence Boundary Respect** (ADR-011):
   - Never splits mid-sentence (preserves semantic units)
   - Long sentences (>chunk_size) become single chunks
   - Uses spaCy for accurate boundary detection

3. **Immutable Chunks**:
   - Frozen dataclasses prevent mutations
   - Deterministic output (same input → same chunks)
   - Safe for parallel processing

4. **Configurable Overlap**:
   - Overlap preserves context across chunk boundaries
   - Range: 0% (no overlap) to 50% (max recommended)
   - Default: 15% balances context vs. redundancy

**Epic 3 Pipeline Integration:**

```
Epic 2 Output (ProcessingResult)
    ↓
    └─→ ContentBlock[] (text blocks from extraction/normalization)
         ↓
    ChunkingEngine.chunk(result) → Iterator[Chunk]
         ↓
         ├─→ SentenceSegmenter (spaCy en_core_web_md)
         │    └─→ Sentence boundaries detected
         ↓
         ├─→ Chunk Assembly (respecting boundaries)
         │    ├─→ Accumulate sentences until ~chunk_size
         │    ├─→ Apply overlap (keep last N% tokens)
         │    └─→ Yield chunk (generator pattern)
         ↓
    Output Stage (Epic 3 Story 3.4+)
         ├─→ JSON writer (structured metadata)
         ├─→ TXT writer (individual chunk files)
         └─→ CSV writer (chunk index)
```

**Performance Characteristics:**

| Metric | Baseline | NFR Target | Status |
|--------|----------|------------|--------|
| 10k-word latency | 3.0s | <4.0s | ✅ 75% of threshold |
| Memory (10k words) | 255 MB | <500 MB | ✅ 51% of limit |
| Batch memory | ≤7.8 MB variance | <100 MB | ✅ Constant |
| Scaling | 0.19s per 1k words | Linear | ✅ Validated |

See `docs/performance-baselines-epic-3.md` for detailed benchmarks.

## JSON Output Format (Story 3.4)

**Decision:** Emit a single JSON document per processed file with the shape:

```json
{
  "metadata": {
    "processing_version": "1.0.0-epic3",
    "processing_timestamp": "2025-11-15T04:30:56Z",
    "configuration": {"chunk_size": 512, "overlap_pct": 0.15, "entity_aware": false, "quality_enrichment": true},
    "source_documents": [".../test_document.txt"],
    "chunk_count": 123
  },
  "chunks": [
    {
      "chunk_id": "acme_report_chunk_000",
      "text": "...",
      "metadata": {...ChunkMetadata serialization...},
      "entities": [...EntityReference...],
      "quality": {...QualityScore...}
    }
  ]
}
```

**Rationale**
- Single document JSON is human readable, diff-friendly, and immediately parsable by `json.load()`, pandas (`pd.json_normalize(chunks)`), jq, Node.js, and downstream vector-database importers.
- JSON Schema Draft 7 validation (`src/data_extract/output/schemas/data-extract-chunk.schema.json`) enforces structure, score ranges, enums, and string patterns. Validation is enabled by default and can be disabled per formatter instance.
- Metadata header captures reproducibility details (tool version, timestamp, chunking configuration, source file list, chunk count) and is required for audit trails.

**Implementation Notes**
- Formatter protocol + dataclasses live in `src/data_extract/output/formatters/base.py`; `JsonFormatter` is in `.../json_formatter.py`.
- Schema reference for consumers documented in `docs/json-schema-reference.md`.
- Brownfield compatibility: `data_extract.chunk.engine` normalizes metadata emanating from both `data_extract.core` Pydantic objects and the legacy `src.core` dataclasses so JsonFormatter always receives a canonical `Metadata`.
- Validation/compatibility tests: `tests/unit/test_output/test_json_schema.py`, `tests/unit/test_output/test_json_formatter.py`, `tests/integration/test_output/test_json_output_pipeline.py`, and `tests/integration/test_output/test_json_compatibility.py`.
- Performance baselines (<1 second per document) tracked in `tests/performance/test_json_performance.py` with summary metrics published in `docs/performance-baselines-epic-3.md`.
## Entity Relationships

**Six Audit Entity Types** (Domain-Specific):
1. **Process** → Business processes under audit
2. **Risk** → Identified risks (can relate to multiple processes)
3. **Control** → Security controls (mitigate risks)
4. **Regulation** → Regulatory frameworks (SOX, GDPR, etc.)
5. **Policy** → Corporate policies (implement regulations)
6. **Issue** → Audit findings (gaps in controls)

**Relationships Preserved:**
- Risk → Control: "Risk X mitigated by Control Y"
- Process → Risk: "Process A has Risk B"
- Regulation → Policy: "Policy implements Regulation"
- Control → Issue: "Control C has finding Issue D"

## Storage & Persistence

**File-Based (No Database):**
- **Processing manifest**: `.processing_manifest.json` (tracks processed files)
- **Configuration**: `~/.data-extract/config.yaml` or project-local
- **Logs**: `~/.data-extract/logs/` or configured location
- **Cache**: TF-IDF vectors, LSA models saved as joblib files
- **Outputs**: JSON, TXT, CSV in configured output directory

**Caching Strategy:**
```python
# File hash as cache key
file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()

# Manifest tracks: {file_hash: {output_path, timestamp, config_hash}}
if file_hash in manifest and config_hash == manifest[file_hash]["config_hash"]:
    return load_from_cache(manifest[file_hash]["output_path"])
```

# Data Extraction Tool - Data Models Reference

**Generated**: 2025-11-30
**Scan Level**: Exhaustive
**Total Models**: 22 classes

---

## Overview

This document catalogs all data models in the Data Extraction Tool. Models are organized by module and follow these patterns:

- **Pydantic v2 Models**: Runtime validation with `frozen=True` for immutability
- **Dataclasses**: Lightweight data containers with `frozen=True`
- **Enums**: Type-safe domain concepts

---

## Core Models (`src/data_extract/core/models.py`)

**Location**: `src/data_extract/core/models.py` (491 lines)
**Purpose**: Primary data structures for the 5-stage pipeline

### Enums

#### ContentType
```python
class ContentType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    IMAGE = "image"
    CODE = "code"
    UNKNOWN = "unknown"
```
**Purpose**: Classifies content block types from extracted documents

#### EntityType
```python
class EntityType(str, Enum):
    PROCESS = "process"
    RISK = "risk"
    CONTROL = "control"
    REGULATION = "regulation"
    POLICY = "policy"
    ISSUE = "issue"
```
**Purpose**: Audit domain entity classification for RAG optimization

#### DocumentType
```python
class DocumentType(str, Enum):
    REPORT = "report"
    MATRIX = "matrix"
    EXPORT = "export"
    IMAGE = "image"
```
**Purpose**: Document classification for schema-driven normalization

#### QualityFlag
```python
class QualityFlag(str, Enum):
    LOW_OCR_CONFIDENCE = "low_ocr_confidence"
    MISSING_IMAGES = "missing_images"
    INCOMPLETE_EXTRACTION = "incomplete_extraction"
    COMPLEX_OBJECTS = "complex_objects"
```
**Purpose**: Quality validation flags for extraction results

### Pydantic Models

#### Position
```python
class Position(BaseModel):
    model_config = ConfigDict(frozen=True)

    page: int
    sequence_index: int
```
**Purpose**: Document position tracking for content blocks
**Fields**: 2

#### ContentBlock
```python
class ContentBlock(BaseModel):
    model_config = ConfigDict(frozen=True)

    block_type: ContentType
    content: str
    position: Position
    metadata: dict[str, Any] = {}
```
**Purpose**: Structural element from document extraction
**Fields**: 4

#### Entity
```python
class Entity(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: EntityType
    id: str
    text: str
    confidence: float
    location: Position
```
**Purpose**: Audit domain entity with confidence scoring
**Fields**: 5

#### Metadata
```python
class Metadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_file: str
    file_hash: str
    processing_timestamp: datetime
    processing_version: str
    document_type: DocumentType
    page_count: int
    word_count: int
    char_count: int
    quality_scores: dict[str, float]
    ocr_confidence: float | None = None
    completeness_ratio: float
    entity_tags: list[str] = []
    custom_metadata: dict[str, Any] = {}
    # ... additional fields
```
**Purpose**: Comprehensive provenance tracking for all outputs
**Fields**: 14+

#### ValidationReport
```python
class ValidationReport(BaseModel):
    quarantine_recommended: bool
    confidence_scores: dict[str, float]
    quality_flags: list[QualityFlag]
    extraction_gaps: list[str]
    warnings: list[str]
    errors: list[str]
    remediation_suggestions: list[str]
    validation_timestamp: datetime
```
**Purpose**: Quality validation results with remediation guidance
**Fields**: 8

#### Document
```python
class Document(BaseModel):
    id: str
    text: str
    entities: list[Entity]
    metadata: Metadata
    structure: list[ContentBlock]
```
**Purpose**: Processed document ready for chunking
**Fields**: 5

#### Chunk
```python
class Chunk(BaseModel):
    id: str
    text: str
    document_id: str
    position_index: int
    token_count: int
    word_count: int
    entities: list[Entity]
    section_context: str
    quality_score: float
    readability_scores: dict[str, float]
    metadata: ChunkMetadata
```
**Purpose**: RAG-optimized chunk with quality metrics
**Fields**: 10

#### ProcessingResult
```python
class ProcessingResult(BaseModel):
    file_path: str
    document_type: DocumentType
    content_blocks: list[ContentBlock]
    entities: list[Entity]
    metadata: Metadata
```
**Purpose**: Epic 2 normalization output
**Fields**: 5

#### ProcessingContext
```python
class ProcessingContext(BaseModel):
    config: dict[str, Any]
    logger: Any
    metrics: dict[str, Any]
```
**Purpose**: Shared pipeline state across stages
**Fields**: 3

---

## Chunk Models (`src/data_extract/chunk/models.py`)

**Location**: `src/data_extract/chunk/models.py` (132 lines)
**Purpose**: Chunking-specific data structures

### ChunkMetadata (Dataclass)
```python
@dataclass(frozen=True)
class ChunkMetadata:
    entity_tags: list[str]
    section_context: str
    entity_relationships: dict[str, list[str]]
    quality: QualityScore
    source_hash: str
    document_type: str
    word_count: int
    token_count: int
    created_at: datetime
    processing_version: str
    parent_document_id: str
    position_in_document: int
    overlap_with_previous: int
    overlap_with_next: int
    semantic_density: float
```
**Purpose**: Rich metadata for entity-aware chunks (Story 3.2-3.3)
**Fields**: 15

### QualityScore (Dataclass)
```python
@dataclass(frozen=True)
class QualityScore:
    readability_flesch_kincaid: float
    readability_gunning_fog: float
    ocr_confidence: float
    completeness: float
    coherence: float
    overall: float
    flags: list[str] = field(default_factory=list)
```
**Purpose**: Multi-dimensional quality metrics for chunks
**Fields**: 7

---

## Semantic Models (`src/data_extract/semantic/models.py`)

**Location**: `src/data_extract/semantic/models.py` (129 lines)
**Purpose**: Classical NLP analysis configuration and results

### SemanticResult (Dataclass)
```python
@dataclass
class SemanticResult:
    tfidf_matrix: Any  # scipy.sparse matrix
    vectorizer: Any    # TfidfVectorizer
    vocabulary: dict[str, int]
    feature_names: list[str]
    chunk_ids: list[str]
    cache_hit: bool
    processing_time_ms: float
    success: bool
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
```
**Purpose**: TF-IDF vectorization output with caching metadata
**Fields**: 11

### TfidfConfig (Dataclass)
```python
@dataclass
class TfidfConfig:
    max_features: int = 1000
    min_df: int = 1
    max_df: float = 0.95
    ngram_range: tuple[int, int] = (1, 1)
    sublinear_tf: bool = False
    use_cache: bool = True
    quality_threshold: float = 0.0
    random_state: int = 42
```
**Purpose**: TF-IDF vectorization configuration
**Fields**: 8

---

## CLI Models (`src/data_extract/cli/models.py`)

**Location**: `src/data_extract/cli/models.py` (723 lines)
**Purpose**: CLI command results and configuration

### OutputFormat (Enum)
```python
class OutputFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    TXT = "txt"
```
**Purpose**: CLI output format selection
**Fields**: 4 values

### CommandResult (Pydantic)
```python
class CommandResult(BaseModel):
    success: bool
    exit_code: int
    output: str
    errors: list[str]
    data: dict[str, Any]
    command: str
    args: dict[str, Any]
    metadata: dict[str, Any]
    timestamp: datetime
```
**Purpose**: Standardized CLI command response
**Fields**: 9

---

## CLI Config Models (`src/data_extract/cli/config/models.py`)

**Location**: `src/data_extract/cli/config/models.py` (~100 lines)
**Purpose**: Configuration preset management

### ValidationLevel (Enum)
```python
class ValidationLevel(str, Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    STRICT = "strict"
```
**Purpose**: Validation strictness for processing
**Fields**: 3 values

### PresetConfig (Dataclass)
```python
@dataclass
class PresetConfig:
    name: str
    description: str
    chunk_size: int
    quality_threshold: float
    output_format: str
    dedup_threshold: float
    include_metadata: bool
    validation_level: ValidationLevel
    created: datetime | None = None
```
**Purpose**: Saved configuration presets (audit-standard, rag-optimized, quick-scan)
**Fields**: 9

---

## Model Summary Table

| Model Name | Type | Location | Fields | Purpose |
|------------|------|----------|--------|---------|
| **ContentType** | Enum | core/models.py | 7 | Content block classification |
| **EntityType** | Enum | core/models.py | 6 | Audit domain entities |
| **DocumentType** | Enum | core/models.py | 4 | Document classification |
| **QualityFlag** | Enum | core/models.py | 4 | Quality validation flags |
| **Position** | Pydantic | core/models.py | 2 | Document position |
| **ContentBlock** | Pydantic | core/models.py | 4 | Structural element |
| **Entity** | Pydantic | core/models.py | 5 | Domain entity |
| **Metadata** | Pydantic | core/models.py | 14+ | Provenance tracking |
| **ValidationReport** | Pydantic | core/models.py | 8 | Quality validation |
| **Document** | Pydantic | core/models.py | 5 | Processed document |
| **Chunk** | Pydantic | core/models.py | 10 | RAG chunk |
| **ProcessingResult** | Pydantic | core/models.py | 5 | Stage 2 output |
| **ProcessingContext** | Pydantic | core/models.py | 3 | Pipeline state |
| **ChunkMetadata** | Dataclass | chunk/models.py | 15 | Chunk metadata |
| **QualityScore** | Dataclass | chunk/models.py | 7 | Quality metrics |
| **SemanticResult** | Dataclass | semantic/models.py | 11 | TF-IDF output |
| **TfidfConfig** | Dataclass | semantic/models.py | 8 | TF-IDF config |
| **OutputFormat** | Enum | cli/models.py | 4 | Output format |
| **CommandResult** | Pydantic | cli/models.py | 9 | Command response |
| **ValidationLevel** | Enum | cli/config/models.py | 3 | Validation strictness |
| **PresetConfig** | Dataclass | cli/config/models.py | 9 | Config preset |

**Total: 22 data models**

---

## Model Relationships

```
Document
├── entities: list[Entity]
│   └── type: EntityType
│   └── location: Position
├── metadata: Metadata
│   └── document_type: DocumentType
│   └── quality_scores: dict
└── structure: list[ContentBlock]
    └── block_type: ContentType
    └── position: Position

Chunk
├── entities: list[Entity]
├── metadata: ChunkMetadata
│   └── quality: QualityScore
│   │   └── flags: list[QualityFlag]
│   └── entity_relationships: dict
└── readability_scores: dict

SemanticResult
├── tfidf_matrix: sparse matrix
├── vectorizer: TfidfVectorizer
└── chunk_ids: list[str] → links to Chunk.id

PresetConfig
└── validation_level: ValidationLevel
└── output_format: str → OutputFormat value
```

---

## Immutability Pattern

All models use immutability to prevent pipeline state corruption:

**Pydantic v2 Models**:
```python
model_config = ConfigDict(frozen=True)
```

**Dataclasses**:
```python
@dataclass(frozen=True)
```

This ensures:
- Thread safety in batch processing
- Predictable behavior across pipeline stages
- No accidental mutations during transformation

---

## Usage Examples

### Creating a Content Block
```python
from data_extract.core.models import ContentBlock, ContentType, Position

block = ContentBlock(
    block_type=ContentType.PARAGRAPH,
    content="This is a sample paragraph.",
    position=Position(page=1, sequence_index=0),
    metadata={"source": "section_1"}
)
```

### Creating TF-IDF Config
```python
from data_extract.semantic.models import TfidfConfig

config = TfidfConfig(
    max_features=500,
    min_df=2,
    ngram_range=(1, 2),
    use_cache=True
)
```

### Creating a Preset
```python
from data_extract.cli.config.models import PresetConfig, ValidationLevel

preset = PresetConfig(
    name="my-preset",
    description="Custom processing preset",
    chunk_size=1000,
    quality_threshold=0.7,
    output_format="json",
    dedup_threshold=0.85,
    include_metadata=True,
    validation_level=ValidationLevel.STANDARD
)
```

---

**Last Updated**: 2025-11-30 | **Workflow**: document-project v1.2.0

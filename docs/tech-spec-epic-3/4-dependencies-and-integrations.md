# 4. Dependencies and Integrations

## 4.1 External Dependencies

### spaCy 3.7.2+ with en_core_web_md Model
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

### textstat 0.7.x
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

### Python Standard Library Dependencies

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

## 4.2 Internal Dependencies (Epic 2 Outputs)

### ProcessingResult (Epic 2 Output Model)
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

### SentenceSegmenter (Epic 2.5.2)
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

### Entity Normalization (Epic 2 Story 2.2)
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

## 4.3 Dependency Version Summary

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

## 4.4 Integration Points

### Upstream Integration (Epic 2 → Epic 3)
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

### Downstream Integration (Epic 3 → Epic 4)
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

### Downstream Integration (Epic 3 → Epic 5)
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

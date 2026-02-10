# Epic 3: Chunking Engine - Complete Reference

Epic 3 implements semantic boundary-aware chunking that transforms normalized text into RAG-optimized chunks while preserving document structure and entity context.

## Entity-Aware Chunking (Story 3.2)

Story 3.2 adds entity-aware boundary adjustment to prevent splitting entity definitions across chunks.

**EntityPreserver Integration:**
- `analyze_entities()`: Maps Epic 2 entities to EntityReference objects with positions
- `find_entity_gaps()`: Identifies safe split zones between entity boundaries
- `detect_entity_relationships()`: Finds relationship patterns (e.g., "RISK-001 mitigated by CTRL-042")

**How it works:**
1. ChunkingEngine analyzes entities at document start (when `entity_aware=True`)
2. During chunk generation, when target size reached, engine calls `find_entity_gaps()`
3. Engine searches for nearest gap within ±20% of chunk_size to adjust boundary
4. If suitable gap found, boundary shifts to preserve entity completeness
5. Entities marked as `is_partial=True` if split is unavoidable (e.g., entity > chunk_size)

**Preservation rate:** >95% of entities kept intact within single chunks (AC-3.2-1).

## ChunkingEngine Usage Patterns

**Basic Usage:**
```python
from data_extract.chunk import ChunkingEngine, ChunkingConfig

# Initialize engine with default configuration
config = ChunkingConfig(
    chunk_size=512,      # Target tokens per chunk (128-2048)
    overlap_pct=0.15     # 15% overlap between chunks (0.0-0.5)
)
engine = ChunkingEngine(config)

# Chunk a ProcessingResult
from data_extract.core.models import ProcessingResult
result = ProcessingResult(...)  # From normalize stage
chunks = engine.chunk(result)   # Returns List[Chunk]
```

**Streaming Large Documents:**
```python
# Memory-efficient streaming using generator
for chunk in engine.chunk(result):
    # Process chunk immediately (constant memory)
    output_writer.write_chunk(chunk)
```

**Configuration Options:**
```python
config = ChunkingConfig(
    chunk_size=1024,       # Larger chunks for dense content
    overlap_pct=0.25,      # Higher overlap preserves more context
    respect_sentences=True # Always enabled (semantic boundaries)
)
```

## Chunk Configuration Reference

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `chunk_size` | 128-2048 tokens | 512 | Target chunk size (may exceed for long sentences) |
| `overlap_pct` | 0.0-0.5 | 0.15 | Overlap between chunks (0% = no overlap, 50% = max) |
| `respect_sentences` | N/A | True | Always respects sentence boundaries (spaCy-based) |

**Key Behaviors:**
- **Semantic Boundaries:** Chunks never split mid-sentence (uses spaCy sentence segmentation)
- **Long Sentences:** Sentences >chunk_size become single chunks (preserves context)
- **Metadata Preservation:** Each chunk includes source file, position, entity tags, quality scores
- **Memory Efficiency:** Generator-based streaming (constant memory across batch sizes)

**Performance Characteristics:**
- **Latency:** ~0.19s per 1,000 words (linear scaling)
- **Memory:** 255 MB peak for 10k-word document (51% of 500 MB limit)
- **Throughput:** ~5,000 words/second (including spaCy segmentation)

See `docs/performance-baselines-epic-3.md` for detailed performance baselines.

## JsonFormatter & JSON Schema (Story 3.4)

**Location**
- Formatter protocol/dataclasses: `src/data_extract/output/formatters/base.py`
- Implementation: `src/data_extract/output/formatters/json_formatter.py`
- JSON Schema (Draft 7): `src/data_extract/output/schemas/data-extract-chunk.schema.json`
- Reference doc for downstream consumers: `docs/json-schema-reference.md`

**Output Contract**
- Root object: `{"metadata": {...}, "chunks": [...]}` (single JSON document, not JSON Lines)
- `metadata` captures processing version, timestamp, chunking config, source files, and chunk count
- Each `chunk` entry serializes the Chunk/ChunkMetadata/QualityScore/EntityReference models (ISO 8601 timestamps, stringified paths)
- Schema validation is enabled by default; disable with `JsonFormatter(validate=False)` when high-throughput jobs already trust upstream validation

**Dependencies**
- `pip install textstat pandas`
- `python -m spacy download en_core_web_md`
- Install `jq` CLI (e.g., `curl -L https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64 -o venv/bin/jq && chmod +x venv/bin/jq`)
- Node.js available on PATH (used to exercise `JSON.parse`)

**Validation Commands**
```bash
# Unit coverage (structure, schema, serialization)
pytest tests/unit/test_output/test_json_formatter.py tests/unit/test_output/test_json_schema.py

# End-to-end pipeline validation (json.load, pandas, jq, Node, queryability, determinism)
pytest tests/integration/test_output/test_json_output_pipeline.py

# UTF-8 + path compatibility
pytest tests/integration/test_output/test_json_compatibility.py

# Performance baselines (<1s/doc target, validation toggle)
pytest tests/performance/test_json_performance.py
```

**Gotchas**
- JsonFormatter materializes the chunk iterator (array output). Large documents should stay under ~500 chunks; JSON Lines support is deferred to Story 3.7/5.x.
- Schema expects `source_hash` to be 12–64 hex characters. Emit `None` when provenance isn't available instead of empty strings.
- pandas compatibility relies on `pd.json_normalize(json_data["chunks"])`; `pd.read_json` on the root object mixes dict + array and raises.
- jq tests require the binary on PATH; install per instructions above.

## TxtFormatter & Plain Text Output (Story 3.5)

**Location**
- Formatter implementation: `src/data_extract/output/formatters/txt_formatter.py`
- Shared utilities: `src/data_extract/output/utils.py`
- Reference documentation: `docs/txt-format-reference.md`

**Output Contract**
- Clean plain text optimized for direct LLM upload (ChatGPT/Claude)
- Configurable chunk delimiters (default: `━━━ CHUNK {{n}} ━━━`)
- Optional compact metadata headers (source, entities, quality)
- UTF-8-sig encoding with BOM (Windows compatibility)
- Zero formatting artifacts (no markdown/HTML/JSON/ANSI codes)

**Usage Patterns**
```python
from data_extract.output.formatters import TxtFormatter
from data_extract.chunk import ChunkingEngine, ChunkingConfig

# Basic usage (clean text only)
formatter = TxtFormatter()
result = formatter.format_chunks(chunks, Path("output.txt"))

# With metadata headers
formatter = TxtFormatter(include_metadata=True)
result = formatter.format_chunks(chunks, Path("output.txt"))

# Custom delimiter
formatter = TxtFormatter(delimiter="--- CHUNK {{n}} ---")
result = formatter.format_chunks(chunks, Path("output.txt"))
```

**Validation Commands**
```bash
# Unit tests (26 tests)
pytest tests/unit/test_output/test_txt_formatter.py -v

# Integration tests (8 tests - end-to-end pipeline)
pytest tests/integration/test_output/test_txt_pipeline.py -v

# Compatibility tests (5 tests - Unicode, paths, artifacts)
pytest tests/integration/test_output/test_txt_compatibility.py -v

# Performance tests (2 tests - latency baselines)
pytest tests/performance/test_txt_performance.py -v
```

**Output Format**
- Single concatenated TXT file with all chunks
- UTF-8-sig BOM for Windows compatibility
- Delimiters between chunks with sequential numbering (001, 002, ...)
- Optional metadata headers (1-3 lines when enabled)

**Performance Characteristics**
- Small documents (10 chunks): ~0.01s (100x faster than 1s target)
- Large documents (100 chunks): ~0.03s (33x faster than 3s target)
- Memory: ~5MB peak (constant across batch sizes)

**Key Features**
- Clean text (markdown/HTML artifacts removed automatically)
- Deterministic output (same input → byte-identical files)
- Cross-platform (Windows/Unix paths, Unicode filenames)
- Multilingual support (preserves emoji, Chinese, Arabic, etc.)

**Common Use Cases**
1. **LLM Context Upload**: Copy/paste TXT output directly to ChatGPT/Claude
2. **Audit Documentation**: Generate clean reports from messy corporate documents
3. **Text Analysis**: Prepare corpus for downstream NLP tools
4. **Human Review**: Readable format for manual QA workflows

## CsvFormatter & CSV Output (Story 3.6)

**Location**
- Formatter implementation: `src/data_extract/output/formatters/csv_formatter.py`
- Parser validator: `src/data_extract/output/validation/csv_parser.py`
- Unit tests: `tests/unit/test_output/test_csv_formatter.py`, `tests/unit/test_output/test_csv_parser_validator.py`

**Output Contract**
- Canonical 10-column schema (chunk_id, source_file, section_context, chunk_text, entity_tags, quality_score, word_count, token_count, processing_version, warnings)
- RFC 4180 compliant escaping (commas, quotes, newlines)
- UTF-8-sig encoding with BOM (Windows Excel compatibility)
- Optional text truncation with ellipsis indicator
- Semicolon-delimited entity tags for spreadsheet filtering
- Multi-engine parser validation (Python csv + pandas + csvkit)

**Usage Patterns**
```python
from data_extract.output.formatters import CsvFormatter
from pathlib import Path

# Basic usage
formatter = CsvFormatter()
result = formatter.format_chunks(chunks, Path("output.csv"))

# With truncation and validation disabled
formatter = CsvFormatter(max_text_length=200, validate=False)
result = formatter.format_chunks(chunks, Path("output.csv"))
```

**Validation Commands**
```bash
# Unit tests (13 tests - formatter + parser validator)
pytest tests/unit/test_output/test_csv_formatter.py tests/unit/test_output/test_csv_parser_validator.py -v

# Quality gates (BLUE phase - all pass)
python -m black src/data_extract/output/ --check
python -m ruff check src/data_extract/output/
python -m mypy src/data_extract/output/
```

**Status**: Core formatter production-ready with RED→GREEN→BLUE TDD complete. OutputWriter/Organization/CLI integration completed in Story 3.7 (shared infrastructure across JSON/TXT/CSV formatters).

## Output Organization Strategies (Story 3.7)

**Purpose:** Organize output files (JSON/TXT/CSV) by document, entity, or flat layout with comprehensive manifests.

**Strategies:**
- **BY_DOCUMENT:** One folder per source document (audit_report/, risk_matrix/)
- **BY_ENTITY:** Folders by entity type (risks/, controls/, processes/, unclassified/)
- **FLAT:** Single directory with prefixed filenames + manifest.json

**Manifest Enrichment (AC-3.7-6):**
Each manifest includes:
- `config_snapshot` - Chunking/formatter configuration for reproducibility
- `source_hashes` - SHA-256 hashes for source file integrity verification
- `entity_summary` - Entity statistics (total_entities, entity_types, unique_entity_ids)
- `quality_summary` - Quality score aggregations (avg/min/max, quality_flags)
- `generated_at` - ISO 8601 timestamp

**Structured Logging (AC-3.7-7):**
All organization operations emit structlog events:
- organization_start, folder_created, manifest_generated, organization_complete
- Timestamped entries for audit trail per FR-8.3

**References:**
- Format docs: `docs/csv-format-reference.md`, `docs/organizer-reference.md`
- Samples: `docs/examples/csv-output-samples/`, `docs/examples/manifest-samples/`
- Performance: `docs/performance-baselines-epic-3.md` (Organization overhead <50ms)

**Usage:**
```bash
# BY_DOCUMENT organization
data-extract process input.pdf --format csv --output output/ \
  --organize --strategy by_document

# BY_ENTITY organization
data-extract process input.pdf --format json --output output/ \
  --organize --strategy by_entity

# FLAT organization
data-extract process input.pdf --format txt --output output/ \
  --organize --strategy flat
```

## OutputWriter & Production Integration (Story 3.5 - Bucket 2)

**Location**
- Writer implementation: `src/data_extract/output/writer.py`
- CLI implementation: `src/data_extract/cli.py`
- Integration tests: `tests/integration/test_output/test_writer_integration.py`

**OutputWriter API**

OutputWriter is the main entry point for generating formatted output from chunks. It coordinates formatters (JSON, TXT, CSV) with organization strategies.

**Programmatic Usage:**
```python
from data_extract.output.writer import OutputWriter
from data_extract.output.organization import OrganizationStrategy
from pathlib import Path

writer = OutputWriter()

# Concatenated TXT output (default)
result = writer.write(
    chunks=my_chunks,
    output_path=Path("output.txt"),
    format_type="txt"
)

# Per-chunk TXT files
result = writer.write(
    chunks=my_chunks,
    output_path=Path("output/"),
    format_type="txt",
    per_chunk=True
)

# With metadata headers
result = writer.write(
    chunks=my_chunks,
    output_path=Path("output.txt"),
    format_type="txt",
    include_metadata=True
)

# Custom delimiter
result = writer.write(
    chunks=my_chunks,
    output_path=Path("output.txt"),
    format_type="txt",
    delimiter="--- CHUNK {{n}} ---"
)

# Organized output with BY_DOCUMENT strategy
result = writer.write(
    chunks=my_chunks,
    output_path=Path("output/"),
    format_type="txt",
    per_chunk=True,
    organize=True,
    strategy=OrganizationStrategy.BY_DOCUMENT
)

# JSON output (validation optional)
result = writer.write(
    chunks=my_chunks,
    output_path=Path("output.json"),
    format_type="json",
    validate=False  # Disable schema validation for performance
)
```

**CLI Usage (Minimal Implementation for Story 3.5):**

```bash
# Basic TXT output (concatenated)
data-extract process input.pdf --format txt --output chunks.txt

# Per-chunk TXT files
data-extract process input.pdf --format txt --output output/ --per-chunk

# With metadata headers
data-extract process input.pdf --format txt --output chunks.txt --include-metadata

# Custom delimiter
data-extract process input.pdf --format txt --output chunks.txt --delimiter "--- CHUNK {{n}} ---"

# Organized output with BY_DOCUMENT strategy
data-extract process input.pdf --format txt --output output/ --per-chunk --organize --strategy by_document

# Organized output with FLAT strategy
data-extract process input.pdf --format txt --output output/ --per-chunk --organize --strategy flat

# JSON output
data-extract process input.pdf --format json --output output.json

# Display version information
data-extract version
```

**Available CLI Options:**
- `--format {json,txt}`: Output format (default: txt)
- `--output PATH`: Output file or directory path (required)
- `--per-chunk`: Write each chunk to separate file (TXT only)
- `--include-metadata`: Include metadata headers (TXT only)
- `--organize`: Enable output organization (requires --strategy)
- `--strategy {by_document,by_entity,flat}`: Organization strategy
- `--delimiter TEXT`: Custom chunk delimiter (TXT only, use {{n}} for chunk number)

**Organization Strategies:**
- `by_document`: One folder per source document
- `by_entity`: One folder per entity type (risks/, controls/, etc.)
- `flat`: Single directory with prefixed filenames

**Note:** This is a minimal implementation for Story 3.5 UAT validation. Epic 5 will implement full Typer-based CLI with:
- Complete extraction pipeline integration
- Configuration cascade (CLI → env vars → YAML → defaults)
- Batch processing and progress indicators
- Advanced error handling and recovery

**Validation Commands:**
```bash
# Integration tests (17 test cases)
pytest tests/integration/test_output/test_writer_integration.py -v

# Run all output tests
pytest tests/integration/test_output/ -v

# CLI smoke tests
pytest tests/integration/test_output/test_writer_integration.py::TestCLIIntegration -v
```

## Quality Gates

**Pre-commit workflow** (0 violations required):
1. `black src/ tests/` → Fix formatting
2. `ruff check src/ tests/` → Fix linting
3. `mypy src/data_extract/` → Fix type violations (run from project root)
4. Run tests → Fix failures
5. Commit clean code

**Key Patterns**:
- Fix validation issues immediately (don't defer tech debt)
- Always include integration tests (catch memory/NFR issues)
- Profile before optimizing (establish baselines first)
- Document architectural decisions as you go

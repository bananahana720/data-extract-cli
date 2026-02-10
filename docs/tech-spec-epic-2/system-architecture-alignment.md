# System Architecture Alignment

Epic 2 implements the **normalize/** module defined in the Architecture (pages 100-105), adhering to the Pipeline Stage Pattern established in Epic 1.

## Architectural Components Referenced

**Core Architecture (Epic 1 Foundation)**:
- `src/data_extract/core/pipeline.py` - PipelineStage[Input, Output] protocol implemented by all normalizers
- `src/data_extract/core/models.py` - Pydantic models (Document, ContentBlock, Metadata, Entity) used as data contracts
- `src/data_extract/core/exceptions.py` - Exception hierarchy (ProcessingError for recoverable errors, CriticalError for fatal)

**New Components (Epic 2)**:
- `src/data_extract/normalize/normalizer.py` - Main normalization orchestrator implementing PipelineStage[Document, Document]
- `src/data_extract/normalize/cleaning.py` - Text cleaning and artifact removal
- `src/data_extract/normalize/entities.py` - Entity normalization with 6 audit domain types
- `src/data_extract/normalize/schema.py` - Schema standardization across document types
- `src/data_extract/normalize/validation.py` - Completeness validation and quality checking
- `src/data_extract/normalize/metadata.py` - Metadata enrichment framework

## Design Pattern Compliance

**Pipeline Stage Pattern** (Architecture pages 349-398):
- All normalizers implement `PipelineStage[Document, Document]` protocol
- Input: `Document` with raw extracted text from Epic 1 extractors
- Output: `Document` with cleaned text, normalized entities, enriched metadata
- Processing context passed through for logging and configuration

**Error Handling Pattern** (Architecture pages 412-433):
- Continue-on-error: ProcessingError for file-level failures (log, quarantine, continue batch)
- Halt-on-critical: CriticalError for unrecoverable errors (invalid configuration, missing dependencies)
- No silent failures: all quality issues flagged in metadata

**Configuration Cascade Pattern** (Architecture pages 486-508):
- Cleaning rules: YAML config > defaults (e.g., OCR artifact patterns, header/footer thresholds)
- Entity dictionaries: User config > built-in defaults (GRC acronyms, entity patterns)
- Quality thresholds: CLI flags > env vars > config file > hardcoded (e.g., 95% OCR confidence)

## Constraints from Architecture

**ADR-002 (Pydantic v2)**: All data models use Pydantic with runtime validation
- `Entity`, `Metadata`, `Document` models enforce schema compliance
- Schema standardization leverages Pydantic validation for document type detection

**ADR-004 (Classical NLP Only)**: Entity recognition uses spaCy statistical models (no transformers)
- spaCy `en_core_web_md` model for sentence boundaries and NER patterns
- Custom entity patterns via spaCy's rule-based matcher (no BERT/GPT)

**ADR-005 (Streaming Pipeline)**: Normalization processes documents one at a time
- Constant memory footprint (not batch-loading entire corpus)
- Enables batch processing with graceful error handling

**NFR-R1 (Deterministic Processing)**: Same input + config → identical output
- No randomness in normalization (fixed cleaning rules, consistent entity matching)
- Audit trail requirement: processing decisions logged with before/after snapshots

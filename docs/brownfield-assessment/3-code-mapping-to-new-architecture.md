# 3. Code Mapping to New Architecture

## 3.1 Architecture Comparison

**Brownfield Structure:**
```
src/
├── cli/              # Click-based CLI
├── extractors/       # Format-specific extractors
├── processors/       # Content enrichment
├── formatters/       # Output formats
├── core/             # Interfaces and models
├── pipeline/         # Orchestration
└── infrastructure/   # Config, logging, errors, progress
```

**New Architecture (Epic 1):**
```
src/data_extract/
├── core/          # Pydantic models, PipelineStage protocol
├── extract/       # Document extraction (Epic 2)
├── normalize/     # Text normalization (Epic 2)
├── chunk/         # Semantic chunking (Epic 3)
├── semantic/      # TF-IDF, LSA, similarity (Epic 4)
├── output/        # JSON, TXT, CSV output formats (Epic 3)
├── config/        # Configuration management (Epic 5)
├── utils/         # Shared utilities
└── cli.py         # Typer-based CLI (Epic 5)
```

## 3.2 Module Mapping Table

| Brownfield Module | New Architecture Module | Mapping Strategy | Priority | Notes |
|-------------------|-------------------------|------------------|----------|-------|
| **src/extractors/** | **src/data_extract/extract/** | **WRAP** | Epic 2 | Adapter pattern, preserve existing extractors |
| `pdf_extractor.py` | `extract/pdf.py` | Wrap with adapter | Story 2.1 | Keep OCR, table extraction |
| `docx_extractor.py` | `extract/docx.py` | Wrap + enhance | Story 2.1 | Add image extraction (DOCX-IMAGE-001) |
| `excel_extractor.py` | `extract/excel.py` | Wrap as-is | Story 2.1 | TDD impl is solid |
| `pptx_extractor.py` | `extract/pptx.py` | Wrap as-is | Story 2.1 | TDD impl is solid |
| `csv_extractor.py` | `extract/csv.py` | Wrap as-is | Story 2.1 | Mature v1.0.6, excellent |
| `txt_extractor.py` | `extract/txt.py` | **REWRITE** | Story 2.1 | Too basic, add markdown parsing |
| **src/processors/** | **src/data_extract/normalize/** | **ADAPT** | Epic 2 | Refactor for new pipeline |
| `metadata_aggregator.py` | `normalize/metadata.py` | Refactor | Story 2.2 | Add entity extraction (spaCy) |
| `quality_validator.py` | `normalize/validation.py` | Refactor | Story 2.2 | Integrate with new models |
| `context_linker.py` | `normalize/structure.py` | Refactor | Story 2.2 | Rename, preserve algorithm |
| **NEW** | `normalize/cleaning.py` | **CREATE** | Story 2.1 | FR-N1: Artifact removal |
| **NEW** | `normalize/entities.py` | **CREATE** | Story 2.2 | FR-N2: Entity normalization |
| **NEW** | `normalize/schema.py` | **CREATE** | Story 2.3 | FR-N3: Schema standardization |
| **src/formatters/** | **src/data_extract/output/** | **REFACTOR** | Epic 3 | Rename, add CSV formatter |
| `json_formatter.py` | `output/json.py` | Refactor | Story 3.4 | Adapt to new models |
| `markdown_formatter.py` | `output/markdown.py` | Refactor + fix | Story 3.5 | Complete table rendering |
| `chunked_text_formatter.py` | `chunk/chunker.py` | **MOVE + REFACTOR** | Story 3.1 | Move to chunk/, implement semantic boundaries |
| **NEW** | `output/csv.py` | **CREATE** | Story 3.6 | FR-C3: CSV output format |
| **NEW** | `output/txt.py` | **CREATE** | Story 3.5 | FR-C3: Plain text output |
| **NEW** | `chunk/metadata.py` | **CREATE** | Story 3.2 | FR-C2: Chunk metadata enrichment |
| **NEW** | `chunk/entity_aware.py` | **CREATE** | Story 3.2 | FR-C1: Entity-aware chunking |
| **src/pipeline/** | **src/data_extract/core/** | **REFACTOR** | Epic 1 | Move to core, implement PipelineStage protocol |
| `extraction_pipeline.py` | `core/pipeline.py` | Refactor | Story 1.4 | Implement PipelineStage[Input, Output] protocol |
| `batch_processor.py` | `core/batch.py` | Refactor | Story 1.4 | Make thread-safe (per-worker pipelines) |
| **src/core/** | **src/data_extract/core/** | **MIGRATE** | Epic 1 | Convert to Pydantic models |
| `interfaces.py` | `core/protocol.py` | Replace with Protocol | Story 1.4 | ABC → Protocol (PEP 544) |
| `models.py` | `core/models.py` | Convert to Pydantic | Story 1.4 | frozen dataclass → Pydantic BaseModel |
| **src/infrastructure/** | **src/data_extract/config/ + utils/** | **DISTRIBUTE** | Epic 5 | Split infrastructure |
| `config_manager.py` | `config/manager.py` | Refactor + enhance | Story 5.2 | Add config versioning (FR-B3, FR-O2) |
| `logging_framework.py` | `utils/logging.py` | Keep with structlog | Epic 1 | Migrate to structlog (ADR requirement) |
| `error_handler.py` | `utils/errors.py` | Refactor + centralize | Epic 1 | Create error code registry |
| `progress_tracker.py` | `utils/progress.py` | Keep as-is | Epic 1 | Solid implementation |
| **src/cli/** | **src/data_extract/cli.py** | **REPLACE** | Epic 5 | Migrate Click → Typer |
| `main.py`, `commands.py` | `cli.py` | Rewrite with Typer | Story 5.1 | Add pipeline-style commands (FR-U1) |
| `progress_display.py` | `cli.py` (inline) | Integrate | Story 5.1 | Keep Rich, simplify |
| **NEW** | `semantic/tfidf.py` | **CREATE** | Epic 4 | FR-S1: TF-IDF vectorization |
| **NEW** | `semantic/similarity.py` | **CREATE** | Epic 4 | FR-S2: Document similarity |
| **NEW** | `semantic/lsa.py` | **CREATE** | Epic 4 | FR-S3: Latent Semantic Analysis |
| **NEW** | `semantic/quality.py` | **CREATE** | Epic 4 | FR-S4: Quality metrics (textstat) |

## 3.3 Refactoring Strategy by Phase

**Phase 1: Wrap & Adapt (Epic 1-2, Stories 1.4, 2.1)**
- **Goal:** Preserve brownfield extractors with adapter pattern
- **Approach:** Create `ExtractorAdapter` to wrap `BaseExtractor` → `PipelineStage[Path, Document]`
- **Timeline:** Stories 1.4, 2.1
- **Files to wrap:** pdf_extractor.py, docx_extractor.py, excel_extractor.py, pptx_extractor.py, csv_extractor.py

**Phase 2: Refactor Core (Epic 2-3, Stories 2.1-3.6)**
- **Goal:** Refactor processors and formatters to new pipeline
- **Approach:** Convert to PipelineStage protocol, adapt to Pydantic models
- **Timeline:** Epic 2-3
- **Files to refactor:** processors (→ normalize/), formatters (→ output/)

**Phase 3: Deprecate (Epic 5, Story 5.6)**
- **Goal:** Deprecate brownfield packages
- **Approach:** Add deprecation warnings, migrate consumers, remove in v2.0
- **Timeline:** End of Epic 5
- **Deprecation plan:**
  - Epic 1-4: Brownfield and new architecture coexist
  - Epic 5: Deprecation warnings added
  - Post-Epic 5: Brownfield packages removed

---

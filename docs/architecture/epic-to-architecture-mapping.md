# Epic to Architecture Mapping

| Epic | Primary Components | Integration Points | Key Patterns |
|------|-------------------|-------------------|--------------|
| **Epic 1: Foundation** | `core/`, `pyproject.toml`, `tests/` | All other epics depend on foundation | Pipeline pattern, Pydantic models, pytest framework |
| **Epic 2: Normalization** | `normalize/` (cleaning, entities, schema, validation) | Receives from `extract/`, feeds to `chunk/` | Strategy pattern for cleaning rules, Entity registry |
| **Epic 3: Chunking** | `chunk/` (engine, models, sentence_segmenter) | Uses spaCy from Story 2.5.2, feeds to `output/` | Semantic boundary-aware chunking, Generator-based streaming |
| **Epic 4: Semantic Analysis** | `semantic/` (tfidf, similarity, lsa, quality) | Works on chunks from `chunk/`, uses scikit-learn/gensim | Vectorization pipeline, Similarity matrix |
| **Epic 5: CLI UX** | `cli.py`, `config/`, `utils/progress.py`, `utils/errors.py` | Orchestrates all pipeline stages | Command pattern, Configuration cascade, Rich UI |

## Epic-Specific Architecture Notes

**Epic 1 (Foundation):**
- Defines `Pipeline` protocol in `core/pipeline.py` with contracts: `process(input) → output`
- All stages implement pipeline interface for composability
- `core/models.py` defines shared data structures used across all stages

**Epic 2 (Normalization):**
- Six entity types (processes, risks, controls, regulations, policies, issues) handled in `normalize/entities.py`
- Entity registry pattern with configurable dictionaries for domain-specific terms
- Validation produces quality scores stored in metadata for downstream filtering

**Epic 3 (Chunking):**
- **ChunkingEngine** respects sentence boundaries (never splits mid-sentence)
- Uses **SentenceSegmenter** (Story 2.5.2) with spaCy `en_core_web_md` model
- Generator-based streaming for constant memory usage (not batch-loading)
- **Chunk data model** (frozen dataclass): text, metadata, position, token_count, source_block_id
- Configuration: chunk_size (128-2048 tokens), overlap_pct (0.0-0.5)
- Metadata includes: source_file, position_index, token_count, word_count, source_block_id
- Performance: ~3s for 10k words, 255 MB memory (linear scaling validated)

**Epic 4 (Semantic Analysis):**
- TF-IDF vectors stored as scipy sparse matrices for memory efficiency
- LSA components configurable (default: 100-300), explained variance tracked
- Similarity uses cosine similarity on vectors, cached for performance

**Epic 5 (CLI UX):**
- Typer app in `cli.py` with sub-commands: `process`, `similarity`, `validate`, `config`, `info`
- Configuration cascade: CLI flags → ENV vars → YAML file → defaults
- Rich progress shows: [████████░░] 65% (13/20) | Current: file.pdf | 2m 34s elapsed

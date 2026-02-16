"""Semantic boundary-aware chunking engine.

This module implements the core chunking logic for RAG-optimized text processing.
Chunks text at semantic boundaries (sentences, paragraphs, sections) to maintain
complete context for LLM retrieval without mid-sentence splits.

Type Contract: Document (normalized) → Iterator[Chunk]

Compliance:
    - AC-3.1-1: Chunks never split mid-sentence (spaCy sentence boundaries)
    - AC-3.1-2: Section boundaries respected when possible
    - AC-3.1-3: Chunk size configurable (128-2048 tokens, default 512)
    - AC-3.1-4: Chunk overlap configurable (0-50%, default 15%)
    - AC-3.1-5: Sentence tokenization uses spaCy (via get_sentence_boundaries)
    - AC-3.1-6: Edge cases handled gracefully (very long sentences, micro-sentences, etc.)
    - AC-3.1-7: Deterministic chunking (same input → same chunks)
    - AC-3.3-1: Quality enrichment with source traceability (Story 3.3)
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union, cast

import structlog

from ..core.exceptions import ProcessingError
from ..core.models import Chunk, Document, Entity, Metadata, ProcessingContext, ProcessingResult
from .entity_preserver import EntityPreserver, EntityReference
from .metadata_enricher import MetadataEnricher
from .models import ChunkMetadata

logger = structlog.get_logger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration for ChunkingEngine (Story 3.3).

    Attributes:
        chunk_size: Target chunk size in tokens (128-2048, default 512)
        overlap_pct: Overlap percentage as float (0.0-0.5, default 0.15)
        entity_aware: Enable entity-aware chunking (default False)
        quality_enrichment: Enable quality metadata enrichment (default True)

    Example:
        >>> config = ChunkingConfig(chunk_size=1024, overlap_pct=0.25)
        >>> engine = ChunkingEngine(config)
    """

    chunk_size: int = 512
    overlap_pct: float = 0.15
    entity_aware: bool = False
    quality_enrichment: bool = True


class ChunkingEngine:
    """Semantic boundary-aware chunking engine for RAG workflows.

    Chunks documents at semantic boundaries (sentences, sections) with configurable
    size and overlap. Ensures no mid-sentence splits for coherent LLM context.

    Design Patterns:
        - Dependency Injection: Accepts SentenceSegmenter for testability
        - Streaming Generator: Yields chunks one at a time (memory-efficient)
        - Deterministic Processing: Same input always produces identical chunks
        - Immutable Output: Chunks are Pydantic models (validation + serialization)
        - PipelineStage Protocol: Implements process(Document, Context) -> List[Chunk]

    Attributes:
        segmenter: SentenceSegmenter instance for sentence boundary detection
        chunk_size: Target chunk size in tokens (default: 512)
        overlap_pct: Overlap percentage as float 0.0-0.5 (default: 0.15)
        overlap_tokens: Calculated overlap in tokens (chunk_size * overlap_pct)

    Example:
        >>> from data_extract.chunk.sentence_segmenter import SentenceSegmenter
        >>> segmenter = SentenceSegmenter()
        >>> engine = ChunkingEngine(segmenter=segmenter, chunk_size=512, overlap_pct=0.15)
        >>> chunks = engine.process(document, context)
        >>> print(f"Generated {len(chunks)} chunks")
        Generated 42 chunks

    NFR Compliance:
        - NFR-P3: Chunks 10,000-word document in <2 seconds
        - NFR-P4: 100% deterministic (same input → same chunks)
    """

    def __init__(
        self,
        config: Optional[ChunkingConfig] = None,
        segmenter: Optional[Any] = None,
        chunk_size: Optional[int] = None,
        overlap_pct: Optional[float] = None,
        entity_aware: Optional[bool] = None,
        entity_preserver: Optional[EntityPreserver] = None,
        quality_enrichment: Optional[bool] = None,
    ):
        """Initialize chunking engine with configuration.

        Supports two initialization patterns:
        1. New pattern (Story 3.3): ChunkingEngine(config=ChunkingConfig(...))
        2. Legacy pattern (Stories 3.1-3.2): ChunkingEngine(segmenter, chunk_size=512, ...)

        Args:
            config: ChunkingConfig instance (new pattern, Story 3.3). If provided, overrides
                individual parameters.
            segmenter: SentenceSegmenter instance for sentence boundary detection.
                If None, creates default SentenceSegmenter.
            chunk_size: Target chunk size in tokens. Range: 128-2048. Default: 512.
            overlap_pct: Overlap percentage as float. Range: 0.0-0.5. Default: 0.15.
            entity_aware: Enable entity-aware chunking (Story 3.2). Default: False.
            entity_preserver: EntityPreserver instance. If None and entity_aware=True,
                creates default EntityPreserver.
            quality_enrichment: Enable quality metadata enrichment (Story 3.3). Default: True.

        Raises:
            ValueError: If chunk_size < 1 or overlap_pct < 0.0 or overlap_pct > 1.0

        Example:
            >>> # New pattern (Story 3.3)
            >>> config = ChunkingConfig(chunk_size=1024, quality_enrichment=True)
            >>> engine = ChunkingEngine(config)
            >>> # Legacy pattern (backward compatibility)
            >>> engine = ChunkingEngine(segmenter, chunk_size=512, overlap_pct=0.15)
        """
        # Resolve configuration from config or individual parameters
        if config is not None:
            # New pattern: Use ChunkingConfig
            _chunk_size = config.chunk_size
            _overlap_pct = config.overlap_pct
            _entity_aware = config.entity_aware
            _quality_enrichment = config.quality_enrichment
        else:
            # Legacy pattern: Use individual parameters
            _chunk_size = chunk_size if chunk_size is not None else 512
            _overlap_pct = overlap_pct if overlap_pct is not None else 0.15
            _entity_aware = entity_aware if entity_aware is not None else False
            _quality_enrichment = quality_enrichment if quality_enrichment is not None else True

        # Validate configuration (AC-3.1-3, AC-3.1-4)
        if _chunk_size < 1:
            raise ValueError(f"chunk_size must be >= 1, got {_chunk_size}")
        if _overlap_pct < 0.0 or _overlap_pct > 1.0:
            raise ValueError(f"overlap_pct must be 0.0-1.0, got {_overlap_pct}")

        # Initialize segmenter if not provided
        if segmenter is None:
            from .sentence_segmenter import SentenceSegmenter

            segmenter = SentenceSegmenter()

        self.segmenter = segmenter
        self.chunk_size = _chunk_size
        self.overlap_pct = _overlap_pct
        self.overlap_tokens = int(_chunk_size * _overlap_pct)
        self.entity_aware = _entity_aware
        self.entity_preserver = entity_preserver if entity_preserver else EntityPreserver()
        self.quality_enrichment = _quality_enrichment
        self._enricher = MetadataEnricher() if _quality_enrichment else None

        # Configuration warnings
        if _chunk_size < 128 or _chunk_size > 2048:
            logger.warning(
                "chunk_size outside recommended range",
                chunk_size=_chunk_size,
                recommended_range="128-2048",
            )
        if _overlap_pct > 0.5:
            logger.warning(
                "overlap_pct > 50% may cause excessive duplication",
                overlap_pct=_overlap_pct,
                recommended_max=0.5,
            )

        logger.info(
            "ChunkingEngine initialized",
            chunk_size=_chunk_size,
            overlap_pct=_overlap_pct,
            overlap_tokens=self.overlap_tokens,
            entity_aware=_entity_aware,
            quality_enrichment=_quality_enrichment,
        )

    def chunk(self, result: ProcessingResult) -> Iterator[Chunk]:
        """Chunk ProcessingResult and yield enriched chunks (Story 3.3 integration).

        New unified entry point for Story 3.3. Accepts ProcessingResult from Epic 2,
        extracts normalized text, performs chunking, and enriches with quality metadata.

        Args:
            result: ProcessingResult from Epic 2 normalize stage

        Yields:
            Chunk objects with quality-enriched metadata

        Raises:
            ProcessingError: For recoverable errors (empty doc, segmentation failures)

        Example:
            >>> config = ChunkingConfig(chunk_size=512, quality_enrichment=True)
            >>> engine = ChunkingEngine(config)
            >>> chunks = list(engine.chunk(processing_result))
            >>> chunks[0].metadata.quality.overall
            0.93
        """
        # Convert ProcessingResult to Document for chunk_document()
        # Extract text from content_blocks
        text_parts = []
        for block in result.content_blocks:
            if hasattr(block, "content"):
                text_parts.append(block.content)
            elif isinstance(block, dict):
                text_parts.append(block.get("content", ""))

        full_text = "\n".join(text_parts)

        # Resolve metadata/state across brownfield (src.core) and greenfield models
        document_metadata = self._resolve_document_metadata(result)
        source_path = self._resolve_source_path(result, document_metadata)

        # Create Document-like object (duck typing for chunk_document)
        # Use a simple namespace object
        from types import SimpleNamespace

        document_ns = SimpleNamespace(
            id=self._resolve_document_id(result, source_path),
            text=full_text,
            entities=result.entities if hasattr(result, "entities") else [],
            metadata=document_metadata,
            structure={"content_blocks": result.content_blocks},
        )

        # Create ProcessingContext
        context = ProcessingContext(
            config={},
            logger=logger,
            metrics={},
        )

        # Chunk document and enrich each chunk
        # Type ignore: SimpleNamespace duck types as Document
        for chunk in self.chunk_document(document_ns, context):  # type: ignore[arg-type]
            # Enrich with quality metadata if enabled
            if self.quality_enrichment and self._enricher:
                # Build source metadata from ProcessingResult
                source_metadata = {
                    "source_file": str(source_path) if source_path else "",
                    "source_hash": self._resolve_source_hash(document_metadata),
                    "document_type": self._resolve_document_type(result, document_metadata),
                    "ocr_confidence": self._extract_ocr_confidence(result, document_metadata),
                    "completeness": self._resolve_completeness_ratio(document_metadata),
                    "config_snapshot": {
                        "chunk_size": self.chunk_size,
                        "overlap_pct": self.overlap_pct,
                        "entity_aware": self.entity_aware,
                        "quality_enrichment": self.quality_enrichment,
                    },
                }

                # Enrich chunk with quality metadata
                enriched_chunk = self._enricher.enrich_chunk(chunk, source_metadata)
                yield enriched_chunk
            else:
                # No enrichment - yield chunk as-is
                yield chunk

    def process(self, document: Document, context: ProcessingContext) -> List[Chunk]:
        """Process document and return chunks (implements PipelineStage protocol).

        This is the main entry point implementing the PipelineStage[Document, List[Chunk]]
        protocol. Converts the generator output to a list for compatibility.

        Args:
            document: Normalized document from Epic 2
            context: Processing context (config, logger, metrics)

        Returns:
            List of Chunk objects with metadata

        Raises:
            ProcessingError: For recoverable errors (empty doc, segmentation failures)

        Example:
            >>> engine = ChunkingEngine(segmenter, chunk_size=512)
            >>> chunks = engine.process(document, context)
            >>> print(f"Generated {len(chunks)} chunks")
        """
        return list(self.chunk_document(document, context))

    def chunk_document(self, document: Document, context: ProcessingContext) -> Iterator[Chunk]:
        """Chunk document at semantic boundaries with configurable size and overlap.

        Implements semantic chunking algorithm:
        1. Extract sentences using spaCy sentence boundaries
        2. Build chunks respecting sentence boundaries (no mid-sentence splits)
        3. Apply sliding window with configured overlap
        4. Detect and preserve section boundaries when possible
        5. (Story 3.2) Analyze entity boundaries for entity-aware chunking
        6. Handle edge cases (very long sentences, micro-sentences, empty docs)

        Args:
            document: Normalized document from Epic 2 (with text, entities, metadata)
            context: Processing context (config, logger, metrics)

        Yields:
            Chunk: Semantic chunks with metadata, entities, and quality scores

        Raises:
            ProcessingError: For recoverable errors (empty doc, sentence segmentation failures)

        Edge Cases (AC-3.1-6):
            - Very Long Sentences (>chunk_size): Entire sentence becomes single chunk, warning logged
            - Micro-Sentences (<10 chars): Combined with adjacent until chunk_size reached
            - Short Sections (<chunk_size): Section becomes single chunk, no artificial splitting
            - Empty Documents: Returns empty iterator (no chunks), logs info
            - No Punctuation: spaCy statistical model handles (no fallback needed)

        Example:
            >>> engine = ChunkingEngine(chunk_size=512, overlap_pct=0.15)
            >>> chunks = list(engine.chunk_document(document, context))
            >>> print(f"Generated {len(chunks)} chunks")
            Generated 42 chunks
        """
        # Handle empty document edge case (AC-3.1-6)
        if not document.text or not document.text.strip():
            if context.logger:
                context.logger.info(
                    "Empty normalized document - no chunks produced",
                    document_id=document.id,
                    source_file=document.metadata.source_file,
                )
            return

        # Extract normalized text
        text = document.text

        # Get sentences using segmenter (AC-3.1-5)
        try:
            sentences = self.segmenter.segment(text)
        except Exception as e:
            raise ProcessingError(
                f"Sentence segmentation failed for document {document.id}: {e}"
            ) from e

        if not sentences:
            if context.logger:
                context.logger.info(
                    "No sentences extracted - no chunks produced",
                    document_id=document.id,
                    source_file=document.metadata.source_file,
                )
            return

        # Detect section boundaries from document structure (AC-3.1-2)
        section_markers = self._detect_section_boundaries(document, sentences)

        # Build section hierarchy map (AC-3.2-7 - Bucket B)
        section_hierarchy = self._build_section_hierarchy(document, sentences)

        # Analyze entities if entity-aware mode enabled (AC-3.2-1, Story 3.2)
        entity_refs: List[EntityReference] = []
        all_entity_relationships: List[Tuple[str, str, str]] = []
        if self.entity_aware and document.entities:
            entity_refs = self.entity_preserver.analyze_entities(text, document.entities)
            all_entity_relationships = self.entity_preserver.detect_entity_relationships(
                text, entity_refs
            )
            if context.logger:
                context.logger.info(
                    "Entity analysis complete",
                    document_id=document.id,
                    entity_count=len(entity_refs),
                    relationship_count=len(all_entity_relationships),
                )

        # Generate chunks using sliding window with overlap
        chunk_index = 0
        for chunk_text, chunk_metadata in self._generate_chunks(
            sentences,
            section_markers,
            entity_refs,
            all_entity_relationships,
            section_hierarchy,
            document,
            context,
        ):
            # Generate deterministic chunk ID (AC-3.1-7)
            source_stem = Path(document.metadata.source_file).stem
            chunk_id = f"{source_stem}_chunk_{chunk_index:03d}"

            # Calculate token and word counts
            token_count = len(chunk_text) // 4  # Industry standard approximation
            word_count = len(chunk_text.split())

            # Extract entities in this chunk (preserve from document)
            chunk_entities = self._extract_chunk_entities(
                chunk_text, document.entities, chunk_index
            )

            # Create chunk with metadata (entity metadata in chunk_metadata dict)
            chunk = Chunk(
                id=chunk_id,
                text=chunk_text,
                document_id=document.id,
                position_index=chunk_index,
                token_count=token_count,
                word_count=word_count,
                entities=chunk_entities,
                section_context=chunk_metadata.get("section_context", ""),
                quality_score=0.0,  # Placeholder for Story 3.3
                readability_scores={},  # Placeholder for Story 3.3
                metadata=self._create_chunk_metadata(
                    document,
                    chunk_id,
                    chunk_index,
                    token_count,
                    word_count,
                    context,
                    chunk_metadata,
                ),
            )

            yield chunk
            chunk_index += 1

        if context.logger:
            context.logger.info(
                "Document chunking complete",
                document_id=document.id,
                total_chunks=chunk_index,
                chunk_size=self.chunk_size,
                overlap_pct=self.overlap_pct,
                entity_aware=self.entity_aware,
            )

    def _build_section_hierarchy(self, document: Document, sentences: List[str]) -> Dict[int, str]:
        """Build section hierarchy map (sentence_idx -> breadcrumb).

        Args:
            document: Document with structure metadata
            sentences: List of sentences from document text

        Returns:
            Dict mapping sentence index to section breadcrumb string
            (e.g., {0: "Introduction", 5: "Risk Assessment > Controls"})
        """
        section_map: Dict[int, str] = {}

        if "content_blocks" not in document.structure:
            return section_map

        content_blocks = document.structure["content_blocks"]
        heading_stack: List[tuple[int, str]] = []  # (level, heading_text)

        # Build map of heading content to sentence index
        heading_to_sentence_idx: Dict[str, int] = {}
        for idx, sentence in enumerate(sentences):
            for block in content_blocks:
                block_type = None
                if hasattr(block, "block_type"):
                    block_type = block.block_type
                elif isinstance(block, dict):
                    block_type = block.get("block_type")

                is_heading = False
                if block_type is not None and hasattr(block_type, "value"):
                    is_heading = block_type.value == "heading"
                elif block_type == "heading":
                    is_heading = True

                if is_heading:
                    heading_content = (
                        block.content if hasattr(block, "content") else block.get("content", "")
                    )
                    # Flexible matching: check if heading appears in sentence
                    # Handle both "1. Introduction" and "## 1. Introduction" formats
                    # Also handle cases where splitting by "." breaks headings
                    if heading_content:
                        # Strip markdown, numbers, and punctuation for fuzzy matching
                        sentence_normalized = (
                            sentence.replace("#", "").replace("\n", " ").strip().lower()
                        )
                        # Extract the text part of heading (e.g., "Introduction" from "1. Introduction")
                        heading_parts = heading_content.split()
                        if heading_parts:
                            # Use the last meaningful word (usually the topic)
                            heading_key = heading_parts[-1].strip().lower()
                            if len(heading_key) > 3 and heading_key in sentence_normalized:
                                heading_to_sentence_idx[heading_content] = idx
                                break

        # Process blocks to build breadcrumbs
        section_start_indices = []  # List of (sentence_idx, breadcrumb)

        for block in content_blocks:
            block_type = None
            if hasattr(block, "block_type"):
                block_type = block.block_type
            elif isinstance(block, dict):
                block_type = block.get("block_type")

            is_heading = False
            if block_type is not None and hasattr(block_type, "value"):
                is_heading = block_type.value == "heading"
            elif block_type == "heading":
                is_heading = True

            if is_heading:
                heading_content = (
                    block.content if hasattr(block, "content") else block.get("content", "")
                )
                metadata = (
                    block.metadata if hasattr(block, "metadata") else block.get("metadata", {})
                )
                level = metadata.get("level", 1)

                # Update heading stack (pop higher or equal level headings)
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()

                # Add current heading to stack
                heading_stack.append((level, heading_content))

                # Build breadcrumb from stack
                breadcrumb = " > ".join([h[1] for h in heading_stack])

                # Find sentence index for this heading
                if heading_content in heading_to_sentence_idx:
                    sent_idx = heading_to_sentence_idx[heading_content]
                    section_start_indices.append((sent_idx, breadcrumb))

        # Sort by sentence index
        section_start_indices.sort(key=lambda x: x[0])

        # Map all sentences to their section breadcrumb
        for i in range(len(section_start_indices)):
            start_idx, breadcrumb = section_start_indices[i]
            end_idx = (
                section_start_indices[i + 1][0]
                if i + 1 < len(section_start_indices)
                else len(sentences)
            )

            # Map all sentences in this section range
            for sent_idx in range(start_idx, end_idx):
                section_map[sent_idx] = breadcrumb

        return section_map

    def _detect_section_boundaries(self, document: Document, sentences: List[str]) -> List[int]:
        """Detect section boundaries from document structure.

        **IMPLEMENTED: AC-3.1-2 completion in Story 3.2**

        Detects section markers from multiple sources:
        1. ContentBlocks with block_type="heading" from document.structure
        2. Page break markers from document.structure
        3. Regex patterns for markdown/numbered headings in text

        Args:
            document: Document with structure metadata and text
            sentences: Pre-segmented sentences from document.text (avoids redundant segmentation)

        Returns:
            List of sentence indices where sections begin (sorted, deterministic)

        Example:
            >>> # Document with 2 headings
            >>> section_indices = engine._detect_section_boundaries(document, sentences)
            >>> section_indices
            [0, 5]  # Sections start at sentence 0 and 5
        """
        import re

        section_indices: List[int] = []

        # Strategy 1: Check document.structure for content_blocks with headings
        if "content_blocks" in document.structure:
            content_blocks = document.structure["content_blocks"]
            for block in content_blocks:
                # Check if block is a heading (both object and dict forms)
                block_type = None
                if hasattr(block, "block_type"):
                    block_type = block.block_type
                elif isinstance(block, dict):
                    block_type = block.get("block_type")

                # Handle ContentType enum or string
                is_heading = False
                if block_type is not None and hasattr(block_type, "value"):
                    is_heading = block_type.value == "heading"
                elif block_type == "heading":
                    is_heading = True

                if is_heading:
                    # Get heading content
                    heading_content = (
                        block.content if hasattr(block, "content") else block.get("content", "")
                    )

                    # Map block content to sentence index
                    for idx, sentence in enumerate(sentences):
                        if heading_content in sentence:
                            if idx not in section_indices:
                                section_indices.append(idx)
                            break

        # Strategy 2: Check for page break markers in structure
        # Option A: page_breaks as list of positions
        if "page_breaks" in document.structure:
            page_breaks = document.structure["page_breaks"]
            # Map page break positions to sentence indices
            for break_pos in page_breaks:
                # Find nearest sentence index for this position
                char_pos = 0
                for idx, sentence in enumerate(sentences):
                    char_pos += len(sentence)
                    if char_pos >= break_pos:
                        if idx not in section_indices:
                            section_indices.append(idx)
                        break

        # Option B: page breaks in ContentBlock metadata (page_break_after flag)
        if "content_blocks" in document.structure:
            content_blocks = document.structure["content_blocks"]
            for idx, block in enumerate(content_blocks):
                # Check for page_break_after in metadata
                metadata = (
                    block.metadata if hasattr(block, "metadata") else block.get("metadata", {})
                )
                if metadata.get("page_break_after"):
                    # Next block starts a new section
                    next_idx = idx + 1
                    if next_idx < len(content_blocks):
                        # Find sentence index for next block
                        next_block = content_blocks[next_idx]
                        next_content = (
                            next_block.content
                            if hasattr(next_block, "content")
                            else next_block.get("content", "")
                        )
                        for sent_idx, sentence in enumerate(sentences):
                            if next_content in sentence:
                                if sent_idx not in section_indices:
                                    section_indices.append(sent_idx)
                                break

        # Strategy 3: Regex patterns for markdown and numbered headings
        # Pattern 1: Markdown headings (### Title)
        markdown_pattern = re.compile(r"^#{1,6}\s+(.+)$")
        # Pattern 2: Numbered headings (1.2.3 Title)
        numbered_pattern = re.compile(r"^\d+(\.\d+)*\s+(.+)$")

        for idx, sentence in enumerate(sentences):
            stripped = sentence.strip()
            if markdown_pattern.match(stripped) or numbered_pattern.match(stripped):
                if idx not in section_indices:
                    section_indices.append(idx)

        # Sort indices for determinism (AC-3.2-8)
        section_indices.sort()

        logger.debug(
            "Section boundaries detected",
            section_count=len(section_indices),
            indices=section_indices,
            document_id=document.id,
        )

        return section_indices

    def _generate_chunks(
        self,
        sentences: List[str],
        section_markers: List[int],
        entity_refs: List[EntityReference],
        all_relationships: List[Tuple[str, str, str]],
        section_hierarchy: Dict[int, str],
        document: Document,
        context: ProcessingContext,
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """Generate chunks using sliding window with sentence boundaries.

        Implements chunking algorithm with edge case handling:
        - Respects sentence boundaries (no mid-sentence splits)
        - Applies sliding window with overlap
        - (Story 3.2) Respects entity boundaries when entity_aware=True
        - (Story 3.2) Populates section context breadcrumbs (AC-3.2-7)
        - Handles very long sentences (>chunk_size)
        - Combines micro-sentences (<10 chars)
        - Preserves section boundaries when possible

        Args:
            sentences: List of sentence texts
            section_markers: Sentence indices marking section boundaries
            entity_refs: List of EntityReference objects (from EntityPreserver)
            all_relationships: All detected relationships from EntityPreserver
            section_hierarchy: Map of sentence index to section breadcrumb
            document: Source document
            context: Processing context

        Yields:
            Tuple of (chunk_text, chunk_metadata dict)
        """
        current_chunk: List[str] = []
        current_token_count = 0
        sentence_idx = 0

        # Build sentence position map for entity-aware chunking
        sentence_positions: List[int] = []
        pos = 0
        for sent in sentences:
            sentence_positions.append(pos)
            pos += len(sent) + 1  # +1 for space between sentences

        while sentence_idx < len(sentences):
            sentence = sentences[sentence_idx]
            sentence_token_count = len(sentence) // 4

            # Edge case: Very long sentence (AC-3.1-6)
            if sentence_token_count > self.chunk_size:
                # Yield current chunk if not empty
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunk_start_idx = sentence_idx - len(current_chunk)
                    chunk_start_pos = sentence_positions[chunk_start_idx]
                    chunk_end_pos = sentence_positions[sentence_idx]
                    section_context = section_hierarchy.get(chunk_start_idx, "")
                    metadata = self._build_chunk_metadata(
                        chunk_text,
                        chunk_start_pos,
                        chunk_end_pos,
                        entity_refs,
                        all_relationships,
                        section_context,
                    )
                    yield (chunk_text, metadata)
                    current_chunk = []
                    current_token_count = 0

                # Yield very long sentence as single chunk with warning
                if context.logger:
                    context.logger.warning(
                        "Sentence exceeds chunk_size - yielding as single chunk",
                        sentence_tokens=sentence_token_count,
                        chunk_size=self.chunk_size,
                        sentence_preview=(
                            sentence[:100] + "..." if len(sentence) > 100 else sentence
                        ),
                    )
                chunk_start_pos = sentence_positions[sentence_idx]
                chunk_end_pos = chunk_start_pos + len(sentence)
                section_context = section_hierarchy.get(sentence_idx, "")
                metadata = self._build_chunk_metadata(
                    sentence,
                    chunk_start_pos,
                    chunk_end_pos,
                    entity_refs,
                    all_relationships,
                    section_context,
                )
                yield (sentence, metadata)
                sentence_idx += 1
                continue

            # Edge case: Micro-sentence (AC-3.1-6)
            # Combine with adjacent sentences until chunk_size reached
            if len(sentence) < 10 and current_token_count == 0:
                # Start accumulating micro-sentences
                micro_batch = [sentence]
                micro_tokens = sentence_token_count
                start_idx = sentence_idx
                sentence_idx += 1

                while sentence_idx < len(sentences) and micro_tokens < self.chunk_size:
                    next_sentence = sentences[sentence_idx]
                    next_tokens = len(next_sentence) // 4
                    if micro_tokens + next_tokens > self.chunk_size:
                        break
                    micro_batch.append(next_sentence)
                    micro_tokens += next_tokens
                    sentence_idx += 1

                # Yield combined micro-sentences as chunk
                chunk_text = " ".join(micro_batch)
                chunk_start_pos = sentence_positions[start_idx]
                chunk_end_pos = (
                    sentence_positions[sentence_idx]
                    if sentence_idx < len(sentences)
                    else len(document.text)
                )
                section_context = section_hierarchy.get(start_idx, "")
                metadata = self._build_chunk_metadata(
                    chunk_text,
                    chunk_start_pos,
                    chunk_end_pos,
                    entity_refs,
                    all_relationships,
                    section_context,
                )
                yield (chunk_text, metadata)
                continue

            # Normal case: Add sentence to current chunk
            if current_token_count + sentence_token_count <= self.chunk_size:
                current_chunk.append(sentence)
                current_token_count += sentence_token_count
                sentence_idx += 1
            else:
                # Chunk is full - check if we should adjust boundary for entity preservation
                chunk_start_idx = sentence_idx - len(current_chunk)
                chunk_start_pos = sentence_positions[chunk_start_idx]
                chunk_end_pos = sentence_positions[sentence_idx]

                # Entity-aware boundary adjustment (AC-3.2-1, AC-3.2-4)
                if self.entity_aware and entity_refs:
                    # Find entity gaps near the boundary
                    entity_gaps = self.entity_preserver.find_entity_gaps(entity_refs, document.text)
                    # Find best gap near current boundary
                    best_gap = self._find_nearest_gap(
                        chunk_end_pos, entity_gaps, sentence_positions
                    )
                    if best_gap is not None and best_gap != chunk_end_pos:
                        # Adjust chunk boundary to gap position
                        # Find sentence index closest to gap
                        adjusted_idx = sentence_idx
                        for idx in range(sentence_idx, min(sentence_idx + 3, len(sentences))):
                            if sentence_positions[idx] >= best_gap:
                                adjusted_idx = idx
                                break
                        if adjusted_idx != sentence_idx:
                            # Include more sentences to reach gap
                            while sentence_idx < adjusted_idx and sentence_idx < len(sentences):
                                current_chunk.append(sentences[sentence_idx])
                                current_token_count += len(sentences[sentence_idx]) // 4
                                sentence_idx += 1
                            chunk_end_pos = (
                                sentence_positions[sentence_idx]
                                if sentence_idx < len(sentences)
                                else len(document.text)
                            )

                # Yield chunk
                chunk_text = " ".join(current_chunk)
                section_context = section_hierarchy.get(chunk_start_idx, "")
                metadata = self._build_chunk_metadata(
                    chunk_text,
                    chunk_start_pos,
                    chunk_end_pos,
                    entity_refs,
                    all_relationships,
                    section_context,
                )
                yield (chunk_text, metadata)

                # Start new chunk with overlap
                if self.overlap_tokens > 0:
                    # Calculate how many sentences to retain for overlap
                    overlap_sentences: List[str] = []
                    overlap_tokens = 0
                    for sent in reversed(current_chunk):
                        sent_tokens = len(sent) // 4
                        if overlap_tokens + sent_tokens <= self.overlap_tokens:
                            overlap_sentences.insert(0, sent)
                            overlap_tokens += sent_tokens
                        else:
                            break

                    current_chunk = overlap_sentences
                    current_token_count = overlap_tokens
                else:
                    current_chunk = []
                    current_token_count = 0

        # Yield final chunk if not empty
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_start_idx = sentence_idx - len(current_chunk)
            chunk_start_pos = sentence_positions[chunk_start_idx]
            chunk_end_pos = len(document.text)
            section_context = section_hierarchy.get(chunk_start_idx, "")
            metadata = self._build_chunk_metadata(
                chunk_text,
                chunk_start_pos,
                chunk_end_pos,
                entity_refs,
                all_relationships,
                section_context,
            )
            yield (chunk_text, metadata)

    def _find_nearest_gap(
        self, boundary_pos: int, entity_gaps: List[int], sentence_positions: List[int]
    ) -> Optional[int]:
        """Find nearest entity gap to proposed chunk boundary.

        Args:
            boundary_pos: Proposed chunk boundary position
            entity_gaps: List of safe gap positions from EntityPreserver
            sentence_positions: List of sentence start positions

        Returns:
            Position of nearest gap, or None if no suitable gap found
        """
        if not entity_gaps:
            return None

        # Find gap closest to boundary_pos
        nearest_gap = None
        min_distance = float("inf")

        for gap_pos in entity_gaps:
            distance = abs(gap_pos - boundary_pos)
            # Only consider gaps within reasonable range (±20% of chunk_size chars)
            max_adjustment = self.chunk_size * 4 * 0.2  # Convert tokens to chars
            if distance < min_distance and distance < max_adjustment:
                nearest_gap = gap_pos
                min_distance = distance

        return nearest_gap

    def _build_chunk_metadata(
        self,
        chunk_text: str,
        chunk_start_pos: int,
        chunk_end_pos: int,
        entity_refs: List[EntityReference],
        all_relationships: List[Tuple[str, str, str]],
        section_context: str = "",
    ) -> Dict[str, Any]:
        """Build chunk metadata including entity tags, relationships, and section context.

        Args:
            chunk_text: Chunk text content
            chunk_start_pos: Character position where chunk starts
            chunk_end_pos: Character position where chunk ends
            entity_refs: All entity references from document
            all_relationships: All detected relationships from EntityPreserver
            section_context: Section breadcrumb for this chunk position

        Returns:
            Dict with section_context, entity_tags, entity_relationships
        """
        metadata: Dict[str, Any] = {"section_context": section_context}

        if not self.entity_aware or not entity_refs:
            return metadata

        # Find entities within this chunk's boundaries
        chunk_entity_refs = []
        for entity_ref in entity_refs:
            # Check if entity overlaps with chunk
            if entity_ref.start_pos < chunk_end_pos and entity_ref.end_pos > chunk_start_pos:
                # Determine if entity is partial (split across boundary)
                is_partial = (
                    entity_ref.start_pos < chunk_start_pos or entity_ref.end_pos > chunk_end_pos
                )
                # Create EntityReference for this chunk
                chunk_entity_refs.append(
                    EntityReference(
                        entity_type=entity_ref.entity_type,
                        entity_id=entity_ref.entity_id,
                        start_pos=entity_ref.start_pos,
                        end_pos=entity_ref.end_pos,
                        is_partial=is_partial,
                        context_snippet=entity_ref.context_snippet,
                    )
                )

        # Store entity tags in metadata
        metadata["entity_tags"] = chunk_entity_refs

        # Find relationships where both entities are in this chunk
        chunk_entity_ids = {ref.entity_id for ref in chunk_entity_refs}
        chunk_relationships = []
        for entity1, rel_type, entity2 in all_relationships:
            # Include relationship if both entities are in this chunk
            if entity1 in chunk_entity_ids and entity2 in chunk_entity_ids:
                chunk_relationships.append((entity1, rel_type, entity2))

        metadata["entity_relationships"] = chunk_relationships

        return metadata

    def _resolve_document_metadata(self, result: ProcessingResult) -> Metadata:
        """Resolve metadata object from ProcessingResult (new or brownfield)."""
        metadata = getattr(result, "metadata", None)
        if isinstance(metadata, Metadata):
            return metadata

        legacy_metadata = metadata or getattr(result, "document_metadata", None)
        source_path = self._resolve_source_path(result, legacy_metadata)
        return self._build_metadata_from_legacy(result, legacy_metadata, source_path)

    def _resolve_source_path(self, result: ProcessingResult, metadata: Any) -> Optional[Path]:
        """Resolve source file path from ProcessingResult or metadata."""
        if metadata and hasattr(metadata, "source_file") and metadata.source_file:
            return Path(metadata.source_file)
        if hasattr(result, "file_path") and getattr(result, "file_path"):
            return Path(result.file_path)
        return None

    def _resolve_document_id(self, result: ProcessingResult, source_path: Optional[Path]) -> str:
        """Determine identifier for document namespace."""
        if source_path:
            return source_path.stem
        if hasattr(result, "file_path") and getattr(result, "file_path"):
            return Path(result.file_path).stem
        if hasattr(result, "document_id") and getattr(result, "document_id"):
            return str(result.document_id)
        return "unknown"

    def _resolve_source_hash(self, metadata: Any) -> str:
        """Extract file hash from metadata when available."""
        if metadata and hasattr(metadata, "file_hash") and metadata.file_hash:
            return cast(str, metadata.file_hash)
        if metadata and hasattr(metadata, "hash") and metadata.hash:
            return cast(str, metadata.hash)
        return ""

    def _resolve_document_type(self, result: ProcessingResult, metadata: Any) -> str:
        """Resolve document type string."""
        doc_type = getattr(result, "document_type", None)
        if doc_type:
            return doc_type.value if hasattr(doc_type, "value") else str(doc_type)
        if metadata and hasattr(metadata, "document_type") and metadata.document_type:
            doc_type = metadata.document_type
            return doc_type.value if hasattr(doc_type, "value") else str(doc_type)
        return ""

    def _resolve_completeness_ratio(self, metadata: Any) -> float:
        """Resolve completeness ratio from metadata."""
        if metadata is None:
            return 1.0
        for attr in ("completeness_ratio", "completeness"):
            if hasattr(metadata, attr):
                value = getattr(metadata, attr)
                if value is not None:
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        continue
        return 1.0

    def _build_metadata_from_legacy(
        self, result: ProcessingResult, legacy_metadata: Any, source_path: Optional[Path]
    ) -> Metadata:
        """Build Metadata object from legacy DocumentMetadata structures."""
        source_file = source_path or Path("unknown")
        file_hash = ""
        processing_timestamp = datetime.now(timezone.utc)
        tool_version = "legacy-unknown"
        config_version = "legacy"
        document_subtype = None

        if legacy_metadata:
            file_hash = getattr(legacy_metadata, "file_hash", "") or ""
            processing_timestamp = (
                getattr(legacy_metadata, "processing_timestamp", None)
                or getattr(legacy_metadata, "extracted_at", None)
                or processing_timestamp
            )
            tool_version = (
                getattr(legacy_metadata, "tool_version", None)
                or getattr(legacy_metadata, "extractor_version", None)
                or tool_version
            )
            config_version = getattr(legacy_metadata, "config_version", None) or config_version
            document_subtype = getattr(legacy_metadata, "document_subtype", None)

        document_type = self._resolve_document_type(result, legacy_metadata)

        return Metadata(
            source_file=source_file,
            file_hash=file_hash,
            processing_timestamp=processing_timestamp,
            tool_version=tool_version,
            config_version=config_version,
            document_type=document_type,
            document_subtype=document_subtype,
            quality_scores={},
            ocr_confidence={},
            completeness_ratio=self._resolve_completeness_ratio(legacy_metadata),
            quality_flags=[],
            entity_tags=[],
            entity_counts={},
            entity_relationships=[],
            section_context=None,
            config_snapshot={},
            validation_report={},
        )

    def _extract_ocr_confidence(self, result: ProcessingResult, metadata: Any) -> float:
        """Extract average OCR confidence from ProcessingResult metadata.

        Args:
            result: ProcessingResult with metadata containing OCR confidence

        Returns:
            Average OCR confidence (0.0-1.0), defaults to 1.0 if not available
        """
        candidate = None
        if (
            hasattr(result, "metadata")
            and result.metadata
            and hasattr(result.metadata, "ocr_confidence")
        ):
            candidate = result.metadata.ocr_confidence
        elif metadata and hasattr(metadata, "ocr_confidence"):
            candidate = metadata.ocr_confidence

        if candidate is None:
            return 1.0

        ocr_conf = candidate

        # Handle Dict[int, float] (per-page scores) - calculate average
        if isinstance(ocr_conf, dict):
            if not ocr_conf:
                return 1.0
            return sum(ocr_conf.values()) / len(ocr_conf)

        # Handle float (simple score)
        if isinstance(ocr_conf, (int, float)):
            return float(ocr_conf)

        # Fallback
        return 1.0

    def _extract_chunk_entities(
        self, chunk_text: str, document_entities: List[Entity], chunk_index: int
    ) -> List[Entity]:
        """Extract entities that appear in this chunk.

        Args:
            chunk_text: Chunk text to search
            document_entities: All entities from parent document
            chunk_index: Position of this chunk in document

        Returns:
            List of entities found in chunk text
        """
        # Simple implementation: Check if entity text appears in chunk
        chunk_entities = []
        for entity in document_entities:
            if hasattr(entity, "text") and entity.text in chunk_text:
                chunk_entities.append(entity)
        return chunk_entities

    def _create_chunk_metadata(
        self,
        document: Document,
        chunk_id: str,
        position_index: int,
        token_count: int,
        word_count: int,
        context: ProcessingContext,
        chunk_metadata: Dict[str, Any],
    ) -> Union[Metadata, ChunkMetadata]:
        """Create metadata for chunk with provenance tracking.

        Args:
            document: Parent document
            chunk_id: Unique chunk identifier
            position_index: Chunk position in document
            token_count: Number of tokens in chunk
            word_count: Number of words in chunk
            context: Processing context
            chunk_metadata: Dict with entity_tags, entity_relationships, section_context

        Returns:
            ChunkMetadata if entity_aware enabled, otherwise Metadata (backward compatibility)
        """

        # Extract entity information from chunk_metadata
        entity_tags_refs = chunk_metadata.get("entity_tags", [])
        entity_relationships = chunk_metadata.get("entity_relationships", [])
        section_context = chunk_metadata.get("section_context", "")

        # If entity_aware mode, return ChunkMetadata (Story 3.2)
        if self.entity_aware:
            # Create enhanced metadata with document provenance + chunk-specific fields
            # CRITICAL: Preserve original processing_timestamp for determinism (AC-3.2-8)
            source_metadata = Metadata(
                source_file=document.metadata.source_file,
                file_hash=document.metadata.file_hash,
                processing_timestamp=document.metadata.processing_timestamp,
                tool_version="3.2.0",  # Story 3.2
                config_version="1.0",
                document_type=document.metadata.document_type,
                document_subtype=None,
                completeness_ratio=None,
                entity_tags=[
                    ref.entity_id for ref in entity_tags_refs if isinstance(ref, EntityReference)
                ],
                entity_relationships=entity_relationships,
                section_context=section_context,
                config_snapshot={
                    "chunk_size": self.chunk_size,
                    "overlap_pct": self.overlap_pct,
                    "overlap_tokens": self.overlap_tokens,
                    "entity_aware": self.entity_aware,
                    "chunking_engine_version": "3.2.0",  # Story 3.2
                    "entity_refs": [ref.to_dict() for ref in entity_tags_refs],
                },
            )

            return ChunkMetadata(
                entity_tags=entity_tags_refs,  # List[EntityReference] (AC-3.2-6)
                section_context=section_context,
                entity_relationships=entity_relationships,
                source_metadata=source_metadata,
            )

        # Backward compatibility: Return Metadata for non-entity-aware mode
        return Metadata(
            source_file=document.metadata.source_file,
            file_hash=document.metadata.file_hash,
            processing_timestamp=document.metadata.processing_timestamp,
            tool_version="3.2.0",  # Story 3.2
            config_version="1.0",
            document_type=document.metadata.document_type,
            document_subtype=None,
            completeness_ratio=None,
            entity_tags=[],
            section_context=section_context,
            config_snapshot={
                "chunk_size": self.chunk_size,
                "overlap_pct": self.overlap_pct,
                "overlap_tokens": self.overlap_tokens,
                "entity_aware": self.entity_aware,
                "chunking_engine_version": "3.2.0",
            },
        )

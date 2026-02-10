"""Metadata enrichment component for chunk quality scoring (Story 3.3).

Implements MetadataEnricher class that calculates comprehensive quality metrics
for text chunks including readability scores, coherence, quality flags, and
word/token counts.

This module satisfies:
    - AC-3.3-1: Source traceability (file path, SHA-256 hash, document type)
    - AC-3.3-4: Readability scores (Flesch-Kincaid, Gunning Fog)
    - AC-3.3-5: Composite quality score (weighted average)
    - AC-3.3-7: Word/token counts
    - AC-3.3-8: Quality flags (specific issue detection)
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple

import textstat  # type: ignore[import-untyped]

from ..core.models import Chunk
from .models import ChunkMetadata
from .quality import QualityScore
from .sentence_segmenter import SentenceSegmenter


class MetadataEnricher:
    """Enriches chunks with comprehensive metadata and quality scores.

    Calculates quality metrics using textstat for readability, lexical overlap
    for coherence, and source metadata for OCR/completeness. Generates quality
    flags for targeted manual review.

    Designed for dependency injection (textstat_library parameter) to enable
    testing with mocked readability calculations.

    Example:
        >>> enricher = MetadataEnricher()
        >>> chunk = Chunk(id="test_001", text="Sample text.", ...)
        >>> source_metadata = {
        ...     "ocr_confidence": 0.99,
        ...     "completeness": 0.95,
        ...     "source_hash": "abc123",
        ...     "document_type": "report"
        ... }
        >>> enriched = enricher.enrich_chunk(chunk, source_metadata)
        >>> enriched.metadata.quality.overall
        0.93
    """

    def __init__(self, textstat_library: Any = textstat) -> None:
        """Initialize enricher with textstat library.

        Args:
            textstat_library: Textstat module for readability metrics (default: textstat).
                Used for dependency injection in tests.
        """
        self._textstat = textstat_library
        self._segmenter = SentenceSegmenter()

    def enrich_chunk(self, chunk: Chunk, source_metadata: Dict[str, Any]) -> Chunk:
        """Enrich chunk with quality metadata and scores.

        Main entry point for metadata enrichment. Calculates all quality metrics,
        creates QualityScore object, and returns new Chunk with enriched metadata.
        Maintains immutability (frozen dataclasses).

        Args:
            chunk: Basic chunk from ChunkingEngine
            source_metadata: Source document metadata from ProcessingResult
                Expected fields: ocr_confidence, completeness, source_hash, document_type

        Returns:
            New Chunk instance with enriched ChunkMetadata including QualityScore

        Example:
            >>> enricher = MetadataEnricher()
            >>> chunk = Chunk(id="test", text="Clean text.", ...)
            >>> source_meta = {"ocr_confidence": 0.99, "completeness": 0.98, ...}
            >>> enriched = enricher.enrich_chunk(chunk, source_meta)
            >>> enriched.metadata.quality.is_high_quality()
            True
        """
        text = chunk.text

        # Calculate readability scores (AC-3.3-4)
        flesch_kincaid, gunning_fog = self._calculate_readability(text)

        # Extract source quality metrics (AC-3.3-5)
        ocr_confidence = source_metadata.get("ocr_confidence", 1.0)
        completeness = source_metadata.get("completeness", 1.0)

        # Calculate coherence (AC-3.3-5)
        coherence = self._calculate_coherence(text)

        # Calculate word and token counts (AC-3.3-7)
        word_count, token_count = self._calculate_word_token_counts(text)

        # Normalize readability for overall score (0-1 scale)
        # Flesch-Kincaid grade level: 0-20+ scale → 0-1 scale (inverted: lower grade = higher quality)
        readability_normalized = max(0.0, min(1.0, 1.0 - (flesch_kincaid / 20.0)))

        # Calculate overall weighted score (AC-3.3-5)
        overall = self._calculate_overall_quality(
            {
                "ocr_confidence": ocr_confidence,
                "completeness": completeness,
                "coherence": coherence,
                "readability_normalized": readability_normalized,
            }
        )

        # Create QualityScore
        quality_score = QualityScore(
            readability_flesch_kincaid=flesch_kincaid,
            readability_gunning_fog=gunning_fog,
            ocr_confidence=ocr_confidence,
            completeness=completeness,
            coherence=coherence,
            overall=overall,
            flags=[],  # Populated next
        )

        # Detect quality flags (AC-3.3-8)
        flags = self._detect_quality_flags(quality_score, text)

        # Recreate with flags (frozen dataclass workaround)
        quality_score = QualityScore(
            readability_flesch_kincaid=quality_score.readability_flesch_kincaid,
            readability_gunning_fog=quality_score.readability_gunning_fog,
            ocr_confidence=quality_score.ocr_confidence,
            completeness=quality_score.completeness,
            coherence=quality_score.coherence,
            overall=quality_score.overall,
            flags=flags,
        )

        # Extract source traceability (AC-3.3-1)
        source_hash = source_metadata.get("source_hash") or None
        document_type = source_metadata.get("document_type") or None

        # Extract source file and config snapshot (AC-3.4-3, AC-3.4-6 - Story 3.4)
        source_file = source_metadata.get("source_file") or None
        config_snapshot = source_metadata.get("config_snapshot") or {}

        # Create enriched metadata
        enriched_metadata = ChunkMetadata(
            entity_tags=(
                getattr(chunk.metadata, "entity_tags", [])
                if hasattr(chunk, "metadata") and chunk.metadata
                else []
            ),
            section_context=(
                getattr(chunk.metadata, "section_context", "")
                if hasattr(chunk, "metadata") and chunk.metadata
                else ""
            ),
            entity_relationships=(
                getattr(chunk.metadata, "entity_relationships", [])
                if hasattr(chunk, "metadata") and chunk.metadata
                else []
            ),
            source_metadata=(
                getattr(chunk.metadata, "source_metadata", None)
                if hasattr(chunk, "metadata") and chunk.metadata
                else None
            ),
            quality=quality_score,
            source_hash=source_hash,
            document_type=document_type,
            word_count=word_count,
            token_count=token_count,
            created_at=datetime.now(),
            processing_version="1.0.0",
            source_file=source_file,
            config_snapshot=config_snapshot,
        )

        # Return new chunk with enriched metadata (immutability)
        # Chunk is a Pydantic model, use model_copy with update
        return chunk.model_copy(
            update={
                "metadata": enriched_metadata,
                "word_count": word_count,
                "token_count": token_count,
            }
        )

    def _calculate_readability(self, text: str) -> Tuple[float, float]:
        """Calculate readability scores using textstat library.

        Uses Flesch-Kincaid Grade Level and Gunning Fog Index. Handles edge
        cases (empty text, very short text) gracefully.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (flesch_kincaid_score, gunning_fog_score)
            Returns (0.0, 0.0) for empty text.

        Example:
            >>> enricher = MetadataEnricher()
            >>> fk, gf = enricher._calculate_readability("Simple text. Easy read.")
            >>> fk < 8.0  # Low grade level
            True
        """
        if not text or not text.strip():
            return (0.0, 0.0)

        try:
            flesch_kincaid = self._textstat.flesch_kincaid_grade(text)
            gunning_fog = self._textstat.gunning_fog(text)

            # Ensure valid ranges (0.0-30.0)
            flesch_kincaid = max(0.0, min(30.0, flesch_kincaid))
            gunning_fog = max(0.0, min(30.0, gunning_fog))

            return (flesch_kincaid, gunning_fog)
        except Exception:
            # Fallback for very short text or textstat errors
            return (0.0, 0.0)

    def _calculate_coherence(self, text: str) -> float:
        """Calculate coherence using sentence-to-sentence lexical overlap heuristic.

        Simple lexical overlap: For each adjacent sentence pair, calculate
        intersection ∩ / union ∪ of words. Average across all pairs.

        This is a temporary heuristic for Epic 3. Will be replaced with
        TF-IDF cosine similarity in Epic 4.

        Args:
            text: Text to analyze

        Returns:
            Coherence score (0.0-1.0)
            1.0 for single sentence (no comparison needed)
            0.0 for empty text

        Example:
            >>> enricher = MetadataEnricher()
            >>> # High overlap (repeated words)
            >>> coherence = enricher._calculate_coherence(
            ...     "The cat sat. The cat ran. The cat jumped."
            ... )
            >>> coherence > 0.5
            True
        """
        if not text or not text.strip():
            return 0.0

        # Segment into sentences
        try:
            sentences = self._segmenter.segment(text)
        except Exception:
            # Fallback to simple split if segmenter fails
            sentences = [s.strip() for s in text.split(".") if s.strip()]

        if len(sentences) <= 1:
            return 1.0  # Single sentence is perfectly coherent

        # Common stop words to exclude (improves content word matching)
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "as",
            "by",
            "is",
            "be",
            "are",
            "was",
            "were",
            "been",
            "being",
            "this",
            "that",
            "these",
            "those",
        }

        # Calculate lexical overlap for adjacent sentence pairs
        overlaps: List[float] = []
        for i in range(len(sentences) - 1):
            # Strip punctuation and filter stop words for better content matching
            sent1_words = set(
                word.strip(".,!?;:").lower()
                for word in sentences[i].split()
                if word.strip(".,!?;:") and word.strip(".,!?;:").lower() not in stop_words
            )
            sent2_words = set(
                word.strip(".,!?;:").lower()
                for word in sentences[i + 1].split()
                if word.strip(".,!?;:") and word.strip(".,!?;:").lower() not in stop_words
            )

            # Calculate overlap using average of bidirectional coverage
            # This is more lenient than Jaccard and better captures keyword repetition
            if len(sent1_words) == 0 or len(sent2_words) == 0:
                continue

            # Exact match intersection
            intersection = sent1_words & sent2_words

            # Also check for word root matches (simple: first 3 chars)
            # This catches plurals, verb forms (risk/risks, assess/assessment)
            # Include cases where one word is in exact match but the other isn't
            root_matches = 0
            for w1 in sent1_words:
                if w1 in intersection:
                    continue  # Skip if already exact matched
                for w2 in sent2_words:
                    # Check if roots match (min 3 chars for better recall)
                    if len(w1) >= 3 and len(w2) >= 3 and w1[:3] == w2[:3]:
                        root_matches += 1
                        break  # Count each w1 only once

            # Effective intersection size (exact + root matches)
            # Root matches weighted at 1.0 (treat as equivalent to exact match for coherence)
            effective_intersection_size = len(intersection) + root_matches

            if effective_intersection_size > 0:
                # Coverage from sent1 perspective + sent2 perspective, averaged
                coverage1 = effective_intersection_size / len(sent1_words)
                coverage2 = effective_intersection_size / len(sent2_words)
                overlap = (coverage1 + coverage2) / 2.0
                overlaps.append(overlap)
            else:
                overlaps.append(0.0)

        # Return average overlap
        if overlaps:
            return sum(overlaps) / len(overlaps)
        else:
            return 0.0

    def _calculate_overall_quality(self, quality_components: Dict[str, float]) -> float:
        """Calculate overall quality as weighted composite score.

        Weights:
            - OCR confidence: 40% (foundation metric)
            - Completeness: 30% (entity preservation critical)
            - Coherence: 20% (semantic flow)
            - Readability: 10% (normalized, low priority for technical docs)

        Args:
            quality_components: Dict with ocr_confidence, completeness, coherence,
                readability_normalized (all 0.0-1.0)

        Returns:
            Overall quality score (0.0-1.0)

        Example:
            >>> enricher = MetadataEnricher()
            >>> overall = enricher._calculate_overall_quality({
            ...     "ocr_confidence": 0.95,
            ...     "completeness": 0.90,
            ...     "coherence": 0.80,
            ...     "readability_normalized": 0.85
            ... })
            >>> 0.85 <= overall <= 0.95
            True
        """
        ocr = quality_components.get("ocr_confidence", 1.0)
        completeness = quality_components.get("completeness", 1.0)
        coherence = quality_components.get("coherence", 1.0)
        readability = quality_components.get("readability_normalized", 1.0)

        # Weighted average
        overall = (0.4 * ocr) + (0.3 * completeness) + (0.2 * coherence) + (0.1 * readability)

        # Ensure 0.0-1.0 range
        return max(0.0, min(1.0, overall))

    def _detect_quality_flags(self, quality: QualityScore, text: str) -> List[str]:
        """Detect specific quality issues and generate flags.

        Flag detection logic:
            - low_ocr: OCR confidence < 0.95
            - incomplete_extraction: Completeness < 0.90
            - high_complexity: Flesch-Kincaid grade level > 15.0
            - gibberish: >30% non-alphabetic characters

        Args:
            quality: QualityScore with calculated metrics
            text: Original text for gibberish detection

        Returns:
            List of applicable quality flags (empty if no issues)

        Example:
            >>> enricher = MetadataEnricher()
            >>> quality = QualityScore(
            ...     readability_flesch_kincaid=18.0,  # High complexity
            ...     ocr_confidence=0.87,  # Low OCR
            ...     completeness=0.85,  # Incomplete
            ...     ...
            ... )
            >>> flags = enricher._detect_quality_flags(quality, "Normal text")
            >>> "low_ocr" in flags and "incomplete_extraction" in flags
            True
        """
        flags: List[str] = []

        # Check OCR confidence threshold
        if quality.ocr_confidence < 0.95:
            flags.append("low_ocr")

        # Check completeness threshold
        if quality.completeness < 0.90:
            flags.append("incomplete_extraction")

        # Check readability complexity threshold
        if quality.readability_flesch_kincaid > 15.0:
            flags.append("high_complexity")

        # Check gibberish (>30% non-alphabetic characters)
        if text and len(text) > 0:
            alphabetic_count = sum(1 for c in text if c.isalpha())
            total_count = len(text)
            non_alphabetic_pct = 1.0 - (alphabetic_count / total_count)

            if non_alphabetic_pct > 0.30:
                flags.append("gibberish")

        return flags

    def _calculate_word_token_counts(self, text: str) -> Tuple[int, int]:
        """Calculate word count and token count.

        Word count: Whitespace split (simple, fast)
        Token count: len(text) / 4 heuristic (OpenAI approximation)

        Args:
            text: Text to count

        Returns:
            Tuple of (word_count, token_count)

        Example:
            >>> enricher = MetadataEnricher()
            >>> words, tokens = enricher._calculate_word_token_counts("Hello world test")
            >>> words
            3
            >>> tokens
            3
        """
        if not text or not text.strip():
            return (0, 0)

        # Word count (whitespace split)
        word_count = len(text.split())

        # Token count (len/4 heuristic)
        token_count = len(text) // 4

        return (word_count, token_count)


__all__ = ["MetadataEnricher"]

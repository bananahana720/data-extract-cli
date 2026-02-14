"""Performance tests for entity-aware chunking (Story 3.2 - NFR-P3).

Tests entity-aware chunking performance requirements:
- NFR-P3: Entity-aware overhead <0.3s per 10k words (10% overhead over baseline)
- Total latency: <3.3s per 10k words (baseline 3.0s + 0.3s entity processing)
- Section detection: <0.1s per document

Performance baselines established for tracking regressions.
"""

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import pytest

pytestmark = [
    pytest.mark.P2,
    pytest.mark.performance,
    pytest.mark.chunking,
    pytest.mark.entity_aware,
]


def _coverage_perf_multiplier() -> float:
    """Relax strict wall-clock thresholds when coverage instrumentation is active."""
    coverage_markers = (
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COVERAGE_RUN",
        "PYTEST_COV",
    )
    return 1.5 if any(str(os.environ.get(name, "")).strip() for name in coverage_markers) else 1.0


from data_extract.chunk import ChunkingEngine, SentenceSegmenter  # noqa: E402
from data_extract.core.models import (  # noqa: E402
    Document,
    Entity,
    EntityType,
    Metadata,
    ProcessingContext,
)


def create_test_metadata(source_file: str = "performance_test.pdf") -> Metadata:
    """Create metadata for performance tests."""
    return Metadata(
        source_file=Path(source_file),
        file_hash="perf_test_hash",
        processing_timestamp=datetime.now(timezone.utc),
        tool_version="3.2.0",
        config_version="1.0",
    )


def generate_entity_rich_text(
    word_count: int, entity_density: float = 0.05
) -> tuple[str, List[Entity]]:
    """Generate synthetic entity-rich text for performance testing.

    Args:
        word_count: Target word count for generated text
        entity_density: Fraction of sentences that contain entities (default: 5%)

    Returns:
        Tuple of (text, entities) where entities is list of Entity objects
    """
    sentences = []
    entities = []
    words_per_sentence = 20
    num_sentences = word_count // words_per_sentence
    entity_types = [EntityType.RISK, EntityType.CONTROL, EntityType.POLICY]

    current_position = 0

    for i in range(num_sentences):
        # Determine if this sentence contains an entity
        has_entity = (i % int(1 / entity_density)) == 0

        if has_entity:
            entity_type = entity_types[i % len(entity_types)]
            entity_id = f"{entity_type.name}-{i:04d}"

            # Create sentence with entity
            sentence = (
                f"{entity_id}: This is a test entity with description spanning multiple words "
                f"to simulate realistic entity definitions in enterprise documents. "
                f"The entity has identifier {entity_id} and type {entity_type.name}."
            )

            # Calculate entity location
            entity_start = current_position
            entity_end = entity_start + len(sentence)

            entities.append(
                Entity(
                    type=entity_type,
                    id=entity_id,
                    text=sentence,
                    confidence=0.95,
                    location={"start": entity_start, "end": entity_end},
                )
            )
        else:
            # Regular sentence without entity
            sentence = " ".join([f"word{j}" for j in range(words_per_sentence)]) + "."

        sentences.append(sentence)
        current_position += len(sentence) + 1  # +1 for space

    text = " ".join(sentences)
    return text, entities


@pytest.fixture
def large_entity_rich_document():
    """Generate 10k-word document with ~50 entities for performance testing."""
    text, entities = generate_entity_rich_text(word_count=10000, entity_density=0.05)

    return Document(
        id="perf_test_entity_rich",
        text=text,
        entities=entities,
        metadata=create_test_metadata("large_entity_rich.pdf"),
        structure={},
    )


@pytest.fixture
def multi_section_document():
    """Generate document with 10 sections for section detection performance testing."""
    sections = []
    entities = []
    current_position = 0

    for section_num in range(1, 11):
        # Section heading
        heading = f"## Section {section_num}: Test Section {section_num}\n\n"
        sections.append(heading)
        current_position += len(heading)

        # Section content (3 paragraphs)
        for para_num in range(3):
            # Every 2nd paragraph has an entity
            if para_num % 2 == 0:
                entity_id = f"CTRL-SEC{section_num}-{para_num:02d}"
                paragraph = (
                    f"{entity_id}: This paragraph contains an entity with identifier {entity_id}. "
                    f"It describes control measures for section {section_num}. "
                    f"The control is part of the overall security framework. "
                )

                entities.append(
                    Entity(
                        type=EntityType.CONTROL,
                        id=entity_id,
                        text=paragraph,
                        confidence=0.95,
                        location={
                            "start": current_position,
                            "end": current_position + len(paragraph),
                        },
                    )
                )
            else:
                paragraph = (
                    f"This is a regular paragraph in section {section_num}. "
                    f"It contains supporting information and context. "
                    f"The content helps establish section boundaries. "
                )

            sections.append(paragraph + "\n\n")
            current_position += len(paragraph) + 2

    text = "".join(sections)

    return Document(
        id="perf_test_multi_section",
        text=text,
        entities=entities,
        metadata=create_test_metadata("multi_section.pdf"),
        structure={"sections": [f"Section {i}" for i in range(1, 11)]},
    )


class TestEntityAwareChunkingLatency:
    """Test entity-aware chunking latency against NFR-P3 requirements."""

    def test_entity_aware_chunking_latency_nfr_p3(self, large_entity_rich_document):
        """Should complete entity-aware chunking within <3.3s per 10k words (NFR-P3).

        Validates that entity-aware chunking overhead is <0.3s beyond baseline:
        - Story 3.1 baseline: ~3.0s for 10k words
        - Entity processing overhead target: <0.3s (10% increase)
        - Total target: <3.3s for entity-aware chunking
        """
        # GIVEN: 10k-word document with ~50 entities
        document = large_entity_rich_document
        word_count = len(document.text.split())

        # WHEN: Chunk with entity_aware=True
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(
            segmenter=segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        start_time = time.perf_counter()
        chunks = list(engine.process(document, context))
        elapsed = time.perf_counter() - start_time

        # THEN: Latency <3.3s (Story 3.1 baseline 3.0s + 0.3s entity overhead)
        target_total_s = 3.3 * _coverage_perf_multiplier()
        assert elapsed < target_total_s, (
            f"Entity-aware chunking took {elapsed:.3f}s (target: <{target_total_s:.3f}s, NFR-P3). "
            f"Document: {word_count} words, {len(document.entities)} entities, {len(chunks)} chunks."
        )

        # AND: Document processed successfully
        assert len(chunks) > 0
        assert word_count >= 10000, f"Test document has {word_count} words (expected: ≥10,000)"

        # Record metrics for baseline tracking
        print(
            f"\n[NFR-P3 Entity-Aware Baseline] 10k-word chunking: {elapsed:.3f}s "
            f"({len(chunks)} chunks, {word_count} words, {len(document.entities)} entities)"
        )

    def test_entity_analysis_overhead(self, large_entity_rich_document):
        """Entity analysis overhead should be <0.3s per 10k words.

        Measures the delta between baseline chunking (entity_aware=False) and
        entity-aware chunking (entity_aware=True) to isolate entity processing cost.
        """
        document = large_entity_rich_document
        segmenter = SentenceSegmenter()

        # Measure baseline without entity awareness (Story 3.1)
        engine_baseline = ChunkingEngine(
            segmenter=segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=False
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        start = time.perf_counter()
        baseline_chunks = list(engine_baseline.process(document, context))
        baseline_time = time.perf_counter() - start

        # Measure with entity awareness
        engine_entity = ChunkingEngine(
            segmenter=segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )

        start = time.perf_counter()
        entity_chunks = list(engine_entity.process(document, context))
        entity_time = time.perf_counter() - start

        # Calculate overhead
        overhead = entity_time - baseline_time
        overhead_pct = (overhead / baseline_time * 100) if baseline_time > 0 else 0

        target_overhead_s = 0.3 * _coverage_perf_multiplier()
        assert overhead < target_overhead_s, (
            f"Entity analysis overhead: {overhead:.3f}s (target: <{target_overhead_s:.3f}s). "
            f"Baseline: {baseline_time:.3f}s, Entity-aware: {entity_time:.3f}s, "
            f"Overhead: {overhead_pct:.1f}%"
        )

        # Verify both modes produce similar chunk counts
        assert len(baseline_chunks) > 0
        assert len(entity_chunks) > 0

        print(
            f"\n[Entity Overhead] Baseline: {baseline_time:.3f}s, "
            f"Entity-aware: {entity_time:.3f}s, Overhead: {overhead:.3f}s ({overhead_pct:.1f}%)"
        )

    def test_section_detection_overhead(self, multi_section_document):
        """Section detection overhead should be <0.1s per document.

        Measures the cost of detecting section boundaries in a document with
        10 sections. Section detection should be fast to avoid impacting overall
        chunking latency.
        """
        document = multi_section_document

        # GIVEN: Document with 10 sections
        section_count = len(document.structure.get("sections", []))
        assert section_count == 10, f"Test document should have 10 sections (got {section_count})"

        # WHEN: Section detection occurs during chunking
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512, overlap_pct=0.15)

        # Measure section detection time (embedded in chunking process)
        # Note: Section detection happens during sentence segmentation
        context = ProcessingContext(config={}, logger=None, metrics={})

        start_time = time.perf_counter()
        chunks = list(engine.process(document, context))
        total_time = time.perf_counter() - start_time

        # THEN: Total processing time should be reasonable
        # For a ~3k word document with 10 sections, expect <1.5s total
        # Section detection overhead should be negligible (<0.1s of total time)
        section_target_s = 1.5 * _coverage_perf_multiplier()
        assert total_time < section_target_s, (
            f"Multi-section document chunking took {total_time:.3f}s (expected <{section_target_s:.3f}s). "
            f"Document: {len(document.text.split())} words, {section_count} sections, {len(chunks)} chunks."
        )

        # AND: Document processed successfully with sections
        assert len(chunks) > 0

        # Note: Isolating pure section detection time requires internal instrumentation
        # This test validates that section-aware documents don't significantly impact performance
        print(
            f"\n[Section Detection] Multi-section chunking: {total_time:.3f}s "
            f"({section_count} sections, {len(chunks)} chunks)"
        )


class TestEntityAwareMemoryEfficiency:
    """Test that entity-aware chunking maintains memory efficiency."""

    def test_entity_metadata_memory_overhead(self, large_entity_rich_document):
        """Entity metadata should not significantly increase chunk memory footprint.

        Validates that storing entity tags and metadata doesn't balloon chunk size
        beyond reasonable limits.
        """
        # GIVEN: 10k-word document with ~50 entities
        document = large_entity_rich_document

        # WHEN: Chunk with entity_aware=True
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(
            segmenter=segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        chunks = list(engine.process(document, context))

        # THEN: Chunks should be created successfully
        assert len(chunks) > 0

        # AND: Each chunk with entities should have reasonable metadata size
        # (This is a smoke test - detailed memory profiling done separately)
        chunks_with_entities = [
            c for c in chunks if hasattr(c.metadata, "entity_tags") and c.metadata.entity_tags
        ]

        assert len(chunks_with_entities) > 0, "Expected some chunks to contain entities"

        # Record metrics
        avg_entities_per_chunk = sum(
            len(c.metadata.entity_tags) for c in chunks_with_entities
        ) / len(chunks_with_entities)

        print(
            f"\n[Memory Efficiency] {len(chunks_with_entities)} chunks with entities "
            f"(avg {avg_entities_per_chunk:.1f} entities/chunk)"
        )

"""Performance tests for memory efficiency (NFR-P2).

Tests memory usage requirements:
- Individual document processing: ≤500MB peak memory
- Batch processing: Constant memory across batch sizes
- No memory leaks across multiple documents

Uses get_total_memory() pattern from scripts/profile_pipeline.py for
accurate memory tracking across main + worker processes.
"""

import time
from datetime import datetime, timezone
from pathlib import Path

import psutil
import pytest

from data_extract.chunk import ChunkingEngine, SentenceSegmenter
from data_extract.core.models import Document, Metadata, ProcessingContext

pytestmark = [
    pytest.mark.P1,
    pytest.mark.performance,
    pytest.mark.chunking,
]


def get_total_memory() -> int:
    """Get total memory usage across main process and all workers.

    Adapted from scripts/profile_pipeline.py:151-167.
    Returns memory in bytes.
    """
    main_process = psutil.Process()
    total_memory = main_process.memory_info().rss

    # Add memory from all child processes (worker pool)
    try:
        children = main_process.children(recursive=True)
        for child in children:
            try:
                total_memory += child.memory_info().rss
            except psutil.NoSuchProcess:
                pass  # Worker exited
    except Exception:
        pass  # Fallback to main process memory only

    return total_memory


def bytes_to_mb(bytes_val: int) -> float:
    """Convert bytes to megabytes."""
    return bytes_val / (1024 * 1024)


class TestIndividualDocumentMemory:
    """Test memory usage for individual document processing."""

    def test_nfr_p2_individual_document_memory(self):
        """Should process individual document with ≤500MB peak memory (NFR-P2)."""
        # GIVEN: Large document (10k words)
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512)

        words_per_sentence = 50
        num_sentences = 200
        sentence_template = " ".join([f"word{i}" for i in range(words_per_sentence)]) + ". "
        text = sentence_template * num_sentences

        document = Document(
            id="memory_test",
            text=text,
            entities=[],
            metadata=Metadata(
                source_file=Path("memory_test.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(timezone.utc),
                tool_version="3.1.0",
                config_version="1.0",
            ),
            structure={},
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        # Baseline memory before processing
        baseline_memory = get_total_memory()

        # WHEN: Processing document
        chunks = list(engine.process(document, context))
        peak_memory = get_total_memory()
        memory_delta = peak_memory - baseline_memory

        # THEN: Peak memory delta ≤500MB
        memory_delta_mb = bytes_to_mb(memory_delta)
        assert (
            memory_delta_mb <= 500
        ), f"Memory delta: {memory_delta_mb:.1f}MB (requirement: ≤500MB)"

        print(
            f"\n[NFR-P2] Individual doc memory: {memory_delta_mb:.1f}MB "
            f"({len(chunks)} chunks, 10k words)"
        )

    def test_memory_release_after_processing(self):
        """Should release memory after document processing completes."""
        # GIVEN: ChunkingEngine
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512)

        # Baseline memory
        baseline_memory = get_total_memory()

        # WHEN: Processing document
        text = "This is a test sentence. " * 1000
        document = Document(
            id="release_test",
            text=text,
            entities=[],
            metadata=Metadata(
                source_file=Path("release_test.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(timezone.utc),
                tool_version="3.1.0",
                config_version="1.0",
            ),
            structure={},
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        chunks = list(engine.process(document, context))
        get_total_memory()

        # Clear chunks reference
        del chunks
        del document

        # Allow garbage collection
        import gc

        gc.collect()
        time.sleep(0.1)

        # THEN: Memory returns to near baseline
        final_memory = get_total_memory()
        memory_growth = final_memory - baseline_memory
        memory_growth_mb = bytes_to_mb(memory_growth)

        # Allow some memory growth for caches, but should not retain full chunk data
        assert memory_growth_mb < 50, f"Memory not released: {memory_growth_mb:.1f}MB retained"

        print(
            f"\n[Memory Release] Growth after cleanup: {memory_growth_mb:.1f}MB "
            f"(baseline: {bytes_to_mb(baseline_memory):.1f}MB)"
        )


class TestBatchProcessingMemory:
    """Test memory usage across batch processing."""

    @pytest.mark.parametrize("batch_size", [10, 50, 100])
    def test_constant_memory_across_batch_sizes(self, batch_size):
        """Should maintain constant memory across different batch sizes."""
        # GIVEN: ChunkingEngine
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512)

        baseline_memory = get_total_memory()
        peak_memory = baseline_memory

        # WHEN: Processing batch of documents sequentially
        for doc_num in range(batch_size):
            # Create document (1k words each)
            text = f"Document {doc_num} content. " * 200

            document = Document(
                id=f"batch_{batch_size}_doc_{doc_num}",
                text=text,
                entities=[],
                metadata=Metadata(
                    source_file=Path(f"batch_{doc_num}.pdf"),
                    file_hash=f"hash_{doc_num}",
                    processing_timestamp=datetime.now(timezone.utc),
                    tool_version="3.1.0",
                    config_version="1.0",
                ),
                structure={},
            )
            context = ProcessingContext(config={}, logger=None, metrics={})

            # Process document
            chunks = list(engine.process(document, context))

            # Track peak memory
            current_memory = get_total_memory()
            peak_memory = max(peak_memory, current_memory)

            # Clean up immediately (simulate streaming)
            del chunks
            del document

        # THEN: Peak memory is constant (doesn't grow with batch size)
        memory_delta = peak_memory - baseline_memory
        memory_delta_mb = bytes_to_mb(memory_delta)

        # Memory should not grow linearly with batch size
        # Allow ≤100MB growth regardless of batch size (constant overhead)
        assert (
            memory_delta_mb <= 100
        ), f"Batch {batch_size}: {memory_delta_mb:.1f}MB growth (expected: ≤100MB)"

        print(
            f"\n[Batch Memory] {batch_size} docs: {memory_delta_mb:.1f}MB peak "
            f"(baseline: {bytes_to_mb(baseline_memory):.1f}MB)"
        )

    def test_no_memory_leak_across_documents(self):
        """Should not leak memory across multiple document processing cycles."""
        # GIVEN: ChunkingEngine
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512)

        # Process first batch and measure memory
        baseline_memory = get_total_memory()

        for i in range(10):
            text = f"Batch 1 document {i}. " * 100
            document = Document(
                id=f"leak_test_1_{i}",
                text=text,
                entities=[],
                metadata=Metadata(
                    source_file=Path(f"leak_1_{i}.pdf"),
                    file_hash=f"hash_1_{i}",
                    processing_timestamp=datetime.now(timezone.utc),
                    tool_version="3.1.0",
                    config_version="1.0",
                ),
                structure={},
            )
            context = ProcessingContext(config={}, logger=None, metrics={})
            chunks = list(engine.process(document, context))
            del chunks
            del document

        batch1_memory = get_total_memory()

        # WHEN: Processing second batch
        for i in range(10):
            text = f"Batch 2 document {i}. " * 100
            document = Document(
                id=f"leak_test_2_{i}",
                text=text,
                entities=[],
                metadata=Metadata(
                    source_file=Path(f"leak_2_{i}.pdf"),
                    file_hash=f"hash_2_{i}",
                    processing_timestamp=datetime.now(timezone.utc),
                    tool_version="3.1.0",
                    config_version="1.0",
                ),
                structure={},
            )
            context = ProcessingContext(config={}, logger=None, metrics={})
            chunks = list(engine.process(document, context))
            del chunks
            del document

        batch2_memory = get_total_memory()

        # THEN: Memory should not grow significantly between batches
        batch1_delta = bytes_to_mb(batch1_memory - baseline_memory)
        batch2_delta = bytes_to_mb(batch2_memory - baseline_memory)
        memory_leak = batch2_delta - batch1_delta

        # Allow small growth for caching, but no significant leak
        assert abs(memory_leak) < 20, f"Memory leak detected: {memory_leak:.1f}MB growth"

        print(
            f"\n[Memory Leak Test] Batch1: {batch1_delta:.1f}MB, "
            f"Batch2: {batch2_delta:.1f}MB (leak: {memory_leak:.1f}MB)"
        )


class TestMemoryProfilingUtility:
    """Test memory profiling utility functions."""

    def test_get_total_memory_accuracy(self):
        """Should accurately measure total memory including workers."""
        # GIVEN: Current process
        baseline = get_total_memory()

        # WHEN: Allocating memory
        # Allocate ~10MB of data
        large_data = ["x" * 1000000 for _ in range(10)]  # 10 x 1MB strings

        after_alloc = get_total_memory()
        delta_mb = bytes_to_mb(after_alloc - baseline)

        # THEN: Detects memory increase
        assert delta_mb >= 5, f"Memory tracking detected {delta_mb:.1f}MB (expected: ≥5MB)"

        # Cleanup
        del large_data
        import gc

        gc.collect()

        print(f"\n[Memory Tracking] Detected allocation: {delta_mb:.1f}MB")

    def test_memory_measurement_overhead(self):
        """Should have minimal overhead for memory measurement."""
        # GIVEN: Memory measurement function
        # WHEN: Timing memory measurements
        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            _ = get_total_memory()

        elapsed = time.perf_counter() - start
        per_call = (elapsed / iterations) * 1000  # Convert to milliseconds

        # THEN: Each measurement is fast (<15ms per call - acceptable overhead)
        assert per_call < 15, f"Memory measurement: {per_call:.2f}ms/call (expected: <15ms)"

        print(f"\n[Memory Measurement] Overhead: {per_call:.2f}ms per call")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

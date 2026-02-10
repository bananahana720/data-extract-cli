"""Performance tests for quality metrics (Story 4.4).

Tests that quality metrics computation meets performance requirements:
- <10ms per chunk
- <10s for 1000 chunks
- Minimal memory overhead
"""

import pytest

pytestmark = [
    pytest.mark.P1,
    pytest.mark.performance,
]

import gc  # noqa: E402
import time  # noqa: E402
from typing import List  # noqa: E402

from data_extract.core.models import Chunk  # noqa: E402
from data_extract.semantic.quality_metrics import (  # noqa: E402
    QualityConfig,
    QualityMetricsStage,
)


class TestQualityPerformance:
    """Test performance characteristics of quality metrics."""

    @pytest.fixture
    def performance_config(self):
        """Create config optimized for performance testing."""
        return QualityConfig(
            use_cache=False,  # Test raw performance without caching
            detect_gibberish=True,  # Include all processing
        )

    @pytest.fixture
    def single_chunk(self) -> Chunk:
        """Create a single chunk for timing tests."""
        return Chunk(
            id="perf_001",
            text=(
                "The comprehensive financial audit report demonstrates significant "
                "improvements in operational efficiency and revenue management. "
                "Our detailed analysis reveals that key performance indicators "
                "have exceeded expectations across all business segments."
            ),
            document_id="perf_doc",
            position_index=0,
            token_count=40,
            word_count=40,
            quality_score=0.0,
            metadata={},
        )

    @pytest.fixture
    def small_corpus(self) -> List[Chunk]:
        """Create 10 chunks for small-scale testing."""
        texts = [
            "The quarterly earnings report shows strong revenue growth exceeding analyst expectations.",
            "Risk management procedures have been updated to reflect current market conditions.",
            "Compliance teams implemented new controls to address identified vulnerabilities.",
            "Financial statements indicate improved cash flow and reduced operational costs.",
            "Strategic initiatives have resulted in increased market share and customer satisfaction.",
            "Audit findings reveal no material weaknesses in internal control systems.",
            "Revenue recognition policies align with current accounting standards and regulations.",
            "Cost reduction measures have improved profit margins across all divisions.",
            "Investment portfolio performance exceeded benchmark indices for the fiscal year.",
            "Operational metrics demonstrate continuous improvement in efficiency and quality.",
        ]

        return [
            Chunk(
                id=f"small_{i:03d}",
                text=text,
                document_id="small_doc",
                position_index=i,
                token_count=len(text.split()),
                word_count=len(text.split()),
                quality_score=0.0,
                metadata={},
            )
            for i, text in enumerate(texts)
        ]

    @pytest.fixture
    def large_corpus(self) -> List[Chunk]:
        """Create 1000 chunks for large-scale testing."""
        base_texts = [
            "Financial analysis reveals strong performance metrics across all business segments with revenue growth.",
            "Operational efficiency improvements have resulted in significant cost savings and enhanced productivity.",
            "Risk assessment procedures identify potential vulnerabilities and implement appropriate control measures.",
            "Compliance monitoring ensures adherence to regulatory requirements and industry best practices.",
            "Strategic planning initiatives drive long-term growth and competitive advantage in the marketplace.",
        ]

        chunks = []
        for i in range(1000):
            text = base_texts[i % len(base_texts)] + f" Document section {i}."
            chunks.append(
                Chunk(
                    id=f"large_{i:04d}",
                    text=text,
                    document_id=f"doc_{i // 100}",
                    position_index=i % 100,
                    token_count=len(text.split()),
                    word_count=len(text.split()),
                    quality_score=0.0,
                    metadata={},
                )
            )
        return chunks

    def test_single_chunk_performance(self, performance_config, single_chunk):
        """Test performance for a single chunk (<10ms requirement)."""
        stage = QualityMetricsStage(config=performance_config)

        # Warm-up run (to load any lazy imports)
        _ = stage.process([single_chunk])

        # Timed runs
        times = []
        for _ in range(10):
            start = time.perf_counter()
            result = stage.process([single_chunk])
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # Convert to ms

            assert len(result) == 1
            assert result[0].quality_score > 0

        avg_time = sum(times) / len(times)
        max_time = max(times)

        # Log performance metrics
        print("\nSingle chunk performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  Min: {min(times):.2f}ms")

        # Verify requirement: <10ms per chunk
        assert avg_time < 10.0, f"Average time {avg_time:.2f}ms exceeds 10ms requirement"
        assert max_time < 20.0, f"Max time {max_time:.2f}ms too high (allowing 2x for variance)"

    def test_small_corpus_performance(self, performance_config, small_corpus):
        """Test performance for 10 chunks."""
        stage = QualityMetricsStage(config=performance_config)

        start = time.perf_counter()
        results = stage.process(small_corpus)
        elapsed = time.perf_counter() - start

        assert len(results) == 10
        per_chunk_time = (elapsed * 1000) / 10

        print("\nSmall corpus (10 chunks):")
        print(f"  Total time: {elapsed*1000:.2f}ms")
        print(f"  Per chunk: {per_chunk_time:.2f}ms")

        # Should still meet per-chunk requirement
        assert per_chunk_time < 10.0, f"Per-chunk time {per_chunk_time:.2f}ms exceeds requirement"

    def test_large_corpus_performance(self, performance_config, large_corpus):
        """Test performance for 1000 chunks (<10s requirement)."""
        stage = QualityMetricsStage(config=performance_config)

        # Force garbage collection before test
        gc.collect()

        start = time.perf_counter()
        results = stage.process(large_corpus)
        elapsed = time.perf_counter() - start

        assert len(results) == 1000
        per_chunk_time = (elapsed * 1000) / 1000

        print("\nLarge corpus (1000 chunks):")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Per chunk: {per_chunk_time:.2f}ms")

        # Verify requirement: <10s for 1000 chunks
        assert elapsed < 10.0, f"Total time {elapsed:.2f}s exceeds 10s requirement"
        assert per_chunk_time < 10.0, f"Per-chunk time {per_chunk_time:.2f}ms exceeds requirement"

    def test_cache_performance_improvement(self, single_chunk):
        """Test that caching improves performance."""
        # Test with cache enabled
        cached_config = QualityConfig(use_cache=True)
        cached_stage = QualityMetricsStage(config=cached_config)

        # Warmup run to avoid initialization overhead
        warmup = Chunk(
            id="warmup",
            text="Warmup text for initialization.",
            document_id="warmup",
            position_index=0,
            token_count=5,
            word_count=5,
            quality_score=0.0,
            metadata={},
        )
        _ = cached_stage.process([warmup])

        # First run (cache miss) - using the actual test chunk
        start1 = time.perf_counter()
        _ = cached_stage.process([single_chunk])
        first_run = time.perf_counter() - start1

        # Second run (cache hit)
        start2 = time.perf_counter()
        _ = cached_stage.process([single_chunk])
        second_run = time.perf_counter() - start2

        print("\nCache performance:")
        print(f"  First run (miss): {first_run*1000:.2f}ms")
        print(f"  Second run (hit): {second_run*1000:.2f}ms")
        print(f"  Speedup: {first_run/second_run:.1f}x")

        # Cache hit should be significantly faster
        assert second_run < first_run, "Cache hit should be faster than cache miss"

    def test_memory_efficiency(self, performance_config, large_corpus):
        """Test memory efficiency with large corpus."""
        import tracemalloc  # noqa: E402

        stage = QualityMetricsStage(config=performance_config)

        # Start memory tracking
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Process large corpus
        results = stage.process(large_corpus)

        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, "lineno")

        # Calculate total memory used
        total_memory = sum(stat.size_diff for stat in top_stats) / 1024 / 1024  # MB

        print("\nMemory usage for 1000 chunks:")
        print(f"  Total increase: {total_memory:.2f} MB")
        print(f"  Per chunk: {total_memory*1024:.2f} KB")

        tracemalloc.stop()

        # Memory usage should be reasonable (< 100MB for 1000 chunks)
        assert total_memory < 100, f"Memory usage {total_memory:.2f}MB exceeds 100MB limit"
        assert len(results) == 1000

    def test_scaling_linearity(self, performance_config):
        """Test that performance scales linearly with chunk count."""
        stage = QualityMetricsStage(config=performance_config)

        # Warmup run to avoid initialization overhead skewing results
        warmup_chunks = [
            Chunk(
                id="warmup",
                text="This is a warmup chunk.",
                document_id="warmup_doc",
                position_index=0,
                token_count=5,
                word_count=5,
                quality_score=0.0,
                metadata={},
            )
        ]
        _ = stage.process(warmup_chunks)

        sizes = [10, 50, 100, 200]
        times = []

        for size in sizes:
            chunks = [
                Chunk(
                    id=f"scale_{i:04d}",
                    text=f"This is test chunk number {i} with some financial content.",
                    document_id="scale_doc",
                    position_index=i,
                    token_count=10,
                    word_count=10,
                    quality_score=0.0,
                    metadata={},
                )
                for i in range(size)
            ]

            gc.collect()  # Clean slate for each test
            start = time.perf_counter()
            _ = stage.process(chunks)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        print("\nScaling test:")
        for size, elapsed in zip(sizes, times):
            per_chunk = (elapsed * 1000) / size
            print(f"  {size} chunks: {elapsed*1000:.2f}ms total, {per_chunk:.2f}ms per chunk")

        # Check that per-chunk time remains roughly constant
        per_chunk_times = [(t * 1000) / s for t, s in zip(times, sizes)]
        max_variance = max(per_chunk_times) / min(per_chunk_times)

        # Allow up to 3x variance in per-chunk time (reasonable for Python with GC, report generation)
        assert (
            max_variance < 3.0
        ), f"Performance not scaling linearly (variance: {max_variance:.2f}x)"

    def test_concurrent_processing_safety(self, performance_config, small_corpus):
        """Test that quality metrics can handle concurrent processing."""
        import queue  # noqa: E402
        import threading  # noqa: E402

        stage = QualityMetricsStage(config=performance_config)
        results_queue = queue.Queue()
        errors = []

        def process_chunks():
            try:
                result = stage.process(small_corpus)
                results_queue.put(len(result))
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=process_chunks)
            threads.append(t)

        # Start all threads
        start = time.perf_counter()
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join(timeout=5.0)

        elapsed = time.perf_counter() - start

        # Check results
        assert len(errors) == 0, f"Errors during concurrent processing: {errors}"

        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        assert len(results) == 5, "Not all threads completed"
        assert all(r == 10 for r in results), "Incorrect results from concurrent processing"

        print("\nConcurrent processing (5 threads):")
        print(f"  Total time: {elapsed*1000:.2f}ms")
        print("  All threads completed successfully")

    @pytest.mark.parametrize("text_length", [100, 500, 1000, 5000])
    def test_text_length_impact(self, performance_config, text_length):
        """Test performance impact of different text lengths."""
        # Generate text of specified length
        words = ["financial", "audit", "report", "analysis", "revenue", "performance"]
        text = " ".join(words[i % len(words)] for i in range(text_length // 10))

        chunk = Chunk(
            id="length_test",
            text=text,
            document_id="length_doc",
            position_index=0,
            token_count=text_length // 10,
            word_count=text_length // 10,
            quality_score=0.0,
            metadata={},
        )

        stage = QualityMetricsStage(config=performance_config)

        # Time processing
        times = []
        for _ in range(5):
            start = time.perf_counter()
            result = stage.process([chunk])
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)

            assert len(result) == 1

        avg_time = sum(times) / len(times)
        print(f"\nText length {text_length} chars: {avg_time:.2f}ms")

        # Even long texts should meet performance requirement
        assert avg_time < 20.0, f"Processing time {avg_time:.2f}ms too high for {text_length} chars"

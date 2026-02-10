"""
Performance benchmarks for pipeline orchestration.

This module benchmarks end-to-end pipeline performance, including:
- Format detection overhead
- Processor chain execution
- Formatter generation
- Batch processing throughput

NOTE: Tests skipped - brownfield processors/formatters moved to TRASH.
"""

import pytest

pytestmark = [
    pytest.mark.P1,
    pytest.mark.performance,
    pytest.mark.skip(
        reason="Brownfield processors/formatters moved to TRASH - needs greenfield rewrite"
    ),
]

from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402

# Brownfield imports no longer available - stub classes for syntax validation
# from src.core import ContentBlock, ContentType, ExtractionResult, Position  # noqa: E402
# from src.formatters import ChunkedTextFormatter, JsonFormatter, MarkdownFormatter  # noqa: E402
# from src.processors import ContextLinker, MetadataAggregator, QualityValidator  # noqa: E402
# from tests.performance.conftest import (  # noqa: E402
#     BenchmarkResult,
#     assert_memory_limit,
#     assert_performance_target,
# )


# Stub imports for F821 compliance - tests are skipped, these won't execute
class ContextLinker:  # noqa: E302
    """Stub class."""

    pass


class MetadataAggregator:  # noqa: E302
    """Stub class."""

    pass


class QualityValidator:  # noqa: E302
    """Stub class."""

    pass


class JsonFormatter:  # noqa: E302
    """Stub class."""

    pass


class MarkdownFormatter:  # noqa: E302
    """Stub class."""

    pass


class ChunkedTextFormatter:  # noqa: E302
    """Stub class."""

    pass


class BenchmarkResult:  # noqa: E302
    """Stub class."""

    def __init__(self, **kwargs):  # noqa: E302
        pass


def assert_performance_target(*args, **kwargs):  # noqa: E302
    """Stub function."""
    pass


def assert_memory_limit(*args, **kwargs):  # noqa: E302
    """Stub function."""
    pass


# ============================================================================
# Test Configuration
# ============================================================================

# Performance targets for pipeline operations (in milliseconds)
PROCESSOR_CHAIN_TARGET_MS = 1000  # Context + Metadata + Quality
FORMATTER_TARGET_MS = 500  # Format generation
END_TO_END_TARGET_MS = 5000  # Full pipeline on medium file


# ============================================================================
# Helper Functions
# ============================================================================


def create_sample_extraction_result(num_blocks: int = 100):
    """
    Create sample extraction result for benchmarking.

    Args:
        num_blocks: Number of content blocks to generate

    Returns:
        ExtractionResult with generated content blocks (not available - stub)
    """
    # Types not imported - return None to skip
    return None


# ============================================================================
# Processor Chain Benchmarks
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.processing
class TestProcessorChainBenchmarks:
    """Performance benchmarks for processor chain execution."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize processors for all tests."""
        self.context_linker = ContextLinker()
        self.metadata_aggregator = MetadataAggregator()
        self.quality_validator = QualityValidator()

    def test_context_linker_performance(self, perf_measure, production_baseline_manager):
        """Benchmark ContextLinker processing."""
        # Create sample data
        extraction_result = create_sample_extraction_result(num_blocks=100)

        # Measure performance
        with perf_measure() as perf:
            result = self.context_linker.process(extraction_result)

        # Verify processing succeeded
        assert result.success, f"Processing failed: {result.errors}"
        assert len(result.content_blocks) == len(extraction_result.content_blocks)

        # Create benchmark result
        benchmark = BenchmarkResult(
            operation="processor_context_linking",
            duration_ms=perf.duration_ms,
            memory_mb=perf.peak_memory_mb,
            file_size_kb=0,  # Not file-based
            throughput=(
                len(extraction_result.content_blocks) / perf.duration_seconds
                if perf.duration_seconds > 0
                else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={"num_blocks": len(extraction_result.content_blocks)},
        )

        # Assert performance targets
        assert_performance_target(perf.duration_ms, PROCESSOR_CHAIN_TARGET_MS, "Context linking")
        assert_memory_limit(perf.peak_memory_mb, 200, "Context linking")

        # Log for baseline
        print(f"\n{'='*60}")
        print("Context Linker Benchmark:")
        print(f"  Blocks Processed: {len(extraction_result.content_blocks)}")
        print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.3f}s)")
        print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
        print(f"  Throughput: {benchmark.throughput:.2f} blocks/s")
        print(f"{'='*60}")

        # Update baseline
        production_baseline_manager.update_baseline("processor_context_linking", benchmark)
        production_baseline_manager.save()

    def test_metadata_aggregator_performance(self, perf_measure, production_baseline_manager):
        """Benchmark MetadataAggregator processing."""
        # Create sample data
        extraction_result = create_sample_extraction_result(num_blocks=100)

        # Measure performance
        with perf_measure() as perf:
            result = self.metadata_aggregator.process(extraction_result)

        # Verify processing succeeded
        assert result.success, f"Processing failed: {result.errors}"

        # Create benchmark result
        benchmark = BenchmarkResult(
            operation="processor_metadata_aggregation",
            duration_ms=perf.duration_ms,
            memory_mb=perf.peak_memory_mb,
            file_size_kb=0,
            throughput=(
                len(extraction_result.content_blocks) / perf.duration_seconds
                if perf.duration_seconds > 0
                else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={"num_blocks": len(extraction_result.content_blocks)},
        )

        # Assert performance targets
        assert_performance_target(
            perf.duration_ms, PROCESSOR_CHAIN_TARGET_MS, "Metadata aggregation"
        )
        assert_memory_limit(perf.peak_memory_mb, 200, "Metadata aggregation")

        # Log for baseline
        print(f"\n{'='*60}")
        print("Metadata Aggregator Benchmark:")
        print(f"  Blocks Processed: {len(extraction_result.content_blocks)}")
        print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.3f}s)")
        print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
        print(f"  Throughput: {benchmark.throughput:.2f} blocks/s")
        print(f"{'='*60}")

        # Update baseline
        production_baseline_manager.update_baseline("processor_metadata_aggregation", benchmark)
        production_baseline_manager.save()

    def test_quality_validator_performance(self, perf_measure, production_baseline_manager):
        """Benchmark QualityValidator processing."""
        # Create sample data
        extraction_result = create_sample_extraction_result(num_blocks=100)

        # Measure performance
        with perf_measure() as perf:
            result = self.quality_validator.process(extraction_result)

        # Verify processing succeeded
        assert result.success, f"Processing failed: {result.errors}"

        # Create benchmark result
        benchmark = BenchmarkResult(
            operation="processor_quality_validation",
            duration_ms=perf.duration_ms,
            memory_mb=perf.peak_memory_mb,
            file_size_kb=0,
            throughput=(
                len(extraction_result.content_blocks) / perf.duration_seconds
                if perf.duration_seconds > 0
                else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={
                "num_blocks": len(extraction_result.content_blocks),
                "quality_score": result.quality_score,
            },
        )

        # Assert performance targets
        assert_performance_target(perf.duration_ms, PROCESSOR_CHAIN_TARGET_MS, "Quality validation")
        assert_memory_limit(perf.peak_memory_mb, 200, "Quality validation")

        # Log for baseline
        print(f"\n{'='*60}")
        print("Quality Validator Benchmark:")
        print(f"  Blocks Processed: {len(extraction_result.content_blocks)}")
        print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.3f}s)")
        print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
        print(f"  Throughput: {benchmark.throughput:.2f} blocks/s")
        print(f"  Quality Score: {result.quality_score:.2f}")
        print(f"{'='*60}")

        # Update baseline
        production_baseline_manager.update_baseline("processor_quality_validation", benchmark)
        production_baseline_manager.save()

    def test_full_processor_chain_performance(self, perf_measure, production_baseline_manager):
        """Benchmark full processor chain execution."""
        # Create sample data
        extraction_result = create_sample_extraction_result(num_blocks=100)

        # Measure performance of full chain
        with perf_measure() as perf:
            # Run full processor chain
            result = self.context_linker.process(extraction_result)
            result = self.metadata_aggregator.process(result)
            result = self.quality_validator.process(result)

        # Verify processing succeeded
        assert result.success, f"Processing failed: {result.errors}"

        # Create benchmark result
        benchmark = BenchmarkResult(
            operation="processor_chain_full",
            duration_ms=perf.duration_ms,
            memory_mb=perf.peak_memory_mb,
            file_size_kb=0,
            throughput=(
                len(extraction_result.content_blocks) / perf.duration_seconds
                if perf.duration_seconds > 0
                else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={
                "num_blocks": len(extraction_result.content_blocks),
                "num_processors": 3,
                "quality_score": result.quality_score,
            },
        )

        # Assert performance targets (sum of all processors)
        assert_performance_target(
            perf.duration_ms, PROCESSOR_CHAIN_TARGET_MS * 3, "Full processor chain", tolerance=0.3
        )
        assert_memory_limit(perf.peak_memory_mb, 300, "Full processor chain")

        # Log for baseline
        print(f"\n{'='*60}")
        print("Full Processor Chain Benchmark:")
        print(f"  Blocks Processed: {len(extraction_result.content_blocks)}")
        print("  Processors: Context → Metadata → Quality")
        print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.3f}s)")
        print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
        print(f"  Throughput: {benchmark.throughput:.2f} blocks/s")
        print(f"  Quality Score: {result.quality_score:.2f}")
        print(f"{'='*60}")

        # Update baseline
        production_baseline_manager.update_baseline("processor_chain_full", benchmark)
        production_baseline_manager.save()


# ============================================================================
# Formatter Benchmarks
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.formatting
class TestFormatterBenchmarks:
    """Performance benchmarks for output formatters."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize formatters for all tests."""
        self.json_formatter = JsonFormatter()
        self.markdown_formatter = MarkdownFormatter()
        self.chunked_formatter = ChunkedTextFormatter()

    def test_json_formatter_performance(self, perf_measure, production_baseline_manager):
        """Benchmark JSON formatter."""
        # Create sample data
        extraction_result = create_sample_extraction_result(num_blocks=100)

        # Measure performance
        with perf_measure() as perf:
            output = self.json_formatter.format(extraction_result.content_blocks)

        # Verify formatting succeeded
        assert output.success, f"Formatting failed: {output.errors}"
        assert len(output.formatted_content) > 0

        # Create benchmark result
        benchmark = BenchmarkResult(
            operation="formatter_json",
            duration_ms=perf.duration_ms,
            memory_mb=perf.peak_memory_mb,
            file_size_kb=len(output.formatted_content) / 1024,
            throughput=(
                len(extraction_result.content_blocks) / perf.duration_seconds
                if perf.duration_seconds > 0
                else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={
                "num_blocks": len(extraction_result.content_blocks),
                "output_size_kb": len(output.formatted_content) / 1024,
            },
        )

        # Assert performance targets
        assert_performance_target(perf.duration_ms, FORMATTER_TARGET_MS, "JSON formatting")
        assert_memory_limit(perf.peak_memory_mb, 100, "JSON formatting")

        # Log for baseline
        print(f"\n{'='*60}")
        print("JSON Formatter Benchmark:")
        print(f"  Blocks Formatted: {len(extraction_result.content_blocks)}")
        print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.3f}s)")
        print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
        print(f"  Output Size: {len(output.formatted_content) / 1024:.2f} KB")
        print(f"  Throughput: {benchmark.throughput:.2f} blocks/s")
        print(f"{'='*60}")

        # Update baseline
        production_baseline_manager.update_baseline("formatter_json", benchmark)
        production_baseline_manager.save()

    def test_markdown_formatter_performance(self, perf_measure, production_baseline_manager):
        """Benchmark Markdown formatter."""
        # Create sample data
        extraction_result = create_sample_extraction_result(num_blocks=100)

        # Measure performance
        with perf_measure() as perf:
            output = self.markdown_formatter.format(extraction_result.content_blocks)

        # Verify formatting succeeded
        assert output.success, f"Formatting failed: {output.errors}"
        assert len(output.formatted_content) > 0

        # Create benchmark result
        benchmark = BenchmarkResult(
            operation="formatter_markdown",
            duration_ms=perf.duration_ms,
            memory_mb=perf.peak_memory_mb,
            file_size_kb=len(output.formatted_content) / 1024,
            throughput=(
                len(extraction_result.content_blocks) / perf.duration_seconds
                if perf.duration_seconds > 0
                else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={
                "num_blocks": len(extraction_result.content_blocks),
                "output_size_kb": len(output.formatted_content) / 1024,
            },
        )

        # Assert performance targets
        assert_performance_target(perf.duration_ms, FORMATTER_TARGET_MS, "Markdown formatting")
        assert_memory_limit(perf.peak_memory_mb, 100, "Markdown formatting")

        # Log for baseline
        print(f"\n{'='*60}")
        print("Markdown Formatter Benchmark:")
        print(f"  Blocks Formatted: {len(extraction_result.content_blocks)}")
        print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.3f}s)")
        print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
        print(f"  Output Size: {len(output.formatted_content) / 1024:.2f} KB")
        print(f"  Throughput: {benchmark.throughput:.2f} blocks/s")
        print(f"{'='*60}")

        # Update baseline
        production_baseline_manager.update_baseline("formatter_markdown", benchmark)
        production_baseline_manager.save()

    def test_chunked_formatter_performance(self, perf_measure, production_baseline_manager):
        """Benchmark Chunked Text formatter."""
        # Create sample data
        extraction_result = create_sample_extraction_result(num_blocks=100)

        # Measure performance
        with perf_measure() as perf:
            output = self.chunked_formatter.format(extraction_result.content_blocks)

        # Verify formatting succeeded
        assert output.success, f"Formatting failed: {output.errors}"
        assert len(output.formatted_content) > 0

        # Create benchmark result
        benchmark = BenchmarkResult(
            operation="formatter_chunked",
            duration_ms=perf.duration_ms,
            memory_mb=perf.peak_memory_mb,
            file_size_kb=len(output.formatted_content) / 1024,
            throughput=(
                len(extraction_result.content_blocks) / perf.duration_seconds
                if perf.duration_seconds > 0
                else 0
            ),
            timestamp=datetime.now().isoformat(),
            metadata={
                "num_blocks": len(extraction_result.content_blocks),
                "output_size_kb": len(output.formatted_content) / 1024,
            },
        )

        # Assert performance targets
        assert_performance_target(perf.duration_ms, FORMATTER_TARGET_MS, "Chunked formatting")
        assert_memory_limit(perf.peak_memory_mb, 100, "Chunked formatting")

        # Log for baseline
        print(f"\n{'='*60}")
        print("Chunked Formatter Benchmark:")
        print(f"  Blocks Formatted: {len(extraction_result.content_blocks)}")
        print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.3f}s)")
        print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
        print(f"  Output Size: {len(output.formatted_content) / 1024:.2f} KB")
        print(f"  Throughput: {benchmark.throughput:.2f} blocks/s")
        print(f"{'='*60}")

        # Update baseline
        production_baseline_manager.update_baseline("formatter_chunked", benchmark)
        production_baseline_manager.save()


# ============================================================================
# Batch Processing Benchmarks
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.pipeline
class TestBatchProcessingBenchmarks:
    """Performance benchmarks for batch processing operations."""

    def test_sequential_batch_performance(
        self, fixture_dir: Path, perf_measure, production_baseline_manager
    ):
        """Benchmark sequential batch processing."""
        from extractors.pdf_extractor import PdfExtractor  # noqa: E402

        # Get sample files
        pdf_files = list((fixture_dir / "real-world-files").glob("*.pdf"))[:3]  # Process 3 files

        if len(pdf_files) < 3:
            pytest.skip("Not enough PDF files for batch test")

        extractor = PdfExtractor()
        results = []

        # Measure performance
        with perf_measure() as perf:
            for pdf_file in pdf_files:
                result = extractor.extract(pdf_file)
                results.append(result)

        # Verify all succeeded
        success_count = sum(1 for r in results if r.success)
        assert success_count == len(
            pdf_files
        ), f"Only {success_count}/{len(pdf_files)} extractions succeeded"

        # Calculate metrics
        total_size_kb = sum(f.stat().st_size / 1024 for f in pdf_files)
        throughput = len(pdf_files) / perf.duration_seconds if perf.duration_seconds > 0 else 0

        # Create benchmark result
        benchmark = BenchmarkResult(
            operation="batch_sequential",
            duration_ms=perf.duration_ms,
            memory_mb=perf.peak_memory_mb,
            file_size_kb=total_size_kb,
            throughput=throughput,
            timestamp=datetime.now().isoformat(),
            metadata={"num_files": len(pdf_files), "files_per_second": throughput},
        )

        # Assert performance targets
        assert_performance_target(
            perf.duration_ms,
            END_TO_END_TARGET_MS * len(pdf_files),
            "Batch sequential processing",
            tolerance=1.0,
        )
        assert_memory_limit(perf.peak_memory_mb, 500, "Batch sequential processing")

        # Log for baseline
        print(f"\n{'='*60}")
        print("Sequential Batch Processing Benchmark:")
        print(f"  Files Processed: {len(pdf_files)}")
        print(f"  Total Size: {total_size_kb:.2f} KB")
        print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.2f}s)")
        print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
        print(f"  Throughput: {throughput:.2f} files/s")
        print(f"{'='*60}")

        # Update baseline
        production_baseline_manager.update_baseline("batch_sequential", benchmark)
        production_baseline_manager.save()

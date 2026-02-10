"""
Baseline capture script - runs benchmarks without strict assertions.

This script establishes initial performance baselines by running all
extractors on sample files and recording actual performance without
failing on threshold violations.

Run with: pytest tests/performance/test_baseline_capture.py -v -s

NOTE: Tests skipped - brownfield extractors moved to TRASH.
"""

import pytest

pytestmark = [
    pytest.mark.P1,
    pytest.mark.performance,
    pytest.mark.skip(reason="Brownfield extractors moved to TRASH - needs greenfield rewrite"),
]

from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402

# Brownfield imports no longer available - stub classes for syntax validation
# from extractors.excel_extractor import ExcelExtractor  # noqa: E402
# from extractors.pdf_extractor import PdfExtractor  # noqa: E402
# from extractors.txt_extractor import TextFileExtractor  # noqa: E402
# from tests.performance.conftest import (  # noqa: E402
#     BenchmarkResult,
#     PerformanceMeasurement,
# )


# Stub imports for F821 compliance - tests are skipped, these won't execute
class PdfExtractor:  # noqa: E302
    """Stub class."""

    pass


class ExcelExtractor:  # noqa: E302
    """Stub class."""

    pass


class TextFileExtractor:  # noqa: E302
    """Stub class."""

    pass


class BenchmarkResult:  # noqa: E302
    """Stub class."""

    def __init__(self, **kwargs):  # noqa: E302
        pass


def get_file_size_kb(file_path: Path) -> float:
    """Get file size in kilobytes."""
    return file_path.stat().st_size / 1024


def create_benchmark(operation: str, perf, file_path: Path, extra_metadata: dict = None):
    """Create benchmark result."""
    file_size_kb = get_file_size_kb(file_path)
    throughput = file_size_kb / perf.duration_seconds if perf.duration_seconds > 0 else 0

    # Return dict instead of BenchmarkResult (type not imported)
    return {
        "operation": operation,
        "duration_ms": perf.duration_ms,
        "memory_mb": perf.peak_memory_mb,
        "file_size_kb": file_size_kb,
        "throughput": throughput,
        "timestamp": datetime.now().isoformat(),
        "metadata": {"file_name": file_path.name, **(extra_metadata or {})},
    }


@pytest.mark.performance
@pytest.mark.slow
class TestBaselineCapture:
    """Capture performance baselines without strict assertions."""

    def test_capture_pdf_baselines(
        self, fixture_dir: Path, perf_measure, production_baseline_manager
    ):
        """Capture PDF extraction baselines."""
        extractor = PdfExtractor()

        # Test files of different sizes
        test_files = [
            ("pdf_small", "COBIT-2019-Framework-Introduction-and-Methodology_res_eng_1118.pdf"),
            ("pdf_medium", "NIST.SP.800-37r2.pdf"),
            ("pdf_large", "COBIT-2019-Design-Guide_res_eng_1218.pdf"),
        ]

        for operation, filename in test_files:
            pdf_file = fixture_dir / "real-world-files" / filename

            if not pdf_file.exists():
                print(f"SKIP: {filename} not found")
                continue

            print(f"\n{'='*70}")
            print(f"Benchmarking: {filename}")

            # Measure
            with perf_measure() as perf:
                result = extractor.extract(pdf_file)

            # Check success
            if not result.success:
                print(f"  FAILED: {result.errors}")
                continue

            # Create benchmark
            benchmark = create_benchmark(
                operation=operation,
                perf=perf,
                file_path=pdf_file,
                extra_metadata={"pages": result.document_metadata.page_count},
            )

            # Print results
            print(f"  File Size: {benchmark.file_size_kb:.2f} KB")
            print(f"  Pages: {result.document_metadata.page_count}")
            print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.2f}s)")
            print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
            print(f"  Throughput: {benchmark.throughput:.2f} KB/s")
            print(f"  Blocks: {len(result.content_blocks)}")
            print(f"{'='*70}")

            # Save baseline
            production_baseline_manager.update_baseline(operation, benchmark)

        production_baseline_manager.save()
        print(f"\nBaselines saved to: {production_baseline_manager.baseline_file}")

    def test_capture_excel_baselines(
        self, fixture_dir: Path, perf_measure, production_baseline_manager
    ):
        """Capture Excel extraction baselines."""
        extractor = ExcelExtractor()

        test_files = [
            ("excel_small", "excel/simple_single_sheet.xlsx"),
            ("excel_medium", "real-world-files/NIST-Privacy-Framework-V1.0-Core.xlsx"),
            ("excel_large", "real-world-files/sp800-53ar5-assessment-procedures.xlsx"),
        ]

        for operation, relative_path in test_files:
            excel_file = fixture_dir / relative_path

            if not excel_file.exists():
                print(f"SKIP: {relative_path} not found")
                continue

            print(f"\n{'='*70}")
            print(f"Benchmarking: {relative_path}")

            with perf_measure() as perf:
                result = extractor.extract(excel_file)

            if not result.success:
                print(f"  FAILED: {result.errors}")
                continue

            benchmark = create_benchmark(operation, perf, excel_file)

            print(f"  File Size: {benchmark.file_size_kb:.2f} KB")
            print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.2f}s)")
            print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
            print(f"  Throughput: {benchmark.throughput:.2f} KB/s")
            print(f"  Blocks: {len(result.content_blocks)}")
            print(f"{'='*70}")

            production_baseline_manager.update_baseline(operation, benchmark)

        production_baseline_manager.save()

    def test_capture_txt_baselines(
        self, fixture_dir: Path, perf_measure, production_baseline_manager
    ):
        """Capture TXT extraction baselines."""
        extractor = TextFileExtractor()

        test_files = [
            ("txt_small", "sample.txt"),
            ("txt_medium", "real-world-files/test_case_03_nested_structure.txt"),
        ]

        for operation, relative_path in test_files:
            txt_file = fixture_dir / relative_path

            if not txt_file.exists():
                print(f"SKIP: {relative_path} not found")
                continue

            print(f"\n{'='*70}")
            print(f"Benchmarking: {relative_path}")

            with perf_measure() as perf:
                result = extractor.extract(txt_file)

            if not result.success:
                print(f"  FAILED: {result.errors}")
                continue

            benchmark = create_benchmark(operation, perf, txt_file)

            print(f"  File Size: {benchmark.file_size_kb:.2f} KB")
            print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.2f}s)")
            print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
            print(f"  Throughput: {benchmark.throughput:.2f} KB/s")
            print(f"  Blocks: {len(result.content_blocks)}")
            print(f"{'='*70}")

            production_baseline_manager.update_baseline(operation, benchmark)

        production_baseline_manager.save()

    def test_capture_processor_baselines(self, perf_measure, production_baseline_manager):
        """Capture processor chain baselines."""
        from src.core import (  # noqa: E402
            ContentBlock,
            ContentType,
            DocumentMetadata,
            ExtractionResult,
            Position,
        )
        from src.processors import ContextLinker, MetadataAggregator, QualityValidator  # noqa: E402

        # Create sample data
        blocks = []
        for i in range(100):
            block = ContentBlock(
                block_type=ContentType.PARAGRAPH,
                content=f"Sample paragraph {i} for benchmarking.",
                position=Position(page=i // 20 + 1, sequence_index=i),
                metadata={},
            )
            blocks.append(block)

        metadata = DocumentMetadata(
            source_file=Path("benchmark.txt"),
            file_format="txt",
            file_size_bytes=10000,
            page_count=5,
            word_count=500,
        )

        extraction_result = ExtractionResult(
            content_blocks=tuple(blocks),
            document_metadata=metadata,
            success=True,
            errors=(),
            warnings=(),
        )

        # Test processors
        processors = [
            ("processor_context", ContextLinker()),
            ("processor_metadata", MetadataAggregator()),
            ("processor_quality", QualityValidator()),
        ]

        for operation, processor in processors:
            print(f"\n{'='*70}")
            print(f"Benchmarking: {operation}")

            with perf_measure() as perf:
                result = processor.process(extraction_result)

            if not result.success:
                print(f"  FAILED: {result.errors}")
                continue

            throughput = len(blocks) / perf.duration_seconds if perf.duration_seconds > 0 else 0

            benchmark = BenchmarkResult(
                operation=operation,
                duration_ms=perf.duration_ms,
                memory_mb=perf.peak_memory_mb,
                file_size_kb=0,
                throughput=throughput,
                timestamp=datetime.now().isoformat(),
                metadata={"num_blocks": len(blocks)},
            )

            print(f"  Blocks: {len(blocks)}")
            print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.3f}s)")
            print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
            print(f"  Throughput: {throughput:.2f} blocks/s")
            print(f"{'='*70}")

            production_baseline_manager.update_baseline(operation, benchmark)

        production_baseline_manager.save()

    def test_capture_formatter_baselines(self, perf_measure, production_baseline_manager):
        """Capture formatter baselines."""
        from src.core import ContentBlock, ContentType, Position  # noqa: E402
        from src.formatters import (  # noqa: E402
            ChunkedTextFormatter,
            JsonFormatter,
            MarkdownFormatter,
        )

        # Create sample data
        blocks = []
        for i in range(100):
            block = ContentBlock(
                block_type=ContentType.PARAGRAPH,
                content=f"Sample paragraph {i} for benchmarking.",
                position=Position(page=i // 20 + 1, sequence_index=i),
                metadata={},
            )
            blocks.append(block)

        formatters = [
            ("formatter_json", JsonFormatter()),
            ("formatter_markdown", MarkdownFormatter()),
            ("formatter_chunked", ChunkedTextFormatter()),
        ]

        for operation, formatter in formatters:
            print(f"\n{'='*70}")
            print(f"Benchmarking: {operation}")

            with perf_measure() as perf:
                output = formatter.format(tuple(blocks))

            if not output.success:
                print(f"  FAILED: {output.errors}")
                continue

            throughput = len(blocks) / perf.duration_seconds if perf.duration_seconds > 0 else 0

            benchmark = BenchmarkResult(
                operation=operation,
                duration_ms=perf.duration_ms,
                memory_mb=perf.peak_memory_mb,
                file_size_kb=len(output.formatted_content) / 1024,
                throughput=throughput,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "num_blocks": len(blocks),
                    "output_size_kb": len(output.formatted_content) / 1024,
                },
            )

            print(f"  Blocks: {len(blocks)}")
            print(f"  Duration: {perf.duration_ms:.2f} ms ({perf.duration_seconds:.3f}s)")
            print(f"  Peak Memory: {perf.peak_memory_mb:.2f} MB")
            print(f"  Output Size: {len(output.formatted_content) / 1024:.2f} KB")
            print(f"  Throughput: {throughput:.2f} blocks/s")
            print(f"{'='*70}")

            production_baseline_manager.update_baseline(operation, benchmark)

        production_baseline_manager.save()

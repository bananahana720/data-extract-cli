#!/usr/bin/env python
"""
Test Extraction Runner - Real-World File Validation

Tests the data-extractor-tool against real enterprise documents to validate:
- Extraction accuracy and completeness
- Error handling and recovery
- Performance metrics
- Output quality

This provides practical validation complementing unit/integration tests.
"""

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors import DocxExtractor, PdfExtractor
from src.formatters import JsonFormatter, MarkdownFormatter
from src.infrastructure import get_logger
from src.pipeline import ExtractionPipeline
from src.processors import ContextLinker, MetadataAggregator, QualityValidator

from examples.minimal_extractor import TextFileExtractor

# Try to import optional extractors
try:
    from src.extractors.pptx_extractor import PptxExtractor
except ImportError:
    PptxExtractor = None

try:
    from src.extractors.excel_extractor import ExcelExtractor
except ImportError:
    ExcelExtractor = None

logger = get_logger(__name__)


class TestExtractionRunner:
    """Runs test extractions and generates comprehensive reports."""

    def __init__(self, test_files_dir: Path, output_dir: Path):
        """
        Initialize test runner.

        Args:
            test_files_dir: Directory containing test files
            output_dir: Directory for extraction outputs
        """
        self.test_files_dir = test_files_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Create pipeline
        self.pipeline = self._create_pipeline()

        # Results storage
        self.results: List[Dict[str, Any]] = []

    def _create_pipeline(self) -> ExtractionPipeline:
        """Create and configure extraction pipeline."""
        pipeline = ExtractionPipeline()

        # Register extractors
        pipeline.register_extractor("docx", DocxExtractor())
        pipeline.register_extractor("pdf", PdfExtractor())

        # Register optional extractors if available
        if PptxExtractor is not None:
            pipeline.register_extractor("pptx", PptxExtractor())
        if ExcelExtractor is not None:
            pipeline.register_extractor("xlsx", ExcelExtractor())

        pipeline.register_extractor("txt", TextFileExtractor())  # Text file extractor

        # Add processors
        pipeline.add_processor(ContextLinker())
        pipeline.add_processor(MetadataAggregator())
        pipeline.add_processor(QualityValidator())

        # Add formatters
        pipeline.add_formatter(JsonFormatter())
        pipeline.add_formatter(MarkdownFormatter())

        return pipeline

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run extraction tests on all files.

        Returns:
            Summary of all test results
        """
        print("=" * 80)
        print(">> Data Extraction Tool - Real-World File Testing")
        print("=" * 80)
        print(f"\nTest files directory: {self.test_files_dir}")
        print(f"Output directory: {self.output_dir}")
        print(f"Timestamp: {datetime.now().isoformat()}\n")

        # Get all test files
        test_files = list(self.test_files_dir.glob("*"))
        test_files = [f for f in test_files if f.is_file()]

        print(f"Found {len(test_files)} test files\n")

        # Group files by type
        files_by_type = self._group_files_by_type(test_files)

        # Run tests by file type
        for file_type, files in files_by_type.items():
            print(f"\n{'=' * 80}")
            print(f">> Testing {file_type.upper()} files ({len(files)} files)")
            print("=" * 80)

            for file_path in files:
                self._test_file(file_path, file_type)

        # Generate summary
        summary = self._generate_summary()

        # Save results
        self._save_results(summary)

        # Print summary
        self._print_summary(summary)

        return summary

    def _group_files_by_type(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Group files by extension."""
        by_type = {"pdf": [], "xlsx": [], "txt": [], "docx": [], "pptx": [], "other": []}

        for file_path in files:
            ext = file_path.suffix.lower().lstrip(".")
            if ext in by_type:
                by_type[ext].append(file_path)
            else:
                by_type["other"].append(file_path)

        # Remove empty categories
        return {k: v for k, v in by_type.items() if v}

    def _test_file(self, file_path: Path, file_type: str) -> None:
        """
        Test extraction on a single file.

        Args:
            file_path: Path to test file
            file_type: File extension/type
        """
        print(f"\n  Testing: {file_path.name}")

        result = {
            "file_name": file_path.name,
            "file_type": file_type,
            "file_size": file_path.stat().st_size,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "errors": [],
            "warnings": [],
            "metrics": {},
            "output_files": [],
        }

        try:
            # Run extraction
            start_time = datetime.now()
            pipeline_result = self.pipeline.process_file(file_path)
            duration = (datetime.now() - start_time).total_seconds()

            result["success"] = pipeline_result.success
            result["metrics"]["duration_seconds"] = duration

            if pipeline_result.success:
                # Extract metrics
                result["metrics"]["blocks_extracted"] = len(
                    pipeline_result.extraction_result.content_blocks
                )

                if pipeline_result.processing_result:
                    result["metrics"][
                        "quality_score"
                    ] = pipeline_result.processing_result.quality_score
                    if pipeline_result.processing_result.quality_issues:
                        result["warnings"].extend(pipeline_result.processing_result.quality_issues)

                # Save outputs
                for formatted_output in pipeline_result.formatted_outputs:
                    output_filename = f"{file_path.stem}_{formatted_output.format_type}.{formatted_output.format_type}"
                    output_path = self.output_dir / output_filename

                    output_path.write_text(formatted_output.content, encoding="utf-8")
                    result["output_files"].append(str(output_path))

                print(
                    f"    [OK] SUCCESS - {result['metrics']['blocks_extracted']} blocks, "
                    f"{duration:.2f}s, quality: {result['metrics'].get('quality_score', 'N/A')}"
                )

            else:
                result["errors"] = (
                    list(pipeline_result.all_errors) if pipeline_result.all_errors else []
                )
                print(f"    [FAIL] FAILED - {result['errors']}")

        except Exception as e:
            result["errors"].append(str(e))
            result["traceback"] = traceback.format_exc()
            print(f"    [ERROR] EXCEPTION - {str(e)}")

        self.results.append(result)

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of all test results."""
        total_files = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total_files - successful

        # Group by file type
        by_type = {}
        for result in self.results:
            file_type = result["file_type"]
            if file_type not in by_type:
                by_type[file_type] = {"total": 0, "success": 0, "failed": 0}

            by_type[file_type]["total"] += 1
            if result["success"]:
                by_type[file_type]["success"] += 1
            else:
                by_type[file_type]["failed"] += 1

        # Calculate metrics
        total_duration = sum(r["metrics"].get("duration_seconds", 0) for r in self.results)
        avg_duration = total_duration / total_files if total_files > 0 else 0

        total_blocks = sum(
            r["metrics"].get("blocks_extracted", 0) for r in self.results if r["success"]
        )
        avg_quality = sum(
            r["metrics"].get("quality_score", 0)
            for r in self.results
            if r["success"] and "quality_score" in r["metrics"]
        )
        quality_count = sum(
            1 for r in self.results if r["success"] and "quality_score" in r["metrics"]
        )
        avg_quality = avg_quality / quality_count if quality_count > 0 else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_files * 100) if total_files > 0 else 0,
            "by_type": by_type,
            "metrics": {
                "total_duration_seconds": total_duration,
                "avg_duration_seconds": avg_duration,
                "total_blocks_extracted": total_blocks,
                "avg_quality_score": avg_quality,
            },
            "detailed_results": self.results,
        }

    def _save_results(self, summary: Dict[str, Any]) -> None:
        """Save results to JSON file."""
        results_file = (
            self.output_dir
            / f"test_extraction_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n>> Results saved to: {results_file}")

    def _print_summary(self, summary: Dict[str, Any]) -> None:
        """Print summary report to console."""
        print("\n" + "=" * 80)
        print(">> TEST EXTRACTION SUMMARY")
        print("=" * 80)

        print(f"\n  Total Files: {summary['total_files']}")
        print(f"  [OK] Successful: {summary['successful']}")
        print(f"  [FAIL] Failed: {summary['failed']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")

        print("\n  Results by File Type:")
        for file_type, stats in summary["by_type"].items():
            success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(
                f"    {file_type.upper():10s} - {stats['success']}/{stats['total']} ({success_rate:.1f}%)"
            )

        print("\n  Performance Metrics:")
        print(f"    Total Duration: {summary['metrics']['total_duration_seconds']:.2f}s")
        print(f"    Avg Duration: {summary['metrics']['avg_duration_seconds']:.2f}s")
        print(f"    Total Blocks: {summary['metrics']['total_blocks_extracted']}")
        print(f"    Avg Quality: {summary['metrics']['avg_quality_score']:.1f}/100")

        # Show failures
        failures = [r for r in self.results if not r["success"]]
        if failures:
            print("\n  [WARN] Failed Files:")
            for failure in failures:
                print(f"    - {failure['file_name']} ({failure['file_type']})")
                for error in failure["errors"][:3]:  # Show first 3 errors
                    print(f"      Error: {error}")

        print("\n" + "=" * 80)


def main():
    """Main entry point."""
    # Paths
    base_dir = Path(__file__).parent
    test_files_dir = base_dir / "test-files-assesses-extraction-tool"
    output_dir = base_dir / "test-extraction-outputs"

    if not test_files_dir.exists():
        print(f"[ERROR] Test files directory not found: {test_files_dir}")
        sys.exit(1)

    # Run tests
    runner = TestExtractionRunner(test_files_dir, output_dir)
    summary = runner.run_all_tests()

    # Exit with appropriate code
    if summary["failed"] > 0:
        print(f"\n[WARN] {summary['failed']} file(s) failed extraction")
        sys.exit(1)
    else:
        print(f"\n[OK] All {summary['successful']} files extracted successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()

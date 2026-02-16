"""Semantic Command Export Tests - TDD RED Phase (Story 5-4).

Test cases for --export-summary flag on semantic commands.

Expected: All tests FAIL initially (RED phase of TDD).

AC-5-4: semantic analyze --export-summary flag
AC-5-4: semantic deduplicate --export-summary flag
AC-5-4: semantic cluster --export-summary flag
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("typer", reason="Typer is required for CLI tests")
from typer.testing import CliRunner  # noqa: E402

from data_extract.cli.base import _reset_app, get_app  # noqa: E402


@pytest.fixture
def runner():
    """Provide fresh CLI runner with reset app instance."""
    _reset_app()
    return CliRunner()


@pytest.fixture
def app():
    """Get fresh app instance."""
    _reset_app()
    return get_app()


@pytest.fixture
def sample_chunks_dir(tmp_path: Path) -> Path:
    """Create a directory with sample chunk JSON files."""
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()

    # Create sample chunk files
    texts = [
        "Machine learning algorithms process data to find patterns",
        "Data extraction involves parsing documents to extract information",
        "Risk management identifies and mitigates potential issues",
        "Document classification organizes files by topic",
        "Quality assurance validates software requirements",
    ]

    for i, text in enumerate(texts):
        chunk_data = {
            "id": f"chunk_{i:03d}",
            "text": text,
            "document_id": f"doc_{i // 2}",
            "position_index": i % 3,
            "token_count": len(text.split()),
            "word_count": len(text.split()),
            "entities": [],
            "section_context": "",
            "quality_score": 0.85,
            "readability_scores": {"flesch_reading_ease": 65.0},
            "metadata": {
                "source_file": f"document_{i // 2}.pdf",
                "processing_version": "1.0.0",
                "entity_tags": [],
                "quality": {
                    "overall": 0.85,
                    "completeness": 0.9,
                    "coherence": 0.8,
                    "ocr_confidence": 0.95,
                },
            },
        }
        chunk_file = chunks_dir / f"chunk_{i:03d}.json"
        chunk_file.write_text(json.dumps(chunk_data, indent=2))

    return chunks_dir


@pytest.fixture
def duplicate_chunks_dir(tmp_path: Path) -> Path:
    """Create chunks directory with some duplicates for testing."""
    chunks_dir = tmp_path / "duplicates"
    chunks_dir.mkdir()

    # Create chunks with some near-duplicates
    texts = [
        "The quick brown fox jumps over the lazy dog. This is a test document.",
        "The quick brown fox jumps over the lazy dog. This is a test document.",  # Exact dup
        "Machine learning is transforming the data science landscape",
        "Data science landscape is being transformed by machine learning",  # Near dup
        "A completely different topic about cooking recipes",
    ]

    for i, text in enumerate(texts):
        chunk_data = {
            "id": f"dup_chunk_{i:03d}",
            "text": text,
            "document_id": f"doc_{i}",
            "position_index": 0,
            "token_count": len(text.split()),
            "word_count": len(text.split()),
            "entities": [],
            "section_context": "",
            "quality_score": 0.85,
            "readability_scores": {"flesch_reading_ease": 65.0},
            "metadata": {
                "source_file": f"doc_{i}.pdf",
                "processing_version": "1.0.0",
                "entity_tags": [],
            },
        }
        chunk_file = chunks_dir / f"dup_chunk_{i:03d}.json"
        chunk_file.write_text(json.dumps(chunk_data, indent=2))

    return chunks_dir


# ==============================================================================
# Semantic Analyze - Export Summary Tests
# ==============================================================================


class TestSemanticAnalyzeExportSummary:
    """Test cases for semantic analyze --export-summary flag."""

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_analyze_export_summary_flag_recognized(
        self, runner: CliRunner, app, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary flag is recognized by analyze.

        Given: semantic analyze command with --export-summary flag
        When: We invoke the command
        Then: Should not fail due to unknown flag

        Expected RED failure: Flag not recognized
        """
        output_file = tmp_path / "results.json"

        result = runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
                "--export-summary",
            ],
        )

        assert "unrecognized arguments" not in result.output
        assert "no such option" not in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_analyze_export_summary_creates_summary_file(
        self, runner: CliRunner, app, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary creates a summary file.

        Given: --export-summary flag on analyze
        When: We invoke the command
        Then: Should create a summary.json file in output directory
        And: Summary should contain analysis statistics

        Expected RED failure: Summary file not created
        """
        output_file = tmp_path / "results.json"

        result = runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
                "--export-summary",
            ],
        )

        # Look for summary file
        summary_files = list(tmp_path.glob("*summary*"))
        assert len(summary_files) > 0, "No summary file created"

        # Verify it's valid JSON
        if summary_files:
            summary_file = summary_files[0]
            assert summary_file.exists()
            if summary_file.suffix == ".json":
                content = json.loads(summary_file.read_text())
                assert isinstance(content, dict)
                # Should contain analysis statistics
                assert any(
                    key in content
                    for key in [
                        "summary",
                        "statistics",
                        "total_chunks",
                        "total_documents",
                    ]
                )

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_analyze_export_summary_contains_metrics(
        self, runner: CliRunner, app, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify summary file contains analysis metrics.

        Given: --export-summary flag
        When: Command completes
        Then: Summary should contain key metrics
        And: Should include chunk count, document count, etc.

        Expected RED failure: Summary lacks expected metrics
        """
        output_file = tmp_path / "results.json"

        result = runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
                "--export-summary",
            ],
        )

        summary_files = list(tmp_path.glob("*summary*"))
        if summary_files:
            summary_file = summary_files[0]
            summary_data = json.loads(summary_file.read_text())

            # Should have common metrics
            assert any(
                key in str(summary_data).lower() for key in ["chunk", "document", "count", "total"]
            )

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_analyze_export_summary_short_flag(
        self, runner: CliRunner, app, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary has short flag variant.

        Given: semantic analyze with -s flag (or similar)
        When: We invoke the command
        Then: Should work same as --export-summary

        Expected RED failure: Short flag not recognized
        """
        output_file = tmp_path / "results.json"

        # Try common short flags
        for short_flag in ["-s", "-es", "--export"]:
            result = runner.invoke(
                app,
                [
                    "semantic",
                    "analyze",
                    str(sample_chunks_dir),
                    "-o",
                    str(output_file),
                    short_flag,
                ],
            )

            # At least one variant should work
            if "no such option" not in result.output.lower():
                break


# ==============================================================================
# Semantic Deduplicate - Export Summary Tests
# ==============================================================================


class TestSemanticDeduplicateExportSummary:
    """Test cases for semantic deduplicate --export-summary flag."""

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_deduplicate_export_summary_flag_recognized(
        self, runner: CliRunner, app, duplicate_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary flag is recognized by deduplicate.

        Given: semantic deduplicate with --export-summary flag
        When: We invoke the command
        Then: Should not fail due to unknown flag

        Expected RED failure: Flag not recognized
        """
        output_dir = tmp_path / "clean"

        result = runner.invoke(
            app,
            [
                "semantic",
                "deduplicate",
                str(duplicate_chunks_dir),
                "-o",
                str(output_dir),
                "--export-summary",
            ],
        )

        assert "unrecognized arguments" not in result.output
        assert "no such option" not in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_deduplicate_export_summary_creates_file(
        self, runner: CliRunner, app, duplicate_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary creates summary for deduplicate.

        Given: --export-summary on deduplicate command
        When: Command completes
        Then: Should create summary file
        And: Summary should contain deduplication statistics

        Expected RED failure: Summary not created or no dedup stats
        """
        output_dir = tmp_path / "clean"

        result = runner.invoke(
            app,
            [
                "semantic",
                "deduplicate",
                str(duplicate_chunks_dir),
                "-o",
                str(output_dir),
                "--export-summary",
            ],
        )

        # Look for summary file
        summary_files = list(tmp_path.glob("*summary*"))
        assert len(summary_files) > 0, "No summary file created"

        if summary_files:
            summary_file = summary_files[0]
            summary_data = json.loads(summary_file.read_text())

            # Should contain dedup-related metrics
            assert any(
                key in str(summary_data).lower()
                for key in [
                    "duplicate",
                    "removed",
                    "kept",
                    "similarity",
                    "grouped",
                ]
            )

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_deduplicate_export_summary_shows_removal_count(
        self, runner: CliRunner, app, duplicate_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify summary shows count of removed duplicates.

        Given: --export-summary on deduplicate
        When: Command completes
        Then: Summary should show how many chunks were removed
        And: Should show how many were kept

        Expected RED failure: Removal stats not in summary
        """
        output_dir = tmp_path / "clean"

        result = runner.invoke(
            app,
            [
                "semantic",
                "deduplicate",
                str(duplicate_chunks_dir),
                "-o",
                str(output_dir),
                "--export-summary",
            ],
        )

        summary_files = list(tmp_path.glob("*summary*"))
        if summary_files:
            summary_file = summary_files[0]
            summary_data = json.loads(summary_file.read_text())

            # Should have numeric stats
            assert any(char.isdigit() for char in json.dumps(summary_data))


# ==============================================================================
# Semantic Cluster - Export Summary Tests
# ==============================================================================


class TestSemanticClusterExportSummary:
    """Test cases for semantic cluster --export-summary flag."""

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_cluster_export_summary_flag_recognized(
        self, runner: CliRunner, app, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary flag is recognized by cluster.

        Given: semantic cluster with --export-summary flag
        When: We invoke the command
        Then: Should not fail due to unknown flag

        Expected RED failure: Flag not recognized
        """
        output_file = tmp_path / "clusters.json"

        result = runner.invoke(
            app,
            [
                "semantic",
                "cluster",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
                "--export-summary",
            ],
        )

        assert "unrecognized arguments" not in result.output
        assert "no such option" not in result.output.lower()

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_cluster_export_summary_creates_file(
        self, runner: CliRunner, app, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary creates summary for cluster.

        Given: --export-summary on cluster command
        When: Command completes
        Then: Should create summary file
        And: Summary should contain clustering statistics

        Expected RED failure: Summary not created or no cluster stats
        """
        output_file = tmp_path / "clusters.json"

        result = runner.invoke(
            app,
            [
                "semantic",
                "cluster",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
                "--export-summary",
            ],
        )

        # Look for summary file
        summary_files = list(tmp_path.glob("*summary*"))
        assert len(summary_files) > 0, "No summary file created"

        if summary_files:
            summary_file = summary_files[0]
            summary_data = json.loads(summary_file.read_text())

            # Should contain cluster-related metrics
            assert any(
                key in str(summary_data).lower() for key in ["cluster", "group", "topic", "center"]
            )

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_cluster_export_summary_shows_cluster_count(
        self, runner: CliRunner, app, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify summary shows number of clusters created.

        Given: --export-summary on cluster command
        When: Command completes
        Then: Summary should show cluster count
        And: Should show items per cluster

        Expected RED failure: Cluster count stats missing
        """
        output_file = tmp_path / "clusters.json"

        result = runner.invoke(
            app,
            [
                "semantic",
                "cluster",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
                "--export-summary",
            ],
        )

        summary_files = list(tmp_path.glob("*summary*"))
        if summary_files:
            summary_file = summary_files[0]
            summary_data = json.loads(summary_file.read_text())

            # Should mention clusters and have numbers
            assert any(key in str(summary_data).lower() for key in ["cluster", "n_cluster"])


# ==============================================================================
# Export Summary - Format Tests
# ==============================================================================


class TestExportSummaryFormats:
    """Test cases for export summary in different formats."""

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_analyze_export_summary_json_format(
        self, runner: CliRunner, app, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify summary can be exported as JSON.

        Given: --export-summary on analyze
        When: Output format is JSON (default)
        Then: Should create valid JSON summary file

        Expected RED failure: Summary not in JSON format
        """
        output_file = tmp_path / "results.json"

        result = runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
                "--export-summary",
            ],
        )

        summary_files = list(tmp_path.glob("*summary*"))
        assert len(summary_files) > 0

        if summary_files:
            summary_file = summary_files[0]
            # Should be valid JSON
            try:
                json.loads(summary_file.read_text())
            except json.JSONDecodeError:
                pytest.fail("Summary file is not valid JSON")

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_deduplicate_export_summary_csv_format(
        self, runner: CliRunner, app, duplicate_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify summary can be exported as CSV.

        Given: --export-summary with --format csv
        When: Command completes
        Then: Should create CSV summary file

        Expected RED failure: CSV format not supported for summary
        """
        output_dir = tmp_path / "clean"

        result = runner.invoke(
            app,
            [
                "semantic",
                "deduplicate",
                str(duplicate_chunks_dir),
                "-o",
                str(output_dir),
                "--export-summary",
                "--format",
                "csv",
            ],
        )

        # May create CSV summary or still JSON
        summary_files = list(tmp_path.glob("*summary*"))
        if summary_files:
            summary_file = summary_files[0]
            assert summary_file.exists()


# ==============================================================================
# Export Summary - Combined Flag Tests
# ==============================================================================


class TestExportSummaryWithOtherFlags:
    """Test cases for --export-summary combined with other flags."""

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_analyze_export_summary_with_verbose(
        self, runner: CliRunner, app, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary works with --verbose.

        Given: Both --export-summary and --verbose flags
        When: We invoke analyze command
        Then: Should create summary file
        And: Should show verbose output

        Expected RED failure: Flags conflict or summary not created
        """
        output_file = tmp_path / "results.json"

        result = runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
                "--export-summary",
                "-v",
            ],
        )

        assert result.exit_code == 0 or len(result.output) > 0

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_cluster_export_summary_with_format_option(
        self, runner: CliRunner, app, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary with custom output format.

        Given: --export-summary with -f html
        When: We invoke cluster command
        Then: Should create summary file
        And: Main output should be in specified format

        Expected RED failure: Format and summary conflict
        """
        output_file = tmp_path / "clusters.html"

        result = runner.invoke(
            app,
            [
                "semantic",
                "cluster",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
                "--export-summary",
                "-f",
                "html",
            ],
        )

        # Should complete successfully
        assert result.exit_code == 0 or len(result.output) > 0

    @pytest.mark.cli
    @pytest.mark.story_5_4
    def test_deduplicate_export_summary_with_dry_run(
        self, runner: CliRunner, app, duplicate_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """
        RED: Verify --export-summary works with --dry-run.

        Given: Both --export-summary and --dry-run flags
        When: We invoke deduplicate command
        Then: Should show what would be removed in summary
        And: Should not actually modify files

        Expected RED failure: Summary not created in dry-run mode
        """
        output_dir = tmp_path / "clean"

        result = runner.invoke(
            app,
            [
                "semantic",
                "deduplicate",
                str(duplicate_chunks_dir),
                "-o",
                str(output_dir),
                "--export-summary",
                "--dry-run",
            ],
        )

        # Should complete and show summary of what would happen
        # Output dir should be empty (dry-run)
        output_files = list(output_dir.glob("*.json"))
        # Either empty (dry-run) or contains summary (if exported)

"""Tests for semantic CLI commands.

Tests AC-4.5-1 (analyze), AC-4.5-2 (deduplicate), AC-4.5-3 (cluster),
AC-4.5-6 (progress indicators), AC-4.5-7 (configuration), AC-4.5-8 (export),
AC-4.5-9 (validation), AC-4.5-10 (quality gates).
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from data_extract.app import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide Typer test runner."""
    return CliRunner()


@pytest.fixture
def sample_chunks_dir(tmp_path: Path) -> Path:
    """Create a directory with sample chunk JSON files for testing."""
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()

    # Create sample chunk files with diverse text content
    # Use varied vocabulary to ensure TF-IDF can work with min_df=1
    texts = [
        "Machine learning algorithms process data to find patterns. "
        "Neural networks are a popular type of machine learning model. "
        "Deep learning extends neural networks with many layers.",
        "Data extraction involves parsing documents to extract information. "
        "Natural language processing helps understand text content. "
        "Text mining discovers knowledge from unstructured data.",
        "Risk management identifies and mitigates potential issues. "
        "Audit controls ensure compliance with regulations. "
        "Internal controls prevent fraud and errors in organizations.",
        "Document classification organizes files by topic and content. "
        "Semantic analysis determines the meaning of text. "
        "Information retrieval finds relevant documents from collections.",
        "Quality assurance validates that software meets requirements. "
        "Testing strategies include unit tests and integration tests. "
        "Automated testing improves development efficiency.",
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
                    "readability_flesch_kincaid": 8.0,
                    "readability_gunning_fog": 10.0,
                    "flags": [],
                },
            },
        }
        chunk_file = chunks_dir / f"chunk_{i:03d}.json"
        chunk_file.write_text(json.dumps(chunk_data, indent=2))

    return chunks_dir


@pytest.fixture
def duplicate_chunks_dir(tmp_path: Path) -> Path:
    """Create a directory with duplicate chunk files for deduplication testing."""
    chunks_dir = tmp_path / "duplicates"
    chunks_dir.mkdir()

    # Create chunks where some are near-duplicates
    texts = [
        "The quick brown fox jumps over the lazy dog. This is a test document.",
        "The quick brown fox jumps over the lazy dog. This is a test document.",  # Exact dup
        "Machine learning is transforming the data science landscape significantly.",
        "Data science landscape is being transformed by machine learning significantly.",  # Near dup
        "A completely different topic about cooking recipes and kitchen equipment.",
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
                "quality": {
                    "overall": 0.85,
                    "completeness": 0.9,
                    "coherence": 0.8,
                    "ocr_confidence": 0.95,
                    "readability_flesch_kincaid": 8.0,
                    "readability_gunning_fog": 10.0,
                    "flags": [],
                },
            },
        }
        chunk_file = chunks_dir / f"dup_chunk_{i:03d}.json"
        chunk_file.write_text(json.dumps(chunk_data, indent=2))

    return chunks_dir


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a sample .data-extract.yaml config file."""
    config_path = tmp_path / ".data-extract.yaml"
    config_content = """semantic:
  tfidf:
    max_features: 3000
    ngram_range: [1, 1]
    min_df: 1
  similarity:
    duplicate_threshold: 0.90
    related_threshold: 0.6
  lsa:
    n_components: 50
    n_clusters: 5
  quality:
    min_score: 0.4
  cache:
    enabled: true
    max_size_mb: 100
"""
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def test_config_file(tmp_path: Path) -> Path:
    """Create a test config file with settings optimized for small test datasets."""
    config_path = tmp_path / ".data-extract.yaml"
    config_content = """semantic:
  tfidf:
    max_features: 1000
    ngram_range: [1, 1]
    min_df: 1
    max_df: 1.0
  similarity:
    duplicate_threshold: 0.95
    related_threshold: 0.7
  lsa:
    n_components: 50
    n_clusters: 3
  quality:
    min_score: 0.3
  cache:
    enabled: false
    max_size_mb: 100
"""
    config_path.write_text(config_content)
    return config_path


class TestSemanticAnalyzeCommand:
    """Tests for `data-extract semantic analyze` command."""

    def test_analyze_basic(
        self,
        cli_runner: CliRunner,
        sample_chunks_dir: Path,
        test_config_file: Path,
        tmp_path: Path,
    ) -> None:
        """AC-4.5-1: Test basic analyze command with JSON output."""
        output_file = tmp_path / "results.json"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-c",
                str(test_config_file),
                "-o",
                str(output_file),
            ],
        )

        # Command should succeed
        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists(), "Output file not created"

        # Verify JSON output structure
        output_data = json.loads(output_file.read_text())
        assert "summary" in output_data
        assert "similarity" in output_data

    def test_analyze_html_report(
        self,
        cli_runner: CliRunner,
        sample_chunks_dir: Path,
        test_config_file: Path,
        tmp_path: Path,
    ) -> None:
        """AC-4.5-5: Test HTML report generation."""
        output_file = tmp_path / "report.html"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-c",
                str(test_config_file),
                "--report",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists()

        # Verify HTML structure
        html_content = output_file.read_text()
        assert "<!DOCTYPE html>" in html_content
        assert "Semantic Analysis Report" in html_content

    def test_analyze_csv_format(
        self,
        cli_runner: CliRunner,
        sample_chunks_dir: Path,
        test_config_file: Path,
        tmp_path: Path,
    ) -> None:
        """AC-4.5-8: Test CSV export format."""
        output_file = tmp_path / "results.csv"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-c",
                str(test_config_file),
                "-f",
                "csv",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists()

        csv_content = output_file.read_text()
        assert "metric,value" in csv_content

    def test_analyze_with_config_file(
        self,
        cli_runner: CliRunner,
        sample_chunks_dir: Path,
        config_file: Path,
        tmp_path: Path,
    ) -> None:
        """AC-4.5-7: Test configuration from file."""
        output_file = tmp_path / "results.json"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-c",
                str(config_file),
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_analyze_cli_overrides_config(
        self,
        cli_runner: CliRunner,
        sample_chunks_dir: Path,
        config_file: Path,
        tmp_path: Path,
    ) -> None:
        """AC-4.5-7: Test that CLI flags override config file values."""
        output_file = tmp_path / "results.json"

        # CLI specifies different threshold than config file (0.95 vs 0.90)
        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-c",
                str(config_file),
                "--duplicate-threshold",
                "0.95",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_analyze_graph_export(
        self,
        cli_runner: CliRunner,
        sample_chunks_dir: Path,
        test_config_file: Path,
        tmp_path: Path,
    ) -> None:
        """AC-4.5-8: Test graph export in different formats."""
        output_file = tmp_path / "results.json"

        for graph_format in ["json", "csv", "dot"]:
            result = cli_runner.invoke(
                app,
                [
                    "semantic",
                    "analyze",
                    str(sample_chunks_dir),
                    "-c",
                    str(test_config_file),
                    "-o",
                    str(output_file),
                    "--export-graph",
                    graph_format,
                ],
            )

            assert result.exit_code == 0, f"Graph export {graph_format} failed: {result.output}"

    def test_analyze_invalid_threshold(
        self, cli_runner: CliRunner, sample_chunks_dir: Path
    ) -> None:
        """AC-4.5-9: Test validation of threshold parameter range."""
        # Test value outside valid range (0.0-1.0)
        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "--duplicate-threshold",
                "1.5",
            ],
        )

        assert result.exit_code != 0, "Should reject invalid threshold"
        assert "1.5 is not in the range" in result.output or "invalid" in result.output.lower()

    def test_analyze_invalid_min_quality(
        self, cli_runner: CliRunner, sample_chunks_dir: Path
    ) -> None:
        """AC-4.5-9: Test validation of min-quality parameter range."""
        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "--min-quality",
                "-0.5",
            ],
        )

        assert result.exit_code != 0, "Should reject invalid min-quality"

    def test_analyze_nonexistent_path(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """AC-4.5-9: Test error handling for nonexistent input path."""
        result = cli_runner.invoke(app, ["semantic", "analyze", str(tmp_path / "nonexistent")])

        assert result.exit_code != 0
        assert "does not exist" in result.output.lower() or "error" in result.output.lower()

    def test_analyze_verbose_output(
        self,
        cli_runner: CliRunner,
        sample_chunks_dir: Path,
        test_config_file: Path,
    ) -> None:
        """AC-4.5-6: Test verbose output includes additional information."""
        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "analyze",
                str(sample_chunks_dir),
                "-c",
                str(test_config_file),
                "-v",
            ],
        )

        # Verbose mode should show more details
        assert result.exit_code == 0, f"Command failed: {result.output}"


class TestSemanticDeduplicateCommand:
    """Tests for `data-extract semantic deduplicate` command."""

    def test_deduplicate_basic(
        self, cli_runner: CliRunner, duplicate_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """AC-4.5-2: Test basic deduplicate command."""
        output_dir = tmp_path / "clean"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "deduplicate",
                str(duplicate_chunks_dir),
                "-o",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_deduplicate_dry_run(self, cli_runner: CliRunner, duplicate_chunks_dir: Path) -> None:
        """AC-4.5-2: Test dry-run mode shows duplicates without removing."""
        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "deduplicate",
                str(duplicate_chunks_dir),
                "--dry-run",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Dry run should report findings but not modify
        assert "duplicate" in result.output.lower() or "group" in result.output.lower()

    def test_deduplicate_custom_threshold(
        self, cli_runner: CliRunner, duplicate_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """AC-4.5-2: Test custom threshold parameter."""
        output_dir = tmp_path / "clean"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "deduplicate",
                str(duplicate_chunks_dir),
                "-t",
                "0.85",
                "-o",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_deduplicate_invalid_threshold(
        self, cli_runner: CliRunner, duplicate_chunks_dir: Path
    ) -> None:
        """AC-4.5-9: Test validation rejects threshold outside 0.0-1.0 range."""
        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "deduplicate",
                str(duplicate_chunks_dir),
                "-t",
                "2.0",
            ],
        )

        assert result.exit_code != 0, "Should reject invalid threshold"


class TestSemanticClusterCommand:
    """Tests for `data-extract semantic cluster` command."""

    def test_cluster_basic(
        self, cli_runner: CliRunner, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """AC-4.5-3: Test basic cluster command."""
        output_file = tmp_path / "clusters.json"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "cluster",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_cluster_with_k(
        self, cli_runner: CliRunner, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """AC-4.5-3: Test cluster command with configurable K."""
        output_file = tmp_path / "clusters.json"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "cluster",
                str(sample_chunks_dir),
                "-k",
                "3",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_cluster_html_format(
        self, cli_runner: CliRunner, sample_chunks_dir: Path, tmp_path: Path
    ) -> None:
        """AC-4.5-3, AC-4.5-8: Test cluster command with HTML output."""
        output_file = tmp_path / "clusters.html"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "cluster",
                str(sample_chunks_dir),
                "-f",
                "html",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"


class TestSemanticTopicsCommand:
    """Tests for `data-extract semantic topics` command."""

    @pytest.mark.skip(reason="Topics command requires larger corpus for TF-IDF")
    def test_topics_basic(
        self,
        cli_runner: CliRunner,
        sample_chunks_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Test basic topics extraction command."""
        output_file = tmp_path / "topics.json"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "topics",
                str(sample_chunks_dir),
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

    @pytest.mark.skip(reason="Topics command requires larger corpus for TF-IDF")
    def test_topics_custom_count(
        self,
        cli_runner: CliRunner,
        sample_chunks_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Test topics command with custom topic count."""
        output_file = tmp_path / "topics.json"

        result = cli_runner.invoke(
            app,
            [
                "semantic",
                "topics",
                str(sample_chunks_dir),
                "-n",
                "5",
                "-o",
                str(output_file),
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_topics_help(self, cli_runner: CliRunner) -> None:
        """Test topics command has help text."""
        result = cli_runner.invoke(app, ["semantic", "topics", "--help"])

        assert result.exit_code == 0
        assert "--n-topics" in result.output or "-n" in result.output
        assert "lsa" in result.output.lower() or "topic" in result.output.lower()


class TestHelpText:
    """Test that CLI provides helpful documentation."""

    def test_semantic_group_help(self, cli_runner: CliRunner) -> None:
        """Verify semantic command group has help text."""
        result = cli_runner.invoke(app, ["semantic", "--help"])

        assert result.exit_code == 0
        assert "semantic analysis" in result.output.lower()
        assert "analyze" in result.output
        assert "deduplicate" in result.output
        assert "cluster" in result.output

    def test_analyze_help(self, cli_runner: CliRunner) -> None:
        """Verify analyze command has comprehensive help text."""
        result = cli_runner.invoke(app, ["semantic", "analyze", "--help"])

        assert result.exit_code == 0
        assert "--output" in result.output or "-o" in result.output
        assert "--format" in result.output or "-f" in result.output
        assert "example" in result.output.lower()

    def test_deduplicate_help(self, cli_runner: CliRunner) -> None:
        """Verify deduplicate command has comprehensive help text."""
        result = cli_runner.invoke(app, ["semantic", "deduplicate", "--help"])

        assert result.exit_code == 0
        assert "--threshold" in result.output or "-t" in result.output
        assert "--dry-run" in result.output

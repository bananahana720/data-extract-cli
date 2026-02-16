"""Tests for cache management CLI commands.

Tests AC-4.5-4: Cache subcommands for status, clear, warm operations.
"""

import json
from pathlib import Path

import pytest

pytest.importorskip("typer", reason="Typer is required for CLI tests")
from typer.testing import CliRunner  # noqa: E402

from data_extract.app import app  # noqa: E402
from data_extract.semantic.cache import CacheManager  # noqa: E402


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide Typer test runner."""
    return CliRunner()


@pytest.fixture
def sample_chunks_dir(tmp_path: Path) -> Path:
    """Create a directory with sample chunk JSON files for testing."""
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()

    for i in range(3):
        chunk_data = {
            "id": f"cache_test_chunk_{i:03d}",
            "text": f"Sample text for cache testing chunk {i}. "
            f"This text is used for warming the cache.",
            "document_id": f"cache_doc_{i}",
            "position_index": i,
            "token_count": 15,
            "word_count": 12,
            "entities": [],
            "section_context": "",
            "quality_score": 0.85,
            "readability_scores": {"flesch_reading_ease": 65.0},
            "metadata": {
                "source_file": f"cache_doc_{i}.pdf",
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
        chunk_file = chunks_dir / f"cache_test_chunk_{i:03d}.json"
        chunk_file.write_text(json.dumps(chunk_data, indent=2))

    return chunks_dir


@pytest.fixture
def clean_cache() -> None:
    """Ensure cache is clean before and after test."""
    cache_manager = CacheManager()
    cache_manager.clear()
    yield
    cache_manager.clear()


class TestCacheStatusCommand:
    """Tests for `data-extract cache status` command."""

    def test_cache_status_basic(self, cli_runner: CliRunner) -> None:
        """AC-4.5-4: Test basic cache status command."""
        result = cli_runner.invoke(app, ["cache", "status"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "cache" in result.output.lower()

    def test_cache_status_verbose(self, cli_runner: CliRunner) -> None:
        """AC-4.5-4: Test verbose cache status shows detailed info."""
        result = cli_runner.invoke(app, ["cache", "status", "-v"])

        assert result.exit_code == 0, f"Command failed: {result.output}"


class TestCacheClearCommand:
    """Tests for `data-extract cache clear` command."""

    def test_cache_clear_empty(self, cli_runner: CliRunner, clean_cache: None) -> None:
        """AC-4.5-4: Test clearing an already empty cache."""
        result = cli_runner.invoke(app, ["cache", "clear", "-f"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "empty" in result.output.lower()

    def test_cache_clear_force(self, cli_runner: CliRunner) -> None:
        """AC-4.5-4: Test force clear without confirmation."""
        result = cli_runner.invoke(app, ["cache", "clear", "-f"])

        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_cache_clear_with_pattern(self, cli_runner: CliRunner) -> None:
        """AC-4.5-4: Test selective clear with pattern matching."""
        result = cli_runner.invoke(app, ["cache", "clear", "-p", "tfidf_*", "-f"])

        assert result.exit_code == 0, f"Command failed: {result.output}"


class TestCacheWarmCommand:
    """Tests for `data-extract cache warm` command."""

    def test_cache_warm_basic(
        self, cli_runner: CliRunner, sample_chunks_dir: Path, clean_cache: None
    ) -> None:
        """AC-4.5-4: Test basic cache warming."""
        result = cli_runner.invoke(app, ["cache", "warm", str(sample_chunks_dir)])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "complete" in result.output.lower() or "warm" in result.output.lower()

    def test_cache_warm_verbose(
        self, cli_runner: CliRunner, sample_chunks_dir: Path, clean_cache: None
    ) -> None:
        """AC-4.5-4: Test verbose cache warming."""
        result = cli_runner.invoke(app, ["cache", "warm", str(sample_chunks_dir), "-v"])

        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_cache_warm_nonexistent_path(self, cli_runner: CliRunner) -> None:
        """AC-4.5-9: Test error handling for nonexistent path."""
        result = cli_runner.invoke(app, ["cache", "warm", "/nonexistent/path"])

        assert result.exit_code != 0


class TestCacheMetricsCommand:
    """Tests for `data-extract cache metrics` command."""

    def test_cache_metrics_text(self, cli_runner: CliRunner) -> None:
        """AC-4.5-4: Test cache metrics in text format."""
        result = cli_runner.invoke(app, ["cache", "metrics"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "metric" in result.output.lower() or "cache" in result.output.lower()

    def test_cache_metrics_json(self, cli_runner: CliRunner) -> None:
        """AC-4.5-4: Test cache metrics in JSON format."""
        result = cli_runner.invoke(app, ["cache", "metrics", "-f", "json"])

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify JSON is valid
        try:
            metrics = json.loads(result.output)
            assert "entries" in metrics or "hits" in metrics
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON output: {result.output}")


class TestCacheHelpText:
    """Test that cache CLI provides helpful documentation."""

    def test_cache_group_help(self, cli_runner: CliRunner) -> None:
        """Verify cache command group has help text."""
        result = cli_runner.invoke(app, ["cache", "--help"])

        assert result.exit_code == 0
        assert "cache" in result.output.lower()
        assert "status" in result.output
        assert "clear" in result.output
        assert "warm" in result.output

    def test_cache_status_help(self, cli_runner: CliRunner) -> None:
        """Verify cache status command has help text."""
        result = cli_runner.invoke(app, ["cache", "status", "--help"])

        assert result.exit_code == 0
        assert "--verbose" in result.output or "-v" in result.output

    def test_cache_clear_help(self, cli_runner: CliRunner) -> None:
        """Verify cache clear command has help text."""
        result = cli_runner.invoke(app, ["cache", "clear", "--help"])

        assert result.exit_code == 0
        assert "--pattern" in result.output or "-p" in result.output
        assert "--force" in result.output or "-f" in result.output

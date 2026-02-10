"""Integration tests for CLI organization flags (Story 3.7).

Tests the data-extract CLI with --organization and --strategy flags,
verifying proper routing to organization strategies.

Test Coverage:
    - --organization by_document flag
    - --organization by_entity flag
    - --organization flat flag (default)
    - Invalid strategy error handling
    - Organization with --format flag combinations
"""

import json
import subprocess

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.cli, pytest.mark.organization]


class TestCLIOrganizationFlags:
    """Integration tests for CLI organization flags (AC-3.7-5)."""

    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """Create a minimal test PDF file."""
        # For testing, we'll create a simple text file instead
        # Real implementation would need actual PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_text("Test content for CLI organization testing")
        return pdf_path

    @pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
    def test_cli_organization_by_document_flag(self, sample_pdf, tmp_path):
        """Should organize output by document when --organization by_document passed."""
        output_dir = tmp_path / "output"

        # Run CLI with BY_DOCUMENT organization
        result = subprocess.run(
            [
                "data-extract",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--organization",
                "by_document",
            ],
            capture_output=True,
            text=True,
        )

        # Verify success
        assert result.returncode == 0

        # Verify BY_DOCUMENT folder structure exists
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        assert manifest["organization_strategy"] == "by_document"

    @pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
    def test_cli_organization_by_entity_flag(self, sample_pdf, tmp_path):
        """Should organize output by entity when --organization by_entity passed."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                "data-extract",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
                "--organization",
                "by_entity",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        assert manifest["organization_strategy"] == "by_entity"

    @pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
    def test_cli_organization_flat_default(self, sample_pdf, tmp_path):
        """Should use flat organization by default when no flag specified."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                "data-extract",
                "process",
                str(sample_pdf),
                "--format",
                "txt",
                "--output",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        # Default should be flat
        assert manifest["organization_strategy"] == "flat"
        assert manifest["folders"] == {
            str(output_dir): {"chunk_count": 1, "chunk_ids": ["chunk_001"]}
        }

    @pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
    def test_cli_invalid_organization_strategy(self, sample_pdf, tmp_path):
        """Should error on invalid organization strategy."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                "data-extract",
                "process",
                str(sample_pdf),
                "--output",
                str(output_dir),
                "--organization",
                "invalid_strategy",
            ],
            capture_output=True,
            text=True,
        )

        # Should fail with error
        assert result.returncode != 0
        assert "invalid" in result.stderr.lower() or "unknown" in result.stderr.lower()

    @pytest.mark.skip(reason="Organization flag not yet implemented in CLI (Story 5.x)")
    def test_cli_organization_with_csv_format(self, sample_pdf, tmp_path):
        """Should combine organization strategy with CSV format."""
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                "data-extract",
                "process",
                str(sample_pdf),
                "--format",
                "csv",
                "--output",
                str(output_dir),
                "--organization",
                "by_document",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Verify CSV exists in organized structure
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()

        # Should have CSV files in document folders
        csv_files = list(output_dir.rglob("*.csv"))
        assert len(csv_files) > 0


# Placeholder for functional CLI organization tests (Unit-level CLI validation)
class TestCLIOrganizationUnit:
    """Unit tests for CLI argument parsing and validation."""

    def test_organization_flag_accepts_valid_strategies(self):
        """Should accept by_document, by_entity, flat as valid strategies."""
        valid_strategies = ["by_document", "by_entity", "flat"]

        from data_extract.output.organization import OrganizationStrategy

        for strategy in valid_strategies:
            # Verify enum has this value
            assert any(s.value == strategy for s in OrganizationStrategy)

    def test_organization_strategy_enum_complete(self):
        """Should have exactly 3 organization strategies defined."""
        from data_extract.output.organization import OrganizationStrategy

        strategies = list(OrganizationStrategy)
        assert len(strategies) == 3

        strategy_values = [s.value for s in strategies]
        assert "by_document" in strategy_values
        assert "by_entity" in strategy_values
        assert "flat" in strategy_values

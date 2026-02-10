"""TDD RED Phase Tests: Pydantic Configuration Model Structure (AC-5.2-4).

These tests verify nested configuration structure and composition.
Domain: Nested configuration structure and composition.

All tests are designed to FAIL initially (TDD RED phase).
"""

import pytest

# P0: Critical path - always run
pytestmark = [
    pytest.mark.P0,
    pytest.mark.story_5_2,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_2
class TestSemanticConfigModel:
    """AC-5.2-4: Test SemanticConfig Pydantic model validation."""

    def test_semantic_config_has_tfidf_nested_config(self):
        """
        RED: Verify SemanticConfig has nested tfidf config.

        Given: A SemanticConfig model
        When: We create it with default values
        Then: It should have tfidf as nested TfidfConfig

        Expected RED failure: No nested tfidf attribute
        """
        try:
            from data_extract.cli.models import SemanticConfig, TfidfConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = SemanticConfig()
        assert hasattr(config, "tfidf"), "SemanticConfig should have 'tfidf' attribute"
        assert isinstance(
            config.tfidf, TfidfConfig
        ), f"tfidf should be TfidfConfig, got {type(config.tfidf)}"

    def test_semantic_config_has_similarity_nested_config(self):
        """
        RED: Verify SemanticConfig has nested similarity config.

        Given: A SemanticConfig model
        When: We create it with default values
        Then: It should have similarity as nested SimilarityConfig

        Expected RED failure: No nested similarity attribute
        """
        try:
            from data_extract.cli.models import SemanticConfig, SimilarityConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = SemanticConfig()
        assert hasattr(config, "similarity"), "SemanticConfig should have 'similarity' attribute"
        assert isinstance(
            config.similarity, SimilarityConfig
        ), f"similarity should be SimilarityConfig, got {type(config.similarity)}"

    def test_semantic_config_has_lsa_nested_config(self):
        """
        RED: Verify SemanticConfig has nested lsa config.

        Given: A SemanticConfig model
        When: We create it with default values
        Then: It should have lsa as nested LsaConfig

        Expected RED failure: No nested lsa attribute
        """
        try:
            from data_extract.cli.models import LsaConfig, SemanticConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = SemanticConfig()
        assert hasattr(config, "lsa"), "SemanticConfig should have 'lsa' attribute"
        assert isinstance(config.lsa, LsaConfig), f"lsa should be LsaConfig, got {type(config.lsa)}"

    def test_semantic_config_nested_validation_propagates(self):
        """
        RED: Verify validation errors in nested config propagate correctly.

        Given: A SemanticConfig model
        When: We create it with invalid nested tfidf.max_features
        Then: ValidationError should be raised with field path

        Expected RED failure: Nested validation not working
        """
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import SemanticConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        with pytest.raises(ValidationError) as exc_info:
            SemanticConfig(tfidf={"max_features": -100})

        error_str = str(exc_info.value)
        # Should include the nested path
        assert (
            "tfidf" in error_str.lower() or "max_features" in error_str.lower()
        ), f"Error should mention nested field path: {error_str}"


@pytest.mark.unit
@pytest.mark.story_5_2
class TestExportConfigModel:
    """AC-5.2-4: Test ExportConfig Pydantic model validation."""

    def test_export_config_exists(self):
        """
        RED: Verify ExportConfig Pydantic model exists.

        Given: The models module
        When: We import ExportConfig
        Then: It should be a Pydantic BaseModel

        Expected RED failure: ImportError
        """
        try:
            from pydantic import BaseModel

            from data_extract.cli.models import ExportConfig
        except ImportError as e:
            pytest.fail(f"Cannot import ExportConfig: {e}")

        assert issubclass(ExportConfig, BaseModel), "ExportConfig must be a Pydantic BaseModel"

    def test_export_config_format_validation(self):
        """
        RED: Verify ExportConfig validates format field.

        Given: An ExportConfig model
        When: We create it with invalid format
        Then: ValidationError should be raised

        Expected RED failure: Invalid format accepted
        """
        try:
            from pydantic import ValidationError

            from data_extract.cli.models import ExportConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Should accept valid formats
        valid_config = ExportConfig(format="json")
        assert valid_config.format == "json"

        # Should reject invalid formats
        with pytest.raises(ValidationError) as exc_info:
            ExportConfig(format="invalid_format_xyz")

        assert (
            "format" in str(exc_info.value).lower()
        ), f"Error should mention format field: {exc_info.value}"

    def test_export_config_has_output_path(self):
        """
        RED: Verify ExportConfig has output_path field.

        Given: An ExportConfig model
        When: We create it
        Then: It should have output_path field (optional)

        Expected RED failure: No output_path field
        """
        try:
            from pathlib import Path

            from data_extract.cli.models import ExportConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        # Should work without output_path
        config = ExportConfig()
        assert hasattr(config, "output_path"), "ExportConfig should have output_path"

        # Should accept Path
        config_with_path = ExportConfig(output_path=Path("/tmp/output"))
        assert config_with_path.output_path is not None

    def test_export_config_default_values(self):
        """
        RED: Verify ExportConfig has sensible defaults.

        Given: An ExportConfig model
        When: We create it without arguments
        Then: It should have default values

        Expected RED failure: Missing defaults
        """
        try:
            from data_extract.cli.models import ExportConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = ExportConfig()
        assert config.format is not None, "format should have default"
        assert hasattr(config, "pretty_print"), "Should have pretty_print field"

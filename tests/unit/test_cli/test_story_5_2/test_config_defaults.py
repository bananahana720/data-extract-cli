"""TDD RED Phase Tests: Pydantic Configuration Model Defaults (AC-5.2-4).

These tests verify default value verification for all config models.
Domain: Default value verification for all config models.

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
class TestConfigModelDefaultValues:
    """AC-5.2-4: Test configuration models have sensible default values."""

    def test_tfidf_config_default_max_features(self):
        """
        RED: Verify TfidfConfig has default max_features = 5000.

        Given: A TfidfConfig model
        When: We create it without arguments
        Then: max_features should default to 5000

        Expected RED failure: Wrong default value
        """
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = TfidfConfig()
        assert config.max_features == 5000, (
            f"TfidfConfig default max_features should match specification. "
            f"Expected: 5000, got: {config.max_features}"
        )

    def test_tfidf_config_default_ngram_range(self):
        """
        RED: Verify TfidfConfig has default ngram_range = (1, 2).

        Given: A TfidfConfig model
        When: We create it without arguments
        Then: ngram_range should default to (1, 2)

        Expected RED failure: Wrong default value
        """
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = TfidfConfig()
        assert config.ngram_range == (1, 2), (
            f"TfidfConfig default ngram_range should support unigrams and bigrams. "
            f"Expected: (1, 2), got: {config.ngram_range}"
        )

    def test_tfidf_config_default_min_df(self):
        """
        RED: Verify TfidfConfig has default min_df = 2.

        Given: A TfidfConfig model
        When: We create it without arguments
        Then: min_df should default to 2

        Expected RED failure: Wrong default value
        """
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = TfidfConfig()
        assert config.min_df == 2, (
            f"TfidfConfig default min_df should filter rare terms. "
            f"Expected: 2, got: {config.min_df}"
        )

    def test_tfidf_config_default_max_df(self):
        """
        RED: Verify TfidfConfig has default max_df = 0.95.

        Given: A TfidfConfig model
        When: We create it without arguments
        Then: max_df should default to 0.95

        Expected RED failure: Wrong default value
        """
        try:
            from data_extract.cli.models import TfidfConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = TfidfConfig()
        assert config.max_df == 0.95, (
            f"TfidfConfig default max_df should filter common terms. "
            f"Expected: 0.95, got: {config.max_df}"
        )

    def test_similarity_config_default_duplicate_threshold(self):
        """
        RED: Verify SimilarityConfig has default duplicate_threshold = 0.95.

        Given: A SimilarityConfig model
        When: We create it without arguments
        Then: duplicate_threshold should default to 0.95

        Expected RED failure: Wrong default value
        """
        try:
            from data_extract.cli.models import SimilarityConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = SimilarityConfig()
        assert config.duplicate_threshold == 0.95, (
            f"SimilarityConfig default duplicate_threshold should be strict. "
            f"Expected: 0.95, got: {config.duplicate_threshold}"
        )

    def test_similarity_config_default_related_threshold(self):
        """
        RED: Verify SimilarityConfig has default related_threshold = 0.7.

        Given: A SimilarityConfig model
        When: We create it without arguments
        Then: related_threshold should default to 0.7

        Expected RED failure: Wrong default value
        """
        try:
            from data_extract.cli.models import SimilarityConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = SimilarityConfig()
        assert config.related_threshold == 0.7, (
            f"SimilarityConfig default related_threshold should be moderate. "
            f"Expected: 0.7, got: {config.related_threshold}"
        )

    def test_lsa_config_default_n_components(self):
        """
        RED: Verify LsaConfig has default n_components = 100.

        Given: A LsaConfig model
        When: We create it without arguments
        Then: n_components should default to 100

        Expected RED failure: Wrong default value
        """
        try:
            from data_extract.cli.models import LsaConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = LsaConfig()
        assert config.n_components == 100, (
            f"LsaConfig default n_components should balance dimensionality. "
            f"Expected: 100, got: {config.n_components}"
        )

    def test_cache_config_default_enabled(self):
        """
        RED: Verify CacheConfig has default enabled = True.

        Given: A CacheConfig model
        When: We create it without arguments
        Then: enabled should default to True

        Expected RED failure: Wrong default value
        """
        try:
            from data_extract.cli.models import CacheConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = CacheConfig()
        assert config.enabled is True, (
            f"CacheConfig default enabled should be True for performance. "
            f"Expected: True, got: {config.enabled}"
        )

    def test_cache_config_default_max_size_mb(self):
        """
        RED: Verify CacheConfig has default max_size_mb = 500.

        Given: A CacheConfig model
        When: We create it without arguments
        Then: max_size_mb should default to 500

        Expected RED failure: Wrong default value
        """
        try:
            from data_extract.cli.models import CacheConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = CacheConfig()
        assert config.max_size_mb == 500, (
            f"CacheConfig default max_size_mb should be reasonable. "
            f"Expected: 500, got: {config.max_size_mb}"
        )

    def test_quality_config_default_min_score(self):
        """
        RED: Verify QualityConfig has default min_score = 0.3.

        Given: A QualityConfig model
        When: We create it without arguments
        Then: min_score should default to 0.3

        Expected RED failure: Wrong default value
        """
        try:
            from data_extract.cli.models import QualityConfig
        except ImportError as e:
            pytest.fail(f"Cannot import: {e}")

        config = QualityConfig()
        assert config.min_score == 0.3, (
            f"QualityConfig default min_score should filter low-quality content. "
            f"Expected: 0.3, got: {config.min_score}"
        )

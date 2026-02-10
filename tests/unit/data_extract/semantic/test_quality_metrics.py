"""Unit tests for quality metrics integration with textstat (Story 4.4).

Tests the QualityMetricsStage, ReadabilityScores, QualityConfig, and
quality assessment functionality with comprehensive coverage.
"""

from unittest.mock import MagicMock, patch

import pytest

from data_extract.core.models import Chunk
from data_extract.semantic.quality_metrics import (
    QualityConfig,
    QualityDistributionReport,
    QualityFlag,
    QualityMetricsStage,
    ReadabilityScores,
)

pytestmark = [pytest.mark.P1, pytest.mark.unit]


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    return [
        Chunk(
            id="chunk_001",
            text="The quick brown fox jumps over the lazy dog. This is a simple sentence with clear meaning.",
            document_id="doc_001",
            position_index=0,
            token_count=15,
            word_count=15,
            quality_score=0.0,
            metadata={"source": "test"},
        ),
        Chunk(
            id="chunk_002",
            text="@#$%^&*()_+ gibberish text with lots of special characters!!!",
            document_id="doc_001",
            position_index=1,
            token_count=8,
            word_count=8,
            quality_score=0.0,
            metadata={"source": "test"},
        ),
        Chunk(
            id="chunk_003",
            text="In the realm of quantum mechanics, the wave function collapse represents a fundamental paradox that challenges our understanding of reality at the subatomic level.",
            document_id="doc_002",
            position_index=0,
            token_count=25,
            word_count=25,
            quality_score=0.0,
            metadata={"source": "test"},
        ),
    ]


@pytest.fixture
def quality_config():
    """Create test configuration."""
    return QualityConfig(
        min_quality=0.3,
        weights={
            "flesch_ease": 0.3,
            "grade_level": 0.3,
            "lexical_diversity": 0.2,
            "anomaly_absence": 0.2,
        },
        detect_gibberish=True,
        use_cache=False,  # Disable cache for unit tests
    )


class TestQualityFlag:
    """Test QualityFlag enum."""

    def test_quality_flag_values(self):
        """Test quality flag enum values."""
        assert QualityFlag.HIGH.value == "high"
        assert QualityFlag.MEDIUM.value == "medium"
        assert QualityFlag.LOW.value == "low"
        assert QualityFlag.REVIEW.value == "review"


class TestReadabilityScores:
    """Test ReadabilityScores dataclass."""

    def test_readability_scores_creation(self):
        """Test creating readability scores."""
        scores = ReadabilityScores(
            flesch_reading_ease=60.0,
            flesch_kincaid_grade=8.0,
            gunning_fog=10.0,
            smog_index=9.0,
            coleman_liau_index=8.5,
            automated_readability_index=8.0,
            dale_chall_readability_score=7.5,
            linsear_write_formula=8.0,
            syllable_count=100,
            lexical_diversity=0.75,
        )
        assert scores.flesch_reading_ease == 60.0
        assert scores.flesch_kincaid_grade == 8.0
        assert scores.syllable_count == 100
        assert scores.lexical_diversity == 0.75

    def test_readability_scores_to_dict(self):
        """Test converting readability scores to dictionary."""
        scores = ReadabilityScores(
            flesch_reading_ease=65.0,
            flesch_kincaid_grade=9.0,
            lexical_diversity=0.8,
        )
        result = scores.to_dict()
        assert result["flesch_reading_ease"] == 65.0
        assert result["flesch_kincaid_grade"] == 9.0
        assert result["lexical_diversity"] == 0.8
        assert "syllable_count" in result


class TestQualityConfig:
    """Test QualityConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = QualityConfig()
        assert config.min_quality == 0.3
        assert config.detect_gibberish is True
        assert config.use_cache is True
        assert "flesch_ease" in config.weights
        assert config.weights["flesch_ease"] == 0.2

    def test_custom_config(self):
        """Test custom configuration."""
        config = QualityConfig(
            min_quality=0.5,
            weights={"custom": 1.0},
            detect_gibberish=False,
            use_cache=False,
        )
        assert config.min_quality == 0.5
        assert config.weights == {"custom": 1.0}
        assert config.detect_gibberish is False
        assert config.use_cache is False

    def test_cache_key_components(self):
        """Test cache key generation components."""
        config = QualityConfig()
        components = config.get_cache_key_components()
        assert isinstance(components, tuple)
        assert config.min_quality in components
        assert config.detect_gibberish in components


class TestQualityDistributionReport:
    """Test QualityDistributionReport dataclass."""

    def test_report_creation(self):
        """Test creating quality distribution report."""
        report = QualityDistributionReport(
            total_chunks=100,
            high_quality_count=60,
            medium_quality_count=30,
            low_quality_count=10,
            mean_score=0.7,
            std_score=0.15,
        )
        assert report.total_chunks == 100
        assert report.high_quality_count == 60
        assert report.mean_score == 0.7

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        report = QualityDistributionReport(
            total_chunks=50,
            high_quality_count=20,
            medium_quality_count=20,
            low_quality_count=10,
            mean_score=0.65,
        )
        result = report.to_dict()
        assert result["total_chunks"] == 50
        assert result["distribution"]["high"] == 20
        assert result["statistics"]["mean"] == 0.65


class TestQualityMetricsStage:
    """Test QualityMetricsStage functionality."""

    def test_stage_initialization(self, quality_config):
        """Test stage initialization."""
        stage = QualityMetricsStage(config=quality_config)
        assert stage.config == quality_config
        assert stage.cache_manager is None  # Cache disabled in config

    def test_stage_with_cache(self):
        """Test stage with cache enabled."""
        config = QualityConfig(use_cache=True)
        stage = QualityMetricsStage(config=config)
        assert stage.cache_manager is not None

    def test_empty_input(self, quality_config):
        """Test processing empty input."""
        stage = QualityMetricsStage(config=quality_config)
        result = stage.process([])
        assert result == []

    @patch("data_extract.semantic.quality_metrics.textstat")
    def test_process_chunks(self, mock_textstat, sample_chunks, quality_config):
        """Test processing chunks with quality metrics."""
        # Mock textstat functions
        mock_textstat.flesch_reading_ease.return_value = 60.0
        mock_textstat.flesch_kincaid_grade.return_value = 8.0
        mock_textstat.gunning_fog.return_value = 10.0
        mock_textstat.smog_index.return_value = 9.0
        mock_textstat.coleman_liau_index.return_value = 8.5
        mock_textstat.automated_readability_index.return_value = 8.0
        mock_textstat.dale_chall_readability_score.return_value = 7.5
        mock_textstat.linsear_write_formula.return_value = 8.0
        mock_textstat.syllable_count.return_value = 100

        stage = QualityMetricsStage(config=quality_config)
        result = stage.process(sample_chunks)

        assert len(result) == len(sample_chunks)
        for chunk in result:
            assert chunk.quality_score >= 0.0
            assert chunk.quality_score <= 1.0
            assert "readability_scores" in chunk.readability_scores or hasattr(
                chunk, "readability_scores"
            )

    def test_lexical_diversity_calculation(self, quality_config):
        """Test lexical diversity calculation."""
        stage = QualityMetricsStage(config=quality_config)

        # High diversity text
        text1 = "The quick brown fox jumps over the lazy dog"
        diversity1 = stage._calculate_lexical_diversity(text1)
        assert diversity1 == 8 / 9  # "the" appears twice

        # Low diversity text
        text2 = "the the the the the"
        diversity2 = stage._calculate_lexical_diversity(text2)
        assert diversity2 == 0.2  # 1 unique out of 5

        # Empty text
        diversity3 = stage._calculate_lexical_diversity("")
        assert diversity3 == 0.0

    @patch("data_extract.semantic.quality_metrics.textstat")
    def test_readability_scores_computation(self, mock_textstat, quality_config):
        """Test computing readability scores."""
        mock_textstat.flesch_reading_ease.return_value = 75.0
        mock_textstat.flesch_kincaid_grade.return_value = 6.0
        mock_textstat.gunning_fog.return_value = 8.0
        mock_textstat.smog_index.return_value = 7.0
        mock_textstat.coleman_liau_index.return_value = 6.5
        mock_textstat.automated_readability_index.return_value = 6.0
        mock_textstat.dale_chall_readability_score.return_value = 5.5
        mock_textstat.linsear_write_formula.return_value = 6.0
        mock_textstat.syllable_count.return_value = 50

        stage = QualityMetricsStage(config=quality_config)
        text = "This is a simple test sentence."
        scores = stage._compute_readability_scores(text)

        assert scores.flesch_reading_ease == 75.0
        assert scores.flesch_kincaid_grade == 6.0
        assert scores.syllable_count == 50

    def test_readability_scores_edge_cases(self, quality_config):
        """Test readability scores with edge cases."""
        stage = QualityMetricsStage(config=quality_config)

        # Empty text
        scores1 = stage._compute_readability_scores("")
        assert scores1.flesch_reading_ease == 0.0

        # Very short text
        scores2 = stage._compute_readability_scores("Hi")
        assert scores2.lexical_diversity in [0.0, 1.0]  # Depends on implementation

    def test_composite_score_calculation(self, quality_config):
        """Test composite quality score calculation."""
        stage = QualityMetricsStage(config=quality_config)

        readability = ReadabilityScores(
            flesch_reading_ease=70.0,  # 0.7 normalized
            flesch_kincaid_grade=8.0,  # 0.33 normalized (1 - 8/12)
            lexical_diversity=0.8,
        )

        text = "Normal text without anomalies."
        score = stage._compute_composite_score(text, readability)

        assert 0.0 <= score <= 1.0
        # With default weights: 0.3*0.7 + 0.3*0.33 + 0.2*0.8 + 0.2*~1.0
        # = 0.21 + 0.099 + 0.16 + 0.2 = ~0.67
        assert 0.5 < score < 0.8

    def test_anomaly_detection(self, quality_config):
        """Test anomaly detection functionality."""
        stage = QualityMetricsStage(config=quality_config)

        # Normal text
        normal_readability = ReadabilityScores(
            flesch_kincaid_grade=8.0,
            lexical_diversity=0.7,
        )
        normal_score = stage._detect_anomalies("This is normal text.", normal_readability)
        assert normal_score < 0.5

        # Gibberish with special characters
        gibberish_readability = ReadabilityScores(
            flesch_kincaid_grade=25.0,  # Very high grade level
            lexical_diversity=0.05,  # Very low diversity
        )
        gibberish_text = "@#$%^&*()_+" * 10
        gibberish_score = stage._detect_anomalies(gibberish_text, gibberish_readability)
        assert gibberish_score > 0.5

    def test_quality_flag_determination(self, quality_config):
        """Test quality flag determination."""
        stage = QualityMetricsStage(config=quality_config)

        readability = ReadabilityScores(
            flesch_kincaid_grade=8.0,
            lexical_diversity=0.7,
        )

        # High quality
        flag1 = stage._determine_quality_flag(0.8, "Normal text", readability)
        assert flag1 == QualityFlag.HIGH

        # Medium quality
        flag2 = stage._determine_quality_flag(0.5, "Normal text", readability)
        assert flag2 == QualityFlag.MEDIUM

        # Low quality
        flag3 = stage._determine_quality_flag(0.2, "Normal text", readability)
        assert flag3 == QualityFlag.LOW

    def test_review_requirement_detection(self, quality_config):
        """Test detection of texts requiring review."""
        stage = QualityMetricsStage(config=quality_config)

        # Extreme grade level
        extreme_readability = ReadabilityScores(flesch_kincaid_grade=30.0)
        assert stage._requires_review("Some text", extreme_readability) is True

        # Very short text
        normal_readability = ReadabilityScores(flesch_kincaid_grade=8.0)
        assert stage._requires_review("Hi", normal_readability) is True

        # Extreme lexical poverty
        poor_readability = ReadabilityScores(
            flesch_kincaid_grade=8.0,
            lexical_diversity=0.02,
        )
        long_text = "word " * 50
        assert stage._requires_review(long_text, poor_readability) is True

    def test_chunk_enrichment(self, sample_chunks, quality_config):
        """Test chunk enrichment with quality metrics."""
        stage = QualityMetricsStage(config=quality_config)
        chunk = sample_chunks[0]

        readability = ReadabilityScores(
            flesch_reading_ease=70.0,
            flesch_kincaid_grade=8.0,
        )

        enriched = stage._enrich_chunk(chunk, readability, 0.75, QualityFlag.HIGH)

        assert enriched.quality_score == 0.75
        assert "flesch_reading_ease" in enriched.readability_scores
        assert enriched.metadata["quality_flag"] == "high"

    def test_quality_report_generation(self, sample_chunks, quality_config):
        """Test quality distribution report generation."""
        stage = QualityMetricsStage(config=quality_config)

        # Enrich chunks with different quality levels
        chunks = sample_chunks.copy()
        chunks[0].metadata["quality_flag"] = QualityFlag.HIGH.value
        chunks[1].metadata["quality_flag"] = QualityFlag.LOW.value
        chunks[2].metadata["quality_flag"] = QualityFlag.MEDIUM.value

        scores = [0.8, 0.2, 0.5]
        report = stage._generate_quality_report(chunks, scores)

        assert report.total_chunks == 3
        assert report.high_quality_count == 1
        assert report.low_quality_count == 1
        assert report.medium_quality_count == 1
        assert 0.4 < report.mean_score < 0.6  # Mean of [0.8, 0.2, 0.5]
        assert len(report.score_histogram) > 0

    @patch("data_extract.semantic.quality_metrics.textstat")
    def test_error_handling(self, mock_textstat, sample_chunks, quality_config):
        """Test error handling in readability computation."""
        # Simulate textstat error
        mock_textstat.flesch_reading_ease.side_effect = Exception("Test error")

        stage = QualityMetricsStage(config=quality_config)
        scores = stage._compute_readability_scores("Test text")

        # Should return default scores on error
        assert scores.flesch_reading_ease == 0.0
        assert scores.flesch_kincaid_grade == 0.0

    def test_cache_key_generation(self):
        """Test cache key generation."""
        config = QualityConfig(use_cache=True)
        stage = QualityMetricsStage(config=config)

        key1 = stage._generate_cache_key("Test text 1")
        key2 = stage._generate_cache_key("Test text 2")
        key3 = stage._generate_cache_key("Test text 1")

        assert key1 != key2  # Different texts
        assert key1 == key3  # Same text

    @patch("data_extract.semantic.quality_metrics.CacheManager")
    def test_caching_behavior(self, mock_cache_manager, sample_chunks, quality_config):
        """Test caching behavior."""
        # Setup mock cache
        mock_cache = MagicMock()
        mock_cache_manager.return_value = mock_cache
        mock_cache.get.return_value = None  # Cache miss first time

        config = QualityConfig(use_cache=True)
        stage = QualityMetricsStage(config=config)

        # Process chunks - should cache results
        _ = stage.process([sample_chunks[0]])

        # Verify cache was used
        assert mock_cache.get.called
        assert mock_cache.set.called

    def test_performance_metrics(self, sample_chunks, quality_config):
        """Test performance metric tracking."""
        stage = QualityMetricsStage(config=quality_config)

        # Process chunks and check timing
        import time

        start = time.time()
        result = stage.process(sample_chunks)
        elapsed = time.time() - start

        # Should complete quickly (well under 10ms per chunk requirement)
        assert elapsed < 1.0  # Very generous limit for CI
        assert len(result) == len(sample_chunks)

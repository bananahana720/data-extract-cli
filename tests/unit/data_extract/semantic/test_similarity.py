"""Unit tests for similarity analysis stage."""

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from src.data_extract.semantic.models import SemanticResult
from src.data_extract.semantic.similarity import (
    SimilarityAnalysisStage,
    SimilarityConfig,
    SimilarityResult,
)

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestSimilarityConfig:
    """Test SimilarityConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SimilarityConfig()
        assert config.duplicate_threshold == 0.95
        assert config.related_threshold == 0.7
        assert config.block_size == 100
        assert config.use_cache is True
        assert config.compute_graph is True
        assert config.min_similarity == 0.1

    def test_custom_values(self):
        """Test custom configuration values."""
        config = SimilarityConfig(
            duplicate_threshold=0.9, related_threshold=0.6, block_size=50, use_cache=False
        )
        assert config.duplicate_threshold == 0.9
        assert config.related_threshold == 0.6
        assert config.block_size == 50
        assert config.use_cache is False

    def test_cache_key_components(self):
        """Test cache key components generation."""
        config = SimilarityConfig()
        components = config.get_cache_key_components()
        assert len(components) == 4
        assert components[0] == 0.95  # duplicate_threshold
        assert components[1] == 0.7  # related_threshold


class TestSimilarityResult:
    """Test SimilarityResult dataclass."""

    def test_default_initialization(self):
        """Test default initialization of result."""
        result = SimilarityResult()
        assert result.similarity_matrix is None
        assert result.similar_pairs == []
        assert result.duplicate_groups == []
        assert result.similarity_graph == {}
        assert result.statistics == {}
        assert result.processing_time_ms == 0.0
        assert result.cache_hit is False

    def test_with_data(self):
        """Test result with actual data."""
        matrix = np.array([[1.0, 0.8], [0.8, 1.0]])
        pairs = [("doc1", "doc2", 0.8)]
        groups = [["doc1", "doc2"]]

        result = SimilarityResult(
            similarity_matrix=matrix,
            similar_pairs=pairs,
            duplicate_groups=groups,
            processing_time_ms=100.5,
        )

        assert result.similarity_matrix.shape == (2, 2)
        assert len(result.similar_pairs) == 1
        assert len(result.duplicate_groups) == 1
        assert result.processing_time_ms == 100.5


class TestSimilarityAnalysisStage:
    """Test SimilarityAnalysisStage implementation."""

    @pytest.fixture
    def sample_corpus(self):
        """Create sample corpus for testing."""
        return [
            "The quick brown fox jumps over the lazy dog",
            "The quick brown fox jumps over the lazy dog",  # Duplicate
            "A fast brown fox leaps over a sleepy dog",  # Similar
            "Python is a programming language",  # Different
            "Data science involves statistics and machine learning",  # Different
        ]

    @pytest.fixture
    def tfidf_result(self, sample_corpus):
        """Create TF-IDF result for testing."""
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(sample_corpus)

        return SemanticResult(
            tfidf_matrix=tfidf_matrix,
            vectorizer=vectorizer,
            vocabulary=vectorizer.vocabulary_,
            feature_names=vectorizer.get_feature_names_out(),
            chunk_ids=[f"doc_{i}" for i in range(len(sample_corpus))],
            success=True,
        )

    def test_initialization(self):
        """Test stage initialization."""
        stage = SimilarityAnalysisStage()
        assert stage.config.duplicate_threshold == 0.95
        assert stage.cache_manager is not None

        # Without cache
        stage_no_cache = SimilarityAnalysisStage(config=SimilarityConfig(use_cache=False))
        assert stage_no_cache.cache_manager is None

    def test_process_valid_input(self, tfidf_result):
        """Test processing with valid TF-IDF input."""
        stage = SimilarityAnalysisStage(config=SimilarityConfig(use_cache=False))

        result = stage.process(tfidf_result)

        # Check success
        assert result.success is True
        assert result.error is None

        # Check similarity matrix
        assert "similarity_matrix" in result.data
        matrix = result.data["similarity_matrix"]
        assert matrix.shape == (5, 5)

        # Check diagonal is 1.0 (self-similarity)
        np.testing.assert_array_almost_equal(np.diag(matrix), np.ones(5))

        # Check symmetry
        np.testing.assert_array_almost_equal(matrix, matrix.T)

        # Check similar pairs
        assert "similar_pairs" in result.data
        pairs = result.data["similar_pairs"]
        assert len(pairs) > 0

        # Doc 0 and 1 should be duplicates (identical text)
        duplicate_found = False
        for id1, id2, sim in pairs:
            if (id1 == "doc_0" and id2 == "doc_1") or (id1 == "doc_1" and id2 == "doc_0"):
                assert sim > 0.99  # Should be ~1.0
                duplicate_found = True
        assert duplicate_found, "Duplicate not detected"

    def test_duplicate_detection(self, tfidf_result):
        """Test duplicate detection with threshold."""
        stage = SimilarityAnalysisStage(
            config=SimilarityConfig(duplicate_threshold=0.95, use_cache=False)
        )

        result = stage.process(tfidf_result)

        # Check duplicate groups
        assert "duplicate_groups" in result.data
        groups = result.data["duplicate_groups"]
        assert len(groups) > 0

        # Doc 0 and 1 should be in same group
        doc0_doc1_grouped = False
        for group in groups:
            if "doc_0" in group and "doc_1" in group:
                doc0_doc1_grouped = True
                break
        assert doc0_doc1_grouped, "Duplicates not grouped together"

    def test_similarity_graph(self, tfidf_result):
        """Test similarity graph construction."""
        stage = SimilarityAnalysisStage(
            config=SimilarityConfig(related_threshold=0.5, compute_graph=True, use_cache=False)
        )

        result = stage.process(tfidf_result)

        # Check graph exists
        assert "similarity_graph" in result.data
        graph = result.data["similarity_graph"]
        assert isinstance(graph, dict)

        # Check edges exist for similar documents
        if "doc_0" in graph:
            edges = graph["doc_0"]
            assert len(edges) > 0
            # Edges should be sorted by similarity (descending)
            sims = [sim for _, sim in edges]
            assert sims == sorted(sims, reverse=True)

    def test_statistics_computation(self, tfidf_result):
        """Test similarity statistics computation."""
        stage = SimilarityAnalysisStage(config=SimilarityConfig(use_cache=False))

        result = stage.process(tfidf_result)

        # Check statistics
        assert "similarity_statistics" in result.data
        stats = result.data["similarity_statistics"]

        # Required statistics
        assert "mean" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        assert "median" in stats
        assert "n_samples" in stats
        assert "n_similar_pairs" in stats
        assert "n_duplicate_pairs" in stats
        assert "duplicate_rate" in stats

        # Threshold counts
        for threshold in [0.5, 0.7, 0.8, 0.9, 0.95]:
            assert f"pairs_above_{threshold}" in stats

        # Validate values
        assert 0 <= stats["mean"] <= 1
        assert stats["max"] <= 1.0
        assert stats["min"] >= 0.0
        assert stats["n_samples"] == 5

    def test_block_wise_computation(self):
        """Test block-wise computation for large matrices."""
        # Create larger corpus
        large_corpus = [f"Document number {i} contains text" for i in range(150)]
        vectorizer = TfidfVectorizer(max_features=100)
        tfidf_matrix = vectorizer.fit_transform(large_corpus)

        large_result = SemanticResult(
            tfidf_matrix=tfidf_matrix, chunk_ids=[f"doc_{i}" for i in range(150)], success=True
        )

        stage = SimilarityAnalysisStage(config=SimilarityConfig(block_size=50, use_cache=False))

        result = stage.process(large_result)

        assert result.success is True
        matrix = result.data["similarity_matrix"]
        assert matrix.shape == (150, 150)

        # Check symmetry
        np.testing.assert_array_almost_equal(matrix, matrix.T, decimal=5)

    def test_symmetry_property(self, tfidf_result):
        """Test that similarity matrix is symmetric."""
        stage = SimilarityAnalysisStage(config=SimilarityConfig(use_cache=False))

        result = stage.process(tfidf_result)
        matrix = result.data["similarity_matrix"]

        # Check perfect symmetry
        np.testing.assert_array_almost_equal(matrix, matrix.T)

        # Check specific pairs
        for i in range(matrix.shape[0]):
            for j in range(i + 1, matrix.shape[1]):
                assert abs(matrix[i, j] - matrix[j, i]) < 1e-10

    def test_deterministic_output(self, tfidf_result):
        """Test that output is deterministic across runs."""
        stage = SimilarityAnalysisStage(config=SimilarityConfig(use_cache=False))

        # Run multiple times
        result1 = stage.process(tfidf_result)
        result2 = stage.process(tfidf_result)

        # Compare matrices
        matrix1 = result1.data["similarity_matrix"]
        matrix2 = result2.data["similarity_matrix"]
        np.testing.assert_array_almost_equal(matrix1, matrix2)

        # Compare similar pairs (should be in same order)
        pairs1 = result1.data["similar_pairs"]
        pairs2 = result2.data["similar_pairs"]
        assert pairs1 == pairs2

    def test_error_handling_no_matrix(self):
        """Test error handling when TF-IDF matrix is missing."""
        invalid_input = SemanticResult(tfidf_matrix=None, success=True)

        stage = SimilarityAnalysisStage()
        result = stage.process(invalid_input)

        assert result.success is False
        assert "No TF-IDF matrix available" in result.error

    def test_error_handling_failed_input(self):
        """Test error handling when input indicates failure."""
        failed_input = SemanticResult(success=False, error="Previous stage failed")

        stage = SimilarityAnalysisStage()
        result = stage.process(failed_input)

        assert result.success is False

    def test_sparse_matrix_handling(self, sample_corpus):
        """Test handling of sparse TF-IDF matrices."""
        vectorizer = TfidfVectorizer(max_features=50)
        sparse_matrix = vectorizer.fit_transform(sample_corpus)

        # Verify it's sparse
        assert isinstance(sparse_matrix, csr_matrix)

        sparse_input = SemanticResult(
            tfidf_matrix=sparse_matrix,
            chunk_ids=[f"doc_{i}" for i in range(len(sample_corpus))],
            success=True,
        )

        stage = SimilarityAnalysisStage(config=SimilarityConfig(use_cache=False))
        result = stage.process(sparse_input)

        assert result.success is True
        assert result.data["similarity_matrix"].shape == (5, 5)

    def test_memory_efficiency(self):
        """Test memory efficiency with configurable thresholds."""
        # Create corpus with varying similarity
        corpus = [
            "Document A about topic 1",
            "Document B about topic 1",
            "Document C about topic 2",
            "Document D about topic 2",
            "Document E about topic 3",
        ]

        vectorizer = TfidfVectorizer()
        matrix = vectorizer.fit_transform(corpus)

        input_data = SemanticResult(
            tfidf_matrix=matrix, chunk_ids=[f"doc_{i}" for i in range(len(corpus))], success=True
        )

        # Process with minimum similarity threshold
        stage = SimilarityAnalysisStage(
            config=SimilarityConfig(min_similarity=0.3, use_cache=False)
        )

        result = stage.process(input_data)
        assert result.success is True

        # Check that low similarities are still computed
        sim_matrix = result.data["similarity_matrix"]
        assert sim_matrix.min() >= 0  # All similarities computed

    def test_duplicate_groups_transitive(self):
        """Test that duplicate groups handle transitive relationships."""
        # Create corpus with transitive duplicates
        # A == B, B == C, therefore A == C (transitive)
        corpus = [
            "The document contains important information",
            "The document contains important information",  # Dup of 0
            "The document contains important information",  # Dup of 0 and 1
            "Different content here",
            "Another different document",
        ]

        vectorizer = TfidfVectorizer()
        matrix = vectorizer.fit_transform(corpus)

        input_data = SemanticResult(
            tfidf_matrix=matrix, chunk_ids=["A", "B", "C", "D", "E"], success=True
        )

        stage = SimilarityAnalysisStage(
            config=SimilarityConfig(duplicate_threshold=0.99, use_cache=False)
        )

        result = stage.process(input_data)
        groups = result.data["duplicate_groups"]

        # A, B, C should be in same group
        abc_grouped = False
        for group in groups:
            if "A" in group and "B" in group and "C" in group:
                abc_grouped = True
                assert len(group) == 3
                break

        assert abc_grouped, "Transitive duplicates not grouped correctly"

    def test_performance_small_matrix(self, tfidf_result):
        """Test performance meets requirements for small matrix."""
        import time

        stage = SimilarityAnalysisStage(config=SimilarityConfig(use_cache=False))

        start = time.time()
        result = stage.process(tfidf_result)
        elapsed_ms = (time.time() - start) * 1000

        assert result.success is True
        # Should be well under 200ms for 5x5 matrix
        assert elapsed_ms < 200

        # Check reported time
        assert result.metadata["similarity_processing_time_ms"] > 0

    def test_metadata_enrichment(self, tfidf_result):
        """Test that metadata is properly enriched."""
        stage = SimilarityAnalysisStage(config=SimilarityConfig(use_cache=False))

        result = stage.process(tfidf_result)

        # Check metadata additions
        assert "similarity_cache_hit" in result.metadata
        assert "similarity_processing_time_ms" in result.metadata
        assert "n_duplicates" in result.metadata
        assert "n_similar_pairs" in result.metadata

        assert result.metadata["similarity_cache_hit"] is False
        assert result.metadata["similarity_processing_time_ms"] > 0
        assert result.metadata["n_duplicates"] >= 0
        assert result.metadata["n_similar_pairs"] >= 0


class TestCacheIntegration:
    """Test cache integration with similarity analysis."""

    @pytest.fixture
    def stage_with_cache(self):
        """Create stage with caching enabled."""
        import shutil
        from pathlib import Path

        from src.data_extract.semantic.cache import CacheManager

        # Clear cache directory to ensure clean state
        cache_dir = Path(".data-extract-cache/models/")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)

        # Reset cache manager singleton for clean state
        if hasattr(CacheManager, "_reset"):
            CacheManager._reset()

        return SimilarityAnalysisStage(config=SimilarityConfig(use_cache=True))

    def test_cache_usage(self, tfidf_result, stage_with_cache):
        """Test that cache is used when enabled."""
        # First run - cache miss
        result1 = stage_with_cache.process(tfidf_result)
        assert result1.success is True
        assert result1.metadata["similarity_cache_hit"] is False

        # Second run - cache hit
        result2 = stage_with_cache.process(tfidf_result)
        assert result2.success is True
        assert result2.metadata["similarity_cache_hit"] is True

        # Results should be identical
        matrix1 = result1.data["similarity_matrix"]
        matrix2 = result2.data["similarity_matrix"]
        np.testing.assert_array_almost_equal(matrix1, matrix2)

    # Add missing fixture for cache test
    @pytest.fixture
    def tfidf_result(self):
        """Create TF-IDF result for cache testing."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        corpus = [
            "Document one about testing",
            "Document two about caching",
            "Document three about similarity",
        ]

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)

        return SemanticResult(
            tfidf_matrix=tfidf_matrix, chunk_ids=["doc_0", "doc_1", "doc_2"], success=True
        )

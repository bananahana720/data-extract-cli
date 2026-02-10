"""Unit tests for LSA reduction stage."""

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from src.data_extract.semantic.lsa import LsaConfig, LsaReductionStage
from src.data_extract.semantic.models import SemanticResult


class TestLsaConfig:
    """Test LSA configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LsaConfig()
        assert config.n_components == 100
        assert config.n_clusters is None
        assert config.random_state == 42
        assert config.use_cache is True
        assert config.normalize is True
        assert config.top_n_terms == 10
        assert config.min_variance_explained == 0.8

    def test_config_validation(self):
        """Test configuration validation."""
        # n_components out of range
        with pytest.raises(ValueError, match="n_components must be between 50 and 300"):
            LsaConfig(n_components=49)

        with pytest.raises(ValueError, match="n_components must be between 50 and 300"):
            LsaConfig(n_components=301)

        # n_clusters too small
        with pytest.raises(ValueError, match="n_clusters must be >= 2"):
            LsaConfig(n_clusters=1)

    def test_cache_key_components(self):
        """Test cache key component generation."""
        config = LsaConfig(n_components=150, n_clusters=10)
        components = config.get_cache_key_components()
        assert components == (150, 10, 42, True, 10)


class TestLsaReductionStage:
    """Test LSA reduction stage."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            "Machine learning algorithms analyze data patterns.",
            "Deep learning neural networks process complex information.",
            "Data science combines statistics and programming skills.",
            "Financial markets require risk management strategies.",
            "Investment portfolios need diversification approaches.",
            "Banking systems implement security protocols.",
            "Cybersecurity threats evolve constantly requiring updates.",
            "Network security protects against unauthorized access.",
            "Firewall configurations prevent intrusion attempts.",
        ]

    @pytest.fixture
    def tfidf_result(self, sample_documents):
        """Create TF-IDF result for testing."""
        vectorizer = TfidfVectorizer(max_features=100, min_df=1)
        tfidf_matrix = vectorizer.fit_transform(sample_documents)

        return SemanticResult(
            tfidf_matrix=tfidf_matrix,
            vectorizer=vectorizer,
            vocabulary=vectorizer.vocabulary_,
            feature_names=np.array(vectorizer.get_feature_names_out()),
            chunk_ids=[f"doc_{i}" for i in range(len(sample_documents))],
            success=True,
        )

    def test_initialization(self):
        """Test stage initialization."""
        stage = LsaReductionStage()
        assert stage.config.n_components == 100
        assert stage.cache_manager is not None

        # Without cache
        config = LsaConfig(use_cache=False)
        stage = LsaReductionStage(config)
        assert stage.cache_manager is None

    def test_process_valid_input(self, tfidf_result):
        """Test processing with valid input."""
        stage = LsaReductionStage(LsaConfig(n_components=50, use_cache=False))
        result = stage.process(tfidf_result)

        assert result.success is True
        assert result.error is None
        assert result.data is not None
        assert "lsa_vectors" in result.data
        assert "topics" in result.data
        assert "clusters" in result.data
        assert "explained_variance" in result.data
        assert "silhouette_score" in result.data

        # Check LSA vectors shape
        lsa_vectors = result.data["lsa_vectors"]
        assert lsa_vectors.shape[0] == 9  # Number of documents
        assert lsa_vectors.shape[1] <= 50  # n_components or less

    def test_process_invalid_input(self):
        """Test processing with invalid input."""
        stage = LsaReductionStage()

        # Failed input
        failed_result = SemanticResult(success=False, error="Previous stage failed")
        result = stage.process(failed_result)
        assert result.success is False
        assert result.error == "Previous stage failed"

        # Missing TF-IDF matrix
        empty_result = SemanticResult(success=True)
        result = stage.process(empty_result)
        assert result.success is False
        assert "No TF-IDF matrix" in result.error

    def test_topic_extraction(self, tfidf_result):
        """Test topic extraction."""
        stage = LsaReductionStage(LsaConfig(n_components=50, top_n_terms=5, use_cache=False))
        result = stage.process(tfidf_result)

        topics = result.data["topics"]
        assert isinstance(topics, dict)
        assert len(topics) > 0

        # Check each topic has top terms
        for topic_idx, terms in topics.items():
            assert isinstance(terms, list)
            assert len(terms) == 5  # top_n_terms

    def test_clustering(self, tfidf_result):
        """Test document clustering."""
        stage = LsaReductionStage(LsaConfig(n_components=50, n_clusters=3, use_cache=False))
        result = stage.process(tfidf_result)

        clusters = result.data["clusters"]
        assert len(clusters) == 9  # Number of documents
        assert len(np.unique(clusters)) == 3  # n_clusters

        # Check silhouette score
        score = result.data["silhouette_score"]
        assert isinstance(score, float)
        assert -1 <= score <= 1  # Valid silhouette score range

    def test_explained_variance(self, tfidf_result):
        """Test explained variance calculation."""
        stage = LsaReductionStage(LsaConfig(n_components=50, use_cache=False))
        result = stage.process(tfidf_result)

        explained_variance = result.data["explained_variance"]
        assert isinstance(explained_variance, np.ndarray)
        assert len(explained_variance) <= 50
        assert np.sum(explained_variance) <= 1.0  # Total variance ratio <= 1

        # Check metadata
        total_variance = result.metadata["total_variance_explained"]
        assert total_variance == np.sum(explained_variance)

    def test_normalization(self, tfidf_result):
        """Test L2 normalization of LSA vectors."""
        # With normalization
        stage = LsaReductionStage(LsaConfig(n_components=50, normalize=True, use_cache=False))
        result = stage.process(tfidf_result)

        lsa_vectors = result.data["lsa_vectors"]
        norms = np.linalg.norm(lsa_vectors, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(len(norms)), decimal=5)

        # Without normalization
        stage = LsaReductionStage(LsaConfig(n_components=50, normalize=False, use_cache=False))
        result = stage.process(tfidf_result)

        lsa_vectors = result.data["lsa_vectors"]
        norms = np.linalg.norm(lsa_vectors, axis=1)
        # Not all norms should be exactly 1
        assert not np.allclose(norms, np.ones(len(norms)))

    def test_determinism(self, tfidf_result):
        """Test deterministic results with fixed random state."""
        config = LsaConfig(n_components=50, n_clusters=3, random_state=42, use_cache=False)

        # Run twice
        stage1 = LsaReductionStage(config)
        result1 = stage1.process(tfidf_result)

        stage2 = LsaReductionStage(config)
        result2 = stage2.process(tfidf_result)

        # Results should be identical
        np.testing.assert_array_equal(result1.data["clusters"], result2.data["clusters"])
        np.testing.assert_array_almost_equal(
            result1.data["lsa_vectors"], result2.data["lsa_vectors"], decimal=6
        )

    def test_topic_distributions(self, tfidf_result):
        """Test topic distribution calculation."""
        stage = LsaReductionStage(LsaConfig(n_components=50, use_cache=False))
        result = stage.process(tfidf_result)

        distributions = result.data["topic_distributions"]
        assert distributions is not None
        assert distributions.shape[0] == 9  # Number of documents

        # Each row should sum to approximately 1 (probability distribution)
        row_sums = np.sum(distributions, axis=1)
        np.testing.assert_array_almost_equal(row_sums, np.ones(len(row_sums)), decimal=5)

    def test_auto_cluster_selection(self, tfidf_result):
        """Test automatic cluster number selection."""
        stage = LsaReductionStage(LsaConfig(n_components=50, n_clusters=None, use_cache=False))
        result = stage.process(tfidf_result)

        clusters = result.data["clusters"]
        n_clusters = len(np.unique(clusters))

        # Should use sqrt(n/2) heuristic
        expected = max(2, int(np.sqrt(9 / 2)))  # 9 documents
        assert n_clusters == expected

    def test_small_dataset_handling(self):
        """Test handling of very small datasets."""
        # Create tiny dataset
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(["doc1", "doc2"])

        small_result = SemanticResult(
            tfidf_matrix=tfidf_matrix,
            vectorizer=vectorizer,
            feature_names=np.array(vectorizer.get_feature_names_out()),
            chunk_ids=["doc_1", "doc_2"],
            success=True,
        )

        stage = LsaReductionStage(LsaConfig(n_components=100, use_cache=False))
        result = stage.process(small_result)

        assert result.success is True
        # Should adapt n_components to data size
        assert result.data["lsa_vectors"].shape[1] < 100

    def test_cluster_centers(self, tfidf_result):
        """Test cluster center calculation."""
        stage = LsaReductionStage(LsaConfig(n_components=50, n_clusters=3, use_cache=False))
        result = stage.process(tfidf_result)

        centers = result.data["cluster_centers"]
        assert centers is not None
        assert centers.shape[0] == 3  # n_clusters
        assert centers.shape[1] <= 50  # n_components

    def test_processing_time_tracking(self, tfidf_result):
        """Test processing time is tracked."""
        stage = LsaReductionStage(LsaConfig(use_cache=False))
        result = stage.process(tfidf_result)

        assert result.processing_time_ms > 0
        assert result.processing_time_ms < 5000  # Should be fast for small dataset

    def test_incremental_fit_support(self, tfidf_result):
        """Test that stage supports incremental processing."""
        # This tests the interface - actual incremental fit would be in AC-4.3-9
        stage = LsaReductionStage(LsaConfig(n_components=50, use_cache=False))

        # Process first batch
        result1 = stage.process(tfidf_result)
        assert result1.success is True

        # Process second batch (simulated)
        result2 = stage.process(tfidf_result)
        assert result2.success is True

    def test_empty_vocabulary_handling(self):
        """Test handling of empty vocabulary."""
        # Create result with empty features
        empty_result = SemanticResult(
            tfidf_matrix=csr_matrix((0, 0)),
            feature_names=np.array([]),
            chunk_ids=[],
            success=True,
        )

        stage = LsaReductionStage()
        result = stage.process(empty_result)

        # Should handle gracefully
        assert result.success is False or result.data["lsa_vectors"].shape[0] == 0

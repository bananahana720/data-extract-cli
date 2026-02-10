"""Unit tests for TF-IDF vectorization stage."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from data_extract.chunk.models import Chunk
from data_extract.core.models import Metadata
from data_extract.semantic.cache import CacheManager
from data_extract.semantic.models import SemanticResult, TfidfConfig
from data_extract.semantic.tfidf import TfidfVectorizationStage

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestTfidfConfig:
    """Tests for TfidfConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TfidfConfig()
        assert config.max_features == 5000
        assert config.min_df == 2
        assert config.max_df == 0.95
        assert config.ngram_range == (1, 2)
        assert config.sublinear_tf is True
        assert config.use_cache is True
        assert config.quality_threshold == 0.5
        assert config.random_state == 42

    def test_custom_config(self):
        """Test custom configuration values."""
        config = TfidfConfig(
            max_features=10000,
            min_df=5,
            max_df=0.9,
            ngram_range=(1, 3),
            sublinear_tf=False,
            use_cache=False,
            quality_threshold=0.7,
            random_state=123,
        )
        assert config.max_features == 10000
        assert config.min_df == 5
        assert config.max_df == 0.9
        assert config.ngram_range == (1, 3)
        assert config.sublinear_tf is False
        assert config.use_cache is False
        assert config.quality_threshold == 0.7
        assert config.random_state == 123

    def test_to_dict(self):
        """Test conversion to dictionary for vectorizer initialization."""
        config = TfidfConfig()
        params = config.to_dict()

        assert params["max_features"] == 5000
        assert params["min_df"] == 2
        assert params["max_df"] == 0.95
        assert params["ngram_range"] == (1, 2)
        assert params["sublinear_tf"] is True
        assert params["use_idf"] is True
        assert params["norm"] == "l2"
        assert params["smooth_idf"] is True
        assert params["token_pattern"] == r"\b\w+\b"
        assert params["lowercase"] is True
        assert params["strip_accents"] == "unicode"

    def test_cache_key_components(self):
        """Test cache key components extraction."""
        config = TfidfConfig(
            max_features=3000,
            min_df=3,
            max_df=0.85,
            ngram_range=(2, 3),
            sublinear_tf=False,
            quality_threshold=0.6,
            random_state=99,
        )
        components = config.get_cache_key_components()
        assert components == (3000, 3, 0.85, (2, 3), False, 0.6, 99)


class TestSemanticResult:
    """Tests for SemanticResult class."""

    def test_semantic_result_initialization(self):
        """Test SemanticResult initialization with TF-IDF data."""
        # Create mock data
        matrix = csr_matrix([[1, 2], [3, 4]])
        vectorizer = MagicMock(spec=TfidfVectorizer)
        vocabulary = {"word1": 0, "word2": 1}
        feature_names = np.array(["word1", "word2"])
        chunk_ids = ["chunk1", "chunk2"]

        result = SemanticResult(
            tfidf_matrix=matrix,
            vectorizer=vectorizer,
            vocabulary=vocabulary,
            feature_names=feature_names,
            chunk_ids=chunk_ids,
            cache_hit=True,
            processing_time_ms=123.45,
        )

        assert result.success is True
        assert result.tfidf_matrix is matrix
        assert result.vectorizer is vectorizer
        assert result.vocabulary == vocabulary
        assert np.array_equal(result.feature_names, feature_names)
        assert result.chunk_ids == chunk_ids
        assert result.cache_hit is True
        assert result.processing_time_ms == 123.45

    def test_get_chunk_vector(self):
        """Test retrieving vector for specific chunk."""
        matrix = csr_matrix([[1, 2], [3, 4], [5, 6]])
        chunk_ids = ["chunk1", "chunk2", "chunk3"]

        result = SemanticResult(
            tfidf_matrix=matrix,
            chunk_ids=chunk_ids,
        )

        # Test valid chunk ID
        vector = result.get_chunk_vector("chunk2")
        assert vector is not None
        assert vector.shape == (1, 2)
        assert vector.toarray()[0, 0] == 3
        assert vector.toarray()[0, 1] == 4

        # Test invalid chunk ID
        vector = result.get_chunk_vector("chunk999")
        assert vector is None

    def test_get_vocabulary_size(self):
        """Test vocabulary size calculation."""
        vocabulary = {"word1": 0, "word2": 1, "word3": 2}
        result = SemanticResult(vocabulary=vocabulary)
        assert result.get_vocabulary_size() == 3

        # Test with None vocabulary
        result = SemanticResult(vocabulary=None)
        assert result.get_vocabulary_size() == 0

    def test_get_num_chunks(self):
        """Test number of chunks calculation."""
        chunk_ids = ["chunk1", "chunk2", "chunk3"]
        result = SemanticResult(chunk_ids=chunk_ids)
        assert result.get_num_chunks() == 3

        # Test with None chunk_ids
        result = SemanticResult(chunk_ids=None)
        assert result.get_num_chunks() == 0


class TestTfidfVectorizationStage:
    """Tests for TfidfVectorizationStage class."""

    def create_test_chunks(self, num_chunks: int = 3) -> list:
        """Create test chunks with varying quality scores."""
        chunks = []
        texts = [
            "The quick brown fox jumps over the lazy dog",
            "Machine learning is a subset of artificial intelligence",
            "Natural language processing enables computers to understand text",
        ]
        quality_scores = [0.8, 0.3, 0.9]  # One below threshold

        # Create base metadata that's common to all chunks
        base_metadata = Metadata(
            source_file=Path("test_document.pdf"),
            file_hash="abc123def456",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0.0",
        )

        for i in range(min(num_chunks, len(texts))):
            text = texts[i]
            word_count = len(text.split())

            # Create chunk with all required fields
            chunk = Chunk(
                id=f"chunk_{i:03d}",
                text=text,
                document_id=f"doc_{i}",
                position_index=i,
                token_count=word_count * 2,  # Approximate tokens
                word_count=word_count,
                quality_score=quality_scores[i],
                metadata=base_metadata,
                entities=[],
                readability_scores={},
            )
            chunks.append(chunk)
        return chunks

    def test_initialization_default_config(self):
        """Test stage initialization with default config."""
        stage = TfidfVectorizationStage()
        assert stage.config is not None
        assert stage.config.max_features == 5000
        assert stage.cache_manager is not None

    def test_initialization_custom_config(self):
        """Test stage initialization with custom config."""
        config = TfidfConfig(use_cache=False, max_features=1000)
        stage = TfidfVectorizationStage(config=config)
        assert stage.config.max_features == 1000
        assert stage.cache_manager is None  # Cache disabled

    def test_process_empty_input(self):
        """Test processing with empty input."""
        stage = TfidfVectorizationStage()
        result = stage.process([])

        assert isinstance(result, SemanticResult)
        assert result.success is False
        assert "No chunks provided" in result.error

    def test_process_quality_filtering(self):
        """Test that chunks are filtered by quality score."""
        config = TfidfConfig(
            use_cache=False, quality_threshold=0.5, min_df=1
        )  # Lower min_df for small test
        stage = TfidfVectorizationStage(config=config)
        chunks = self.create_test_chunks(3)

        result = stage.process(chunks)

        assert result.success is True
        # Only 2 chunks should pass (quality scores 0.8 and 0.9)
        assert result.get_num_chunks() == 2
        assert "chunk_000" in result.chunk_ids
        assert "chunk_001" not in result.chunk_ids  # Filtered out (0.3 < 0.5)
        assert "chunk_002" in result.chunk_ids

    def test_process_all_filtered_out(self):
        """Test when all chunks are filtered out."""
        config = TfidfConfig(use_cache=False, quality_threshold=0.95)
        stage = TfidfVectorizationStage(config=config)
        chunks = self.create_test_chunks(3)

        result = stage.process(chunks)

        assert result.success is False
        assert "No chunks passed quality threshold" in result.error

    def test_process_successful_vectorization(self):
        """Test successful TF-IDF vectorization."""
        config = TfidfConfig(
            use_cache=False,
            quality_threshold=0.5,
            max_features=100,
            min_df=1,  # Lower for test data
            ngram_range=(1, 2),
        )
        stage = TfidfVectorizationStage(config=config)
        chunks = self.create_test_chunks(3)

        result = stage.process(chunks)

        assert result.success is True
        assert result.tfidf_matrix is not None
        assert isinstance(result.tfidf_matrix, csr_matrix)
        assert result.tfidf_matrix.shape[0] == 2  # 2 chunks passed quality filter
        assert result.vocabulary is not None
        assert len(result.vocabulary) > 0
        assert result.feature_names is not None
        assert len(result.feature_names) == len(result.vocabulary)
        assert result.chunk_ids == ["chunk_000", "chunk_002"]

    def test_process_deterministic_output(self):
        """Test that identical input produces identical output."""
        config = TfidfConfig(use_cache=False, quality_threshold=0.0, min_df=1)
        stage = TfidfVectorizationStage(config=config)
        chunks = self.create_test_chunks(3)

        # Process same chunks multiple times
        result1 = stage.process(chunks)
        result2 = stage.process(chunks)
        result3 = stage.process(chunks)

        # Check that outputs are identical
        assert result1.vocabulary == result2.vocabulary == result3.vocabulary
        assert np.array_equal(result1.feature_names, result2.feature_names)
        assert np.array_equal(result2.feature_names, result3.feature_names)
        # Check matrix values are very close (accounting for floating point)
        assert np.allclose(
            result1.tfidf_matrix.toarray(),
            result2.tfidf_matrix.toarray(),
            rtol=1e-10,
        )
        assert np.allclose(
            result2.tfidf_matrix.toarray(),
            result3.tfidf_matrix.toarray(),
            rtol=1e-10,
        )

    @patch("data_extract.semantic.tfidf.CacheManager")
    def test_process_with_cache_hit(self, mock_cache_manager_class):
        """Test processing with cache hit."""
        # Setup mock cache manager
        mock_cache_instance = MagicMock()
        mock_cache_manager_class.return_value = mock_cache_instance

        # Mock cache hit data
        cached_matrix = csr_matrix([[1, 2], [3, 4]])
        cached_vectorizer = MagicMock(spec=TfidfVectorizer)
        cached_vocabulary = {"test": 0, "data": 1}
        cached_features = np.array(["test", "data"])

        mock_cache_instance.get.return_value = {
            "matrix": cached_matrix,
            "vectorizer": cached_vectorizer,
            "vocabulary": cached_vocabulary,
            "feature_names": cached_features,
        }

        # Create stage and process
        config = TfidfConfig(use_cache=True, quality_threshold=0.0)
        stage = TfidfVectorizationStage(config=config)
        chunks = self.create_test_chunks(2)

        result = stage.process(chunks)

        # Verify cache was checked
        mock_cache_instance.generate_cache_key.assert_called_once()
        mock_cache_instance.get.assert_called_once()

        # Verify cached data was used
        assert result.success is True
        assert result.cache_hit is True
        assert result.tfidf_matrix is cached_matrix
        assert result.vectorizer is cached_vectorizer

    @patch("data_extract.semantic.tfidf.CacheManager")
    def test_process_with_cache_miss(self, mock_cache_manager_class):
        """Test processing with cache miss and subsequent caching."""
        # Setup mock cache manager
        mock_cache_instance = MagicMock()
        mock_cache_manager_class.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = None  # Cache miss

        # Create stage and process
        config = TfidfConfig(use_cache=True, quality_threshold=0.0, min_df=1)
        stage = TfidfVectorizationStage(config=config)
        chunks = self.create_test_chunks(2)

        result = stage.process(chunks)

        # Verify cache was checked and set
        mock_cache_instance.generate_cache_key.assert_called_once()
        mock_cache_instance.get.assert_called_once()
        mock_cache_instance.set.assert_called_once()

        # Verify result
        assert result.success is True
        assert result.cache_hit is False

    def test_transform_not_fitted(self):
        """Test transform before fitting."""
        stage = TfidfVectorizationStage()
        chunks = self.create_test_chunks(2)

        result = stage.transform(chunks)
        assert result is None

    def test_transform_after_process(self):
        """Test transform after processing."""
        config = TfidfConfig(use_cache=False, quality_threshold=0.0, min_df=1)
        stage = TfidfVectorizationStage(config=config)

        # First process to fit vectorizer
        chunks = self.create_test_chunks(2)
        process_result = stage.process(chunks)
        assert process_result.success is True

        # Now transform new chunks
        base_metadata = Metadata(
            source_file=Path("test_transform.pdf"),
            file_hash="xyz789",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0.0",
        )

        new_chunks = [
            Chunk(
                id="new_001",
                text="This is new test data for transformation",
                document_id="new_doc",
                position_index=0,
                token_count=14,
                word_count=7,
                quality_score=0.9,
                metadata=base_metadata,
                entities=[],
                readability_scores={},
            )
        ]
        transform_result = stage.transform(new_chunks)

        assert transform_result is not None
        assert isinstance(transform_result, csr_matrix)
        assert transform_result.shape[0] == 1

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # With cache enabled
        config = TfidfConfig(use_cache=True)
        stage = TfidfVectorizationStage(config=config)
        stats = stage.get_cache_stats()
        assert "cache_hits" in stats
        assert "cache_misses" in stats

        # With cache disabled
        config = TfidfConfig(use_cache=False)
        stage = TfidfVectorizationStage(config=config)
        stats = stage.get_cache_stats()
        assert stats == {"cache_enabled": False}

    def test_clear_cache(self):
        """Test clearing cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            # Reset singleton to use new cache dir
            CacheManager._reset()
            cache_manager = CacheManager()
            cache_manager._initialized = False
            cache_manager.__init__(cache_dir=cache_dir)

            config = TfidfConfig(use_cache=True)
            stage = TfidfVectorizationStage(config=config)
            stage.cache_manager = cache_manager

            # Add something to cache
            cache_manager.set("test_key", {"data": "test"})
            stats = cache_manager.get_stats()
            assert stats["num_entries"] == 1

            # Clear cache
            stage.clear_cache()
            stats = cache_manager.get_stats()
            assert stats["num_entries"] == 0

    def test_get_config(self):
        """Test getting configuration."""
        config = TfidfConfig(max_features=3000)
        stage = TfidfVectorizationStage(config=config)
        retrieved_config = stage.get_config()
        assert retrieved_config is config
        assert retrieved_config.max_features == 3000

    def test_vectorization_with_ngrams(self):
        """Test that n-grams are properly extracted."""
        config = TfidfConfig(
            use_cache=False,
            quality_threshold=0.0,
            min_df=1,
            max_df=1.0,  # Allow all documents for single-document test
            ngram_range=(1, 2),
        )
        stage = TfidfVectorizationStage(config=config)

        base_metadata = Metadata(
            source_file=Path("test_ngrams.pdf"),
            file_hash="ngram123",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0.0",
        )

        chunks = [
            Chunk(
                id="test",
                text="machine learning",
                document_id="doc",
                position_index=0,
                token_count=4,
                word_count=2,
                quality_score=1.0,
                metadata=base_metadata,
                entities=[],
                readability_scores={},
            )
        ]

        result = stage.process(chunks)
        assert result.success is True

        # Check that bigram "machine learning" is in vocabulary
        assert "machine" in result.vocabulary
        assert "learning" in result.vocabulary
        assert "machine learning" in result.vocabulary

    def test_sparse_matrix_memory_efficiency(self):
        """Test that sparse matrix format is used for memory efficiency."""
        config = TfidfConfig(use_cache=False, quality_threshold=0.0, min_df=1)
        stage = TfidfVectorizationStage(config=config)

        base_metadata = Metadata(
            source_file=Path("test_sparse.pdf"),
            file_hash="sparse456",
            processing_timestamp=datetime.now(),
            tool_version="1.0.0",
            config_version="1.0.0",
        )

        # Create many chunks with diverse vocabulary
        chunks = []
        for i in range(100):
            text = f"This is document number {i} with unique word{i}"
            word_count = len(text.split())
            chunk = Chunk(
                id=f"chunk_{i:03d}",
                text=text,
                document_id=f"doc_{i}",
                position_index=i,
                token_count=word_count * 2,
                word_count=word_count,
                quality_score=1.0,
                metadata=base_metadata,
                entities=[],
                readability_scores={},
            )
            chunks.append(chunk)

        result = stage.process(chunks)
        assert result.success is True
        assert isinstance(result.tfidf_matrix, csr_matrix)

        # Check sparsity
        matrix = result.tfidf_matrix
        density = matrix.nnz / (matrix.shape[0] * matrix.shape[1])
        assert density < 0.5  # Should be sparse (less than 50% non-zero)

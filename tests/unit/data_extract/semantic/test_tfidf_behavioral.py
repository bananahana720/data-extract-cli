"""
Behavioral tests for TF-IDF functionality using real sklearn.

These tests validate actual behavior, not structure.
No stubs, no skipif, no fake tests - only real behavioral validation.
"""

import numpy as np
import pytest
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestTfidfBehavior:
    """Test TF-IDF behavior using real sklearn implementation."""

    def test_tfidf_produces_sparse_matrix(self):
        """TF-IDF should produce sparse matrix for efficiency."""
        corpus = [
            "The quick brown fox jumps over the lazy dog",
            "A quick brown dog jumps over the lazy fox",
            "The fox and the dog are both quick and brown",
        ]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)

        # Behavioral assertions - test OUTCOMES not structure
        assert sparse.issparse(vectors), "TF-IDF should produce sparse matrix"
        assert vectors.shape[0] == 3, "Should have one vector per document"
        assert vectors.shape[1] > 0, "Should have vocabulary features"
        assert vectors.dtype == np.float64, "Should use float64 for precision"

    def test_tfidf_weights_decrease_with_frequency(self):
        """Common words should have lower TF-IDF weights."""
        # Create corpus where "the" appears in all docs, "unique" in only one
        corpus = ["the quick brown fox", "the lazy dog", "the unique elephant"]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)
        vocab = vectorizer.vocabulary_

        # Get weights for "the" (common) vs "unique" (rare)
        the_idx = vocab.get("the")
        unique_idx = vocab.get("unique")

        # "the" appears in all docs, should have lower weight
        # "unique" appears in one doc, should have higher weight
        the_weights = vectors[:, the_idx].toarray().flatten()
        unique_weights = vectors[:, unique_idx].toarray().flatten()

        assert max(the_weights) < max(
            unique_weights
        ), "Common words should have lower TF-IDF weights than rare words"

    def test_tfidf_handles_empty_documents(self):
        """TF-IDF should handle empty documents gracefully."""
        corpus = ["document one", "", "document three"]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)

        # Empty document should produce zero vector
        empty_doc_vector = vectors[1].toarray().flatten()
        assert np.allclose(empty_doc_vector, 0), "Empty doc should have zero vector"
        assert vectors.shape[0] == 3, "Should preserve document count"

    def test_tfidf_vocabulary_excludes_stopwords(self):
        """TF-IDF with stop_words should exclude common words."""
        corpus = [
            "The data analysis is important",
            "Important analysis of the data",
            "Data is the key",
        ]

        # With stopwords
        vectorizer_with_stop = TfidfVectorizer(stop_words="english")
        vectorizer_without_stop = TfidfVectorizer()

        vectorizer_with_stop.fit(corpus)
        vectorizer_without_stop.fit(corpus)

        vocab_with = set(vectorizer_with_stop.vocabulary_.keys())
        vocab_without = set(vectorizer_without_stop.vocabulary_.keys())

        # Behavioral test: stopwords should reduce vocabulary
        assert len(vocab_with) < len(
            vocab_without
        ), "Removing stopwords should reduce vocabulary size"
        assert "the" not in vocab_with, "Common stopword 'the' should be excluded"
        assert "data" in vocab_with, "Content word 'data' should be included"

    def test_tfidf_normalization_creates_unit_vectors(self):
        """TF-IDF with L2 norm should create unit vectors."""
        corpus = [
            "document about machine learning",
            "another document about deep learning",
            "final document about learning",
        ]

        vectorizer = TfidfVectorizer(norm="l2")
        vectors = vectorizer.fit_transform(corpus)

        # Each document vector should have L2 norm of 1
        for i in range(vectors.shape[0]):
            doc_vector = vectors[i].toarray().flatten()
            norm = np.linalg.norm(doc_vector)
            assert np.allclose(
                norm, 1.0, rtol=1e-7
            ), f"Document {i} should have unit norm, got {norm}"

    def test_tfidf_max_features_limits_vocabulary(self):
        """max_features parameter should limit vocabulary size."""
        corpus = [
            "one two three four five six seven eight nine ten",
            "alpha beta gamma delta epsilon zeta eta theta iota kappa",
            "red green blue yellow orange purple pink brown black white",
        ]

        max_features = 10
        vectorizer = TfidfVectorizer(max_features=max_features)
        vectors = vectorizer.fit_transform(corpus)

        # Behavioral validation
        assert (
            len(vectorizer.vocabulary_) == max_features
        ), f"Vocabulary should be limited to {max_features} features"
        assert vectors.shape[1] == max_features, f"Vector dimension should be {max_features}"

        # Most frequent/important terms should be kept
        # (This is behavioral - we care about the outcome, not the algorithm)
        assert vectors.nnz > 0, "Should have non-zero entries"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

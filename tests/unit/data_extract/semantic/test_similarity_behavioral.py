"""
Behavioral tests for document similarity using real sklearn.

These tests validate actual behavior of similarity metrics.
No stubs, no skipif, no fake tests - only real behavioral validation.
"""

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestSimilarityBehavior:
    """Test document similarity behavior using real sklearn implementation."""

    def test_identical_documents_have_perfect_similarity(self):
        """Identical documents should have similarity of 1.0."""
        doc1 = "The quick brown fox jumps over the lazy dog"
        doc2 = "The quick brown fox jumps over the lazy dog"
        doc3 = "A completely different text about something else"

        corpus = [doc1, doc2, doc3]
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)

        similarity_matrix = cosine_similarity(vectors)

        # Behavioral assertions
        assert np.allclose(
            similarity_matrix[0, 1], 1.0
        ), "Identical docs should have similarity = 1"
        assert similarity_matrix[0, 2] < 0.5, "Different docs should have low similarity"
        assert np.allclose(np.diag(similarity_matrix), 1.0), "Self-similarity should be 1.0"

    def test_similarity_is_symmetric(self):
        """Similarity should be symmetric: sim(A,B) = sim(B,A)."""
        corpus = [
            "Document about machine learning algorithms",
            "Text discussing deep learning neural networks",
            "Article on natural language processing",
            "Paper about computer vision techniques",
        ]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)
        similarity_matrix = cosine_similarity(vectors)

        # Check symmetry
        for i in range(len(corpus)):
            for j in range(len(corpus)):
                assert np.allclose(
                    similarity_matrix[i, j], similarity_matrix[j, i]
                ), f"Similarity not symmetric at ({i},{j})"

    def test_related_documents_have_higher_similarity(self):
        """Documents on related topics should have higher similarity."""
        ml_doc1 = "Machine learning uses algorithms to learn patterns from data"
        ml_doc2 = "Deep learning is a subset of machine learning using neural networks"
        cooking_doc = "Italian pasta recipes require fresh ingredients and proper timing"
        sports_doc = "Basketball requires teamwork, strategy, and physical fitness"

        corpus = [ml_doc1, ml_doc2, cooking_doc, sports_doc]
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)
        similarity_matrix = cosine_similarity(vectors)

        ml_similarity = similarity_matrix[0, 1]  # ML docs
        ml_cooking = similarity_matrix[0, 2]  # ML vs cooking
        ml_sports = similarity_matrix[0, 3]  # ML vs sports
        cooking_sports = similarity_matrix[2, 3]  # Cooking vs sports

        # Behavioral validation
        assert ml_similarity > ml_cooking, "Related ML docs should be more similar than ML-cooking"
        assert ml_similarity > ml_sports, "Related ML docs should be more similar than ML-sports"
        assert ml_similarity > 0.2, "Related documents should have meaningful similarity"
        assert ml_cooking < 0.1, "Unrelated topics should have low similarity"

    def test_similarity_range_bounded(self):
        """Cosine similarity should be bounded between -1 and 1."""
        corpus = [
            "First document with some content",
            "Second document with different content",
            "Third document about something else",
            "Fourth document with unique information",
            "Fifth document discussing various topics",
        ]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)
        similarity_matrix = cosine_similarity(vectors)

        # All similarities should be in valid range
        assert np.all(similarity_matrix >= -1.0), "Similarities should be >= -1"
        assert np.all(
            similarity_matrix <= 1.0001
        ), "Similarities should be <= 1 (with small tolerance)"
        # TF-IDF vectors are non-negative, so similarities should be >= 0
        assert np.all(similarity_matrix >= 0), "TF-IDF similarities should be non-negative"

    def test_stopword_removal_improves_content_similarity(self):
        """Removing stopwords should improve content-based similarity."""
        # Docs with same content but different function words
        doc1 = "The machine learning algorithm is very important"
        doc2 = "A machine learning algorithm was quite important"
        doc3 = "Pizza recipes from traditional Italian cooking"

        # Test with and without stopwords
        vectorizer_with_stop = TfidfVectorizer(stop_words="english")
        vectorizer_no_stop = TfidfVectorizer()

        for vectorizer, name in [
            (vectorizer_with_stop, "with_stop"),
            (vectorizer_no_stop, "no_stop"),
        ]:
            corpus = [doc1, doc2, doc3]
            vectors = vectorizer.fit_transform(corpus)
            sim_matrix = cosine_similarity(vectors)

            if name == "with_stop":
                sim_with_stop = sim_matrix[0, 1]
            else:
                sim_no_stop = sim_matrix[0, 1]

        # Behavioral assertion: removing stopwords increases content similarity
        assert (
            sim_with_stop > sim_no_stop
        ), "Stopword removal should increase similarity for content-similar docs"

    def test_empty_document_similarity(self):
        """Empty documents should be handled gracefully."""
        corpus = [
            "Normal document with content",
            "",  # Empty document
            "Another document with text",
        ]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)
        similarity_matrix = cosine_similarity(vectors)

        # Empty doc should have zero similarity with others (except self)
        assert similarity_matrix[1, 0] == 0, "Empty doc should have 0 similarity with others"
        assert similarity_matrix[1, 2] == 0, "Empty doc should have 0 similarity with others"
        # Note: sklearn may give 0 or NaN for empty-empty similarity
        # depending on version, but it should be handled without error

    def test_similarity_threshold_filtering(self):
        """Can use similarity threshold to find related documents."""
        corpus = [
            "Python programming for data science",
            "Data science with Python and pandas",
            "Machine learning in Python",
            "Cooking Italian pasta dishes",
            "Basketball game strategies",
        ]

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)
        similarity_matrix = cosine_similarity(vectors)

        # Find docs similar to first doc (threshold = 0.2)
        threshold = 0.2
        similar_to_first = np.where(similarity_matrix[0, :] > threshold)[0]

        # Should find the Python/data science related docs (indices 0, 1, 2)
        # Should not find cooking or basketball docs
        assert 0 in similar_to_first, "Should include self"
        assert 1 in similar_to_first, "Should find related data science doc"
        assert 3 not in similar_to_first, "Should not find cooking doc"
        assert 4 not in similar_to_first, "Should not find basketball doc"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

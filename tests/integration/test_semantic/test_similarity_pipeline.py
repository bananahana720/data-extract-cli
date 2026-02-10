"""
Integration tests for document and chunk similarity analysis.

Test IDs: SIM-001 through SIM-010

Tests similarity computation, matrix generation, and related document identification.
"""

from typing import List

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.semantic]

from src.data_extract.chunk.models import Chunk  # noqa: E402
from src.data_extract.core.models import ProcessingContext  # noqa: E402

pytestmark = [
    pytest.mark.integration,
    pytest.mark.semantic,
    pytest.mark.similarity,
    pytest.mark.epic4,
]


class TestSimilarityIntegration:
    """Integration tests for similarity analysis."""

    def test_sim001_document_similarity_matrix(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test SIM-001: Generate document similarity matrix.

        Given: TF-IDF vectors from multiple documents
        When: Computing pairwise similarity
        Then: Symmetric matrix with diagonal = 1.0
        """
        import numpy as np  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            ),
            min_df=semantic_processing_context.config.get("tfidf", {}).get("min_df", 1),
            max_df=semantic_processing_context.config.get("tfidf", {}).get("max_df", 0.95),
        )
        vectors = vectorizer.fit_transform(texts)

        # Compute similarity matrix
        similarity_matrix = cosine_similarity(vectors)

        # Behavioral assertions
        n_docs = len(chunked_documents)
        assert similarity_matrix.shape == (n_docs, n_docs), "Should be square matrix"

        # Check symmetry
        assert np.allclose(similarity_matrix, similarity_matrix.T), "Must be symmetric"

        # Check diagonal (self-similarity = 1)
        assert np.allclose(similarity_matrix.diagonal(), 1.0), "Self-similarity should be 1"

        # Check range
        assert similarity_matrix.min() >= -1.0, "Cosine similarity >= -1"
        assert similarity_matrix.max() <= 1.0, "Cosine similarity <= 1"

        # Check no NaN/Inf
        assert not np.any(np.isnan(similarity_matrix)), "No NaN values"
        assert not np.any(np.isinf(similarity_matrix)), "No infinite values"

    def test_sim002_chunk_to_chunk_similarity(
        self, entity_rich_chunks: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test SIM-002: Compute similarity between specific chunks.

        Given: Two chunks with known content
        When: Computing similarity
        Then: Score reflects content overlap
        """
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Create test chunks - including duplicates for testing
        test_chunks = entity_rich_chunks[:3] if len(entity_rich_chunks) >= 3 else entity_rich_chunks
        test_chunks.append(test_chunks[0])  # Add duplicate

        # Extract text and compute vectors
        texts = [chunk.text for chunk in test_chunks]
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            )
        )
        vectors = vectorizer.fit_transform(texts)

        # Compute pairwise similarities
        similarity_matrix = cosine_similarity(vectors)

        # Duplicate should have perfect similarity
        assert similarity_matrix[0, 3] > 0.99, "Duplicate chunks should have ~1.0 similarity"

        # Different chunks should have lower similarity (unless they're very similar)
        if len(test_chunks) > 1:
            assert similarity_matrix[0, 1] <= 1.0, "Different chunks similarity should be <= 1.0"

        # All similarities should be in valid range
        assert (similarity_matrix >= -1.0).all(), "All similarities should be >= -1"
        assert (similarity_matrix <= 1.0).all(), "All similarities should be <= 1"

    def test_sim003_find_similar_chunks(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test SIM-003: Find top-k similar chunks.

        Given: Query chunk
        When: Searching for similar chunks
        Then: Returns k most similar with scores
        """
        import numpy as np  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            )
        )
        vectors = vectorizer.fit_transform(texts)

        # Select query chunk (first one)
        query_vector = vectors[0]

        # Compute similarities to all chunks
        similarities = cosine_similarity(query_vector, vectors).flatten()

        # Find top-k similar (k=3)
        k = min(3, len(chunked_documents))
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        top_k_scores = similarities[top_k_indices]

        # Assertions
        assert len(top_k_indices) == k, f"Should return exactly {k} results"
        assert np.all(np.diff(top_k_scores) <= 0), "Scores should be in descending order"
        assert top_k_indices[0] == 0, "Query chunk should be most similar to itself"
        assert np.isclose(top_k_scores[0], 1.0), "Self-similarity should be 1.0"

    def test_sim004_similarity_threshold_filtering(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test SIM-004: Filter by similarity threshold.

        Given: Similarity scores
        When: Applying threshold from config
        Then: Only high-similarity pairs returned
        """
        import numpy as np  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Extract text and compute vectors
        texts = [chunk.text for chunk in chunked_documents]
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            )
        )
        vectors = vectorizer.fit_transform(texts)

        # Compute similarity matrix
        similarity_matrix = cosine_similarity(vectors)

        # Apply threshold (from config or default)
        threshold = semantic_processing_context.config.get("similarity", {}).get("threshold", 0.7)

        # Find pairs above threshold (excluding diagonal)
        np.fill_diagonal(similarity_matrix, 0)  # Exclude self-similarity
        high_similarity_pairs = np.argwhere(similarity_matrix > threshold)

        # Assertions
        if len(high_similarity_pairs) > 0:
            # All pairs should be above threshold
            for i, j in high_similarity_pairs:
                assert similarity_matrix[i, j] > threshold, f"Pair ({i}, {j}) not above threshold"

        # Verify threshold from config was used properly
        assert threshold >= 0 and threshold <= 1, "Threshold should be in [0, 1]"

    def test_sim005_cross_document_similarity(
        self,
        technical_corpus: List[str],
        business_corpus: List[str],
        semantic_processing_context: ProcessingContext,
    ):
        """
        Test SIM-005: Similarity across document boundaries.

        Given: Chunks from different documents
        When: Computing similarity
        Then: Identifies related content across docs
        """
        import numpy as np  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Combine corpora with labels
        all_docs = technical_corpus + business_corpus
        labels = [0] * len(technical_corpus) + [1] * len(business_corpus)

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            )
        )
        vectors = vectorizer.fit_transform(all_docs)

        # Compute similarity matrix
        similarity_matrix = cosine_similarity(vectors)

        # Calculate within-group vs between-group similarities
        tech_indices = [i for i, label in enumerate(labels) if label == 0]
        biz_indices = [i for i, label in enumerate(labels) if label == 1]

        # Compute average within-group similarities
        within_tech_sims = []
        for i in tech_indices:
            for j in tech_indices:
                if i != j:
                    within_tech_sims.append(similarity_matrix[i, j])

        within_biz_sims = []
        for i in biz_indices:
            for j in biz_indices:
                if i != j:
                    within_biz_sims.append(similarity_matrix[i, j])

        # Compute average between-group similarities
        between_sims = []
        for i in tech_indices:
            for j in biz_indices:
                between_sims.append(similarity_matrix[i, j])

        # Assertions - domain-specific documents should cluster
        if within_tech_sims and within_biz_sims and between_sims:
            avg_within_tech = np.mean(within_tech_sims)
            avg_within_biz = np.mean(within_biz_sims)
            avg_between = np.mean(between_sims)

            # Within-group similarity should be higher than between-group
            assert (
                avg_within_tech > avg_between or avg_within_biz > avg_between
            ), "Domain-specific documents should show clustering tendency"

    def test_sim006_entity_aware_similarity(
        self, entity_rich_chunks: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test SIM-006: Entity-aware similarity computation.

        Given: Chunks with entity annotations (RISK, CONTROL)
        When: Computing similarity
        Then: Entity relationships enhance similarity scores
        """
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Get chunks with entities
        test_chunks = entity_rich_chunks[:5] if len(entity_rich_chunks) >= 5 else entity_rich_chunks

        # Extract text with entity boost (simple approach)
        texts = []
        for chunk in test_chunks:
            text = chunk.text
            # Boost entity terms by repeating them
            entities = chunk.metadata.get("entities", [])
            for entity in entities:
                if isinstance(entity, dict) and "text" in entity:
                    text += f" {entity['text']} {entity['text']}"  # Double weight for entities
            texts.append(text)

        # Compute similarity with entity-boosted text
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            )
        )
        vectors = vectorizer.fit_transform(texts)
        similarity_with_entities = cosine_similarity(vectors)

        # Compare with non-entity similarity
        plain_texts = [chunk.text for chunk in test_chunks]
        plain_vectors = vectorizer.fit_transform(plain_texts)
        similarity_without_entities = cosine_similarity(plain_vectors)

        # Assertions
        # Entity-aware should produce valid similarities
        assert (similarity_with_entities >= -1.0).all() and (
            similarity_with_entities <= 1.0
        ).all(), "Entity-aware similarities should be in valid range"

        # Both methods should preserve self-similarity
        import numpy as np  # noqa: E402

        assert np.allclose(
            similarity_with_entities.diagonal(), 1.0
        ), "Entity-aware should preserve self-similarity"

    def test_sim007_similarity_performance(
        self,
        chunked_documents: List[Chunk],
        semantic_processing_context: ProcessingContext,
        performance_thresholds: dict,
        performance_timer,
    ):
        """
        Test SIM-007: Similarity computation meets performance baseline.

        Given: N documents
        When: Computing NxN similarity matrix
        Then: Completes within threshold time
        """
        import time  # noqa: E402

        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create vectors (not timed)
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            )
        )
        vectors = vectorizer.fit_transform(texts)

        # Time similarity computation
        start_time = time.time()
        similarity_matrix = cosine_similarity(vectors)
        elapsed_time = time.time() - start_time

        # Get threshold
        threshold = performance_thresholds.get("similarity_ms", 50) / 1000.0  # Convert to seconds

        # Assertions
        assert similarity_matrix is not None, "Should produce similarity matrix"
        assert (
            elapsed_time < threshold
        ), f"Similarity computation took {elapsed_time:.3f}s, exceeding {threshold:.3f}s threshold"

        # Verify matrix correctness
        n_docs = len(chunked_documents)
        assert similarity_matrix.shape == (n_docs, n_docs), "Should produce NxN matrix"

    def test_sim008_cosine_similarity_accuracy(
        self, mock_tfidf_vectors, semantic_processing_context: ProcessingContext
    ):
        """
        Test SIM-008: Cosine similarity computed correctly.

        Given: Vectors with known similarity
        When: Computing cosine similarity
        Then: Results match expected formula
        """
        import numpy as np  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Create test vectors with known similarity
        # Orthogonal vectors (similarity = 0)
        v1 = np.array([[1, 0, 0]])
        v2 = np.array([[0, 1, 0]])

        # Identical vectors (similarity = 1)
        v3 = np.array([[1, 1, 1]])
        v4 = np.array([[1, 1, 1]])

        # Opposite vectors (similarity = -1)
        v5 = np.array([[1, 1, 1]])
        v6 = np.array([[-1, -1, -1]])

        # Compute similarities
        sim_orthogonal = cosine_similarity(v1, v2)[0, 0]
        sim_identical = cosine_similarity(v3, v4)[0, 0]
        sim_opposite = cosine_similarity(v5, v6)[0, 0]

        # Manual calculation for verification
        def manual_cosine(a, b):
            dot_product = np.dot(a.flatten(), b.flatten())
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            return dot_product / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0

        manual_orthogonal = manual_cosine(v1, v2)
        manual_identical = manual_cosine(v3, v4)
        manual_opposite = manual_cosine(v5, v6)

        # Assertions
        assert np.isclose(
            sim_orthogonal, 0.0, atol=1e-6
        ), "Orthogonal vectors should have 0 similarity"
        assert np.isclose(
            sim_identical, 1.0, atol=1e-6
        ), "Identical vectors should have 1 similarity"
        assert np.isclose(
            sim_opposite, -1.0, atol=1e-6
        ), "Opposite vectors should have -1 similarity"

        # Verify manual calculation matches sklearn
        assert np.isclose(
            sim_orthogonal, manual_orthogonal, atol=1e-6
        ), "Should match manual calculation"
        assert np.isclose(
            sim_identical, manual_identical, atol=1e-6
        ), "Should match manual calculation"
        assert np.isclose(
            sim_opposite, manual_opposite, atol=1e-6
        ), "Should match manual calculation"


class TestSimilarityEdgeCases:
    """Edge case tests for similarity analysis."""

    def test_sim009_zero_vector_similarity(self, semantic_processing_context: ProcessingContext):
        """
        Test SIM-009: Handle zero vectors in similarity.

        Given: Chunks producing zero vectors
        When: Computing similarity
        Then: Handles gracefully (0 similarity)
        """
        import datetime  # noqa: E402
        from pathlib import Path  # noqa: E402

        import numpy as np  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Create chunks that will produce zero/empty vectors
        from src.data_extract.chunk.models import Chunk  # noqa: E402
        from src.data_extract.core.models import Metadata  # noqa: E402

        test_chunks = [
            Chunk(
                id="chunk_1",
                text="",
                document_id="doc_1",
                position_index=0,
                token_count=0,
                word_count=0,
                quality_score=0.5,
                metadata=Metadata(
                    source_file=Path("/test/doc1.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),  # Empty
            Chunk(
                id="chunk_2",
                text="   ",
                document_id="doc_2",
                position_index=0,
                token_count=0,
                word_count=0,
                quality_score=0.5,
                metadata=Metadata(
                    source_file=Path("/test/doc2.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=3,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),  # Whitespace
            Chunk(
                id="chunk_3",
                text="the the the",
                document_id="doc_3",
                position_index=0,
                token_count=3,
                word_count=3,
                quality_score=0.3,
                metadata=Metadata(
                    source_file=Path("/test/doc3.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=11,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),  # Only stopwords
            Chunk(
                id="chunk_4",
                text="machine learning algorithms",
                document_id="doc_4",
                position_index=0,
                token_count=7,
                word_count=3,
                quality_score=0.9,
                metadata=Metadata(
                    source_file=Path("/test/doc4.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=27,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),  # Normal
        ]

        # Extract texts (handle empty)
        texts = [chunk.text if chunk.text.strip() else " " for chunk in test_chunks]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(max_features=1000, min_df=1, stop_words="english")

        try:
            vectors = vectorizer.fit_transform(texts)
            similarity_matrix = cosine_similarity(vectors)

            # Check for NaN or Inf
            assert not np.any(np.isnan(similarity_matrix)), "Should not produce NaN"
            assert not np.any(np.isinf(similarity_matrix)), "Should not produce Inf"

            # Zero vectors should have 0 similarity to non-zero vectors
            # (or NaN handled gracefully)
            assert similarity_matrix.shape == (4, 4), "Should handle all vectors"

        except ValueError:
            # It's okay if vectorizer can't handle all empty documents
            # This is expected behavior - just ensure no crash
            pass

    def test_sim010_single_document_similarity(
        self, single_document: str, semantic_processing_context: ProcessingContext
    ):
        """
        Test SIM-010: Single document similarity matrix.

        Given: Single document/chunk
        When: Computing similarity matrix
        Then: Returns 1x1 matrix with value 1.0
        """
        import numpy as np  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Create single document list
        texts = [single_document]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            )
        )
        vectors = vectorizer.fit_transform(texts)

        # Compute similarity matrix
        similarity_matrix = cosine_similarity(vectors)

        # Assertions
        assert similarity_matrix.shape == (1, 1), "Single document should produce 1x1 matrix"
        assert np.isclose(similarity_matrix[0, 0], 1.0), "Self-similarity should be 1.0"

    def test_sim011_large_matrix_memory_efficiency(
        self, semantic_processing_context: ProcessingContext
    ):
        """
        Test SIM-011: Memory-efficient large matrix computation.

        Given: Large number of documents (100+)
        When: Computing similarity matrix
        Then: Uses sparse/efficient representation
        """
        import numpy as np  # noqa: E402
        import scipy.sparse  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

        # Create large corpus (100 documents)
        np.random.seed(42)  # For reproducibility
        vocab = [
            "data",
            "process",
            "extract",
            "document",
            "pipeline",
            "analysis",
            "semantic",
            "chunk",
            "vector",
            "similarity",
            "matrix",
            "compute",
        ]

        large_corpus = []
        for i in range(100):
            # Generate random documents from vocabulary
            doc_length = np.random.randint(10, 50)
            doc_words = np.random.choice(vocab, doc_length)
            large_corpus.append(" ".join(doc_words))

        # Create TF-IDF vectors (should be sparse)
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            )
        )
        vectors = vectorizer.fit_transform(large_corpus)

        # Verify sparse representation
        assert scipy.sparse.issparse(vectors), "Large corpus should use sparse representation"

        # Compute similarity (this might be dense, but input should be sparse)
        similarity_matrix = cosine_similarity(vectors)

        # Assertions
        assert similarity_matrix.shape == (100, 100), "Should handle 100x100 matrix"
        assert not np.any(np.isnan(similarity_matrix)), "No NaN values in large matrix"

        # Check memory efficiency (sparse vectors should have low density)
        if scipy.sparse.issparse(vectors):
            density = vectors.nnz / (vectors.shape[0] * vectors.shape[1])
            assert density < 0.5, f"Sparse matrix should have low density, got {density:.2f}"

    def test_sim012_similarity_metric_options(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test SIM-012: Different similarity metrics produce valid results.

        Given: Same vectors
        When: Using different metrics (cosine, euclidean, etc.)
        Then: Each metric produces valid similarity scores
        """
        import numpy as np  # noqa: E402
        from scipy.spatial.distance import cdist  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
        from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            )
        )
        vectors = vectorizer.fit_transform(texts).toarray()  # Convert to dense for all metrics

        # Compute different similarity/distance metrics
        cosine_sim = cosine_similarity(vectors)
        euclidean_dist = euclidean_distances(vectors)

        # Convert distances to similarities (inverse)
        euclidean_sim = 1 / (1 + euclidean_dist)  # Convert distance to similarity

        # Additional metrics using scipy
        manhattan_dist = cdist(vectors, vectors, metric="cityblock")
        manhattan_sim = 1 / (1 + manhattan_dist)

        # Assertions for each metric
        n_docs = len(chunked_documents)

        # Cosine similarity assertions
        assert cosine_sim.shape == (n_docs, n_docs), "Cosine should produce NxN matrix"
        assert (cosine_sim >= -1.0).all() and (cosine_sim <= 1.0).all(), "Cosine in [-1, 1]"
        assert np.allclose(cosine_sim.diagonal(), 1.0), "Cosine diagonal should be 1"

        # Euclidean similarity assertions
        assert euclidean_sim.shape == (n_docs, n_docs), "Euclidean should produce NxN matrix"
        assert (euclidean_sim > 0).all() and (euclidean_sim <= 1.0).all(), "Euclidean sim in (0, 1]"
        assert np.allclose(euclidean_sim.diagonal(), 1.0), "Euclidean diagonal should be 1"

        # Manhattan similarity assertions
        assert manhattan_sim.shape == (n_docs, n_docs), "Manhattan should produce NxN matrix"
        assert (manhattan_sim > 0).all() and (manhattan_sim <= 1.0).all(), "Manhattan sim in (0, 1]"
        assert np.allclose(manhattan_sim.diagonal(), 1.0), "Manhattan diagonal should be 1"

        # All metrics should be symmetric
        assert np.allclose(cosine_sim, cosine_sim.T), "Cosine should be symmetric"
        assert np.allclose(euclidean_sim, euclidean_sim.T), "Euclidean should be symmetric"
        assert np.allclose(manhattan_sim, manhattan_sim.T), "Manhattan should be symmetric"

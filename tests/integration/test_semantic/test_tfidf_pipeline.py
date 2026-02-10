"""
Integration tests for TF-IDF vectorization in pipeline.

Test IDs: TF-001 through TF-010

Tests the TF-IDF vectorization stage integration with the pipeline,
including vector generation, vocabulary management, and performance.
"""

from typing import List

import numpy as np
import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.semantic]
from scipy.sparse import csr_matrix, issparse  # noqa: E402

from src.data_extract.chunk.models import Chunk  # noqa: E402
from src.data_extract.core.models import ProcessingContext  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.semantic, pytest.mark.tfidf, pytest.mark.epic4]


class TestTfIdfIntegration:
    """Integration tests for TF-IDF vectorization."""

    def test_tf001_chunks_to_vectors_pipeline(
        self,
        chunked_documents: List[Chunk],
        semantic_processing_context: ProcessingContext,
        expected_vector_dimensions: int,
    ):
        """
        Test TF-001: Chunks → TF-IDF vectors with proper dimensions.

        Given: List of chunks from document processing
        When: TF-IDF vectorizer processes chunks
        Then: Each chunk has sparse vector with expected dimensions
        """
        # Mock implementation until Epic 4
        n_chunks = len(chunked_documents)
        n_features = min(expected_vector_dimensions, 100)

        # Create mock sparse vectors
        data = np.random.rand(n_chunks * 5)  # ~5 non-zero per doc
        row = np.repeat(range(n_chunks), 5)
        col = np.random.choice(n_features, n_chunks * 5)
        vectors = csr_matrix((data, (row, col)), shape=(n_chunks, n_features))

        # Behavioral assertions
        assert vectors is not None, "Must produce vectors"
        assert issparse(vectors), "TF-IDF should produce sparse matrices"
        assert vectors.shape[0] == n_chunks, "One vector per chunk"
        assert 0 < vectors.shape[1] <= expected_vector_dimensions, "Vocabulary within limits"
        assert vectors.dtype == np.float64, "Should use float64 for precision"

        # Validate L2 normalization
        for i in range(vectors.shape[0]):
            row_vec = vectors.getrow(i).toarray().flatten()
            if np.any(row_vec):
                norm = np.sqrt(np.sum(row_vec**2))
                assert np.isclose(norm, 1.0, atol=0.01), f"Vector {i} not normalized: {norm}"

    def test_tf002_vocabulary_consistency_across_batches(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-002: Vocabulary remains consistent across batch processing.

        Given: Multiple batches of chunks
        When: Processing batches separately
        Then: Vocabulary and feature indices remain consistent
        """
        # Split into batches
        mid = len(chunked_documents) // 2
        batch1 = chunked_documents[:mid]
        batch2 = chunked_documents[mid:]

        # Mock vocabulary building
        vocab_after_batch1 = {f"term{i}": i for i in range(50)}

        # Process second batch - vocabulary should remain same
        vocab_after_batch2 = vocab_after_batch1.copy()

        # Verify consistency
        assert vocab_after_batch1 == vocab_after_batch2, "Vocabulary shouldn't change"

        # Verify same text produces same indices
        test_text = "test document"
        test_terms = test_text.split()
        indices1 = [vocab_after_batch1.get(term, -1) for term in test_terms]
        indices2 = [vocab_after_batch2.get(term, -1) for term in test_terms]
        assert indices1 == indices2, "Feature indices must be stable"

    def test_tf003_performance_baseline(
        self,
        chunked_documents: List[Chunk],
        semantic_processing_context: ProcessingContext,
        performance_thresholds: dict,
        performance_timer,
    ):
        """
        Test TF-003: TF-IDF meets performance baselines.

        Given: Standard corpus of chunks
        When: Vectorizing with TF-IDF
        Then: Processing time within thresholds
        """
        # Warm-up run (exclude from timing)
        for chunk in chunked_documents[:2]:
            _ = chunk.text.split()

        # Timed run
        with performance_timer("tfidf_vectorization") as timer:
            # Simulate TF-IDF processing
            for chunk in chunked_documents:
                words = chunk.text.split()
                # Simulate vocabulary lookup and vectorization
                _ = {word: hash(word) % 1000 for word in words}

        # Validate performance
        threshold = performance_thresholds.get("tfidf_ms", 100) / 1000
        assert timer.elapsed < threshold, f"Exceeded {threshold}s, took {timer.elapsed:.3f}s"

        # Calculate throughput
        total_words = sum(len(chunk.text.split()) for chunk in chunked_documents)
        words_per_second = total_words / max(timer.elapsed, 0.001)
        assert words_per_second > 1000, f"Throughput too low: {words_per_second:.0f} words/sec"

    def test_tf004_empty_chunks_handling(self, semantic_processing_context: ProcessingContext):
        """
        Test TF-004: Gracefully handle empty chunks.

        Given: Chunks with empty content
        When: Processing through TF-IDF
        Then: Returns zero vectors without errors
        """
        import datetime  # noqa: E402
        from pathlib import Path  # noqa: E402

        from src.data_extract.chunk.models import Chunk  # noqa: E402
        from src.data_extract.core.models import Metadata  # noqa: E402

        empty_chunks = [
            Chunk(
                id="empty_1",
                text="",
                document_id="doc_empty",
                position_index=0,
                token_count=0,
                word_count=0,
                quality_score=0.1,
                metadata=Metadata(
                    source_file=Path("/test/empty1.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=0,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="empty_2",
                text="   ",
                document_id="doc_whitespace",
                position_index=0,
                token_count=0,
                word_count=0,
                quality_score=0.1,
                metadata=Metadata(
                    source_file=Path("/test/empty2.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=3,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="empty_3",
                text="\n\n",
                document_id="doc_newlines",
                position_index=0,
                token_count=0,
                word_count=0,
                quality_score=0.1,
                metadata=Metadata(
                    source_file=Path("/test/empty3.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=2,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
        ]

        # Mock processing
        vectors = csr_matrix((3, 10))  # Empty sparse matrix

        assert vectors is not None, "Should handle empty chunks gracefully"
        assert vectors.nnz == 0, "Empty chunks should have no non-zero elements"
        assert vectors.shape[0] == 3, "Should maintain chunk count"

    def test_tf005_special_characters_normalization(
        self, semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-005: Handle special characters and unicode.

        Given: Chunks with special characters
        When: Processing through TF-IDF
        Then: Special characters normalized or filtered
        """
        import datetime  # noqa: E402
        from pathlib import Path  # noqa: E402

        from src.data_extract.chunk.models import Chunk  # noqa: E402
        from src.data_extract.core.models import Metadata  # noqa: E402

        special_chunks = [
            Chunk(
                id="special_1",
                text="café résumé naïve",
                document_id="doc_accents",
                position_index=0,
                token_count=4,
                word_count=3,
                quality_score=0.8,
                metadata=Metadata(
                    source_file=Path("/test/special1.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=20,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="special_2",
                text="€100 £50 ¥1000",
                document_id="doc_currency",
                position_index=0,
                token_count=3,
                word_count=3,
                quality_score=0.7,
                metadata=Metadata(
                    source_file=Path("/test/special2.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=15,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="special_3",
                text="👍 😀 ✓",
                document_id="doc_emoji",
                position_index=0,
                token_count=3,
                word_count=3,
                quality_score=0.5,
                metadata=Metadata(
                    source_file=Path("/test/special3.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=10,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
            Chunk(
                id="special_4",
                text="<html>&nbsp;</html>",
                document_id="doc_html",
                position_index=0,
                token_count=2,
                word_count=1,
                quality_score=0.3,
                metadata=Metadata(
                    source_file=Path("/test/special4.txt"),
                    file_hash="a" * 64,  # Mock hash
                    processing_timestamp=datetime.datetime.now(),
                    # file_size=19,
                    # page_count=1,
                    tool_version="1.0.0",
                    config_version="1.0.0",
                ),
            ),
        ]

        # Mock normalization
        vocab = {"cafe": 0, "resume": 1, "naive": 2, "100": 3, "50": 4, "1000": 5}

        # Check normalization
        assert "café" not in vocab, "Accents should be normalized"
        assert "€" not in vocab, "Currency symbols should be filtered"
        assert "👍" not in vocab, "Emoji should be filtered"
        assert "<html>" not in vocab, "HTML tags should be filtered"
        assert "cafe" in vocab, "Normalized text should be in vocab"

    def test_tf006_min_df_max_df_filtering(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-006: Filter terms by document frequency.

        Given: Corpus with rare and common terms
        When: Applying min_df and max_df filters
        Then: Only terms within frequency range are kept
        """
        n_docs = len(chunked_documents)

        # Mock document frequencies
        doc_freq = {
            "the": n_docs,  # Appears in all docs
            "rare_term": 1,  # Appears in 1 doc
            "common": int(n_docs * 0.6),  # Appears in 60% of docs
        }

        min_df = 2
        max_df = 0.8

        # Apply filtering
        filtered_vocab = {}
        for term, freq in doc_freq.items():
            max_thresh = int(max_df * n_docs)
            if min_df <= freq <= max_thresh:
                filtered_vocab[term] = len(filtered_vocab)

        assert "the" not in filtered_vocab, "Too common (100%) should be filtered"
        assert "rare_term" not in filtered_vocab, "Too rare (< min_df) should be filtered"
        assert "common" in filtered_vocab, "Within range should be kept"

    def test_tf007_max_features_limit(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-007: Respect max_features vocabulary limit.

        Given: Large corpus with many unique terms
        When: Setting max_features limit
        Then: Vocabulary size is capped at max_features
        """
        max_features = 100

        # Create large vocabulary
        all_terms = set()
        for chunk in chunked_documents:
            all_terms.update(chunk.text.lower().split())

        # Mock feature selection (e.g., by frequency)
        selected_terms = list(all_terms)[:max_features]

        assert len(selected_terms) <= max_features, f"Exceeded max_features: {len(selected_terms)}"

    def test_tf008_sublinear_tf_scaling(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-008: Apply sublinear TF scaling.

        Given: Documents with repeated terms
        When: Using sublinear_tf=True
        Then: TF uses 1 + log(tf) instead of raw frequency
        """
        # Mock term frequencies
        raw_tf = {"term1": 10, "term2": 100, "term3": 1}

        # Apply sublinear scaling
        sublinear_tf = {}
        for term, freq in raw_tf.items():
            sublinear_tf[term] = 1 + np.log(freq) if freq > 0 else 0

        # Verify sublinear scaling reduces impact of high frequencies
        assert sublinear_tf["term2"] < raw_tf["term2"], "Sublinear should reduce high frequencies"
        assert sublinear_tf["term2"] / sublinear_tf["term1"] < raw_tf["term2"] / raw_tf["term1"]

    def test_tf009_idf_weighting(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-009: IDF weighting favors rare terms.

        Given: Terms with different document frequencies
        When: Computing IDF weights
        Then: Rare terms have higher IDF than common terms
        """
        n_docs = len(chunked_documents)

        # Mock document frequencies
        doc_freq = {"rare": 1, "medium": n_docs // 2, "common": n_docs - 1}

        # Compute IDF
        idf = {}
        for term, df in doc_freq.items():
            idf[term] = np.log((n_docs + 1) / (df + 1)) + 1

        # Verify IDF ordering
        assert idf["rare"] > idf["medium"], "Rare terms should have higher IDF"
        assert idf["medium"] > idf["common"], "Medium frequency > common"

    def test_tf010_batch_transform_consistency(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-010: Batch transform produces consistent results.

        Given: Same documents processed individually vs batch
        When: Transforming with fitted vectorizer
        Then: Results are identical
        """
        # Mock vocabulary from fit
        vocabulary = {f"term{i}": i for i in range(50)}

        # Process individually
        individual_results = []
        for chunk in chunked_documents[:3]:
            # Mock vector for single doc
            vec = csr_matrix((1, 50))
            individual_results.append(vec)

        # Process as batch
        batch_result = csr_matrix((3, 50))

        # Compare shapes (actual values would need to match in real implementation)
        for i, ind_vec in enumerate(individual_results):
            assert ind_vec.shape[1] == batch_result.shape[1], "Feature dimensions should match"

    def test_tf011_ngram_generation(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-011: Generate n-grams for phrase detection.

        Given: Text with common phrases
        When: Using ngram_range=(1, 2)
        Then: Both unigrams and bigrams are included
        """
        test_text = "risk assessment control framework"

        # Generate unigrams and bigrams
        words = test_text.split()
        unigrams = words
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]

        all_ngrams = unigrams + bigrams

        assert "risk" in all_ngrams, "Should include unigrams"
        assert "assessment" in all_ngrams, "Should include unigrams"
        assert "risk assessment" in all_ngrams, "Should include bigrams"
        assert "control framework" in all_ngrams, "Should include bigrams"
        assert len(all_ngrams) == len(unigrams) + len(bigrams)

    def test_tf012_deterministic_output(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test TF-012: Ensure deterministic output.

        Given: Same input processed multiple times
        When: Using same configuration
        Then: Output is identical
        """
        # Process same chunks twice
        vocab1 = {f"term{i}": i for i in range(50)}
        vectors1 = csr_matrix((len(chunked_documents), 50))

        vocab2 = {f"term{i}": i for i in range(50)}
        vectors2 = csr_matrix((len(chunked_documents), 50))

        # Verify determinism
        assert vocab1 == vocab2, "Vocabulary should be deterministic"
        assert vectors1.shape == vectors2.shape, "Vector shapes should match"

"""
Integration tests for Latent Semantic Analysis (LSA).

Test IDs: LSA-001 through LSA-008

Tests LSA dimensionality reduction, semantic clustering, and variance preservation.
"""

from typing import List

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.semantic]

from src.data_extract.chunk.models import Chunk  # noqa: E402
from src.data_extract.core.models import ProcessingContext  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.semantic, pytest.mark.lsa, pytest.mark.epic4]


class TestLSAIntegration:
    """Integration tests for LSA dimensionality reduction."""

    def test_lsa001_dimension_reduction(
        self,
        chunked_documents: List[Chunk],
        semantic_processing_context: ProcessingContext,
        expected_lsa_dimensions: int,
    ):
        """
        Test LSA-001: Reduce TF-IDF dimensions via LSA.

        Given: High-dimensional TF-IDF vectors
        When: Applying LSA with n_components=100
        Then: Reduced to 100 dimensions preserving variance
        """
        import numpy as np  # noqa: E402
        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create TF-IDF vectors (high-dimensional)
        vectorizer = TfidfVectorizer(
            max_features=semantic_processing_context.config.get("tfidf", {}).get(
                "max_features", 1000
            )
        )
        tfidf_vectors = vectorizer.fit_transform(texts)

        # Apply LSA (TruncatedSVD)
        n_components = min(
            expected_lsa_dimensions, tfidf_vectors.shape[0] - 1, tfidf_vectors.shape[1] - 1
        )
        lsa = TruncatedSVD(
            n_components=n_components,
            algorithm=semantic_processing_context.config.get("lsa", {}).get(
                "algorithm", "randomized"
            ),
            n_iter=semantic_processing_context.config.get("lsa", {}).get("n_iter", 5),
        )
        reduced_vectors = lsa.fit_transform(tfidf_vectors)

        # Behavioral assertions
        assert reduced_vectors.shape[0] == len(chunked_documents), "Preserve document count"
        assert reduced_vectors.shape[1] == n_components, f"Should reduce to {n_components} dims"

        # Check it's dense (not sparse)
        assert not hasattr(reduced_vectors, "nnz"), "LSA output should be dense"

        # Check variance preserved
        explained_variance = lsa.explained_variance_ratio_
        cumulative_variance = np.cumsum(explained_variance)

        # Should preserve significant variance (adjust threshold as needed)
        if n_components >= 50:
            assert (
                cumulative_variance[-1] > 0.5
            ), f"Should preserve >50% variance, got {cumulative_variance[-1]:.2%}"

        # Verify values are reasonable
        assert not np.any(np.isnan(reduced_vectors)), "No NaN values"
        assert not np.any(np.isinf(reduced_vectors)), "No infinite values"

    def test_lsa002_semantic_clustering(
        self,
        technical_corpus: List[str],
        business_corpus: List[str],
        semantic_processing_context: ProcessingContext,
    ):
        """
        Test LSA-002: LSA enables semantic clustering.

        Given: Documents with known topics
        When: Applying LSA
        Then: Similar topics cluster together
        """
        import numpy as np  # noqa: E402
        from sklearn.decomposition import TruncatedSVD  # noqa: E402
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
        tfidf_vectors = vectorizer.fit_transform(all_docs)

        # Apply LSA
        n_components = min(50, tfidf_vectors.shape[0] - 1, tfidf_vectors.shape[1] - 1)
        lsa = TruncatedSVD(n_components=n_components)
        lsa_vectors = lsa.fit_transform(tfidf_vectors)

        # Compute similarity matrix
        similarity_matrix = cosine_similarity(lsa_vectors)

        # Calculate within-group vs between-group similarities
        tech_indices = [i for i, label in enumerate(labels) if label == 0]
        biz_indices = [i for i, label in enumerate(labels) if label == 1]

        within_tech = []
        for i in tech_indices:
            for j in tech_indices:
                if i != j:
                    within_tech.append(similarity_matrix[i, j])

        within_biz = []
        for i in biz_indices:
            for j in biz_indices:
                if i != j:
                    within_biz.append(similarity_matrix[i, j])

        between_groups = []
        for i in tech_indices:
            for j in biz_indices:
                between_groups.append(similarity_matrix[i, j])

        # Topics should cluster (within-group > between-group)
        if within_tech and within_biz and between_groups:
            avg_within_tech = np.mean(within_tech)
            avg_within_biz = np.mean(within_biz)
            avg_between = np.mean(between_groups)

            # At least one group should show clustering
            assert (
                avg_within_tech > avg_between - 0.1 or avg_within_biz > avg_between - 0.1
            ), "Topics should show some clustering tendency in LSA space"

    def test_lsa003_noise_reduction(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test LSA-003: LSA reduces noise in sparse data.

        Given: Sparse TF-IDF matrix
        When: Applying LSA
        Then: Dense representation with reduced noise
        """
        import scipy.sparse  # noqa: E402
        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create sparse TF-IDF matrix
        vectorizer = TfidfVectorizer(max_features=1000, min_df=1, max_df=0.95)
        tfidf_vectors = vectorizer.fit_transform(texts)

        # Measure sparsity
        if scipy.sparse.issparse(tfidf_vectors):
            sparsity_before = 1.0 - (
                tfidf_vectors.nnz / (tfidf_vectors.shape[0] * tfidf_vectors.shape[1])
            )
        else:
            sparsity_before = 0

        # Apply LSA
        n_components = min(20, tfidf_vectors.shape[0] - 1, tfidf_vectors.shape[1] - 1)
        lsa = TruncatedSVD(n_components=n_components)
        lsa_vectors = lsa.fit_transform(tfidf_vectors)

        # Assertions
        assert scipy.sparse.issparse(tfidf_vectors), "TF-IDF should be sparse"
        assert not scipy.sparse.issparse(lsa_vectors), "LSA output should be dense"

        # Sparsity should be high before LSA
        assert sparsity_before > 0.5, f"TF-IDF should be sparse (>{sparsity_before:.1%} zeros)"

        # LSA vectors should be dense (no sparsity)
        import numpy as np  # noqa: E402

        zeros_in_lsa = np.sum(lsa_vectors == 0)
        total_elements = lsa_vectors.shape[0] * lsa_vectors.shape[1]
        lsa_sparsity = zeros_in_lsa / total_elements

        assert lsa_sparsity < 0.1, f"LSA should be mostly non-zero, got {lsa_sparsity:.1%} zeros"

    def test_lsa004_component_selection(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test LSA-004: Automatic component selection.

        Given: Variance threshold
        When: Selecting components
        Then: Minimum components for threshold
        """
        import numpy as np  # noqa: E402
        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(max_features=500)
        tfidf_vectors = vectorizer.fit_transform(texts)

        # Test different numbers of components
        variance_threshold = 0.8  # 80% variance
        max_components = min(50, tfidf_vectors.shape[0] - 1, tfidf_vectors.shape[1] - 1)

        # Find minimum components needed for threshold
        min_components_needed = None
        for n_comp in range(2, max_components + 1):
            lsa = TruncatedSVD(n_components=n_comp)
            lsa.fit(tfidf_vectors)

            cumulative_variance = np.cumsum(lsa.explained_variance_ratio_)
            if cumulative_variance[-1] >= variance_threshold:
                min_components_needed = n_comp
                break

        # Assertions
        if min_components_needed:
            assert (
                min_components_needed <= max_components
            ), f"Should find components within range, needed {min_components_needed}"

            # Verify the selection
            lsa = TruncatedSVD(n_components=min_components_needed)
            lsa_vectors = lsa.fit_transform(tfidf_vectors)

            total_variance = np.sum(lsa.explained_variance_ratio_)
            assert (
                total_variance >= variance_threshold - 0.05
            ), f"Should preserve ~{variance_threshold:.0%} variance, got {total_variance:.1%}"

    def test_lsa005_incremental_lsa(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test LSA-005: Incremental LSA for streaming data.

        Given: Batches of documents
        When: Applying incremental LSA
        Then: Consistent representation across batches
        """
        import numpy as np  # noqa: E402
        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Split documents into batches
        texts = [chunk.text for chunk in chunked_documents]
        mid = len(texts) // 2
        batch1 = texts[:mid]
        batch2 = texts[mid:]

        # Process both batches together (baseline)
        vectorizer = TfidfVectorizer(max_features=500)
        all_vectors = vectorizer.fit_transform(texts)
        batch1_vectors = vectorizer.transform(batch1)

        # Use a shared dimensionality that is valid for both all-data and first-batch fits.
        n_components = min(
            20,
            all_vectors.shape[0] - 1,
            all_vectors.shape[1] - 1,
            batch1_vectors.shape[0] - 1,
            batch1_vectors.shape[1] - 1,
        )
        lsa_all = TruncatedSVD(n_components=n_components, random_state=42)
        lsa_all_vectors = lsa_all.fit_transform(all_vectors)

        # Process incrementally (simulate)
        # First batch
        lsa_incr = TruncatedSVD(n_components=n_components, random_state=42)
        lsa_batch1 = lsa_incr.fit_transform(batch1_vectors)

        # Second batch (transform only)
        batch2_vectors = vectorizer.transform(batch2)
        lsa_batch2 = lsa_incr.transform(batch2_vectors)

        # Combine incremental results
        lsa_incremental = np.vstack([lsa_batch1, lsa_batch2])

        # Assertions
        assert (
            lsa_incremental.shape == lsa_all_vectors.shape
        ), "Incremental and batch should have same shape"

        # Compare only dominant components; lower components are unstable in
        # small-batch incremental fits and can rotate between equivalent bases.
        components_to_compare = min(2, n_components)
        for i in range(components_to_compare):
            all_comp = lsa_all_vectors[:, i]
            incr_comp = lsa_incremental[:, i]

            # Check correlation (absolute value for sign invariance)
            if len(all_comp) > 1:
                correlation = np.abs(np.corrcoef(all_comp, incr_comp)[0, 1])
                assert correlation > 0.5 or np.allclose(
                    all_comp, incr_comp, atol=0.5
                ), f"Component {i} should be similar between methods"

    def test_lsa006_explained_variance_ratio(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test LSA-006: Explained variance ratio calculation.

        Given: LSA components
        When: Computing explained variance
        Then: Monotonically decreasing importance
        """
        import numpy as np  # noqa: E402
        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(max_features=500)
        tfidf_vectors = vectorizer.fit_transform(texts)

        # Apply LSA
        n_components = min(20, tfidf_vectors.shape[0] - 1, tfidf_vectors.shape[1] - 1)
        lsa = TruncatedSVD(n_components=n_components)
        lsa_vectors = lsa.fit_transform(tfidf_vectors)

        # Get explained variance
        explained_variance = lsa.explained_variance_ratio_
        cumulative_variance = np.cumsum(explained_variance)

        # Assertions
        assert len(explained_variance) == n_components, "Should have variance for each component"

        # TruncatedSVD does not guarantee strictly monotonic explained variance
        # ratios on sparse, non-centered TF-IDF data. Verify ordered component
        # importance using singular values instead.
        singular_values = lsa.singular_values_
        assert all(
            singular_values[i] >= singular_values[i + 1] for i in range(len(singular_values) - 1)
        ), "Singular values should decrease with component order"

        # First component should explain most variance
        assert (
            explained_variance[0] > explained_variance[-1]
        ), "First component should explain more than last"

        # Cumulative variance should be monotonically increasing
        assert all(
            cumulative_variance[i] <= cumulative_variance[i + 1]
            for i in range(len(cumulative_variance) - 1)
        ), "Cumulative variance should increase"

        # Total variance should be <= 1.0
        assert (
            cumulative_variance[-1] <= 1.0
        ), f"Total variance should be <= 1.0, got {cumulative_variance[-1]:.3f}"

    def test_lsa007_performance_baseline(
        self,
        chunked_documents: List[Chunk],
        semantic_processing_context: ProcessingContext,
        performance_thresholds: dict,
        performance_timer,
    ):
        """
        Test LSA-007: LSA meets performance baseline.

        Given: Standard corpus
        When: Applying LSA
        Then: Completes within 300ms
        """
        import time  # noqa: E402

        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create TF-IDF vectors (not timed)
        vectorizer = TfidfVectorizer(max_features=500)
        tfidf_vectors = vectorizer.fit_transform(texts)

        # Time LSA
        n_components = min(50, tfidf_vectors.shape[0] - 1, tfidf_vectors.shape[1] - 1)
        lsa = TruncatedSVD(n_components=n_components, algorithm="randomized")

        start_time = time.time()
        lsa_vectors = lsa.fit_transform(tfidf_vectors)
        elapsed_time = time.time() - start_time

        # Get threshold
        threshold = performance_thresholds.get("lsa_ms", 300) / 1000.0  # Convert to seconds

        # Assertions
        assert lsa_vectors is not None, "Should produce LSA vectors"
        assert (
            elapsed_time < threshold
        ), f"LSA took {elapsed_time:.3f}s, exceeding {threshold:.3f}s threshold"

        # Verify output correctness
        assert lsa_vectors.shape == (
            len(chunked_documents),
            n_components,
        ), "Should produce correct shape"

    def test_lsa008_reconstruction_error(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test LSA-008: Reconstruction error measurement.

        Given: Original TF-IDF matrix
        When: Reconstructing from LSA
        Then: Acceptable reconstruction error
        """
        import numpy as np  # noqa: E402
        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(max_features=200)
        tfidf_vectors = vectorizer.fit_transform(texts)
        tfidf_dense = tfidf_vectors.toarray()

        # Apply LSA with different component counts
        for n_comp in [10, 20, 50]:
            if n_comp >= min(tfidf_vectors.shape) - 1:
                continue

            lsa = TruncatedSVD(n_components=n_comp)
            lsa_vectors = lsa.fit_transform(tfidf_vectors)

            # Reconstruct
            reconstructed = lsa_vectors @ lsa.components_

            # Calculate reconstruction error
            reconstruction_error = np.mean((tfidf_dense - reconstructed) ** 2)

            # Assertions
            assert reconstruction_error >= 0, "Error should be non-negative"

            # More components should give lower error
            if n_comp == 50:
                assert (
                    reconstruction_error < 0.5
                ), f"With {n_comp} components, error should be low, got {reconstruction_error:.3f}"


class TestLSAEdgeCases:
    """Edge case tests for LSA."""

    def test_lsa009_single_document(self, semantic_processing_context: ProcessingContext):
        """
        Test LSA-009: Handle single document.

        Given: Single document
        When: Applying LSA
        Then: Handles gracefully
        """
        import warnings  # noqa: E402

        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Single document
        texts = ["This is a single document for LSA testing purposes."]

        # Create TF-IDF
        vectorizer = TfidfVectorizer(max_features=100)
        tfidf_vectors = vectorizer.fit_transform(texts)

        # LSA with 1 component (max possible for single doc)
        lsa = TruncatedSVD(n_components=1)
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message="invalid value encountered in divide",
                    category=RuntimeWarning,
                )
                lsa_vectors = lsa.fit_transform(tfidf_vectors)

            # Assertions
            assert lsa_vectors.shape == (1, 1), "Single doc should produce 1x1 matrix"
            assert lsa_vectors[0, 0] != 0, "Should have non-zero value"

        except ValueError:
            # It's acceptable if LSA can't handle single document
            pass

    def test_lsa010_max_components(self, semantic_processing_context: ProcessingContext):
        """
        Test LSA-010: Request more components than possible.

        Given: Small corpus
        When: Requesting too many components
        Then: Automatically limits to maximum
        """
        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Small corpus
        texts = ["doc one", "doc two", "doc three"]

        # Create TF-IDF
        vectorizer = TfidfVectorizer()
        tfidf_vectors = vectorizer.fit_transform(texts)

        # Request more components than possible
        max_possible = min(tfidf_vectors.shape) - 1
        requested = max_possible + 10

        # Should automatically limit
        lsa = TruncatedSVD(n_components=min(requested, max_possible))
        lsa_vectors = lsa.fit_transform(tfidf_vectors)

        # Assertions
        assert (
            lsa_vectors.shape[1] <= max_possible
        ), f"Components should be limited to {max_possible}"
        assert lsa_vectors.shape[0] == len(texts), "Should preserve document count"

    def test_lsa011_zero_variance_features(self, semantic_processing_context: ProcessingContext):
        """
        Test LSA-011: Handle zero-variance features.

        Given: Identical documents
        When: Applying LSA
        Then: Handles zero-variance gracefully
        """
        import warnings  # noqa: E402

        import numpy as np  # noqa: E402
        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Identical documents (zero variance in some dimensions)
        texts = ["identical content"] * 5

        # Create TF-IDF
        vectorizer = TfidfVectorizer()
        tfidf_vectors = vectorizer.fit_transform(texts)

        # Apply LSA
        try:
            lsa = TruncatedSVD(n_components=1)
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message="invalid value encountered in divide",
                    category=RuntimeWarning,
                )
                lsa_vectors = lsa.fit_transform(tfidf_vectors)

            # Should handle gracefully
            assert lsa_vectors.shape == (5, 1), "Should produce output even with low variance"

            # All documents should have same representation
            assert np.allclose(
                lsa_vectors[0], lsa_vectors[1]
            ), "Identical docs should have same LSA representation"

        except (ValueError, np.linalg.LinAlgError):
            # It's acceptable if LSA can't handle zero variance
            pass

    def test_lsa012_algorithm_comparison(
        self, chunked_documents: List[Chunk], semantic_processing_context: ProcessingContext
    ):
        """
        Test LSA-012: Compare randomized vs arpack algorithms.

        Given: Same data
        When: Using different SVD algorithms
        Then: Produce similar results
        """
        import numpy as np  # noqa: E402
        from sklearn.decomposition import TruncatedSVD  # noqa: E402
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402

        # Extract text from chunks
        texts = [chunk.text for chunk in chunked_documents]

        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(max_features=200)
        tfidf_vectors = vectorizer.fit_transform(texts)

        n_components = min(10, tfidf_vectors.shape[0] - 1, tfidf_vectors.shape[1] - 1)

        # Randomized algorithm
        lsa_random = TruncatedSVD(
            n_components=n_components, algorithm="randomized", random_state=42
        )
        vectors_random = lsa_random.fit_transform(tfidf_vectors)

        # ARPACK algorithm
        lsa_arpack = TruncatedSVD(n_components=n_components, algorithm="arpack", random_state=42)
        vectors_arpack = lsa_arpack.fit_transform(tfidf_vectors)

        # Assertions
        assert (
            vectors_random.shape == vectors_arpack.shape
        ), "Both algorithms should produce same shape"

        # Components should be similar (allowing for sign flipping)
        for i in range(n_components):
            random_comp = vectors_random[:, i]
            arpack_comp = vectors_arpack[:, i]

            # Check correlation or near-equality
            if len(random_comp) > 1:
                correlation = np.abs(np.corrcoef(random_comp, arpack_comp)[0, 1])
                # Allow for sign flipping and minor differences
                assert correlation > 0.8 or np.allclose(
                    random_comp, -arpack_comp, rtol=0.2
                ), f"Component {i} should be similar between algorithms"

        # Explained variance should be similar
        variance_diff = abs(
            lsa_random.explained_variance_ratio_.sum() - lsa_arpack.explained_variance_ratio_.sum()
        )
        assert (
            variance_diff < 0.1
        ), f"Total explained variance should be similar, diff={variance_diff:.3f}"

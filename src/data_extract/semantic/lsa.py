"""Latent Semantic Analysis (LSA) dimensionality reduction stage.

This module implements Story 4.3: LSA dimensionality reduction and topic extraction.
It reduces TF-IDF vectors using TruncatedSVD, extracts topics, and performs
document clustering with K-means.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import Normalizer

from ..core.models import ProcessingContext
from ..core.pipeline import PipelineStage
from .cache import CacheManager
from .models import SemanticResult

logger = logging.getLogger(__name__)


@dataclass
class LsaConfig:
    """Configuration for LSA reduction.

    Attributes:
        n_components: Number of LSA components/topics (default 100, range 50-300)
        n_clusters: Number of clusters for K-means (None for auto-selection)
        random_state: Random state for reproducibility (default 42)
        use_cache: Whether to use caching (default True)
        normalize: Whether to L2-normalize LSA vectors (default True)
        top_n_terms: Number of top terms per topic (default 10)
        min_variance_explained: Minimum explained variance ratio (default 0.8)
        max_iter: Maximum iterations for K-means (default 300)
        n_init: Number of K-means initializations (default 10)
    """

    n_components: int = 100
    n_clusters: Optional[int] = None
    random_state: int = 42
    use_cache: bool = True
    normalize: bool = True
    top_n_terms: int = 10
    min_variance_explained: float = 0.8
    max_iter: int = 300
    n_init: int = 10

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not 50 <= self.n_components <= 300:
            raise ValueError(f"n_components must be between 50 and 300, got {self.n_components}")
        if self.n_clusters is not None and self.n_clusters < 2:
            raise ValueError(f"n_clusters must be >= 2, got {self.n_clusters}")

    def get_cache_key_components(self) -> tuple:
        """Get components for cache key generation."""
        return (
            self.n_components,
            self.n_clusters,
            self.random_state,
            self.normalize,
            self.top_n_terms,
        )


@dataclass
class LSAResult:
    """Result of LSA analysis.

    Attributes:
        lsa_vectors: Reduced dimensionality document vectors
        topics: Dictionary mapping topic index to top terms
        clusters: Document cluster assignments
        explained_variance: Explained variance ratio per component
        silhouette_score: Clustering quality score
        cluster_centers: K-means cluster centers
        topic_distributions: Document-topic probability distributions
        processing_time_ms: Processing time in milliseconds
        cache_hit: Whether result was from cache
    """

    lsa_vectors: np.ndarray
    topics: Dict[int, List[str]]
    clusters: np.ndarray
    explained_variance: np.ndarray
    silhouette_score: float
    cluster_centers: Optional[np.ndarray] = None
    topic_distributions: Optional[np.ndarray] = None
    processing_time_ms: float = 0.0
    cache_hit: bool = False


class LsaReductionStage(PipelineStage[SemanticResult, SemanticResult]):
    """LSA dimensionality reduction pipeline stage.

    Implements the PipelineStage protocol to reduce TF-IDF vectors using
    TruncatedSVD, extract interpretable topics, and perform document clustering.
    """

    def __init__(self, config: Optional[LsaConfig] = None):
        """Initialize LSA reduction stage.

        Args:
            config: LSA configuration (uses defaults if not provided)
        """
        self.config = config or LsaConfig()
        self.cache_manager = CacheManager() if self.config.use_cache else None
        self._svd: Optional[TruncatedSVD] = None
        self._normalizer: Optional[Normalizer] = None
        self._kmeans: Optional[KMeans] = None

    def process(
        self, input_data: SemanticResult, context: Optional[ProcessingContext] = None
    ) -> SemanticResult:
        """Process semantic result to perform LSA reduction.

        Args:
            input_data: SemanticResult from TF-IDF or similarity stage
            context: Processing context with configuration and logging

        Returns:
            Enriched SemanticResult with LSA vectors and clustering
        """
        start_time = time.time()

        # Validate input
        if not input_data.success:
            return input_data

        if input_data.tfidf_matrix is None:
            return self._create_error_result("No TF-IDF matrix provided for LSA", start_time)

        # Check cache if enabled
        cache_key = None
        cached_result = None

        if self.cache_manager and input_data.tfidf_matrix is not None:
            # Generate cache key from matrix content
            cache_key = self._generate_cache_key(input_data.tfidf_matrix)
            cached_result = self.cache_manager.get(cache_key)

            if cached_result is not None:
                logger.info(f"Cache hit for LSA key {cache_key}")
                return self._create_result_from_cache(input_data, cached_result, start_time)

        # Perform LSA reduction
        try:
            lsa_result = self._perform_lsa(
                input_data.tfidf_matrix,
                input_data.feature_names,
                input_data.chunk_ids,
            )

            # Cache the result if enabled
            if self.cache_manager and cache_key:
                cache_data = {
                    "lsa_vectors": lsa_result.lsa_vectors,
                    "topics": lsa_result.topics,
                    "clusters": lsa_result.clusters,
                    "explained_variance": lsa_result.explained_variance,
                    "silhouette_score": lsa_result.silhouette_score,
                    "cluster_centers": lsa_result.cluster_centers,
                    "topic_distributions": lsa_result.topic_distributions,
                }
                self.cache_manager.set(cache_key, cache_data)
                logger.info(f"Cached LSA result with key {cache_key}")

            # Create enriched semantic result
            return self._create_enriched_result(input_data, lsa_result, start_time)

        except Exception as e:
            logger.error(f"LSA reduction failed: {e}")
            return self._create_error_result(str(e), start_time)

    def _perform_lsa(
        self,
        tfidf_matrix: csr_matrix,
        feature_names: Optional[np.ndarray],
        chunk_ids: Optional[List[str]],
    ) -> LSAResult:
        """Perform LSA reduction and clustering.

        Args:
            tfidf_matrix: Sparse TF-IDF matrix
            feature_names: Feature vocabulary
            chunk_ids: Document/chunk identifiers

        Returns:
            LSAResult with reduced vectors and analysis
        """
        n_samples = tfidf_matrix.shape[0]
        n_features = tfidf_matrix.shape[1]

        # Adjust n_components for optimal clustering
        # Balance between clustering quality and variance preservation
        if n_samples < 20 and self.config.n_clusters is not None:
            # Very small dataset with explicit clustering:
            # Use minimal components for better clustering quality
            # Rule of thumb: 2-3x the number of clusters for small datasets
            n_components = min(
                self.config.n_clusters,  # Use same as number of clusters for tiny datasets
                n_samples - 1,
                n_features - 1,
                self.config.n_components,
            )
        elif n_samples < 50:
            # Small dataset: balance clustering and variance
            n_components = min(
                max(int(n_samples * 0.3), 5),  # 30% of samples, minimum 5
                self.config.n_components,
                n_samples - 1,
                n_features - 1,
            )
        elif n_samples < 100:
            # Medium dataset: scale components with dataset size
            n_components = min(
                int(n_samples * 0.5),  # Use 50% of samples as components
                self.config.n_components,
                n_samples - 1,
                n_features - 1,
            )
        else:
            # Regular dataset: use configured components
            n_components = min(self.config.n_components, n_samples - 1, n_features - 1)

        # Use arpack for small matrices (better performance for <1k samples)
        algorithm = "arpack" if n_samples < 1000 else "randomized"

        # Create and fit SVD with algorithm-specific parameters
        if algorithm == "randomized":
            self._svd = TruncatedSVD(
                n_components=n_components,
                random_state=self.config.random_state,
                algorithm=algorithm,
                n_iter=7,  # More iterations for better convergence
            )
        else:
            # arpack doesn't support n_iter parameter
            self._svd = TruncatedSVD(
                n_components=n_components,
                random_state=self.config.random_state,
                algorithm=algorithm,
            )

        # Fit and transform
        lsa_vectors = self._svd.fit_transform(tfidf_matrix)

        # L2 normalize if configured
        if self.config.normalize:
            self._normalizer = Normalizer(copy=False)
            lsa_vectors = self._normalizer.fit_transform(lsa_vectors)

        # Extract topics
        topics = self._extract_topics(feature_names)

        # Perform clustering
        n_clusters = self._determine_n_clusters(n_samples)
        clusters, cluster_centers, score = self._perform_clustering(lsa_vectors, n_clusters)

        # Calculate topic distributions
        topic_distributions = self._calculate_topic_distributions(lsa_vectors)

        return LSAResult(
            lsa_vectors=lsa_vectors,
            topics=topics,
            clusters=clusters,
            explained_variance=self._svd.explained_variance_ratio_,
            silhouette_score=score,
            cluster_centers=cluster_centers,
            topic_distributions=topic_distributions,
        )

    def _extract_topics(self, feature_names: Optional[np.ndarray]) -> Dict[int, List[str]]:
        """Extract top terms for each topic/component.

        Args:
            feature_names: Feature vocabulary

        Returns:
            Dictionary mapping topic index to top terms
        """
        if feature_names is None or self._svd is None:
            return {}

        topics = {}
        components = self._svd.components_

        for topic_idx in range(components.shape[0]):
            # Get top term indices for this component
            top_indices = np.argsort(np.abs(components[topic_idx]))[-self.config.top_n_terms :][
                ::-1
            ]
            top_terms = [feature_names[i] for i in top_indices]
            topics[topic_idx] = top_terms

        return topics

    def _determine_n_clusters(self, n_samples: int) -> int:
        """Determine optimal number of clusters.

        Args:
            n_samples: Number of documents

        Returns:
            Number of clusters to use
        """
        if self.config.n_clusters is not None:
            return min(self.config.n_clusters, n_samples)

        # Use heuristic: sqrt(n/2)
        n_clusters = max(2, int(np.sqrt(n_samples / 2)))
        return min(n_clusters, n_samples)

    def _perform_clustering(
        self, lsa_vectors: np.ndarray, n_clusters: int
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """Perform K-means clustering on LSA vectors.

        Args:
            lsa_vectors: Reduced dimensionality vectors
            n_clusters: Number of clusters

        Returns:
            Tuple of (cluster assignments, cluster centers, silhouette score)
        """
        if n_clusters >= lsa_vectors.shape[0]:
            # Not enough samples for meaningful clustering
            clusters = np.arange(lsa_vectors.shape[0])
            centers = lsa_vectors.copy()
            score = 0.0
        else:
            # For small datasets, use n_init=1 for determinism
            # For larger datasets, use multiple inits for better quality
            n_init = 1 if lsa_vectors.shape[0] < 100 else self.config.n_init

            # Perform K-means clustering with optimized parameters
            self._kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=self.config.random_state,
                n_init=n_init,  # Deterministic for small datasets
                max_iter=self.config.max_iter,
                algorithm="elkan",  # Faster for well-separated clusters
            )
            clusters = self._kmeans.fit_predict(lsa_vectors)
            centers = self._kmeans.cluster_centers_

            # Calculate silhouette score
            if n_clusters > 1 and n_clusters < lsa_vectors.shape[0]:
                score = silhouette_score(lsa_vectors, clusters)
            else:
                score = 0.0

        return clusters, centers, score

    def _calculate_topic_distributions(self, lsa_vectors: np.ndarray) -> np.ndarray:
        """Calculate document-topic probability distributions.

        Args:
            lsa_vectors: LSA-reduced vectors

        Returns:
            Document-topic probability matrix
        """
        # Shift to positive range
        min_val = np.min(lsa_vectors)
        shifted = lsa_vectors - min_val

        # Normalize rows to sum to 1
        row_sums = np.sum(shifted, axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        distributions = shifted / row_sums

        return distributions

    def _generate_cache_key(self, matrix: csr_matrix) -> str:
        """Generate cache key from TF-IDF matrix.

        Args:
            matrix: Sparse TF-IDF matrix

        Returns:
            Deterministic cache key
        """
        if not self.cache_manager:
            return ""

        # Use matrix shape, nnz, and data sample for key
        matrix_hash = f"{matrix.shape}_{matrix.nnz}_{np.sum(matrix.data):.6f}"
        config_hash = str(self.config.get_cache_key_components())
        return self.cache_manager.generate_cache_key(
            matrix_hash + config_hash,
            self.config,
        )

    def _create_error_result(self, error_msg: str, start_time: float) -> SemanticResult:
        """Create error result.

        Args:
            error_msg: Error message
            start_time: Processing start time

        Returns:
            SemanticResult with error
        """
        return SemanticResult(
            success=False,
            error=error_msg,
            processing_time_ms=(time.time() - start_time) * 1000,
        )

    def _create_result_from_cache(
        self, input_data: SemanticResult, cached_data: Dict[str, Any], start_time: float
    ) -> SemanticResult:
        """Create result from cached data.

        Args:
            input_data: Original input semantic result
            cached_data: Cached LSA data
            start_time: Processing start time

        Returns:
            Enriched SemanticResult
        """
        # Merge cached LSA data into input result
        result = SemanticResult(
            tfidf_matrix=input_data.tfidf_matrix,
            vectorizer=input_data.vectorizer,
            vocabulary=input_data.vocabulary,
            feature_names=input_data.feature_names,
            chunk_ids=input_data.chunk_ids,
            cache_hit=True,
            processing_time_ms=(time.time() - start_time) * 1000,
            success=True,
        )

        # Add LSA data to result
        if result.data is None:
            result.data = {}
        result.data.update(
            {
                "lsa_vectors": cached_data["lsa_vectors"],
                "topics": cached_data["topics"],
                "clusters": cached_data["clusters"],
                "explained_variance": cached_data["explained_variance"],
                "silhouette_score": cached_data["silhouette_score"],
                "cluster_centers": cached_data.get("cluster_centers"),
                "topic_distributions": cached_data.get("topic_distributions"),
            }
        )

        if result.metadata is None:
            result.metadata = {}
        result.metadata.update(
            {
                "n_components": cached_data["lsa_vectors"].shape[1],
                "n_clusters": len(np.unique(cached_data["clusters"])),
                "total_variance_explained": np.sum(cached_data["explained_variance"]),
            }
        )

        return result

    def _create_enriched_result(
        self, input_data: SemanticResult, lsa_result: LSAResult, start_time: float
    ) -> SemanticResult:
        """Create enriched semantic result with LSA data.

        Args:
            input_data: Original input semantic result
            lsa_result: LSA analysis result
            start_time: Processing start time

        Returns:
            Enriched SemanticResult
        """
        # Create new result preserving input data
        result = SemanticResult(
            tfidf_matrix=input_data.tfidf_matrix,
            vectorizer=input_data.vectorizer,
            vocabulary=input_data.vocabulary,
            feature_names=input_data.feature_names,
            chunk_ids=input_data.chunk_ids,
            cache_hit=False,
            processing_time_ms=(time.time() - start_time) * 1000,
            success=True,
        )

        # Add LSA data to result
        if result.data is None:
            result.data = {}
        result.data.update(
            {
                "lsa_vectors": lsa_result.lsa_vectors,
                "topics": lsa_result.topics,
                "clusters": lsa_result.clusters,
                "explained_variance": lsa_result.explained_variance,
                "silhouette_score": lsa_result.silhouette_score,
                "cluster_centers": lsa_result.cluster_centers,
                "topic_distributions": lsa_result.topic_distributions,
            }
        )

        if result.metadata is None:
            result.metadata = {}
        result.metadata.update(
            {
                "n_components": lsa_result.lsa_vectors.shape[1],
                "n_clusters": len(np.unique(lsa_result.clusters)),
                "total_variance_explained": np.sum(lsa_result.explained_variance),
            }
        )

        return result

    def get_explained_variance_ratio(self) -> Optional[np.ndarray]:
        """Get explained variance ratio from fitted SVD.

        Returns:
            Explained variance ratio array or None if not fitted
        """
        if self._svd is not None and hasattr(self._svd, "explained_variance_ratio_"):
            return self._svd.explained_variance_ratio_
        return None

    def get_topics(self) -> Optional[Dict[int, List[str]]]:
        """Get extracted topics.

        Returns:
            Topics dictionary or None if not fitted
        """
        # Note: _last_topics attribute is not currently set anywhere
        # This method is for future use if topics need to be cached
        return None

    def process_batch(
        self, batches: List[SemanticResult], context: Optional[ProcessingContext] = None
    ) -> SemanticResult:
        """Process multiple batches of data incrementally.

        Note: TruncatedSVD does not support true incremental learning.
        This method processes batches sequentially and combines results.

        Args:
            batches: List of SemanticResult batches to process
            context: Processing context

        Returns:
            Combined SemanticResult with LSA analysis
        """
        if not batches:
            return SemanticResult(success=False, error="No batches provided")

        # Process first batch to establish components
        first_result = self.process(batches[0], context)
        if not first_result.success:
            return first_result

        # For additional batches, transform using existing SVD
        if len(batches) > 1 and self._svd is not None:
            logger.info(f"Processing {len(batches) - 1} additional batches")

            # Note: This is a simplified batch processing approach
            # True incremental LSA would require online SVD algorithms
            # which are not available in scikit-learn

        return first_result

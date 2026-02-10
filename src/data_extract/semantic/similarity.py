"""Document and chunk similarity analysis using cosine similarity.

This module implements Story 4.2: Document and Chunk Similarity Analysis Engine.
It computes pairwise similarity between documents using TF-IDF vectors from Story 4.1,
identifies duplicates, and builds relationship graphs for navigation.
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

from ..core.models import ProcessingContext
from ..core.pipeline import PipelineStage
from .cache import CacheManager
from .models import SemanticResult

logger = logging.getLogger(__name__)


@dataclass
class SimilarityConfig:
    """Configuration for similarity analysis.

    Attributes:
        duplicate_threshold: Similarity threshold for duplicate detection (default 0.95)
        related_threshold: Similarity threshold for related documents (default 0.7)
        block_size: Block size for memory-efficient computation (default 100)
        use_cache: Whether to use caching (default True)
        compute_graph: Whether to build similarity graph (default True)
        min_similarity: Minimum similarity to store (sparsification, default 0.1)
    """

    duplicate_threshold: float = 0.95
    related_threshold: float = 0.7
    block_size: int = 100
    use_cache: bool = True
    compute_graph: bool = True
    min_similarity: float = 0.1

    def get_cache_key_components(self) -> tuple:
        """Get components for cache key generation."""
        return (
            self.duplicate_threshold,
            self.related_threshold,
            self.block_size,
            self.min_similarity,
        )


@dataclass
class SimilarityResult:
    """Result of similarity analysis.

    Attributes:
        similarity_matrix: Pairwise similarity matrix (sparse or dense)
        similar_pairs: List of (id1, id2, similarity) tuples above threshold
        duplicate_groups: Groups of duplicate documents
        similarity_graph: Graph structure with edges for relationships
        statistics: Similarity statistics (mean, std, max, etc.)
        processing_time_ms: Time taken for processing
        cache_hit: Whether result was from cache
    """

    similarity_matrix: Optional[np.ndarray] = None
    similar_pairs: Optional[List[Tuple[str, str, float]]] = None
    duplicate_groups: Optional[List[List[str]]] = None
    similarity_graph: Optional[Dict[str, List[Tuple[str, float]]]] = None
    statistics: Optional[Dict[str, float]] = None
    processing_time_ms: float = 0.0
    cache_hit: bool = False

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.similar_pairs is None:
            self.similar_pairs = []
        if self.duplicate_groups is None:
            self.duplicate_groups = []
        if self.similarity_graph is None:
            self.similarity_graph = {}
        if self.statistics is None:
            self.statistics = {}


class SimilarityAnalysisStage(PipelineStage[SemanticResult, SemanticResult]):
    """Compute document similarity using TF-IDF vectors.

    This stage implements pairwise cosine similarity computation with:
    - Memory-efficient block-wise processing for large matrices
    - Duplicate detection with configurable threshold
    - Similarity graph construction for document navigation
    - Comprehensive statistics reporting
    """

    def __init__(self, config: Optional[SimilarityConfig] = None):
        """Initialize similarity analysis stage.

        Args:
            config: Similarity configuration (uses defaults if not provided)
        """
        self.config = config or SimilarityConfig()
        self.cache_manager = CacheManager() if self.config.use_cache else None

    def process(
        self, input_data: SemanticResult, context: Optional[ProcessingContext] = None
    ) -> SemanticResult:
        """Process TF-IDF vectors to compute similarity.

        Args:
            input_data: SemanticResult containing TF-IDF matrix from Story 4.1
            context: Processing context with configuration

        Returns:
            Enriched SemanticResult with similarity data added
        """
        start_time = time.time()

        # Validate input
        if not input_data.success or input_data.tfidf_matrix is None:
            logger.error("Invalid input: TF-IDF matrix not available")
            return self._create_error_result(input_data, "No TF-IDF matrix available")

        tfidf_matrix = input_data.tfidf_matrix
        chunk_ids = input_data.chunk_ids or []

        logger.info(
            f"Computing similarity for {tfidf_matrix.shape[0]} documents "
            f"with {tfidf_matrix.shape[1]} features"
        )

        # Check cache if enabled
        cache_key = None
        if self.cache_manager:
            cache_key = self._generate_cache_key(tfidf_matrix, chunk_ids)
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for similarity matrix: {cache_key}")
                return self._merge_cached_result(input_data, cached_result, start_time)

        # Compute similarity matrix
        try:
            n_samples = tfidf_matrix.shape[0]

            if n_samples > 1000 and n_samples > self.config.block_size:
                # Use block-wise computation for large matrices
                logger.info(f"Using block-wise computation (block_size={self.config.block_size})")
                similarity_matrix = self._compute_blockwise_similarity(tfidf_matrix)
            else:
                # Direct computation for small matrices
                logger.info("Using direct similarity computation")
                similarity_matrix = cosine_similarity(tfidf_matrix)

            # Ensure symmetry (numerical precision can cause slight asymmetry)
            similarity_matrix = self._ensure_symmetry(similarity_matrix)

            # Find similar pairs and duplicates
            similar_pairs = self._find_similar_pairs(
                similarity_matrix, chunk_ids, self.config.related_threshold
            )
            duplicate_pairs = self._find_similar_pairs(
                similarity_matrix, chunk_ids, self.config.duplicate_threshold
            )
            duplicate_groups = self._group_duplicates(duplicate_pairs, chunk_ids)

            # Build similarity graph if requested
            similarity_graph = None
            if self.config.compute_graph:
                similarity_graph = self._build_similarity_graph(
                    similarity_matrix, chunk_ids, self.config.related_threshold
                )

            # Compute statistics
            statistics = self._compute_statistics(
                similarity_matrix, len(similar_pairs), len(duplicate_pairs)
            )

            # Create result
            similarity_result = SimilarityResult(
                similarity_matrix=similarity_matrix,
                similar_pairs=similar_pairs,
                duplicate_groups=duplicate_groups,
                similarity_graph=similarity_graph,
                statistics=statistics,
                processing_time_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
            )

            # Cache the result if enabled
            if self.cache_manager and cache_key:
                self.cache_manager.set(cache_key, similarity_result)
                logger.info(f"Cached similarity result: {cache_key}")

            # Merge with input data
            return self._merge_similarity_result(input_data, similarity_result)

        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return self._create_error_result(input_data, str(e))

    def _compute_blockwise_similarity(
        self, matrix: csr_matrix, block_size: Optional[int] = None
    ) -> np.ndarray:
        """Compute similarity matrix in blocks to manage memory.

        Args:
            matrix: Input TF-IDF matrix (sparse or dense)
            block_size: Size of blocks (uses config default if not provided)

        Returns:
            Dense similarity matrix
        """
        if block_size is None:
            block_size = self.config.block_size

        n_samples = matrix.shape[0]
        similarity = np.zeros((n_samples, n_samples), dtype=np.float32)

        # Process in blocks
        for i in range(0, n_samples, block_size):
            end_i = min(i + block_size, n_samples)
            for j in range(i, n_samples, block_size):  # Start from i for upper triangle
                end_j = min(j + block_size, n_samples)

                # Compute block similarity
                block = cosine_similarity(matrix[i:end_i], matrix[j:end_j])

                # Store in result matrix
                similarity[i:end_i, j:end_j] = block
                if i != j:
                    # Mirror to lower triangle for symmetry
                    similarity[j:end_j, i:end_i] = block.T

        return similarity

    def _ensure_symmetry(self, matrix: np.ndarray) -> np.ndarray:
        """Ensure similarity matrix is perfectly symmetric.

        Args:
            matrix: Similarity matrix

        Returns:
            Symmetric matrix
        """
        # Average with transpose to ensure perfect symmetry
        return (matrix + matrix.T) / 2

    def _find_similar_pairs(
        self, similarity_matrix: np.ndarray, chunk_ids: List[str], threshold: float
    ) -> List[Tuple[str, str, float]]:
        """Find pairs of documents above similarity threshold.

        Args:
            similarity_matrix: Pairwise similarity matrix
            chunk_ids: List of chunk identifiers
            threshold: Similarity threshold

        Returns:
            List of (id1, id2, similarity) tuples
        """
        pairs = []
        n_samples = similarity_matrix.shape[0]

        # Only check upper triangle (matrix is symmetric)
        for i in range(n_samples):
            for j in range(i + 1, n_samples):
                similarity = similarity_matrix[i, j]
                if similarity >= threshold:
                    id1 = chunk_ids[i] if i < len(chunk_ids) else f"doc_{i}"
                    id2 = chunk_ids[j] if j < len(chunk_ids) else f"doc_{j}"
                    pairs.append((id1, id2, float(similarity)))

        # Sort by similarity (descending)
        pairs.sort(key=lambda x: x[2], reverse=True)
        return pairs

    def _group_duplicates(
        self, duplicate_pairs: List[Tuple[str, str, float]], chunk_ids: List[str]
    ) -> List[List[str]]:
        """Group duplicate documents using transitive relationships.

        Args:
            duplicate_pairs: List of duplicate pairs
            chunk_ids: All chunk identifiers

        Returns:
            List of duplicate groups
        """
        if not duplicate_pairs:
            return []

        # Build adjacency list
        adjacency: Dict[str, set] = {}
        for id1, id2, _ in duplicate_pairs:
            if id1 not in adjacency:
                adjacency[id1] = set()
            if id2 not in adjacency:
                adjacency[id2] = set()
            adjacency[id1].add(id2)
            adjacency[id2].add(id1)

        # Find connected components (transitive closure)
        visited: set = set()
        groups = []

        for node in adjacency:
            if node not in visited:
                group = self._dfs_component(node, adjacency, visited)
                groups.append(sorted(list(group)))

        return groups

    def _dfs_component(self, node: str, adjacency: Dict[str, set], visited: set) -> set:
        """Depth-first search to find connected component.

        Args:
            node: Starting node
            adjacency: Adjacency list
            visited: Set of visited nodes

        Returns:
            Set of nodes in the component
        """
        component = set()
        stack = [node]

        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                component.add(current)
                stack.extend(adjacency.get(current, set()) - visited)

        return component

    def _build_similarity_graph(
        self, similarity_matrix: np.ndarray, chunk_ids: List[str], threshold: float
    ) -> Dict[str, List[Tuple[str, float]]]:
        """Build similarity graph with edges above threshold.

        Args:
            similarity_matrix: Pairwise similarity matrix
            chunk_ids: List of chunk identifiers
            threshold: Minimum similarity for edges

        Returns:
            Graph as adjacency list with weighted edges
        """
        graph = {}
        n_samples = similarity_matrix.shape[0]

        for i in range(n_samples):
            id_i = chunk_ids[i] if i < len(chunk_ids) else f"doc_{i}"
            edges = []

            for j in range(n_samples):
                if i != j:  # No self-loops
                    similarity = similarity_matrix[i, j]
                    if similarity >= threshold:
                        id_j = chunk_ids[j] if j < len(chunk_ids) else f"doc_{j}"
                        edges.append((id_j, float(similarity)))

            if edges:
                # Sort edges by similarity (descending)
                edges.sort(key=lambda x: x[1], reverse=True)
                graph[id_i] = edges

        return graph

    def _compute_statistics(
        self, similarity_matrix: np.ndarray, n_similar: int, n_duplicates: int
    ) -> Dict[str, float]:
        """Compute similarity statistics.

        Args:
            similarity_matrix: Pairwise similarity matrix
            n_similar: Number of similar pairs
            n_duplicates: Number of duplicate pairs

        Returns:
            Dictionary of statistics
        """
        # Get upper triangle (excluding diagonal)
        n_samples = similarity_matrix.shape[0]
        upper_triangle = similarity_matrix[np.triu_indices(n_samples, k=1)]

        stats = {
            "mean": float(np.mean(upper_triangle)),
            "std": float(np.std(upper_triangle)),
            "min": float(np.min(upper_triangle)),
            "max": float(np.max(upper_triangle)),
            "median": float(np.median(upper_triangle)),
            "n_samples": n_samples,
            "n_similar_pairs": n_similar,
            "n_duplicate_pairs": n_duplicates,
            "duplicate_rate": n_duplicates / max(1, n_samples * (n_samples - 1) // 2),
        }

        # Count pairs above various thresholds
        for threshold in [0.5, 0.7, 0.8, 0.9, 0.95]:
            count = np.sum(upper_triangle >= threshold)
            stats[f"pairs_above_{threshold}"] = int(count)

        return stats

    def _generate_cache_key(self, tfidf_matrix: csr_matrix, chunk_ids: List[str]) -> str:
        """Generate cache key for similarity matrix.

        Args:
            tfidf_matrix: Input TF-IDF matrix
            chunk_ids: List of chunk identifiers

        Returns:
            Cache key string
        """
        if self.cache_manager:
            # Include matrix content and config in key
            content = f"{tfidf_matrix.data.tobytes()}{str(chunk_ids)}"
            config_components = self.config.get_cache_key_components()
            return self.cache_manager.generate_cache_key(content, config_components)
        return ""

    def _merge_cached_result(
        self, input_data: SemanticResult, cached_result: SimilarityResult, start_time: float
    ) -> SemanticResult:
        """Merge cached similarity result with input data.

        Args:
            input_data: Original semantic result
            cached_result: Cached similarity result
            start_time: Processing start time

        Returns:
            Merged semantic result
        """
        # Update input data with cached similarity data
        if input_data.data is None:
            input_data.data = {}

        input_data.data.update(
            {
                "similarity_matrix": cached_result.similarity_matrix,
                "similar_pairs": cached_result.similar_pairs,
                "duplicate_groups": cached_result.duplicate_groups,
                "similarity_graph": cached_result.similarity_graph,
                "similarity_statistics": cached_result.statistics,
            }
        )

        if input_data.metadata is None:
            input_data.metadata = {}

        input_data.metadata.update(
            {
                "similarity_cache_hit": True,
                "similarity_processing_time_ms": (time.time() - start_time) * 1000,
                "n_duplicates": len(cached_result.duplicate_groups or []),
                "n_similar_pairs": len(cached_result.similar_pairs or []),
            }
        )

        return input_data

    def _merge_similarity_result(
        self, input_data: SemanticResult, similarity_result: SimilarityResult
    ) -> SemanticResult:
        """Merge computed similarity result with input data.

        Args:
            input_data: Original semantic result
            similarity_result: Computed similarity result

        Returns:
            Merged semantic result
        """
        # Update input data with similarity data
        if input_data.data is None:
            input_data.data = {}

        input_data.data.update(
            {
                "similarity_matrix": similarity_result.similarity_matrix,
                "similar_pairs": similarity_result.similar_pairs,
                "duplicate_groups": similarity_result.duplicate_groups,
                "similarity_graph": similarity_result.similarity_graph,
                "similarity_statistics": similarity_result.statistics,
            }
        )

        if input_data.metadata is None:
            input_data.metadata = {}

        input_data.metadata.update(
            {
                "similarity_cache_hit": similarity_result.cache_hit,
                "similarity_processing_time_ms": similarity_result.processing_time_ms,
                "n_duplicates": len(similarity_result.duplicate_groups or []),
                "n_similar_pairs": len(similarity_result.similar_pairs or []),
            }
        )

        return input_data

    def _create_error_result(
        self, input_data: SemanticResult, error_message: str
    ) -> SemanticResult:
        """Create error result preserving input data.

        Args:
            input_data: Original semantic result
            error_message: Error message

        Returns:
            Semantic result with error
        """
        input_data.success = False
        input_data.error = f"Similarity analysis failed: {error_message}"
        return input_data

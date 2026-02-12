"""
Fixtures for semantic integration testing.

Provides reusable fixtures for TF-IDF, similarity, LSA, and quality metrics testing
following Epic 4 integration patterns.
"""

from pathlib import Path
from typing import Dict, List

import pytest

pytestmark = [pytest.mark.P0, pytest.mark.integration]

from src.data_extract.chunk.models import Chunk  # noqa: E402
from src.data_extract.core.models import ProcessingContext, ProcessingResult  # noqa: E402

# ============================================================================
# CORPUS FIXTURES
# ============================================================================


@pytest.fixture
def semantic_corpus_documents() -> List[str]:
    """
    Provide semantic corpus documents for testing.

    Returns:
        List of documents with varied content types for testing:
        - Technical documentation
        - Business reports
        - Mixed content
    """
    return [
        # Technical document 1
        "The data extraction pipeline processes documents efficiently using "
        "a five-stage modular architecture. Each stage implements frozen "
        "dataclasses for immutability and type safety.",
        # Technical document 2 (similar to 1)
        "Document processing pipeline extracts data with high performance "
        "through modular stages. Type safety and immutability are enforced "
        "via frozen dataclasses.",
        # Business document 1
        "Financial reports show quarterly revenue growth of 15% year-over-year. "
        "Risk assessment indicates stable market conditions with controlled "
        "exposure to volatility.",
        # Business document 2
        "The audit identified RISK-001 which is mitigated by CTRL-001 and "
        "CTRL-002. Additional controls may be required for emerging risks "
        "in Q4 operations.",
        # Mixed content document
        "Machine learning algorithms analyze text patterns to identify "
        "semantic relationships. This enables risk assessment and control "
        "mapping in enterprise systems.",
    ]


@pytest.fixture
def technical_corpus() -> List[str]:
    """Technical documentation corpus for domain-specific testing."""
    return [
        "Python implementation uses type hints for static analysis.",
        "The API endpoint accepts JSON payloads with authentication.",
        "Database schema includes foreign key constraints for integrity.",
        "Unit tests validate component behavior with mocked dependencies.",
        "Continuous integration pipeline runs automated quality checks.",
    ]


@pytest.fixture
def business_corpus() -> List[str]:
    """Business documentation corpus for domain-specific testing."""
    return [
        "Quarterly earnings exceeded analyst expectations by 5%.",
        "Market share increased through strategic acquisitions.",
        "Regulatory compliance audit completed with no major findings.",
        "Customer satisfaction scores improved across all segments.",
        "Supply chain optimization reduced operational costs by 12%.",
    ]


# ============================================================================
# CHUNK FIXTURES
# ============================================================================


@pytest.fixture
def chunked_documents(semantic_corpus_documents) -> List[Chunk]:
    """
    Generate chunked documents from corpus.

    Creates realistic chunks with:
    - Entity references
    - Quality scores
    - Sequential chunk IDs
    - Metadata with provenance

    Returns:
        List of Chunk objects ready for semantic processing
    """
    chunks = []

    for doc_idx, doc_content in enumerate(semantic_corpus_documents):
        # Simulate sentence-based chunking
        sentences = [s.strip() + "." for s in doc_content.split(". ") if s.strip()]

        for chunk_idx, sentence in enumerate(sentences):
            # Extract entities (simplified pattern matching)
            entities = []
            if "RISK-" in sentence:
                import re  # noqa: E402

                risks = re.findall(r"RISK-\d+", sentence)
                entities.extend([{"type": "RISK", "value": r} for r in risks])
            if "CTRL-" in sentence:
                import re  # noqa: E402

                controls = re.findall(r"CTRL-\d+", sentence)
                entities.extend([{"type": "CONTROL", "value": c} for c in controls])

            # Create metadata object
            import datetime  # noqa: E402
            import hashlib  # noqa: E402
            from pathlib import Path  # noqa: E402

            from src.data_extract.core.models import Metadata  # noqa: E402

            metadata = Metadata(
                source_file=Path(f"/docs/doc_{doc_idx}.txt"),
                file_hash=hashlib.sha256(doc_content.encode()).hexdigest(),
                processing_timestamp=datetime.datetime.now(),
                tool_version="1.0.0",
                config_version="1.0.0",
                entity_tags=[e["value"] for e in entities],
            )

            chunk = Chunk(
                id=f"doc{doc_idx}_chunk{chunk_idx}",
                text=sentence,
                document_id=f"doc_{doc_idx}",
                position_index=chunk_idx,
                token_count=len(sentence) // 4,  # Simple estimation
                word_count=len(sentence.split()),
                quality_score=0.85 + (0.1 if entities else 0.0),  # Higher score for entity-rich
                entities=[],  # Will be populated later if needed
                metadata=metadata,
            )
            chunks.append(chunk)

    return chunks


@pytest.fixture
def entity_rich_chunks() -> List[Chunk]:
    """Chunks with known entities for relationship testing."""
    entity_docs = [
        "RISK-001 is mitigated by CTRL-001 and CTRL-002.",
        "Control CTRL-001 addresses multiple risks including RISK-001 and RISK-003.",
        "The audit found RISK-002 requires additional control CTRL-003.",
        "CTRL-002 provides secondary mitigation for RISK-001 and RISK-002.",
    ]

    chunks = []
    for idx, content in enumerate(entity_docs):
        # Extract entities
        import re  # noqa: E402

        risks = re.findall(r"RISK-\d+", content)
        controls = re.findall(r"CTRL-\d+", content)

        entities = []
        entities.extend([{"type": "RISK", "value": r} for r in risks])
        entities.extend([{"type": "CONTROL", "value": c} for c in controls])

        # Create metadata object
        import datetime  # noqa: E402
        import hashlib  # noqa: E402
        from pathlib import Path  # noqa: E402

        from src.data_extract.core.models import Metadata  # noqa: E402

        metadata = Metadata(
            source_file=Path(f"/docs/entity_doc_{idx}.txt"),
            file_hash=hashlib.sha256(content.encode()).hexdigest(),
            processing_timestamp=datetime.datetime.now(),
            tool_version="1.0.0",
            config_version="1.0.0",
            entity_tags=[e["value"] for e in entities],
        )

        chunk = Chunk(
            id=f"entity_chunk_{idx}",
            text=content,
            document_id=f"entity_doc_{idx}",
            position_index=idx,
            token_count=len(content) // 4,
            word_count=len(content.split()),
            quality_score=0.95,  # High quality for entity-rich content
            entities=[],  # Will be populated later if needed
            metadata=metadata,
        )
        chunks.append(chunk)

    return chunks


# ============================================================================
# CONTEXT FIXTURES
# ============================================================================


@pytest.fixture
def semantic_processing_context(tmp_path: Path) -> ProcessingContext:
    """
    Create ProcessingContext configured for semantic analysis.

    Returns:
        ProcessingContext with semantic configuration including:
        - TF-IDF parameters
        - LSA components
        - Similarity thresholds
        - Quality metrics settings
    """
    tfidf_config = {
        "max_features": 1000,
        "min_df": 1,
        "max_df": 0.95,
        "use_idf": True,
        "sublinear_tf": True,
        "norm": "l2",
    }
    lsa_config = {"n_components": 100, "algorithm": "randomized", "n_iter": 5}
    similarity_config = {"threshold": 0.7, "metric": "cosine", "top_k": 5}
    quality_config = {"calculate_readability": True, "calculate_complexity": True, "threshold": 0.6}

    return ProcessingContext(
        config={
            # Current test access pattern
            "tfidf": tfidf_config,
            "lsa": lsa_config,
            "similarity": similarity_config,
            "quality": quality_config,
            # Legacy nested/flattened pattern retained for compatibility
            "semantic": {
                **tfidf_config,
                **lsa_config,
                "similarity_threshold": similarity_config["threshold"],
                "similarity_metric": similarity_config["metric"],
                "top_k_similar": similarity_config["top_k"],
                "quality_threshold": quality_config["threshold"],
                "tfidf": tfidf_config,
                "lsa": lsa_config,
                "similarity": similarity_config,
                "quality": quality_config,
            },
        },
        source_file="test_corpus.txt",
        output_dir=tmp_path / "output",
        metrics={},
    )


@pytest.fixture
def single_document() -> str:
    """Single document fixture for 1x1 similarity edge-case tests."""
    return "A single semantic analysis document used for similarity matrix testing."


@pytest.fixture
def mock_tfidf_vectors():
    """Deterministic TF-IDF-like vectors for accuracy tests."""
    import numpy as np  # noqa: E402

    vectors = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.5, 0.5, 0.0],
        ],
        dtype=np.float64,
    )
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return vectors / norms


# ============================================================================
# DIMENSION AND THRESHOLD FIXTURES
# ============================================================================


@pytest.fixture
def expected_vector_dimensions() -> int:
    """Expected dimensions for TF-IDF vectors."""
    return 1000  # Based on max_features config


@pytest.fixture
def expected_lsa_dimensions() -> int:
    """Expected dimensions after LSA reduction."""
    return 100  # Based on n_components config


@pytest.fixture
def performance_thresholds() -> Dict[str, float]:
    """
    Performance baselines for semantic operations.

    Returns:
        Dict of operation -> max_seconds
    """
    return {
        "tfidf_fit": 0.1,  # 100ms for fitting on corpus
        "tfidf_transform": 0.05,  # 50ms per document
        "similarity_matrix": 0.2,  # 200ms for 10x10 matrix
        "lsa_fit": 0.3,  # 300ms for LSA decomposition
        "lsa_transform": 0.05,  # 50ms per document
        "quality_metrics": 0.01,  # 10ms per chunk
        "full_pipeline": 0.5,  # 500ms for complete semantic processing
    }


# ============================================================================
# MOCK STAGE FIXTURES
# ============================================================================


@pytest.fixture
def mock_tfidf_stage():
    """
    Mock TF-IDF stage for testing pipeline integration.

    Returns a stage that:
    - Accepts List[Chunk]
    - Returns ProcessingResult with TF-IDF vectors
    - Tracks invocation for assertions
    """

    class MockTfIdfStage:
        def __init__(self):
            self.invoked = False
            self.input_chunks = None
            self.fitted = False

        def fit(self, chunks):
            """Fit the TF-IDF model."""
            self.fitted = True
            return self

        def process(self, chunks: List[Chunk], context: ProcessingContext) -> ProcessingResult:
            """Process chunks through TF-IDF."""
            self.invoked = True
            self.input_chunks = chunks

            # Create mock sparse vectors (simplified)
            import numpy as np  # noqa: E402

            rng = np.random.default_rng(42)
            vectors = []
            for _ in chunks:
                # Mock sparse vector as dense for simplicity
                vector = rng.random((1, 1000))
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm  # Normalize
                vectors.append(vector)

            return ProcessingResult(
                success=True,
                data={
                    "vectors": vectors,
                    "vocabulary": ["term1", "term2", "term3"],  # Mock vocabulary
                    "feature_names": ["feature1", "feature2"],
                    "document_frequency": {"term1": 0.5, "term2": 0.3, "term3": 0.2},
                },
                metrics={"n_features": 1000, "n_documents": len(chunks), "sparsity": 0.95},
            )

    return MockTfIdfStage()


@pytest.fixture
def mock_similarity_stage():
    """
    Mock similarity analysis stage for testing.

    Returns a stage that:
    - Accepts TF-IDF vectors
    - Returns similarity matrix
    - Provides top-k similar items
    """

    class MockSimilarityStage:
        def __init__(self):
            self.invoked = False

        def process(self, vectors, context: ProcessingContext) -> ProcessingResult:
            """Compute similarity matrix."""
            self.invoked = True

            import numpy as np  # noqa: E402

            n_docs = len(vectors) if isinstance(vectors, list) else vectors.shape[0]
            rng = np.random.default_rng(42)

            # Create mock similarity matrix
            matrix = np.eye(n_docs)  # Identity matrix (diagonal = 1.0)
            # Add some off-diagonal similarities
            for i in range(n_docs):
                for j in range(i + 1, n_docs):
                    sim = rng.uniform(0.3, 0.9)
                    matrix[i, j] = sim
                    matrix[j, i] = sim  # Symmetric

            return ProcessingResult(
                success=True,
                data={
                    "similarity_matrix": matrix,
                    "top_similar_pairs": [
                        {"doc1": 0, "doc2": 1, "score": 0.85},
                        {"doc1": 2, "doc2": 3, "score": 0.78},
                    ],
                },
                metrics={
                    "matrix_size": n_docs,
                    "avg_similarity": float(np.mean(matrix[matrix < 1.0])),
                    "max_similarity": float(np.max(matrix[matrix < 1.0])),
                },
            )

    return MockSimilarityStage()


@pytest.fixture
def mock_lsa_stage():
    """
    Mock LSA stage for testing dimensionality reduction.

    Returns a stage that:
    - Accepts high-dimensional vectors
    - Returns reduced dimensions
    - Tracks variance explained
    """

    class MockLSAStage:
        def __init__(self, n_components=100):
            self.n_components = n_components
            self.invoked = False
            self.fitted = False

        def fit(self, vectors):
            """Fit LSA model."""
            self.fitted = True
            return self

        def process(self, vectors, context: ProcessingContext) -> ProcessingResult:
            """Apply LSA dimensionality reduction."""
            self.invoked = True

            import numpy as np  # noqa: E402

            n_docs = len(vectors) if isinstance(vectors, list) else vectors.shape[0]
            rng = np.random.default_rng(42)

            # Create mock reduced vectors
            reduced_vectors = rng.random((n_docs, self.n_components))

            # Mock explained variance (decreasing)
            explained_variance = np.array(
                [0.15 * np.exp(-i * 0.05) for i in range(self.n_components)]
            )
            explained_variance = explained_variance / explained_variance.sum()

            return ProcessingResult(
                success=True,
                data={
                    "lsa_vectors": reduced_vectors,
                    "explained_variance": explained_variance,
                    "explained_variance_ratio": float(explained_variance.sum()),
                    "n_components": self.n_components,
                },
                metrics={
                    "original_dims": 1000,
                    "reduced_dims": self.n_components,
                    "variance_preserved": 0.85,
                },
            )

    return MockLSAStage(n_components=100)


@pytest.fixture
def mock_quality_stage():
    """
    Mock quality metrics stage for testing.

    Returns a stage that:
    - Computes readability scores
    - Computes complexity metrics
    - Provides aggregate quality assessment
    """

    class MockQualityStage:
        def __init__(self):
            self.invoked = False

        def process(self, chunks: List[Chunk], context: ProcessingContext) -> ProcessingResult:
            """Calculate quality metrics."""
            self.invoked = True

            import numpy as np  # noqa: E402

            rng = np.random.default_rng(42)
            quality_scores = []
            for chunk in chunks:
                # Mock quality metrics
                score = {
                    "flesch_reading_ease": rng.uniform(30, 70),
                    "flesch_kincaid_grade": rng.uniform(8, 14),
                    "smog_index": rng.uniform(10, 16),
                    "automated_readability_index": rng.uniform(8, 15),
                    "text_complexity": rng.uniform(0.4, 0.8),
                }
                quality_scores.append(score)

            return ProcessingResult(
                success=True,
                data={
                    "quality_scores": quality_scores,
                    "avg_readability": np.mean([s["flesch_reading_ease"] for s in quality_scores]),
                    "avg_grade_level": np.mean([s["flesch_kincaid_grade"] for s in quality_scores]),
                },
                metrics={"chunks_analyzed": len(chunks), "processing_time": 0.01 * len(chunks)},
            )

    return MockQualityStage()


# ============================================================================
# PERFORMANCE TIMER FIXTURE
# ============================================================================


@pytest.fixture
def performance_timer():
    """Simple performance timer for measuring execution time."""
    import time  # noqa: E402

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed = None
            self.label = None

        def start(self):
            """Start timing."""
            self.start_time = time.perf_counter()
            self.end_time = None
            self.elapsed = None

        def stop(self):
            """Stop timing and calculate elapsed."""
            self.end_time = time.perf_counter()
            self.elapsed = self.end_time - self.start_time
            return self.elapsed

        def reset(self):
            """Reset timer."""
            self.start_time = None
            self.end_time = None
            self.elapsed = None
            self.label = None

        def __call__(self, label: str = "operation"):
            """Support `with performance_timer('name') as timer` usage."""
            self.label = label
            self.start()
            return self

        def __enter__(self):
            """Context manager enter."""
            if self.start_time is None:
                self.start()
            return self

        def __exit__(self, exc_type, exc, tb):
            """Context manager exit."""
            self.stop()
            return False

    return PerformanceTimer()


# ============================================================================
# SAMPLE FILE FIXTURES
# ============================================================================


@pytest.fixture
def sample_text_file(tmp_path: Path, semantic_corpus_documents) -> Path:
    """Create a sample text file with semantic corpus content."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("\n\n".join(semantic_corpus_documents))
    return file_path


@pytest.fixture
def multiple_test_files(tmp_path: Path, technical_corpus, business_corpus) -> List[Path]:
    """Create multiple test files for batch processing."""
    files = []

    # Technical documents
    for idx, content in enumerate(technical_corpus[:3]):
        file_path = tmp_path / f"tech_doc_{idx}.txt"
        file_path.write_text(content)
        files.append(file_path)

    # Business documents
    for idx, content in enumerate(business_corpus[:3]):
        file_path = tmp_path / f"business_doc_{idx}.txt"
        file_path.write_text(content)
        files.append(file_path)

    return files

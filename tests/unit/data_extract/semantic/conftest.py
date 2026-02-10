"""
Unit test fixtures for semantic module testing.

Provides lightweight fixtures for unit testing individual semantic components
without full pipeline integration.
"""

from typing import Any, Dict, List

import numpy as np
import pytest

# ============================================================================
# SIMPLE DATA FIXTURES
# ============================================================================


@pytest.fixture
def simple_documents() -> List[str]:
    """Simple test documents for unit testing."""
    return [
        "The quick brown fox jumps over the lazy dog.",
        "A quick brown dog jumps over the lazy fox.",
        "The fox is quick and brown.",
        "Data extraction processes documents.",
        "Document processing extracts data.",
    ]


@pytest.fixture
def single_document() -> str:
    """Single document for isolated testing."""
    return "This is a test document for semantic analysis unit testing."


@pytest.fixture
def empty_document() -> str:
    """Empty document for edge case testing."""
    return ""


@pytest.fixture
def special_char_document() -> str:
    """Document with special characters for normalization testing."""
    return "Test @document with #special $chars & symbols! (Including) [brackets]."


# ============================================================================
# MOCK VECTOR FIXTURES
# ============================================================================


@pytest.fixture
def mock_tfidf_vectors() -> np.ndarray:
    """Mock TF-IDF vectors for unit testing."""
    # Create 5 documents x 10 features sparse matrix (as dense for simplicity)
    vectors = np.random.rand(5, 10)
    # Normalize rows to unit length (L2 norm)
    for i in range(vectors.shape[0]):
        vectors[i] = vectors[i] / np.linalg.norm(vectors[i])
    return vectors


@pytest.fixture
def mock_vocabulary() -> Dict[str, int]:
    """Mock vocabulary for TF-IDF testing."""
    return {
        "quick": 0,
        "brown": 1,
        "fox": 2,
        "jumps": 3,
        "lazy": 4,
        "dog": 5,
        "data": 6,
        "extraction": 7,
        "processes": 8,
        "documents": 9,
    }


@pytest.fixture
def mock_idf_weights() -> Dict[str, float]:
    """Mock IDF weights for testing."""
    return {
        "quick": 1.2,
        "brown": 1.2,
        "fox": 1.5,
        "jumps": 1.2,
        "lazy": 1.2,
        "dog": 1.5,
        "data": 2.0,
        "extraction": 2.0,
        "processes": 2.0,
        "documents": 1.8,
    }


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================


@pytest.fixture
def tfidf_config() -> Dict[str, Any]:
    """TF-IDF configuration for unit testing."""
    return {
        "max_features": 100,
        "min_df": 1,
        "max_df": 1.0,
        "use_idf": True,
        "sublinear_tf": False,
        "norm": "l2",
    }


@pytest.fixture
def lsa_config() -> Dict[str, Any]:
    """LSA configuration for unit testing."""
    return {"n_components": 5, "algorithm": "randomized", "n_iter": 5, "random_state": 42}


@pytest.fixture
def similarity_config() -> Dict[str, Any]:
    """Similarity configuration for unit testing."""
    return {"metric": "cosine", "threshold": 0.5, "top_k": 3}


@pytest.fixture
def quality_config() -> Dict[str, Any]:
    """Quality metrics configuration for unit testing."""
    return {
        "calculate_flesch": True,
        "calculate_smog": True,
        "calculate_ari": True,
        "min_quality_score": 0.5,
    }


# ============================================================================
# EXPECTED OUTPUT FIXTURES
# ============================================================================


@pytest.fixture
def expected_similarity_matrix() -> np.ndarray:
    """Expected similarity matrix structure."""
    # 5x5 symmetric matrix with diagonal = 1.0
    matrix = np.eye(5)
    # Add some off-diagonal similarities
    matrix[0, 1] = matrix[1, 0] = 0.8  # High similarity
    matrix[2, 3] = matrix[3, 2] = 0.6  # Medium similarity
    matrix[0, 4] = matrix[4, 0] = 0.3  # Low similarity
    return matrix


@pytest.fixture
def expected_quality_scores() -> List[Dict[str, float]]:
    """Expected quality score structure."""
    return [
        {
            "flesch_reading_ease": 65.0,
            "flesch_kincaid_grade": 8.5,
            "smog_index": 10.2,
            "automated_readability_index": 9.1,
        },
        {
            "flesch_reading_ease": 58.0,
            "flesch_kincaid_grade": 10.2,
            "smog_index": 11.5,
            "automated_readability_index": 10.8,
        },
    ]


# ============================================================================
# HELPER FIXTURES
# ============================================================================


@pytest.fixture
def tokenizer():
    """Simple tokenizer for unit testing."""

    def tokenize(text: str) -> List[str]:
        """Basic whitespace and punctuation tokenizer."""
        import re

        # Remove punctuation and split on whitespace
        text = re.sub(r"[^\w\s]", "", text.lower())
        return text.split()

    return tokenize


@pytest.fixture
def vector_comparator():
    """Helper for comparing vectors with tolerance."""

    def compare(v1: np.ndarray, v2: np.ndarray, tolerance: float = 1e-6) -> bool:
        """Compare two vectors within tolerance."""
        return np.allclose(v1, v2, rtol=tolerance, atol=tolerance)

    return compare


# ============================================================================
# VALIDATION FIXTURES
# ============================================================================
# Note: semantic_validator fixtures removed - validation utility deleted in Wave 3 cleanup

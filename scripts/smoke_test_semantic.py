#!/usr/bin/env python
"""
Semantic Dependencies Smoke Test Script

This script validates that all semantic analysis dependencies are properly installed
and meet the performance baselines required for Epic 4 implementation.

Story: 3.5-4-semantic-dependencies-smoke-test
Requirements:
  - TF-IDF fit/transform < 100ms on 1k-word document
  - LSA dimensionality reduction functional
  - Textstat readability metrics operational
  - Cosine similarity computation working

Usage:
    python scripts/smoke_test_semantic.py

Returns:
    0 on success, non-zero on failure (CI integration)
"""

import sys
import time
from typing import List, Tuple

import numpy as np


def test_import_dependencies() -> Tuple[bool, str]:
    """Test that all semantic dependencies can be imported."""
    print("Testing dependency imports...")
    try:
        import joblib
        import sklearn
        import textstat
        from sklearn.decomposition import TruncatedSVD  # noqa: F401
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: F401
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: F401

        # Check versions
        sklearn_version = sklearn.__version__
        joblib_version = joblib.__version__
        # Handle textstat version (can be tuple or string)
        textstat_version_raw = textstat.__version__
        if isinstance(textstat_version_raw, tuple):
            textstat_version = ".".join(map(str, textstat_version_raw))
        else:
            textstat_version = str(textstat_version_raw)

        print(f"  ✓ scikit-learn {sklearn_version}")
        print(f"  ✓ joblib {joblib_version}")
        print(f"  ✓ textstat {textstat_version}")

        # Validate minimum versions
        from packaging import version

        if version.parse(sklearn_version) < version.parse("1.3.0"):
            return False, f"scikit-learn version {sklearn_version} < 1.3.0 minimum"
        if version.parse(joblib_version) < version.parse("1.3.0"):
            return False, f"joblib version {joblib_version} < 1.3.0 minimum"
        if version.parse(textstat_version) < version.parse("0.7.3"):
            return False, f"textstat version {textstat_version} < 0.7.3 minimum"

        return True, "All dependencies imported successfully"
    except ImportError as e:
        return False, f"Import failed: {e}"


def generate_test_corpus(num_docs: int = 10, words_per_doc: int = 100) -> List[str]:
    """Generate a test corpus for performance testing."""
    # Create realistic document-like text
    sample_sentences = [
        "The enterprise data extraction pipeline processes documents efficiently.",
        "Semantic analysis enables intelligent content understanding at scale.",
        "Machine learning algorithms extract meaningful patterns from text data.",
        "Document processing requires careful handling of diverse formats.",
        "Natural language processing transforms unstructured data into insights.",
        "The modular architecture ensures scalable and maintainable systems.",
        "Quality metrics validate the accuracy of extraction results.",
        "Performance optimization reduces processing latency significantly.",
        "Entity recognition identifies key information within documents.",
        "Chunking strategies preserve semantic boundaries in text segmentation.",
    ]

    corpus = []
    for i in range(num_docs):
        # Build document by repeating and varying sentences
        doc_sentences = []
        word_count = 0
        while word_count < words_per_doc:
            sentence = sample_sentences[i % len(sample_sentences)]
            # Add variation
            if i % 2 == 0:
                sentence = sentence.replace("data", f"data_{i}")
            doc_sentences.append(sentence)
            word_count += len(sentence.split())

        corpus.append(" ".join(doc_sentences))

    return corpus


def test_tfidf_performance() -> Tuple[bool, str]:
    """Test TF-IDF vectorization performance (<100ms for 1k words)."""
    print("\nTesting TF-IDF performance...")

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer

        # Generate test corpus (10 docs, 100 words each = 1000 words total)
        corpus = generate_test_corpus(num_docs=10, words_per_doc=100)

        # Create vectorizer
        vectorizer = TfidfVectorizer(max_features=1000, min_df=1, max_df=0.95, use_idf=True)

        # Measure fit_transform time
        start_time = time.perf_counter()
        tfidf_matrix = vectorizer.fit_transform(corpus)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Validate output
        num_docs, num_features = tfidf_matrix.shape
        vocab_size = len(vectorizer.vocabulary_)

        print(f"  • Documents: {num_docs}")
        print(f"  • Features: {num_features}")
        print(f"  • Vocabulary size: {vocab_size}")
        print(f"  • Processing time: {elapsed_ms:.2f}ms")

        # Check performance baseline
        if elapsed_ms >= 100:
            return False, f"TF-IDF took {elapsed_ms:.2f}ms, exceeds 100ms target"

        # Validate output structure
        if num_docs != 10:
            return False, f"Expected 10 documents, got {num_docs}"
        if num_features == 0:
            return False, "No features extracted"
        if vocab_size == 0:
            return False, "Empty vocabulary"

        print(f"  ✓ TF-IDF performance: {elapsed_ms:.2f}ms < 100ms baseline")
        return True, f"TF-IDF completed in {elapsed_ms:.2f}ms"

    except Exception as e:
        return False, f"TF-IDF test failed: {e}"


def test_lsa_dimensionality_reduction() -> Tuple[bool, str]:
    """Test LSA (TruncatedSVD) dimensionality reduction."""
    print("\nTesting LSA dimensionality reduction...")

    try:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        # Generate corpus and create TF-IDF matrix
        corpus = generate_test_corpus(num_docs=10, words_per_doc=100)
        vectorizer = TfidfVectorizer(max_features=500)
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # Apply LSA
        n_components = 5  # Reduce to 5 components for testing
        lsa = TruncatedSVD(n_components=n_components, random_state=42)

        start_time = time.perf_counter()
        lsa_matrix = lsa.fit_transform(tfidf_matrix)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Check explained variance
        explained_variance_ratio = lsa.explained_variance_ratio_.sum()

        print(f"  • Input shape: {tfidf_matrix.shape}")
        print(f"  • Output shape: {lsa_matrix.shape}")
        print(f"  • Components: {n_components}")
        print(f"  • Explained variance: {explained_variance_ratio:.2%}")
        print(f"  • Processing time: {elapsed_ms:.2f}ms")

        # Validate results
        if lsa_matrix.shape != (10, n_components):
            return False, f"Unexpected LSA output shape: {lsa_matrix.shape}"
        if explained_variance_ratio < 0.1:  # At least 10% variance
            return False, f"Low explained variance: {explained_variance_ratio:.2%}"

        print("  ✓ LSA reduction successful")
        return True, "LSA dimensionality reduction working correctly"

    except Exception as e:
        return False, f"LSA test failed: {e}"


def test_cosine_similarity() -> Tuple[bool, str]:
    """Test cosine similarity computation."""
    print("\nTesting cosine similarity...")

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        # Create test documents
        identical_docs = ["This is a test document"] * 2
        different_docs = [
            "The quick brown fox jumps over the lazy dog",
            "Machine learning enables artificial intelligence applications",
        ]

        # Test identical documents
        vectorizer = TfidfVectorizer()
        identical_vectors = vectorizer.fit_transform(identical_docs)
        identical_similarity = cosine_similarity(identical_vectors)[0, 1]

        # Test different documents
        different_vectors = vectorizer.fit_transform(different_docs)
        different_similarity = cosine_similarity(different_vectors)[0, 1]

        print(f"  • Identical docs similarity: {identical_similarity:.4f}")
        print(f"  • Different docs similarity: {different_similarity:.4f}")

        # Validate results
        if not (0.99 <= identical_similarity <= 1.0):
            return False, f"Identical docs similarity {identical_similarity} not ~1.0"
        if not (0.0 <= different_similarity <= 0.3):
            return False, f"Different docs similarity {different_similarity} too high"

        # Test similarity matrix
        corpus = generate_test_corpus(num_docs=5, words_per_doc=50)
        corpus_vectors = vectorizer.fit_transform(corpus)

        start_time = time.perf_counter()
        similarity_matrix = cosine_similarity(corpus_vectors)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        print(f"  • Similarity matrix shape: {similarity_matrix.shape}")
        print(f"  • Processing time: {elapsed_ms:.2f}ms")

        # Validate all values in [0, 1] with small tolerance for floating point errors
        min_val = similarity_matrix.min()
        max_val = similarity_matrix.max()
        if not (-0.0001 <= min_val and max_val <= 1.0001):
            return (
                False,
                f"Similarity values outside [0, 1] range: min={min_val:.6f}, max={max_val:.6f}",
            )

        # Diagonal should be 1.0 (self-similarity)
        diagonal = np.diag(similarity_matrix)
        if not np.allclose(diagonal, 1.0):
            return False, "Diagonal values (self-similarity) not 1.0"

        print("  ✓ Cosine similarity working correctly")
        return True, "Cosine similarity computation successful"

    except Exception as e:
        return False, f"Cosine similarity test failed: {e}"


def test_textstat_metrics() -> Tuple[bool, str]:
    """Test textstat readability metrics."""
    print("\nTesting textstat readability metrics...")

    try:
        import textstat

        # Sample text for testing
        sample_text = """
        The enterprise data extraction pipeline processes complex documents efficiently.
        It handles various formats including PDF, DOCX, and XLSX files.
        The system uses advanced natural language processing techniques.
        Quality metrics ensure accurate extraction results across all document types.
        Performance optimization reduces processing time significantly.
        """

        # Calculate various readability scores
        flesch_score = textstat.flesch_reading_ease(sample_text)
        flesch_kincaid = textstat.flesch_kincaid_grade(sample_text)
        smog_score = textstat.smog_index(sample_text)
        coleman_liau = textstat.coleman_liau_index(sample_text)
        ari_score = textstat.automated_readability_index(sample_text)

        print(f"  • Flesch Reading Ease: {flesch_score:.2f}")
        print(f"  • Flesch-Kincaid Grade: {flesch_kincaid:.2f}")
        print(f"  • SMOG Index: {smog_score:.2f}")
        print(f"  • Coleman-Liau Index: {coleman_liau:.2f}")
        print(f"  • Automated Readability Index: {ari_score:.2f}")

        # Validate scores are reasonable
        if not (0 <= flesch_score <= 100):
            return False, f"Flesch score {flesch_score} out of range"
        if flesch_kincaid < 0:
            return False, f"Invalid Flesch-Kincaid grade: {flesch_kincaid}"

        print("  ✓ Textstat metrics calculated successfully")
        return True, "Textstat readability metrics working"

    except Exception as e:
        return False, f"Textstat test failed: {e}"


def test_end_to_end_pipeline() -> Tuple[bool, str]:
    """Test full semantic pipeline end-to-end (<500ms)."""
    print("\nTesting end-to-end semantic pipeline...")

    try:
        import textstat
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        # Generate test corpus
        corpus = generate_test_corpus(num_docs=20, words_per_doc=100)

        start_time = time.perf_counter()

        # Step 1: TF-IDF vectorization
        vectorizer = TfidfVectorizer(max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # Step 2: LSA reduction
        lsa = TruncatedSVD(n_components=10, random_state=42)
        lsa_matrix = lsa.fit_transform(tfidf_matrix)

        # Step 3: Compute similarities
        similarity_matrix = cosine_similarity(lsa_matrix)

        # Step 4: Calculate readability for first document
        readability_score = textstat.flesch_reading_ease(corpus[0])

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        print(f"  • Corpus size: {len(corpus)} documents")
        print(f"  • TF-IDF features: {tfidf_matrix.shape[1]}")
        print(f"  • LSA components: {lsa_matrix.shape[1]}")
        print(f"  • Similarity matrix: {similarity_matrix.shape}")
        print(f"  • Sample readability: {readability_score:.2f}")
        print(f"  • Total pipeline time: {elapsed_ms:.2f}ms")

        # Check performance baseline
        if elapsed_ms >= 500:
            return False, f"Pipeline took {elapsed_ms:.2f}ms, exceeds 500ms target"

        print(f"  ✓ End-to-end pipeline: {elapsed_ms:.2f}ms < 500ms baseline")
        return True, f"Pipeline completed in {elapsed_ms:.2f}ms"

    except Exception as e:
        return False, f"End-to-end test failed: {e}"


def main():
    """Main smoke test runner."""
    print("=" * 60)
    print("Semantic Dependencies Smoke Test")
    print("Story: 3.5-4-semantic-dependencies-smoke-test")
    print("=" * 60)

    tests = [
        ("Dependency Imports", test_import_dependencies),
        ("TF-IDF Performance", test_tfidf_performance),
        ("LSA Reduction", test_lsa_dimensionality_reduction),
        ("Cosine Similarity", test_cosine_similarity),
        ("Textstat Metrics", test_textstat_metrics),
        ("End-to-End Pipeline", test_end_to_end_pipeline),
    ]

    results = []
    all_passed = True

    for test_name, test_func in tests:
        passed, message = test_func()
        results.append((test_name, passed, message))
        if not passed:
            all_passed = False
            print(f"\n✗ {test_name} FAILED: {message}")

    # Summary
    print("\n" + "=" * 60)
    print("SMOKE TEST SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)

    for test_name, passed, message in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            print(f"       {message}")

    print(f"\nResult: {passed_count}/{total_count} tests passed")

    if all_passed:
        print("\n✓ All smoke tests passed! Semantic dependencies ready for Epic 4.")
        return 0
    else:
        print("\n✗ Some tests failed. Please install missing dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

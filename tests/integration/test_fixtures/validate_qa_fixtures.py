#!/usr/bin/env python
"""
QA Fixtures Validation Runner

Simple validation script to test QA fixtures without pytest dependency.
This verifies all critical acceptance criteria for P0-3.
"""

import json
import re
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import fixtures
# Import PII scanner
from tests.fixtures.greenfield.pii_scanner import PIIScanner
from tests.fixtures.semantic_corpus import (
    CORPUS_CHARACTERISTICS,
    generate_large_corpus,
    get_business_corpus,
    get_edge_case_corpus,
    get_mixed_corpus,
    get_similarity_test_pairs,
    get_technical_corpus,
)


class Colors:
    """Terminal colors for output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_test_header(test_name: str, case_number: int):
    """Print formatted test header."""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Test Case {case_number}: {test_name}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")


def print_result(passed: bool, message: str):
    """Print test result."""
    if passed:
        print(f"{Colors.GREEN}✓ {message}{Colors.END}")
    else:
        print(f"{Colors.RED}✗ {message}{Colors.END}")


def validate_corpus_size():
    """Test Case 1: Corpus Size Validation."""
    print_test_header("Corpus Size Validation", 1)

    all_passed = True

    # Technical corpus
    technical = get_technical_corpus()
    passed = len(technical) >= 5
    print_result(passed, f"Technical corpus size: {len(technical)} documents (min: 5)")
    all_passed = all_passed and passed

    total_words = sum(len(doc.split()) for doc in technical)
    passed = total_words >= 200
    print_result(passed, f"Technical corpus words: {total_words} (min: 200)")
    all_passed = all_passed and passed

    # Business corpus
    business = get_business_corpus()
    passed = len(business) >= 5
    print_result(passed, f"Business corpus size: {len(business)} documents (min: 5)")
    all_passed = all_passed and passed

    # Mixed corpus
    mixed = get_mixed_corpus()
    passed = len(mixed) >= 10
    print_result(passed, f"Mixed corpus size: {len(mixed)} documents (min: 10)")
    all_passed = all_passed and passed

    # Edge cases
    edge = get_edge_case_corpus()
    passed = len(edge) >= 7
    print_result(passed, f"Edge case corpus size: {len(edge)} cases (min: 7)")
    all_passed = all_passed and passed

    return all_passed


def validate_corpus_quality():
    """Test Case 2: Corpus Quality Metrics."""
    print_test_header("Corpus Quality Metrics", 2)

    all_passed = True

    # Vocabulary diversity
    corpora = {
        "technical": get_technical_corpus(),
        "business": get_business_corpus(),
        "mixed": get_mixed_corpus(),
    }

    diversity_threshold = 0.3

    for name, corpus in corpora.items():
        full_text = " ".join(corpus).lower()
        words = re.findall(r"\b\w+\b", full_text)
        unique_words = set(words)

        diversity = len(unique_words) / len(words) if words else 0
        passed = diversity >= diversity_threshold

        print_result(
            passed,
            f"{name.capitalize()} diversity: {diversity:.2f} "
            f"({len(unique_words)} unique / {len(words)} total)",
        )
        all_passed = all_passed and passed

    # Entity distribution check
    mixed = get_mixed_corpus()
    full_text = " ".join(mixed)

    entity_patterns = {
        "technical": r"\b(API|ML|AI|TF-IDF|LSA|NLP|JSON|XML|HTTP)\b",
        "business": r"\b(revenue|compliance|customer|strategic|risk)\b",
    }

    for entity_type, pattern in entity_patterns.items():
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        passed = len(matches) > 0
        print_result(passed, f"{entity_type.capitalize()} entities found: {len(matches)}")
        all_passed = all_passed and passed

    return all_passed


def validate_pii_compliance():
    """Test Case 3: PII and Compliance Validation."""
    print_test_header("PII and Compliance Validation", 3)

    all_passed = True
    scanner = PIIScanner()

    all_corpora = {
        "technical": get_technical_corpus(),
        "business": get_business_corpus(),
        "mixed": get_mixed_corpus(),
        "edge_case": get_edge_case_corpus(),
    }

    total_violations = 0

    for corpus_name, corpus in all_corpora.items():
        results = scanner.scan_corpus(corpus, corpus_name)
        violations = results["violation_count"]
        total_violations += violations

        passed = violations == 0
        print_result(
            passed,
            f"{corpus_name.capitalize()} corpus: "
            f"{'PII-free' if passed else f'{violations} violations found'}",
        )
        all_passed = all_passed and passed

    # Check for real company names
    all_text = " ".join(
        [
            " ".join(get_technical_corpus()),
            " ".join(get_business_corpus()),
            " ".join(get_mixed_corpus()),
        ]
    )

    real_entities = ["Microsoft", "Google", "Amazon", "Facebook", "Apple"]
    found_entities = []

    for entity in real_entities:
        if entity in all_text:
            found_entities.append(entity)

    passed = len(found_entities) == 0
    print_result(
        passed, f"Real entity check: {'None found' if passed else f'Found: {found_entities}'}"
    )
    all_passed = all_passed and passed

    return all_passed


def validate_cross_format():
    """Test Case 4: Cross-Format Consistency."""
    print_test_header("Cross-Format Consistency", 4)

    all_passed = True

    # Test loading consistency
    technical1 = get_technical_corpus()
    technical2 = get_technical_corpus()

    passed = technical1 == technical2
    print_result(passed, "Deterministic loading: Fixtures return same data")
    all_passed = all_passed and passed

    # Test serialization
    try:
        corpus = get_technical_corpus()
        json_str = json.dumps(corpus)
        loaded = json.loads(json_str)
        passed = loaded == corpus
        print_result(passed, "JSON serialization: Round-trip successful")
        all_passed = all_passed and passed
    except Exception as e:
        print_result(False, f"JSON serialization failed: {e}")
        all_passed = False

    # Test generator determinism
    gen1 = generate_large_corpus(num_docs=10, words_per_doc=20)
    gen2 = generate_large_corpus(num_docs=10, words_per_doc=20)

    passed = gen1 == gen2
    print_result(passed, "Generator determinism: Same parameters = same output")
    all_passed = all_passed and passed

    return all_passed


def validate_edge_cases():
    """Test Case 5: Edge Case Coverage."""
    print_test_header("Edge Case Coverage", 5)

    all_passed = True
    corpus = get_edge_case_corpus()

    edge_types_found = {
        "very_short": False,
        "very_long": False,
        "unicode": False,
        "numbers": False,
        "special_chars": False,
    }

    for doc in corpus:
        if len(doc.split()) <= 3:
            edge_types_found["very_short"] = True
        if len(doc.split()) > 50:
            edge_types_found["very_long"] = True
        if re.search(r"[^\x00-\x7F]", doc):
            edge_types_found["unicode"] = True
        if re.search(r"\d", doc):
            edge_types_found["numbers"] = True
        if re.search(r"[!@#$%^&*()]", doc):
            edge_types_found["special_chars"] = True

    for edge_type, found in edge_types_found.items():
        print_result(
            found,
            f"{edge_type.replace('_', ' ').title()} case: {'Present' if found else 'Missing'}",
        )
        all_passed = all_passed and found

    # Count total coverage
    covered = sum(1 for v in edge_types_found.values() if v)
    passed = covered >= 5
    print_result(passed, f"Edge case types covered: {covered}/5")
    all_passed = all_passed and passed

    return all_passed


def validate_performance():
    """Test Case 6: Performance Characteristics."""
    print_test_header("Performance Characteristics", 6)

    all_passed = True

    # Load time test
    start = time.perf_counter()
    _ = get_technical_corpus()
    _ = get_business_corpus()
    _ = get_mixed_corpus()
    _ = get_edge_case_corpus()
    load_time_ms = (time.perf_counter() - start) * 1000

    passed = load_time_ms < 100
    print_result(passed, f"Load time: {load_time_ms:.1f}ms (limit: 100ms)")
    all_passed = all_passed and passed

    # Memory footprint
    import sys

    corpus_sizes = {
        "technical": sys.getsizeof(get_technical_corpus()),
        "business": sys.getsizeof(get_business_corpus()),
        "mixed": sys.getsizeof(get_mixed_corpus()),
        "edge": sys.getsizeof(get_edge_case_corpus()),
    }

    total_kb = sum(corpus_sizes.values()) / 1024
    passed = total_kb < 10 * 1024  # 10MB limit
    print_result(passed, f"Memory usage: {total_kb:.1f}KB (limit: 10MB)")
    all_passed = all_passed and passed

    # Reproducibility test
    corpus1 = generate_large_corpus(num_docs=50, words_per_doc=30)
    corpus2 = generate_large_corpus(num_docs=50, words_per_doc=30)

    passed = corpus1 == corpus2
    print_result(passed, "Generation reproducibility: Identical outputs")
    all_passed = all_passed and passed

    return all_passed


def validate_gold_standards():
    """Test Case 7: Gold Standard Reference Data."""
    print_test_header("Gold Standard Reference Data", 7)

    all_passed = True

    # Test similarity pairs
    pairs = get_similarity_test_pairs()

    passed = len(pairs) >= 4
    print_result(passed, f"Similarity test pairs: {len(pairs)} pairs (min: 4)")
    all_passed = all_passed and passed

    # Validate pair structure
    for idx, pair in enumerate(pairs):
        has_all_fields = all(
            k in pair for k in ["doc1", "doc2", "expected_similarity", "description"]
        )

        if has_all_fields:
            min_sim, max_sim = pair["expected_similarity"]
            valid_range = 0 <= min_sim <= max_sim <= 1

            if not valid_range:
                print_result(False, f"Pair {idx}: Invalid similarity range")
                all_passed = False
        else:
            print_result(False, f"Pair {idx}: Missing required fields")
            all_passed = False

    if all_passed:
        print_result(True, "All similarity pairs properly structured")

    # Check corpus characteristics documentation
    passed = len(CORPUS_CHARACTERISTICS) >= 4
    print_result(
        passed, f"Corpus characteristics documented: {len(CORPUS_CHARACTERISTICS)} corpora"
    )
    all_passed = all_passed and passed

    return all_passed


def validate_maintenance():
    """Test Case 8: Fixture Maintenance and Updates."""
    print_test_header("Fixture Maintenance and Updates", 8)

    all_passed = True

    # Check module documentation
    corpus_module_path = Path("tests/fixtures/semantic_corpus.py")

    if corpus_module_path.exists():
        content = corpus_module_path.read_text()

        # Check for Epic 4 reference
        passed = "Epic 4" in content or "epic 4" in content.lower()
        print_result(passed, "Epic 4 reference in module")
        all_passed = all_passed and passed

        # Check for CORPUS_CHARACTERISTICS
        passed = "CORPUS_CHARACTERISTICS" in content
        print_result(passed, "CORPUS_CHARACTERISTICS baseline present")
        all_passed = all_passed and passed
    else:
        print_result(False, "Corpus module not found")
        all_passed = False

    # Test backward compatibility
    try:
        # Basic calls should work
        technical = get_technical_corpus()
        business = get_business_corpus()

        # Generator with defaults should work
        large = generate_large_corpus()

        passed = len(large) == 1000
        print_result(passed, f"Default generator parameters: {len(large)} docs (expected: 1000)")
        all_passed = all_passed and passed

        # Custom parameters should work
        custom = generate_large_corpus(num_docs=25, words_per_doc=50)
        passed = len(custom) == 25
        print_result(passed, f"Custom generator parameters: {len(custom)} docs (expected: 25)")
        all_passed = all_passed and passed

    except Exception as e:
        print_result(False, f"Backward compatibility failed: {e}")
        all_passed = False

    return all_passed


def main():
    """Run all validation tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print("QA FIXTURES VALIDATION TEST SUITE")
    print("P0-3: Epic 4 Foundation Validation")
    print(f"{'='*60}{Colors.END}\n")

    test_results = {
        "Corpus Size": validate_corpus_size(),
        "Corpus Quality": validate_corpus_quality(),
        "PII Compliance": validate_pii_compliance(),
        "Cross-Format": validate_cross_format(),
        "Edge Cases": validate_edge_cases(),
        "Performance": validate_performance(),
        "Gold Standards": validate_gold_standards(),
        "Maintenance": validate_maintenance(),
    }

    # Summary
    print(f"\n{Colors.BOLD}{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}{Colors.END}\n")

    passed_count = sum(1 for v in test_results.values() if v)
    total_count = len(test_results)

    for test_name, passed in test_results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name:20} [{status}]")

    print(
        f"\n{Colors.BOLD}Overall Result: {passed_count}/{total_count} test cases passed{Colors.END}"
    )

    if passed_count == total_count:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL VALIDATION TESTS PASSED!{Colors.END}")
        print(f"{Colors.GREEN}Epic 4 has validated, reliable test data foundation.{Colors.END}")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠️  Some tests failed. Review output above.{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
Validation script for performance baseline suite delivery.

Run this to verify all deliverables are in place.
"""

import pytest

pytestmark = pytest.mark.P1

import json  # noqa: E402
from pathlib import Path  # noqa: E402


def validate_delivery():
    """Validate all performance baseline deliverables."""

    print("=" * 70)
    print("PERFORMANCE BASELINE SUITE - DELIVERY VALIDATION")
    print("=" * 70)

    base_dir = Path(__file__).parent
    project_root = base_dir.parent.parent

    issues = []
    successes = []

    # Check test infrastructure files
    test_files = {
        "__init__.py": "Package documentation",
        "conftest.py": "Fixtures and utilities",
        "test_baseline_capture.py": "Baseline establishment",
        "test_extractor_benchmarks.py": "Extractor benchmarks",
        "test_pipeline_benchmarks.py": "Pipeline benchmarks",
        "README.md": "Usage documentation",
    }

    print("\n1. Test Infrastructure Files:")
    for filename, description in test_files.items():
        filepath = base_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"   ✅ {filename:35} ({size:,} bytes) - {description}")
            successes.append(f"Test file: {filename}")
        else:
            print(f"   ❌ {filename:35} MISSING - {description}")
            issues.append(f"Missing test file: {filename}")

    # Check baseline data
    print("\n2. Baseline Data:")
    baseline_file = base_dir / "baselines.json"
    if baseline_file.exists():
        with open(baseline_file, "r") as f:
            baselines = json.load(f)

        num_baselines = len(baselines.get("baselines", {}))
        print(f"   ✅ baselines.json exists with {num_baselines} operations")

        # List baselines
        for operation in baselines.get("baselines", {}).keys():
            print(f"      - {operation}")

        successes.append(f"Baseline data: {num_baselines} operations")

        if num_baselines < 10:
            issues.append(f"Only {num_baselines} baselines (expected 11+)")
    else:
        print("   ❌ baselines.json MISSING")
        issues.append("Missing baselines.json")

    # Check documentation
    print("\n3. Documentation:")
    docs_dir = project_root / "docs" / "architecture"
    doc_files = {
        "epic-4-performance-baselines.md": "Comprehensive performance report",
    }

    for filename, description in doc_files.items():
        filepath = docs_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"   ✅ {filename:40} ({size:,} bytes) - {description}")
            successes.append(f"Documentation: {filename}")
        else:
            print(f"   ❌ {filename:40} MISSING - {description}")
            issues.append(f"Missing documentation: {filename}")

    # Check pytest markers
    print("\n4. Pytest Configuration:")
    pytest_ini = project_root / "pytest.ini"
    if pytest_ini.exists():
        content = pytest_ini.read_text()
        markers_found = []

        if "performance:" in content:
            markers_found.append("performance")
        if "slow:" in content:
            markers_found.append("slow")

        if markers_found:
            print(f"   ✅ pytest.ini configured with markers: {', '.join(markers_found)}")
            successes.append("Pytest markers configured")
        else:
            print("   ⚠️  pytest.ini exists but markers not found")
            issues.append("Pytest markers not configured")
    else:
        print("   ❌ pytest.ini MISSING")
        issues.append("Missing pytest.ini")

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"✅ Successes: {len(successes)}")
    print(f"❌ Issues: {len(issues)}")

    if issues:
        print("\nIssues Found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n🎉 ALL DELIVERABLES VERIFIED!")

    print("\n" + "=" * 70)

    return len(issues) == 0


if __name__ == "__main__":
    import sys  # noqa: E402

    success = validate_delivery()
    sys.exit(0 if success else 1)

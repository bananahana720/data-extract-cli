#!/usr/bin/env python3
"""
Performance Baseline Validator

Checks performance against established baselines for the Data Extraction Tool project.
Detects changed files, runs relevant performance tests, compares against baselines,
generates regression reports, and flags NFR violations.

Usage:
    python scripts/validate_performance.py                         # Run all checks
    python scripts/validate_performance.py --component chunk       # Check specific component
    python scripts/validate_performance.py --update-baseline       # Update baselines
    python scripts/validate_performance.py --ci-mode               # CI/CD integration mode
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import structlog  # type: ignore[import-not-found]

# Configure structured logging
logger = structlog.get_logger()

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
PERFORMANCE_TESTS_DIR = TESTS_DIR / "performance"
DOCS_DIR = PROJECT_ROOT / "docs"
BASELINE_PATTERN = "performance-baselines-*.md"

# NFR thresholds from requirements
NFR_P1_THROUGHPUT = 1000  # words per second minimum
NFR_P2_MEMORY_LIMIT = 500  # MB per document maximum
NFR_P3_LATENCY = {
    "chunk": 5.0,  # seconds per 10k words
    "extract": 10.0,  # seconds per document
    "pipeline": 30.0,  # seconds end-to-end
}

# Component mapping for smart test detection
COMPONENT_MAPPING = {
    "extract": ["test_extract_performance", "test_pdf_performance", "test_docx_performance"],
    "normalize": ["test_normalize_performance", "test_entity_performance"],
    "chunk": ["test_chunking_performance", "test_entity_chunking_performance"],
    "semantic": ["test_tfidf_performance", "test_lsa_performance"],
    "output": ["test_json_performance", "test_csv_performance", "test_txt_performance"],
}


class PerformanceValidator:
    """Validates performance against established baselines."""

    def __init__(
        self,
        component: Optional[str] = None,
        update_baseline: bool = False,
        ci_mode: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize the performance validator.

        Args:
            component: Specific component to test (None for all)
            update_baseline: Update baseline documentation
            ci_mode: CI/CD mode (strict failures)
            verbose: Enable verbose output
        """
        self.component = component
        self.update_baseline = update_baseline
        self.ci_mode = ci_mode
        self.verbose = verbose
        self.start_time = time.time()
        self.test_results: Dict[str, dict] = {}
        self.baseline_data: Dict[str, dict] = {}
        self.regressions: List[dict] = []
        self.nfr_violations: List[dict] = []
        logger.info(
            "initialized_performance_validator",
            component=component,
            update_baseline=update_baseline,
            ci_mode=ci_mode,
        )

    def print_header(self) -> None:
        """Print validation header."""
        print("=" * 70)
        print("📊 Performance Baseline Validator")
        print("=" * 70)
        print(f"Mode: {'CI/CD' if self.ci_mode else 'Interactive'}")
        print(f"Component: {self.component or 'All'}")
        print(f"Update Baseline: {self.update_baseline}")
        print()

    def detect_changed_files(self) -> List[str]:
        """
        Detect changed files and determine which performance tests to run.

        Returns:
            List of test modules to run
        """
        print("🔍 Detecting changed files...")

        try:
            # Get list of changed files from git
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1..HEAD"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0:
                # Try alternative: uncommitted changes
                result = subprocess.run(
                    ["git", "diff", "--name-only"],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT,
                )

            changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

            # Map changed files to components
            affected_components = set()
            for file in changed_files:
                if "extract" in file.lower():
                    affected_components.add("extract")
                if "normaliz" in file.lower():
                    affected_components.add("normalize")
                if "chunk" in file.lower():
                    affected_components.add("chunk")
                if "semantic" in file.lower() or "tfidf" in file.lower() or "lsa" in file.lower():
                    affected_components.add("semantic")
                if "output" in file.lower() or "format" in file.lower():
                    affected_components.add("output")

            # Get test modules for affected components
            test_modules = []
            for comp in affected_components:
                if comp in COMPONENT_MAPPING:
                    test_modules.extend(COMPONENT_MAPPING[comp])

            if test_modules:
                print(f"  📝 Changed components: {', '.join(affected_components)}")
                print(f"  🎯 Performance tests to run: {len(test_modules)} modules")
            else:
                print("  ℹ️  No component changes detected, running all performance tests")
                # Run all tests if no specific changes detected
                for tests in COMPONENT_MAPPING.values():
                    test_modules.extend(tests)

            return list(set(test_modules))  # Remove duplicates

        except Exception as e:
            logger.warning("git_detection_failed", error=str(e))
            print(f"  ⚠️  Git detection failed: {e}")
            print("  ℹ️  Running all performance tests")

            # Return all tests on error
            all_tests = []
            for tests in COMPONENT_MAPPING.values():
                all_tests.extend(tests)
            return list(set(all_tests))

    def parse_baseline_documents(self) -> bool:
        """
        Parse baseline documents from docs/performance-baselines-*.md.

        Returns:
            True if baselines parsed successfully
        """
        print("📖 Parsing performance baselines...")

        baseline_files = list(DOCS_DIR.glob(BASELINE_PATTERN))

        if not baseline_files:
            print(f"  ⚠️  No baseline files found matching {BASELINE_PATTERN}")
            return False

        for baseline_file in baseline_files:
            try:
                content = baseline_file.read_text()

                # Parse markdown tables using regex
                # Looking for tables like:
                # | Metric | Baseline | Actual | Status |
                # |--------|----------|--------|--------|
                # | ... | ... | ... | ... |

                # Parse markdown tables - pattern for future use if needed
                # table_pattern = r"\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|"

                for line in content.split("\n"):
                    # Parse performance metrics from bullet points
                    if "seconds" in line.lower() or "ms" in line.lower():
                        self._extract_metric_from_line(line, baseline_file.stem)

                    # Parse memory metrics
                    if "mb" in line.lower() or "memory" in line.lower():
                        self._extract_memory_metric(line, baseline_file.stem)

                    # Parse throughput metrics
                    if "words per second" in line.lower() or "throughput" in line.lower():
                        self._extract_throughput_metric(line, baseline_file.stem)

                print(f"  ✅ Parsed {baseline_file.name}")

            except Exception as e:
                logger.error("baseline_parse_error", file=str(baseline_file), error=str(e))
                print(f"  ❌ Failed to parse {baseline_file.name}: {e}")

        # Log parsed baselines
        if self.verbose and self.baseline_data:
            print(f"\n  📊 Parsed {len(self.baseline_data)} baseline metrics")
            for key in list(self.baseline_data.keys())[:5]:
                print(f"    • {key}: {self.baseline_data[key]}")

        return bool(self.baseline_data)

    def _extract_metric_from_line(self, line: str, source: str) -> None:
        """Extract performance metric from a markdown line."""
        # Pattern: "metric_name: X.XX seconds"
        patterns = [
            r"([^:]+):\s*([\d.]+)\s*seconds",
            r"([^:]+):\s*([\d.]+)\s*ms",
            r"(\w+).*?([\d.]+)s\s",
        ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                metric_name = match.group(1).strip()
                value = float(match.group(2))

                # Convert ms to seconds if needed
                if "ms" in line.lower():
                    value = value / 1000

                key = f"{source}_{metric_name}".lower().replace(" ", "_").replace("-", "_")
                self.baseline_data[key] = {
                    "value": value,
                    "unit": "seconds",
                    "source": source,
                }

    def _extract_memory_metric(self, line: str, source: str = "baseline") -> None:
        """Extract memory metric from a markdown line."""
        pattern = r"([\d.]+)\s*MB"
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            # Store memory metrics
            if "peak" in line.lower():
                key = "peak_memory"
            elif "delta" in line.lower():
                key = "memory_delta"
            else:
                key = "memory"

            self.baseline_data[f"memory_{key}"] = {
                "value": value,
                "unit": "MB",
                "source": "baseline",
            }

    def _extract_throughput_metric(self, line: str, source: str = "baseline") -> None:
        """Extract throughput metric from a markdown line."""
        pattern = r"([\d.]+)\s*words?\s*per\s*second"
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            self.baseline_data["throughput"] = {
                "value": value,
                "unit": "words/second",
                "source": "baseline",
            }

    def run_performance_tests(self, test_modules: List[str]) -> bool:
        """
        Run performance tests for specified modules.

        Args:
            test_modules: List of test module names to run

        Returns:
            True if tests ran successfully
        """
        print(f"\n🏃 Running {len(test_modules)} performance test modules...")

        success = True

        for test_module in test_modules:
            test_path = PERFORMANCE_TESTS_DIR / f"{test_module}.py"

            if not test_path.exists():
                print(f"  ⚠️  Test file not found: {test_path}")
                continue

            print(f"\n  🔬 Running {test_module}...")

            try:
                # Run pytest with JSON output for parsing
                result = subprocess.run(
                    [
                        "pytest",
                        str(test_path),
                        "--tb=short",
                        "--benchmark-json=performance_results.json",
                        "-v",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_ROOT,
                )

                # Parse test output
                if result.returncode == 0:
                    print(f"    ✅ {test_module} passed")
                    self._parse_test_output(test_module, result.stdout)
                else:
                    print(f"    ❌ {test_module} failed")
                    if self.verbose:
                        print(f"    Output: {result.stdout[:500]}")
                    success = False

                # Try to parse benchmark JSON if it exists
                benchmark_file = PROJECT_ROOT / "performance_results.json"
                if benchmark_file.exists():
                    try:
                        with open(benchmark_file) as f:
                            benchmark_data = json.load(f)
                            self._parse_benchmark_data(test_module, benchmark_data)
                        benchmark_file.unlink()  # Clean up
                    except Exception:
                        pass

            except FileNotFoundError:
                print("    ❌ pytest not found. Please install test dependencies.")
                return False
            except Exception as e:
                logger.error("test_execution_error", test=test_module, error=str(e))
                print(f"    ❌ Error running {test_module}: {e}")
                success = False

        return success

    def _parse_test_output(self, test_module: str, output: str) -> None:
        """Parse test output for performance metrics."""
        # Look for timing information in pytest output
        timing_pattern = r"([\d.]+)s\s+call"
        matches = re.findall(timing_pattern, output)

        if matches:
            avg_time = sum(float(m) for m in matches) / len(matches)
            self.test_results[f"{test_module}_time"] = {
                "value": avg_time,
                "unit": "seconds",
                "test": test_module,
            }

        # Look for memory usage (if reported)
        memory_pattern = r"Peak memory:\s*([\d.]+)\s*MB"
        match = re.search(memory_pattern, output, re.IGNORECASE)
        if match:
            self.test_results[f"{test_module}_memory"] = {
                "value": float(match.group(1)),
                "unit": "MB",
                "test": test_module,
            }

    def _parse_benchmark_data(self, test_module: str, benchmark_data: dict) -> None:
        """Parse pytest-benchmark JSON output."""
        if "benchmarks" in benchmark_data:
            for benchmark in benchmark_data["benchmarks"]:
                name = benchmark.get("name", "unknown")
                stats = benchmark.get("stats", {})

                # Store timing stats
                if "mean" in stats:
                    key = f"{test_module}_{name}_mean"
                    self.test_results[key] = {
                        "value": stats["mean"],
                        "unit": "seconds",
                        "test": test_module,
                    }

    def compare_with_baselines(self) -> bool:
        """
        Compare test results against baselines.

        Returns:
            True if within acceptable limits
        """
        print("\n📈 Comparing results with baselines...")

        if not self.baseline_data:
            print("  ⚠️  No baseline data available for comparison")
            return True

        within_limits = True

        for test_key, test_result in self.test_results.items():
            # Find matching baseline
            baseline_key = None
            for bkey in self.baseline_data.keys():
                if any(part in bkey for part in test_key.split("_")):
                    baseline_key = bkey
                    break

            if baseline_key and baseline_key in self.baseline_data:
                baseline = self.baseline_data[baseline_key]

                # Calculate delta
                actual = test_result["value"]
                expected = baseline["value"]
                delta_pct = ((actual - expected) / expected) * 100 if expected > 0 else 0

                # Check for regression (>10% worse)
                if delta_pct > 10:
                    self.regressions.append(
                        {
                            "metric": test_key,
                            "expected": expected,
                            "actual": actual,
                            "delta_pct": delta_pct,
                            "unit": test_result["unit"],
                        }
                    )
                    print(f"  ⚠️  Regression: {test_key}")
                    print(f"      Expected: {expected:.3f} {test_result['unit']}")
                    print(f"      Actual: {actual:.3f} {test_result['unit']}")
                    print(f"      Delta: +{delta_pct:.1f}%")
                    within_limits = False

                elif delta_pct < -10:
                    # Performance improvement
                    print(f"  ✨ Improvement: {test_key}")
                    print(f"      Delta: {delta_pct:.1f}%")

                else:
                    # Within acceptable range
                    if self.verbose:
                        print(f"  ✅ {test_key}: within baseline ({delta_pct:+.1f}%)")

        return within_limits

    def check_nfr_violations(self) -> bool:
        """
        Check for Non-Functional Requirement violations.

        Returns:
            True if all NFRs are met
        """
        print("\n🚨 Checking NFR compliance...")

        nfr_pass = True

        # Check NFR-P1: Throughput
        throughput_metrics = [k for k in self.test_results if "throughput" in k.lower()]
        for metric in throughput_metrics:
            value = self.test_results[metric]["value"]
            if value < NFR_P1_THROUGHPUT:
                self.nfr_violations.append(
                    {
                        "nfr": "NFR-P1",
                        "requirement": f">={NFR_P1_THROUGHPUT} words/sec",
                        "actual": f"{value:.1f} words/sec",
                        "metric": metric,
                    }
                )
                print(f"  ❌ NFR-P1 Violation: {metric}")
                print(f"      Required: >={NFR_P1_THROUGHPUT} words/sec")
                print(f"      Actual: {value:.1f} words/sec")
                nfr_pass = False

        # Check NFR-P2: Memory
        memory_metrics = [k for k in self.test_results if "memory" in k.lower()]
        for metric in memory_metrics:
            value = self.test_results[metric]["value"]
            if value > NFR_P2_MEMORY_LIMIT:
                self.nfr_violations.append(
                    {
                        "nfr": "NFR-P2",
                        "requirement": f"<={NFR_P2_MEMORY_LIMIT} MB",
                        "actual": f"{value:.1f} MB",
                        "metric": metric,
                    }
                )
                print(f"  ❌ NFR-P2 Violation: {metric}")
                print(f"      Required: <={NFR_P2_MEMORY_LIMIT} MB")
                print(f"      Actual: {value:.1f} MB")
                nfr_pass = False

        # Check NFR-P3: Latency
        for component, max_latency in NFR_P3_LATENCY.items():
            component_metrics = [k for k in self.test_results if component in k.lower()]
            for metric in component_metrics:
                value = self.test_results[metric]["value"]
                if value > max_latency:
                    self.nfr_violations.append(
                        {
                            "nfr": "NFR-P3",
                            "component": component,
                            "requirement": f"<={max_latency} seconds",
                            "actual": f"{value:.2f} seconds",
                            "metric": metric,
                        }
                    )
                    print(f"  ❌ NFR-P3 Violation: {metric}")
                    print(f"      Component: {component}")
                    print(f"      Required: <={max_latency} seconds")
                    print(f"      Actual: {value:.2f} seconds")
                    nfr_pass = False

        if nfr_pass:
            print("  ✅ All NFRs satisfied")

        return nfr_pass

    def generate_regression_report(self) -> None:
        """Generate detailed regression report."""
        if not self.regressions and not self.nfr_violations:
            return

        report_path = PROJECT_ROOT / "performance_regression_report.md"

        with open(report_path, "w") as f:
            f.write("# Performance Regression Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")

            if self.regressions:
                f.write("## Performance Regressions\n\n")
                f.write("| Metric | Expected | Actual | Delta | Status |\n")
                f.write("|--------|----------|--------|-------|--------|\n")

                for reg in self.regressions:
                    f.write(
                        f"| {reg['metric']} | {reg['expected']:.3f} {reg['unit']} | "
                        f"{reg['actual']:.3f} {reg['unit']} | +{reg['delta_pct']:.1f}% | ⚠️ |\n"
                    )

            if self.nfr_violations:
                f.write("\n## NFR Violations\n\n")
                f.write("| NFR | Requirement | Actual | Metric | Status |\n")
                f.write("|-----|-------------|--------|--------|--------|\n")

                for viol in self.nfr_violations:
                    f.write(
                        f"| {viol['nfr']} | {viol['requirement']} | "
                        f"{viol['actual']} | {viol['metric']} | ❌ |\n"
                    )

            f.write("\n## Recommendations\n\n")
            f.write("1. Review recent changes that may have impacted performance\n")
            f.write("2. Profile the affected components to identify bottlenecks\n")
            f.write(
                "3. Consider optimization strategies or adjust baselines if changes are intentional\n"
            )

        print(f"\n📄 Regression report saved to {report_path}")

    def update_baseline_documentation(self) -> bool:
        """
        Update baseline documentation with current results.

        Returns:
            True if update successful
        """
        if not self.update_baseline:
            return True

        print("\n📝 Updating baseline documentation...")

        # Find or create baseline file for current epic
        baseline_file = DOCS_DIR / "performance-baselines-epic-current.md"

        try:
            # Read existing content or create new
            if baseline_file.exists():
                content = baseline_file.read_text()
            else:
                content = "# Performance Baselines - Current\n\n"
                content += f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n"
                content += "**Status:** Auto-generated\n\n"

            # Add new baseline section
            content += f"\n## Updated Baselines ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"

            # Add performance table
            content += "| Metric | Value | Unit | Component |\n"
            content += "|--------|-------|------|----------|\n"

            for key, result in self.test_results.items():
                component = key.split("_")[0] if "_" in key else "unknown"
                content += f"| {key} | {result['value']:.3f} | {result['unit']} | {component} |\n"

            # Write updated content
            baseline_file.write_text(content)

            print(f"  ✅ Updated {baseline_file.name}")
            return True

        except Exception as e:
            logger.error("baseline_update_error", error=str(e))
            print(f"  ❌ Failed to update baseline: {e}")
            return False

    def generate_summary(self) -> bool:
        """Generate and display summary of validation results."""
        print("\n" + "=" * 70)
        print("📊 Performance Validation Summary")
        print("=" * 70)

        # Metrics summary
        print(f"\n📈 Metrics Validated: {len(self.test_results)}")
        print(f"⚠️  Regressions Found: {len(self.regressions)}")
        print(f"🚨 NFR Violations: {len(self.nfr_violations)}")

        # Performance summary
        elapsed = time.time() - self.start_time
        print(f"\n⏱️  Validation completed in {elapsed:.1f} seconds")

        # Overall status
        if not self.regressions and not self.nfr_violations:
            print("\n✅ Performance validation PASSED")
            print("All metrics within acceptable limits")
        else:
            print("\n❌ Performance validation FAILED")

            if self.regressions:
                print(f"\nRegressions detected in {len(self.regressions)} metrics:")
                for reg in self.regressions[:3]:  # Show top 3
                    print(f"  • {reg['metric']}: +{reg['delta_pct']:.1f}% regression")

            if self.nfr_violations:
                print(f"\nNFR violations in {len(self.nfr_violations)} requirements:")
                for viol in self.nfr_violations[:3]:  # Show top 3
                    print(f"  • {viol['nfr']}: {viol['metric']}")

        # CI/CD exit code
        if self.ci_mode:
            success = not self.regressions and not self.nfr_violations
            print(f"\nCI/CD Exit Code: {0 if success else 1}")
            return success

        return True

    def run(self) -> bool:
        """
        Run the complete performance validation process.

        Returns:
            True if validation passed
        """
        self.print_header()

        # If component specified, use its tests
        if self.component:
            if self.component in COMPONENT_MAPPING:
                test_modules = COMPONENT_MAPPING[self.component]
                print(f"📦 Testing component: {self.component}")
            else:
                print(f"❌ Unknown component: {self.component}")
                print(f"   Available: {', '.join(COMPONENT_MAPPING.keys())}")
                return False
        else:
            # Detect changed files and determine tests
            test_modules = self.detect_changed_files()

        # Parse baseline documents
        self.parse_baseline_documents()

        # Run performance tests
        if not test_modules:
            print("ℹ️  No performance tests to run")
            return True

        tests_passed = self.run_performance_tests(test_modules)

        if not tests_passed and self.ci_mode:
            print("\n❌ Performance tests failed")
            return False

        # Compare with baselines
        if self.test_results:
            self.compare_with_baselines()

        # Check NFR compliance
        self.check_nfr_violations()

        # Generate regression report if needed
        if self.regressions or self.nfr_violations:
            self.generate_regression_report()

        # Update baseline if requested
        if self.update_baseline and self.test_results:
            self.update_baseline_documentation()

        # Generate summary
        return self.generate_summary()


def main() -> None:
    """Main entry point for the performance validator."""
    parser = argparse.ArgumentParser(
        description="Performance baseline validator for Data Extraction Tool"
    )
    parser.add_argument(
        "--component",
        choices=["extract", "normalize", "chunk", "semantic", "output"],
        help="Test specific component only",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline documentation with current results",
    )
    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="CI/CD mode with strict failures",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Run validator
    validator = PerformanceValidator(
        component=args.component,
        update_baseline=args.update_baseline,
        ci_mode=args.ci_mode,
        verbose=args.verbose,
    )

    success = validator.run()

    # Exit with appropriate code for CI/CD
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

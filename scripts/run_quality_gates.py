#!/usr/bin/env python3
"""
Quality Gate Runner

Unified quality check execution for the Data Extraction Tool project.
Runs black, ruff, mypy sequentially with proper error handling and reporting.

Usage:
    python scripts/run_quality_gates.py                    # Default mode
    python scripts/run_quality_gates.py --pre-commit       # Quick pre-commit checks
    python scripts/run_quality_gates.py --ci-mode          # Full CI pipeline checks
    python scripts/run_quality_gates.py --changed-only     # Test only changed files
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import structlog

# Configure structured logging
logger = structlog.get_logger()

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
GREENFIELD_SRC = SRC_DIR / "data_extract"

# Coverage thresholds
GREENFIELD_COVERAGE_THRESHOLD = 80  # >80% for greenfield code
OVERALL_COVERAGE_THRESHOLD = 60  # >60% overall


class QualityGateRunner:
    """Runs quality checks and generates reports."""

    def __init__(self, mode: str = "default", changed_only: bool = False):
        """
        Initialize the quality gate runner.

        Args:
            mode: Execution mode (default, pre-commit, ci-mode)
            changed_only: If True, run tests only for changed files
        """
        self.mode = mode
        self.changed_only = changed_only
        self.results: Dict[str, dict] = {}
        self.start_time = time.time()
        logger.info("initialized_quality_gate_runner", mode=mode, changed_only=changed_only)

    def run_black_check(self) -> Tuple[bool, str]:
        """
        Run Black formatting check.

        Returns:
            Tuple of (success, output)
        """
        logger.info("running_black_check")
        cmd = ["black", "--check", "src/", "tests/", "scripts/"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
            success = result.returncode == 0

            if success:
                output = "✅ Black: All files formatted correctly"
            else:
                output = f"❌ Black: Formatting issues found\n{result.stdout}\n{result.stderr}"

            self.results["black"] = {
                "passed": success,
                "output": output,
                "command": " ".join(cmd),
            }

            logger.info("black_check_complete", success=success)
            return success, output

        except FileNotFoundError:
            output = "⚠️  Black not installed. Run: pip install black"
            self.results["black"] = {"passed": False, "output": output}
            return False, output

    def run_ruff_check(self) -> Tuple[bool, str]:
        """
        Run Ruff linting check.

        Returns:
            Tuple of (success, output)
        """
        logger.info("running_ruff_check")
        cmd = ["ruff", "check", "src/", "tests/", "scripts/"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
            success = result.returncode == 0

            if success:
                output = "✅ Ruff: No linting violations found"
            else:
                output = f"❌ Ruff: Linting violations found\n{result.stdout}\n{result.stderr}"

            self.results["ruff"] = {
                "passed": success,
                "output": output,
                "command": " ".join(cmd),
            }

            logger.info("ruff_check_complete", success=success)
            return success, output

        except FileNotFoundError:
            output = "⚠️  Ruff not installed. Run: pip install ruff"
            self.results["ruff"] = {"passed": False, "output": output}
            return False, output

    def run_mypy_check(self) -> Tuple[bool, str]:
        """
        Run mypy type checking.

        Returns:
            Tuple of (success, output)
        """
        logger.info("running_mypy_check")

        # Run mypy on greenfield code (strict mode)
        cmd = ["mypy", "src/data_extract/", "--strict"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
            success = result.returncode == 0

            if success:
                output = "✅ Mypy: No type violations found"
            else:
                output = f"❌ Mypy: Type violations found\n{result.stdout}\n{result.stderr}"

            self.results["mypy"] = {
                "passed": success,
                "output": output,
                "command": " ".join(cmd),
            }

            logger.info("mypy_check_complete", success=success)
            return success, output

        except FileNotFoundError:
            output = "⚠️  Mypy not installed. Run: pip install mypy"
            self.results["mypy"] = {"passed": False, "output": output}
            return False, output

    def detect_changed_files(self) -> List[Path]:
        """
        Detect files changed since last commit.

        Returns:
            List of changed file paths
        """
        logger.info("detecting_changed_files")

        try:
            # Get list of modified files
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

            if result.returncode != 0:
                logger.warning("git_diff_failed", stderr=result.stderr)
                return []

            changed = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    path = PROJECT_ROOT / line
                    if path.exists() and path.suffix == ".py":
                        changed.append(path)

            logger.info("changed_files_detected", count=len(changed))
            return changed

        except Exception as e:
            logger.error("failed_to_detect_changes", error=str(e))
            return []

    def run_tests(self) -> Tuple[bool, str, Dict[str, float]]:
        """
        Run pytest with coverage.

        Returns:
            Tuple of (success, output, coverage_data)
        """
        logger.info("running_tests", changed_only=self.changed_only)

        cmd = ["pytest", "--cov=src", "--cov-report=term"]

        if self.changed_only:
            # Detect changed files and map to test files
            changed = self.detect_changed_files()
            if changed:
                test_files = self._map_source_to_tests(changed)
                if test_files:
                    cmd.extend([str(f) for f in test_files])
                else:
                    logger.info("no_relevant_test_files")
                    return True, "No test files for changed sources", {}

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
            success = result.returncode == 0

            # Parse coverage from output
            coverage_data = self._parse_coverage(result.stdout)

            if success:
                output = "✅ Tests: All tests passed"
            else:
                output = f"❌ Tests: Some tests failed\n{result.stdout[-2000:]}"  # Last 2000 chars

            self.results["pytest"] = {
                "passed": success,
                "output": output,
                "coverage": coverage_data,
                "command": " ".join(cmd),
            }

            logger.info("tests_complete", success=success, coverage=coverage_data)
            return success, output, coverage_data

        except FileNotFoundError:
            output = "⚠️  Pytest not installed. Run: pip install pytest pytest-cov"
            self.results["pytest"] = {"passed": False, "output": output}
            return False, output, {}

    def _map_source_to_tests(self, source_files: List[Path]) -> List[Path]:
        """
        Map source files to their corresponding test files.

        Args:
            source_files: List of source file paths

        Returns:
            List of test file paths
        """
        test_files = []

        for source in source_files:
            # Convert src/module/file.py to tests/unit/data_extract/module/test_file.py
            if source.is_relative_to(SRC_DIR):
                rel_path = source.relative_to(SRC_DIR)
                # Check if it's a data_extract module
                if str(rel_path).startswith("data_extract/"):
                    # New structure: tests/unit/data_extract/module/test_file.py
                    module_path = rel_path.relative_to("data_extract")
                    test_path = (
                        TESTS_DIR
                        / "unit"
                        / "data_extract"
                        / module_path.parent
                        / f"test_{module_path.name}"
                    )
                else:
                    # Old structure for brownfield: tests/unit/test_module/test_file.py
                    test_path = (
                        TESTS_DIR / "unit" / f"test_{rel_path.parent}" / f"test_{rel_path.name}"
                    )
                if test_path.exists():
                    test_files.append(test_path)

            # Scripts to test_scripts mapping
            elif source.is_relative_to(SCRIPTS_DIR):
                test_path = TESTS_DIR / "unit" / "test_scripts" / f"test_{source.name}"
                if test_path.exists():
                    test_files.append(test_path)

        return test_files

    def _parse_coverage(self, output: str) -> Dict[str, float]:
        """
        Parse coverage percentages from pytest output.

        Args:
            output: Pytest output

        Returns:
            Dictionary with coverage percentages
        """
        coverage = {}

        # Look for coverage report in output
        for line in output.split("\n"):
            if "TOTAL" in line and "%" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if "%" in part:
                        try:
                            coverage["overall"] = float(part.rstrip("%"))
                        except ValueError:
                            pass

            # Look for greenfield coverage
            if "data_extract" in line and "%" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if "%" in part:
                        try:
                            coverage["greenfield"] = float(part.rstrip("%"))
                        except ValueError:
                            pass

        return coverage

    def check_coverage_thresholds(self, coverage: Dict[str, float]) -> Tuple[bool, str]:
        """
        Check if coverage meets thresholds.

        Args:
            coverage: Coverage data

        Returns:
            Tuple of (meets_thresholds, message)
        """
        messages = []
        meets_thresholds = True

        # Check greenfield coverage
        if "greenfield" in coverage:
            if coverage["greenfield"] >= GREENFIELD_COVERAGE_THRESHOLD:
                messages.append(
                    f"✅ Greenfield coverage: {coverage['greenfield']:.1f}% (>={GREENFIELD_COVERAGE_THRESHOLD}%)"
                )
            else:
                messages.append(
                    f"❌ Greenfield coverage: {coverage['greenfield']:.1f}% (<{GREENFIELD_COVERAGE_THRESHOLD}%)"
                )
                meets_thresholds = False
        else:
            messages.append("⚠️  Greenfield coverage not measured")

        # Check overall coverage
        if "overall" in coverage:
            if coverage["overall"] >= OVERALL_COVERAGE_THRESHOLD:
                messages.append(
                    f"✅ Overall coverage: {coverage['overall']:.1f}% (>={OVERALL_COVERAGE_THRESHOLD}%)"
                )
            else:
                messages.append(
                    f"❌ Overall coverage: {coverage['overall']:.1f}% (<{OVERALL_COVERAGE_THRESHOLD}%)"
                )
                meets_thresholds = False
        else:
            messages.append("⚠️  Overall coverage not measured")

        return meets_thresholds, "\n".join(messages)

    def check_spacy_model(self) -> Tuple[bool, str]:
        """
        Check if spaCy en_core_web_md model is installed.

        Returns:
            Tuple of (installed, message)
        """
        logger.info("checking_spacy_model")

        try:
            import spacy

            try:
                nlp = spacy.load("en_core_web_md")
                output = f"✅ spaCy model installed: en_core_web_md v{nlp.meta['version']}"
                success = True
            except OSError:
                output = (
                    "❌ spaCy model not installed. Run: python -m spacy download en_core_web_md"
                )
                success = False

            self.results["spacy"] = {"passed": success, "output": output}
            return success, output

        except ImportError:
            output = "⚠️  spaCy not installed. Run: pip install spacy"
            self.results["spacy"] = {"passed": False, "output": output}
            return False, output

    def generate_report(self, format: str = "both") -> Dict[str, str]:
        """
        Generate quality report in specified format.

        Args:
            format: Report format (json, markdown, both)

        Returns:
            Dictionary with report(s)
        """
        reports = {}
        elapsed_time = time.time() - self.start_time

        # Add metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode,
            "changed_only": self.changed_only,
            "elapsed_seconds": round(elapsed_time, 2),
        }

        # JSON report
        if format in ["json", "both"]:
            json_report = {"metadata": metadata, "results": self.results}
            reports["json"] = json.dumps(json_report, indent=2)

        # Markdown report
        if format in ["markdown", "both"]:
            md_lines = [
                "# Quality Gate Report",
                "",
                f"**Generated:** {metadata['timestamp']}",
                f"**Mode:** {metadata['mode']}",
                f"**Elapsed Time:** {metadata['elapsed_seconds']}s",
                "",
                "## Results",
                "",
            ]

            # Summary
            passed = sum(1 for r in self.results.values() if r.get("passed", False))
            total = len(self.results)
            md_lines.append(f"**Overall:** {passed}/{total} checks passed")
            md_lines.append("")

            # Individual results
            for check, result in self.results.items():
                md_lines.append(f"### {check.title()}")
                md_lines.append("")
                md_lines.append(result.get("output", "No output"))
                if "coverage" in result:
                    md_lines.append("")
                    md_lines.append("**Coverage:**")
                    for key, value in result["coverage"].items():
                        md_lines.append(f"- {key}: {value:.1f}%")
                md_lines.append("")

            reports["markdown"] = "\n".join(md_lines)

        return reports

    def run_all_checks(self) -> bool:
        """
        Run all quality checks based on mode.

        Returns:
            True if all checks pass
        """
        all_passed = True

        # Run checks based on mode
        if self.mode == "pre-commit":
            # Quick checks for pre-commit
            checks = [
                ("Black", self.run_black_check),
                ("Ruff", self.run_ruff_check),
                ("Mypy", self.run_mypy_check),
            ]
        else:
            # Full checks for default and CI mode
            checks = [
                ("Black", self.run_black_check),
                ("Ruff", self.run_ruff_check),
                ("Mypy", self.run_mypy_check),
                ("spaCy", self.check_spacy_model),
            ]

            # Add tests for CI mode
            if self.mode == "ci-mode":
                checks.append(("Tests", lambda: self.run_tests()[:2]))

        # Execute checks sequentially
        for name, check_func in checks:
            print(f"\n🔍 Running {name}...")
            success, output = check_func()[:2]  # Get first two values
            print(output)

            if not success:
                all_passed = False
                if self.mode == "pre-commit":
                    # Stop on first failure in pre-commit mode
                    break

        # Check coverage if tests were run
        if "pytest" in self.results and "coverage" in self.results["pytest"]:
            coverage = self.results["pytest"]["coverage"]
            meets_thresholds, coverage_msg = self.check_coverage_thresholds(coverage)
            print(f"\n📊 Coverage Check:\n{coverage_msg}")
            if not meets_thresholds:
                all_passed = False

        return all_passed


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run quality gates for Data Extraction Tool")

    parser.add_argument(
        "--pre-commit",
        action="store_true",
        help="Quick mode for pre-commit hooks (black, ruff, mypy only)",
    )

    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="Full mode for CI pipeline (includes tests and coverage)",
    )

    parser.add_argument(
        "--changed-only", action="store_true", help="Run tests only for changed files"
    )

    parser.add_argument(
        "--report-format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Report format (default: both)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("quality-reports"),
        help="Directory for report files",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_arguments()

    # Determine mode
    if args.pre_commit:
        mode = "pre-commit"
    elif args.ci_mode:
        mode = "ci-mode"
    else:
        mode = "default"

    print(f"🚀 Quality Gate Runner - {mode.upper()} mode")
    print("=" * 50)

    # Run quality checks
    runner = QualityGateRunner(mode=mode, changed_only=args.changed_only)
    all_passed = runner.run_all_checks()

    # Generate and save reports
    reports = runner.generate_report(format=args.report_format)

    # Save reports to files
    if not args.pre_commit:  # Don't save reports in pre-commit mode
        args.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if "json" in reports:
            json_path = args.output_dir / f"quality_report_{timestamp}.json"
            json_path.write_text(reports["json"])
            print(f"\n📄 JSON report saved: {json_path}")

        if "markdown" in reports:
            md_path = args.output_dir / f"quality_report_{timestamp}.md"
            md_path.write_text(reports["markdown"])
            print(f"📄 Markdown report saved: {md_path}")

    # Final status
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All quality gates PASSED!")
        return 0
    else:
        print("❌ Some quality gates FAILED - see details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

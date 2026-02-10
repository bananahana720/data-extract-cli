#!/usr/bin/env python3
"""
Dependency Auditor for Test Infrastructure

Scans test files for import statements, cross-references with pyproject.toml,
identifies missing dependencies, and generates comprehensive audit reports.

This tool ensures test dependencies are properly declared and maintained.

Usage:
    python scripts/audit_dependencies.py
    python scripts/audit_dependencies.py --output markdown
    python scripts/audit_dependencies.py --cache-dir .cache --update-docs
"""

import argparse
import ast
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog  # type: ignore[import-not-found]

# Configure structured logging
logger = structlog.get_logger()

# Constants
TEST_DIR = Path(__file__).parent.parent / "tests"
PROJECT_ROOT = Path(__file__).parent.parent
CACHE_DIR = PROJECT_ROOT / ".cache" / "dependency_audit"
DOCS_DIR = PROJECT_ROOT / "docs"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

# Standard library modules that don't need to be declared
STDLIB_MODULES = {
    "abc",
    "argparse",
    "ast",
    "asyncio",
    "base64",
    "collections",
    "contextlib",
    "copy",
    "csv",
    "datetime",
    "decimal",
    "difflib",
    "enum",
    "functools",
    "hashlib",
    "io",
    "itertools",
    "json",
    "logging",
    "math",
    "multiprocessing",
    "os",
    "pathlib",
    "pickle",
    "platform",
    "pprint",
    "queue",
    "random",
    "re",
    "shutil",
    "signal",
    "socket",
    "sqlite3",
    "subprocess",
    "sys",
    "tempfile",
    "textwrap",
    "threading",
    "time",
    "traceback",
    "typing",
    "unittest",
    "urllib",
    "uuid",
    "warnings",
    "weakref",
    "xml",
    "zipfile",
}

# Project internal modules (don't need declaration)
PROJECT_MODULES = {"data_extract", "src", "tests"}


class DependencyAuditor:
    """Audits test dependencies against declared dependencies in pyproject.toml."""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        """
        Initialize the dependency auditor.

        Args:
            cache_dir: Directory for caching analysis results
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.test_imports: Dict[str, Set[str]] = defaultdict(set)
        self.declared_deps: Set[str] = set()
        self.missing_deps: Set[str] = set()
        self.unused_deps: Set[str] = set()
        self.cache: Dict[str, Any] = {}
        logger.info("initialized_dependency_auditor", cache_dir=str(cache_dir))

    def scan_test_files(self, test_dir: Path = TEST_DIR) -> Dict[str, Set[str]]:
        """
        Scan all test files for import statements using AST.

        Args:
            test_dir: Directory containing test files

        Returns:
            Dictionary mapping test files to their imports
        """
        logger.info("scanning_test_files", test_dir=str(test_dir))

        for test_file in test_dir.rglob("*.py"):
            if "__pycache__" in str(test_file):
                continue

            # Check cache based on file mtime
            file_mtime = test_file.stat().st_mtime
            cache_key = str(test_file)

            if cache_key in self.cache and self.cache[cache_key]["mtime"] == file_mtime:
                # Use cached result
                imports = self.cache[cache_key]["imports"]
                logger.debug("using_cached_imports", file=str(test_file))
            else:
                # Parse file for imports
                imports = self._extract_imports(test_file)
                # Update cache
                self.cache[cache_key] = {"mtime": file_mtime, "imports": imports}
                logger.debug("parsed_imports", file=str(test_file), count=len(imports))

            # Try to make path relative to PROJECT_ROOT, otherwise use absolute path
            try:
                relative_path = test_file.relative_to(PROJECT_ROOT)
            except ValueError:
                # File is outside PROJECT_ROOT (e.g., in tests), use absolute path
                relative_path = test_file

            self.test_imports[str(relative_path)] = imports

        # Save cache
        self._save_cache()

        logger.info(
            "scan_complete",
            files_scanned=len(self.test_imports),
            total_imports=sum(len(imp) for imp in self.test_imports.values()),
        )

        return self.test_imports

    def _extract_imports(self, file_path: Path) -> Set[str]:
        """
        Extract import statements from a Python file using AST.

        Args:
            file_path: Path to Python file

        Returns:
            Set of imported module names
        """
        imports = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                        imports.add(module_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split(".")[0]
                        imports.add(module_name)
        except Exception as e:
            logger.warning("failed_to_parse_file", file=str(file_path), error=str(e))

        # Filter out standard library and project internal modules
        imports = {
            imp for imp in imports if imp not in STDLIB_MODULES and imp not in PROJECT_MODULES
        }

        return imports

    def load_declared_dependencies(self, pyproject_path: Path = PYPROJECT_PATH) -> Set[str]:
        """
        Load declared dependencies from pyproject.toml.

        Args:
            pyproject_path: Path to pyproject.toml

        Returns:
            Set of declared package names
        """
        logger.info("loading_declared_dependencies", pyproject_path=str(pyproject_path))

        try:
            import toml  # type: ignore[import-untyped]
        except ImportError:
            # Fallback to parsing manually
            logger.warning("toml_not_installed_using_manual_parser")
            return self._parse_pyproject_manually(pyproject_path)

        with open(pyproject_path, "r") as f:
            data = toml.load(f)

        # Extract dependencies from various sections
        deps = set()

        # Main dependencies
        if "project" in data and "dependencies" in data["project"]:
            for dep in data["project"]["dependencies"]:
                package_name = self._extract_package_name(dep)
                if package_name:
                    deps.add(package_name)

        # Optional dependencies (including dev)
        if "project" in data and "optional-dependencies" in data["project"]:
            for group, group_deps in data["project"]["optional-dependencies"].items():
                for dep in group_deps:
                    package_name = self._extract_package_name(dep)
                    if package_name:
                        deps.add(package_name)

        self.declared_deps = deps
        logger.info("loaded_dependencies", count=len(deps))

        return deps

    def _parse_pyproject_manually(self, pyproject_path: Path) -> Set[str]:
        """
        Manually parse pyproject.toml when toml library is not available.

        Args:
            pyproject_path: Path to pyproject.toml

        Returns:
            Set of declared package names
        """
        deps = set()

        with open(pyproject_path, "r") as f:
            content = f.read()

        # Regular expression to match dependency declarations
        dep_pattern = r'"([a-zA-Z0-9_-]+)(?:\[.*?\])?[><=!~]'

        for match in re.finditer(dep_pattern, content):
            package_name = match.group(1)
            # Normalize package names
            package_name = package_name.lower().replace("-", "_")
            deps.add(package_name)

        return deps

    def _extract_package_name(self, dep_spec: str) -> Optional[str]:
        """
        Extract package name from dependency specification.

        Args:
            dep_spec: Dependency specification (e.g., "pytest>=8.0.0")

        Returns:
            Package name or None
        """
        # Remove version specifiers and extras
        match = re.match(r"^([a-zA-Z0-9_-]+)", dep_spec)
        if match:
            # Normalize package name (convert hyphens to underscores)
            package_name = match.group(1).lower().replace("-", "_")
            return package_name
        return None

    def cross_reference(self) -> Tuple[Set[str], Set[str]]:
        """
        Cross-reference test imports with declared dependencies.

        Returns:
            Tuple of (missing_dependencies, unused_dependencies)
        """
        logger.info("cross_referencing_dependencies")

        # Collect all unique imports from tests
        all_test_imports = set()
        for imports in self.test_imports.values():
            all_test_imports.update(imports)

        # Normalize import names for comparison
        normalized_imports = {self._normalize_import_name(imp) for imp in all_test_imports}
        normalized_declared = {self._normalize_import_name(dep) for dep in self.declared_deps}

        # Find missing dependencies (used in tests but not declared)
        self.missing_deps = normalized_imports - normalized_declared

        # Find unused dependencies (declared but not used in tests)
        # Note: This might include dependencies used by src code, not just tests
        self.unused_deps = normalized_declared - normalized_imports

        logger.info(
            "cross_reference_complete",
            missing_count=len(self.missing_deps),
            unused_count=len(self.unused_deps),
        )

        return self.missing_deps, self.unused_deps

    def _normalize_import_name(self, name: str) -> str:
        """
        Normalize import/package names for comparison.

        Args:
            name: Import or package name

        Returns:
            Normalized name
        """
        # Common mappings (keys should be lowercase)
        mappings = {
            "pil": "pillow",
            "cv2": "opencv_python",
            "sklearn": "scikit_learn",
            "yaml": "pyyaml",
            "bs4": "beautifulsoup4",
        }

        normalized = name.lower().replace("-", "_")
        return mappings.get(normalized, normalized)

    def generate_report(self, output_format: str = "json") -> str:
        """
        Generate dependency audit report.

        Args:
            output_format: Output format (json or markdown)

        Returns:
            Formatted report
        """
        logger.info("generating_report", format=output_format)

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_test_files": len(self.test_imports),
                "total_imports": sum(len(imp) for imp in self.test_imports.values()),
                "declared_dependencies": len(self.declared_deps),
                "missing_dependencies": len(self.missing_deps),
                "potentially_unused": len(self.unused_deps),
            },
            "missing_dependencies": sorted(self.missing_deps),
            "potentially_unused": sorted(self.unused_deps),
            "test_imports": {file: sorted(imports) for file, imports in self.test_imports.items()},
            "recommendations": self._generate_recommendations(),
        }

        if output_format == "markdown":
            return self._format_markdown_report(report_data)
        else:
            return json.dumps(report_data, indent=2)

    def _generate_recommendations(self) -> List[str]:
        """
        Generate actionable recommendations based on audit findings.

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if self.missing_deps:
            recommendations.append(
                f"Add {len(self.missing_deps)} missing dependencies to pyproject.toml [dev] section"
            )
            for dep in sorted(self.missing_deps)[:5]:  # Show first 5
                recommendations.append(f"  - Add: {dep}")
            if len(self.missing_deps) > 5:
                recommendations.append(f"  ... and {len(self.missing_deps) - 5} more")

        if self.unused_deps:
            recommendations.append(
                f"Review {len(self.unused_deps)} potentially unused test dependencies"
            )
            recommendations.append("  Note: These may be used by src code or optional features")

        if not self.missing_deps and not self.unused_deps:
            recommendations.append("✅ All test dependencies are properly declared!")

        return recommendations

    def _format_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """
        Format report as markdown.

        Args:
            report_data: Report data dictionary

        Returns:
            Markdown formatted report
        """
        md_lines = [
            "# Test Dependency Audit Report",
            "",
            f"**Generated:** {report_data['timestamp']}",
            "",
            "## Summary",
            "",
            f"- **Test Files Scanned:** {report_data['summary']['total_test_files']}",
            f"- **Total Imports Found:** {report_data['summary']['total_imports']}",
            f"- **Declared Dependencies:** {report_data['summary']['declared_dependencies']}",
            f"- **Missing Dependencies:** {report_data['summary']['missing_dependencies']}",
            f"- **Potentially Unused:** {report_data['summary']['potentially_unused']}",
            "",
        ]

        if report_data["missing_dependencies"]:
            md_lines.extend(
                [
                    "## ⚠️ Missing Dependencies",
                    "",
                    "These packages are imported in tests but not declared in pyproject.toml:",
                    "",
                ]
            )
            for dep in report_data["missing_dependencies"]:
                md_lines.append(f"- `{dep}`")
            md_lines.append("")

        if report_data["potentially_unused"]:
            md_lines.extend(
                [
                    "## 📋 Potentially Unused Test Dependencies",
                    "",
                    "These are declared but not found in test imports:",
                    "(Note: May be used by src code or optional features)",
                    "",
                ]
            )
            for dep in report_data["potentially_unused"]:
                md_lines.append(f"- `{dep}`")
            md_lines.append("")

        md_lines.extend(
            [
                "## 💡 Recommendations",
                "",
            ]
        )
        for rec in report_data["recommendations"]:
            md_lines.append(rec)
        md_lines.append("")

        return "\n".join(md_lines)

    def update_documentation(self, report: str, docs_dir: Path = DOCS_DIR) -> None:
        """
        Update test dependency documentation.

        Args:
            report: Audit report content
            docs_dir: Documentation directory
        """
        logger.info("updating_documentation", docs_dir=str(docs_dir))

        # Create processes directory if needed
        processes_dir = docs_dir / "processes"
        processes_dir.mkdir(parents=True, exist_ok=True)

        # Write audit report
        report_path = processes_dir / "test-dependency-audit-report.md"
        with open(report_path, "w") as f:
            f.write(report)

        logger.info("documentation_updated", path=str(report_path))

    def _save_cache(self) -> None:
        """Save cache to disk."""
        cache_file = self.cache_dir / "import_cache.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
            logger.debug("cache_saved", path=str(cache_file))
        except Exception as e:
            logger.warning("failed_to_save_cache", error=str(e))

    def _load_cache(self) -> None:
        """Load cache from disk."""
        cache_file = self.cache_dir / "import_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    self.cache = json.load(f)
                logger.debug("cache_loaded", path=str(cache_file))
            except Exception as e:
                logger.warning("failed_to_load_cache", error=str(e))
                self.cache = {}
        else:
            self.cache = {}


def main() -> None:
    """Main entry point for the dependency auditor."""
    parser = argparse.ArgumentParser(
        description="Audit test dependencies against pyproject.toml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate JSON report
  python scripts/audit_dependencies.py

  # Generate markdown report
  python scripts/audit_dependencies.py --output markdown

  # Update documentation
  python scripts/audit_dependencies.py --update-docs

  # Use custom cache directory
  python scripts/audit_dependencies.py --cache-dir /tmp/dep_cache
        """,
    )

    parser.add_argument(
        "--output",
        choices=["json", "markdown"],
        default="json",
        help="Output format for the audit report (default: json)",
    )

    parser.add_argument(
        "--cache-dir", type=Path, default=CACHE_DIR, help="Directory for caching analysis results"
    )

    parser.add_argument(
        "--update-docs", action="store_true", help="Update test dependency documentation"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        )

    try:
        # Initialize auditor
        auditor = DependencyAuditor(cache_dir=args.cache_dir)

        # Load cache
        auditor._load_cache()

        # Scan test files
        auditor.scan_test_files()

        # Load declared dependencies
        auditor.load_declared_dependencies()

        # Cross-reference
        missing, unused = auditor.cross_reference()

        # Generate report
        report = auditor.generate_report(output_format=args.output)

        # Output report
        print(report)

        # Update documentation if requested
        if args.update_docs:
            auditor.update_documentation(report)
            print("\n✅ Documentation updated in docs/processes/", file=sys.stderr)

        # Exit with error code if missing dependencies found
        if missing:
            print(f"\n⚠️  Found {len(missing)} missing dependencies!", file=sys.stderr)
            sys.exit(1)
        else:
            print("\n✅ All test dependencies are properly declared!", file=sys.stderr)
            sys.exit(0)

    except Exception as e:
        logger.error("dependency_audit_failed", error=str(e))
        print(f"❌ Audit failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

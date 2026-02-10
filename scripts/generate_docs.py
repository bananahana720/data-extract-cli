#!/usr/bin/env python3
"""
Documentation Generator

Automatically generates API documentation from code using AST parsing,
creates coverage reports, updates README sections, and generates architecture diagrams.

Usage:
    python scripts/generate_docs.py --output-dir docs/api
    python scripts/generate_docs.py --update-readme --coverage
    python scripts/generate_docs.py --architecture --format mermaid
"""

import argparse
import ast
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog  # type: ignore[import-not-found]
import yaml  # type: ignore[import-untyped]

# Configure structured logging
logger = structlog.get_logger()

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = PROJECT_ROOT / "docs"
COVERAGE_FILE = PROJECT_ROOT / ".coverage"


class DocumentationGenerator:
    """Generates documentation from Python source code using AST analysis."""

    def __init__(
        self,
        source_dir: Path = SRC_DIR,
        output_dir: Path = OUTPUT_DIR,
        config_file: Optional[Path] = None,
    ):
        """
        Initialize the documentation generator.

        Args:
            source_dir: Directory containing source code
            output_dir: Directory for output documentation
            config_file: Optional configuration file
        """
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.config = self._load_config(config_file) if config_file else {}
        self.modules_data: Dict[str, Any] = {}
        logger.info("initialized_documentation_generator", source_dir=str(source_dir))

    def _load_config(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file."""
        if config_file.suffix in [".yaml", ".yml"]:
            with open(config_file) as f:
                result = yaml.safe_load(f)
                return result if isinstance(result, dict) else {}
        elif config_file.suffix == ".json":
            with open(config_file) as f:
                result = json.load(f)
                return result if isinstance(result, dict) else {}
        else:
            logger.warning("unsupported_config_format", file=str(config_file))
            return {}

    def extract_docstrings(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract docstrings and type hints from a Python file using AST.

        Args:
            file_path: Path to Python file

        Returns:
            Dictionary containing module info, classes, and functions
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            logger.error("ast_parse_error", file=str(file_path), error=str(e))
            return {}

        module_info: Dict[str, Any] = {
            "path": str(file_path.relative_to(self.source_dir)),
            "module_docstring": ast.get_docstring(tree) or "",
            "classes": [],
            "functions": [],
            "imports": [],
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node)
                module_info["classes"].append(class_info)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only extract module-level functions
                if node.col_offset == 0:
                    func_info = self._extract_function_info(node)
                    module_info["functions"].append(func_info)
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                import_info = self._extract_import_info(node)
                if import_info:
                    module_info["imports"].append(import_info)

        return module_info

    def _extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract information from a class definition."""
        class_info: Dict[str, Any] = {
            "name": node.name,
            "docstring": ast.get_docstring(node) or "",
            "bases": [self._get_name(base) for base in node.bases],
            "methods": [],
            "attributes": [],
        }

        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                method_info = self._extract_function_info(item)
                class_info["methods"].append(method_info)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Class attributes with type annotations
                attr_info = {
                    "name": item.target.id,
                    "type": self._get_annotation(item.annotation),
                    "value": self._get_value(item.value) if item.value else None,
                }
                class_info["attributes"].append(attr_info)

        return class_info

    def _extract_function_info(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Dict[str, Any]:
        """Extract information from a function definition."""
        func_info: Dict[str, Any] = {
            "name": node.name,
            "docstring": ast.get_docstring(node) or "",
            "async": isinstance(node, ast.AsyncFunctionDef),
            "args": [],
            "returns": None,
            "decorators": [self._get_name(d) for d in node.decorator_list],
        }

        # Extract arguments and type hints
        for arg in node.args.args:
            arg_info: Dict[str, Any] = {"name": arg.arg, "type": None, "default": None}
            if arg.annotation:
                arg_info["type"] = self._get_annotation(arg.annotation)
            func_info["args"].append(arg_info)

        # Extract default values
        defaults_start = len(node.args.args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            func_info["args"][defaults_start + i]["default"] = self._get_value(default)

        # Extract return type
        if node.returns:
            func_info["returns"] = self._get_annotation(node.returns)

        return func_info

    def _extract_import_info(self, node: ast.Import | ast.ImportFrom) -> Optional[str]:
        """Extract import information."""
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            return f"import {', '.join(names)}"
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            return f"from {module} import {', '.join(names)}"
        return None

    def _get_annotation(self, node: ast.AST) -> str:
        """Get string representation of a type annotation."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation(node.value)
            # Special handling for Dict, List, etc. with tuple slices
            if isinstance(node.slice, ast.Tuple):
                elements = [self._get_annotation(e) for e in node.slice.elts]
                slice_val = ", ".join(elements)
            else:
                slice_val = self._get_annotation(node.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(node, ast.Tuple):
            elements = [self._get_annotation(e) for e in node.elts]
            return f"({', '.join(elements)})"
        elif isinstance(node, ast.Attribute):
            value = self._get_annotation(node.value)
            return f"{value}.{node.attr}"
        elif isinstance(node, (ast.BinOp)) and isinstance(node.op, ast.BitOr):
            # Handle Union types (Type1 | Type2)
            left = self._get_annotation(node.left)
            right = self._get_annotation(node.right)
            return f"{left} | {right}"
        else:
            return ast.unparse(node)

    def _get_name(self, node: ast.AST) -> str:
        """Get name from various AST node types."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            return f"{value}.{node.attr}"
        else:
            return ast.unparse(node)

    def _get_value(self, node: ast.AST) -> Any:
        """Get value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, (ast.List, ast.Tuple)):
            return [self._get_value(e) for e in node.elts]
        elif isinstance(node, ast.Dict):
            return {
                self._get_value(k) if k else None: self._get_value(v)
                for k, v in zip(node.keys, node.values)
            }
        else:
            return ast.unparse(node)

    def generate_api_documentation(self, format: str = "markdown") -> None:
        """
        Generate API documentation for all Python modules.

        Args:
            format: Output format (markdown or html)
        """
        logger.info("generating_api_documentation", format=format)
        start_time = time.time()

        # Collect all Python files
        python_files = list(self.source_dir.rglob("*.py"))
        logger.info("found_python_files", count=len(python_files))

        # Extract information from each file
        for file_path in python_files:
            if "__pycache__" not in str(file_path):
                module_info = self.extract_docstrings(file_path)
                if module_info:
                    module_key = str(file_path.relative_to(self.source_dir))
                    self.modules_data[module_key] = module_info

        # Generate output files
        if format == "markdown":
            self._generate_markdown_docs()
        elif format == "html":
            self._generate_html_docs()
        else:
            logger.warning("unsupported_format", format=format)

        elapsed = time.time() - start_time
        logger.info("api_documentation_complete", elapsed=f"{elapsed:.2f}s")

    def _generate_markdown_docs(self) -> None:
        """Generate markdown documentation files."""
        api_dir = self.output_dir / "api"
        api_dir.mkdir(parents=True, exist_ok=True)

        # Generate module overview
        modules_md = self._generate_modules_overview()
        modules_file = api_dir / "modules.md"
        modules_file.write_text(modules_md)
        logger.info("generated_modules_overview", path=str(modules_file))

        # Generate class documentation
        classes_md = self._generate_classes_documentation()
        classes_file = api_dir / "classes.md"
        classes_file.write_text(classes_md)
        logger.info("generated_classes_documentation", path=str(classes_file))

        # Generate function documentation
        functions_md = self._generate_functions_documentation()
        functions_file = api_dir / "functions.md"
        functions_file.write_text(functions_md)
        logger.info("generated_functions_documentation", path=str(functions_file))

    def _generate_modules_overview(self) -> str:
        """Generate markdown for modules overview."""
        lines = ["# API Modules Overview", "", "## Module Index", ""]

        for module_path, info in sorted(self.modules_data.items()):
            module_name = module_path.replace("/", ".").replace(".py", "")
            docstring_preview = (
                info["module_docstring"][:100] + "..."
                if len(info["module_docstring"]) > 100
                else info["module_docstring"]
            )
            lines.append(f"### `{module_name}`")
            if docstring_preview:
                lines.append(f"_{docstring_preview}_")
            lines.append(f"- **Classes:** {len(info['classes'])}")
            lines.append(f"- **Functions:** {len(info['functions'])}")
            lines.append("")

        return "\n".join(lines)

    def _generate_classes_documentation(self) -> str:
        """Generate markdown for all classes."""
        lines = ["# API Classes Documentation", ""]

        for module_path, info in sorted(self.modules_data.items()):
            if not info["classes"]:
                continue

            module_name = module_path.replace("/", ".").replace(".py", "")
            lines.append(f"## Module: `{module_name}`")
            lines.append("")

            for class_info in info["classes"]:
                lines.append(f"### Class: `{class_info['name']}`")
                if class_info["bases"]:
                    lines.append(f"**Inherits from:** {', '.join(class_info['bases'])}")
                if class_info["docstring"]:
                    lines.append("")
                    lines.append(class_info["docstring"])
                lines.append("")

                # Document methods
                if class_info["methods"]:
                    lines.append("#### Methods:")
                    for method in class_info["methods"]:
                        self._format_function_markdown(method, lines, indent="- ")
                    lines.append("")

                # Document attributes
                if class_info["attributes"]:
                    lines.append("#### Attributes:")
                    for attr in class_info["attributes"]:
                        attr_line = f"- `{attr['name']}`"
                        if attr["type"]:
                            attr_line += f": `{attr['type']}`"
                        lines.append(attr_line)
                    lines.append("")

        return "\n".join(lines)

    def _generate_functions_documentation(self) -> str:
        """Generate markdown for module-level functions."""
        lines = ["# API Functions Documentation", ""]

        for module_path, info in sorted(self.modules_data.items()):
            if not info["functions"]:
                continue

            module_name = module_path.replace("/", ".").replace(".py", "")
            lines.append(f"## Module: `{module_name}`")
            lines.append("")

            for func in info["functions"]:
                self._format_function_markdown(func, lines)
                lines.append("")

        return "\n".join(lines)

    def _format_function_markdown(
        self, func: Dict[str, Any], lines: List[str], indent: str = ""
    ) -> None:
        """Format function information as markdown."""
        func_name = func["name"]
        if func["async"]:
            func_name = f"async {func_name}"

        # Function signature
        args_str = ", ".join(
            [
                f"{arg['name']}: {arg['type'] or 'Any'}"
                + (f" = {arg['default']}" if arg["default"] else "")
                for arg in func["args"]
            ]
        )
        returns_str = f" -> {func['returns']}" if func["returns"] else ""

        lines.append(f"{indent}**`{func_name}({args_str}){returns_str}`**")

        if func["decorators"]:
            lines.append(f"{indent}  Decorators: {', '.join(func['decorators'])}")

        if func["docstring"]:
            # Indent docstring properly
            docstring_lines = func["docstring"].split("\n")
            for line in docstring_lines:
                lines.append(f"{indent}  {line}")

    def _generate_html_docs(self) -> None:
        """Generate HTML documentation (placeholder for future enhancement)."""
        logger.warning("html_generation_not_implemented")
        # Could integrate with sphinx or pdoc3 here

    def generate_coverage_report(self) -> Dict[str, Any]:
        """
        Generate coverage report with visual representation.

        Returns:
            Coverage statistics dictionary
        """
        logger.info("generating_coverage_report")

        try:
            import coverage  # type: ignore[import-not-found]
        except ImportError:
            logger.error("coverage_module_not_installed")
            return {"error": "coverage module not installed"}

        cov = coverage.Coverage()

        # Load existing coverage data if available
        if COVERAGE_FILE.exists():
            cov.load()

            # Generate HTML report
            html_dir = self.output_dir / "coverage"
            html_dir.mkdir(parents=True, exist_ok=True)

            cov.html_report(directory=str(html_dir))

            # Get statistics
            stats = {}
            for filename in cov.get_data().measured_files():
                analysis = cov.analysis2(filename)
                if analysis:
                    stats[filename] = {
                        "statements": len(analysis[1]),
                        "missing": len(analysis[3]),
                        "coverage": (
                            100 * (1 - len(analysis[3]) / len(analysis[1])) if analysis[1] else 0
                        ),
                    }

            # Generate summary report
            total_statements = sum(s["statements"] for s in stats.values())
            total_missing = sum(s["missing"] for s in stats.values())
            overall_coverage = (
                100 * (1 - total_missing / total_statements) if total_statements else 0
            )

            report = {
                "overall_coverage": f"{overall_coverage:.1f}%",
                "total_statements": total_statements,
                "total_missing": total_missing,
                "module_breakdown": stats,
                "html_report": str(html_dir / "index.html"),
            }

            logger.info("coverage_report_generated", coverage=report["overall_coverage"])
            return report
        else:
            logger.warning("no_coverage_data", file=str(COVERAGE_FILE))
            return {"error": "No coverage data found. Run tests with coverage first."}

    def update_readme_sections(
        self, sections: List[str], readme_path: Optional[Path] = None
    ) -> None:
        """
        Update specific sections in README.md.

        Args:
            sections: List of section names to update (e.g., ["API", "Coverage"])
            readme_path: Optional path to README.md (defaults to project root)
        """
        if readme_path is None:
            readme_path = PROJECT_ROOT / "README.md"
        if not readme_path.exists():
            # Try parent directory (for test compatibility)
            parent_readme = self.source_dir.parent / "README.md"
            if parent_readme.exists():
                readme_path = parent_readme
            else:
                logger.error("readme_not_found", path=str(readme_path))
                return

        with open(readme_path, "r") as f:
            readme_content = f.read()

        for section in sections:
            logger.info("updating_readme_section", section=section)
            if section == "API":
                api_content = self._generate_api_section()
                readme_content = self._replace_section(
                    readme_content, "API Documentation", api_content
                )
            elif section == "Coverage":
                coverage_content = self._generate_coverage_section()
                readme_content = self._replace_section(
                    readme_content, "Test Coverage", coverage_content
                )

        with open(readme_path, "w") as f:
            f.write(readme_content)

        logger.info("readme_updated", sections=sections)

    def _replace_section(self, content: str, section_title: str, new_content: str) -> str:
        """Replace a section in markdown content."""
        import re

        # Find section boundaries
        pattern = rf"(## {section_title}.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            # Replace section content
            section_start = match.start()
            section_end = match.end()
            updated = (
                content[:section_start]
                + f"## {section_title}\n\n{new_content}\n"
                + content[section_end:]
            )
            return updated
        else:
            # Section doesn't exist, append it
            return content + f"\n## {section_title}\n\n{new_content}\n"

    def _generate_api_section(self) -> str:
        """Generate API section content for README."""
        lines = []

        # Count totals
        total_classes = sum(len(info["classes"]) for info in self.modules_data.values())
        total_functions = sum(len(info["functions"]) for info in self.modules_data.values())
        total_modules = len(self.modules_data)

        lines.append(
            f"The Data Extraction Tool provides {total_modules} modules with {total_classes} classes and {total_functions} functions."
        )
        lines.append("")
        lines.append("### Key Modules:")
        lines.append("")

        # Highlight important modules
        for module_path in sorted(self.modules_data.keys())[:5]:
            module_name = module_path.replace("/", ".").replace(".py", "")
            lines.append(f"- `{module_name}`")

        lines.append("")
        lines.append("See [API Documentation](docs/api/) for complete reference.")

        return "\n".join(lines)

    def _generate_coverage_section(self) -> str:
        """Generate coverage section content for README."""
        report = self.generate_coverage_report()

        if "error" in report:
            return f"Coverage data not available. {report['error']}"

        lines = [
            f"**Overall Coverage:** {report['overall_coverage']}",
            "",
            f"- Total Statements: {report['total_statements']:,}",
            f"- Missing Lines: {report['total_missing']:,}",
            "",
            "See [Coverage Report](docs/coverage/index.html) for detailed breakdown.",
        ]

        return "\n".join(lines)

    def generate_architecture_diagram(self, format: str = "mermaid") -> str:
        """
        Generate architecture diagram from code structure.

        Args:
            format: Output format (mermaid or graphviz)

        Returns:
            Diagram code as string
        """
        logger.info("generating_architecture_diagram", format=format)

        if format == "mermaid":
            return self._generate_mermaid_diagram()
        elif format == "graphviz":
            return self._generate_graphviz_diagram()
        else:
            logger.warning("unsupported_diagram_format", format=format)
            return ""

    def _generate_mermaid_diagram(self) -> str:
        """Generate Mermaid diagram of system architecture."""
        lines = ["```mermaid", "graph TB"]

        # Group modules by package
        packages: Dict[str, List[str]] = {}
        for module_path in self.modules_data.keys():
            parts = module_path.split("/")
            if len(parts) > 1:
                package = parts[0]
                if package not in packages:
                    packages[package] = []
                packages[package].append(parts[-1].replace(".py", ""))

        # Create subgraphs for packages
        for i, (package, modules) in enumerate(packages.items()):
            lines.append(f"    subgraph {package}[{package.title()} Package]")
            for module in modules[:5]:  # Limit to 5 modules per package
                node_id = f"{package}_{module}".replace("-", "_")
                lines.append(f"        {node_id}[{module}]")
            if len(modules) > 5:
                lines.append(f"        {package}_more[...+{len(modules)-5} more]")
            lines.append("    end")

        # Add some example relationships
        if len(packages) > 1:
            pkg_names = list(packages.keys())
            for i in range(len(pkg_names) - 1):
                lines.append(f"    {pkg_names[i]} --> {pkg_names[i+1]}")

        lines.append("```")

        # Save to file
        arch_dir = self.output_dir / "architecture"
        arch_dir.mkdir(parents=True, exist_ok=True)
        diagram_file = arch_dir / "system.mermaid"
        diagram_content = "\n".join(lines)
        diagram_file.write_text(diagram_content)

        logger.info("mermaid_diagram_generated", path=str(diagram_file))
        return diagram_content

    def _generate_graphviz_diagram(self) -> str:
        """Generate Graphviz DOT diagram (placeholder)."""
        logger.warning("graphviz_generation_not_implemented")
        return ""


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate documentation from Python source code",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--source-dir",
        type=Path,
        default=SRC_DIR,
        help="Source code directory",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for documentation",
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Configuration file (YAML or JSON)",
    )

    parser.add_argument(
        "--api",
        action="store_true",
        help="Generate API documentation",
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report",
    )

    parser.add_argument(
        "--update-readme",
        nargs="*",
        choices=["API", "Coverage"],
        help="Update README sections",
    )

    parser.add_argument(
        "--architecture",
        action="store_true",
        help="Generate architecture diagram",
    )

    parser.add_argument(
        "--format",
        choices=["markdown", "html", "mermaid", "graphviz"],
        default="markdown",
        help="Output format",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without writing files",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    try:
        args = parse_arguments()

        # Configure logging
        if args.verbose:
            import logging

            structlog.configure(
                wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
            )

        # Initialize generator
        generator = DocumentationGenerator(
            source_dir=args.source_dir,
            output_dir=args.output_dir,
            config_file=args.config,
        )

        # Execute requested operations
        if args.api:
            generator.generate_api_documentation(format=args.format)
            print(f"✅ API documentation generated in {args.output_dir}/api/")

        if args.coverage:
            report = generator.generate_coverage_report()
            if "error" not in report:
                print(f"✅ Coverage report: {report['overall_coverage']}")
                print(f"   HTML report: {report['html_report']}")

        if args.update_readme:
            sections = args.update_readme or ["API", "Coverage"]
            generator.update_readme_sections(sections)
            print(f"✅ README.md updated: {', '.join(sections)} sections")

        if args.architecture:
            diagram = generator.generate_architecture_diagram(format=args.format)
            if diagram:
                print(f"✅ Architecture diagram generated ({args.format})")

        return 0

    except Exception as e:
        logger.error("documentation_generation_failed", error=str(e))
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

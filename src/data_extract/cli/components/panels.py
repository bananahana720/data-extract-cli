"""Rich Panel components for CLI visual feedback.

This module provides:
- PreflightPanel: Pre-flight validation display before batch operations
- QualityDashboard: Quality metrics display after processing
- PreflightResult: Dataclass for preflight analysis results

AC-5.3-2: Quality dashboard (Rich Panel) shows metrics with visual bars
AC-5.3-3: Pre-flight validation panel before batch operations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from .feedback import get_console

# Size threshold for large file warning (5MB)
LARGE_FILE_THRESHOLD = 5 * 1024 * 1024

# Estimated seconds per file for various types
TIME_ESTIMATES = {
    ".pdf": 2.0,
    ".docx": 1.0,
    ".xlsx": 1.5,
    ".pptx": 1.5,
    ".txt": 0.2,
    ".csv": 0.3,
    "default": 1.0,
}


def _get_panel_box() -> Any:
    """Get box style for panels based on NO_COLOR environment variable.

    Returns ASCII box for NO_COLOR compliance, otherwise default rounded box.
    """
    import os

    from rich import box as rich_box

    if os.environ.get("NO_COLOR"):
        return rich_box.ASCII
    return rich_box.ROUNDED


@dataclass
class PreflightResult:
    """Results from pre-flight analysis of files to process.

    Attributes:
        file_count: Total number of files found
        type_distribution: Dict mapping extension to count
        total_size_bytes: Total size of all files in bytes
        issues: List of warning messages
        estimated_time_seconds: Estimated processing time
        warnings: Alias for issues (for compatibility)
    """

    file_count: int = 0
    type_distribution: dict[str, int] = field(default_factory=dict)
    total_size_bytes: int = 0
    issues: list[str] = field(default_factory=list)
    estimated_time_seconds: float = 0.0

    @property
    def warnings(self) -> list[str]:
        """Alias for issues (for test compatibility)."""
        return self.issues

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for dict-like access compatibility."""
        return hasattr(self, key)


class PreflightPanel:
    """Pre-flight validation panel for batch operations.

    Analyzes files before processing to provide:
    - File count and type breakdown
    - Estimated processing time
    - Warnings for problematic files (large, empty, etc.)
    - Output directory confirmation

    Usage:
        panel = PreflightPanel(output_dir=Path("output"))
        result = panel.analyze([Path("doc1.pdf"), Path("doc2.txt")])
        console.print(panel.render())
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        console: Optional[Console] = None,
    ) -> None:
        """Initialize PreflightPanel.

        Args:
            output_dir: Output directory path for display
            console: Rich Console for rendering
        """
        self._output_dir = output_dir
        self._console = console or get_console()
        self._result: Optional[PreflightResult] = None

    def analyze(self, files: Union[list[Path], list[str]]) -> PreflightResult:
        """Analyze files for pre-flight check.

        Args:
            files: List of file paths to analyze

        Returns:
            PreflightResult with analysis data
        """
        result = PreflightResult()

        # Handle empty list
        if not files:
            self._result = result
            return result

        # Convert to Path objects if needed
        paths = [Path(f) if isinstance(f, str) else f for f in files]

        result.file_count = len(paths)
        type_counts: dict[str, int] = {}
        total_size = 0
        estimated_time = 0.0
        issues: list[str] = []

        for path in paths:
            # Type distribution
            ext = path.suffix.lower() if path.suffix else ".unknown"
            type_counts[ext] = type_counts.get(ext, 0) + 1

            # Size analysis (if file exists)
            if path.exists():
                size = path.stat().st_size
                total_size += size

                # Check for large files
                if size > LARGE_FILE_THRESHOLD:
                    issues.append(f"Large file warning: {path.name} ({size / 1024 / 1024:.1f}MB)")

                # Check for empty files
                if size == 0:
                    issues.append(f"Empty file warning: {path.name}")

            # Estimate time
            time_per_file = TIME_ESTIMATES.get(ext, TIME_ESTIMATES["default"])
            estimated_time += time_per_file

        result.type_distribution = type_counts
        result.total_size_bytes = total_size
        result.issues = issues
        result.estimated_time_seconds = estimated_time

        self._result = result
        return result

    def render(self, result: Optional[PreflightResult] = None) -> Panel:
        """Render pre-flight panel.

        Args:
            result: PreflightResult to render. Uses stored result if None.

        Returns:
            Rich Panel object
        """
        result = result or self._result or PreflightResult()

        # Build content
        content_lines = []

        # File count
        content_lines.append(
            Text.assemble(
                ("Files: ", "bold"),
                (f"{result.file_count} documents", "cyan"),
            )
        )

        # Type breakdown
        if result.type_distribution:
            type_parts = []
            for ext, count in sorted(
                result.type_distribution.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                ext_name = ext.upper().lstrip(".")
                type_parts.append(f"{ext_name}: {count}")
            content_lines.append(
                Text.assemble(
                    ("Types: ", "bold"),
                    (", ".join(type_parts), "white"),
                )
            )

        # Size info
        if result.total_size_bytes > 0:
            size_mb = result.total_size_bytes / 1024 / 1024
            content_lines.append(
                Text.assemble(
                    ("Total size: ", "bold"),
                    (f"{size_mb:.1f}MB", "white"),
                )
            )

        # Estimated time
        if result.estimated_time_seconds > 0:
            if result.estimated_time_seconds >= 60:
                minutes = result.estimated_time_seconds / 60
                time_str = f"~{minutes:.1f} minutes"
            else:
                time_str = f"~{result.estimated_time_seconds:.0f} seconds"
            content_lines.append(
                Text.assemble(
                    ("Estimated time: ", "bold"),
                    (time_str, "green"),
                )
            )

        # Output directory
        if self._output_dir:
            content_lines.append(
                Text.assemble(
                    ("Output: ", "bold"),
                    (str(self._output_dir), "cyan"),
                )
            )

        # Warnings/issues
        if result.issues:
            content_lines.append(Text(""))  # Blank line
            content_lines.append(Text("Warnings:", style="bold yellow"))
            for issue in result.issues:
                content_lines.append(Text(f"  - {issue}", style="yellow"))

        # Action buttons hint
        content_lines.append(Text(""))
        content_lines.append(
            Text.assemble(
                ("[Continue] ", "bold green"),
                ("Press Enter to proceed | ", "dim"),
                ("[Cancel] ", "bold red"),
                ("Ctrl+C to abort", "dim"),
            )
        )

        # Create panel
        content = Group(*content_lines)
        return Panel(
            content,
            title="Pre-flight Check",
            border_style="blue",
            padding=(1, 2),
            box=_get_panel_box(),
        )


@dataclass
class QualityMetrics:
    """Quality metrics for dashboard display."""

    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    excellent_count: int = 0  # >90 quality score
    good_count: int = 0  # 70-90 quality score
    needs_review_count: int = 0  # <70 quality score
    suggestions: list[str] = field(default_factory=list)
    learning_tip: str = ""


class QualityDashboard:
    """Quality metrics dashboard displayed after processing.

    Shows:
    - Files processed successfully vs failed
    - Quality distribution with visual bars
    - Actionable suggestions
    - Learning tips

    Usage:
        dashboard = QualityDashboard(metrics=metrics_dict)
        console.print(dashboard.render())
    """

    def __init__(
        self,
        metrics: Optional[Union[dict[str, Any], QualityMetrics, Any]] = None,
        console: Optional[Console] = None,
    ) -> None:
        """Initialize QualityDashboard.

        Args:
            metrics: Quality metrics (dict or QualityMetrics or dataclass)
            console: Rich Console for rendering
        """
        self._console = console or get_console()
        self._metrics = self._parse_metrics(metrics)

    def _parse_metrics(
        self, metrics: Optional[Union[dict[str, Any], QualityMetrics, Any]]
    ) -> QualityMetrics:
        """Parse metrics into QualityMetrics object.

        Args:
            metrics: Input metrics in various formats

        Returns:
            QualityMetrics object
        """
        if metrics is None:
            return QualityMetrics()

        if isinstance(metrics, QualityMetrics):
            return metrics

        if isinstance(metrics, dict):
            return QualityMetrics(
                total_files=metrics.get("total_files", 0),
                successful_files=metrics.get("successful_files", 0),
                failed_files=metrics.get("failed_files", 0),
                excellent_count=metrics.get("excellent_count", 0),
                good_count=metrics.get("good_count", 0),
                needs_review_count=metrics.get("needs_review_count", 0),
                suggestions=metrics.get("suggestions", []),
                learning_tip=metrics.get(
                    "learning_tip",
                    "Quality scores are based on text density, structure, and coherence.",
                ),
            )

        # Handle dataclass-like objects with attributes
        return QualityMetrics(
            total_files=getattr(metrics, "total_files", 0),
            successful_files=getattr(metrics, "successful_files", 0),
            failed_files=getattr(metrics, "failed_files", 0),
            excellent_count=getattr(metrics, "excellent_count", 0),
            good_count=getattr(metrics, "good_count", 0),
            needs_review_count=getattr(metrics, "needs_review_count", 0),
            suggestions=getattr(metrics, "suggestions", []),
            learning_tip=getattr(
                metrics,
                "learning_tip",
                "Quality scores are based on text density, structure, and coherence.",
            ),
        )

    def render(self, metrics: Optional[dict[str, Any]] = None) -> Panel:
        """Render quality dashboard panel.

        Args:
            metrics: Optional metrics dict (uses stored metrics if None)

        Returns:
            Rich Panel object
        """
        if metrics:
            self._metrics = self._parse_metrics(metrics)

        m = self._metrics
        content_lines = []

        # Success summary
        if m.total_files > 0:
            success_text = f"{m.successful_files}/{m.total_files} files processed successfully"
            if m.failed_files > 0:
                success_text += f" ({m.failed_files} failed)"
            content_lines.append(
                Text(success_text, style="bold green" if m.failed_files == 0 else "bold yellow")
            )
        else:
            content_lines.append(Text("No files processed", style="dim"))

        content_lines.append(Text(""))

        # Quality distribution with bars
        if m.total_files > 0:
            content_lines.append(Text("Quality Distribution:", style="bold"))

            total = m.excellent_count + m.good_count + m.needs_review_count
            if total > 0:
                # Excellent (>90)
                excellent_pct = (m.excellent_count / total) * 100 if total > 0 else 0
                content_lines.append(
                    Text.assemble(
                        ("  Excellent (>90):    ", "green"),
                        (f"{m.excellent_count:3d} ", "bold green"),
                        self._make_bar(excellent_pct),
                    )
                )

                # Good (70-90)
                good_pct = (m.good_count / total) * 100 if total > 0 else 0
                content_lines.append(
                    Text.assemble(
                        ("  Good (70-90):       ", "yellow"),
                        (f"{m.good_count:3d} ", "bold yellow"),
                        self._make_bar(good_pct),
                    )
                )

                # Needs Review (<70)
                review_pct = (m.needs_review_count / total) * 100 if total > 0 else 0
                content_lines.append(
                    Text.assemble(
                        ("  Needs Review (<70): ", "red"),
                        (f"{m.needs_review_count:3d} ", "bold red"),
                        self._make_bar(review_pct),
                    )
                )

        content_lines.append(Text(""))

        # Suggestions
        if m.suggestions:
            content_lines.append(Text("Suggestions:", style="bold cyan"))
            for suggestion in m.suggestions:
                # Highlight dedupe command if present
                if "dedupe" in suggestion.lower():
                    content_lines.append(Text(f"  - {suggestion}", style="cyan"))
                else:
                    content_lines.append(Text(f"  - {suggestion}"))

        # Learning tip
        if m.learning_tip:
            content_lines.append(Text(""))
            content_lines.append(
                Text.assemble(
                    ("Learn more: ", "bold magenta"),
                    (m.learning_tip, "dim"),
                )
            )

        # Create panel
        content = Group(*content_lines)
        return Panel(
            content,
            title="Quality Insights",
            border_style="green",
            padding=(1, 2),
            box=_get_panel_box(),
        )

    def _make_bar(self, percentage: float, width: int = 20) -> Text:
        """Create a simple text-based progress bar.

        Args:
            percentage: Percentage to display (0-100)
            width: Width of the bar in characters

        Returns:
            Text object with bar representation
        """
        filled = int((percentage / 100) * width)
        bar = "=" * filled + "-" * (width - filled)
        return Text(f"[{bar}] {percentage:5.1f}%", style="dim")


__all__ = [
    "PreflightResult",
    "PreflightPanel",
    "QualityMetrics",
    "QualityDashboard",
]

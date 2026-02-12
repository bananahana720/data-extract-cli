"""Summary statistics and reporting module for CLI (Story 5-4).

This module provides:
- SummaryReport: Frozen dataclass for comprehensive summary statistics
- QualityMetrics: Frozen dataclass for quality distribution tracking
- StageTimer: Track elapsed time for pipeline stages
- StageName: Enum for pipeline stage identification
- ExportFormat: Enum for export format options
- Render functions: Rich Panel/Table rendering for visual feedback
- Export functions: Multiple format exports (TXT, JSON, HTML)

AC-5.4-1: SummaryReport dataclass with quality, timing, errors, suggestions
AC-5.4-2: Quality distribution breakdown (excellent/good/review/flagged)
AC-5.4-3: Per-stage timing breakdown with visual formatting
AC-5.4-4: Export summary in multiple formats (TXT, JSON, HTML)
"""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from html import escape
from pathlib import Path
from typing import Any, Iterator, Sequence

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class StageName(str, Enum):
    """Pipeline stage names for timing tracking."""

    EXTRACT = "extract"
    NORMALIZE = "normalize"
    CHUNK = "chunk"
    SEMANTIC = "semantic"
    OUTPUT = "output"


class ExportFormat(str, Enum):
    """Export format options for summary reports."""

    TXT = "txt"
    JSON = "json"
    HTML = "html"


@dataclass(frozen=True)
class QualityMetrics:
    """Quality metrics for processed chunks.

    Attributes:
        avg_quality: Average quality score (0.0 to 1.0)
        excellent_count: Number of chunks with quality >= 0.9
        good_count: Number of chunks with quality >= 0.7
        review_count: Number of chunks with quality < 0.7
        flagged_count: Number of chunks flagged for manual review
        entity_count: Total number of entities identified
        readability_score: Flesch readability score
        duplicate_percentage: Percentage of duplicate chunks detected
    """

    avg_quality: float
    excellent_count: int
    good_count: int
    review_count: int
    flagged_count: int
    entity_count: int
    readability_score: float
    duplicate_percentage: float = 0.0

    @property
    def total_count(self) -> int:
        """Total number of chunks across all quality levels."""
        return self.excellent_count + self.good_count + self.review_count

    def get_distribution(self) -> dict[str, float]:
        """Return quality distribution as percentages.

        Returns:
            Dict mapping quality level to percentage
        """
        total = self.total_count
        if total == 0:
            return {"excellent": 0.0, "good": 0.0, "review": 0.0}

        return {
            "excellent": (self.excellent_count / total) * 100,
            "good": (self.good_count / total) * 100,
            "review": (self.review_count / total) * 100,
        }


@dataclass(frozen=True)
class SummaryReport:
    """Comprehensive summary report for pipeline execution.

    Attributes:
        files_processed: Number of files successfully processed
        files_failed: Number of files that failed processing
        chunks_created: Total number of chunks created
        errors: Tuple of error messages
        quality_metrics: Optional quality metrics for chunks
        timing: Dict mapping stage name to duration in milliseconds
        config: Dict of configuration settings used
        next_steps: Tuple of suggested next actions
        processing_duration_ms: Total processing duration in milliseconds
    """

    files_processed: int
    files_failed: int
    chunks_created: int
    errors: tuple[str, ...]
    quality_metrics: QualityMetrics | None
    timing: dict[str, float]
    config: dict[str, Any]
    next_steps: tuple[str, ...]
    processing_duration_ms: float = 0.0


class StageTimer:
    """Track elapsed time for pipeline stages.

    Usage:
        timer = StageTimer(StageName.EXTRACT)
        timer.start()
        # ... do work ...
        elapsed_ms = timer.stop()
        print(timer.format_duration())
    """

    def __init__(self, stage: StageName | str) -> None:
        """Initialize StageTimer for a specific stage.

        Args:
            stage: Pipeline stage being timed
        """
        self._stage = stage
        self._start_time: float | None = None
        self._elapsed_ms: float | None = None

    @property
    def stage(self) -> StageName | str:
        """Pipeline stage being timed."""
        return self._stage

    def start(self) -> None:
        """Start timing the stage."""
        self._start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop timing and return elapsed milliseconds.

        Returns:
            Elapsed time in milliseconds, or 0 if not started
        """
        if self._start_time is None:
            self._elapsed_ms = 0.0
            return 0.0

        elapsed = time.perf_counter() - self._start_time
        self._elapsed_ms = elapsed * 1000  # Convert to milliseconds
        return self._elapsed_ms

    def elapsed(self) -> float:
        """Get elapsed time in milliseconds.

        Returns:
            Elapsed time, or 0 if not stopped
        """
        return self._elapsed_ms or 0.0

    def format_duration(self) -> str:
        """Format elapsed time as human-readable string.

        Returns:
            Formatted duration like "1.5s" or "150ms"
        """
        if self._elapsed_ms is None:
            return "0ms"

        if self._elapsed_ms >= 1000:
            return f"{self._elapsed_ms / 1000:.2f}s"
        return f"{self._elapsed_ms:.0f}ms"


# ============================================================================
# RENDER FUNCTIONS - Rich Panel/Table visualization
# ============================================================================


def _get_panel_box() -> Any:
    """Get box style for panels based on NO_COLOR environment variable.

    Returns ASCII box for NO_COLOR compliance, otherwise default rounded box.
    """
    from rich import box as rich_box

    if os.environ.get("NO_COLOR"):
        return rich_box.ASCII
    return rich_box.ROUNDED


def render_summary_panel(report: SummaryReport) -> Panel:
    """Render summary report as Rich Panel.

    Args:
        report: SummaryReport to render

    Returns:
        Rich Panel with summary content
    """
    content_lines = []

    # Files processed
    success_rate = (
        (report.files_processed / (report.files_processed + report.files_failed)) * 100
        if (report.files_processed + report.files_failed) > 0
        else 0
    )
    content_lines.append(
        Text.assemble(
            ("Files: ", "bold"),
            (f"{report.files_processed} processed", "green"),
            (f", {report.files_failed} failed", "red" if report.files_failed > 0 else "dim"),
            (f" ({success_rate:.0f}%)", "dim"),
        )
    )

    # Chunks created
    content_lines.append(
        Text.assemble(
            ("Chunks: ", "bold"),
            (f"{report.chunks_created}", "cyan"),
        )
    )

    # Total timing
    total_time_ms = sum(report.timing.values())
    if total_time_ms >= 1000:
        time_str = f"{total_time_ms / 1000:.2f}s"
    else:
        time_str = f"{total_time_ms:.0f}ms"
    content_lines.append(
        Text.assemble(
            ("Processing time: ", "bold"),
            (time_str, "green"),
        )
    )

    # Quality metrics if available
    if report.quality_metrics:
        content_lines.append(Text(""))  # Blank line
        content_lines.append(
            Text.assemble(
                ("Avg quality: ", "bold"),
                (f"{report.quality_metrics.avg_quality:.2f}", "cyan"),
            )
        )

    # Errors section
    if report.errors:
        content_lines.append(Text(""))
        content_lines.append(Text("Errors:", style="bold red"))
        for error in report.errors[:5]:  # Limit to 5 errors
            content_lines.append(Text(f"  - {error}", style="red"))
        if len(report.errors) > 5:
            content_lines.append(Text(f"  ... and {len(report.errors) - 5} more", style="dim"))

    # Next steps
    if report.next_steps:
        content_lines.append(Text(""))
        content_lines.append(Text("Next Steps:", style="bold magenta"))
        for step in report.next_steps:
            content_lines.append(Text(f"  • {step}", style="cyan"))

    # Determine border style based on success
    border_style = "green" if report.files_failed == 0 else "yellow"

    content = Group(*content_lines)
    return Panel(
        content,
        title="Processing Summary",
        border_style=border_style,
        padding=(1, 2),
        box=_get_panel_box(),
    )


def render_quality_dashboard(metrics: QualityMetrics) -> Table:
    """Render quality metrics as Rich Table with distribution bars.

    Args:
        metrics: QualityMetrics to visualize

    Returns:
        Rich Table with quality distribution
    """
    table = Table(
        title="Quality Distribution",
        show_header=True,
        header_style="bold cyan",
        box=_get_panel_box(),
    )

    table.add_column("Level", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Distribution", width=40)

    distribution = metrics.get_distribution()

    # Excellent (>= 0.9)
    excellent_pct = distribution["excellent"]
    table.add_row(
        Text("Excellent (≥90)", style="green"),
        str(metrics.excellent_count),
        _make_progress_bar(excellent_pct, "green"),
    )

    # Good (0.7 - 0.9)
    good_pct = distribution["good"]
    table.add_row(
        Text("Good (70-90)", style="yellow"),
        str(metrics.good_count),
        _make_progress_bar(good_pct, "yellow"),
    )

    # Review (< 0.7)
    review_pct = distribution["review"]
    table.add_row(
        Text("Review (<70)", style="red"),
        str(metrics.review_count),
        _make_progress_bar(review_pct, "red"),
    )

    # Add summary row
    table.add_section()
    table.add_row(
        Text("Total", style="bold"),
        str(metrics.total_count),
        Text(f"Avg: {metrics.avg_quality:.2f}", style="dim"),
    )

    return table


def render_timing_breakdown(timing: dict[str, float]) -> Table:
    """Render per-stage timing breakdown as Rich Table.

    Args:
        timing: Dict mapping stage name to duration in milliseconds

    Returns:
        Rich Table with timing breakdown
    """
    table = Table(
        title="Timing Breakdown",
        show_header=True,
        header_style="bold cyan",
        box=_get_panel_box(),
    )

    table.add_column("Stage", style="bold")
    table.add_column("Duration", justify="right")
    table.add_column("Percentage", justify="right")

    total_ms = sum(timing.values())

    for stage_name in ["extract", "normalize", "chunk", "semantic", "output"]:
        duration_ms = timing.get(stage_name, 0.0)

        # Format duration
        if duration_ms >= 1000:
            duration_str = f"{duration_ms / 1000:.2f}s"
        else:
            duration_str = f"{duration_ms:.0f}ms"

        # Calculate percentage
        percentage = (duration_ms / total_ms * 100) if total_ms > 0 else 0

        # Style based on percentage (highlight slow stages)
        style = "red" if percentage > 40 else "green" if percentage < 20 else "yellow"

        table.add_row(
            stage_name.capitalize(),
            duration_str,
            Text(f"{percentage:.1f}%", style=style),
        )

    # Total row
    table.add_section()
    total_str = f"{total_ms / 1000:.2f}s" if total_ms >= 1000 else f"{total_ms:.0f}ms"
    table.add_row(
        Text("Total", style="bold"),
        Text(total_str, style="bold green"),
        "100.0%",
    )

    return table


def render_next_steps(steps: Sequence[str]) -> Panel:
    """Render next steps recommendations as Rich Panel.

    Args:
        steps: Sequence of suggested next actions

    Returns:
        Rich Panel with bulleted recommendations
    """
    if not steps:
        return Panel(
            Text("No additional steps required.", style="dim"),
            title="Next Steps",
            border_style="green",
            box=_get_panel_box(),
        )

    content_lines = []
    for step in steps:
        content_lines.append(Text(f"• {step}", style="cyan"))

    content = Group(*content_lines)
    return Panel(
        content,
        title="Next Steps",
        border_style="magenta",
        padding=(1, 2),
        box=_get_panel_box(),
    )


def _make_progress_bar(percentage: float, color: str = "green", width: int = 30) -> Text:
    """Create a text-based progress bar.

    Args:
        percentage: Percentage to display (0-100)
        color: Color style for the bar
        width: Width of the bar in characters

    Returns:
        Text object with bar representation
    """
    filled = int((percentage / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    return Text(f"{bar} {percentage:5.1f}%", style=color)


# ============================================================================
# EXPORT FUNCTIONS - Multi-format export support
# ============================================================================


def _iter_summary_section_data(report: SummaryReport) -> Iterator[tuple[str, list[str]]]:
    """Yield summary sections as line collections for reuse across exporters."""
    yield (
        "header",
        [
            "=" * 60,
            "PROCESSING SUMMARY REPORT",
            "=" * 60,
            f"Files Processed: {report.files_processed}",
            f"Files Failed: {report.files_failed}",
            f"Chunks Created: {report.chunks_created}",
        ],
    )

    if report.quality_metrics:
        metrics = report.quality_metrics
        yield (
            "quality",
            [
                "QUALITY METRICS",
                "-" * 60,
                f"Average Quality: {metrics.avg_quality:.2f}",
                f"Excellent (>=90): {metrics.excellent_count}",
                f"Good (70-90): {metrics.good_count}",
                f"Review (<70): {metrics.review_count}",
                f"Flagged: {metrics.flagged_count}",
                f"Entities: {metrics.entity_count}",
                f"Readability: {metrics.readability_score:.1f}",
            ],
        )

    if report.timing:
        timing_lines = [
            "TIMING BREAKDOWN",
            "-" * 60,
        ]
        total_ms = sum(report.timing.values())
        for stage, duration_ms in report.timing.items():
            percentage = (duration_ms / total_ms * 100) if total_ms > 0 else 0
            duration_str = (
                f"{duration_ms / 1000:.2f}s" if duration_ms >= 1000 else f"{duration_ms:.0f}ms"
            )
            timing_lines.append(f"{stage.capitalize():12s}: {duration_str:>10s} ({percentage:5.1f}%)")
        yield ("timing", timing_lines)

    if report.errors:
        yield (
            "errors",
            [
                "ERRORS",
                "-" * 60,
                *(f"  - {error}" for error in report.errors),
            ],
        )

    if report.next_steps:
        yield (
            "next_steps",
            [
                "NEXT STEPS",
                "-" * 60,
                *(f"  • {step}" for step in report.next_steps),
            ],
        )


def iter_summary_sections(report: SummaryReport) -> Iterator[str]:
    """Yield progressively renderable text blocks for each summary section."""
    for _, lines in _iter_summary_section_data(report):
        yield "\n".join(lines)


def export_summary(
    report: SummaryReport,
    output_path: Path,
    format: ExportFormat,
) -> Path:
    """Export summary report to file in specified format.

    Args:
        report: SummaryReport to export
        output_path: Output file path
        format: Export format (TXT, JSON, HTML)

    Returns:
        Path to created file
    """
    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == ExportFormat.TXT:
        _export_txt(report, output_path)
    elif format == ExportFormat.JSON:
        _export_json(report, output_path)
    elif format == ExportFormat.HTML:
        _export_html(report, output_path)

    return output_path


def export_summary_parallel(
    report: SummaryReport,
    output_dir: Path,
    formats: Sequence[ExportFormat],
    max_workers: int = 3,
) -> dict[ExportFormat, Path]:
    """Export one report to multiple formats concurrently."""
    normalized_formats: list[ExportFormat] = []
    for format_item in formats:
        if format_item not in normalized_formats:
            normalized_formats.append(format_item)

    if not normalized_formats:
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    worker_count = min(max(1, max_workers), len(normalized_formats))
    futures = {}

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        for format_item in normalized_formats:
            output_path = output_dir / f"summary.{format_item.value}"
            futures[format_item] = executor.submit(export_summary, report, output_path, format_item)

        return {format_item: future.result() for format_item, future in futures.items()}


def _export_txt(report: SummaryReport, output_path: Path) -> None:
    """Export summary as plain text.

    Args:
        report: SummaryReport to export
        output_path: Output file path
    """
    output_path.write_text("\n\n".join(iter_summary_sections(report)))


def _export_json(report: SummaryReport, output_path: Path) -> None:
    """Export summary as JSON.

    Args:
        report: SummaryReport to export
        output_path: Output file path
    """
    data: dict[str, Any] = {
        "files_processed": report.files_processed,
        "files_failed": report.files_failed,
        "chunks_created": report.chunks_created,
        "processing_duration_ms": report.processing_duration_ms,
        "errors": list(report.errors),
        "timing": report.timing,
        "config": report.config,
        "next_steps": list(report.next_steps),
    }

    if report.quality_metrics:
        m = report.quality_metrics
        data["quality_metrics"] = {
            "avg_quality": m.avg_quality,
            "excellent_count": m.excellent_count,
            "good_count": m.good_count,
            "review_count": m.review_count,
            "flagged_count": m.flagged_count,
            "entity_count": m.entity_count,
            "readability_score": m.readability_score,
            "duplicate_percentage": m.duplicate_percentage,
            "distribution": m.get_distribution(),
        }

    output_path.write_text(json.dumps(data, indent=2))


def _export_html(report: SummaryReport, output_path: Path) -> None:
    """Export summary as HTML with styling.

    Args:
        report: SummaryReport to export
        output_path: Output file path
    """
    from datetime import datetime

    section_data = {section: lines for section, lines in _iter_summary_section_data(report)}

    # Build quality section
    quality_html = ""
    if report.quality_metrics:
        m = report.quality_metrics
        dist = m.get_distribution()
        quality_html = f"""
        <div class="section">
            <h2>Quality Metrics</h2>
            <div class="grid">
                <div class="card">
                    <h3>Average Quality</h3>
                    <div class="stat">{m.avg_quality:.2f}</div>
                </div>
                <div class="card">
                    <h3>Excellent</h3>
                    <div class="stat">{m.excellent_count}</div>
                    <div class="stat-label">{dist['excellent']:.1f}%</div>
                </div>
                <div class="card">
                    <h3>Good</h3>
                    <div class="stat">{m.good_count}</div>
                    <div class="stat-label">{dist['good']:.1f}%</div>
                </div>
                <div class="card">
                    <h3>Review</h3>
                    <div class="stat">{m.review_count}</div>
                    <div class="stat-label">{dist['review']:.1f}%</div>
                </div>
            </div>
            <p style="margin-top: 1rem;">
                <strong>Flagged:</strong> {m.flagged_count} |
                <strong>Entities:</strong> {m.entity_count} |
                <strong>Readability:</strong> {m.readability_score:.1f}
            </p>
        </div>
        """

    # Build timing section
    timing_row_items: list[str] = []
    total_ms = sum(report.timing.values())
    for stage, duration_ms in report.timing.items():
        percentage = (duration_ms / total_ms * 100) if total_ms > 0 else 0
        duration_str = (
            f"{duration_ms / 1000:.2f}s" if duration_ms >= 1000 else f"{duration_ms:.0f}ms"
        )
        timing_row_items.append(
            f"""
        <tr>
            <td>{stage.capitalize()}</td>
            <td>{duration_str}</td>
            <td>{percentage:.1f}%</td>
        </tr>
        """
        )
    timing_rows = "".join(timing_row_items)

    # Build errors section
    errors_html = ""
    errors_section = section_data.get("errors")
    if errors_section:
        error_items = "\n".join(
            f"<li>{escape(line.removeprefix('  - '))}</li>"
            for line in errors_section
            if line.startswith("  - ")
        )
        errors_html = f"""
        <div class="section">
            <h2>Errors ({len(report.errors)})</h2>
            <ul class="error-list">
                {error_items}
            </ul>
        </div>
        """

    # Build next steps section
    next_steps_html = ""
    next_steps_section = section_data.get("next_steps")
    if next_steps_section:
        step_items = "\n".join(
            f"<li>{escape(line.removeprefix('  • '))}</li>"
            for line in next_steps_section
            if line.startswith("  • ")
        )
        next_steps_html = f"""
        <div class="section">
            <h2>Next Steps</h2>
            <ul class="steps-list">
                {step_items}
            </ul>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Processing Summary Report</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #16a34a;
            --warning: #ca8a04;
            --error: #dc2626;
            --background: #f8fafc;
            --surface: #ffffff;
            --text: #1e293b;
            --muted: #64748b;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--background);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            background: var(--surface);
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        h1 {{ color: var(--primary); margin-bottom: 0.5rem; }}
        .meta {{ color: var(--muted); font-size: 0.875rem; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: var(--surface);
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            color: var(--primary);
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
            text-transform: uppercase;
        }}
        .stat {{ font-size: 2rem; font-weight: 700; color: var(--text); }}
        .stat-label {{ color: var(--muted); font-size: 0.875rem; }}
        .section {{
            background: var(--surface);
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        .section h2 {{
            color: var(--text);
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--primary);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: var(--background);
            font-weight: 600;
        }}
        .error-list, .steps-list {{
            list-style-position: inside;
            padding-left: 1rem;
        }}
        .error-list li {{ color: var(--error); margin-bottom: 0.5rem; }}
        .steps-list li {{ color: var(--primary); margin-bottom: 0.5rem; }}
        footer {{
            text-align: center;
            color: var(--muted);
            padding: 2rem;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Processing Summary Report</h1>
            <p class="meta">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <div class="grid">
            <div class="card">
                <h3>Files Processed</h3>
                <div class="stat">{report.files_processed}</div>
            </div>
            <div class="card">
                <h3>Files Failed</h3>
                <div class="stat">{report.files_failed}</div>
            </div>
            <div class="card">
                <h3>Chunks Created</h3>
                <div class="stat">{report.chunks_created}</div>
            </div>
            <div class="card">
                <h3>Processing Time</h3>
                <div class="stat">{sum(report.timing.values()) / 1000:.2f}</div>
                <div class="stat-label">seconds</div>
            </div>
        </div>

        {quality_html}

        <div class="section">
            <h2>Timing Breakdown</h2>
            <table>
                <thead>
                    <tr>
                        <th>Stage</th>
                        <th>Duration</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    {timing_rows}
                </tbody>
            </table>
        </div>

        {errors_html}

        {next_steps_html}

        <footer>
            <p>Data Extraction Tool - Processing Summary</p>
        </footer>
    </div>
</body>
</html>
"""

    output_path.write_text(html)


__all__ = [
    "StageName",
    "ExportFormat",
    "QualityMetrics",
    "SummaryReport",
    "StageTimer",
    "render_summary_panel",
    "render_quality_dashboard",
    "render_timing_breakdown",
    "render_next_steps",
    "iter_summary_sections",
    "export_summary",
    "export_summary_parallel",
]

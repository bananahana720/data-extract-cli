"""Console display for security findings using Rich."""

from pathlib import Path
from typing import List, Optional

from rich import box  # type: ignore[import-not-found]
from rich.console import Console  # type: ignore[import-not-found]
from rich.panel import Panel  # type: ignore[import-not-found]
from rich.table import Table  # type: ignore[import-not-found]
from rich.text import Text  # type: ignore[import-not-found]

from ..config import SEVERITY_LEVELS
from ..models import ScanStatistics, SecurityFinding
from .base import AbstractReporter


class ConsoleReporter(AbstractReporter):
    """Display security findings in the console."""

    def __init__(self):
        """Initialize console reporter."""
        self.console = Console()

    def generate(
        self,
        findings: List[SecurityFinding],
        stats: ScanStatistics,
        output_file: Optional[Path] = None,
    ) -> str:
        """Display findings in the console.

        Args:
            findings: List of security findings
            stats: Scan statistics
            output_file: Not used for console output

        Returns:
            Empty string (console output only)
        """
        if not findings:
            self.console.print("[green]✓ No security issues found![/green]")
            return ""

        self._display_summary(stats)
        self._display_findings_table(findings)

        return ""

    def _display_summary(self, stats: ScanStatistics) -> None:
        """Display summary panel."""
        summary = f"""[bold]Security Scan Results[/bold]

Total Findings: [bold red]{stats.total_findings}[/bold red]
Files Scanned: {stats.files_scanned}

Breakdown by Type:
  • Secrets: {stats.secrets_found}
  • Vulnerabilities: {stats.vulnerabilities_found}
  • Permissions: {stats.permission_issues}
  • SAST: {stats.sast_findings}"""

        self.console.print(Panel(summary, title="🔒 Security Summary", border_style="red"))

    def _display_findings_table(self, findings: List[SecurityFinding]) -> None:
        """Display findings in a table."""
        table = Table(title="Security Findings", box=box.ROUNDED)
        table.add_column("Severity", style="bold")
        table.add_column("Type")
        table.add_column("Description")
        table.add_column("Location")

        # Show top findings only
        for finding in findings[:20]:
            severity_style = SEVERITY_LEVELS.get(finding.severity, "white")
            location = finding.file_path or "N/A"
            if finding.line_number:
                location += f":{finding.line_number}"

            description = finding.description
            if len(description) > 60:
                description = description[:60] + "..."

            table.add_row(
                Text(finding.severity, style=severity_style),
                finding.finding_type,
                description,
                location,
            )

        self.console.print("\n")
        self.console.print(table)

        if len(findings) > 20:
            self.console.print(f"\n[dim]... and {len(findings) - 20} more findings[/dim]")

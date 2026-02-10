"""Security scanner orchestration."""

from pathlib import Path
from typing import List

import structlog  # type: ignore[import-not-found]
from rich.console import Console  # type: ignore[import-not-found]

from .config import PROJECT_ROOT
from .models import ScanStatistics, SecurityFinding
from .reporters import ConsoleReporter, JSONReporter, MarkdownReporter
from .scanners.dependencies import DependencyScanner
from .scanners.history import GitHistoryScanner
from .scanners.permissions import PermissionsScanner
from .scanners.sast import SASTScanner
from .scanners.secrets import SecretsScanner
from .utils import CacheManager

logger = structlog.get_logger()


class SecurityOrchestrator:
    """Orchestrates all security scanning operations."""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        """Initialize the security orchestrator."""
        self.project_root = project_root
        self.console = Console()
        self.cache_manager = CacheManager()
        self.findings: List[SecurityFinding] = []
        self.stats = ScanStatistics()

        # Initialize scanners
        self.secrets_scanner = SecretsScanner(project_root, self.cache_manager)
        self.dependency_scanner = DependencyScanner(project_root)
        self.permissions_scanner = PermissionsScanner(project_root)
        self.sast_scanner = SASTScanner(project_root)
        self.history_scanner = GitHistoryScanner(project_root)

        # Initialize reporters
        self.console_reporter = ConsoleReporter()
        self.markdown_reporter = MarkdownReporter()
        self.json_reporter = JSONReporter()

        logger.info("initialized_security_orchestrator", project_root=str(project_root))

    def scan_secrets(self, use_gitleaks: bool = True) -> List[SecurityFinding]:
        """Run secrets scanning."""
        findings = self.secrets_scanner.scan(use_gitleaks=use_gitleaks)
        self.findings.extend(findings)
        self.stats.secrets_found = len(findings)
        self.stats.files_scanned = (
            self.secrets_scanner.stats.files_scanned
            if hasattr(self.secrets_scanner, "stats")
            else 0
        )
        return findings

    def scan_dependencies(self) -> List[SecurityFinding]:
        """Run dependency vulnerability scanning."""
        findings = self.dependency_scanner.scan()
        self.findings.extend(findings)
        self.stats.vulnerabilities_found = len(findings)
        return findings

    def scan_permissions(self) -> List[SecurityFinding]:
        """Run file permissions validation."""
        findings = self.permissions_scanner.scan()
        self.findings.extend(findings)
        self.stats.permission_issues = len(findings)
        return findings

    def scan_sast(self) -> List[SecurityFinding]:
        """Run SAST analysis."""
        findings = self.sast_scanner.scan()
        self.findings.extend(findings)
        self.stats.sast_findings = len(findings)
        return findings

    def scan_history(self, max_commits: int = 100) -> List[SecurityFinding]:
        """Scan git history for secrets."""
        findings = self.history_scanner.scan(max_commits=max_commits)
        self.findings.extend(findings)
        self.stats.secrets_found += len(findings)
        return findings

    def run_all_scans(self, use_gitleaks: bool = True) -> List[SecurityFinding]:
        """Run all security scans."""
        with self.console.status("[bold green]Running security scans...") as status:
            status.update("Scanning for secrets...")
            self.scan_secrets(use_gitleaks=use_gitleaks)

            status.update("Checking dependencies...")
            self.scan_dependencies()

            status.update("Validating permissions...")
            self.scan_permissions()

            status.update("Running SAST analysis...")
            self.scan_sast()

        self.stats.total_findings = len(self.findings)
        return self.findings

    def display_findings(self) -> None:
        """Display findings in the console."""
        self.console_reporter.generate(self.findings, self.stats)

    def generate_report(self, format: str = "markdown", output_file: Path = None) -> str:
        """Generate security report in specified format."""
        if format == "json":
            return self.json_reporter.generate(self.findings, self.stats, output_file)
        elif format == "text":
            # For text format, return a simplified version
            return self._generate_text_report()
        else:  # markdown
            return self.markdown_reporter.generate(self.findings, self.stats, output_file)

    def _generate_text_report(self) -> str:
        """Generate plain text report."""
        from datetime import datetime

        lines = []
        lines.append("SECURITY SCAN REPORT")
        lines.append("=" * 50)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total Findings: {self.stats.total_findings}")
        lines.append("")

        # Group by severity
        from .config import SEVERITY_LEVELS

        for severity in SEVERITY_LEVELS.keys():
            severity_findings = [f for f in self.findings if f.severity == severity]
            if severity_findings:
                lines.append(f"{severity}: {len(severity_findings)} findings")
                for finding in severity_findings[:5]:
                    lines.append(f"  - {finding.description}")
                    if finding.file_path:
                        lines.append(f"    File: {finding.file_path}")
                lines.append("")

        return "\n".join(lines)

    def save_false_positives(self) -> None:
        """Save false positive cache."""
        self.cache_manager.save_false_positives()

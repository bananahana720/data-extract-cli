"""Markdown report generation for security findings."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..config import SEVERITY_LEVELS
from ..models import ScanStatistics, SecurityFinding
from .base import AbstractReporter


class MarkdownReporter(AbstractReporter):
    """Generate markdown format security reports."""

    def generate(
        self,
        findings: List[SecurityFinding],
        stats: ScanStatistics,
        output_file: Optional[Path] = None,
    ) -> str:
        """Generate markdown format security report.

        Args:
            findings: List of security findings
            stats: Scan statistics
            output_file: Optional output file path

        Returns:
            Markdown report content
        """
        # Group findings by severity
        findings_by_severity: Dict[str, List[SecurityFinding]] = {}
        for severity in SEVERITY_LEVELS.keys():
            findings_by_severity[severity] = [f for f in findings if f.severity == severity]

        report = self._generate_header(stats)
        report += self._generate_summary(stats)
        report += self._generate_findings_section(findings_by_severity)
        report += self._generate_recommendations()

        if output_file:
            self.save(report, output_file)

        return report

    def _generate_header(self, stats: ScanStatistics) -> str:
        """Generate report header."""
        project_name = Path.cwd().name
        return f"""# Security Scan Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Project:** {project_name}

"""

    def _generate_summary(self, stats: ScanStatistics) -> str:
        """Generate summary section."""
        return f"""## Summary

- **Files Scanned:** {stats.files_scanned}
- **Total Findings:** {stats.total_findings}
- **Secrets Found:** {stats.secrets_found}
- **Vulnerabilities:** {stats.vulnerabilities_found}
- **Permission Issues:** {stats.permission_issues}
- **SAST Findings:** {stats.sast_findings}

"""

    def _generate_findings_section(
        self, findings_by_severity: Dict[str, List[SecurityFinding]]
    ) -> str:
        """Generate findings section grouped by severity."""
        report = "## Findings by Severity\n\n"

        for severity, findings in findings_by_severity.items():
            if not findings:
                continue

            report += f"### {severity} ({len(findings)} findings)\n\n"

            for finding in findings[:10]:  # Limit to first 10 per severity
                report += f"**Type:** {finding.finding_type}\n"
                report += f"**Description:** {finding.description}\n"

                if finding.file_path:
                    report += f"**File:** `{finding.file_path}`"
                    if finding.line_number:
                        report += f" (line {finding.line_number})"
                    report += "\n"

                if finding.matched_pattern:
                    report += f"**Match:** `{finding.matched_pattern}`\n"

                if finding.commit_hash:
                    report += (
                        f"**Commit:** {finding.commit_hash} "
                        f"by {finding.author} on {finding.date}\n"
                    )

                if finding.remediation:
                    report += f"**Remediation:** {finding.remediation}\n"

                report += "\n---\n\n"

            if len(findings) > 10:
                report += f"*... and {len(findings) - 10} more {severity} findings*\n\n"

        return report

    def _generate_recommendations(self) -> str:
        """Generate recommendations section."""
        return """
## Recommendations

1. **Immediate Actions:**
   - Rotate any exposed credentials immediately
   - Remove secrets from source code
   - Update vulnerable dependencies

2. **Preventive Measures:**
   - Use environment variables for sensitive configuration
   - Implement pre-commit hooks to prevent secret commits
   - Regular dependency updates and security scanning
   - Use secrets management tools (e.g., HashiCorp Vault, AWS Secrets Manager)

3. **Best Practices:**
   - Never commit credentials, even in development
   - Use .gitignore for sensitive files
   - Implement least-privilege file permissions
   - Regular security audits and training
"""

"""JSON report generation for security findings."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import ScanStatistics, SecurityFinding
from .base import AbstractReporter


class JSONReporter(AbstractReporter):
    """Generate JSON format security reports."""

    def generate(
        self,
        findings: List[SecurityFinding],
        stats: ScanStatistics,
        output_file: Optional[Path] = None,
    ) -> str:
        """Generate JSON format security report.

        Args:
            findings: List of security findings
            stats: Scan statistics
            output_file: Optional output file path

        Returns:
            JSON report content
        """
        report_data = self._build_report_data(findings, stats)
        report = json.dumps(report_data, indent=2)

        if output_file:
            self.save(report, output_file)

        return report

    def _build_report_data(
        self, findings: List[SecurityFinding], stats: ScanStatistics
    ) -> Dict[str, Any]:
        """Build the report data structure.

        Args:
            findings: List of security findings
            stats: Scan statistics

        Returns:
            Report data dictionary
        """
        project_name = Path.cwd().name

        report_data: Dict[str, Any] = {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "project": project_name,
                "scanner_version": "2.0.0",
            },
            "statistics": {
                "files_scanned": stats.files_scanned,
                "total_findings": stats.total_findings,
                "secrets_found": stats.secrets_found,
                "vulnerabilities_found": stats.vulnerabilities_found,
                "permission_issues": stats.permission_issues,
                "sast_findings": stats.sast_findings,
            },
            "findings": [],
        }

        for finding in findings:
            report_data["findings"].append(self._serialize_finding(finding))

        return report_data

    def _serialize_finding(self, finding: SecurityFinding) -> Dict[str, Any]:
        """Serialize a SecurityFinding to dictionary.

        Args:
            finding: Security finding to serialize

        Returns:
            Serialized finding dictionary
        """
        return {
            "type": finding.finding_type,
            "severity": finding.severity,
            "description": finding.description,
            "file_path": finding.file_path,
            "line_number": finding.line_number,
            "matched_pattern": finding.matched_pattern,
            "remediation": finding.remediation,
            "commit_hash": finding.commit_hash,
            "author": finding.author,
            "date": finding.date,
            "false_positive": finding.false_positive,
        }

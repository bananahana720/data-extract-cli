"""Static Application Security Testing (SAST) scanner integration."""

import json
import subprocess
from pathlib import Path
from typing import List

import structlog  # type: ignore[import-not-found]

from ..models import SecurityFinding
from .base import AbstractScanner

logger = structlog.get_logger()

# Try to import optional Bandit dependency
try:
    from bandit.core import config as bandit_config  # type: ignore[import-not-found]
    from bandit.core import manager as bandit_manager  # type: ignore[import-not-found]

    HAS_BANDIT = True
except ImportError:
    HAS_BANDIT = False


class SASTScanner(AbstractScanner):
    """Scanner for SAST tool integration."""

    def scan(self) -> List[SecurityFinding]:
        """Run Static Application Security Testing.

        Returns:
            List of security findings
        """
        findings = []

        if HAS_BANDIT:
            findings.extend(self._scan_with_bandit())
        else:
            logger.warning("bandit_not_installed", message="Install bandit for SAST scanning")

        self.findings.extend(findings)
        return findings

    def _scan_with_bandit(self) -> List[SecurityFinding]:
        """Run Bandit security linter."""
        findings = []

        try:
            # Try using Bandit as a library first
            findings = self._scan_with_bandit_library()
        except Exception as e:
            logger.error("bandit_library_failed", error=str(e))
            # Fallback to CLI
            findings = self._scan_with_bandit_cli()

        return findings

    def _scan_with_bandit_library(self) -> List[SecurityFinding]:
        """Use Bandit as a library."""
        findings = []

        # Configure Bandit
        conf = bandit_config.BanditConfig()
        manager = bandit_manager.BanditManager(conf, "file")

        # Discover Python files to scan
        python_files = []
        for file_path in self.project_root.rglob("*.py"):
            if self.should_scan_file(file_path):
                python_files.append(str(file_path))

        if not python_files:
            logger.info("no_python_files_to_scan")
            return findings

        # Run Bandit on discovered files
        manager.discover_files(python_files)
        manager.run_tests()

        # Convert Bandit results to our format
        severity_map = {
            "HIGH": "HIGH",
            "MEDIUM": "MEDIUM",
            "LOW": "LOW",
            "UNDEFINED": "INFO",
        }

        for issue in manager.get_issue_list():
            findings.append(
                SecurityFinding(
                    finding_type="sast",
                    severity=severity_map.get(issue.severity, "INFO"),
                    description=f"{issue.test}: {issue.text}",
                    file_path=str(Path(issue.fname).relative_to(self.project_root)),
                    line_number=issue.lineno,
                    matched_pattern=issue.code if hasattr(issue, "code") else None,
                    remediation=f"Review and fix: {issue.test_id} - {issue.issue_text}",
                )
            )

        logger.info("bandit_scan_completed", findings_count=len(findings))
        return findings

    def _scan_with_bandit_cli(self) -> List[SecurityFinding]:
        """Fallback to running Bandit as CLI command."""
        findings = []

        try:
            result = subprocess.run(
                ["bandit", "-r", str(self.project_root), "-f", "json"],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                bandit_output = json.loads(result.stdout)
                for issue in bandit_output.get("results", []):
                    findings.append(
                        SecurityFinding(
                            finding_type="sast",
                            severity=issue.get("issue_severity", "INFO"),
                            description=(
                                f"{issue.get('test_name', 'Unknown')}: "
                                f"{issue.get('issue_text', 'Security issue')}"
                            ),
                            file_path=str(
                                Path(issue.get("filename")).relative_to(self.project_root)
                            ),
                            line_number=issue.get("line_number"),
                            remediation=f"Fix issue: {issue.get('test_id', 'Unknown')}",
                        )
                    )
                logger.info("bandit_cli_scan_completed", findings_count=len(findings))

        except Exception as cli_error:
            logger.error("bandit_cli_scan_failed", error=str(cli_error))

        return findings

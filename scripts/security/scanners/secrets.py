"""Secrets and credential detection scanner."""

import json
import re
import subprocess
from pathlib import Path
from typing import List

import structlog  # type: ignore[import-not-found]
from rich.progress import (  # type: ignore[import-not-found]
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)

from ..config import REMEDIATION_ADVICE, SCAN_EXTENSIONS, SECRET_PATTERNS
from ..models import SecurityFinding
from ..utils import CacheManager, find_files_to_scan
from .base import AbstractScanner

logger = structlog.get_logger()


class SecretsScanner(AbstractScanner):
    """Scanner for detecting hardcoded secrets and credentials."""

    def __init__(self, project_root: Path, cache_manager: CacheManager = None):
        """Initialize secrets scanner."""
        super().__init__(project_root)
        self.cache_manager = cache_manager or CacheManager()

    def scan(self, use_gitleaks: bool = True) -> List[SecurityFinding]:
        """Scan for hardcoded secrets and credentials.

        Args:
            use_gitleaks: Whether to use GitLeaks if available

        Returns:
            List of security findings
        """
        findings = []

        if use_gitleaks and self._is_gitleaks_available():
            # Use GitLeaks for comprehensive scanning
            findings.extend(self._scan_with_gitleaks())

        # Also run our custom pattern matching
        findings.extend(self._scan_with_patterns())

        self.findings.extend(findings)
        return findings

    def _is_gitleaks_available(self) -> bool:
        """Check if GitLeaks is installed and available."""
        try:
            result = subprocess.run(["gitleaks", "version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("gitleaks_not_installed")
            return False

    def _scan_with_gitleaks(self) -> List[SecurityFinding]:
        """Run GitLeaks scanner."""
        findings = []

        try:
            # Run gitleaks with JSON output
            cmd = [
                "gitleaks",
                "detect",
                "--source",
                str(self.project_root),
                "--report-format",
                "json",
                "--report-path",
                "/tmp/gitleaks-report.json",
                "--no-git",
            ]

            subprocess.run(cmd, capture_output=True, text=True)

            # Parse results
            report_path = Path("/tmp/gitleaks-report.json")
            if report_path.exists():
                with open(report_path, "r") as f:
                    gitleaks_findings = json.load(f)

                for finding in gitleaks_findings:
                    findings.append(
                        SecurityFinding(
                            finding_type="secret",
                            severity="HIGH",
                            description=finding.get("Description", "Secret detected"),
                            file_path=finding.get("File"),
                            line_number=finding.get("StartLine"),
                            matched_pattern=finding.get("Match"),
                            remediation="Remove or encrypt this secret and rotate credentials",
                        )
                    )

        except Exception as e:
            logger.error("gitleaks_scan_failed", error=str(e))

        return findings

    def _scan_with_patterns(self) -> List[SecurityFinding]:
        """Scan files using custom regex patterns."""
        findings = []
        files_scanned = 0

        # Find files to scan
        files_to_scan = find_files_to_scan(
            self.project_root, SCAN_EXTENSIONS, self.scan_ignore_patterns
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:

            task = progress.add_task("Scanning for secrets...", total=len(files_to_scan))

            for file_path in files_to_scan:
                files_scanned += 1
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    findings.extend(self._scan_content(file_path, content))

                except Exception as e:
                    logger.warning("failed_to_scan_file", file=str(file_path), error=str(e))

                progress.update(task, advance=1)

        logger.info("pattern_scan_completed", files_scanned=files_scanned)
        return findings

    def _scan_content(self, file_path: Path, content: str) -> List[SecurityFinding]:
        """Scan file content for secrets.

        Args:
            file_path: Path to the file
            content: File content to scan

        Returns:
            List of findings in this file
        """
        findings = []

        for pattern_name, pattern_info in SECRET_PATTERNS.items():
            regex = re.compile(pattern_info["pattern"], re.IGNORECASE | re.MULTILINE)
            for match in regex.finditer(content):
                # Calculate line number
                line_number = content[: match.start()].count("\n") + 1

                # Check if marked as false positive
                matched_text = match.group()
                if self.cache_manager.is_false_positive(str(file_path), line_number, matched_text):
                    continue

                findings.append(
                    SecurityFinding(
                        finding_type="secret",
                        severity=pattern_info["severity"],
                        description=pattern_info["description"],
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_number,
                        matched_pattern=(
                            matched_text[:50] + "..." if len(matched_text) > 50 else matched_text
                        ),
                        remediation=REMEDIATION_ADVICE.get(
                            pattern_name,
                            "Remove hardcoded secret and use environment variables",
                        ),
                    )
                )

        return findings

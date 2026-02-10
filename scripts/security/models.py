"""Data models for security scanning."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SecurityFinding:
    """Represents a security finding."""

    finding_type: str  # "secret", "vulnerability", "permission", "sast"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    matched_pattern: Optional[str] = None
    remediation: Optional[str] = None
    false_positive: bool = False
    commit_hash: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None


@dataclass
class ScanStatistics:
    """Statistics for security scanning."""

    files_scanned: int = 0
    secrets_found: int = 0
    vulnerabilities_found: int = 0
    permission_issues: int = 0
    sast_findings: int = 0
    total_findings: int = 0

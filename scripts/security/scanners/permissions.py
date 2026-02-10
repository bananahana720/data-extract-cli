"""File permissions validation scanner."""

import os
from pathlib import Path
from typing import List

import structlog  # type: ignore[import-not-found]

from ..config import SENSITIVE_FILES
from ..models import SecurityFinding
from .base import AbstractScanner

logger = structlog.get_logger()


class PermissionsScanner(AbstractScanner):
    """Scanner for validating file permissions on sensitive files."""

    def scan(self) -> List[SecurityFinding]:
        """Validate file permissions for sensitive files.

        Returns:
            List of security findings
        """
        findings = []

        if os.name != "posix":
            logger.info("permission_scan_skipped", reason="Not a POSIX system")
            return findings

        for pattern, info in SENSITIVE_FILES.items():
            for file_path in self.project_root.glob(pattern):
                if not file_path.is_file():
                    continue

                finding = self._check_file_permissions(file_path, info)
                if finding:
                    findings.append(finding)

        self.findings.extend(findings)
        return findings

    def _check_file_permissions(
        self, file_path: Path, expected_info: dict
    ) -> SecurityFinding | None:
        """Check if file has appropriate permissions.

        Args:
            file_path: Path to the file
            expected_info: Expected severity and permissions

        Returns:
            SecurityFinding if permissions are too permissive, None otherwise
        """
        try:
            # Get current permissions
            stat_info = file_path.stat()
            current_mode = stat_info.st_mode & 0o777
            expected_mode = int(expected_info["permissions"])

            if current_mode > expected_mode:  # More permissive than expected
                return SecurityFinding(
                    finding_type="permission",
                    severity=str(expected_info["severity"]),
                    description="Overly permissive file permissions",
                    file_path=str(file_path.relative_to(self.project_root)),
                    remediation=(
                        f"Change permissions to {oct(expected_mode)} "
                        f"(chmod {oct(expected_mode)[2:]} {file_path})"
                    ),
                )
        except Exception as e:
            logger.warning("failed_to_check_permissions", file=str(file_path), error=str(e))

        return None

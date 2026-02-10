"""Dependency vulnerability scanner."""

import json
import subprocess
from typing import List

import structlog  # type: ignore[import-not-found]

from ..models import SecurityFinding
from .base import AbstractScanner

logger = structlog.get_logger()

# Try to import optional dependency
try:
    from safety import check as safety_check  # type: ignore[import-not-found]

    HAS_SAFETY = True
except ImportError:
    HAS_SAFETY = False


class DependencyScanner(AbstractScanner):
    """Scanner for vulnerable dependencies."""

    def scan(self) -> List[SecurityFinding]:
        """Check for vulnerable dependencies.

        Returns:
            List of security findings
        """
        findings = []

        # Check Python dependencies
        if HAS_SAFETY:
            findings.extend(self._scan_python_deps_safety())
        else:
            findings.extend(self._scan_python_deps_pip_audit())

        # Check JavaScript dependencies if package.json exists
        if (self.project_root / "package.json").exists():
            findings.extend(self._scan_npm_deps())

        self.findings.extend(findings)
        return findings

    def _scan_python_deps_safety(self) -> List[SecurityFinding]:
        """Scan Python dependencies using safety."""
        findings = []

        try:
            # Get installed packages
            result = subprocess.run(
                ["pip", "list", "--format", "json"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                packages = json.loads(result.stdout)

                # Check with safety
                for vuln in safety_check.check(packages):
                    findings.append(
                        SecurityFinding(
                            finding_type="vulnerability",
                            severity=self._map_cvss_to_severity(vuln.get("cvss", 0)),
                            description=(
                                f"{vuln['package']} {vuln['installed_version']}: "
                                f"{vuln['description']}"
                            ),
                            remediation=f"Update to {vuln['safe_version']} or later",
                        )
                    )

        except Exception as e:
            logger.error("safety_scan_failed", error=str(e))

        return findings

    def _scan_python_deps_pip_audit(self) -> List[SecurityFinding]:
        """Scan Python dependencies using pip-audit."""
        findings = []

        try:
            # Check if pip-audit is available
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                audit_results = json.loads(result.stdout)

                for vuln in audit_results.get("vulnerabilities", []):
                    findings.append(
                        SecurityFinding(
                            finding_type="vulnerability",
                            severity=self._map_cvss_to_severity(vuln.get("cvss_score", 0)),
                            description=(
                                f"{vuln['name']} {vuln['version']}: " f"{vuln['description']}"
                            ),
                            remediation=(
                                f"Update to "
                                f"{vuln.get('fixed_version', 'latest secure version')}"
                            ),
                        )
                    )

        except FileNotFoundError:
            logger.info("pip_audit_not_installed")
        except Exception as e:
            logger.error("pip_audit_scan_failed", error=str(e))

        return findings

    def _scan_npm_deps(self) -> List[SecurityFinding]:
        """Scan npm dependencies for vulnerabilities."""
        findings = []

        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.stdout:
                audit_data = json.loads(result.stdout)

                for advisory_id, advisory in audit_data.get("advisories", {}).items():
                    findings.append(
                        SecurityFinding(
                            finding_type="vulnerability",
                            severity=advisory["severity"].upper(),
                            description=(f"{advisory['module_name']}: {advisory['title']}"),
                            remediation=advisory.get("recommendation", "Update to secure version"),
                        )
                    )

        except FileNotFoundError:
            logger.info("npm_not_available")
        except Exception as e:
            logger.error("npm_audit_failed", error=str(e))

        return findings

    @staticmethod
    def _map_cvss_to_severity(cvss_score: float) -> str:
        """Map CVSS score to severity level.

        Args:
            cvss_score: CVSS vulnerability score

        Returns:
            Severity level string
        """
        if cvss_score >= 9.0:
            return "CRITICAL"
        elif cvss_score >= 7.0:
            return "HIGH"
        elif cvss_score >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"

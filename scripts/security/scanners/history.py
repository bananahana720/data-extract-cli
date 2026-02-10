"""Git history scanner for previously committed secrets."""

import re
from datetime import datetime
from typing import List

import structlog  # type: ignore[import-not-found]
from rich.progress import Progress, SpinnerColumn, TextColumn  # type: ignore[import-not-found]

from ..config import SECRET_PATTERNS
from ..models import SecurityFinding
from .base import AbstractScanner

logger = structlog.get_logger()

# Try to import optional GitPython dependency
try:
    import git  # type: ignore[import-not-found]

    HAS_GITPYTHON = True
except ImportError:
    HAS_GITPYTHON = False


class GitHistoryScanner(AbstractScanner):
    """Scanner for secrets in git history."""

    def scan(self, max_commits: int = 100) -> List[SecurityFinding]:
        """Scan git history for previously committed secrets.

        Args:
            max_commits: Maximum number of commits to scan

        Returns:
            List of security findings
        """
        findings = []

        if not HAS_GITPYTHON:
            logger.warning("git_history_scan_skipped", reason="GitPython not installed")
            return findings

        try:
            repo = git.Repo(self.project_root)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:

                progress.add_task(f"Scanning last {max_commits} commits...")

                for commit in list(repo.iter_commits(max_count=max_commits)):
                    # Check commit message
                    findings.extend(self._scan_commit_message(commit))

                    # Check diff
                    if commit.parents:
                        findings.extend(self._scan_commit_diff(commit))

        except Exception as e:
            logger.error("git_history_scan_failed", error=str(e))

        self.findings.extend(findings)
        return findings

    def _scan_commit_message(self, commit) -> List[SecurityFinding]:
        """Scan a commit message for secrets.

        Args:
            commit: Git commit object

        Returns:
            List of findings in the commit message
        """
        findings = []

        for pattern_name, pattern_info in SECRET_PATTERNS.items():
            regex = re.compile(pattern_info["pattern"], re.IGNORECASE)
            if regex.search(commit.message):
                findings.append(
                    SecurityFinding(
                        finding_type="secret",
                        severity=pattern_info["severity"],
                        description=f"{pattern_info['description']} in commit message",
                        commit_hash=commit.hexsha[:8],
                        author=commit.author.email,
                        date=datetime.fromtimestamp(commit.committed_date).isoformat(),
                        remediation=(
                            "Secret found in commit history - consider "
                            "rewriting history if not pushed"
                        ),
                    )
                )

        return findings

    def _scan_commit_diff(self, commit) -> List[SecurityFinding]:
        """Scan commit diff for secrets.

        Args:
            commit: Git commit object

        Returns:
            List of findings in the diff
        """
        findings = []

        diffs = commit.diff(commit.parents[0], create_patch=True)
        for diff in diffs:
            if not diff.diff:
                continue

            diff_text = diff.diff.decode("utf-8", errors="ignore")
            for pattern_name, pattern_info in SECRET_PATTERNS.items():
                regex = re.compile(pattern_info["pattern"], re.IGNORECASE)
                if regex.search(diff_text):
                    findings.append(
                        SecurityFinding(
                            finding_type="secret",
                            severity=pattern_info["severity"],
                            description=f"{pattern_info['description']} in commit diff",
                            file_path=diff.a_path or diff.b_path,
                            commit_hash=commit.hexsha[:8],
                            author=commit.author.email,
                            date=datetime.fromtimestamp(commit.committed_date).isoformat(),
                            remediation=(
                                "Secret in git history - rotate credentials and "
                                "consider cleaning history"
                            ),
                        )
                    )

        return findings

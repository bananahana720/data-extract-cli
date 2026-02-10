#!/usr/bin/env python3
"""
Security Scanner - Refactored Main Entry Point

This is now a thin wrapper that maintains CLI compatibility while using
the modular security scanning framework in the security/ package.

Usage:
    python scripts/scan_security.py                    # Full security scan
    python scripts/scan_security.py --secrets-only     # Only scan for secrets
    python scripts/scan_security.py --deps-only        # Only check dependencies
    python scripts/scan_security.py --history          # Scan git history
    python scripts/scan_security.py --pre-commit       # Pre-commit hook mode
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for security package imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

import structlog  # type: ignore[import-not-found]  # noqa: E402
from security.config import REPORTS_DIR, SECRET_PATTERNS  # noqa: E402
from security.models import SecurityFinding  # noqa: E402
from security.orchestrator import SecurityOrchestrator  # noqa: E402

# Configure structured logging
logger = structlog.get_logger()

# Backward compatibility exports for tests
# The SecurityScanner class has been refactored into SecurityOrchestrator
SecurityScanner = SecurityOrchestrator

# Re-export for test compatibility
__all__ = ["SECRET_PATTERNS", "SecurityFinding", "SecurityScanner", "main"]


def main() -> None:
    """Main entry point for security scanner."""
    parser = argparse.ArgumentParser(
        description="Security Scanner - Comprehensive security analysis"
    )
    parser.add_argument("--secrets-only", action="store_true", help="Only scan for secrets")
    parser.add_argument("--deps-only", action="store_true", help="Only check dependencies")
    parser.add_argument(
        "--permissions-only", action="store_true", help="Only check file permissions"
    )
    parser.add_argument("--sast-only", action="store_true", help="Only run SAST analysis")
    parser.add_argument("--history", action="store_true", help="Scan git history for secrets")
    parser.add_argument(
        "--max-commits",
        type=int,
        default=100,
        help="Maximum commits to scan in history",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "text"],
        default="markdown",
        help="Report format",
    )
    parser.add_argument("--output", type=Path, help="Output file for report")
    parser.add_argument(
        "--pre-commit",
        action="store_true",
        help="Pre-commit hook mode (fail on findings)",
    )
    parser.add_argument(
        "--use-gitleaks",
        action="store_true",
        default=True,
        help="Use GitLeaks if available",
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = SecurityOrchestrator()

    try:
        # Run selected scans
        if args.secrets_only:
            orchestrator.scan_secrets(use_gitleaks=args.use_gitleaks)
        elif args.deps_only:
            orchestrator.scan_dependencies()
        elif args.permissions_only:
            orchestrator.scan_permissions()
        elif args.sast_only:
            orchestrator.scan_sast()
        elif args.history:
            orchestrator.scan_history(max_commits=args.max_commits)
        else:
            # Run all scans
            orchestrator.run_all_scans(use_gitleaks=args.use_gitleaks)

        # Display results
        orchestrator.display_findings()

        # Generate report if requested
        if args.output or args.format != "markdown":
            output_file = args.output
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = "json" if args.format == "json" else "md"
                output_file = REPORTS_DIR / f"security_report_{timestamp}.{ext}"

            orchestrator.generate_report(args.format, output_file)
            print(f"\n[green]Report saved to: {output_file}[/green]")

        # Exit with error code if findings in pre-commit mode
        if args.pre_commit and orchestrator.findings:
            critical_or_high = [
                f for f in orchestrator.findings if f.severity in ["CRITICAL", "HIGH"]
            ]
            if critical_or_high:
                print(
                    "\n[red]❌ Pre-commit check failed: "
                    "Critical/High security issues found[/red]"
                )
                sys.exit(1)

        # Success message
        if not orchestrator.findings:
            print("\n[green]✓ Security scan completed successfully " "with no findings[/green]")

    except KeyboardInterrupt:
        logger.info("scan_interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"[red]Error during security scan: {e}[/red]")
        logger.exception("security_scan_error")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
PII Scanner - Automated Personal Identifiable Information Detection

Provides comprehensive PII detection capabilities for test data validation.
Ensures QA fixtures contain no sensitive or personally identifiable information.
"""

import re
from typing import Dict, List, Optional, Set


class PIIScanner:
    """
    Comprehensive PII detection scanner for test data validation.

    Detects various types of personally identifiable information including:
    - Email addresses
    - Phone numbers
    - Social Security Numbers (SSN)
    - Credit card numbers
    - Names and addresses
    - API keys and tokens
    - Internal IP addresses
    """

    # Common test names that are acceptable (not real PII)
    ALLOWED_TEST_NAMES = {
        "Alice",
        "Bob",
        "Charlie",
        "David",
        "Eve",
        "Frank",
        "Test User",
        "Sample Name",
        "Example Person",
        "User One",
        "User Two",
        "Test Admin",
    }

    # PII detection patterns
    PATTERNS = {
        # Email addresses
        "email": re.compile(
            r"\b[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Z|a-z]{2,}\b",
            re.IGNORECASE,
        ),
        # Phone numbers (various formats)
        "phone": re.compile(
            r"""
            \b(?:
                # International format with clear prefix
                \+[1-9]\d{10,14}|
                # US/Canada format with separators
                (?:\+?1[-.\s])?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}|
                # Generic format with required separators
                \d{3}[-.\s]\d{3}[-.\s]\d{4}
            )\b
            """,
            re.VERBOSE,
        ),
        # Social Security Numbers
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        # Credit card numbers (basic pattern)
        "credit_card": re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b"),
        # IP addresses (private ranges that shouldn't be in test data)
        "private_ip": re.compile(
            r"\b(?:"
            r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # Class A private
            r"172\.(?:1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}|"  # Class B private
            r"192\.168\.\d{1,3}\.\d{1,3}"  # Class C private
            r")\b"
        ),
        # API keys and tokens (common patterns)
        "api_key": re.compile(
            r"(?:"
            r'(?:api[_-]?key|apikey|access[_-]?token|auth[_-]?token|bearer)\s*[:=]\s*["\']?[\w-]{20,}["\']?|'
            r"Bearer\s+[\w-]{20,}|"
            r"sk_(?:live|test)_[\w-]{24,}"  # Stripe-like keys
            r")",
            re.IGNORECASE,
        ),
        # AWS access keys
        "aws_key": re.compile(
            r"(?:"
            r"AKIA[0-9A-Z]{16}|"  # AWS Access Key ID
            r'aws_secret_access_key\s*[:=]\s*["\']?[\w/+=]{40}["\']?'
            r")",
            re.IGNORECASE,
        ),
        # Street addresses
        "street_address": re.compile(
            r"\b\d{1,5}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
            r"(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|"
            r"Lane|Ln\.?|Drive|Dr\.?|Court|Ct\.?|Plaza|Square|Park)\b",
            re.IGNORECASE,
        ),
        # Passport numbers (generic pattern)
        "passport": re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"),
        # Driver's license (generic pattern - varies by state/country)
        "drivers_license": re.compile(r"\b(?:DL|License)[\s#:]*[A-Z0-9]{6,12}\b", re.IGNORECASE),
    }

    # Sensitive data patterns (not PII but should be avoided)
    SENSITIVE_PATTERNS = {
        "password": re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*\S+", re.IGNORECASE),
        "database_url": re.compile(
            r"(?:mysql|postgresql|mongodb|redis)://[^@]+@[^\s]+", re.IGNORECASE
        ),
        "private_key": re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", re.IGNORECASE),
        "jwt_token": re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
    }

    # Real names to detect (shouldn't appear in synthetic test data)
    REAL_NAME_PATTERNS = [
        re.compile(r"\bJohn\s+(?:Doe|Smith|Johnson|Williams|Brown)\b", re.IGNORECASE),
        re.compile(r"\bJane\s+(?:Doe|Smith|Johnson|Williams|Brown)\b", re.IGNORECASE),
        re.compile(r"\bMichael\s+(?:Smith|Johnson|Williams|Brown|Davis)\b", re.IGNORECASE),
        re.compile(r"\bEmily\s+(?:Smith|Johnson|Williams|Brown|Davis)\b", re.IGNORECASE),
        re.compile(r"\bRobert\s+(?:Smith|Johnson|Williams|Brown|Davis)\b", re.IGNORECASE),
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Initialize PII Scanner.

        Args:
            strict_mode: If True, flag potential PII even if uncertain
        """
        self.strict_mode = strict_mode
        self.violations: List[Dict] = []

    def scan_text(self, text: str, context: str = "unknown") -> List[Dict]:
        """
        Scan text for PII and sensitive data.

        Args:
            text: Text to scan
            context: Context identifier (e.g., file name, corpus name)

        Returns:
            List of violations found
        """
        violations = []

        # Check PII patterns
        for pii_type, pattern in self.PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                # Filter out false positives
                filtered_matches = self._filter_false_positives(pii_type, matches)
                if filtered_matches:
                    violations.append(
                        {
                            "type": pii_type,
                            "context": context,
                            "matches": filtered_matches[:5],  # Limit to first 5
                            "severity": "HIGH",
                        }
                    )

        # Check sensitive patterns
        for sensitive_type, pattern in self.SENSITIVE_PATTERNS.items():
            if pattern.search(text):
                violations.append(
                    {
                        "type": sensitive_type,
                        "context": context,
                        "severity": "MEDIUM",
                    }
                )

        # Check for real names
        if self._contains_real_names(text):
            violations.append(
                {
                    "type": "real_names",
                    "context": context,
                    "severity": "LOW" if not self.strict_mode else "MEDIUM",
                }
            )

        return violations

    def scan_corpus(self, corpus: List[str], corpus_name: str = "unknown") -> Dict:
        """
        Scan entire corpus for PII.

        Args:
            corpus: List of documents to scan
            corpus_name: Name of the corpus

        Returns:
            Scan results with summary
        """
        all_violations = []

        for idx, doc in enumerate(corpus):
            context = f"{corpus_name}[{idx}]"
            violations = self.scan_text(doc, context)
            all_violations.extend(violations)

        return {
            "corpus": corpus_name,
            "documents_scanned": len(corpus),
            "violations": all_violations,
            "violation_count": len(all_violations),
            "is_clean": len(all_violations) == 0,
            "summary": self._generate_summary(all_violations),
        }

    def _filter_false_positives(self, pii_type: str, matches: List[str]) -> List[str]:
        """
        Filter out known false positives.

        Args:
            pii_type: Type of PII detected
            matches: List of potential matches

        Returns:
            Filtered list of matches
        """
        filtered = []

        for match in matches:
            # Skip example emails
            if pii_type == "email":
                if any(
                    domain in match.lower() for domain in ["example.com", "test.com", "localhost"]
                ):
                    continue

            # Skip test phone numbers
            elif pii_type == "phone":
                if match in ["555-0123", "555-555-5555", "123-456-7890", "000-000-0000"]:
                    continue

            # Skip test SSNs
            elif pii_type == "ssn":
                if match in ["123-45-6789", "000-00-0000", "111-11-1111"]:
                    continue

            # Skip test credit cards
            elif pii_type == "credit_card":
                # Test cards usually have repeating patterns
                if re.match(r"^(\d)\1{15}$", match.replace(" ", "").replace("-", "")):
                    continue

            filtered.append(match)

        return filtered

    def _contains_real_names(self, text: str) -> bool:
        """
        Check if text contains real-looking names.

        Args:
            text: Text to check

        Returns:
            True if real names detected
        """
        # Check against known test names (these are OK)
        for allowed_name in self.ALLOWED_TEST_NAMES:
            text = text.replace(allowed_name, "")

        # Check for real name patterns
        for pattern in self.REAL_NAME_PATTERNS:
            if pattern.search(text):
                return True

        return False

    def _generate_summary(self, violations: List[Dict]) -> Dict:
        """
        Generate summary of violations.

        Args:
            violations: List of violations

        Returns:
            Summary statistics
        """
        if not violations:
            return {"status": "CLEAN", "message": "No PII detected"}

        by_type = {}
        by_severity = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for violation in violations:
            vtype = violation["type"]
            severity = violation["severity"]

            by_type[vtype] = by_type.get(vtype, 0) + 1
            by_severity[severity] += 1

        return {
            "status": "VIOLATIONS_FOUND",
            "by_type": by_type,
            "by_severity": by_severity,
            "high_severity_count": by_severity["HIGH"],
            "recommendation": "Remove all PII before using in production",
        }

    def validate_fixture(self, fixture_path: str) -> bool:
        """
        Validate a fixture file for PII.

        Args:
            fixture_path: Path to fixture file

        Returns:
            True if fixture is clean
        """
        from pathlib import Path

        path = Path(fixture_path)
        if not path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_path}")

        content = path.read_text()
        violations = self.scan_text(content, str(fixture_path))

        if violations:
            print(f"⚠️ PII found in {fixture_path}:")
            for violation in violations:
                print(f"  - {violation['type']}: {violation.get('matches', 'detected')}")
            return False

        print(f"✅ {fixture_path} is PII-free")
        return True


def scan_directory(directory: str, extensions: Optional[Set[str]] = None) -> Dict:
    """
    Scan entire directory for PII.

    Args:
        directory: Directory path to scan
        extensions: File extensions to scan (default: .py, .txt, .json, .yaml)

    Returns:
        Scan results
    """
    from pathlib import Path

    if extensions is None:
        extensions = {".py", ".txt", ".json", ".yaml", ".yml", ".md"}

    scanner = PIIScanner()
    results = {
        "directory": directory,
        "files_scanned": 0,
        "clean_files": [],
        "violated_files": [],
        "all_violations": [],
    }

    dir_path = Path(directory)
    for file_path in dir_path.rglob("*"):
        if file_path.is_file() and file_path.suffix in extensions:
            results["files_scanned"] += 1

            try:
                content = file_path.read_text()
                violations = scanner.scan_text(content, str(file_path))

                if violations:
                    results["violated_files"].append(str(file_path))
                    results["all_violations"].extend(violations)
                else:
                    results["clean_files"].append(str(file_path))

            except Exception as e:
                print(f"Error scanning {file_path}: {e}")

    results["summary"] = {
        "total_files": results["files_scanned"],
        "clean_files": len(results["clean_files"]),
        "violated_files": len(results["violated_files"]),
        "total_violations": len(results["all_violations"]),
        "is_clean": len(results["violated_files"]) == 0,
    }

    return results


def create_pii_report(scan_results: Dict, output_path: str):
    """
    Create detailed PII scan report.

    Args:
        scan_results: Results from scan_directory or scan_corpus
        output_path: Path to write report
    """
    from pathlib import Path

    report = []
    report.append("# PII Scan Report\n")
    report.append(f"**Scan Date**: {__import__('datetime').datetime.now().isoformat()}\n")

    if "directory" in scan_results:
        report.append(f"**Directory**: `{scan_results['directory']}`\n")
    elif "corpus" in scan_results:
        report.append(f"**Corpus**: {scan_results['corpus']}\n")

    # Summary
    report.append("\n## Summary\n")
    summary = scan_results.get("summary", {})

    if summary.get("is_clean"):
        report.append("✅ **Status**: CLEAN - No PII detected\n")
    else:
        report.append("⚠️ **Status**: VIOLATIONS FOUND\n")

    # Statistics
    report.append("\n## Statistics\n")

    if "files_scanned" in scan_results:
        report.append(f"- Files scanned: {scan_results['files_scanned']}\n")
        report.append(f"- Clean files: {len(scan_results.get('clean_files', []))}\n")
        report.append(f"- Files with violations: {len(scan_results.get('violated_files', []))}\n")

    if "violations" in scan_results:
        violations = scan_results["violations"]
        if violations:
            report.append(f"\n## Violations ({len(violations)} found)\n")

            for violation in violations:
                report.append(f"\n### {violation['type'].upper()}\n")
                report.append(f"- **Context**: {violation['context']}\n")
                report.append(f"- **Severity**: {violation['severity']}\n")

                if "matches" in violation:
                    report.append(f"- **Matches**: {violation['matches'][:3]}\n")

    # Write report
    Path(output_path).write_text("".join(report))
    print(f"📝 Report written to: {output_path}")


# Export main components
__all__ = [
    "PIIScanner",
    "scan_directory",
    "create_pii_report",
]

"""Configuration and constants for security scanning."""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCANIGNORE_FILE = PROJECT_ROOT / ".scanignore"
SECURITY_CONFIG_FILE = PROJECT_ROOT / ".security.yaml"
REPORTS_DIR = PROJECT_ROOT / "docs" / "security-reports"
CACHE_DIR = PROJECT_ROOT / ".cache" / "security"

# Severity levels with color mappings
SEVERITY_LEVELS = {
    "CRITICAL": "red",
    "HIGH": "bright_red",
    "MEDIUM": "yellow",
    "LOW": "bright_yellow",
    "INFO": "cyan",
}

# Secret patterns to detect
SECRET_PATTERNS = {
    "aws_access_key": {
        "pattern": r"AKIA[0-9A-Z]{16}",
        "severity": "CRITICAL",
        "description": "AWS Access Key ID",
    },
    "aws_secret_key": {
        "pattern": r"aws[_\-]?secret[_\-]?access[_\-]?key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}['\"]?",
        "severity": "CRITICAL",
        "description": "AWS Secret Access Key",
    },
    "github_token": {
        "pattern": r"gh[ps]_[A-Za-z0-9]{36}",
        "severity": "CRITICAL",
        "description": "GitHub Personal Access Token",
    },
    "api_key_generic": {
        "pattern": r"(?i)(api[_\-]?key|apikey|api_secret)['\"]?\s*[:=]\s*['\"]?[a-zA-Z0-9\-_]{32,}['\"]?",
        "severity": "HIGH",
        "description": "Generic API Key",
    },
    "private_key": {
        "pattern": r"-----BEGIN\s+(RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----",
        "severity": "CRITICAL",
        "description": "Private Cryptographic Key",
    },
    "jwt_token": {
        "pattern": r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        "severity": "HIGH",
        "description": "JWT Token",
    },
    "slack_webhook": {
        "pattern": r"https://hooks\.slack\.com/services/T[A-Z0-9]{8}/B[A-Z0-9]{8}/[A-Za-z0-9]{24}",
        "severity": "MEDIUM",
        "description": "Slack Webhook URL",
    },
    "database_connection": {
        "pattern": r"(mongodb|postgres|postgresql|mysql|mssql|redis)://[^/\s]+:[^@/\s]+@[^/\s]+",
        "severity": "CRITICAL",
        "description": "Database Connection String with Credentials",
    },
    "password_in_url": {
        "pattern": r"://[^/\s]+:[^@/\s]+@",
        "severity": "HIGH",
        "description": "Password in URL",
    },
    "bearer_token": {
        "pattern": r"(?i)bearer\s+[a-z0-9\-_.]{20,}",
        "severity": "HIGH",
        "description": "Bearer Token",
    },
}

# File extensions to scan
SCAN_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".ps1",
    ".bat",
    ".cmd",
    ".yml",
    ".yaml",
    ".json",
    ".xml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".config",
    ".env",
    ".properties",
    ".sql",
    ".md",
    ".txt",
    ".dockerfile",
    "Dockerfile",
}

# Sensitive file patterns with expected permissions
SENSITIVE_FILES = {
    ".env": {"severity": "HIGH", "permissions": 0o600},
    ".env.*": {"severity": "HIGH", "permissions": 0o600},
    "*.key": {"severity": "CRITICAL", "permissions": 0o600},
    "*.pem": {"severity": "CRITICAL", "permissions": 0o600},
    "*.p12": {"severity": "CRITICAL", "permissions": 0o600},
    "*.pfx": {"severity": "CRITICAL", "permissions": 0o600},
    "id_rsa*": {"severity": "CRITICAL", "permissions": 0o600},
    "id_dsa*": {"severity": "CRITICAL", "permissions": 0o600},
    "id_ecdsa*": {"severity": "CRITICAL", "permissions": 0o600},
    "id_ed25519*": {"severity": "CRITICAL", "permissions": 0o600},
    ".ssh/*": {"severity": "HIGH", "permissions": 0o600},
    "credentials*": {"severity": "HIGH", "permissions": 0o600},
    ".aws/credentials": {"severity": "CRITICAL", "permissions": 0o600},
    ".netrc": {"severity": "HIGH", "permissions": 0o600},
}

# Directories to skip during scanning
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".tox",
    "TRASH",
    ".cache",
}

# Remediation advice for different pattern types
REMEDIATION_ADVICE = {
    "aws_access_key": "Rotate AWS credentials immediately and use IAM roles or AWS Secrets Manager",
    "aws_secret_key": "Rotate AWS credentials immediately and use IAM roles or AWS Secrets Manager",
    "github_token": "Revoke token in GitHub settings and use environment variables",
    "private_key": "Remove key from repository, regenerate if compromised, use key management service",
    "database_connection": "Use environment variables or secrets management for connection strings",
    "jwt_token": "Tokens should not be hardcoded; implement proper token management",
    "api_key_generic": "Remove hardcoded API key and use environment variables or secrets management",
    "slack_webhook": "Rotate webhook URL and use environment variables for configuration",
    "password_in_url": "Never include passwords in URLs; use proper authentication mechanisms",
    "bearer_token": "Store tokens securely in environment variables or secrets management system",
}

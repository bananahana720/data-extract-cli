"""Security scanning package for comprehensive codebase security analysis."""

from .config import PROJECT_ROOT, SEVERITY_LEVELS
from .models import SecurityFinding

__version__ = "2.0.0"
__all__ = ["SecurityFinding", "SEVERITY_LEVELS", "PROJECT_ROOT"]

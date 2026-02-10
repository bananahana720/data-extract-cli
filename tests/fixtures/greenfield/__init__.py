"""
Greenfield Fixtures Standardization Framework

This package provides reusable fixtures that embed AI instructions and BMAD-approved
schemas to ensure deterministic quality for scripts and tests.

Purpose:
- Reduce AI token consumption on boilerplate decisions
- Ensure consistent code quality across all scripts
- Provide validated patterns for common development tasks
- Enable faster development through reusable components
"""

from pathlib import Path

# Package metadata
__version__ = "1.0.0"
__all__ = [
    "script_fixtures",
    "test_fixtures",
    "ai_instructions",
    "schemas",
]

# Package paths
GREENFIELD_ROOT = Path(__file__).parent
SCHEMAS_DIR = GREENFIELD_ROOT / "schemas"
INSTRUCTIONS_PATH = GREENFIELD_ROOT / "ai_instructions.md"


# Load AI instructions on import for easy access
def load_ai_instructions() -> str:
    """Load AI development guidelines."""
    if INSTRUCTIONS_PATH.exists():
        return INSTRUCTIONS_PATH.read_text(encoding="utf-8")
    return ""


# Make instructions available as module attribute
AI_INSTRUCTIONS = load_ai_instructions()

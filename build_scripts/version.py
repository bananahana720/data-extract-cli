"""Single source of truth for package version.

This module provides centralized version information for:
- PyInstaller spec file (data_extract.spec)
- Inno Setup installer script (installer.iss)
- Package metadata (pyproject.toml references this indirectly)

Usage:
    from version import __version__, __app_name__, __author__

Version Format:
    Semantic versioning: MAJOR.MINOR.PATCH
    - MAJOR: Breaking changes
    - MINOR: New features (backward compatible)
    - PATCH: Bug fixes (backward compatible)
"""

__version__ = "1.0.0"
__app_name__ = "Data Extraction Tool"
__author__ = "Data Extraction Tool"


def get_version_tuple() -> tuple[int, int, int]:
    """Return version as tuple for comparisons.

    Returns:
        Tuple of (major, minor, patch) integers

    Example:
        >>> get_version_tuple()
        (1, 0, 0)
    """
    parts = [int(x) for x in __version__.split(".")]
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {__version__}. Expected MAJOR.MINOR.PATCH")
    return (parts[0], parts[1], parts[2])


def get_version_string() -> str:
    """Return formatted version string.

    Returns:
        Version string in format 'AppName v1.0.0'

    Example:
        >>> get_version_string()
        'Data Extraction Tool v1.0.0'
    """
    return f"{__app_name__} v{__version__}"

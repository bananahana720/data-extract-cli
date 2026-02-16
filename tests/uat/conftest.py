"""UAT test fixtures for CLI validation.

Provides fixtures for tmux-cli session management, sample corpus,
and journey test infrastructure.

Story 5-0: UAT Testing Framework
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import pytest

if TYPE_CHECKING:
    from tests.uat.framework.tmux_wrapper import TmuxSession


# -----------------------------------------------------------------------------
# Pytest Markers
# -----------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Register custom UAT markers."""
    config.addinivalue_line("markers", "uat: marks tests as UAT (User Acceptance Tests)")
    config.addinivalue_line(
        "markers",
        "journey: marks tests as user journey tests (deselect if features not implemented)",
    )
    config.addinivalue_line("markers", "requires_tmux: marks tests requiring tmux")


# -----------------------------------------------------------------------------
# tmux Availability Check
# -----------------------------------------------------------------------------


def _local_tmux_cli_shim() -> Path:
    """Return path to local tmux-cli compatibility shim."""
    return Path(__file__).resolve().parents[2] / "scripts" / "tmux-cli"


@pytest.fixture(scope="session")
def tmux_available() -> bool:
    """Check if tmux is available on the system."""
    return shutil.which("tmux") is not None


@pytest.fixture(scope="session")
def tmux_cli_available() -> bool:
    """Check if tmux-cli or local shim is available on the system."""
    if shutil.which("tmux-cli") is not None:
        return True
    local_shim = _local_tmux_cli_shim()
    return local_shim.is_file() and os.access(local_shim, os.X_OK)


# -----------------------------------------------------------------------------
# TmuxSession Fixture
# -----------------------------------------------------------------------------


@pytest.fixture
def tmux_session(
    tmux_available: bool, tmux_cli_available: bool
) -> Generator["TmuxSession", None, None]:
    """Provide a TmuxSession for UAT tests.

    Automatically launches a shell pane and cleans up after test.

    Yields:
        TmuxSession: A configured tmux session wrapper

    Raises:
        pytest.skip: If tmux or tmux-cli is not available
    """
    if not tmux_available:
        pytest.skip("tmux not available on this system")
    if not tmux_cli_available:
        pytest.skip(
            "tmux-cli not available and local shim missing "
            "(expected executable at scripts/tmux-cli)"
        )

    # Import here to avoid import errors when tmux not available
    from tests.uat.framework.tmux_wrapper import TmuxSession

    tmux_cli_bin = shutil.which("tmux-cli")
    if tmux_cli_bin is None:
        local_shim = _local_tmux_cli_shim()
        if local_shim.is_file():
            tmux_cli_bin = str(local_shim)

    session = TmuxSession(tmux_cli_bin=tmux_cli_bin)
    try:
        session.launch("bash")
        yield session
    finally:
        session.kill()


# -----------------------------------------------------------------------------
# Sample Corpus Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sample_corpus_dir() -> Path:
    """Return path to sample corpus directory."""
    return Path(__file__).parent / "fixtures" / "sample_corpus"


@pytest.fixture(scope="session")
def expected_outputs_dir() -> Path:
    """Return path to expected outputs directory."""
    return Path(__file__).parent / "fixtures" / "expected_outputs"


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Provide a temporary output directory for test results."""
    output_dir = tmp_path / "uat_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def sample_pdf_files(sample_corpus_dir: Path) -> list[Path]:
    """Return list of sample PDF files in corpus."""
    return list(sample_corpus_dir.glob("*.pdf"))


@pytest.fixture
def sample_docx_files(sample_corpus_dir: Path) -> list[Path]:
    """Return list of sample DOCX files in corpus."""
    return list(sample_corpus_dir.glob("*.docx"))


@pytest.fixture
def sample_xlsx_files(sample_corpus_dir: Path) -> list[Path]:
    """Return list of sample XLSX files in corpus."""
    return list(sample_corpus_dir.glob("*.xlsx"))


# -----------------------------------------------------------------------------
# CLI Helper Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def cli_command() -> str:
    """Return the CLI command for data-extract."""
    return "data-extract"


@pytest.fixture
def activate_venv_command() -> str:
    """Return command to activate virtual environment."""
    return "source ./.venv/bin/activate"


# -----------------------------------------------------------------------------
# Journey State Fixture
# -----------------------------------------------------------------------------


@pytest.fixture
def journey_state() -> dict[str, object]:
    """Provide shared state for multi-step journey tests.

    Returns:
        dict: A dictionary for storing journey state across steps
    """
    return {
        "outputs": [],
        "screenshots": [],
        "errors": [],
        "metrics": {},
    }

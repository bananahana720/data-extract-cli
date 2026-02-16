"""Unit tests for run_quality_gates script."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module to test
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from scripts.run_quality_gates import QualityGateRunner


@pytest.mark.unit
def test_run_black_check_prefixes_env_path(monkeypatch):
    """Ensure tool subprocesses use the current Python environment PATH."""
    runner = QualityGateRunner(mode="pre-commit")
    expected_bin = str(Path(sys.executable).parent)

    monkeypatch.setenv("PATH", "/usr/bin")

    with patch("scripts.run_quality_gates.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        success, _ = runner.run_black_check()

        assert success is True
        assert mock_run.call_count == 1
        _, kwargs = mock_run.call_args
        env = kwargs["env"]
        assert env["PATH"] == f"{expected_bin}{os.pathsep}/usr/bin"

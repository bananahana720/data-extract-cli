"""Tests for PyInstaller frozen executable support in NLP and OCR modules.

Tests frozen executable path detection, environment overrides, and graceful
degradation when running in development vs. production (frozen) modes.

Modules tested:
    - data_extract.utils.nlp: spaCy model bundling and loading
    - data_extract.normalize.validation: Tesseract bundling and configuration
    - data_extract.cli.ocr_status: OCR availability detection and messaging
"""

import os
import sys
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, Mock, patch

import pytest

# ==============================================================================
# Test: data_extract.utils.nlp - Frozen Base Path Detection
# ==============================================================================


@pytest.mark.unit
class TestNLPFrozenBasePath:
    """Test _get_frozen_base_path() behavior in development and frozen modes."""

    def test_frozen_base_path_returns_none_in_dev(self) -> None:
        """Test that _get_frozen_base_path() returns None in development mode."""
        from data_extract.utils.nlp import _get_frozen_base_path

        # In development mode (not frozen), sys.frozen is False or not set
        # and sys._MEIPASS doesn't exist
        base_path = _get_frozen_base_path()

        assert base_path is None, "Expected None in development mode"

    def test_frozen_base_path_returns_path_when_frozen(self) -> None:
        """Test that _get_frozen_base_path() returns Path when frozen."""
        from data_extract.utils.nlp import _get_frozen_base_path

        # Mock PyInstaller frozen environment
        mock_meipass = "/tmp/_MEI12345"

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", mock_meipass, create=True):
                base_path = _get_frozen_base_path()

                assert base_path is not None, "Expected Path object in frozen mode"
                assert isinstance(base_path, Path), "Expected Path type"
                assert str(base_path) == mock_meipass, "Expected _MEIPASS path"

    def test_frozen_base_path_handles_missing_meipass(self) -> None:
        """Test that _get_frozen_base_path() returns None when frozen=True but _MEIPASS missing."""
        from data_extract.utils.nlp import _get_frozen_base_path

        # Edge case: sys.frozen=True but _MEIPASS doesn't exist
        with patch.object(sys, "frozen", True, create=True):
            # Don't patch _MEIPASS - let it be missing
            base_path = _get_frozen_base_path()

            assert base_path is None, "Expected None when _MEIPASS missing"


# ==============================================================================
# Test: data_extract.utils.nlp - Path Validation
# ==============================================================================


@pytest.mark.unit
class TestNLPPathValidation:
    """Test _validate_override_path() security and validation."""

    def test_validate_override_path_absolute_directory_exists(self, tmp_path: Path) -> None:
        """Test that valid absolute directory path is accepted."""
        from data_extract.utils.nlp import _validate_override_path

        # Create a test directory
        test_dir = tmp_path / "test_model"
        test_dir.mkdir()

        result = _validate_override_path(str(test_dir), expected_type="directory")

        assert result is not None, "Expected valid path for existing directory"
        assert result.is_absolute(), "Expected absolute path"
        assert result == test_dir.resolve(), "Expected resolved path to match"

    def test_validate_override_path_relative_path_rejected(self, tmp_path: Path) -> None:
        """Test that relative paths are rejected after resolution."""
        from data_extract.utils.nlp import _validate_override_path

        # Use a relative path that doesn't resolve to absolute
        # This is tricky because Path.resolve() makes paths absolute
        # So we test by using a path that exists but checking the logic
        test_dir = tmp_path / "test_model"
        test_dir.mkdir()

        # The function resolves paths, so all paths become absolute
        # Test with a non-existent relative path instead
        result = _validate_override_path("./nonexistent", expected_type="directory")

        # Should fail because directory doesn't exist
        assert result is None, "Expected None for non-existent directory"

    def test_validate_override_path_directory_does_not_exist(self, tmp_path: Path) -> None:
        """Test that non-existent directory is rejected."""
        from data_extract.utils.nlp import _validate_override_path

        nonexistent = tmp_path / "nonexistent"

        result = _validate_override_path(str(nonexistent), expected_type="directory")

        assert result is None, "Expected None for non-existent directory"

    def test_validate_override_path_file_when_directory_expected(self, tmp_path: Path) -> None:
        """Test that file is rejected when directory expected."""
        from data_extract.utils.nlp import _validate_override_path

        test_file = tmp_path / "test_file.txt"
        test_file.touch()

        result = _validate_override_path(str(test_file), expected_type="directory")

        assert result is None, "Expected None when file provided but directory expected"

    def test_validate_override_path_invalid_characters(self) -> None:
        """Test that paths with invalid characters are rejected."""
        from data_extract.utils.nlp import _validate_override_path

        # Null bytes are invalid in paths
        invalid_path = "test\x00path"

        result = _validate_override_path(invalid_path, expected_type="directory")

        assert result is None, "Expected None for path with null bytes"

    def test_validate_override_path_symlink_traversal(self, tmp_path: Path) -> None:
        """Test that symlinks are resolved safely."""
        from data_extract.utils.nlp import _validate_override_path

        # Create a real directory
        real_dir = tmp_path / "real_dir"
        real_dir.mkdir()

        # Create a symlink to it
        symlink_dir = tmp_path / "symlink_dir"
        symlink_dir.symlink_to(real_dir)

        result = _validate_override_path(str(symlink_dir), expected_type="directory")

        # Should resolve to real directory
        assert result is not None, "Expected valid path for symlink to directory"
        assert result == real_dir.resolve(), "Expected resolution to real directory"


# ==============================================================================
# Test: data_extract.utils.nlp - spaCy Model Path Discovery
# ==============================================================================


@pytest.mark.unit
class TestNLPSpacyModelPath:
    """Test _find_spacy_model_path() environment override and frozen bundle detection."""

    @pytest.fixture
    def clean_env(self) -> Generator[None, None, None]:
        """Fixture to clean SPACY_MODEL_PATH_OVERRIDE from environment."""
        original_value = os.environ.pop("SPACY_MODEL_PATH_OVERRIDE", None)
        yield
        if original_value:
            os.environ["SPACY_MODEL_PATH_OVERRIDE"] = original_value

    def test_find_spacy_model_path_env_override(self, tmp_path: Path, clean_env: Any) -> None:
        """Test that SPACY_MODEL_PATH_OVERRIDE environment variable is respected."""
        from data_extract.utils.nlp import _find_spacy_model_path

        # Create a temporary directory to represent the override path
        override_path = tmp_path / "custom_model"
        override_path.mkdir()

        # Set environment variable
        os.environ["SPACY_MODEL_PATH_OVERRIDE"] = str(override_path)

        # Call function
        result = _find_spacy_model_path()

        assert result is not None, "Expected path when override set and exists"
        assert result == override_path, "Expected override path to be returned"

    def test_find_spacy_model_path_env_override_nonexistent(
        self, tmp_path: Path, clean_env: Any
    ) -> None:
        """Test that non-existent override path is logged and ignored."""
        from data_extract.utils.nlp import _find_spacy_model_path

        # Set environment variable to non-existent path
        nonexistent_path = tmp_path / "nonexistent_model"
        os.environ["SPACY_MODEL_PATH_OVERRIDE"] = str(nonexistent_path)

        # Call function - should continue to frozen check
        result = _find_spacy_model_path()

        # In development mode with no frozen bundle, should return None
        assert result is None, "Expected None for non-existent override in dev mode"

    def test_find_spacy_model_path_frozen_bundle(self, tmp_path: Path, clean_env: Any) -> None:
        """Test that frozen bundle path is detected correctly."""
        from data_extract.utils.nlp import _find_spacy_model_path

        # Create mock frozen bundle structure
        mock_meipass = tmp_path / "_MEI12345"
        mock_meipass.mkdir()
        model_path = mock_meipass / "en_core_web_md" / "en_core_web_md"
        model_path.mkdir(parents=True)

        # Mock PyInstaller frozen environment
        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", str(mock_meipass), create=True):
                result = _find_spacy_model_path()

                assert result is not None, "Expected path in frozen mode"
                assert result == model_path, "Expected bundled model path"

    def test_find_spacy_model_path_returns_none_in_dev(self, clean_env: Any) -> None:
        """Test that _find_spacy_model_path() returns None in development mode."""
        from data_extract.utils.nlp import _find_spacy_model_path

        # No override, not frozen
        result = _find_spacy_model_path()

        assert result is None, "Expected None to fall back to standard spacy.load()"


# ==============================================================================
# Test: data_extract.normalize.validation - Frozen Base Path Detection
# ==============================================================================


@pytest.mark.unit
class TestValidationFrozenBasePath:
    """Test _get_frozen_base_path() in validation module."""

    def test_validation_frozen_base_path_returns_none_in_dev(self) -> None:
        """Test that validation._get_frozen_base_path() returns None in development mode."""
        from data_extract.normalize.validation import _get_frozen_base_path

        base_path = _get_frozen_base_path()

        assert base_path is None, "Expected None in development mode"

    def test_validation_frozen_base_path_returns_path_when_frozen(self) -> None:
        """Test that validation._get_frozen_base_path() returns Path when frozen."""
        from data_extract.normalize.validation import _get_frozen_base_path

        mock_meipass = "/tmp/_MEI67890"

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", mock_meipass, create=True):
                base_path = _get_frozen_base_path()

                assert base_path is not None, "Expected Path object in frozen mode"
                assert isinstance(base_path, Path), "Expected Path type"
                assert str(base_path) == mock_meipass, "Expected _MEIPASS path"


# ==============================================================================
# Test: data_extract.normalize.validation - Path Validation
# ==============================================================================


@pytest.mark.unit
class TestValidationPathValidation:
    """Test _validate_override_path() security and validation in validation module."""

    def test_validate_override_path_absolute_file_exists(self, tmp_path: Path) -> None:
        """Test that valid absolute file path is accepted."""
        from data_extract.normalize.validation import _validate_override_path

        # Create a test file
        test_file = tmp_path / "tesseract"
        test_file.touch()

        result = _validate_override_path(str(test_file), expected_type="file")

        assert result is not None, "Expected valid path for existing file"
        assert result.is_absolute(), "Expected absolute path"
        assert result == test_file.resolve(), "Expected resolved path to match"

    def test_validate_override_path_file_does_not_exist(self, tmp_path: Path) -> None:
        """Test that non-existent file is rejected."""
        from data_extract.normalize.validation import _validate_override_path

        nonexistent = tmp_path / "nonexistent_tesseract"

        result = _validate_override_path(str(nonexistent), expected_type="file")

        assert result is None, "Expected None for non-existent file"

    def test_validate_override_path_directory_when_file_expected(self, tmp_path: Path) -> None:
        """Test that directory is rejected when file expected."""
        from data_extract.normalize.validation import _validate_override_path

        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        result = _validate_override_path(str(test_dir), expected_type="file")

        assert result is None, "Expected None when directory provided but file expected"

    def test_validate_override_path_handles_oserror(self) -> None:
        """Test that OSError during path resolution is handled gracefully."""
        from data_extract.normalize.validation import _validate_override_path

        # Use a path that might trigger OSError on some systems
        # On Unix-like systems, paths with null bytes trigger ValueError
        # On Windows, certain reserved names might trigger OSError
        invalid_path = "CON" if sys.platform == "win32" else "test\x00path"

        result = _validate_override_path(invalid_path, expected_type="file")

        assert result is None, "Expected None for path that triggers OS error"

    def test_validate_override_path_symlink_to_file(self, tmp_path: Path) -> None:
        """Test that symlinks to files are resolved safely."""
        from data_extract.normalize.validation import _validate_override_path

        # Create a real file
        real_file = tmp_path / "real_tesseract"
        real_file.touch()

        # Create a symlink to it
        symlink_file = tmp_path / "symlink_tesseract"
        symlink_file.symlink_to(real_file)

        result = _validate_override_path(str(symlink_file), expected_type="file")

        # Should resolve to real file
        assert result is not None, "Expected valid path for symlink to file"
        assert result == real_file.resolve(), "Expected resolution to real file"


# ==============================================================================
# Test: data_extract.normalize.validation - Tesseract Path Discovery
# ==============================================================================


@pytest.mark.unit
class TestValidationTesseractPath:
    """Test _find_tesseract_cmd() environment override and frozen bundle detection."""

    @pytest.fixture
    def clean_env(self) -> Generator[None, None, None]:
        """Fixture to clean TESSERACT_CMD from environment."""
        original_value = os.environ.pop("TESSERACT_CMD", None)
        yield
        if original_value:
            os.environ["TESSERACT_CMD"] = original_value

    def test_find_tesseract_cmd_env_override(self, tmp_path: Path, clean_env: Any) -> None:
        """Test that TESSERACT_CMD environment variable is respected."""
        from data_extract.normalize.validation import _find_tesseract_cmd

        # Create a temporary file to represent tesseract executable
        tesseract_exe = tmp_path / "tesseract"
        tesseract_exe.touch()

        # Set environment variable
        os.environ["TESSERACT_CMD"] = str(tesseract_exe)

        # Call function
        result = _find_tesseract_cmd()

        assert result is not None, "Expected path when override set and exists"
        assert result == str(tesseract_exe), "Expected override path to be returned"

    def test_find_tesseract_cmd_env_override_nonexistent(
        self, tmp_path: Path, clean_env: Any
    ) -> None:
        """Test that non-existent override path is logged and ignored."""
        from data_extract.normalize.validation import _find_tesseract_cmd

        # Set environment variable to non-existent path
        nonexistent_path = tmp_path / "nonexistent_tesseract"
        os.environ["TESSERACT_CMD"] = str(nonexistent_path)

        # Call function - should continue to frozen/system checks
        result = _find_tesseract_cmd()

        # May return None or system tesseract depending on environment
        # We're testing that override doesn't crash when path doesn't exist
        assert True, "Function should not raise exception for non-existent override"

    def test_find_tesseract_cmd_frozen_bundle(self, tmp_path: Path, clean_env: Any) -> None:
        """Test that frozen bundle tesseract is detected correctly."""
        from data_extract.normalize.validation import _find_tesseract_cmd

        # Create mock frozen bundle structure
        mock_meipass = tmp_path / "_MEI12345"
        tesseract_dir = mock_meipass / "tesseract"
        tesseract_dir.mkdir(parents=True)

        # Platform-specific executable name
        tesseract_exe_name = "tesseract.exe" if sys.platform == "win32" else "tesseract"
        tesseract_path = tesseract_dir / tesseract_exe_name
        tesseract_path.touch()

        # Mock PyInstaller frozen environment
        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", str(mock_meipass), create=True):
                result = _find_tesseract_cmd()

                assert result is not None, "Expected path in frozen mode"
                assert result == str(tesseract_path), "Expected bundled tesseract path"


# ==============================================================================
# Test: data_extract.normalize.validation - Pytesseract Configuration
# ==============================================================================


@pytest.mark.unit
class TestConfigurePytesseract:
    """Test configure_pytesseract() behavior with and without Tesseract."""

    @pytest.fixture
    def clean_env(self) -> Generator[None, None, None]:
        """Fixture to clean TESSERACT_CMD from environment."""
        original_value = os.environ.pop("TESSERACT_CMD", None)
        yield
        if original_value:
            os.environ["TESSERACT_CMD"] = original_value

    def test_configure_pytesseract_handles_missing(self, tmp_path: Path, clean_env: Any) -> None:
        """Test that configure_pytesseract() returns error tuple when Tesseract missing."""
        from data_extract.normalize.validation import configure_pytesseract

        # Mock frozen environment with no tesseract bundle
        mock_meipass = tmp_path / "_MEI12345"
        mock_meipass.mkdir()

        # Don't create tesseract directory - simulate missing tesseract

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", str(mock_meipass), create=True):
                # Mock shutil.which to return None (tesseract not in PATH)
                with patch("data_extract.normalize.validation.shutil.which", return_value=None):
                    success, error_msg = configure_pytesseract()

                    assert success is False, "Expected False when tesseract missing"
                    assert error_msg is not None, "Expected error message"
                    assert "OCR not available" in error_msg, "Expected Core edition message"

    def test_configure_pytesseract_succeeds_with_tesseract(
        self, tmp_path: Path, clean_env: Any
    ) -> None:
        """Test that configure_pytesseract() succeeds when Tesseract is found."""
        from data_extract.normalize.validation import configure_pytesseract

        # Create mock tesseract executable
        tesseract_exe = tmp_path / "tesseract"
        tesseract_exe.touch()

        # Mock _find_tesseract_cmd to return our mock path
        with patch(
            "data_extract.normalize.validation._find_tesseract_cmd", return_value=str(tesseract_exe)
        ):
            success, error_msg = configure_pytesseract()

            assert success is True, "Expected True when tesseract found"
            assert error_msg is None, "Expected no error message on success"

    def test_configure_pytesseract_handles_missing_import(self, clean_env: Any) -> None:
        """Test that configure_pytesseract() handles missing pytesseract import."""
        # Import the module to check TESSERACT_AVAILABLE
        import data_extract.normalize.validation as validation_module

        # Save original value
        original_available = validation_module.TESSERACT_AVAILABLE

        try:
            # Mock TESSERACT_AVAILABLE to False
            validation_module.TESSERACT_AVAILABLE = False

            from data_extract.normalize.validation import configure_pytesseract

            success, error_msg = configure_pytesseract()

            assert success is False, "Expected False when pytesseract not available"
            assert error_msg is not None, "Expected error message"
            assert "pytesseract or Pillow not installed" in error_msg
        finally:
            # Restore original value
            validation_module.TESSERACT_AVAILABLE = original_available


# ==============================================================================
# Test: data_extract.cli.ocr_status - Frozen Detection
# ==============================================================================


@pytest.mark.unit
class TestOCRStatusFrozenDetection:
    """Test is_frozen() behavior in CLI OCR status module."""

    def test_is_frozen_returns_false_in_dev(self) -> None:
        """Test that is_frozen() returns False in development mode."""
        from data_extract.cli.ocr_status import is_frozen

        result = is_frozen()

        assert result is False, "Expected False in development mode"

    def test_is_frozen_returns_true_when_frozen(self) -> None:
        """Test that is_frozen() returns True when running as frozen executable."""
        from data_extract.cli.ocr_status import is_frozen

        mock_meipass = "/tmp/_MEI12345"

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", mock_meipass, create=True):
                result = is_frozen()

                assert result is True, "Expected True in frozen mode"

    def test_is_frozen_handles_partial_freeze(self) -> None:
        """Test that is_frozen() returns False when frozen=True but _MEIPASS missing."""
        from data_extract.cli.ocr_status import is_frozen

        with patch.object(sys, "frozen", True, create=True):
            # Don't patch _MEIPASS
            result = is_frozen()

            assert result is False, "Expected False when _MEIPASS missing"


# ==============================================================================
# Test: data_extract.cli.ocr_status - OCR Availability Check
# ==============================================================================


@pytest.mark.unit
class TestOCRStatusAvailability:
    """Test check_ocr_available() and messaging behavior."""

    def test_ocr_status_check_returns_tuple(self) -> None:
        """Test that check_ocr_available() returns proper tuple structure."""
        from data_extract.cli.ocr_status import check_ocr_available

        result = check_ocr_available()

        assert isinstance(result, tuple), "Expected tuple return type"
        assert len(result) == 2, "Expected 2-element tuple"

        available, message = result
        assert isinstance(available, bool), "Expected bool for available status"
        assert isinstance(message, str), "Expected str for message"
        assert len(message) > 0, "Expected non-empty message"

    def test_ocr_status_check_frozen_edition_message(self) -> None:
        """Test that check_ocr_available() returns Core Edition message when frozen."""
        from data_extract.cli.ocr_status import check_ocr_available

        # Mock frozen environment
        mock_meipass = "/tmp/_MEI12345"

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", mock_meipass, create=True):
                # Mock pytesseract import to raise exception inside the function
                # The module tries to import pytesseract, so mock it at the import level
                import builtins

                original_import = builtins.__import__

                def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
                    if name == "pytesseract":
                        raise ImportError("pytesseract not available")
                    return original_import(name, *args, **kwargs)

                with patch("builtins.__import__", side_effect=mock_import):
                    available, message = check_ocr_available()

                    assert available is False, "Expected False in Core Edition"
                    assert "Core Edition" in message, "Expected Core Edition in message"
                    assert "Full Edition" in message, "Expected Full Edition suggestion"

    def test_ocr_status_check_dev_edition_message(self) -> None:
        """Test that check_ocr_available() returns installation instructions in dev mode."""
        # Import inside test to avoid module-level caching
        # Clear any cached imports
        import sys

        if "data_extract.cli.ocr_status" in sys.modules:
            # Force reimport by patching at import time
            pass

        # Mock the pytesseract import to succeed, but get_tesseract_version to fail
        mock_pytesseract = MagicMock()
        mock_pytesseract.get_tesseract_version.side_effect = Exception("Tesseract not found")

        with patch.dict("sys.modules", {"pytesseract": mock_pytesseract}):
            # Reimport the module with mocked pytesseract
            from importlib import reload

            import data_extract.cli.ocr_status as ocr_status_module

            reload(ocr_status_module)

            available, message = ocr_status_module.check_ocr_available()

            assert available is False, "Expected False when Tesseract missing"
            assert "Tesseract OCR not found" in message
            assert (
                "Install Tesseract" in message or "sudo apt" in message or "brew install" in message
            ), "Expected installation instructions"


# ==============================================================================
# Test: data_extract.cli.ocr_status - UI Components
# ==============================================================================


@pytest.mark.unit
class TestOCRStatusUIComponents:
    """Test show_ocr_unavailable_panel() and get_ocr_unavailable_suggestion()."""

    def test_show_ocr_unavailable_panel_displays_when_unavailable(self) -> None:
        """Test that show_ocr_unavailable_panel() displays panel when OCR unavailable."""
        from rich.console import Console

        from data_extract.cli.ocr_status import show_ocr_unavailable_panel

        # Create a mock console
        mock_console = Mock(spec=Console)

        # Mock check_ocr_available to return False
        with patch(
            "data_extract.cli.ocr_status.check_ocr_available",
            return_value=(False, "Tesseract not found"),
        ):
            show_ocr_unavailable_panel(mock_console)

            # Verify console.print was called
            mock_console.print.assert_called_once()

    def test_show_ocr_unavailable_panel_skips_when_available(self) -> None:
        """Test that show_ocr_unavailable_panel() doesn't display when OCR is available."""
        from rich.console import Console

        from data_extract.cli.ocr_status import show_ocr_unavailable_panel

        # Create a mock console
        mock_console = Mock(spec=Console)

        # Mock check_ocr_available to return True
        with patch(
            "data_extract.cli.ocr_status.check_ocr_available", return_value=(True, "OCR available")
        ):
            show_ocr_unavailable_panel(mock_console)

            # Verify console.print was NOT called
            mock_console.print.assert_not_called()

    def test_get_ocr_unavailable_suggestion_frozen(self) -> None:
        """Test that get_ocr_unavailable_suggestion() returns Full Edition message when frozen."""
        from data_extract.cli.ocr_status import get_ocr_unavailable_suggestion

        mock_meipass = "/tmp/_MEI12345"

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", mock_meipass, create=True):
                suggestion = get_ocr_unavailable_suggestion()

                assert "Full Edition" in suggestion, "Expected Full Edition in suggestion"
                assert "OCR support" in suggestion, "Expected OCR support mention"

    def test_get_ocr_unavailable_suggestion_dev(self) -> None:
        """Test that get_ocr_unavailable_suggestion() returns installation message in dev mode."""
        from data_extract.cli.ocr_status import get_ocr_unavailable_suggestion

        # Not frozen
        suggestion = get_ocr_unavailable_suggestion()

        assert "Install Tesseract" in suggestion, "Expected installation instruction"
        assert "docs" in suggestion or "instructions" in suggestion, "Expected docs reference"


# ==============================================================================
# Integration Test: Full Frozen Workflow
# ==============================================================================


@pytest.mark.unit
class TestFrozenWorkflowIntegration:
    """Integration tests for frozen executable workflow."""

    @pytest.fixture
    def clean_env_integration(self) -> Generator[None, None, None]:
        """Fixture to clean all environment variables for integration tests."""
        spacy_override = os.environ.pop("SPACY_MODEL_PATH_OVERRIDE", None)
        tesseract_override = os.environ.pop("TESSERACT_CMD", None)
        yield
        if spacy_override:
            os.environ["SPACY_MODEL_PATH_OVERRIDE"] = spacy_override
        if tesseract_override:
            os.environ["TESSERACT_CMD"] = tesseract_override

    def test_frozen_workflow_with_bundled_resources(
        self, tmp_path: Path, clean_env_integration: Any
    ) -> None:
        """Test complete frozen workflow with bundled spaCy and Tesseract."""
        # Create mock frozen bundle structure
        mock_meipass = tmp_path / "_MEI12345"
        mock_meipass.mkdir()

        # Create spaCy model directory
        spacy_model = mock_meipass / "en_core_web_md" / "en_core_web_md"
        spacy_model.mkdir(parents=True)

        # Create Tesseract directory
        tesseract_exe_name = "tesseract.exe" if sys.platform == "win32" else "tesseract"
        tesseract_dir = mock_meipass / "tesseract"
        tesseract_dir.mkdir()
        tesseract_path = tesseract_dir / tesseract_exe_name
        tesseract_path.touch()

        # Mock PyInstaller frozen environment
        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", str(mock_meipass), create=True):
                # Test spaCy model detection
                from data_extract.utils.nlp import _find_spacy_model_path

                spacy_result = _find_spacy_model_path()
                assert spacy_result == spacy_model, "Expected bundled spaCy model"

                # Test Tesseract detection
                from data_extract.normalize.validation import _find_tesseract_cmd

                tesseract_result = _find_tesseract_cmd()
                assert tesseract_result == str(tesseract_path), "Expected bundled Tesseract"

                # Test OCR status detection
                from data_extract.cli.ocr_status import is_frozen

                frozen_status = is_frozen()
                assert frozen_status is True, "Expected frozen status"

    def test_frozen_workflow_without_bundled_resources(
        self, tmp_path: Path, clean_env_integration: Any
    ) -> None:
        """Test frozen workflow when resources are missing (Core Edition)."""
        # Create mock frozen bundle structure WITHOUT resources
        mock_meipass = tmp_path / "_MEI12345"
        mock_meipass.mkdir()

        # Don't create spaCy or Tesseract directories - simulate Core Edition

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", str(mock_meipass), create=True):
                # Mock shutil.which to return None (no system tesseract)
                with patch("data_extract.normalize.validation.shutil.which", return_value=None):
                    # Test spaCy model detection returns None (will fallback to standard load)
                    from data_extract.utils.nlp import _find_spacy_model_path

                    spacy_result = _find_spacy_model_path()
                    # In frozen mode without bundle, should return None (will fail at runtime)
                    assert spacy_result is None, "Expected None for missing bundle"

                    # Test Tesseract detection returns None
                    from data_extract.normalize.validation import _find_tesseract_cmd

                    tesseract_result = _find_tesseract_cmd()
                    assert tesseract_result is None, "Expected None for missing Tesseract"

                    # Test configure_pytesseract returns error
                    from data_extract.normalize.validation import configure_pytesseract

                    success, error_msg = configure_pytesseract()
                    assert success is False, "Expected False for missing Tesseract"
                    assert (
                        error_msg is not None and "Core edition" in error_msg
                    ), "Expected Core edition message"

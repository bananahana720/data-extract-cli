"""
Epic 5 CLI Test Fixtures.

This module provides shared test infrastructure for Epic 5 CLI stories:
- Story 5-1: Command Structure (Typer migration)
- Story 5-2: Configuration Management
- Story 5-3: Progress Indicators
- Story 5-6: Error Handling & Recovery

Fixtures follow BMAD patterns:
- Pure function -> fixture -> composition
- Auto-cleanup via context managers
- Factory functions with seeded randomness
"""

from __future__ import annotations

import json
import os
import random
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Generator, Optional

import pytest
import yaml

# ==============================================================================
# TIER 1: Core Fixtures (Block Multiple Tests)
# ==============================================================================


# ------------------------------------------------------------------------------
# 1.1 Typer CLI Runner
# ------------------------------------------------------------------------------


@pytest.fixture
def typer_cli_runner():
    """
    Provide Typer-native test runner for CLI testing.

    Typer's CliRunner wraps Click's but provides better integration
    with Typer-specific features like type hints and auto-completion.

    Returns:
        TyperCliRunner instance configured for testing

    Usage:
        def test_command(typer_cli_runner):
            from src.data_extract.app import app
            result = typer_cli_runner.invoke(app, ["--help"])
            assert result.exit_code == 0

    Note:
        This fixture will return Click's CliRunner until Typer migration
        is complete (AC-5.1-2). After migration, it returns Typer's runner.
    """
    try:
        from typer.testing import CliRunner as TyperCliRunner

        # Try with mix_stderr if supported
        try:
            return TyperCliRunner(mix_stderr=False)
        except TypeError:
            return TyperCliRunner()
    except ImportError:
        # Fallback to Click runner until Typer is installed
        from click.testing import CliRunner

        try:
            return CliRunner(mix_stderr=False)
        except TypeError:
            return CliRunner()


@pytest.fixture
def isolated_cli_runner(tmp_path: Path) -> Generator[Any, None, None]:
    """
    Provide isolated CLI runner with temporary filesystem.

    Creates isolated environment for tests that need:
    - Clean filesystem state
    - No interference from user configs
    - Deterministic working directory

    Args:
        tmp_path: pytest built-in temporary directory

    Yields:
        CliRunner with isolated filesystem context
    """
    original_cwd = os.getcwd()
    original_home = os.environ.get("HOME")

    # Create isolated structure
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    try:
        os.chdir(work_dir)
        os.environ["HOME"] = str(fake_home)

        # Use appropriate runner
        try:
            from typer.testing import CliRunner as TyperCliRunner

            try:
                yield TyperCliRunner(mix_stderr=False)
            except TypeError:
                yield TyperCliRunner()
        except ImportError:
            from click.testing import CliRunner

            try:
                yield CliRunner(mix_stderr=False)
            except TypeError:
                yield CliRunner()
    finally:
        os.chdir(original_cwd)
        if original_home:
            os.environ["HOME"] = original_home
        elif "HOME" in os.environ:
            del os.environ["HOME"]


# ------------------------------------------------------------------------------
# 1.2 Environment Variable Controller
# ------------------------------------------------------------------------------


class EnvVarsController:
    """Controller for DATA_EXTRACT_* environment variables.

    Provides safe manipulation of environment variables with
    automatic cleanup in tests.
    """

    PREFIX = "DATA_EXTRACT_"

    def __init__(self):
        self._original_values: dict[str, Optional[str]] = {}
        self._managed_vars: set[str] = set()

    def set(self, name: str, value: str) -> None:
        """Set an environment variable, storing original for cleanup."""
        full_name = f"{self.PREFIX}{name}" if not name.startswith(self.PREFIX) else name
        if full_name not in self._original_values:
            self._original_values[full_name] = os.environ.get(full_name)
        os.environ[full_name] = value
        self._managed_vars.add(full_name)

    def unset(self, name: str) -> None:
        """Unset an environment variable."""
        full_name = f"{self.PREFIX}{name}" if not name.startswith(self.PREFIX) else name
        if full_name not in self._original_values:
            self._original_values[full_name] = os.environ.get(full_name)
        if full_name in os.environ:
            del os.environ[full_name]
        self._managed_vars.add(full_name)

    def set_no_color(self, enabled: bool = True) -> None:
        """Set or unset NO_COLOR for accessibility testing."""
        if enabled:
            os.environ["NO_COLOR"] = "1"
        elif "NO_COLOR" in os.environ:
            del os.environ["NO_COLOR"]

    def reset(self) -> None:
        """Reset all managed variables to original values."""
        for var_name in self._managed_vars:
            original = self._original_values.get(var_name)
            if original is None:
                if var_name in os.environ:
                    del os.environ[var_name]
            else:
                os.environ[var_name] = original
        self._managed_vars.clear()
        self._original_values.clear()


@pytest.fixture
def env_vars_fixture() -> Generator[EnvVarsController, None, None]:
    """
    Provide environment variable controller with automatic cleanup.

    Manages DATA_EXTRACT_* variables and NO_COLOR for testing
    configuration cascade and accessibility.

    Yields:
        EnvVarsController instance

    Usage:
        def test_env_override(env_vars_fixture):
            env_vars_fixture.set("OUTPUT_DIR", "/tmp/test")
            env_vars_fixture.set("CHUNK_SIZE", "500")
            # Run test...
    """
    controller = EnvVarsController()
    try:
        yield controller
    finally:
        controller.reset()


# ------------------------------------------------------------------------------
# 1.3 Mock Home Directory Structure
# ------------------------------------------------------------------------------


@dataclass
class MockHomeStructure:
    """Structure representing isolated home directory for testing.

    Attributes:
        root: Base directory (mocked HOME)
        config_dir: ~/.config/data-extract/
        data_extract_dir: ~/.data-extract/
        presets_dir: ~/.data-extract/presets/
        session_dir: .data-extract-session/ (in working directory)
    """

    root: Path
    config_dir: Path = field(init=False)
    data_extract_dir: Path = field(init=False)
    presets_dir: Path = field(init=False)
    session_dir: Path = field(init=False)
    work_dir: Path = field(init=False)

    def __post_init__(self):
        self.config_dir = self.root / ".config" / "data-extract"
        self.data_extract_dir = self.root / ".data-extract"
        self.presets_dir = self.data_extract_dir / "presets"
        self.work_dir = self.root / "work"
        self.session_dir = self.work_dir / ".data-extract-session"

        # Create directory structure
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def create_user_config(self, config_dict: dict) -> Path:
        """Create user config file with given content at ~/.data-extract/config.yaml."""
        # Use data_extract_dir instead of config_dir to match USER_CONFIG_PATH
        config_file = self.data_extract_dir / "config.yaml"
        config_file.write_text(yaml.dump(config_dict))
        return config_file

    def create_project_config(self, config_dict: dict) -> Path:
        """Create project-level config in work directory."""
        config_file = self.work_dir / ".data-extract.yaml"
        config_file.write_text(yaml.dump(config_dict))
        return config_file

    def create_preset(self, name: str, config_dict: dict) -> Path:
        """Create a preset file in presets directory."""
        preset_file = self.presets_dir / f"{name}.yaml"
        preset_file.write_text(yaml.dump(config_dict))
        return preset_file

    def create_session_state(self, session_dict: dict) -> Path:
        """Create session state file for resume testing."""
        self.session_dir.mkdir(exist_ok=True)
        session_file = self.session_dir / "session.json"
        session_file.write_text(json.dumps(session_dict, indent=2))
        return session_file

    def is_first_run(self) -> bool:
        """Check if this simulates a first-run state (no config exists)."""
        user_config = self.config_dir / "config.yaml"
        project_config = self.work_dir / ".data-extract.yaml"
        return not user_config.exists() and not project_config.exists()


@pytest.fixture
def mock_home_directory(tmp_path: Path, monkeypatch) -> Generator[MockHomeStructure, None, None]:
    """
    Provide isolated home directory structure for CLI testing.

    Creates mock ~/.data-extract/, ~/.config/data-extract/, and
    .data-extract-session/ directories with helper methods for
    populating config files.

    Automatically patches Path.cwd() and Path.home() to use the mock directories.

    Args:
        tmp_path: pytest built-in temporary directory
        monkeypatch: pytest monkeypatch fixture

    Yields:
        MockHomeStructure with paths and helper methods

    Usage:
        def test_user_config(mock_home_directory):
            mock_home_directory.create_user_config({"semantic": {"cache_enabled": True}})
            # Run CLI test - will automatically use mocked paths
    """
    import os

    structure = MockHomeStructure(root=tmp_path)

    # Patch Path.home() to return mock home
    monkeypatch.setattr(Path, "home", lambda: structure.root)

    # Patch Path.cwd() to return mock work directory
    monkeypatch.setattr(Path, "cwd", lambda: structure.work_dir)

    # Also patch os.getcwd() for consistency
    monkeypatch.setattr(os, "getcwd", lambda: str(structure.work_dir))

    yield structure
    # Cleanup handled by tmp_path and monkeypatch


# ------------------------------------------------------------------------------
# 1.4 Session State Builder (Story 5-6)
# ------------------------------------------------------------------------------


@dataclass
class SessionStateBuilder:
    """Builder for session state fixtures.

    Creates realistic session state JSON for testing:
    - Resume functionality
    - Retry operations
    - Session cleanup
    """

    session_dir: Path
    session_id: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%dT%H-%M-%S"))

    def build_in_progress(
        self,
        source_directory: str,
        total_files: int,
        processed_files: list[dict[str, str]],
        failed_files: Optional[list[dict[str, str]]] = None,
        configuration: Optional[dict] = None,
    ) -> Path:
        """Create an in-progress session state file.

        Args:
            source_directory: Path to source documents
            total_files: Total file count
            processed_files: List of {path, hash, output} dicts
            failed_files: List of {path, error_type, error_message} dicts
            configuration: CLI configuration used

        Returns:
            Path to created session file
        """
        self.session_dir.mkdir(parents=True, exist_ok=True)

        state = {
            "schema_version": "1.0",
            "session_id": self.session_id,
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "in_progress",
            "source_directory": source_directory,
            "output_directory": str(self.session_dir.parent / "output"),
            "configuration": configuration or {"format": "json", "chunk_size": 500},
            "statistics": {
                "total_files": total_files,
                "processed_count": len(processed_files),
                "failed_count": len(failed_files or []),
                "skipped_count": 0,
            },
            "processed_files": processed_files,
            "failed_files": failed_files or [],
        }

        session_file = self.session_dir / f"session-{self.session_id}.json"
        session_file.write_text(json.dumps(state, indent=2))
        return session_file

    def build_interrupted(self, **kwargs) -> Path:
        """Create an interrupted session state for resume testing."""
        path = self.build_in_progress(**kwargs)
        # Modify status to interrupted
        state = json.loads(path.read_text())
        state["status"] = "interrupted"
        path.write_text(json.dumps(state, indent=2))
        return path

    def cleanup(self) -> None:
        """Remove session directory."""
        if self.session_dir.exists():
            shutil.rmtree(self.session_dir)


@pytest.fixture
def session_state_fixture(tmp_path: Path) -> Generator[SessionStateBuilder, None, None]:
    """
    Provide session state builder for error recovery testing.

    Creates .data-extract-session/ with realistic state files
    for testing --resume and retry functionality.

    Returns:
        SessionStateBuilder instance

    Usage:
        def test_resume(session_state_fixture, typer_cli_runner):
            session = session_state_fixture.build_interrupted(
                source_directory="/docs",
                total_files=50,
                processed_files=[{"path": "file1.pdf", "hash": "abc123", "output": "out/file1.json"}],
                failed_files=[{"path": "bad.pdf", "error_type": "extraction", "error_message": "Corrupted"}],
            )
            result = runner.invoke(app, ["process", "--resume"])
            assert "Resuming session" in result.output
    """
    session_dir = tmp_path / ".data-extract-session"
    builder = SessionStateBuilder(session_dir=session_dir)
    yield builder
    builder.cleanup()


# ------------------------------------------------------------------------------
# 1.5 Mock Rich Console (Story 5-3)
# ------------------------------------------------------------------------------


class MockConsole:
    """Mock Rich Console for capturing formatted output.

    Captures both raw output and ANSI-formatted output for
    testing progress bars, panels, and colored text.
    """

    def __init__(self, width: int = 120, force_terminal: bool = True, no_color: bool = False):
        self._output = StringIO()
        self._operations: list[dict] = []
        self._width = width
        self._no_color = no_color

        # Lazy import Rich to avoid hard dependency
        try:
            from rich.console import Console

            self._console = Console(
                file=self._output,
                width=width,
                force_terminal=force_terminal,
                no_color=no_color,
                record=True,
            )
        except ImportError:
            self._console = None

    @property
    def console(self):
        """Get the underlying Rich Console."""
        return self._console

    @property
    def output(self) -> str:
        """Get captured output as string."""
        return self._output.getvalue()

    @property
    def exported_html(self) -> str:
        """Get output as HTML for detailed inspection."""
        if self._console:
            return self._console.export_html()
        return ""

    @property
    def exported_text(self) -> str:
        """Get output as plain text (no ANSI codes)."""
        if self._console:
            return self._console.export_text()
        return self.output

    def print(self, *args, **kwargs) -> None:
        """Proxy print to console, tracking operation."""
        self._operations.append({"type": "print", "args": args, "kwargs": kwargs})
        if self._console:
            self._console.print(*args, **kwargs)

    def status(self, *args, **kwargs):
        """Proxy status context manager."""
        self._operations.append({"type": "status", "args": args, "kwargs": kwargs})
        if self._console:
            return self._console.status(*args, **kwargs)
        return None

    def clear(self) -> None:
        """Clear captured output."""
        self._output = StringIO()
        self._operations.clear()
        if self._console:
            try:
                from rich.console import Console

                self._console = Console(
                    file=self._output,
                    width=self._width,
                    force_terminal=True,
                    no_color=self._no_color,
                    record=True,
                )
            except ImportError:
                pass


@pytest.fixture
def mock_console() -> MockConsole:
    """
    Provide mock Rich Console for output capture.

    Captures all Rich formatting for testing progress bars,
    panels, tables, and colored output.

    Returns:
        MockConsole instance with assertion helpers

    Usage:
        def test_progress_display(mock_console, monkeypatch):
            # Patch the module's console
            import src.data_extract.cli.components.progress as progress_mod
            monkeypatch.setattr(progress_mod, "console", mock_console.console)

            # Run operation
            display_progress(files)

            # Assert output
            assert "100%" in mock_console.output
    """
    return MockConsole()


@pytest.fixture
def no_color_console() -> MockConsole:
    """
    Provide console with NO_COLOR mode for accessibility testing.

    Returns:
        MockConsole configured with no_color=True
    """
    return MockConsole(no_color=True)


# ==============================================================================
# TIER 2: Factory Functions
# ==============================================================================


class ConfigFactory:
    """Factory for generating test configuration objects.

    Uses seeded random for deterministic but varied test data.
    """

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def semantic_config(
        self,
        max_features: Optional[int] = None,
        ngram_range: Optional[tuple[int, int]] = None,
        **overrides,
    ) -> dict[str, Any]:
        """Generate semantic analysis configuration."""
        config = {
            "tfidf_max_features": max_features or self._rng.randint(1000, 10000),
            "tfidf_ngram_range": ngram_range or (1, self._rng.randint(1, 3)),
            "tfidf_min_df": self._rng.randint(1, 5),
            "tfidf_max_df": round(self._rng.uniform(0.8, 0.99), 2),
            "similarity_duplicate_threshold": round(self._rng.uniform(0.85, 0.99), 2),
            "similarity_related_threshold": round(self._rng.uniform(0.6, 0.8), 2),
            "lsa_n_components": self._rng.randint(50, 200),
            "quality_min_score": round(self._rng.uniform(0.2, 0.5), 2),
            "cache_enabled": self._rng.choice([True, False]),
        }
        config.update(overrides)
        return config

    def preset_config(self, preset_type: str = "default") -> dict[str, Any]:
        """Generate preset configuration by type.

        Args:
            preset_type: One of 'audit-standard', 'rag-optimized', 'quick-scan'
        """
        presets = {
            "audit-standard": {
                "semantic": {
                    "tfidf_max_features": 5000,
                    "tfidf_ngram_range": [1, 2],
                    "quality_min_score": 0.3,
                    "cache_enabled": True,
                }
            },
            "rag-optimized": {
                "semantic": {
                    "tfidf_max_features": 3000,
                    "tfidf_ngram_range": [1, 1],
                    "quality_min_score": 0.5,
                },
                "chunk": {
                    "max_tokens": 256,
                    "overlap": 64,
                },
            },
            "quick-scan": {
                "semantic": {
                    "tfidf_max_features": 1000,
                    "cache_enabled": False,
                },
                "quality": {
                    "skip_readability": True,
                },
            },
        }
        return presets.get(preset_type, presets["audit-standard"])

    def session_state(
        self,
        total_files: int = 50,
        processed_ratio: float = 0.6,
        failed_ratio: float = 0.1,
    ) -> dict[str, Any]:
        """Generate session state dictionary."""
        processed_count = int(total_files * processed_ratio)
        failed_count = int(total_files * failed_ratio)

        processed_files = [
            {
                "path": f"doc_{i}.pdf",
                "hash": f"sha256:{i:064d}",
                "output": f"out/doc_{i}.json",
            }
            for i in range(processed_count)
        ]

        failed_files = [
            {
                "path": f"failed_{i}.pdf",
                "error_type": self._rng.choice(["extraction", "validation", "timeout"]),
                "error_message": f"Mock error {i}",
                "timestamp": "2025-11-25T12:00:00Z",
            }
            for i in range(failed_count)
        ]

        return {
            "total_files": total_files,
            "processed_files": processed_files,
            "failed_files": failed_files,
            "statistics": {
                "total_files": total_files,
                "processed_count": processed_count,
                "failed_count": failed_count,
            },
        }


@pytest.fixture
def config_factory() -> ConfigFactory:
    """Provide ConfigFactory for generating test configurations."""
    return ConfigFactory(seed=42)


class DocumentFactory:
    """Factory for generating test documents with realistic content."""

    TECHNICAL_TERMS = [
        "algorithm",
        "processing",
        "extraction",
        "pipeline",
        "module",
        "architecture",
    ]
    BUSINESS_TERMS = [
        "revenue",
        "compliance",
        "audit",
        "risk",
        "control",
        "assessment",
    ]

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def text_file(
        self, tmp_path: Path, content_type: str = "technical", word_count: int = 100
    ) -> Path:
        """Generate a text file with specified content type."""
        terms = self.TECHNICAL_TERMS if content_type == "technical" else self.BUSINESS_TERMS

        words = []
        for _ in range(word_count):
            if self._rng.random() < 0.3:  # 30% chance of domain term
                words.append(self._rng.choice(terms))
            else:
                words.append(f"word{self._rng.randint(1, 100)}")

        content = " ".join(words)
        file_path = tmp_path / f"{content_type}_{self._rng.randint(1000, 9999)}.txt"
        file_path.write_text(content)
        return file_path

    def batch_files(
        self, tmp_path: Path, count: int = 10, include_errors: bool = False
    ) -> list[Path]:
        """Generate batch of test files, optionally including error-inducing files."""
        files = []
        for i in range(count):
            content_type = self._rng.choice(["technical", "business"])
            files.append(self.text_file(tmp_path, content_type))

        if include_errors:
            # Add a corrupted file
            corrupted = tmp_path / "corrupted.pdf"
            corrupted.write_bytes(b"%PDF-1.4\nCorrupted")
            files.append(corrupted)

        return files


@pytest.fixture
def document_factory() -> DocumentFactory:
    """Provide DocumentFactory for generating test documents."""
    return DocumentFactory(seed=42)


# ==============================================================================
# TIER 3: Story-Specific Supporting Fixtures
# ==============================================================================


# ------------------------------------------------------------------------------
# Story 5-1: Wizard and Learning Mode Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture
def wizard_responses_fixture() -> dict[str, list[str]]:
    """
    Provide input sequences for first-run wizard testing.

    Returns dict of scenario_name -> list of inputs (simulating user typing).
    """
    return {
        "enterprise_default": ["1", "n"],  # Select Enterprise mode, skip tutorial
        "enterprise_tutorial": ["1", "y"],  # Select Enterprise, run tutorial
        "hobbyist_default": ["2", "n"],  # Select Hobbyist mode, skip tutorial
        "hobbyist_tutorial": ["2", "y"],  # Select Hobbyist, run tutorial
        "quick_exit": ["q"],  # Quit immediately
        "invalid_then_valid": ["x", "invalid", "1", "n"],  # Invalid inputs first
    }


@pytest.fixture
def learning_mode_capture() -> dict[str, list[str]]:
    """
    Provide expected learning mode output patterns for validation.

    Returns dict of pattern_name -> expected substrings.
    """
    return {
        "step_indicator": ["[Step", "/"],  # e.g., "[Step 1/4]"
        "learn_tip": ["[LEARN]"],
        "continue_prompt": ["[Continue]", "Press Enter"],
        "insights_summary": ["Insights", "Summary"],
    }


# ------------------------------------------------------------------------------
# Story 5-2: Configuration Cascade Fixtures
# ------------------------------------------------------------------------------


@dataclass
class ConfigCascadeSetup:
    """Setup for 6-layer configuration cascade testing.

    Precedence (highest to lowest):
    1. CLI flags
    2. Environment variables (DATA_EXTRACT_*)
    3. Project config (.data-extract.yaml in cwd)
    4. User config (~/.config/data-extract/config.yaml)
    5. Preset config (~/.data-extract/presets/*.yaml)
    6. Defaults (hardcoded)
    """

    tmp_path: Path
    home_structure: MockHomeStructure
    env_controller: EnvVarsController

    # Tracked config files
    project_config_path: Optional[Path] = None
    user_config_path: Optional[Path] = None
    preset_config_path: Optional[Path] = None

    def set_env_vars(self, overrides: dict[str, str]) -> None:
        """Set environment variable overrides."""
        for key, value in overrides.items():
            self.env_controller.set(key, value)

    def set_project_config(self, config: dict[str, Any]) -> Path:
        """Create project-level config in working directory."""
        self.project_config_path = self.home_structure.create_project_config(config)
        return self.project_config_path

    def set_user_config(self, config: dict[str, Any]) -> Path:
        """Create user-level config."""
        self.user_config_path = self.home_structure.create_user_config(config)
        return self.user_config_path

    def set_preset(self, name: str, config: dict[str, Any]) -> Path:
        """Create a preset configuration."""
        self.preset_config_path = self.home_structure.create_preset(name, config)
        return self.preset_config_path

    def get_expected_precedence(self) -> list[str]:
        """Return expected precedence order for debugging."""
        return [
            "1. CLI flags (--option=value)",
            "2. Environment (DATA_EXTRACT_OPTION)",
            "3. Project (.data-extract.yaml)",
            "4. User (~/.config/data-extract/config.yaml)",
            "5. Preset (~/.data-extract/presets/*.yaml)",
            "6. Defaults (hardcoded)",
        ]


@pytest.fixture
def six_layer_cascade_fixture(
    tmp_path: Path,
    mock_home_directory: MockHomeStructure,
    env_vars_fixture: EnvVarsController,
) -> ConfigCascadeSetup:
    """
    Provide full 6-layer configuration cascade setup.

    Creates isolated environment with all configuration layers
    available for testing precedence and merging.

    Returns:
        ConfigCascadeSetup with methods to configure each layer

    Usage:
        def test_cascade_precedence(six_layer_cascade_fixture, monkeypatch):
            cascade = six_layer_cascade_fixture

            # Set lower layers
            cascade.set_user_config({"semantic": {"tfidf_max_features": 3000}})
            cascade.set_project_config({"semantic": {"tfidf_max_features": 5000}})
            cascade.set_env_vars({"TFIDF_MAX_FEATURES": "7000"})

            # CLI flag should win (passed to invoke)
            result = runner.invoke(app, ["config", "show", "--tfidf-max-features", "10000"])
            assert "10000" in result.output
    """
    return ConfigCascadeSetup(
        tmp_path=tmp_path,
        home_structure=mock_home_directory,
        env_controller=env_vars_fixture,
    )


# ------------------------------------------------------------------------------
# Story 5-6: Error Corpus Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture
def error_corpus_fixture(tmp_path: Path) -> dict[str, Path]:
    """
    Create files guaranteed to fail extraction for error testing.

    Returns dict of error_type -> file_path with:
    - corrupted_pdf: Invalid PDF structure
    - empty_docx: Valid DOCX with no content
    - malformed_xlsx: Truncated Excel file
    - unsupported_format: Unknown extension
    """
    corpus = {}

    # Corrupted PDF
    corrupted_pdf = tmp_path / "corrupted.pdf"
    corrupted_pdf.write_bytes(b"%PDF-1.4\n" + b"\x00" * 100)
    corpus["corrupted_pdf"] = corrupted_pdf

    # Empty DOCX (valid structure, no content)
    try:
        from docx import Document

        empty_docx = tmp_path / "empty.docx"
        doc = Document()
        doc.save(empty_docx)
        corpus["empty_docx"] = empty_docx
    except ImportError:
        # python-docx not installed
        pass

    # Malformed XLSX (truncated ZIP)
    malformed_xlsx = tmp_path / "malformed.xlsx"
    malformed_xlsx.write_bytes(b"PK\x03\x04" + b"\x00" * 50)
    corpus["malformed_xlsx"] = malformed_xlsx

    # Unsupported format
    unsupported = tmp_path / "file.xyz"
    unsupported.write_text("Unknown format content")
    corpus["unsupported_format"] = unsupported

    return corpus


# ------------------------------------------------------------------------------
# Pydantic Validation Test Corpus
# ------------------------------------------------------------------------------


@pytest.fixture
def pydantic_validation_corpus() -> list[dict]:
    """
    Provide invalid configuration values for Pydantic validation testing.

    Returns list of dicts with:
    - field: Configuration field name
    - invalid_value: Value that should fail validation
    - error_type: Expected error type
    - error_message_contains: Substring expected in error
    """
    return [
        {
            "field": "tfidf_max_features",
            "invalid_value": -100,
            "error_type": "ge",
            "error_message_contains": "greater than",
        },
        {
            "field": "tfidf_max_features",
            "invalid_value": "not_a_number",
            "error_type": "type",
            "error_message_contains": "int",
        },
        {
            "field": "tfidf_max_df",
            "invalid_value": 1.5,
            "error_type": "le",
            "error_message_contains": "less than",
        },
        {
            "field": "tfidf_ngram_range",
            "invalid_value": (3, 1),
            "error_type": "value",
            "error_message_contains": "min must be <= max",
        },
        {
            "field": "similarity_threshold",
            "invalid_value": 2.0,
            "error_type": "le",
            "error_message_contains": "at most 1.0",
        },
        {
            "field": "cache_max_size_mb",
            "invalid_value": 0,
            "error_type": "gt",
            "error_message_contains": "greater than 0",
        },
    ]


# ==============================================================================
# Auto-Cleanup Fixtures (autouse patterns)
# ==============================================================================


@pytest.fixture(autouse=False)  # Not autouse by default - import in specific conftest
def cleanup_session_directories(tmp_path: Path):
    """
    Cleanup .data-extract-session directories after CLI tests.

    Runs after each test to ensure no session state leaks between tests.

    Note: Import and mark autouse=True in tests/unit/test_cli/conftest.py
    """
    yield

    # Cleanup patterns
    session_patterns = [
        tmp_path / ".data-extract-session",
        Path.cwd() / ".data-extract-session",
    ]

    for pattern in session_patterns:
        if pattern.exists() and pattern.is_dir():
            try:
                shutil.rmtree(pattern)
            except Exception:
                pass  # Best effort

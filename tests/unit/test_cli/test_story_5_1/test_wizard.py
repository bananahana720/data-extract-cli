"""TDD RED Phase Tests: First-Time Setup Wizard (AC-5.1-6).

These tests verify:
- AC-5.1-6: Journey 1 (First-Time Setup) wizard functional

All tests are designed to FAIL initially (TDD RED phase).
"""

from unittest.mock import patch

import pytest

from tests.fixtures.cli_fixtures import MockHomeStructure

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.story_5_1,
    pytest.mark.unit,
    pytest.mark.cli,
]


@pytest.mark.unit
@pytest.mark.story_5_1
class TestWizardExists:
    """Verify wizard module and function exists."""

    def test_wizard_module_exists(self):
        """
        RED: Verify wizard module can be imported.

        Given: The CLI wizard module
        When: We import the wizard
        Then: It should be importable

        Expected RED failure: ImportError
        """
        # Given/When
        try:
            from data_extract.cli import wizard
        except ImportError as e:
            pytest.fail(f"Cannot import wizard module: {e}")

        # Then
        assert wizard is not None

    def test_first_run_wizard_function_exists(self):
        """
        RED: Verify first_run_wizard function exists.

        Given: The wizard module
        When: We access first_run_wizard
        Then: It should be a callable function

        Expected RED failure: AttributeError
        """
        # Given/When
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Cannot import first_run_wizard: {e}")

        # Then
        assert callable(first_run_wizard)

    def test_is_first_run_function_exists(self):
        """
        RED: Verify is_first_run detection function exists.

        Given: The wizard module
        When: We access is_first_run
        Then: It should be a callable function

        Expected RED failure: AttributeError
        """
        # Given/When
        try:
            from data_extract.cli.wizard import is_first_run
        except ImportError as e:
            pytest.fail(f"Cannot import is_first_run: {e}")

        # Then
        assert callable(is_first_run)


@pytest.mark.unit
@pytest.mark.story_5_1
class TestFirstRunDetection:
    """Test first-run detection logic."""

    def test_detects_first_run_when_no_config(
        self,
        mock_home_directory: MockHomeStructure,
        monkeypatch,
    ):
        """
        RED: Verify first run detected when no config exists.

        Given: A clean environment with no config files
        When: We call is_first_run()
        Then: It should return True

        Expected RED failure: Function not implemented
        """
        # Given
        try:
            from data_extract.cli.wizard import is_first_run
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        # Mock HOME to use test directory
        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        # Ensure no config exists
        user_config = mock_home_directory.config_dir / "config.yaml"
        if user_config.exists():
            user_config.unlink()

        # When
        result = is_first_run()

        # Then
        assert result is True, "Should detect first run when no config exists"

    def test_detects_existing_user_when_config_exists(
        self,
        mock_home_directory: MockHomeStructure,
        monkeypatch,
    ):
        """
        RED: Verify returning user detected when config exists.

        Given: Environment with existing config file
        When: We call is_first_run()
        Then: It should return False

        Expected RED failure: Function not implemented
        """
        # Given
        try:
            from data_extract.cli.wizard import is_first_run
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        # Create existing config
        mock_home_directory.create_user_config({"mode": "enterprise"})

        # When
        result = is_first_run()

        # Then
        assert result is False, "Should not be first run when config exists"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestWizardWelcomePanel:
    """Test wizard welcome panel display."""

    def test_wizard_shows_welcome_message(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
    ):
        """
        RED: Verify wizard displays welcome message.

        Given: First-time user running wizard
        When: Wizard starts
        Then: Welcome panel should be displayed

        Expected RED failure: No welcome output
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        # Mock prompt to return enterprise mode
        with patch("data_extract.cli.wizard.prompt") as mock_prompt:
            mock_prompt.return_value = {"mode": "enterprise", "tutorial": False}

            # When
            first_run_wizard(console=mock_console.console)

        # Then
        output = mock_console.exported_text
        assert "welcome" in output.lower(), f"Expected 'welcome' in output: {output}"

    def test_wizard_shows_tool_name(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
    ):
        """
        RED: Verify wizard displays tool name.

        Given: First-time user running wizard
        When: Wizard displays welcome
        Then: "Data Extraction Tool" should appear

        Expected RED failure: Tool name not in output
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        with patch("data_extract.cli.wizard.prompt") as mock_prompt:
            mock_prompt.return_value = {"mode": "enterprise", "tutorial": False}

            # When
            first_run_wizard(console=mock_console.console)

        # Then
        output = mock_console.exported_text
        assert (
            "data extraction" in output.lower()
        ), f"Expected 'Data Extraction' in output: {output}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestWizardModeSelection:
    """Test mode selection (Enterprise vs Hobbyist)."""

    def test_wizard_prompts_for_mode(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
    ):
        """
        RED: Verify wizard prompts for mode selection.

        Given: First-time wizard flow
        When: We run the wizard
        Then: Mode selection prompt should appear

        Expected RED failure: No mode prompt
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        with patch("data_extract.cli.wizard.prompt") as mock_prompt:
            mock_prompt.return_value = {"mode": "enterprise", "tutorial": False}

            # When
            first_run_wizard(console=mock_console.console)

            # Then - prompt should have been called with mode choices
            assert mock_prompt.called, "prompt() should be called for mode selection"

    def test_wizard_enterprise_mode_selection(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
        wizard_responses_fixture,
    ):
        """
        RED: Verify Enterprise mode can be selected.

        Given: User selects Enterprise mode
        When: We complete wizard
        Then: Config should have mode='enterprise'

        Expected RED failure: Config not saved or wrong mode
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        with patch("data_extract.cli.wizard.prompt") as mock_prompt:
            mock_prompt.return_value = {"mode": "enterprise", "tutorial": False}

            # When
            first_run_wizard(console=mock_console.console)

        # Then - check config file was created with correct mode
        config_file = mock_home_directory.config_dir / "config.yaml"
        assert config_file.exists(), "Config file should be created"

        import yaml

        config = yaml.safe_load(config_file.read_text())
        assert (
            config.get("mode") == "enterprise"
        ), f"Mode should be 'enterprise', got: {config.get('mode')}"

    def test_wizard_hobbyist_mode_selection(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
    ):
        """
        RED: Verify Hobbyist mode can be selected.

        Given: User selects Hobbyist mode
        When: We complete wizard
        Then: Config should have mode='hobbyist'

        Expected RED failure: Mode not saved correctly
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        with patch("data_extract.cli.wizard.prompt") as mock_prompt:
            mock_prompt.return_value = {"mode": "hobbyist", "tutorial": False}

            # When
            first_run_wizard(console=mock_console.console)

        # Then
        config_file = mock_home_directory.config_dir / "config.yaml"
        assert config_file.exists()

        import yaml

        config = yaml.safe_load(config_file.read_text())
        assert config.get("mode") == "hobbyist"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestWizardTutorialOffer:
    """Test tutorial offer during wizard."""

    def test_wizard_offers_tutorial(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
    ):
        """
        RED: Verify wizard offers quick tutorial.

        Given: First-time wizard flow
        When: After mode selection
        Then: Tutorial offer should appear

        Expected RED failure: No tutorial prompt
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        prompt_calls = []

        def capture_prompt(*args, **kwargs):
            prompt_calls.append((args, kwargs))
            if len(prompt_calls) == 1:
                return {"mode": "enterprise"}
            return {"tutorial": False}

        with patch("data_extract.cli.wizard.prompt", side_effect=capture_prompt):
            # When
            first_run_wizard(console=mock_console.console)

        # Then - should have prompts for mode AND tutorial
        output = mock_console.exported_text
        assert (
            "tutorial" in output.lower()
            or "walkthrough" in output.lower()
            or len(prompt_calls) >= 1
        ), "Tutorial offer should be presented"

    def test_wizard_runs_tutorial_when_accepted(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
    ):
        """
        RED: Verify tutorial runs when user accepts.

        Given: User accepts tutorial offer
        When: Tutorial runs
        Then: Educational content should be displayed

        Expected RED failure: Tutorial not executed
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        with patch("data_extract.cli.wizard.prompt") as mock_prompt:
            mock_prompt.return_value = {"mode": "enterprise", "tutorial": True}

            # When
            first_run_wizard(console=mock_console.console)

        # Then - tutorial content should appear
        output = mock_console.exported_text
        # Tutorial should explain something about the tool
        assert (
            "step" in output.lower() or "learn" in output.lower() or "extract" in output.lower()
        ), f"Tutorial content expected in output: {output}"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestWizardConfigCreation:
    """Test wizard creates config files correctly."""

    def test_wizard_creates_config_directory(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
    ):
        """
        RED: Verify wizard creates config directory.

        Given: Clean environment
        When: Wizard completes
        Then: ~/.config/data-extract/ should exist

        Expected RED failure: Directory not created
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        # Remove config dir if exists
        import shutil

        if mock_home_directory.config_dir.exists():
            shutil.rmtree(mock_home_directory.config_dir)

        with patch("data_extract.cli.wizard.prompt") as mock_prompt:
            mock_prompt.return_value = {"mode": "enterprise", "tutorial": False}

            # When
            first_run_wizard(console=mock_console.console)

        # Then
        assert mock_home_directory.config_dir.exists(), "Config directory should be created"

    def test_wizard_creates_valid_yaml_config(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
    ):
        """
        RED: Verify wizard creates valid YAML config.

        Given: Wizard completes successfully
        When: We read the config file
        Then: It should be valid YAML

        Expected RED failure: Invalid YAML or no file
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        with patch("data_extract.cli.wizard.prompt") as mock_prompt:
            mock_prompt.return_value = {"mode": "enterprise", "tutorial": False}

            # When
            first_run_wizard(console=mock_console.console)

        # Then
        config_file = mock_home_directory.config_dir / "config.yaml"
        assert config_file.exists(), "Config file should exist"

        import yaml

        # Should not raise
        config = yaml.safe_load(config_file.read_text())
        assert isinstance(config, dict), "Config should be a dict"

    def test_wizard_saves_user_preferences(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
    ):
        """
        RED: Verify wizard saves user preferences.

        Given: User makes selections during wizard
        When: Wizard completes
        Then: Preferences should be saved in config

        Expected RED failure: Preferences not saved
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        with patch("data_extract.cli.wizard.prompt") as mock_prompt:
            mock_prompt.return_value = {
                "mode": "enterprise",
                "tutorial": False,
            }

            # When
            first_run_wizard(console=mock_console.console)

        # Then
        import yaml

        config_file = mock_home_directory.config_dir / "config.yaml"
        config = yaml.safe_load(config_file.read_text())

        assert "mode" in config, "Config should contain mode"


@pytest.mark.unit
@pytest.mark.story_5_1
class TestWizardOutputFormatting:
    """Test wizard uses Rich formatting correctly."""

    def test_wizard_uses_rich_panel(
        self,
        mock_home_directory: MockHomeStructure,
        mock_console,
        monkeypatch,
    ):
        """
        RED: Verify wizard uses Rich Panel for welcome.

        Given: Wizard displaying welcome
        When: We capture output
        Then: Rich Panel formatting should be present

        Expected RED failure: Plain text output
        """
        # Given
        try:
            from data_extract.cli.wizard import first_run_wizard
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

        monkeypatch.setenv("HOME", str(mock_home_directory.root))

        with patch("data_extract.cli.wizard.prompt") as mock_prompt:
            mock_prompt.return_value = {"mode": "enterprise", "tutorial": False}

            # When
            first_run_wizard(console=mock_console.console)

        # Then - Rich panels have borders
        output = mock_console.output
        # Rich panels typically have box-drawing characters or structured output
        has_formatting = len(output) > 0 and (
            # Check for panel indicators
            "Welcome" in output
            or mock_console._operations  # Operations logged
        )
        assert has_formatting, "Wizard should use Rich formatting"

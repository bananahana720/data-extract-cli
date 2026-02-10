"""Shared fixtures for CLI components tests."""

from io import StringIO
from unittest.mock import Mock

import pytest
from rich.console import Console


@pytest.fixture
def mock_console():
    """Create a mock Rich Console for testing output.

    Returns:
        Mock Console instance for capturing output
    """
    import time

    console = Mock(spec=Console)
    console.no_color = False
    console.get_time = time.time  # Required by Rich Progress
    return console


@pytest.fixture
def string_console():
    """Create a Rich Console that outputs to a StringIO buffer.

    Returns:
        Console instance writing to StringIO for output verification
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, force_terminal=True, width=80)
    # Attach the buffer for test inspection
    console._test_buffer = string_buffer
    return console


@pytest.fixture
def no_color_console():
    """Create a Rich Console with colors disabled.

    Returns:
        Console instance with no_color=True
    """
    string_buffer = StringIO()
    console = Console(file=string_buffer, no_color=True, width=80)
    console._test_buffer = string_buffer
    return console


@pytest.fixture(autouse=True)
def reset_console_singleton():
    """Reset the global console singleton before each test.

    This ensures clean state between tests that use the global console.
    """
    from data_extract.cli.components.feedback import reset_console

    reset_console()
    yield
    reset_console()

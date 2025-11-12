"""Pytest configuration and fixtures for gcallm tests."""

from unittest.mock import Mock

import pytest
from typer.testing import CliRunner


@pytest.fixture()
def cli_runner():
    """Provide a CliRunner for testing CLI commands."""
    return CliRunner()


@pytest.fixture()
def mock_calendar_agent():
    """Provide a mocked CalendarAgent."""
    mock = Mock()
    mock.run.return_value = "Mock event created successfully"
    return mock


@pytest.fixture()
def mock_console():
    """Provide a mocked Rich console."""
    return Mock()

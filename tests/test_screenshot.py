"""Tests for screenshot discovery and integration."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gcallm.helpers.screenshot import find_recent_screenshots


class TestScreenshotDiscovery:
    """Tests for screenshot discovery functionality."""

    def test_find_latest_screenshot(self):
        """Test finding the most recent screenshot."""
        # Create temporary directory with mock screenshots
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock screenshot files
            screenshot1 = Path(tmpdir) / "Screenshot 2025-01-01 at 10.00.00.png"
            screenshot2 = Path(tmpdir) / "Screenshot 2025-01-01 at 11.00.00.png"
            screenshot3 = Path(tmpdir) / "Screenshot 2025-01-01 at 12.00.00.png"

            screenshot1.touch()
            screenshot2.touch()
            screenshot3.touch()

            # Get latest screenshot
            result = find_recent_screenshots(count=1, directory=tmpdir)

            # Should return the most recent one
            assert len(result) == 1
            assert "Screenshot 2025-01-01 at 12.00.00.png" in result[0]

    def test_find_multiple_screenshots(self):
        """Test finding multiple recent screenshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 5 mock screenshots
            for i in range(5):
                screenshot = Path(tmpdir) / f"Screenshot 2025-01-0{i+1}.png"
                screenshot.touch()

            # Get latest 3
            result = find_recent_screenshots(count=3, directory=tmpdir)

            assert len(result) == 3
            # Should be sorted newest-first

    def test_no_screenshots_found(self):
        """Test error handling when no screenshots exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty directory
            with pytest.raises(ValueError, match="No screenshots found"):
                find_recent_screenshots(count=1, directory=tmpdir)

    def test_screenshot_sorting_by_mtime(self):
        """Test screenshots are sorted by modification time (newest first)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import time

            # Create screenshots with different modification times
            screenshot1 = Path(tmpdir) / "Screenshot1.png"
            screenshot1.touch()
            time.sleep(0.01)

            screenshot2 = Path(tmpdir) / "Screenshot2.png"
            screenshot2.touch()
            time.sleep(0.01)

            screenshot3 = Path(tmpdir) / "Screenshot3.png"
            screenshot3.touch()

            result = find_recent_screenshots(count=3, directory=tmpdir)

            # Should be sorted newest-first
            assert "Screenshot3.png" in result[0]
            assert "Screenshot2.png" in result[1]
            assert "Screenshot1.png" in result[2]

    def test_directory_not_found(self):
        """Test error when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            find_recent_screenshots(count=1, directory="/nonexistent/directory")

    def test_spanish_screenshot_pattern(self):
        """Test finding Spanish macOS screenshots (Captura de pantalla)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Spanish screenshot
            screenshot = (
                Path(tmpdir) / "Captura de pantalla 2025-11-04 a la(s) 3.27.08 p.m..png"
            )
            screenshot.touch()

            result = find_recent_screenshots(count=1, directory=tmpdir)

            assert len(result) == 1
            # Spanish screenshot with special chars should be auto-sanitized
            assert ".gcallm_temp_screenshots" in result[0]
            # Original file should still exist
            assert screenshot.exists()

    def test_french_screenshot_pattern(self):
        """Test finding French macOS screenshots (Capture d'écran)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot = Path(tmpdir) / "Capture d'écran 2025-11-04 à 15.27.08.png"
            screenshot.touch()

            result = find_recent_screenshots(count=1, directory=tmpdir)

            assert len(result) == 1
            assert "Capture d'écran" in result[0]

    def test_german_screenshot_pattern(self):
        """Test finding German macOS screenshots (Bildschirmfoto)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot = Path(tmpdir) / "Bildschirmfoto 2025-11-04 um 15.27.08.png"
            screenshot.touch()

            result = find_recent_screenshots(count=1, directory=tmpdir)

            assert len(result) == 1
            assert "Bildschirmfoto" in result[0]

    def test_mixed_locale_screenshots(self):
        """Test finding screenshots from multiple locales in same directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import time

            # Create English screenshot (oldest)
            english = Path(tmpdir) / "Screenshot 2025-11-04 at 10.00.00.png"
            english.touch()
            time.sleep(0.01)

            # Create Spanish screenshot (middle)
            spanish = (
                Path(tmpdir) / "Captura de pantalla 2025-11-04 a la(s) 11.00.00.png"
            )
            spanish.touch()
            time.sleep(0.01)

            # Create French screenshot (newest)
            french = Path(tmpdir) / "Capture d'écran 2025-11-04 à 12.00.00.png"
            french.touch()

            result = find_recent_screenshots(count=3, directory=tmpdir)

            # Should return all 3, sorted by mtime (newest first)
            assert len(result) == 3
            assert "Capture d'écran" in result[0]  # French (newest, no special chars)
            # Spanish has special chars, should be sanitized
            assert ".gcallm_temp_screenshots" in result[1]
            assert "Screenshot" in result[2]  # English (oldest)

    def test_spanish_screenshot_sanitization(self):
        """Test that Spanish screenshots with special chars are auto-sanitized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Spanish screenshot with problematic characters
            # "a la(s)" has parentheses, "p.m." has multiple periods
            spanish = (
                Path(tmpdir) / "Captura de pantalla 2025-11-04 a la(s) 3.27.08 p.m..png"
            )
            spanish.write_text("test")  # Create non-empty file

            result = find_recent_screenshots(count=1, directory=tmpdir)

            # Should return sanitized path (not original with special chars)
            assert len(result) == 1
            result_path = Path(result[0])

            # Sanitized file should exist
            assert result_path.exists()

            # Sanitized filename should NOT have parentheses or multiple periods
            assert "(" not in result_path.name
            assert ")" not in result_path.name
            # Check that it's in temp directory
            assert ".gcallm_temp_screenshots" in str(result_path)

            # Original file should still exist (copy, not move)
            assert spanish.exists()


class TestCLIIntegration:
    """Tests for CLI screenshot flags."""

    @patch("gcallm.helpers.input.find_recent_screenshots")
    @patch(
        "gcallm.cli.create_events"
    )  # Patch where it's imported, not where it's defined
    def test_add_with_screenshot_flag(self, mock_create_events, mock_find_screenshots):
        """Test: gcallm add -s"""
        from typer.testing import CliRunner

        from gcallm.cli import app

        runner = CliRunner()
        mock_find_screenshots.return_value = ["/Users/test/Desktop/Screenshot.png"]
        mock_create_events.return_value = "Event created"

        _result = runner.invoke(app, ["add", "-s"])

        # Should call find_recent_screenshots with count=1
        assert mock_find_screenshots.called
        assert mock_find_screenshots.call_args[1]["count"] == 1

        # Should pass screenshot_paths to create_events
        assert mock_create_events.called

    @patch("gcallm.helpers.input.find_recent_screenshots")
    @patch("gcallm.cli.create_events")  # Patch where it's imported
    def test_add_with_screenshot_short_flag(
        self, mock_create_events, mock_find_screenshots
    ):
        """Test: gcallm add -s (short form)"""
        from typer.testing import CliRunner

        from gcallm.cli import app

        runner = CliRunner()
        mock_find_screenshots.return_value = ["/Users/test/Desktop/Screenshot.png"]
        mock_create_events.return_value = "Event created"

        # Note: -s works fine in pytest with CliRunner
        result = runner.invoke(app, ["add", "-s"])

        assert mock_find_screenshots.called, "find_recent_screenshots was not called"
        assert (
            mock_create_events.called
        ), f"create_events was not called. Exit code: {result.exit_code}"

    @patch("gcallm.helpers.input.find_recent_screenshots")
    @patch("gcallm.cli.create_events")  # Patch where it's imported
    def test_add_with_multiple_screenshots(
        self, mock_create_events, mock_find_screenshots
    ):
        """Test: gcallm add --screenshots 3"""
        from typer.testing import CliRunner

        from gcallm.cli import app

        runner = CliRunner()
        mock_find_screenshots.return_value = [
            "/Users/test/Desktop/Screenshot1.png",
            "/Users/test/Desktop/Screenshot2.png",
            "/Users/test/Desktop/Screenshot3.png",
        ]
        mock_create_events.return_value = "Events created"

        _result = runner.invoke(app, ["add", "--screenshots", "3"])

        # Should call with count=3
        assert mock_find_screenshots.called
        assert mock_find_screenshots.call_args[1]["count"] == 3
        assert mock_create_events.called
        if mock_create_events.call_args:
            assert mock_create_events.call_args[1]["screenshot_paths"] is not None

    @patch("gcallm.helpers.input.find_recent_screenshots")
    @patch("gcallm.cli.create_events")  # Patch where it's imported
    def test_screenshot_plus_text_input(
        self, mock_create_events, mock_find_screenshots
    ):
        """Test: gcallm add -s "Extra context" """
        from typer.testing import CliRunner

        from gcallm.cli import app

        runner = CliRunner()
        mock_find_screenshots.return_value = ["/Users/test/Desktop/Screenshot.png"]
        mock_create_events.return_value = "Event created"

        _result = runner.invoke(app, ["add", "-s", "Team meeting notes"])

        # Should pass both screenshot and text
        assert mock_find_screenshots.called
        assert mock_create_events.called
        if mock_create_events.call_args:
            call_kwargs = mock_create_events.call_args[1]
            assert call_kwargs["screenshot_paths"] is not None
            assert "Team meeting notes" in call_kwargs["user_input"]


class TestAgentIntegration:
    """Tests for agent screenshot handling."""

    @pytest.mark.asyncio()
    @patch("gcallm.agent.ClaudeSDKClient")
    async def test_agent_receives_screenshot_paths(self, mock_client_class):
        """Verify screenshot paths passed to CalendarAgent."""
        from unittest.mock import AsyncMock

        from gcallm.agent import AssistantMessage, CalendarAgent, TextBlock

        # Setup mock client
        mock_client = AsyncMock()
        mock_text_block = Mock()
        mock_text_block.text = "Event created from screenshot"
        mock_text_block.__class__ = TextBlock

        mock_msg = Mock()
        mock_msg.__class__ = AssistantMessage
        mock_msg.content = [mock_text_block]

        async def mock_receive():
            yield mock_msg

        mock_client.receive_response = mock_receive
        mock_client.query = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        agent = CalendarAgent()
        screenshot_paths = ["/Users/test/Desktop/Screenshot.png"]

        # Execute
        _result = await agent.process_events(
            "Create event from screenshot", screenshot_paths=screenshot_paths
        )

        # Verify screenshot paths mentioned in prompt
        assert mock_client.query.called
        call_args = str(mock_client.query.call_args)
        assert "Screenshot.png" in call_args

    @pytest.mark.asyncio()
    @patch("gcallm.agent.ClaudeSDKClient")
    async def test_agent_options_include_desktop_directory(self, mock_client_class):
        """Verify add_dirs contains ~/Desktop when screenshots used."""
        from unittest.mock import AsyncMock

        from gcallm.agent import AssistantMessage, CalendarAgent, TextBlock

        # Setup mock client
        mock_client = AsyncMock()
        mock_text_block = Mock()
        mock_text_block.text = "Event created"
        mock_text_block.__class__ = TextBlock

        mock_msg = Mock()
        mock_msg.__class__ = AssistantMessage
        mock_msg.content = [mock_text_block]

        async def mock_receive():
            yield mock_msg

        mock_client.receive_response = mock_receive
        mock_client.query = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        agent = CalendarAgent()
        screenshot_paths = ["/Users/test/Desktop/Screenshot.png"]

        # Execute
        await agent.process_events("Create event", screenshot_paths=screenshot_paths)

        # Verify ClaudeAgentOptions was created with add_dirs
        # Check the options passed to ClaudeSDKClient
        assert mock_client_class.called
        options = mock_client_class.call_args[1].get("options")

        # When screenshots provided, add_dirs should include Desktop
        if options and hasattr(options, "add_dirs"):
            assert len(options.add_dirs) > 0
            # Should contain expanded Desktop path
            assert any("Desktop" in str(d) for d in options.add_dirs)

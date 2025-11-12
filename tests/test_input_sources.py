"""Tests for composable input source handlers."""

from unittest.mock import patch

from rich.console import Console

from gcallm.helpers.input import (
    handle_clipboard_input,
    handle_direct_input,
    handle_editor_input,
    handle_screenshot_input,
    handle_stdin_input,
)


class TestScreenshotInputHandler:
    """Test handle_screenshot_input."""

    def test_single_screenshot_flag_returns_one_path(self):
        """Single screenshot flag should return latest screenshot."""
        with patch("gcallm.helpers.input.find_recent_screenshots") as mock_find:
            mock_find.return_value = ["/Desktop/Screenshot1.png"]
            result = handle_screenshot_input(screenshots=1)
            assert result == ["/Desktop/Screenshot1.png"]
            mock_find.assert_called_once_with(count=1, directory=None)

    def test_multiple_screenshots_flag_returns_n_paths(self):
        """Multiple screenshots flag should return N latest screenshots."""
        with patch("gcallm.helpers.input.find_recent_screenshots") as mock_find:
            mock_find.return_value = [
                "/Desktop/Screenshot1.png",
                "/Desktop/Screenshot2.png",
            ]
            result = handle_screenshot_input(screenshots=3)
            assert result == [
                "/Desktop/Screenshot1.png",
                "/Desktop/Screenshot2.png",
            ]
            mock_find.assert_called_once_with(count=3, directory=None)

    def test_no_screenshot_flags_returns_none(self):
        """No screenshot flags should return None."""
        result = handle_screenshot_input(screenshots=None)
        assert result is None

    def test_no_screenshots_found_displays_error(self):
        """Should display error and return None if no screenshots found."""
        console = Console()
        with patch("gcallm.helpers.input.find_recent_screenshots") as mock_find:
            with patch("gcallm.helpers.input.format_error") as mock_error:
                mock_find.return_value = []
                result = handle_screenshot_input(screenshots=1, console=console)
                assert result is None
                mock_error.assert_called_once()


class TestDirectInputHandler:
    """Test handle_direct_input."""

    def test_direct_input_returns_text(self):
        """Direct text input should be returned as-is."""
        result = handle_direct_input("Coffee tomorrow at 2pm")
        assert result == "Coffee tomorrow at 2pm"

    def test_none_input_returns_none(self):
        """None input should return None."""
        result = handle_direct_input(None)
        assert result is None

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        result = handle_direct_input("")
        assert result is None


class TestStdinInputHandler:
    """Test handle_stdin_input."""

    def test_stdin_with_data_returns_text(self):
        """Stdin with data should return text."""
        with patch("gcallm.helpers.input.get_from_stdin") as mock_stdin:
            mock_stdin.return_value = "Event from stdin"
            result = handle_stdin_input()
            assert result == "Event from stdin"

    def test_stdin_without_data_returns_none(self):
        """Stdin without data should return None."""
        with patch("gcallm.helpers.input.get_from_stdin") as mock_stdin:
            mock_stdin.return_value = None
            result = handle_stdin_input()
            assert result is None


class TestClipboardInputHandler:
    """Test handle_clipboard_input."""

    def test_clipboard_flag_true_returns_clipboard_content(self):
        """Clipboard flag=True should return clipboard content."""
        with patch("gcallm.helpers.input.get_from_clipboard") as mock_clip:
            mock_clip.return_value = "Event from clipboard"
            result = handle_clipboard_input(clipboard=True)
            assert result == "Event from clipboard"

    def test_clipboard_flag_false_returns_none(self):
        """Clipboard flag=False should return None."""
        result = handle_clipboard_input(clipboard=False)
        assert result is None

    def test_clipboard_empty_returns_none(self):
        """Empty clipboard should return None."""
        with patch("gcallm.helpers.input.get_from_clipboard") as mock_clip:
            mock_clip.return_value = None
            result = handle_clipboard_input(clipboard=True)
            assert result is None


class TestEditorInputHandler:
    """Test handle_editor_input."""

    def test_editor_returns_content(self):
        """Editor should return content from temp file."""
        with patch("gcallm.helpers.input.open_editor") as mock_editor:
            mock_editor.return_value = "Event from editor"
            result = handle_editor_input()
            assert result == "Event from editor"

    def test_editor_cancelled_returns_none(self):
        """Cancelled editor should return None."""
        with patch("gcallm.helpers.input.open_editor") as mock_editor:
            mock_editor.return_value = None
            result = handle_editor_input()
            assert result is None


class TestInputHandlerComposition:
    """Test that handlers work independently and compose well."""

    def test_screenshot_and_direct_input_both_work(self):
        """Screenshot and direct input should be independent."""
        with patch("gcallm.helpers.input.find_recent_screenshots") as mock_find:
            mock_find.return_value = ["/Desktop/Screenshot1.png"]

            screenshots = handle_screenshot_input(screenshots=1)
            text = handle_direct_input("Meeting notes")

            assert screenshots == ["/Desktop/Screenshot1.png"]
            assert text == "Meeting notes"

    def test_handlers_return_none_when_not_applicable(self):
        """All handlers should return None when not applicable."""
        assert handle_screenshot_input(screenshots=None) is None
        assert handle_direct_input(None) is None
        assert handle_clipboard_input(False) is None

        with patch("gcallm.helpers.input.get_from_stdin") as mock_stdin:
            mock_stdin.return_value = None
            assert handle_stdin_input() is None

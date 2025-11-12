"""Tests for input handling."""

from io import StringIO
from unittest.mock import Mock, patch

from gcallm.helpers.input import (
    get_from_clipboard,
    get_from_editor,
    get_from_stdin,
    get_input,
)


class TestGetFromStdin:
    """Tests for stdin input."""

    def test_stdin_with_data(self):
        """Test reading from stdin with data."""
        with patch("sys.stdin", StringIO("test event data")):
            with patch("sys.stdin.isatty", return_value=False):
                result = get_from_stdin()
                assert result == "test event data"

    def test_stdin_is_tty(self):
        """Test stdin returns None when it's a TTY."""
        with patch("sys.stdin.isatty", return_value=True):
            result = get_from_stdin()
            assert result is None

    def test_stdin_empty(self):
        """Test stdin returns None when empty."""
        with patch("sys.stdin", StringIO("")):
            with patch("sys.stdin.isatty", return_value=False):
                result = get_from_stdin()
                assert result is None


class TestGetFromClipboard:
    """Tests for clipboard input."""

    @patch("subprocess.run")
    def test_clipboard_with_data(self, mock_run):
        """Test reading from clipboard with data."""
        mock_run.return_value = Mock(stdout="clipboard content", returncode=0)

        result = get_from_clipboard()

        assert result == "clipboard content"
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_clipboard_empty(self, mock_run):
        """Test clipboard returns None when empty."""
        mock_run.return_value = Mock(stdout="", returncode=0)

        result = get_from_clipboard()

        assert result is None

    @patch("subprocess.run")
    def test_clipboard_error(self, mock_run):
        """Test clipboard returns None on error."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "pbpaste")

        result = get_from_clipboard()

        assert result is None


class TestGetFromEditor:
    """Tests for editor input."""

    @patch("subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    def test_editor_with_content(
        self, mock_unlink, mock_exists, mock_read, mock_tempfile, mock_run
    ):
        """Test getting input from editor."""
        # Setup
        mock_temp = Mock()
        mock_temp.name = "/tmp/test.txt"
        mock_tempfile.return_value.__enter__.return_value = mock_temp

        mock_read.return_value = "# Comment\nTest event\n# Another comment"
        mock_exists.return_value = True
        mock_run.return_value = Mock(returncode=0)

        result = get_from_editor()

        assert result == "Test event"

    @patch("subprocess.run")
    def test_editor_cancelled(self, mock_run):
        """Test editor returns None when cancelled."""
        mock_run.side_effect = KeyboardInterrupt()

        result = get_from_editor()

        assert result is None


class TestGetInput:
    """Tests for main input function."""

    def test_direct_input(self):
        """Test direct input takes priority."""
        result = get_input(direct_input="test event")

        assert result == "test event"

    @patch("gcallm.helpers.input.get_from_stdin")
    def test_stdin_input(self, mock_stdin):
        """Test stdin input when no direct input."""
        mock_stdin.return_value = "stdin event"

        result = get_input()

        assert result == "stdin event"

    @patch("gcallm.helpers.input.get_from_clipboard")
    @patch("gcallm.helpers.input.get_from_stdin")
    def test_clipboard_input(self, mock_stdin, mock_clipboard):
        """Test clipboard input when requested."""
        mock_stdin.return_value = None
        mock_clipboard.return_value = "clipboard event"

        result = get_input(use_clipboard=True)

        assert result == "clipboard event"

    @patch("gcallm.helpers.input.get_from_editor")
    @patch("gcallm.helpers.input.get_from_clipboard")
    @patch("gcallm.helpers.input.get_from_stdin")
    def test_editor_input(self, mock_stdin, mock_clipboard, mock_editor):
        """Test editor input when no other source."""
        mock_stdin.return_value = None
        mock_editor.return_value = "editor event"

        result = get_input(use_editor=True)

        assert result == "editor event"

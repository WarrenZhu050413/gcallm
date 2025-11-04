"""Tests for CLI commands."""

from unittest.mock import Mock, patch
from typer.testing import CliRunner

from gcallm.cli import app


runner = CliRunner()


class TestVerifyCommand:
    """Tests for the verify command."""

    @patch("gcallm.agent.CalendarAgent")
    def test_verify_success(self, mock_agent_class):
        """Test successful verification."""
        mock_agent = Mock()
        mock_agent.run.return_value = "Current time is..."
        mock_agent_class.return_value = mock_agent

        result = runner.invoke(app, ["verify"])

        assert result.exit_code == 0
        assert "✅ All checks passed!" in result.stdout
        assert "Google Calendar MCP: Working" in result.stdout

    @patch("gcallm.agent.CalendarAgent")
    def test_verify_failure(self, mock_agent_class):
        """Test verification failure."""
        mock_agent = Mock()
        mock_agent.run.side_effect = Exception("Connection failed")
        mock_agent_class.return_value = mock_agent

        result = runner.invoke(app, ["verify"])

        assert result.exit_code == 1
        assert "Verification failed" in result.stdout


class TestStatusCommand:
    """Tests for the status command."""

    @patch("gcallm.agent.CalendarAgent")
    def test_status_shows_calendars(self, mock_agent_class):
        """Test status command shows calendar information."""
        mock_agent = Mock()
        mock_agent.run.return_value = "Calendar 1: primary\nCalendar 2: work"
        mock_agent_class.return_value = mock_agent

        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "Google Calendar Status" in result.stdout


class TestCalendarsCommand:
    """Tests for the calendars command."""

    @patch("gcallm.agent.CalendarAgent")
    def test_calendars_lists_available(self, mock_agent_class):
        """Test calendars command lists available calendars."""
        mock_agent = Mock()
        mock_agent.run.return_value = "primary\nwork\npersonal"
        mock_agent_class.return_value = mock_agent

        result = runner.invoke(app, ["calendars"])

        assert result.exit_code == 0
        assert "Available Calendars" in result.stdout


class TestAddCommand:
    """Tests for the add command."""

    @patch("gcallm.cli.create_events")
    def test_add_with_text_creates_event(self, mock_create_events):
        """Test that 'gcallm add \"event text\"' creates an event."""
        mock_create_events.return_value = "✅ Event created successfully"

        result = runner.invoke(app, ["add", "Coffee with Sarah tomorrow at 2pm"])

        assert result.exit_code == 0
        assert mock_create_events.called
        call_args = mock_create_events.call_args
        assert "Coffee with Sarah tomorrow at 2pm" in str(call_args)

    @patch("gcallm.helpers.input.get_from_editor")
    @patch("gcallm.cli.create_events")
    def test_add_without_args_opens_editor(self, mock_create_events, mock_editor):
        """Test that 'gcallm add' without args opens editor."""
        mock_editor.return_value = "Team meeting next Monday at 10am"
        mock_create_events.return_value = "✅ Event created successfully"

        result = runner.invoke(app, ["add"])

        assert result.exit_code == 0
        assert mock_editor.called
        assert mock_create_events.called

    @patch("gcallm.helpers.input.get_from_clipboard")
    @patch("gcallm.cli.create_events")
    def test_add_with_clipboard_flag(self, mock_create_events, mock_clipboard):
        """Test that 'gcallm add --clipboard' reads from clipboard."""
        mock_clipboard.return_value = "Lunch appointment Friday at 12pm"
        mock_create_events.return_value = "✅ Event created successfully"

        result = runner.invoke(app, ["add", "--clipboard"])

        assert result.exit_code == 0
        assert mock_clipboard.called
        assert mock_create_events.called

    @patch("gcallm.cli.create_events")
    def test_rich_formatting_applied(self, mock_create_events):
        """Test that Rich formatting is applied to event output."""
        # Simulate realistic Claude response with markdown
        mock_create_events.return_value = """✅ Created 1 event:

- **Team Meeting**
- **Date & Time:** Monday, November 4, 2025 at 2:00 PM - 3:00 PM (EST)
- **Event Link:** https://www.google.com/calendar/event?eid=abc123"""

        result = runner.invoke(app, ["add", "Team meeting Monday at 2pm"])

        assert result.exit_code == 0
        # Check that the output contains formatted elements
        # The formatter should create panels with "Event Created Successfully"
        assert (
            "Team Meeting" in result.output
            or "Event Created Successfully" in result.output
        )

    @patch("gcallm.cli.create_events")
    def test_conflict_warning_displayed(self, mock_create_events):
        """Test that conflict warnings are displayed properly."""
        mock_create_events.return_value = """✅ Created 1 event:

- **Workshop**
- **Date & Time:** Wednesday at 2:00 PM - 5:00 PM
- **Event Link:** https://www.google.com/calendar/event?eid=xyz

⚠️ Note: This event conflicts with "Other Meeting" (2:00 PM - 3:00 PM)"""

        result = runner.invoke(app, ["add", "Workshop Wednesday at 2pm"])

        assert result.exit_code == 0
        # Should contain conflict information
        assert (
            "Workshop" in result.output
            or "conflicts" in result.output
            or "Note" in result.output
        )

    @patch("gcallm.agent.CalendarAgent")
    def test_cli_uses_tool_results_when_available(self, mock_agent_class):
        """Test that CLI prioritizes tool results over text response."""
        from gcallm.agent import create_events

        # Mock agent to return dict with tool_results
        mock_agent = Mock()
        mock_agent.run.return_value = {
            "text": "Event created successfully",
            "tool_results": [
                {
                    "event_id": "test123",
                    "summary": "Test Event",
                    "start": "2025-11-06T14:00:00-05:00",
                    "end": "2025-11-06T15:00:00-05:00",
                    "htmlLink": "https://www.google.com/calendar/event?eid=test123",
                }
            ],
        }
        mock_agent_class.return_value = mock_agent

        # Capture console output
        from io import StringIO
        from rich.console import Console

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        # Execute
        _result = create_events("Test event tomorrow at 2pm", console=console)

        # Verify tool results were used (should see formatted event, not raw text)
        console_output = output.getvalue()
        assert "Test Event" in console_output
        assert "November" in console_output or "Nov" in console_output
        assert "Event Created Successfully" in console_output

    @patch("gcallm.agent.CalendarAgent")
    def test_cli_falls_back_to_text_when_no_tool_results(self, mock_agent_class):
        """Test that CLI falls back to text formatting when tool_results empty."""
        from gcallm.agent import create_events

        # Mock agent to return dict with empty tool_results
        mock_agent = Mock()
        mock_agent.run.return_value = {
            "text": "✅ Created 1 event:\n\n- **Fallback Event**\n- **Date & Time:** Tomorrow at 3pm",
            "tool_results": [],
        }
        mock_agent_class.return_value = mock_agent

        # Capture console output
        from io import StringIO
        from rich.console import Console

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)

        # Execute
        _result = create_events("Fallback event tomorrow at 3pm", console=console)

        # Should still display something (fallback to markdown parsing)
        console_output = output.getvalue()
        # The markdown fallback or error handling should produce some output
        assert len(console_output) > 0

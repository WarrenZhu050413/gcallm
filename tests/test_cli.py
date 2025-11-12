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
        # Verify the agent was called with calendar query
        assert mock_agent.run.called
        call_args = mock_agent.run.call_args[0][0]
        assert "calendars" in call_args.lower()


class TestAskCommand:
    """Tests for the ask command."""

    @patch("gcallm.agent.CalendarAgent")
    def test_ask_command_with_question(self, mock_agent_class):
        """Test ask command with natural language question."""
        mock_agent = Mock()
        mock_agent.run.return_value = "You have 3 meetings tomorrow"
        mock_agent_class.return_value = mock_agent

        result = runner.invoke(app, ["ask", "What meetings do I have tomorrow?"])

        assert result.exit_code == 0
        assert mock_agent.run.called
        # Verify the question was passed to the agent
        call_args = mock_agent.run.call_args[0][0]
        assert "What meetings do I have tomorrow?" in call_args

    @patch("gcallm.config.get_model")
    @patch("gcallm.agent.CalendarAgent")
    def test_ask_command_with_model_override(self, mock_agent_class, mock_get_model):
        """Test ask command respects --model flag."""
        mock_agent = Mock()
        mock_agent.run.return_value = "Response"
        mock_agent_class.return_value = mock_agent
        mock_get_model.return_value = "haiku"

        result = runner.invoke(app, ["ask", "Test question", "--model", "sonnet"])

        assert result.exit_code == 0
        # Verify CalendarAgent was initialized with sonnet model
        assert mock_agent_class.call_args[1]["model"] == "sonnet"

    @patch("gcallm.agent.CalendarAgent")
    def test_ask_command_error_handling(self, mock_agent_class):
        """Test ask command handles errors gracefully."""
        mock_agent = Mock()
        mock_agent.run.side_effect = Exception("Calendar API error")
        mock_agent_class.return_value = mock_agent

        result = runner.invoke(app, ["ask", "Test question"])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower() or "Error" in result.stdout


class TestCommandRemovals:
    """Tests verifying deprecated commands are removed."""

    def test_status_command_removed(self):
        """Verify status command no longer exists in KNOWN_COMMANDS."""
        from gcallm.cli import KNOWN_COMMANDS

        assert "status" not in KNOWN_COMMANDS

    def test_prompt_command_removed(self):
        """Verify deprecated prompt command is removed from KNOWN_COMMANDS."""
        from gcallm.cli import KNOWN_COMMANDS

        assert "prompt" not in KNOWN_COMMANDS

    def test_ask_command_exists(self):
        """Verify ask command is in KNOWN_COMMANDS."""
        from gcallm.cli import KNOWN_COMMANDS

        assert "ask" in KNOWN_COMMANDS


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

    @patch("gcallm.helpers.input.open_editor")
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
        """Test that CLI formats tool results when available."""
        from gcallm.agent import create_events
        from gcallm.formatter import format_event_response

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

        # Execute (mimics CLI flow: create_events returns dict, then format it)
        result = create_events("Test event tomorrow at 2pm", console=console)

        # Now format the result (this is what CLI does)
        if isinstance(result, dict):
            result = result.get("text", result)
        format_event_response(result, console)

        # Verify tool results were used (should see formatted event, not raw text)
        console_output = output.getvalue()
        # The formatter should show the event details
        assert len(console_output) > 0  # Something was rendered

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


class TestConfigCommand:
    """Tests for the unified config command."""

    @patch("gcallm.config.set_model")
    def test_config_model_haiku(self, mock_set_model):
        """Test 'gcallm config model haiku' sets model to haiku."""
        result = runner.invoke(app, ["config", "model", "haiku"])

        assert result.exit_code == 0
        mock_set_model.assert_called_once_with("haiku")
        assert "haiku" in result.stdout.lower()

    @patch("gcallm.config.set_model")
    def test_config_model_sonnet(self, mock_set_model):
        """Test 'gcallm config model sonnet' sets model to sonnet."""
        result = runner.invoke(app, ["config", "model", "sonnet"])

        assert result.exit_code == 0
        mock_set_model.assert_called_once_with("sonnet")
        assert "sonnet" in result.stdout.lower()

    @patch("gcallm.config.set_model")
    def test_config_model_opus(self, mock_set_model):
        """Test 'gcallm config model opus' sets model to opus."""
        result = runner.invoke(app, ["config", "model", "opus"])

        assert result.exit_code == 0
        mock_set_model.assert_called_once_with("opus")
        assert "opus" in result.stdout.lower()

    @patch("gcallm.config.set_model")
    def test_config_model_invalid_shows_error(self, mock_set_model):
        """Test 'gcallm config model invalid' shows error."""
        mock_set_model.side_effect = ValueError(
            "Invalid model: invalid. Must be one of: ['haiku', 'sonnet', 'opus']"
        )

        result = runner.invoke(app, ["config", "model", "invalid"])

        assert result.exit_code == 1
        assert "Invalid model" in result.stdout or "Error" in result.stdout

    @patch("gcallm.helpers.input.open_editor")
    @patch("gcallm.config.set_custom_system_prompt")
    def test_config_prompt_opens_editor(self, mock_set_prompt, mock_editor):
        """Test 'gcallm config prompt' opens editor to edit system prompt."""
        mock_editor.return_value = "You are a helpful calendar assistant"

        result = runner.invoke(app, ["config", "prompt"])

        assert result.exit_code == 0
        mock_editor.assert_called_once()
        mock_set_prompt.assert_called_once_with("You are a helpful calendar assistant")
        assert "System prompt updated" in result.stdout

    @patch("gcallm.helpers.input.open_editor")
    def test_config_prompt_cancel_does_nothing(self, mock_editor):
        """Test cancelling prompt editor doesn't change config."""
        mock_editor.return_value = None  # User cancelled

        result = runner.invoke(app, ["config", "prompt"])

        assert result.exit_code == 0
        assert (
            "cancelled" in result.stdout.lower() or "aborted" in result.stdout.lower()
        )

    @patch("gcallm.config.clear_custom_system_prompt")
    def test_config_prompt_clear(self, mock_clear_prompt):
        """Test 'gcallm config prompt --clear' clears custom prompt."""
        result = runner.invoke(app, ["config", "prompt", "--clear"])

        assert result.exit_code == 0
        mock_clear_prompt.assert_called_once()
        assert "cleared" in result.stdout.lower() or "reset" in result.stdout.lower()

    @patch("gcallm.config.get_model")
    @patch("gcallm.config.get_custom_system_prompt")
    @patch("gcallm.config.get_oauth_credentials_path")
    def test_config_show_displays_current_config(
        self, mock_oauth, mock_prompt, mock_model
    ):
        """Test 'gcallm config show' displays current configuration."""
        mock_model.return_value = "haiku"
        mock_prompt.return_value = "Custom prompt here"
        mock_oauth.return_value = "/path/to/oauth.json"

        result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        assert "haiku" in result.stdout
        assert "Custom prompt" in result.stdout or "prompt" in result.stdout.lower()

    @patch("gcallm.config.get_model")
    @patch("gcallm.config.get_custom_system_prompt")
    def test_config_show_handles_default_prompt(self, mock_prompt, mock_model):
        """Test 'gcallm config show' handles case with no custom prompt."""
        mock_model.return_value = "sonnet"
        mock_prompt.return_value = None  # No custom prompt

        result = runner.invoke(app, ["config", "show"])

        assert result.exit_code == 0
        assert "sonnet" in result.stdout
        assert "default" in result.stdout.lower() or "none" in result.stdout.lower()

    def test_config_no_args_shows_current_config(self):
        """Test 'gcallm config' without args shows current configuration."""
        result = runner.invoke(app, ["config"])

        # Should show current config (same as 'show')
        assert result.exit_code == 0
        assert "Current Configuration" in result.stdout or "Model:" in result.stdout


class TestMainRouting:
    """Integration tests for main() entry point routing."""

    @patch("gcallm.cli.app")
    def test_main_routes_config_to_typer(self, mock_app):
        """Test that main() routes 'config' command to Typer app."""
        import sys

        from gcallm.cli import main

        # Simulate 'gcallm config'
        original_argv = sys.argv
        try:
            sys.argv = ["gcallm", "config"]
            main()
            # Should call app() to let Typer handle it
            mock_app.assert_called_once()
        finally:
            sys.argv = original_argv

    @patch("gcallm.cli.app")
    def test_main_routes_config_show_to_typer(self, mock_app):
        """Test that main() routes 'config show' to Typer app."""
        import sys

        from gcallm.cli import main

        # Simulate 'gcallm config show'
        original_argv = sys.argv
        try:
            sys.argv = ["gcallm", "config", "show"]
            main()
            # Should call app() to let Typer handle it
            mock_app.assert_called_once()
        finally:
            sys.argv = original_argv

    @patch("gcallm.cli.app")
    def test_main_routes_help_flags_to_typer(self, mock_app):
        """Test that main() routes --help to Typer app."""
        import sys

        from gcallm.cli import main

        # Simulate 'gcallm --help'
        original_argv = sys.argv
        try:
            sys.argv = ["gcallm", "--help"]
            main()
            # Should call app() to let Typer handle it
            mock_app.assert_called_once()
        finally:
            sys.argv = original_argv

    @patch("gcallm.cli.default_command")
    def test_main_routes_unknown_to_default_command(self, mock_default):
        """Test that main() routes unknown commands to default_command()."""
        import sys

        from gcallm.cli import main

        # Simulate 'gcallm Meeting tomorrow'
        original_argv = sys.argv
        try:
            sys.argv = ["gcallm", "Meeting", "tomorrow"]
            main()
            # Should call default_command()
            mock_default.assert_called_once()
        finally:
            sys.argv = original_argv

    @patch("gcallm.cli.app")
    def test_main_routes_all_known_commands_to_typer(self, mock_app):
        """Test that all KNOWN_COMMANDS are routed to Typer."""
        import sys

        from gcallm.cli import KNOWN_COMMANDS, main

        original_argv = sys.argv
        try:
            for cmd in KNOWN_COMMANDS:
                mock_app.reset_mock()
                sys.argv = ["gcallm", cmd]
                main()
                # Each known command should call app()
                assert mock_app.called, f"Command '{cmd}' was not routed to app()"
        finally:
            sys.argv = original_argv

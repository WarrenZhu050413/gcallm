"""Tests for user interaction handlers."""

from io import StringIO
from unittest.mock import patch

from rich.console import Console

from gcallm.agent import ask_user_to_proceed, format_phase2_prompt
from gcallm.conflicts import ConflictReport
from gcallm.formatter import display_conflict_report


class TestDisplayConflictReport:
    """Test conflict report display."""

    def test_display_important_conflict(self):
        """Test displaying an important conflict."""
        response = """⚠️ CONFLICT CHECK: IMPORTANT CONFLICTS DETECTED

Proposed event(s):
- **Team Meeting**

Conflicts detected:
- **Existing Meeting** (2:00 PM - 3:00 PM)

<<AWAIT_USER_DECISION>>"""

        report = ConflictReport.from_response(response)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        display_conflict_report(report, console)

        result = output.getvalue()
        assert "Scheduling Conflicts Detected" in result or "CONFLICT" in result
        assert "Team Meeting" in result

    def test_display_no_conflict(self):
        """Test displaying no conflicts."""
        response = """📋 CONFLICT CHECK: NO CONFLICTS

I will create the following event(s):
- **Lunch Meeting**

Ready to proceed."""

        report = ConflictReport.from_response(response)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        display_conflict_report(report, console)

        result = output.getvalue()
        assert "Event Analysis" in result or "NO CONFLICTS" in result


class TestAskUserToProceed:
    """Test user confirmation prompts."""

    @patch("rich.prompt.Confirm.ask")
    def test_user_confirms_proceed(self, mock_confirm):
        """Test user chooses to proceed despite conflicts."""
        mock_confirm.return_value = True

        response = """⚠️ CONFLICT CHECK: IMPORTANT CONFLICTS DETECTED

<<AWAIT_USER_DECISION>>"""

        report = ConflictReport.from_response(response)
        console = Console()

        should_proceed, message = ask_user_to_proceed(report, console)

        assert should_proceed is True
        assert "confirmed" in message.lower() or "proceed" in message.lower()
        assert mock_confirm.called

    @patch("rich.prompt.Confirm.ask")
    def test_user_cancels(self, mock_confirm):
        """Test user chooses to cancel."""
        mock_confirm.return_value = False

        response = """⚠️ CONFLICT CHECK: IMPORTANT CONFLICTS DETECTED

<<AWAIT_USER_DECISION>>"""

        report = ConflictReport.from_response(response)
        console = Console()

        should_proceed, message = ask_user_to_proceed(report, console)

        assert should_proceed is False
        assert (
            "decided not to create" in message.lower() or "conflict" in message.lower()
        )

    def test_auto_proceed_no_conflicts(self):
        """Test automatic proceed when no user decision needed."""
        response = """📋 CONFLICT CHECK: NO CONFLICTS

Ready to proceed."""

        report = ConflictReport.from_response(response)
        console = Console()

        should_proceed, message = ask_user_to_proceed(report, console)

        assert should_proceed is True
        assert message is None

    def test_auto_proceed_minor_conflicts(self):
        """Test automatic proceed with minor conflicts."""
        response = """📋 CONFLICT CHECK: MINOR CONFLICTS

Note: Minor conflict detected, but proceeding."""

        report = ConflictReport.from_response(response)
        console = Console()

        should_proceed, message = ask_user_to_proceed(report, console)

        assert should_proceed is True
        assert message is None


class TestFormatPhase2Prompt:
    """Test Phase 2 prompt formatting."""

    def test_format_basic_prompt(self):
        """Test formatting a basic Phase 2 prompt."""
        user_decision = "User confirmed: proceed despite conflicts"
        original_input = "Team meeting tomorrow at 2pm"

        prompt = format_phase2_prompt(user_decision, original_input)

        assert "User confirmed" in prompt
        assert "Team meeting tomorrow at 2pm" in prompt
        assert "proceed with creating" in prompt.lower()

    def test_format_with_screenshots(self):
        """Test formatting with screenshot paths."""
        user_decision = "No conflicts detected"
        original_input = "Analyze these event screenshots"
        screenshot_paths = [
            "/Users/test/Desktop/Screenshot1.png",
            "/Users/test/Desktop/Screenshot2.png",
        ]

        prompt = format_phase2_prompt(
            user_decision, original_input, screenshot_paths=screenshot_paths
        )

        assert "No conflicts" in prompt
        assert "Screenshot1.png" in prompt
        assert "Screenshot2.png" in prompt
        assert "2" in prompt  # Count of screenshots

    def test_format_no_conflicts_prompt(self):
        """Test formatting when there were no conflicts."""
        user_decision = "No conflicts detected, proceeding with creation"
        original_input = "Coffee chat Friday at 10am"

        prompt = format_phase2_prompt(user_decision, original_input)

        assert "No conflicts" in prompt
        assert "Coffee chat Friday at 10am" in prompt


class TestInteractionFlow:
    """Test complete interaction flows."""

    @patch("rich.prompt.Confirm.ask")
    def test_full_important_conflict_flow_proceed(self, mock_confirm):
        """Test full flow: important conflict, user proceeds."""
        mock_confirm.return_value = True

        # Phase 1 response
        response = """⚠️ CONFLICT CHECK: IMPORTANT CONFLICTS DETECTED

Proposed event(s):
- **Team Meeting**
- **Date & Time:** Tomorrow at 2:00 PM - 3:00 PM

Conflicts detected:
- **Existing Call** (2:00 PM - 2:30 PM)

<<AWAIT_USER_DECISION>>"""

        report = ConflictReport.from_response(response)

        # Display
        console = Console()
        display_conflict_report(report, console)

        # Ask user
        should_proceed, user_message = ask_user_to_proceed(report, console)

        assert should_proceed is True
        assert report.needs_user_decision is True

        # Format Phase 2
        prompt = format_phase2_prompt(user_message, "Team meeting tomorrow at 2pm")

        assert "confirmed" in prompt.lower()
        assert "Team meeting" in prompt

    @patch("rich.prompt.Confirm.ask")
    def test_full_important_conflict_flow_cancel(self, mock_confirm):
        """Test full flow: important conflict, user cancels."""
        mock_confirm.return_value = False

        response = """⚠️ CONFLICT CHECK: IMPORTANT CONFLICTS DETECTED

<<AWAIT_USER_DECISION>>"""

        report = ConflictReport.from_response(response)
        console = Console()

        should_proceed, user_message = ask_user_to_proceed(report, console)

        assert should_proceed is False
        # Phase 2 should not be reached

    def test_full_no_conflict_flow(self):
        """Test full flow: no conflicts, auto-proceed."""
        response = """📋 CONFLICT CHECK: NO CONFLICTS

I will create the following event(s):
- **Lunch**

Ready to proceed."""

        report = ConflictReport.from_response(response)
        console = Console()

        # Display
        display_conflict_report(report, console)

        # Auto-proceed (no user prompt)
        should_proceed, user_message = ask_user_to_proceed(report, console)

        assert should_proceed is True
        assert user_message is None

        # Phase 2 continues automatically

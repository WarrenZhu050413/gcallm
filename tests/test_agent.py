"""Tests for the Calendar Agent."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from rich.console import Console

from gcallm.agent import CalendarAgent, create_events


class TestCalendarAgent:
    """Tests for CalendarAgent class."""

    def test_agent_initialization(self):
        """Test agent can be initialized."""
        console = Console()
        agent = CalendarAgent(console=console, model="haiku")

        assert agent.console == console
        assert agent.model == "haiku"

    def test_agent_default_model(self):
        """Test agent uses haiku by default (from config)."""
        agent = CalendarAgent()

        assert agent.model == "haiku"

    @pytest.mark.asyncio()
    @patch("gcallm.agent.ClaudeSDKClient")
    async def test_process_events(self, mock_client_class):
        """Test process_events makes correct API calls."""
        # Import the real types to construct proper mock messages
        from gcallm.agent import AssistantMessage, TextBlock

        # Setup mock client
        mock_client = AsyncMock()

        # Create mock text block
        mock_text_block = Mock()
        mock_text_block.text = "Event created successfully"

        # Create a properly structured mock message that will pass isinstance checks
        mock_msg = Mock()
        # Set the class to make isinstance work
        mock_msg.__class__ = AssistantMessage
        mock_msg.content = [mock_text_block]

        # Also setup TextBlock isinstance check
        mock_text_block.__class__ = TextBlock

        # Create an async generator that yields the message
        async def mock_receive():
            yield mock_msg

        # Make receive_response() (when called) return the async generator
        mock_client.receive_response = mock_receive
        mock_client.query = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        agent = CalendarAgent()

        # Execute
        result = await agent.process_events("Test event tomorrow at 3pm")

        # Verify
        assert mock_client.query.called
        assert "Test event tomorrow at 3pm" in str(mock_client.query.call_args)
        assert isinstance(result, dict)
        assert "Event created" in result["text"]

    @pytest.mark.asyncio()
    @patch("gcallm.agent.ClaudeSDKClient")
    async def test_process_events_shows_tool_usage(self, mock_client_class):
        """Test that MCP tool usage is displayed to console."""
        from io import StringIO

        from gcallm.agent import AssistantMessage, TextBlock, ToolUseBlock

        # Setup mock client
        mock_client = AsyncMock()

        # Create mock tool use block (Claude calling the MCP tool)
        mock_tool_use = Mock()
        mock_tool_use.__class__ = ToolUseBlock
        mock_tool_use.name = "mcp__google-calendar__create-event"

        # Create mock text block
        mock_text_block = Mock()
        mock_text_block.__class__ = TextBlock
        mock_text_block.text = "Event created successfully"

        # Create message sequence (ToolResultBlock NOT in stream - SDK limitation)
        mock_msg1 = Mock()
        mock_msg1.__class__ = AssistantMessage
        mock_msg1.content = [mock_tool_use]

        mock_msg2 = Mock()
        mock_msg2.__class__ = AssistantMessage
        mock_msg2.content = [mock_text_block]

        # Create an async generator that yields the messages
        async def mock_receive():
            yield mock_msg1
            yield mock_msg2

        mock_client.receive_response = mock_receive
        mock_client.query = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Capture console output
        output = StringIO()
        from rich.console import Console

        console = Console(file=output, force_terminal=True, width=120)

        agent = CalendarAgent(console=console)

        # Execute
        result = await agent.process_events("SUFRA event")

        # Verify tool usage is shown
        console_output = output.getvalue()
        assert "Using tool: mcp__google-calendar__create-event" in console_output

        # Verify result structure
        assert isinstance(result, dict)
        assert "text" in result
        assert "Event created successfully" in result["text"]

    @pytest.mark.asyncio()
    async def test_agent_hook_captures_tool_results_when_called(self):
        """Test that PostToolUse hook logic captures event data correctly.

        NOTE: In production, this hook does NOT fire (SDK limitation).
        This test verifies the hook WOULD work correctly if it were called.
        """
        agent = CalendarAgent()

        # Simulate hook being called with MCP tool response
        hook_input = {
            "tool_name": "mcp__google-calendar__create-event",
            "tool_response": {
                "event_id": "abc123xyz",
                "summary": "Team Standup",
                "start": "2025-11-05T09:00:00-05:00",
                "end": "2025-11-05T09:30:00-05:00",
                "location": "Conference Room A",
                "htmlLink": "https://www.google.com/calendar/event?eid=abc123xyz",
            },
        }

        # Call hook directly
        await agent._post_tool_use_hook(hook_input, None, {})

        # Verify event was captured
        assert len(agent.captured_tool_results) == 1
        event = agent.captured_tool_results[0]
        assert event["event_id"] == "abc123xyz"
        assert event["summary"] == "Team Standup"
        assert event["start"] == "2025-11-05T09:00:00-05:00"
        assert event["end"] == "2025-11-05T09:30:00-05:00"
        assert event["location"] == "Conference Room A"
        assert (
            event["htmlLink"] == "https://www.google.com/calendar/event?eid=abc123xyz"
        )


class TestCreateEvents:
    """Tests for create_events helper function."""

    @patch("gcallm.agent.CalendarAgent")
    def test_create_events_shows_input(self, mock_agent_class):
        """Test create_events displays input to user."""
        mock_agent = Mock()
        mock_agent.run.return_value = "Event created"
        mock_agent_class.return_value = mock_agent

        mock_console = Mock()
        # Add context manager support for console.status()
        mock_console.status.return_value.__enter__ = Mock()
        mock_console.status.return_value.__exit__ = Mock()

        result = create_events(user_input="Test event", console=mock_console)

        # Verify input was displayed
        assert mock_console.print.called
        assert result == "Event created"

    @patch("gcallm.agent.CalendarAgent")
    def test_create_events_uses_primary_calendar(self, mock_agent_class):
        """Test create_events uses primary calendar (always)."""
        mock_agent = Mock()
        mock_agent.run.return_value = "Event created"
        mock_agent_class.return_value = mock_agent

        result = create_events(user_input="Team meeting")

        # Verify the event was created
        assert mock_agent.run.called
        assert result == "Event created"

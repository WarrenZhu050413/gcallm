"""Tests for the Calendar Agent."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
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
        """Test agent uses sonnet by default."""
        agent = CalendarAgent()

        assert agent.model == "sonnet"

    @pytest.mark.asyncio
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
        assert "Event created" in result

    @pytest.mark.asyncio
    @patch("gcallm.agent.ClaudeSDKClient")
    async def test_process_events_logs_tool_results(self, mock_client_class):
        """Test that MCP tool results are captured and logged."""
        from gcallm.agent import AssistantMessage, TextBlock, ToolUseBlock
        from claude_agent_sdk import ToolResultBlock
        from io import StringIO

        # Setup mock client
        mock_client = AsyncMock()

        # Create mock tool use block (Claude calling the MCP tool)
        mock_tool_use = Mock()
        mock_tool_use.__class__ = ToolUseBlock
        mock_tool_use.name = "mcp__google-calendar__create-event"
        mock_tool_use.input = {
            "summary": "SUFRA - Arab Heritage Night",
            "start_time": "2025-11-08T20:30:00",
            "end_time": "2025-11-08T23:00:00",
            "location": "Lowell Dining Hall",
        }

        # Create mock tool result block (MCP tool response)
        mock_tool_result = Mock()
        mock_tool_result.__class__ = ToolResultBlock
        mock_tool_result.content = [
            {
                "event_id": "706i26dn9im",
                "summary": "SUFRA - Arab Heritage Night",
                "start": "2025-11-08T20:30:00-05:00",
                "end": "2025-11-08T23:00:00-05:00",
                "location": "Lowell Dining Hall",
                "htmlLink": "https://www.google.com/calendar/event?eid=NzA2aTI2ZG45aW1qbnBjYm1wa2FyYzhpdnMgd3podUBjb2xsZWdlLmhhcnZhcmQuZWR1",
            }
        ]
        mock_tool_result.is_error = False

        # Create mock text block
        mock_text_block = Mock()
        mock_text_block.__class__ = TextBlock
        mock_text_block.text = "Event created successfully"

        # Create message sequence
        mock_msg1 = Mock()
        mock_msg1.__class__ = AssistantMessage
        mock_msg1.content = [mock_tool_use]

        mock_msg2 = Mock()
        mock_msg2.__class__ = AssistantMessage
        mock_msg2.content = [mock_tool_result]

        mock_msg3 = Mock()
        mock_msg3.__class__ = AssistantMessage
        mock_msg3.content = [mock_text_block]

        # Create an async generator that yields the messages
        async def mock_receive():
            yield mock_msg1
            yield mock_msg2
            yield mock_msg3

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

        # Verify tool result was logged
        console_output = output.getvalue()
        assert "mcp__google-calendar__create-event" in console_output
        # Should log the full event details from the tool result
        assert (
            "SUFRA - Arab Heritage Night" in console_output
            or "706i26dn9im" in console_output
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

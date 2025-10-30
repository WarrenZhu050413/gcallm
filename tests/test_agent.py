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

        result = create_events(
            user_input="Test event",
            calendar="primary",
            console=mock_console
        )

        # Verify input was displayed
        assert mock_console.print.called
        assert result == "Event created"

    @patch("gcallm.agent.CalendarAgent")
    def test_create_events_with_calendar(self, mock_agent_class):
        """Test create_events uses specified calendar."""
        mock_agent = Mock()
        mock_agent.run.return_value = "Event created in work calendar"
        mock_agent_class.return_value = mock_agent

        result = create_events(
            user_input="Team meeting",
            calendar="work"
        )

        # Verify calendar parameter was passed
        call_args = mock_agent.run.call_args
        assert "work" in str(call_args)

"""Claude Agent with Google Calendar MCP access."""

import asyncio
import json
import os
from typing import Optional

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)
from claude_agent_sdk.types import McpStdioServerConfig
from rich.console import Console
from rich.panel import Panel

from gcallm.config import get_oauth_credentials_path, get_custom_system_prompt


SYSTEM_PROMPT = """You are a calendar assistant. The user will provide event descriptions in natural language, URLs, or structured text.

CRITICAL: You MUST use the Google Calendar MCP tools (prefixed with mcp__google-calendar__). DO NOT use bash tools like gcalcli.

ALWAYS follow this workflow:
1. First, get the current date and time using mcp__google-calendar__get-current-time
2. If the input contains URLs, use WebFetch to fetch the page and extract event details
3. Parse the event information and create events using mcp__google-calendar__create-event
4. After creating events, provide a clear summary of what was created

GUIDELINES:
- Parse relative dates ("tomorrow", "next week", "next Monday") relative to the current time
- Infer reasonable defaults:
  - 1 hour duration for meetings/appointments
  - 30 minutes for calls/coffee chats
- Detect multiple events in a single input (e.g., "Meeting Monday and Wednesday at 3pm" = 2 events)
- For URLs, extract: title, date, time, location, description
- For recurring events, use the recurrence parameter with RFC5545 format
- Use the primary calendar unless user specifies otherwise

Calendar operations are low-stakes. Create events directly without asking for confirmation.

FORMAT YOUR RESPONSE:
After creating events, provide a summary in this format:

✅ Created [N] event(s):

[For each event:]
- Title
- Date & Time
- Location (if available)
- Event Link

Keep the summary concise and scannable.
"""


class CalendarAgent:
    """Claude agent with Google Calendar MCP access."""

    def __init__(self, console: Optional[Console] = None, model: str = "sonnet"):
        """Initialize the calendar agent.

        Args:
            console: Rich console for output
            model: Claude model to use (sonnet, opus, haiku)
        """
        self.console = console or Console()
        self.model = model

    def _log_tool_result(self, block: ToolResultBlock) -> None:
        """Log MCP tool result to console.

        Args:
            block: Tool result block containing the MCP response
        """
        if not block.content:
            return

        try:
            # Format the result nicely
            if isinstance(block.content, list):
                for item in block.content:
                    if isinstance(item, dict):
                        result_json = json.dumps(item, indent=2)
                        self.console.print(f"[dim]Tool result:[/dim]\n{result_json}")
                    else:
                        self.console.print(f"[dim]Tool result:[/dim] {item}")
            else:
                self.console.print(f"[dim]Tool result:[/dim] {block.content}")
        except Exception:
            # Fallback if JSON formatting fails
            self.console.print(f"[dim]Tool result:[/dim] {block.content}")

    async def process_events(self, user_input: str) -> str:
        """Process event description and create events using GCal MCP.

        Args:
            user_input: Natural language event description, URL, or structured text

        Returns:
            Summary of created events
        """
        # Load OAuth credentials path from config
        oauth_path = get_oauth_credentials_path()
        if oauth_path:
            os.environ["GOOGLE_OAUTH_CREDENTIALS"] = oauth_path

        # EXPLICIT MCP configuration for Google Calendar
        # Using McpStdioServerConfig with only required fields
        google_calendar_mcp: McpStdioServerConfig = {
            "command": "npx",
            "args": ["-y", "@cocal/google-calendar-mcp"],
        }

        # Use custom system prompt if configured, otherwise use default
        system_prompt = get_custom_system_prompt() or SYSTEM_PROMPT

        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=system_prompt,
            permission_mode="bypassPermissions",
            max_turns=10,
            mcp_servers={"google-calendar": google_calendar_mcp},
        )

        full_prompt = f"""User input: {user_input}

Please create the event(s) as described."""

        response_text = []

        async with ClaudeSDKClient(options=options) as client:
            # Send query
            await client.query(full_prompt)

            # Stream response
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            response_text.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            # Show tool usage (for transparency)
                            self.console.print(f"[dim]Using tool: {block.name}[/dim]")
                        elif isinstance(block, ToolResultBlock):
                            # Log the full tool result
                            self._log_tool_result(block)

        return "".join(response_text)

    def run(self, user_input: str) -> str:
        """Synchronous wrapper for process_events.

        Args:
            user_input: Natural language event description

        Returns:
            Summary of created events
        """
        return asyncio.run(self.process_events(user_input))


def create_events(user_input: str, console: Optional[Console] = None) -> str:
    """Main entry point for creating events.

    Args:
        user_input: Natural language event description, URL, or structured text
        console: Rich console for output

    Returns:
        Summary of created events
    """
    agent = CalendarAgent(console=console)

    # Show what's being processed
    console = console or Console()
    console.print()
    console.print(Panel(
        f"[cyan]{user_input}[/cyan]",
        title="📤 Creating events from",
        border_style="blue"
    ))
    console.print()

    # Show processing indicator
    with console.status("[bold green]🤖 Processing with Claude...", spinner="dots"):
        result = agent.run(user_input)

    console.print()
    return result

"""Claude Agent with Google Calendar MCP access."""

import asyncio
from typing import Optional

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
)
from rich.console import Console
from rich.panel import Panel


SYSTEM_PROMPT = """You are a calendar assistant. The user will provide event descriptions in natural language, URLs, or structured text.

ALWAYS follow this workflow:
1. First, get the current date and time using the get-current-time tool
2. If the input contains URLs, use WebFetch to fetch the page and extract event details
3. Parse the event information and create events using the create-event tool
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

    async def process_events(self, user_input: str, calendar: str = "primary") -> str:
        """Process event description and create events using GCal MCP.

        Args:
            user_input: Natural language event description, URL, or structured text
            calendar: Target calendar (default: primary)

        Returns:
            Summary of created events
        """
        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=SYSTEM_PROMPT,  # System prompt goes in options
            permission_mode="bypassPermissions",
            max_turns=10,  # Allow multiple tool calls for complex operations
            setting_sources=["user"],  # Load user settings to get MCP configurations
        )

        full_prompt = f"""User input: {user_input}

Target calendar: {calendar}

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
                            if block.name == "mcp__google-calendar__create-event":
                                self.console.print(f"[dim]Creating event...[/dim]")
                            elif block.name == "mcp__google-calendar__get-current-time":
                                self.console.print(f"[dim]Getting current time...[/dim]")
                            elif block.name == "WebFetch":
                                self.console.print(f"[dim]Fetching URL...[/dim]")

        return "".join(response_text)

    def run(self, user_input: str, calendar: str = "primary") -> str:
        """Synchronous wrapper for process_events.

        Args:
            user_input: Natural language event description
            calendar: Target calendar

        Returns:
            Summary of created events
        """
        return asyncio.run(self.process_events(user_input, calendar))


def create_events(user_input: str, calendar: str = "primary", console: Optional[Console] = None) -> str:
    """Main entry point for creating events.

    Args:
        user_input: Natural language event description, URL, or structured text
        calendar: Target calendar (default: primary)
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
        result = agent.run(user_input, calendar)

    console.print()
    return result

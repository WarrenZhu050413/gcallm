"""Claude Agent with Google Calendar MCP access."""

import asyncio
import os
from typing import Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
    ToolUseBlock,
)
from claude_agent_sdk.types import McpStdioServerConfig
from rich.console import Console
from rich.panel import Panel

from gcallm.config import get_custom_system_prompt, get_oauth_credentials_path
from gcallm.conflicts import ConflictReport


SYSTEM_PROMPT = """You are a calendar assistant. The user will provide event descriptions in natural language, URLs, screenshots, or structured text.

CRITICAL: You MUST use the Google Calendar MCP tools (prefixed with mcp__google-calendar__). DO NOT use bash tools like gcalcli.

ALWAYS follow this workflow:
1. First, get the current date and time using mcp__google-calendar__get-current-time
2. If the input contains URLs, use WebFetch to fetch the page and extract event details
3. If the input contains screenshot paths, use the Read tool to analyze the images for event information
4. Parse the event information and create events using mcp__google-calendar__create-event
5. After creating events, provide a clear summary of what was created

GUIDELINES:
- Parse relative dates ("tomorrow", "next week", "next Monday") relative to the current time
- Infer reasonable defaults:
  - 1 hour duration for meetings/appointments
  - 30 minutes for calls/coffee chats
- Detect multiple events in a single input (e.g., "Meeting Monday and Wednesday at 3pm" = 2 events)
- For URLs, extract: title, date, time, location, description
- For recurring events, use the recurrence parameter with RFC5545 format
- Use the primary calendar unless user specifies otherwise

SCREENSHOT ANALYSIS:
When analyzing screenshots for event information:
- Look carefully for dates, times, and locations in the image
- Extract event titles, descriptions, and any relevant details
- Common screenshot types: event flyers, email invitations, meeting notes, calendar screenshots
- If multiple events appear in one screenshot, create all of them
- If details are unclear, make best-guess estimates and note any uncertainty in the summary

Calendar operations are low-stakes. Create events directly without asking for confirmation.

FORMAT YOUR RESPONSE:
After creating events, provide a summary with event details in XML format:

<events>
  <event>
    <title>[Event Title]</title>
    <when>[Date and Time - e.g., "Nov 12, 2024 at 4:30 PM - 6:00 PM"]</when>
    <link>[Google Calendar Event URL]</link>
  </event>
</events>

Include a brief message before or after the XML if helpful, but ALWAYS include the XML block with event details.
"""

INTERACTIVE_SYSTEM_PROMPT = """You are a calendar assistant. The user will provide event descriptions in natural language, URLs, screenshots, or structured text.

CRITICAL: You MUST use the Google Calendar MCP tools (prefixed with mcp__google-calendar__). DO NOT use bash tools like gcalcli.

CRITICAL RESPONSE FORMAT - Use EXACTLY this XML structure in Phase 1:

EXAMPLE 1 (Important Conflict):
<conflict_analysis>
  <status>important_conflicts</status>
  <proposed_events>
    <event>
      <title>Team Meeting</title>
      <datetime>Monday, November 10 at 2:00 PM - 3:00 PM (EST)</datetime>
    </event>
  </proposed_events>
  <conflicts>
    <conflict>
      <title>Project Review</title>
      <time>2:00 PM - 2:30 PM</time>
    </conflict>
    <conflict>
      <title>Client Call</title>
      <time>2:30 PM - 3:00 PM</time>
    </conflict>
  </conflicts>
  <user_decision_required>true</user_decision_required>
</conflict_analysis>

EXAMPLE 2 (No Conflicts):
<conflict_analysis>
  <status>no_conflicts</status>
  <proposed_events>
    <event>
      <title>Lunch</title>
      <datetime>Tuesday at 12:00 PM - 1:00 PM (EST)</datetime>
    </event>
  </proposed_events>
  <user_decision_required>false</user_decision_required>
</conflict_analysis>

EXAMPLE 3 (Minor Conflict):
<conflict_analysis>
  <status>minor_conflicts</status>
  <proposed_events>
    <event>
      <title>Coffee Chat</title>
      <datetime>Friday at 10:00 AM - 10:30 AM (EST)</datetime>
    </event>
  </proposed_events>
  <conflicts>
    <conflict>
      <title>Team Standup (Tentative)</title>
      <time>10:00 AM - 10:15 AM</time>
    </conflict>
  </conflicts>
  <user_decision_required>false</user_decision_required>
</conflict_analysis>

CRITICAL INSTRUCTION - READ THIS CAREFULLY:
In Phase 1, after using the MCP tools, your response must be ONLY the XML <conflict_analysis> tag.
- Do NOT write explanatory text like "I'll analyze..." or "Let me check..."
- Do NOT narrate what you're doing
- JUST output the <conflict_analysis>...</conflict_analysis> XML structure
- Nothing before it, nothing after it

INTERACTIVE MODE WORKFLOW:
This is a TWO-PHASE workflow for conflict-aware event creation:

PHASE 1 - ANALYSIS (DO NOT CREATE EVENTS YET):
1. Get the current date and time using mcp__google-calendar__get-current-time
2. If the input contains URLs, use WebFetch to fetch the page and extract event details
3. If the input contains screenshot paths, use the Read tool to analyze the images
4. Parse the event information and determine what events would be created
5. Check for conflicts using mcp__google-calendar__get-freebusy for each proposed event
6. Output ONLY the XML <conflict_analysis> structure - NOTHING ELSE

PHASE 2 - CREATION (after user confirmation):
1. Create the events using mcp__google-calendar__create-event
2. Provide summary of created events

CONFLICT DETECTION:
- Use mcp__google-calendar__get-freebusy to check if proposed time slots have existing events
- A conflict is IMPORTANT if:
  - 2 or more existing events overlap with the proposed event
  - The existing event is an all-day event
  - The overlap is significant (>50% of the proposed event duration)
- A conflict is MINOR if:
  - Only 1 existing event with minor overlap (<50%)
  - The existing event is marked as "Free" or "Tentative"

GUIDELINES:
- Parse relative dates relative to current time
- Infer reasonable defaults (1hr for meetings, 30min for calls)
- Detect multiple events in single input
- Use RFC5545 format for recurring events
- Primary calendar unless specified otherwise

SCREENSHOT ANALYSIS:
- Extract dates, times, locations, titles from images
- Handle flyers, invitations, meeting notes, calendar screenshots
- Create all events found in screenshots
- Note any uncertainties in the report

CRITICAL REMINDERS:
- Phase 1: Output ONLY the <conflict_analysis> XML structure shown in the examples above
- Phase 1: DO NOT create any events, DO NOT add explanatory text, DO NOT ask questions
- Phase 2: After user confirmation, create the events and provide a summary
"""


class CalendarAgent:
    """Claude agent with Google Calendar MCP access."""

    def __init__(self, console: Optional[Console] = None, model: Optional[str] = None):
        """Initialize the calendar agent.

        Args:
            console: Rich console for output
            model: Claude model to use (haiku, sonnet, opus). If None, uses configured model.
        """
        from gcallm.config import get_model

        self.console = console or Console()
        self.model = model or get_model()  # Default to configured model (haiku)
        self.captured_tool_results: list[dict] = []

    def _setup_mcp_config(
        self, screenshot_paths: Optional[list[str]] = None
    ) -> tuple[dict, list[str], dict]:
        """Set up MCP configuration, filesystem access, and hooks.

        Args:
            screenshot_paths: Optional list of screenshot paths

        Returns:
            Tuple of (google_calendar_mcp, add_dirs, hooks)
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

        # Build add_dirs list for filesystem access
        add_dirs = []
        if screenshot_paths:
            # Grant access to Desktop for reading screenshots
            add_dirs.append(os.path.expanduser("~/Desktop"))

        # Configure PostToolUse hook to capture MCP tool results
        from claude_agent_sdk.types import HookMatcher

        hooks = {
            "PostToolUse": [
                HookMatcher(
                    matcher=None,  # Match ALL tools to see if hook gets called
                    hooks=[self._post_tool_use_hook],
                )
            ]
        }

        return google_calendar_mcp, add_dirs, hooks

    async def _post_tool_use_hook(
        self, hook_input: dict, session_id: str | None, context: dict
    ) -> dict:
        """Hook to capture MCP tool results after tool execution.

        NOTE: This hook is configured but does NOT fire in production with current SDK.
        See TECHNICAL_NOTES.md for details on MCP tool result capture limitation.

        Args:
            hook_input: Hook input containing tool_name, tool_input, tool_response
            session_id: Optional session ID
            context: Hook context

        Returns:
            Hook output dict
        """
        tool_name = hook_input.get("tool_name", "")
        tool_response = hook_input.get("tool_response")

        # Only capture Google Calendar create-event results
        if tool_name == "mcp__google-calendar__create-event" and tool_response:
            # tool_response should be the event dict from MCP
            if (
                isinstance(tool_response, dict)
                and "event_id" in tool_response
                and "summary" in tool_response
            ):
                self.captured_tool_results.append(tool_response)

        return {}

    async def process_events(
        self,
        user_input: str,
        screenshot_paths: Optional[list[str]] = None,
        interactive: bool = False,
    ) -> dict:
        """Process event description and create events using GCal MCP.

        Args:
            user_input: Natural language event description, URL, or structured text
            screenshot_paths: Optional list of screenshot paths to analyze
            interactive: If True, use two-phase workflow with conflict checking

        Returns:
            Dict with 'text' (Claude's response) and 'tool_results' (captured MCP data)
        """
        # Reset captured results for this request
        self.captured_tool_results = []

        # Set up MCP config, filesystem access, and hooks
        google_calendar_mcp, add_dirs, hooks = self._setup_mcp_config(screenshot_paths)

        # Choose system prompt based on mode
        if interactive:
            system_prompt = INTERACTIVE_SYSTEM_PROMPT
        else:
            system_prompt = get_custom_system_prompt() or SYSTEM_PROMPT

        # Permission mode: "default" allows MCP tool usage while requiring approval for file writes
        # This is safer than "bypassPermissions" - users can approve screenshot reads if needed
        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=system_prompt,
            permission_mode="default",  # Require approval for file operations (safer)
            max_turns=10,
            mcp_servers={"google-calendar": google_calendar_mcp},
            add_dirs=add_dirs,  # Grant Desktop access when screenshots provided
            hooks=hooks,  # Enable PostToolUse hook
        )

        # Build prompt with screenshots
        full_prompt = f"User input: {user_input}\n"
        if screenshot_paths:
            full_prompt += f"\nScreenshots to analyze ({len(screenshot_paths)}):\n"
            for path in screenshot_paths:
                full_prompt += f"- {path}\n"

        if interactive:
            full_prompt += (
                "\nPHASE 1: Analyze and output the <conflict_analysis> XML structure ONLY. "
                "Do not add any other text."
            )
        else:
            full_prompt += "\nPlease create the event(s) as described."

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

        return {
            "text": "".join(response_text),
            "tool_results": self.captured_tool_results,
        }

    async def process_events_interactive(
        self, user_input: str, screenshot_paths: Optional[list[str]] = None
    ) -> str:
        """Process events with interactive conflict checking (two-phase workflow).

        Args:
            user_input: Natural language event description
            screenshot_paths: Optional screenshot paths

        Returns:
            Summary of created events or cancellation message
        """
        from gcallm.formatter import display_conflict_report

        # Workflow functions are now in this module (ask_user_to_proceed, format_phase2_prompt)

        # PHASE 1: Analyze and check for conflicts
        phase1_result = await self.process_events(
            user_input=user_input,
            screenshot_paths=screenshot_paths,
            interactive=True,
        )

        # Extract text from result (process_events returns dict now)
        phase1_response = phase1_result["text"]

        # Parse the conflict report with strict XML enforcement
        try:
            report = ConflictReport.from_response(phase1_response, strict=True)
        except ValueError as e:
            # Claude didn't return XML format - show error and extracted response
            self.console.print()
            self.console.print(f"[red]✗ Error: {e}[/red]")
            self.console.print("[yellow]Claude's response:[/yellow]")
            self.console.print(phase1_response[:500])  # Show first 500 chars
            self.console.print()
            raise ValueError(
                "Interactive mode requires XML format from Claude. "
                "Please check system prompt configuration."
            ) from e

        # Display the conflict report to user
        display_conflict_report(report, self.console)

        # Check if user decision is needed
        if report.needs_user_decision:
            should_proceed, user_message = ask_user_to_proceed(report, self.console)

            if not should_proceed:
                self.console.print()
                self.console.print("[yellow]Event creation cancelled.[/yellow]")
                return "Event creation cancelled by user due to scheduling conflicts."

            # User wants to proceed - continue to Phase 2
            self.console.print()
            self.console.print("[green]Proceeding with event creation...[/green]")

        # PHASE 2: Create the events
        # Build Phase 2 prompt
        phase2_prompt = format_phase2_prompt(
            user_decision=(
                "User confirmed: proceed with event creation despite conflicts"
                if report.needs_user_decision
                else "No conflicts detected, proceeding with creation"
            ),
            original_input=user_input,
            screenshot_paths=screenshot_paths,
        )

        # Set up MCP config again for Phase 2
        google_calendar_mcp, add_dirs, hooks = self._setup_mcp_config(screenshot_paths)

        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=INTERACTIVE_SYSTEM_PROMPT,
            permission_mode="default",  # Require approval for file operations (safer)
            max_turns=10,
            mcp_servers={"google-calendar": google_calendar_mcp},
            add_dirs=add_dirs,
            hooks=hooks,  # Enable PostToolUse hook
        )

        response_text = []

        async with ClaudeSDKClient(options=options) as client:
            # Send Phase 2 query
            await client.query(phase2_prompt)

            # Stream response
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            response_text.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            self.console.print(f"[dim]Using tool: {block.name}[/dim]")

        return "".join(response_text)

    def run(
        self,
        user_input: str,
        screenshot_paths: Optional[list[str]] = None,
        interactive: bool = False,
    ) -> dict | str:
        """Synchronous wrapper for process_events.

        Args:
            user_input: Natural language event description
            screenshot_paths: Optional list of screenshot paths
            interactive: If True, use interactive mode with conflict checking

        Returns:
            Dict with 'text' and 'tool_results' (normal mode) or str (interactive mode)
        """
        if interactive:
            text_result = asyncio.run(
                self.process_events_interactive(
                    user_input, screenshot_paths=screenshot_paths
                )
            )
            # Wrap in dict format for consistency
            return {
                "text": text_result,
                "tool_results": self.captured_tool_results,
            }
        else:
            return asyncio.run(
                self.process_events(user_input, screenshot_paths=screenshot_paths)
            )


def ask_user_to_proceed(
    report: "ConflictReport", console: Console
) -> tuple[bool, Optional[str]]:
    """Ask the user whether to proceed with event creation despite conflicts.

    Args:
        report: Parsed conflict report
        console: Rich console for output

    Returns:
        Tuple of (should_proceed, user_message)
        - should_proceed: True if user wants to create events anyway
        - user_message: Optional additional context from user
    """
    if not report.needs_user_decision:
        # No user decision needed, auto-proceed
        return (True, None)

    console.print()

    # Import here to avoid circular dependency
    from rich.prompt import Confirm

    # Ask user to confirm
    proceed = Confirm.ask(
        "[bold]Do you want to create this event anyway?[/bold]",
        default=False,
    )

    if not proceed:
        return (False, "User decided not to create event due to conflicts")

    # User wants to proceed despite conflicts
    return (True, "User confirmed: proceed with event creation despite conflicts")


def format_phase2_prompt(
    user_decision: str,
    original_input: str,
    screenshot_paths: Optional[list[str]] = None,
) -> str:
    """Format the Phase 2 prompt to send to Claude.

    Args:
        user_decision: The user's decision message
        original_input: Original event description from user
        screenshot_paths: Optional screenshot paths

    Returns:
        Formatted prompt for Phase 2
    """
    prompt = f"{user_decision}\n\n"
    prompt += f"Original request: {original_input}\n"

    if screenshot_paths:
        prompt += f"\nScreenshots ({len(screenshot_paths)}):\n"
        for path in screenshot_paths:
            prompt += f"- {path}\n"

    prompt += "\nPlease proceed with creating the event(s) now."
    return prompt


def create_events(
    user_input: str,
    screenshot_paths: Optional[list[str]] = None,
    console: Optional[Console] = None,
    interactive: bool = False,
) -> str:
    """Main entry point for creating events.

    Args:
        user_input: Natural language event description, URL, or structured text
        screenshot_paths: Optional list of screenshot paths to analyze
        console: Rich console for output
        interactive: If True, check for conflicts and ask user before creating

    Returns:
        Summary of created events
    """
    agent = CalendarAgent(console=console)

    # Show what's being processed
    console = console or Console()
    console.print()

    # Build display message
    input_preview = user_input
    if screenshot_paths:
        screenshot_note = f"\n[dim]+ {len(screenshot_paths)} screenshot(s)[/dim]"
        input_preview += screenshot_note

    mode_indicator = "🔍 Analyzing events" if interactive else "📤 Creating events from"

    console.print(
        Panel(
            f"[cyan]{input_preview}[/cyan]",
            title=mode_indicator,
            border_style="blue",
        )
    )
    console.print()

    # Show processing indicator
    status_msg = (
        "[bold green]🤖 Checking for conflicts..."
        if interactive
        else "[bold green]🤖 Processing with Claude..."
    )

    with console.status(status_msg, spinner="dots"):
        result = agent.run(
            user_input, screenshot_paths=screenshot_paths, interactive=interactive
        )

    console.print()

    # Return result without formatting (CLI will format)
    # Extract text if dict, otherwise return as-is
    if isinstance(result, dict):
        return result.get("text", result)
    return result

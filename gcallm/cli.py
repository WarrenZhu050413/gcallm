#!/usr/bin/env python3
"""Command-line interface for gcallm."""

from enum import Enum
from typing import Optional

import sys
import typer
from rich.console import Console

from gcallm.agent import create_events
from gcallm.formatters import format_error, format_no_input_warning
from gcallm.helpers.input import get_input


# Initialize Typer app and console
app = typer.Typer(
    name="gcallm",
    help="Simple CLI to add events to Google Calendar using Claude and natural language",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


class OutputFormat(str, Enum):
    """Output format for CLI commands."""
    RICH = "rich"
    JSON = "json"


def default_command():
    """Handle default behavior when no recognized command is provided."""
    # Get event description from command line args or stdin
    args = sys.argv[1:]

    # Check if it's a known subcommand
    known_commands = ["verify", "status", "calendars"]
    if args and args[0] in known_commands:
        return None  # Let Typer handle it

    # Otherwise, treat as event description
    event_description = " ".join(args) if args else None
    clipboard = "--clipboard" in args or "-c" in args

    # Filter out flags from event description
    if event_description:
        event_description = " ".join([arg for arg in args if not arg.startswith("-")])
        if not event_description:
            event_description = None

    try:
        # Check for stdin first (takes priority)
        has_stdin = not sys.stdin.isatty()

        # Determine if we should use editor mode
        use_editor = not event_description and not clipboard and not has_stdin

        # Get input from various sources
        user_input = get_input(
            direct_input=event_description,
            use_clipboard=clipboard,
            use_editor=use_editor,
        )

        if not user_input:
            format_no_input_warning(console)
            raise typer.Exit(code=1)

        # Create events using Claude agent
        result = create_events(
            user_input=user_input,
            calendar="primary",
            console=console
        )

        # Display result
        console.print(result)
        console.print()

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        format_error(str(e), console)
        raise typer.Exit(code=1)


@app.command(name="add")
def add_command(
    event_description: Optional[str] = typer.Argument(
        None,
        help="Event description in natural language, or URL to fetch"
    ),
    clipboard: bool = typer.Option(
        False,
        "--clipboard",
        "-c",
        help="Read event description from clipboard (pbpaste)"
    ),
    calendar: str = typer.Option(
        "primary",
        "--calendar",
        help="Target calendar (default: primary)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.RICH,
        "--output-format",
        help="Output format"
    ),
) -> None:
    """Add events to Google Calendar using natural language.

    [bold cyan]EXAMPLES[/bold cyan]:
      [dim]$[/dim] gcallm "Coffee with Sarah tomorrow at 2pm"
      [dim]$[/dim] gcallm "https://www.aiandsoul.org/..."
      [dim]$[/dim] gcallm --clipboard
      [dim]$[/dim] pbpaste | gcallm
      [dim]$[/dim] cat events.txt | gcallm
      [dim]$[/dim] gcallm  # Opens editor
    """
    try:
        # Determine if we should use editor mode
        use_editor = not event_description and not clipboard

        # Get input from various sources
        user_input = get_input(
            direct_input=event_description,
            use_clipboard=clipboard,
            use_editor=use_editor,
        )

        if not user_input:
            format_no_input_warning(console)
            raise typer.Exit(code=1)

        # Create events using Claude agent
        result = create_events(
            user_input=user_input,
            calendar=calendar,
            console=console
        )

        # Display result
        if output_format == OutputFormat.JSON:
            console.print_json(data={"success": True, "result": result})
        else:
            console.print(result)
            console.print()

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        format_error(str(e), console)
        raise typer.Exit(code=1)


@app.command()
def verify() -> None:
    """Verify Google Calendar MCP setup.

    [bold cyan]EXAMPLE[/bold cyan]:
      [dim]$[/dim] gcallm verify
    """
    try:
        console.print("=" * 60)
        console.print("gcallm Setup Verification")
        console.print("=" * 60)
        console.print()

        # Try to get current time via MCP (basic connectivity test)
        from gcallm.agent import CalendarAgent
        agent = CalendarAgent(console=console, model="haiku")

        with console.status("[bold green]Checking Google Calendar MCP...", spinner="dots"):
            # Simple test: get current time
            result = agent.run("What is the current date and time?")

        if result:
            console.print("[green]✓[/green] Google Calendar MCP: Working")
            console.print("[green]✓[/green] Claude Agent SDK: Working")
            console.print()
            console.print("[green]✅ All checks passed![/green]")
            console.print()
            console.print("You're ready to use gcallm!")
            console.print("Try: [cyan]gcallm \"Meeting tomorrow at 3pm\"[/cyan]")
        else:
            console.print("[red]✗[/red] Google Calendar MCP: Not responding")
            console.print()
            console.print("[yellow]Please ensure:[/yellow]")
            console.print("  1. Google Calendar MCP is configured")
            console.print("  2. You've authenticated with Google Calendar")
            console.print()
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]✗ Verification failed: {e}[/red]")
        console.print()
        console.print("[yellow]Troubleshooting:[/yellow]")
        console.print("  1. Check: [cyan]claude mcp list[/cyan]")
        console.print("  2. Ensure google-calendar MCP is installed and connected")
        console.print("  3. Try: [cyan]claude mcp get google-calendar[/cyan]")
        console.print()
        raise typer.Exit(code=1)


@app.command()
def status() -> None:
    """Show Google Calendar status.

    [bold cyan]EXAMPLE[/bold cyan]:
      [dim]$[/dim] gcallm status
    """
    try:
        console.print("=" * 60)
        console.print("Google Calendar Status")
        console.print("=" * 60)
        console.print()

        from gcallm.agent import CalendarAgent
        agent = CalendarAgent(console=console, model="haiku")

        with console.status("[bold green]Fetching calendar info...", spinner="dots"):
            result = agent.run("List my available calendars")

        console.print(result)
        console.print()

    except Exception as e:
        format_error(str(e), console)
        raise typer.Exit(code=1)


@app.command()
def calendars() -> None:
    """List available calendars.

    [bold cyan]EXAMPLE[/bold cyan]:
      [dim]$[/dim] gcallm calendars
    """
    try:
        console.print("=" * 60)
        console.print("Available Calendars")
        console.print("=" * 60)
        console.print()

        from gcallm.agent import CalendarAgent
        agent = CalendarAgent(console=console, model="haiku")

        with console.status("[bold green]Fetching calendars...", spinner="dots"):
            result = agent.run("Show me all my calendars with their names and IDs")

        console.print(result)
        console.print()

    except Exception as e:
        format_error(str(e), console)
        raise typer.Exit(code=1)


# Intercept execution to handle default behavior
def main():
    """Main CLI entry point with default command handling."""
    # Check if we have stdin data
    has_stdin = not sys.stdin.isatty()

    if len(sys.argv) == 1:
        if has_stdin:
            # Stdin data with no args - treat as event input
            default_command()
        else:
            # No args and no stdin - show help
            app()
    elif sys.argv[1] not in ["verify", "status", "calendars", "add", "--help", "-h", "--install-completion", "--show-completion"]:
        # Unknown command - treat as event description
        default_command()
    else:
        # Known command - let Typer handle it
        app()


if __name__ == "__main__":
    main()

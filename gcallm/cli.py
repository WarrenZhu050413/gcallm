#!/usr/bin/env python3
"""Command-line interface for gcallm."""

import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from gcallm.agent import create_events
from gcallm.formatter import (
    format_error,
    format_event_response,
    format_no_input_warning,
)
from gcallm.helpers.input import (
    InputContext,
    handle_clipboard_input,
    handle_direct_input,
    handle_editor_input,
    handle_screenshot_input,
    handle_stdin_input,
)


# Known subcommands (used by both default_command and main routing)
KNOWN_COMMANDS = [
    "verify",
    "ask",
    "calendars",
    "add",
    "setup",
    "config",
]

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
    if args and args[0] in KNOWN_COMMANDS:
        return  # Let Typer handle it

    # Otherwise, treat as event description
    event_description = " ".join(args) if args else None
    clipboard = "--clipboard" in args or "-c" in args
    interactive = "--interactive" in args or "-i" in args

    # Filter out flags from event description
    if event_description:
        event_description = " ".join([arg for arg in args if not arg.startswith("-")])
        if not event_description:
            event_description = None

    try:
        # Use composable input handlers (same as add_command)
        context = InputContext()

        # Text input (priority waterfall: direct → stdin → clipboard)
        context.text_input = (
            handle_direct_input(event_description)
            or handle_stdin_input()
            or handle_clipboard_input(clipboard)
        )

        # Only open editor if no text input
        if not context.text_input:
            context.text_input = handle_editor_input()

        # Validate
        if not context.has_any_input():
            format_no_input_warning(console)
            raise typer.Exit(code=1)

        # Create events using Claude agent
        result = create_events(
            user_input=context.text_input,
            screenshot_paths=None,
            console=console,
            interactive=interactive,
        )

        # Display result with Rich formatting
        format_event_response(result, console)

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        format_error(str(e), console)
        raise typer.Exit(code=1)


@app.command(name="add")
def add_command(
    event_description: Optional[str] = typer.Argument(
        None, help="Event description in natural language, or URL to fetch"
    ),
    clipboard: bool = typer.Option(
        False,
        "--clipboard",
        "-c",
        help="Read event description from clipboard (pbpaste)",
    ),
    screenshot: bool = typer.Option(
        False,
        "-s",
        help="Use latest screenshot from Desktop",
    ),
    screenshots: Optional[int] = typer.Option(
        None,
        "--screenshots",
        "-ss",
        help="Use N latest screenshots from Desktop",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Check for conflicts and ask before creating events",
    ),
    calendar: str = typer.Option(
        "primary", "--calendar", help="Target calendar (default: primary)"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.RICH, "--output-format", help="Output format"
    ),
) -> None:
    """Add events to Google Calendar using natural language or screenshots.

    [bold cyan]EXAMPLES[/bold cyan]:
      [dim]$[/dim] gcallm "Coffee with Sarah tomorrow at 2pm"
      [dim]$[/dim] gcallm "https://www.aiandsoul.org/..."
      [dim]$[/dim] gcallm --clipboard
      [dim]$[/dim] gcallm -s              # Use latest screenshot
      [dim]$[/dim] gcallm -ss 3           # Use latest 3 screenshots
      [dim]$[/dim] gcallm --interactive   # Check for conflicts first
      [dim]$[/dim] gcallm -i "Meeting tomorrow" # Interactive mode
      [dim]$[/dim] pbpaste | gcallm
      [dim]$[/dim] cat events.txt | gcallm
      [dim]$[/dim] gcallm  # Opens editor
    """
    try:
        # 1. Gather all inputs using composable handlers
        context = InputContext()

        # Screenshots (independent handler)
        # Combine -s (single) and --screenshots (multiple) flags
        screenshot_count = 1 if screenshot else screenshots
        context.screenshot_paths = handle_screenshot_input(
            screenshots=screenshot_count, console=console
        )

        # Text input (priority waterfall: direct → stdin → clipboard)
        context.text_input = (
            handle_direct_input(event_description)
            or handle_stdin_input()
            or handle_clipboard_input(clipboard)
        )

        # Only open editor if no other text input and no screenshots
        if not context.text_input and not context.screenshot_paths:
            context.text_input = handle_editor_input()

        # 2. Validate - must have at least one input source
        if not context.has_any_input():
            format_no_input_warning(console)
            raise typer.Exit(code=1)

        # 3. Default prompt if only screenshots provided
        if not context.text_input and context.screenshot_paths:
            context.text_input = (
                "Please analyze the screenshot(s) and create calendar events."
            )

        # 4. Create events using Claude agent
        result = create_events(
            user_input=context.text_input,
            screenshot_paths=context.screenshot_paths,
            console=console,
            interactive=interactive,
        )

        # Display result
        if output_format == OutputFormat.JSON:
            console.print_json(data={"success": True, "result": result})
        else:
            format_event_response(result, console)

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

        with console.status(
            "[bold green]Checking Google Calendar MCP...", spinner="dots"
        ):
            # Simple test: get current time
            result = agent.run("What is the current date and time?")

        if result:
            console.print("[green]✓[/green] Google Calendar MCP: Working")
            console.print("[green]✓[/green] Claude Agent SDK: Working")
            console.print()
            console.print("[green]✅ All checks passed![/green]")
            console.print()
            console.print("You're ready to use gcallm!")
            console.print('Try: [cyan]gcallm "Meeting tomorrow at 3pm"[/cyan]')
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
def ask(
    question: str = typer.Argument(..., help="Question about your calendar"),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Model to use (haiku, sonnet, opus)"
    ),
) -> None:
    """Ask Claude questions about your Google Calendar.

    [bold cyan]EXAMPLES[/bold cyan]:
      [dim]$[/dim] gcallm ask "What meetings do I have tomorrow?"
      [dim]$[/dim] gcallm ask "List my calendars"
      [dim]$[/dim] gcallm ask "Do I have any conflicts this week?"
      [dim]$[/dim] gcallm ask "Show events on Friday" -m sonnet
    """
    try:
        from gcallm.agent import CalendarAgent
        from gcallm.config import get_model

        # Use provided model or fall back to config
        agent_model = model or get_model()

        agent = CalendarAgent(console=console, model=agent_model)

        with console.status("[bold green]Processing question...", spinner="dots"):
            result = agent.run(question)

        console.print(result)
        console.print()

    except Exception as e:
        format_error(str(e), console)
        raise typer.Exit(code=1)


@app.command()
def calendars() -> None:
    """List available calendars (convenience alias for 'ask').

    [bold cyan]EXAMPLE[/bold cyan]:
      [dim]$[/dim] gcallm calendars
    """
    try:
        from gcallm.agent import CalendarAgent

        agent = CalendarAgent(console=console, model="haiku")

        with console.status("[bold green]Fetching calendars...", spinner="dots"):
            result = agent.run("List all my calendars with names and IDs")

        console.print(result)
        console.print()

    except Exception as e:
        format_error(str(e), console)
        raise typer.Exit(code=1)


@app.command()
def setup(
    oauth_path: Optional[str] = typer.Argument(
        None, help="Path to OAuth credentials JSON file"
    ),
) -> None:
    """Configure OAuth credentials path.

    [bold cyan]EXAMPLES[/bold cyan]:
      [dim]$[/dim] gcallm setup ~/gcp-oauth.keys.json
      [dim]$[/dim] gcallm setup    [dim]# Interactive prompt[/dim]
    """
    from pathlib import Path

    from gcallm.config import get_oauth_credentials_path, set_oauth_credentials_path

    try:
        # If no path provided, ask for it
        if not oauth_path:
            current = get_oauth_credentials_path()
            if current:
                console.print(f"[dim]Current OAuth path:[/dim] {current}")
                console.print()

            oauth_path = typer.prompt("Enter path to OAuth credentials JSON file")

        # Expand and validate path
        oauth_path_expanded = Path(oauth_path).expanduser().resolve()

        if not oauth_path_expanded.exists():
            console.print(f"[red]✗ File not found:[/red] {oauth_path_expanded}")
            raise typer.Exit(code=1)

        if not oauth_path_expanded.is_file():
            console.print(f"[red]✗ Not a file:[/red] {oauth_path_expanded}")
            raise typer.Exit(code=1)

        # Save to config
        set_oauth_credentials_path(str(oauth_path_expanded))

        console.print()
        console.print("[green]✓[/green] OAuth credentials path configured:")
        console.print(f"  {oauth_path_expanded}")
        console.print()
        console.print("[dim]gcallm will now automatically use these credentials[/dim]")
        console.print()

    except typer.Abort:
        console.print("\n[yellow]Cancelled[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        format_error(str(e), console)
        raise typer.Exit(code=1)


@app.command()
def config(
    setting: Optional[str] = typer.Argument(
        None, help="Setting to configure (model, prompt, show)"
    ),
    value: Optional[str] = typer.Argument(None, help="Value to set (for model)"),
    clear: bool = typer.Option(False, "--clear", help="Clear/reset the setting"),
) -> None:
    """Configure gcallm settings (model, prompt).

    [bold cyan]EXAMPLES[/bold cyan]:
      [dim]$[/dim] gcallm config show              [dim]# Show current configuration[/dim]
      [dim]$[/dim] gcallm config model haiku       [dim]# Set model to haiku[/dim]
      [dim]$[/dim] gcallm config model sonnet      [dim]# Set model to sonnet[/dim]
      [dim]$[/dim] gcallm config model opus        [dim]# Set model to opus[/dim]
      [dim]$[/dim] gcallm config prompt            [dim]# Edit custom system prompt[/dim]
      [dim]$[/dim] gcallm config prompt --clear    [dim]# Reset to default prompt[/dim]
    """
    import tempfile

    from gcallm.agent import SYSTEM_PROMPT
    from gcallm.config import (
        clear_custom_system_prompt,
        get_custom_system_prompt,
        get_model,
        get_oauth_credentials_path,
        set_custom_system_prompt,
        set_model,
    )
    from gcallm.helpers.input import open_editor

    try:
        # Handle 'show' subcommand
        if setting == "show" or setting is None:
            console.print()
            console.print("[bold cyan]Current Configuration[/bold cyan]")
            console.print()

            # Show model
            current_model = get_model()
            console.print(f"[dim]Model:[/dim] {current_model}")

            # Show custom prompt status
            custom_prompt = get_custom_system_prompt()
            if custom_prompt:
                prompt_preview = (
                    custom_prompt[:50] + "..."
                    if len(custom_prompt) > 50
                    else custom_prompt
                )
                console.print(f"[dim]Custom Prompt:[/dim] {prompt_preview}")
            else:
                console.print(
                    "[dim]Custom Prompt:[/dim] [yellow]Using default[/yellow]"
                )

            # Show OAuth path
            oauth_path = get_oauth_credentials_path()
            if oauth_path:
                console.print(f"[dim]OAuth Credentials:[/dim] {oauth_path}")
            else:
                console.print(
                    "[dim]OAuth Credentials:[/dim] [yellow]Not configured[/yellow]"
                )

            console.print()
            return

        # Handle 'model' subcommand
        if setting == "model":
            if not value:
                console.print(
                    "[red]Error:[/red] Please specify a model (haiku, sonnet, opus)"
                )
                console.print("[dim]Example:[/dim] gcallm config model haiku")
                raise typer.Exit(code=1)

            try:
                set_model(value)
                console.print()
                console.print(f"[green]✓[/green] Model set to: [bold]{value}[/bold]")
                console.print()
            except ValueError as e:
                console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(code=1)
            return

        # Handle 'prompt' subcommand
        if setting == "prompt":
            if clear:
                # Reset to default
                clear_custom_system_prompt()
                console.print()
                console.print("[green]✓[/green] System prompt reset to default")
                console.print()
                return

            # Get current custom prompt or default
            current_prompt = get_custom_system_prompt() or SYSTEM_PROMPT

            # Write to temp file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as tf:
                tf.write(current_prompt)
                tf.write("\n\n")
                tf.write("# Edit the system prompt above\n")
                tf.write("# Lines starting with # will be ignored\n")
                tf.write("# Save and quit to update the prompt\n")
                temp_path = tf.name

            try:
                # Open editor
                console.print()
                console.print(
                    "[cyan]Opening editor to customize system prompt...[/cyan]"
                )
                console.print()

                new_prompt = open_editor(temp_path)

                if not new_prompt or new_prompt.strip() == "":
                    console.print("[yellow]Prompt editing cancelled[/yellow]")
                    return

                # Save custom prompt
                set_custom_system_prompt(new_prompt)

                console.print()
                console.print("[green]✓[/green] System prompt updated")
                console.print()
                console.print(
                    "[dim]Use 'gcallm config prompt --clear' to revert to default[/dim]"
                )
                console.print()

            finally:
                # Clean up temp file
                Path(temp_path).unlink(missing_ok=True)

            return

        # Unknown setting
        console.print(f"[red]Error:[/red] Unknown setting: {setting}")
        console.print("[dim]Valid settings:[/dim] model, prompt, show")
        raise typer.Exit(code=1)

    except typer.Abort:
        console.print("\n[yellow]Cancelled[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        if "Invalid model" not in str(e):
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
    elif sys.argv[1] not in KNOWN_COMMANDS + [
        "--help",
        "-h",
        "--install-completion",
        "--show-completion",
    ]:
        # Unknown command - treat as event description
        default_command()
    else:
        # Known command - let Typer handle it
        app()


if __name__ == "__main__":
    main()

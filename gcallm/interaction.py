"""User interaction handlers for interactive mode."""

from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm

from gcallm.conflicts import ConflictReport


def display_conflict_report(report: ConflictReport, console: Console) -> None:
    """Display a nicely formatted conflict report to the user.

    Args:
        report: Parsed conflict report
        console: Rich console for output
    """
    # Display the full response as markdown in a panel
    md = Markdown(report.phase1_response)

    if report.is_important:
        console.print()
        console.print(
            Panel(
                md,
                title="[yellow]⚠️  Scheduling Conflicts Detected[/yellow]",
                border_style="yellow",
            )
        )
    else:
        console.print()
        console.print(
            Panel(
                md,
                title="[cyan]📋 Event Analysis[/cyan]",
                border_style="cyan",
            )
        )


def ask_user_to_proceed(
    report: ConflictReport, console: Console
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

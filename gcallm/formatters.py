"""Rich output formatters for gcallm."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional


def format_error(error_msg: str, console: Optional[Console] = None) -> None:
    """Format and display error message.

    Args:
        error_msg: Error message to display
        console: Rich console for output
    """
    console = console or Console()
    console.print()
    console.print(Panel(
        f"[red]{error_msg}[/red]",
        title="❌ Error",
        border_style="red"
    ))
    console.print()


def format_no_input_warning(console: Optional[Console] = None) -> None:
    """Display warning when no input provided.

    Args:
        console: Rich console for output
    """
    console = console or Console()
    console.print()
    console.print("[yellow]⚠️  No input provided[/yellow]")
    console.print()
    console.print("Usage:")
    console.print("  [cyan]gcallm \"Meeting tomorrow at 3pm\"[/cyan]  # Direct input")
    console.print("  [cyan]gcallm --clipboard[/cyan]                  # From clipboard")
    console.print("  [cyan]pbpaste | gcallm[/cyan]                    # From stdin")
    console.print("  [cyan]gcallm[/cyan]                              # Open editor")
    console.print()


def format_success_message(message: str, console: Optional[Console] = None) -> None:
    """Format and display success message.

    Args:
        message: Success message
        console: Rich console for output
    """
    console = console or Console()
    console.print()
    console.print(Panel(
        f"[green]{message}[/green]",
        title="✅ Success",
        border_style="green"
    ))
    console.print()

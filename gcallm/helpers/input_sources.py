"""Composable input source handlers for gcallm.

Each handler:
- Returns the input data if applicable, None otherwise
- Handles its own errors with user-friendly messages
- Is independently testable
- Can be composed together naturally
"""

from typing import Optional

from rich.console import Console

from gcallm.formatter import format_error
from gcallm.helpers.input import get_from_clipboard, get_from_stdin, open_editor
from gcallm.screenshot import find_recent_screenshots


def handle_screenshot_input(
    screenshot: bool,
    screenshots: Optional[int],
    console: Optional[Console] = None,
) -> Optional[list[str]]:
    """Handle screenshot input source.

    Args:
        screenshot: Single screenshot flag
        screenshots: Multiple screenshots count
        console: Rich console for output

    Returns:
        List of screenshot paths if applicable, None otherwise
    """
    # Not using screenshot input
    if not screenshot and screenshots is None:
        return None

    # Determine count
    count = screenshots if screenshots is not None else 1

    # Find screenshots
    screenshot_paths = find_recent_screenshots(count=count, directory=None)

    if not screenshot_paths:
        console = console or Console()
        format_error(
            "No screenshots found in ~/Desktop. "
            "Take a screenshot (⌘+Shift+4) and try again.",
            console,
        )
        return None

    return screenshot_paths


def handle_direct_input(event_description: Optional[str]) -> Optional[str]:
    """Handle direct text input.

    Args:
        event_description: Text input from command line

    Returns:
        Text if provided, None otherwise
    """
    if event_description and event_description.strip():
        return event_description
    return None


def handle_stdin_input() -> Optional[str]:
    """Handle stdin input source.

    Returns:
        Text from stdin if available, None otherwise
    """
    return get_from_stdin()


def handle_clipboard_input(clipboard: bool) -> Optional[str]:
    """Handle clipboard input source.

    Args:
        clipboard: Whether to use clipboard

    Returns:
        Clipboard content if flag is set and content exists, None otherwise
    """
    if not clipboard:
        return None
    return get_from_clipboard()


def handle_editor_input() -> Optional[str]:
    """Handle editor input source.

    Returns:
        Content from editor if provided, None otherwise
    """
    return open_editor()

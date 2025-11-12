"""Consolidated input handling for gcallm.

This module provides:
1. InputContext dataclass - container for all input sources
2. Low-level input functions - stdin, clipboard, editor
3. Composable input handlers - screenshot, direct, stdin, clipboard, editor
4. Legacy get_input function - for backward compatibility
"""

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console

from gcallm.formatter import format_error
from gcallm.helpers.screenshot import find_recent_screenshots


# ============================================================================
# InputContext - Container for all input sources
# ============================================================================


@dataclass
class InputContext:
    """Container for all input sources.

    Attributes:
        text_input: Text description of event(s)
        screenshot_paths: List of screenshot file paths to analyze
    """

    text_input: Optional[str] = None
    screenshot_paths: Optional[list[str]] = None

    def has_any_input(self) -> bool:
        """Check if context has any input (text or screenshots).

        Returns:
            True if either text_input or screenshot_paths is non-empty
        """
        return bool(self.text_input or self.screenshot_paths)


# ============================================================================
# Low-level input functions
# ============================================================================


def get_from_stdin() -> Optional[str]:
    """Read input from stdin if available.

    Returns:
        Input text from stdin, or None if stdin is a TTY (no piped input)
    """
    if not sys.stdin.isatty():
        # stdin has piped data
        content = sys.stdin.read().strip()
        return content if content else None
    return None


def get_from_clipboard() -> Optional[str]:
    """Read input from clipboard using pbpaste.

    Returns:
        Clipboard content, or None if clipboard is empty or pbpaste fails
    """
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        content = result.stdout.strip()
        return content if content else None
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return None


def open_editor(file_path: Optional[str] = None) -> Optional[str]:
    """Open editor for a specific file path or create temp file.

    Args:
        file_path: Path to file to edit (creates temp if None)

    Returns:
        Content from editor, or None if cancelled
    """
    editor: str = os.environ.get("EDITOR", "nano")

    if file_path:
        # Edit existing file
        edit_path = Path(file_path)
    else:
        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as tf:
            edit_path = Path(tf.name)
            # Write helpful prompt
            tf.write("\n\n\n")
            tf.write("# Enter your event description above\n")
            tf.write("# Lines starting with # will be ignored\n")
            tf.write("# Save and quit to create events\n")
            tf.flush()

    try:
        # Open editor
        subprocess.run([editor, str(edit_path)], check=True)

        # Read content
        content = edit_path.read_text()

        # Filter out comment lines and empty lines
        lines = [
            line
            for line in content.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]

        result = "\n".join(lines).strip()
        return result if result else None

    except (subprocess.CalledProcessError, KeyboardInterrupt):
        return None
    finally:
        # Clean up temp file if we created it
        if not file_path and edit_path.exists():
            edit_path.unlink()


def get_from_editor() -> Optional[str]:
    """Open default editor and return content.

    Uses $EDITOR environment variable, falls back to nano.

    Returns:
        Content from editor, or None if user didn't write anything or cancelled
    """
    return open_editor()


# ============================================================================
# Composable input handlers
# ============================================================================


def handle_screenshot_input(
    screenshots: Optional[int],
    console: Optional[Console] = None,
) -> Optional[list[str]]:
    """Handle screenshot input source.

    Args:
        screenshots: Number of screenshots to use (None = don't use screenshots)
        console: Rich console for output

    Returns:
        List of screenshot paths if applicable, None otherwise
    """
    # Not using screenshot input
    if screenshots is None:
        return None

    # Find screenshots
    screenshot_paths = find_recent_screenshots(count=screenshots, directory=None)

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


# ============================================================================
# Legacy function for backward compatibility
# ============================================================================


def get_input(
    direct_input: Optional[str] = None,
    use_clipboard: bool = False,
    use_editor: bool = False,
) -> Optional[str]:
    """Get input from various sources in priority order.

    Priority:
    1. Direct input (command line argument)
    2. stdin (if piped)
    3. Clipboard (if --clipboard flag)
    4. Editor (if no args and no stdin)

    Args:
        direct_input: Direct text input from command line
        use_clipboard: Whether to use clipboard
        use_editor: Whether to open editor

    Returns:
        Input text, or None if no input available
    """
    # Priority 1: Direct input
    if direct_input:
        return direct_input.strip()

    # Priority 2: stdin (piped input)
    stdin_input = get_from_stdin()
    if stdin_input:
        return stdin_input

    # Priority 3: Clipboard
    if use_clipboard:
        clipboard_input = get_from_clipboard()
        if clipboard_input:
            return clipboard_input
        # If clipboard flag was explicit but empty, return None
        return None

    # Priority 4: Editor (no args and no stdin)
    if use_editor:
        return get_from_editor()

    return None

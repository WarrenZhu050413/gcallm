"""Input context for gcallm operations."""

from dataclasses import dataclass
from typing import Optional


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

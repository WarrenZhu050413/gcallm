"""Screenshot discovery and management for event creation."""

import os
from pathlib import Path


def find_recent_screenshots(count: int = 1, directory: str = "~/Desktop") -> list[str]:
    """Find n most recent screenshots from directory.

    Args:
        count: Number of screenshots to return (default: 1)
        directory: Directory to search (default: ~/Desktop)

    Returns:
        List of absolute paths to screenshots, sorted newest-first

    Raises:
        FileNotFoundError: If directory doesn't exist
        ValueError: If no screenshots found
    """
    desktop = Path(directory).expanduser()

    if not desktop.exists():
        raise FileNotFoundError(f"Directory not found: {desktop}")

    # Find all Screenshot*.png files
    screenshots = list(desktop.glob("Screenshot*.png"))

    if not screenshots:
        raise ValueError(f"No screenshots found in {desktop}")

    # Sort by modification time (newest first)
    screenshots.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return [str(p) for p in screenshots[:count]]

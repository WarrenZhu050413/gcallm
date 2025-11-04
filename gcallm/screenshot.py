"""Screenshot discovery and management for event creation."""

from pathlib import Path


def find_recent_screenshots(count: int = 1, directory: str = "~/Desktop") -> list[str]:
    """Find n most recent screenshots from directory.

    Supports multiple macOS locales:
    - English: Screenshot*.png
    - Spanish: Captura de pantalla*.png
    - French: Capture d'écran*.png
    - German: Bildschirmfoto*.png

    Args:
        count: Number of screenshots to return (default: 1)
        directory: Directory to search (default: ~/Desktop)

    Returns:
        List of absolute paths to screenshots, sorted newest-first

    Raises:
        FileNotFoundError: If directory doesn't exist
        ValueError: If no screenshots found with instructions for Claude
    """
    desktop = Path(directory).expanduser()

    if not desktop.exists():
        raise FileNotFoundError(f"Directory not found: {desktop}")

    # Support multiple locale patterns for macOS screenshots
    patterns = [
        "Screenshot*.png",  # English (US, UK, etc.)
        "Captura de pantalla*.png",  # Spanish
        "Capture d'écran*.png",  # French
        "Bildschirmfoto*.png",  # German
    ]

    screenshots = []
    for pattern in patterns:
        screenshots.extend(desktop.glob(pattern))

    if not screenshots:
        # Provide helpful error with manual fallback instructions
        raise ValueError(
            f"No screenshots found in {desktop}. "
            f"CLAUDE_FALLBACK_INSTRUCTION: The screenshot pattern matching failed. "
            f"Please manually list all .png files in {desktop}, sort by modification time, "
            f"and select the most recent file(s) that appear to be screenshots. "
            f"Use those paths to read the images and extract event information."
        )

    # Sort by modification time (newest first)
    screenshots.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return [str(p) for p in screenshots[:count]]

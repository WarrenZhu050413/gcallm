"""Screenshot discovery and management for event creation."""

import shutil
from datetime import datetime
from pathlib import Path


def _has_problematic_chars(path: Path) -> bool:
    """Check if filename contains characters that cause Read tool failures.

    Problematic characters include:
    - Parentheses: () - Common in Spanish "a la(s)"
    - Spanish time format: "p.m." or "a.m." with double period before extension

    Args:
        path: Path to check

    Returns:
        True if filename has problematic characters
    """
    name = path.name
    # Check for parentheses (common in Spanish "a la(s)")
    if "(" in name or ")" in name:
        return True
    # Check for Spanish time format pattern: "p.m." or "a.m." followed by another period
    # e.g., "3.27.08 p.m..png" has double period before extension
    if " p.m.." in name or " a.m.." in name:
        return True
    return False


def _sanitize_screenshot_path(path: Path, index: int = 1) -> Path:
    """Create a sanitized copy of screenshot with clean filename.

    Args:
        path: Original screenshot path with problematic characters
        index: Index number for temp filename

    Returns:
        Path to sanitized copy
    """
    # Create temp directory for sanitized screenshots
    temp_dir = Path.home() / "Desktop" / ".gcallm_temp_screenshots"
    temp_dir.mkdir(exist_ok=True)

    # Generate clean filename with date and index
    date_str = datetime.now().strftime("%Y-%m-%d")
    clean_name = f"{date_str}-screenshot-{index}.png"
    sanitized_path = temp_dir / clean_name

    # Copy (not move) to preserve original
    shutil.copy2(str(path), str(sanitized_path))

    return sanitized_path


def find_recent_screenshots(count: int = 1, directory: str = "~/Desktop") -> list[str]:
    """Find n most recent screenshots from directory.

    Supports multiple macOS locales:
    - English: Screenshot*.png
    - Spanish: Captura de pantalla*.png
    - French: Capture d'écran*.png
    - German: Bildschirmfoto*.png

    Automatically sanitizes filenames with problematic characters (parentheses,
    Spanish/French time formats) by creating clean copies in a temp directory.

    Args:
        count: Number of screenshots to return (default: 1)
        directory: Directory to search (default: ~/Desktop)

    Returns:
        List of absolute paths to screenshots (sanitized if needed), sorted newest-first

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

    # Take requested count
    selected = screenshots[:count]

    # Sanitize paths with problematic characters
    result_paths = []
    for idx, screenshot in enumerate(selected, start=1):
        if _has_problematic_chars(screenshot):
            # Create sanitized copy
            sanitized = _sanitize_screenshot_path(screenshot, index=idx)
            result_paths.append(str(sanitized))
        else:
            # Use original path
            result_paths.append(str(screenshot))

    return result_paths

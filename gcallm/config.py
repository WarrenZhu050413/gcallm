"""Configuration management for gcallm."""

import json
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".config" / "gcallm"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from file.

    Returns:
        Configuration dictionary with oauth_credentials_path and custom_system_prompt
    """
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(config: dict):
    """Save configuration to file.

    Args:
        config: Configuration dictionary to save
    """
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_oauth_credentials_path() -> Optional[str]:
    """Get the configured OAuth credentials path.

    Falls back to default locations if not explicitly configured:
    1. ~/.gmail-mcp/gcp-oauth.keys.json (common location for gmail-mcp)
    2. ~/.config/gcallm/gcp-oauth.keys.json
    3. ~/gcp-oauth.keys.json

    Returns:
        Path to OAuth credentials file, or None if not found
    """
    config = load_config()
    configured_path = config.get("oauth_credentials_path")

    if configured_path:
        return configured_path

    # Try default locations
    default_locations = [
        Path.home() / ".gmail-mcp" / "gcp-oauth.keys.json",
        Path.home() / ".config" / "gcallm" / "gcp-oauth.keys.json",
        Path.home() / "gcp-oauth.keys.json",
    ]

    for path in default_locations:
        if path.exists() and path.is_file():
            return str(path)

    return None


def set_oauth_credentials_path(path: str):
    """Set the OAuth credentials path.

    Args:
        path: Path to OAuth credentials file
    """
    config = load_config()
    config["oauth_credentials_path"] = str(Path(path).expanduser().resolve())
    save_config(config)


def get_custom_system_prompt() -> Optional[str]:
    """Get the custom system prompt.

    Returns:
        Custom system prompt, or None if not configured
    """
    config = load_config()
    return config.get("custom_system_prompt")


def set_custom_system_prompt(prompt: str):
    """Set the custom system prompt.

    Args:
        prompt: Custom system prompt text
    """
    config = load_config()
    config["custom_system_prompt"] = prompt
    save_config(config)


def clear_custom_system_prompt():
    """Clear the custom system prompt (revert to default)."""
    config = load_config()
    if "custom_system_prompt" in config:
        del config["custom_system_prompt"]
        save_config(config)


def get_model() -> str:
    """Get the configured Claude model.

    Returns:
        Model name (haiku, sonnet, opus), defaults to 'haiku'
    """
    config = load_config()
    return config.get("model", "haiku")


def set_model(model: str):
    """Set the Claude model.

    Args:
        model: Model name (haiku, sonnet, opus)
    """
    valid_models = ["haiku", "sonnet", "opus"]
    if model not in valid_models:
        raise ValueError(f"Invalid model: {model}. Must be one of: {valid_models}")
    config = load_config()
    config["model"] = model
    save_config(config)

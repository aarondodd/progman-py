"""Configuration helpers for Program Manager.

Manages config directory, version check timestamps, and GitHub config defaults.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional


def get_config_dir() -> Path:
    """Get the progman config directory, creating it if needed."""
    config_dir = Path.home() / ".progman"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_version_check_file() -> Path:
    """Get the path to the version check timestamp file."""
    return get_config_dir() / ".version_check"


def get_last_version_check() -> Optional[datetime]:
    """Read the last version check timestamp."""
    check_file = get_version_check_file()
    if not check_file.exists():
        return None

    try:
        with open(check_file, "r", encoding="utf-8") as f:
            timestamp_str = f.read().strip()
            return datetime.fromisoformat(timestamp_str)
    except Exception:
        return None


def record_version_check() -> None:
    """Record the current time as the last version check."""
    check_file = get_version_check_file()
    try:
        with open(check_file, "w", encoding="utf-8") as f:
            f.write(datetime.now().isoformat())
    except Exception:
        pass


def get_default_github_config() -> dict:
    """Return the default GitHub configuration."""
    return {
        "owner": "aarondodd",
        "repo": "progman-py",
    }

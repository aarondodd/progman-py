"""Application model holding all groups, theme state, and config persistence."""

import json
import sys
from pathlib import Path
from typing import List, Optional

from .program_group import ProgramGroup
from .program_item import ProgramItem

# Current config version for migration support
CONFIG_VERSION = 1


class AppModel:
    """Application model holding all groups and items."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path: Path = (
            config_path if config_path is not None else Path.home() / ".progman.json"
        )
        self.config_version: int = CONFIG_VERSION
        self.dark_mode: bool = False
        self.layout_state: str = ""
        self.groups: List[ProgramGroup] = []
        self.github: dict = {
            "owner": "aarondodd",
            "repo": "progman-py",
        }
        self.load()

    def load(self) -> None:
        if not self.config_path.exists():
            self._load_default()
            self.save()
            return

        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self._load_default()
            return

        config_version = data.get("config_version", 0)
        migrated = config_version < CONFIG_VERSION
        if migrated:
            data = self._migrate(data, config_version)

        self.config_version = CONFIG_VERSION
        self.dark_mode = data.get("dark_mode", False)
        self.layout_state = data.get("layout_state", "")
        self.github = data.get("github", {
            "owner": "aarondodd",
            "repo": "progman-py",
        })

        groups_data = data.get("groups", [])
        self.groups = [ProgramGroup.from_dict(g) for g in groups_data]

        if migrated:
            self.save()

    def save(self) -> None:
        data = {
            "config_version": self.config_version,
            "dark_mode": self.dark_mode,
            "layout_state": self.layout_state,
            "github": self.github,
            "groups": [g.to_dict() for g in self.groups],
        }
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _migrate(self, data: dict, from_version: int) -> dict:
        """Migrate config from older versions to current."""
        if from_version == 0:
            data = self._migrate_v0_to_v1(data)
        return data

    @staticmethod
    def _migrate_v0_to_v1(data: dict) -> dict:
        """Migrate from v0 (original progman.py format) to v1.

        Changes:
        - 'theme' (str: "system"|"classic") -> 'dark_mode' (bool)
        - Adds 'config_version': 1
        - Adds 'github' section with defaults
        """
        old_theme = data.get("theme", "system")
        data["dark_mode"] = old_theme == "classic"
        data.pop("theme", None)

        data["config_version"] = CONFIG_VERSION
        data.setdefault("github", {
            "owner": "aarondodd",
            "repo": "progman-py",
        })
        return data

    def _load_default(self) -> None:
        """Create default config with platform-appropriate example items."""
        if sys.platform.startswith("win"):
            default_item = ProgramItem(
                title="Notepad",
                command="notepad.exe",
            )
        else:
            default_item = ProgramItem(
                title="Terminal",
                command="xterm",
            )

        self.groups = [
            ProgramGroup(
                title="Main",
                items=[default_item],
            )
        ]

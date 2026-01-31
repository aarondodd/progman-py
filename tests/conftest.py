"""Pytest configuration and shared fixtures for Program Manager tests."""

import json
import os
import sys

# Force offscreen rendering for headless testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from pathlib import Path
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def tmp_config(tmp_path):
    """Provide a temporary config file path that won't affect the real config."""
    return tmp_path / "test_progman.json"


@pytest.fixture
def sample_config(tmp_config):
    """Provide a temporary config file with sample data."""
    data = {
        "config_version": 1,
        "dark_mode": False,
        "layout_state": "",
        "github": {"owner": "aarondodd", "repo": "progman-py"},
        "groups": [
            {
                "title": "Main",
                "items": [
                    {
                        "title": "Test App",
                        "command": "echo hello",
                        "working_dir": "",
                        "icon_path": "",
                    }
                ],
            },
            {
                "title": "Development",
                "items": [
                    {
                        "title": "Editor",
                        "command": "vim",
                        "working_dir": "/tmp",
                        "icon_path": "",
                    },
                    {
                        "title": "Terminal",
                        "command": "xterm",
                        "working_dir": "",
                        "icon_path": "",
                    },
                ],
            },
        ],
    }
    with open(tmp_config, "w") as f:
        json.dump(data, f)
    return tmp_config


@pytest.fixture
def old_format_config(tmp_config):
    """Provide a v0 (old format) config file for migration testing."""
    data = {
        "theme": "classic",
        "layout_state": json.dumps([
            {"title": "Main", "geometry": [10, 20, 300, 200], "state": "normal"}
        ]),
        "groups": [
            {
                "title": "Main",
                "items": [
                    {
                        "title": "Notepad",
                        "command": "notepad.exe",
                        "working_dir": "",
                        "icon_path": "",
                    }
                ],
            }
        ],
    }
    with open(tmp_config, "w") as f:
        json.dump(data, f)
    return tmp_config

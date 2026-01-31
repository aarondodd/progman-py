"""Tests for data models: ProgramItem, ProgramGroup, AppModel."""

import json

from progman.models.program_item import ProgramItem
from progman.models.program_group import ProgramGroup
from progman.models.app_model import AppModel


class TestProgramItem:
    def test_create_basic(self):
        item = ProgramItem(title="Test", command="echo hello")
        assert item.title == "Test"
        assert item.command == "echo hello"
        assert item.working_dir == ""
        assert item.icon_path == ""

    def test_create_full(self):
        item = ProgramItem(
            title="Editor",
            command="vim",
            working_dir="/tmp",
            icon_path="/usr/share/icons/vim.png",
        )
        assert item.working_dir == "/tmp"
        assert item.icon_path == "/usr/share/icons/vim.png"

    def test_to_dict(self):
        item = ProgramItem(title="Test", command="echo")
        d = item.to_dict()
        assert d == {
            "title": "Test",
            "command": "echo",
            "working_dir": "",
            "icon_path": "",
        }

    def test_from_dict(self):
        d = {"title": "App", "command": "run", "working_dir": "/home", "icon_path": "icon.png"}
        item = ProgramItem.from_dict(d)
        assert item.title == "App"
        assert item.command == "run"
        assert item.working_dir == "/home"
        assert item.icon_path == "icon.png"

    def test_from_dict_missing_fields(self):
        d = {"title": "Minimal"}
        item = ProgramItem.from_dict(d)
        assert item.title == "Minimal"
        assert item.command == ""
        assert item.working_dir == ""

    def test_roundtrip(self):
        original = ProgramItem(title="X", command="y", working_dir="z", icon_path="w")
        restored = ProgramItem.from_dict(original.to_dict())
        assert original == restored


class TestProgramGroup:
    def test_create_empty(self):
        group = ProgramGroup(title="Empty")
        assert group.title == "Empty"
        assert group.items == []

    def test_create_with_items(self):
        items = [ProgramItem(title="A", command="a"), ProgramItem(title="B", command="b")]
        group = ProgramGroup(title="Tools", items=items)
        assert len(group.items) == 2
        assert group.items[0].title == "A"

    def test_to_dict(self):
        group = ProgramGroup(
            title="Dev",
            items=[ProgramItem(title="Editor", command="vim")],
        )
        d = group.to_dict()
        assert d["title"] == "Dev"
        assert len(d["items"]) == 1
        assert d["items"][0]["title"] == "Editor"

    def test_from_dict(self):
        d = {
            "title": "Games",
            "items": [
                {"title": "Solitaire", "command": "sol.exe"},
                {"title": "Minesweeper", "command": "mine.exe"},
            ],
        }
        group = ProgramGroup.from_dict(d)
        assert group.title == "Games"
        assert len(group.items) == 2

    def test_from_dict_empty_items(self):
        d = {"title": "Empty"}
        group = ProgramGroup.from_dict(d)
        assert group.items == []

    def test_roundtrip(self):
        original = ProgramGroup(
            title="Test",
            items=[ProgramItem(title="A", command="a")],
        )
        restored = ProgramGroup.from_dict(original.to_dict())
        assert original.title == restored.title
        assert len(original.items) == len(restored.items)
        assert original.items[0] == restored.items[0]


class TestAppModel:
    def test_load_default_when_no_config(self, tmp_config):
        model = AppModel(config_path=tmp_config)
        assert model.config_version == 1
        assert model.dark_mode is False
        assert len(model.groups) >= 1
        assert model.groups[0].title == "Main"
        # Config file should be created
        assert tmp_config.exists()

    def test_load_existing_config(self, sample_config):
        model = AppModel(config_path=sample_config)
        assert model.dark_mode is False
        assert len(model.groups) == 2
        assert model.groups[0].title == "Main"
        assert model.groups[1].title == "Development"
        assert len(model.groups[1].items) == 2

    def test_save_and_reload(self, tmp_config):
        model = AppModel(config_path=tmp_config)
        model.dark_mode = True
        model.groups.append(ProgramGroup(title="New", items=[]))
        model.save()

        model2 = AppModel(config_path=tmp_config)
        assert model2.dark_mode is True
        assert len(model2.groups) == 2
        assert model2.groups[1].title == "New"

    def test_github_config_defaults(self, tmp_config):
        model = AppModel(config_path=tmp_config)
        assert model.github["owner"] == "aarondodd"
        assert model.github["repo"] == "progman-py"

    def test_invalid_config_falls_back_to_default(self, tmp_config):
        # Write garbage
        with open(tmp_config, "w") as f:
            f.write("not json")
        model = AppModel(config_path=tmp_config)
        assert len(model.groups) >= 1

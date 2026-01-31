"""Tests for config migration from v0 to v1."""

import json

from progman.models.app_model import AppModel, CONFIG_VERSION


class TestConfigMigration:
    def test_v0_to_v1_theme_classic_becomes_dark(self, old_format_config):
        model = AppModel(config_path=old_format_config)
        assert model.dark_mode is True
        assert model.config_version == CONFIG_VERSION

    def test_v0_to_v1_theme_system_becomes_light(self, tmp_config):
        data = {
            "theme": "system",
            "layout_state": "",
            "groups": [{"title": "Main", "items": []}],
        }
        with open(tmp_config, "w") as f:
            json.dump(data, f)

        model = AppModel(config_path=tmp_config)
        assert model.dark_mode is False

    def test_v0_to_v1_preserves_groups(self, old_format_config):
        model = AppModel(config_path=old_format_config)
        assert len(model.groups) == 1
        assert model.groups[0].title == "Main"
        assert len(model.groups[0].items) == 1
        assert model.groups[0].items[0].title == "Notepad"

    def test_v0_to_v1_preserves_layout(self, old_format_config):
        model = AppModel(config_path=old_format_config)
        assert model.layout_state != ""
        layout = json.loads(model.layout_state)
        assert layout[0]["title"] == "Main"
        assert layout[0]["geometry"] == [10, 20, 300, 200]

    def test_v0_to_v1_adds_github_config(self, old_format_config):
        model = AppModel(config_path=old_format_config)
        assert model.github["owner"] == "aarondodd"
        assert model.github["repo"] == "progman-py"

    def test_v0_to_v1_saves_new_format(self, old_format_config):
        model = AppModel(config_path=old_format_config)

        with open(old_format_config) as f:
            saved = json.load(f)

        assert saved["config_version"] == CONFIG_VERSION
        assert "dark_mode" in saved
        assert "theme" not in saved
        assert "github" in saved

    def test_already_v1_no_migration(self, sample_config):
        model = AppModel(config_path=sample_config)
        assert model.config_version == CONFIG_VERSION
        assert model.dark_mode is False

    def test_missing_config_version_triggers_migration(self, tmp_config):
        """Config without config_version is treated as v0."""
        data = {
            "theme": "system",
            "groups": [{"title": "Test", "items": []}],
        }
        with open(tmp_config, "w") as f:
            json.dump(data, f)

        model = AppModel(config_path=tmp_config)
        assert model.config_version == CONFIG_VERSION

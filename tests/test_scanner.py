"""Tests for the platform-specific program scanner."""

import os
import textwrap
from pathlib import Path
from unittest.mock import patch

from progman.utils.scanner import (
    _parse_desktop_file,
    _resolve_linux_icon,
    scan_applications,
    CATEGORY_MAP,
    DiscoveredApp,
)


class TestDesktopFileParsing:
    def test_parse_valid_desktop_file(self, tmp_path):
        desktop = tmp_path / "test.desktop"
        desktop.write_text(textwrap.dedent("""\
            [Desktop Entry]
            Type=Application
            Name=Test Editor
            Exec=testeditor %F
            Icon=testeditor
            Categories=Development;TextEditor;
        """))

        app = _parse_desktop_file(desktop)
        assert app is not None
        assert app.name == "Test Editor"
        assert app.command == "testeditor"
        assert app.group == "Development"

    def test_strip_field_codes(self, tmp_path):
        desktop = tmp_path / "test.desktop"
        desktop.write_text(textwrap.dedent("""\
            [Desktop Entry]
            Type=Application
            Name=Browser
            Exec=/usr/bin/browser %u --new-window
            Categories=Network;
        """))

        app = _parse_desktop_file(desktop)
        assert app is not None
        assert "%u" not in app.command
        assert app.command == "/usr/bin/browser --new-window"

    def test_skip_nodisplay(self, tmp_path):
        desktop = tmp_path / "hidden.desktop"
        desktop.write_text(textwrap.dedent("""\
            [Desktop Entry]
            Type=Application
            Name=Hidden App
            Exec=hidden
            NoDisplay=true
        """))

        app = _parse_desktop_file(desktop)
        assert app is None

    def test_skip_hidden(self, tmp_path):
        desktop = tmp_path / "hidden.desktop"
        desktop.write_text(textwrap.dedent("""\
            [Desktop Entry]
            Type=Application
            Name=Hidden App
            Exec=hidden
            Hidden=true
        """))

        app = _parse_desktop_file(desktop)
        assert app is None

    def test_skip_non_application(self, tmp_path):
        desktop = tmp_path / "link.desktop"
        desktop.write_text(textwrap.dedent("""\
            [Desktop Entry]
            Type=Link
            Name=Some Link
            URL=https://example.com
        """))

        app = _parse_desktop_file(desktop)
        assert app is None

    def test_missing_exec(self, tmp_path):
        desktop = tmp_path / "noexec.desktop"
        desktop.write_text(textwrap.dedent("""\
            [Desktop Entry]
            Type=Application
            Name=No Exec
        """))

        app = _parse_desktop_file(desktop)
        assert app is None

    def test_category_mapping(self, tmp_path):
        for category, expected_group in [
            ("AudioVideo;", "Multimedia"),
            ("Game;", "Games"),
            ("Office;", "Office"),
            ("Utility;", "Accessories"),
        ]:
            desktop = tmp_path / f"test_{category}.desktop"
            desktop.write_text(textwrap.dedent(f"""\
                [Desktop Entry]
                Type=Application
                Name=App
                Exec=app
                Categories={category}
            """))

            app = _parse_desktop_file(desktop)
            assert app is not None
            assert app.group == expected_group

    def test_uncategorized_fallback(self, tmp_path):
        desktop = tmp_path / "nocat.desktop"
        desktop.write_text(textwrap.dedent("""\
            [Desktop Entry]
            Type=Application
            Name=No Category
            Exec=nocat
        """))

        app = _parse_desktop_file(desktop)
        assert app is not None
        assert app.group == "Uncategorized"

    def test_invalid_desktop_file(self, tmp_path):
        desktop = tmp_path / "bad.desktop"
        desktop.write_text("this is not a valid desktop file\n[invalid")

        app = _parse_desktop_file(desktop)
        assert app is None


class TestIconResolution:
    def test_absolute_path_exists(self, tmp_path):
        icon_file = tmp_path / "icon.png"
        icon_file.write_text("")
        result = _resolve_linux_icon(str(icon_file))
        assert result == str(icon_file)

    def test_absolute_path_not_exists(self):
        result = _resolve_linux_icon("/nonexistent/icon.png")
        assert result == ""

    def test_empty_icon(self):
        result = _resolve_linux_icon("")
        assert result == ""


class TestScanApplications:
    def test_returns_list(self):
        apps = scan_applications()
        assert isinstance(apps, list)

    def test_discovered_app_structure(self):
        app = DiscoveredApp(name="Test", command="test", icon_path="", group="Tools")
        assert app.name == "Test"
        assert app.command == "test"
        assert app.group == "Tools"

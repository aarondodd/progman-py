"""Tests for the platform-specific program scanner."""

import os
import struct
import textwrap
from pathlib import Path
from unittest.mock import patch

from progman.utils.scanner import (
    _parse_desktop_file,
    _parse_lnk_binary,
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


def _build_lnk(
    target_path: str = "",
    icon_location: str = "",
    relative_path: str = "",
    is_unicode: bool = True,
) -> bytes:
    """Build a minimal MS-SHLLINK binary for testing.

    Constructs a valid ShellLinkHeader + optional LinkInfo + StringData.
    """
    # --- Flags ---
    flags = 0
    has_link_info = bool(target_path)
    has_relative_path = bool(relative_path)
    has_icon_location = bool(icon_location)
    if has_link_info:
        flags |= 0x02
    if has_relative_path:
        flags |= 0x08
    if has_icon_location:
        flags |= 0x40
    if is_unicode:
        flags |= 0x80

    # --- ShellLinkHeader (76 bytes) ---
    header = struct.pack("<I", 0x4C)  # HeaderSize
    header += b"\x01\x14\x02\x00\x00\x00\x00\x00"  # LinkCLSID (first 8)
    header += b"\xc0\x00\x00\x00\x00\x00\x00\x46"  # LinkCLSID (last 8)
    header += struct.pack("<I", flags)  # LinkFlags
    header += struct.pack("<I", 0)  # FileAttributes
    header += b"\x00" * 8  # CreationTime
    header += b"\x00" * 8  # AccessTime
    header += b"\x00" * 8  # WriteTime
    header += struct.pack("<I", 0)  # FileSize
    header += struct.pack("<I", 0)  # IconIndex
    header += struct.pack("<I", 1)  # ShowCommand (SW_NORMAL)
    header += struct.pack("<H", 0)  # HotKey
    header += b"\x00" * 2  # Reserved1
    header += b"\x00" * 4  # Reserved2
    header += b"\x00" * 4  # Reserved3
    assert len(header) == 76

    body = b""

    # --- LinkInfo ---
    if has_link_info:
        # ANSI local base path
        path_bytes = target_path.encode("cp1252") + b"\x00"
        suffix_bytes = b"\x00"  # CommonPathSuffix (empty)

        link_info_header_size = 28  # no Unicode offsets
        volume_id = struct.pack("<I", 16) + struct.pack("<I", 3) + b"\x00" * 8
        volume_id_offset = link_info_header_size
        local_base_path_offset = volume_id_offset + len(volume_id)
        common_path_suffix_offset = local_base_path_offset + len(path_bytes)

        link_info_size = common_path_suffix_offset + len(suffix_bytes)

        link_info = struct.pack("<I", link_info_size)
        link_info += struct.pack("<I", link_info_header_size)
        link_info += struct.pack("<I", 0x01)  # VolumeIDAndLocalBasePath
        link_info += struct.pack("<I", volume_id_offset)
        link_info += struct.pack("<I", local_base_path_offset)
        link_info += struct.pack("<I", 0)  # CommonNetworkRelativeLinkOffset
        link_info += struct.pack("<I", common_path_suffix_offset)
        link_info += volume_id
        link_info += path_bytes
        link_info += suffix_bytes

        body += link_info

    # --- StringData ---
    def _encode_counted(s: str) -> bytes:
        if is_unicode:
            encoded = s.encode("utf-16-le")
            return struct.pack("<H", len(s)) + encoded
        else:
            encoded = s.encode("cp1252")
            return struct.pack("<H", len(s)) + encoded

    if has_relative_path:
        body += _encode_counted(relative_path)
    if has_icon_location:
        body += _encode_counted(icon_location)

    return header + body


class TestLnkBinaryParser:
    def test_parse_valid_lnk_with_target(self, tmp_path):
        lnk = tmp_path / "test.lnk"
        lnk.write_bytes(_build_lnk(target_path=r"C:\Program Files\app.exe"))

        result = _parse_lnk_binary(lnk)
        assert result is not None
        assert result["target_path"] == r"C:\Program Files\app.exe"

    def test_parse_with_icon_location(self, tmp_path):
        lnk = tmp_path / "test.lnk"
        lnk.write_bytes(
            _build_lnk(
                target_path=r"C:\app.exe",
                icon_location=r"C:\app.exe,0",
            )
        )

        result = _parse_lnk_binary(lnk)
        assert result is not None
        assert result["icon_location"] == r"C:\app.exe,0"

    def test_parse_with_relative_path_fallback(self, tmp_path):
        """When no LinkInfo target, relative_path is used as fallback."""
        lnk = tmp_path / "test.lnk"
        lnk.write_bytes(_build_lnk(relative_path=r".\subfolder\app.exe"))

        result = _parse_lnk_binary(lnk)
        assert result is not None
        assert result["target_path"] == r".\subfolder\app.exe"

    def test_parse_too_small(self, tmp_path):
        lnk = tmp_path / "tiny.lnk"
        lnk.write_bytes(b"\x00" * 10)

        result = _parse_lnk_binary(lnk)
        assert result is None

    def test_parse_bad_header_size(self, tmp_path):
        lnk = tmp_path / "bad.lnk"
        lnk.write_bytes(struct.pack("<I", 0xFF) + b"\x00" * 72)

        result = _parse_lnk_binary(lnk)
        assert result is None

    def test_parse_nonexistent_file(self, tmp_path):
        result = _parse_lnk_binary(tmp_path / "missing.lnk")
        assert result is None

    def test_parse_ansi_mode(self, tmp_path):
        lnk = tmp_path / "ansi.lnk"
        lnk.write_bytes(
            _build_lnk(target_path=r"C:\Tools\editor.exe", is_unicode=False)
        )

        result = _parse_lnk_binary(lnk)
        assert result is not None
        assert result["target_path"] == r"C:\Tools\editor.exe"


class TestScanApplications:
    def test_returns_list(self):
        apps = scan_applications()
        assert isinstance(apps, list)

    def test_discovered_app_structure(self):
        app = DiscoveredApp(name="Test", command="test", icon_path="", group="Tools")
        assert app.name == "Test"
        assert app.command == "test"
        assert app.group == "Tools"

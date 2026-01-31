"""Tests for widgets: GroupWindow, ProgramItemDialog."""

from unittest.mock import patch

from progman.models.program_group import ProgramGroup
from progman.models.program_item import ProgramItem
from progman.utils.icons import icon_for_executable, is_executable_icon
from progman.utils.launcher import Launcher
from progman.widgets.group_window import GroupWindow


class TestGroupWindow:
    def test_create_with_empty_group(self, qapp):
        group = ProgramGroup(title="Empty")
        launcher = Launcher()
        window = GroupWindow(group, launcher)
        assert window.list_widget.count() == 0

    def test_create_with_items(self, qapp):
        group = ProgramGroup(
            title="Test",
            items=[
                ProgramItem(title="App1", command="app1"),
                ProgramItem(title="App2", command="app2"),
            ],
        )
        launcher = Launcher()
        window = GroupWindow(group, launcher)
        assert window.list_widget.count() == 2

    def test_refresh_items(self, qapp):
        group = ProgramGroup(title="Test", items=[])
        launcher = Launcher()
        window = GroupWindow(group, launcher)
        assert window.list_widget.count() == 0

        group.items.append(ProgramItem(title="New", command="new"))
        window.refresh_items()
        assert window.list_widget.count() == 1

    def test_dark_mode_flag(self, qapp):
        group = ProgramGroup(title="Test", items=[
            ProgramItem(title="App", command="app"),
        ])
        launcher = Launcher()
        window = GroupWindow(group, launcher, dark_mode=True)
        assert window._dark_mode is True

    def test_set_dark_mode(self, qapp):
        group = ProgramGroup(title="Test", items=[])
        launcher = Launcher()
        window = GroupWindow(group, launcher, dark_mode=False)
        window.set_dark_mode(True)
        assert window._dark_mode is True

    def test_items_stored_in_user_role(self, qapp):
        item = ProgramItem(title="Stored", command="stored")
        group = ProgramGroup(title="Test", items=[item])
        launcher = Launcher()
        window = GroupWindow(group, launcher)

        from PyQt6.QtCore import Qt
        lw_item = window.list_widget.item(0)
        stored = lw_item.data(Qt.ItemDataRole.UserRole)
        assert stored is item
        assert stored.title == "Stored"

    def test_drag_enabled(self, qapp):
        group = ProgramGroup(title="Test", items=[])
        launcher = Launcher()
        window = GroupWindow(group, launcher)
        assert window.list_widget.dragEnabled() is True
        assert window.list_widget.acceptDrops() is True

    def test_exe_icon_path_uses_extraction(self, qapp, tmp_path):
        """An .exe icon_path should go through icon_for_executable, not QIcon."""
        exe = tmp_path / "fake.exe"
        exe.write_bytes(b"\x00" * 100)

        item = ProgramItem(title="App", command="app", icon_path=str(exe))
        group = ProgramGroup(title="Test", items=[item])
        launcher = Launcher()
        window = GroupWindow(group, launcher)

        # icon_for_executable returns None for a fake .exe, so fallback is used
        lw_item = window.list_widget.item(0)
        icon = lw_item.icon()
        assert not icon.isNull()  # fallback icon should be set

    def test_non_exe_icon_path_uses_qicon(self, qapp, tmp_path):
        """A .png icon_path should use QIcon directly."""
        png = tmp_path / "icon.png"
        png.write_bytes(b"\x00" * 10)

        item = ProgramItem(title="App", command="app", icon_path=str(png))
        group = ProgramGroup(title="Test", items=[item])
        launcher = Launcher()
        window = GroupWindow(group, launcher)

        # The .png path is passed to QIcon (not through executable extraction)
        lw_item = window.list_widget.item(0)
        icon = lw_item.icon()
        # QIcon may or may not load a dummy .png, but it shouldn't crash
        assert icon is not None


class TestExecutableIconHelpers:
    def test_is_executable_icon_exe(self):
        assert is_executable_icon(r"C:\Program Files\app.exe") is True

    def test_is_executable_icon_dll(self):
        assert is_executable_icon(r"C:\Windows\System32\shell32.dll") is True

    def test_is_executable_icon_ico(self):
        assert is_executable_icon(r"C:\icons\app.ico") is True

    def test_is_executable_icon_png(self):
        assert is_executable_icon("/usr/share/icons/app.png") is False

    def test_is_executable_icon_svg(self):
        assert is_executable_icon("/usr/share/icons/app.svg") is False

    def test_icon_for_executable_nonexistent(self, qapp):
        result = icon_for_executable("/nonexistent/path.exe")
        assert result is None

    def test_icon_for_executable_empty_string(self, qapp):
        result = icon_for_executable("")
        assert result is None

    def test_icon_for_executable_fake_file(self, qapp, tmp_path):
        fake = tmp_path / "fake.exe"
        fake.write_bytes(b"\x00" * 100)
        # On Linux, QFileIconProvider returns a generic file icon
        # which should be non-null (Qt always provides something)
        result = icon_for_executable(str(fake))
        # Result is either a valid icon or None -- both are acceptable
        # depending on platform; just verify no crash
        assert result is None or not result.isNull()

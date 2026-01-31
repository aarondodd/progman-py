"""Tests for widgets: GroupWindow, ProgramItemDialog."""

from progman.models.program_group import ProgramGroup
from progman.models.program_item import ProgramItem
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

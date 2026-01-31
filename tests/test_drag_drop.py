"""Tests for drag-and-drop functionality."""

from progman.models.program_group import ProgramGroup
from progman.models.program_item import ProgramItem
from progman.utils.launcher import Launcher
from progman.widgets.group_window import GroupWindow, _drag_state, _DragDropListWidget

from PyQt6.QtCore import Qt


class TestDragDropSetup:
    def test_list_widget_is_custom_subclass(self, qapp):
        group = ProgramGroup(title="Test", items=[])
        launcher = Launcher()
        window = GroupWindow(group, launcher)
        assert isinstance(window.list_widget, _DragDropListWidget)

    def test_drag_enabled(self, qapp):
        group = ProgramGroup(title="Test", items=[])
        launcher = Launcher()
        window = GroupWindow(group, launcher)
        assert window.list_widget.dragEnabled() is True
        assert window.list_widget.acceptDrops() is True

    def test_default_drop_action(self, qapp):
        group = ProgramGroup(title="Test", items=[])
        launcher = Launcher()
        window = GroupWindow(group, launcher)
        assert window.list_widget.defaultDropAction() == Qt.DropAction.MoveAction

    def test_group_window_backref(self, qapp):
        group = ProgramGroup(title="Test", items=[])
        launcher = Launcher()
        window = GroupWindow(group, launcher)
        assert window.list_widget._group_window is window


class TestDragState:
    def test_drag_state_initialized(self):
        assert _drag_state["item"] is None
        assert _drag_state["source_group"] is None
        assert _drag_state["source_window"] is None


class TestReorderSync:
    def test_items_preserved_after_refresh(self, qapp):
        """Verify that all items survive a refresh_items cycle."""
        items = [
            ProgramItem(title="A", command="a"),
            ProgramItem(title="B", command="b"),
            ProgramItem(title="C", command="c"),
        ]
        group = ProgramGroup(title="Test", items=list(items))
        launcher = Launcher()
        window = GroupWindow(group, launcher)

        assert window.list_widget.count() == 3
        assert group.items[0].title == "A"
        assert group.items[1].title == "B"
        assert group.items[2].title == "C"

        # Refresh should not lose items
        window.refresh_items()
        assert window.list_widget.count() == 3
        assert group.items[0].title == "A"

    def test_user_role_data_preserved(self, qapp):
        """Verify ProgramItem references survive in UserRole."""
        items = [
            ProgramItem(title="X", command="x"),
            ProgramItem(title="Y", command="y"),
        ]
        group = ProgramGroup(title="Test", items=list(items))
        launcher = Launcher()
        window = GroupWindow(group, launcher)

        for i in range(window.list_widget.count()):
            lw_item = window.list_widget.item(i)
            data = lw_item.data(Qt.ItemDataRole.UserRole)
            assert isinstance(data, ProgramItem)
            assert data is items[i]

    def test_drop_index_at_empty_space(self, qapp):
        """_index_at_drop returns count when over empty space."""
        group = ProgramGroup(title="Test", items=[
            ProgramItem(title="A", command="a"),
        ])
        launcher = Launcher()
        window = GroupWindow(group, launcher)

        from PyQt6.QtCore import QPoint
        # A point far away from any item should return count
        idx = window.list_widget._index_at_drop(QPoint(9999, 9999))
        assert idx == window.list_widget.count()

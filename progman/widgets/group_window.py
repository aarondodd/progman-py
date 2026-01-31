"""MDI child window displaying a ProgramGroup with drag-and-drop support."""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QMimeData, QPoint, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QDrag, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ..models.program_group import ProgramGroup
from ..models.program_item import ProgramItem
from ..utils.icons import icon_for_executable, is_executable_icon, make_classic_fallback_icon
from ..utils.launcher import Launcher
from .program_item_dialog import ProgramItemDialog

# Module-level drag state for cross-group drag-and-drop.
# Safe because Qt DnD is single-threaded.
_drag_state = {
    "item": None,         # ProgramItem being dragged
    "source_group": None, # ProgramGroup it came from
    "source_window": None,# GroupWindow it came from
}

# Internal MIME type used to identify our own drags
_MIME_TYPE = "application/x-progman-item"


class _DragDropListWidget(QListWidget):
    """QListWidget subclass that handles drag-and-drop manually.

    Qt's built-in DragDrop mode serializes items via MIME, which loses
    Python objects stored in UserRole.  This subclass captures the
    dragged item before the drag starts and processes drops manually
    so no data is lost.
    """

    # Emitted after a successful reorder or cross-group transfer
    order_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._group_window: Optional["GroupWindow"] = None

    def set_group_window(self, gw: "GroupWindow") -> None:
        self._group_window = gw

    # ── Drag ──

    def startDrag(self, supportedActions) -> None:
        current = self.currentItem()
        if current is None:
            return

        item = current.data(Qt.ItemDataRole.UserRole)
        if not isinstance(item, ProgramItem):
            return

        # Record what is being dragged
        gw = self._group_window
        _drag_state["item"] = item
        _drag_state["source_group"] = gw.group if gw else None
        _drag_state["source_window"] = gw

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(_MIME_TYPE, b"")  # marker only
        drag.setMimeData(mime)

        # Use the item's icon as the drag pixmap
        icon = current.icon()
        if not icon.isNull():
            drag.setPixmap(icon.pixmap(32, 32))

        drag.exec(Qt.DropAction.MoveAction)

    # ── Drop ──

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat(_MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasFormat(_MIME_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        if not event.mimeData().hasFormat(_MIME_TYPE):
            event.ignore()
            return

        dragged_item = _drag_state.get("item")
        source_group = _drag_state.get("source_group")
        source_window = _drag_state.get("source_window")
        gw = self._group_window

        if dragged_item is None or gw is None:
            event.ignore()
            return

        target_group = gw.group

        # Determine the drop index from the cursor position
        drop_pos = event.position().toPoint()
        drop_index = self._index_at_drop(drop_pos)

        if source_group is target_group:
            # ── Within-group reorder ──
            try:
                old_index = source_group.items.index(dragged_item)
            except ValueError:
                event.ignore()
                return

            # Remove then insert at new position
            source_group.items.pop(old_index)
            # Adjust index if we removed before the target
            if drop_index > old_index:
                drop_index -= 1
            source_group.items.insert(drop_index, dragged_item)
            gw.refresh_items()
            self.order_changed.emit()
        else:
            # ── Cross-group transfer ──
            if source_group is not None:
                source_group.items = [
                    i for i in source_group.items if i is not dragged_item
                ]
                if source_window is not None:
                    source_window.refresh_items()
                    source_window.list_widget.order_changed.emit()

            target_group.items.insert(drop_index, dragged_item)
            gw.refresh_items()
            self.order_changed.emit()

        # Clear drag state
        _drag_state["item"] = None
        _drag_state["source_group"] = None
        _drag_state["source_window"] = None

        event.acceptProposedAction()

    def _index_at_drop(self, pos: QPoint) -> int:
        """Determine the list index for a drop at *pos*.

        Returns the index of the item under the cursor, or the total
        count (append) if the cursor is over empty space.
        """
        item_at = self.itemAt(pos)
        if item_at is not None:
            return self.row(item_at)
        return self.count()


class GroupWindow(QWidget):
    """A group window that shows program items as icons with drag-and-drop."""

    items_changed = pyqtSignal()

    def __init__(
        self,
        group: ProgramGroup,
        launcher: Launcher,
        dark_mode: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.group = group
        self.launcher = launcher
        self._dark_mode = dark_mode

        self.list_widget = _DragDropListWidget(self)
        self.list_widget.set_group_window(self)
        self._setup_list()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.list_widget)

        self.refresh_items()

    def _setup_list(self) -> None:
        self.list_widget.setViewMode(QListView.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(32, 32))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(10)

        # Enable drag initiation and drop acceptance but do NOT let Qt
        # perform its own internal move — we handle everything in
        # _DragDropListWidget.startDrag / dropEvent.
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDropIndicatorShown(True)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setMovement(QListWidget.Movement.Snap)

        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)

        # Propagate order changes as items_changed for auto-save
        self.list_widget.order_changed.connect(self.items_changed)

    def set_dark_mode(self, dark_mode: bool) -> None:
        """Update dark mode state and refresh icons."""
        self._dark_mode = dark_mode
        self.refresh_items()

    def refresh_items(self) -> None:
        self.list_widget.clear()
        for item in self.group.items:
            lw_item = QListWidgetItem(item.title)
            icon = self._get_icon_for_item(item)
            if icon is not None:
                lw_item.setIcon(icon)
            lw_item.setData(Qt.ItemDataRole.UserRole, item)
            self.list_widget.addItem(lw_item)

    def _get_icon_for_item(self, item: ProgramItem) -> Optional[QIcon]:
        if item.icon_path and Path(item.icon_path).exists():
            if is_executable_icon(item.icon_path):
                icon = icon_for_executable(item.icon_path)
                if icon is not None:
                    return icon
                # Extraction failed -- fall through to fallback
            else:
                return QIcon(item.icon_path)
        return make_classic_fallback_icon(item.title, dark_mode=self._dark_mode)

    def _on_item_double_clicked(self, lw_item: QListWidgetItem) -> None:
        item: ProgramItem = lw_item.data(Qt.ItemDataRole.UserRole)
        self.launcher.launch(item)

    def _on_context_menu(self, pos) -> None:
        item = self.list_widget.itemAt(pos)
        global_pos = self.list_widget.mapToGlobal(pos)

        menu = QMenu(self)

        new_action = QAction("New Program...", self)
        new_action.triggered.connect(self._new_program)
        menu.addAction(new_action)

        if item is not None:
            edit_action = QAction("Edit...", self)
            delete_action = QAction("Delete", self)
            menu.addAction(edit_action)
            menu.addAction(delete_action)

            edit_action.triggered.connect(lambda: self._edit_program(item))
            delete_action.triggered.connect(lambda: self._delete_program(item))

        menu.exec(global_pos)

    def _new_program(self) -> None:
        dlg = ProgramItemDialog(self)
        new_item = dlg.get_item()
        if new_item is None:
            return
        self.group.items.append(new_item)
        self.refresh_items()
        self.items_changed.emit()

    def _edit_program(self, lw_item: QListWidgetItem) -> None:
        item: ProgramItem = lw_item.data(Qt.ItemDataRole.UserRole)
        dlg = ProgramItemDialog(self, item=item)
        updated_item = dlg.get_item()
        if updated_item is None:
            return
        self.refresh_items()
        self.items_changed.emit()

    def _delete_program(self, lw_item: QListWidgetItem) -> None:
        item: ProgramItem = lw_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Delete Program",
            f"Delete '{item.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.group.items = [i for i in self.group.items if i is not item]
        self.refresh_items()
        self.items_changed.emit()

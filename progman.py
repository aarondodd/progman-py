#!/usr/bin/env python3
"""
progman.py - a simple cross-platform Program Manager-style launcher.

Requirements:
    pip install PyQt6

Tested conceptually for:
    - Windows (process launching via subprocess)
    - Linux / other POSIX (process launching via subprocess)

Config:
    Stored as JSON in ~/.progman.json by default.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QInputDialog,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QMdiArea,
    QMdiSubWindow,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

# -----------------------------
# Model
# -----------------------------


@dataclass
class ProgramItem:
    title: str
    command: str
    working_dir: str = ""
    icon_path: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ProgramItem":
        return cls(
            title=data.get("title", ""),
            command=data.get("command", ""),
            working_dir=data.get("working_dir", ""),
            icon_path=data.get("icon_path", ""),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProgramGroup:
    title: str
    items: List[ProgramItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ProgramGroup":
        items_data = data.get("items", [])
        items = [ProgramItem.from_dict(i) for i in items_data]
        return cls(title=data.get("title", ""), items=items)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "items": [i.to_dict() for i in self.items],
        }


class AppModel:
    """
    Application model holding all groups and items.
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path: Path = (
            config_path if config_path is not None else Path.home() / ".progman.json"
        )
        self.groups: List[ProgramGroup] = []
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
            # Fallback to default if config unreadable
            self._load_default()
            return

        groups_data = data.get("groups", [])
        self.groups = [ProgramGroup.from_dict(g) for g in groups_data]

    def save(self) -> None:
        data = {"groups": [g.to_dict() for g in self.groups]}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_default(self) -> None:
        # Simple default group with one item, platform-sensitive.
        if sys.platform.startswith("win"):
            default_item = ProgramItem(
                title="Notepad",
                command="notepad.exe",
                working_dir="",
                icon_path="",
            )
        else:
            # very generic; adjust for your environment
            default_item = ProgramItem(
                title="Terminal",
                command="xterm",
                working_dir="",
                icon_path="",
            )

        self.groups = [
            ProgramGroup(
                title="Main",
                items=[default_item],
            )
        ]


# -----------------------------
# Launcher
# -----------------------------


class Launcher:
    """
    Cross-platform process launcher.
    """

    @staticmethod
    def launch(item: ProgramItem) -> None:
        if not item.command:
            return

        cwd = item.working_dir or None

        try:
            # Using shell=True for convenience to allow simple commands.
            # For stricter security you could split arguments yourself.
            subprocess.Popen(
                item.command,
                shell=True,
                cwd=cwd,
            )
        except Exception as e:
            QMessageBox.critical(
                None,
                "Launch Error",
                f"Failed to launch:\n{item.title}\n\nCommand: {item.command}\n\nError: {e}",
            )


# -----------------------------
# Program Item Dialog
# -----------------------------


class ProgramItemDialog(QDialog):
    """
    Dialog to create or edit a ProgramItem.
    """

    def __init__(self, parent: Optional[QWidget] = None, item: Optional[ProgramItem] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Program Item")
        self._item = item

        self.title_edit = None
        self.command_edit = None
        self.working_edit = None
        self.icon_edit = None

        self._build_ui()

        if item is not None:
            self._populate_from_item(item)

    def _build_ui(self) -> None:
        layout = QFormLayout(self)

        self.title_edit = QLineEditWithBrowse(enabled_browse=False)
        self.command_edit = QLineEditWithBrowse(
            browse_label="Browse...",
            file_filter="Executables (*.exe *.bat *.cmd);;All Files (*)"
            if sys.platform.startswith("win")
            else "All Files (*)",
        )
        self.working_edit = QLineEditWithBrowse(
            browse_label="Browse...",
            dir_mode=True,
        )
        self.icon_edit = QLineEditWithBrowse(
            browse_label="Browse...",
            file_filter="Images (*.ico *.png *.jpg *.jpeg *.bmp);;All Files (*)",
        )

        layout.addRow("Title:", self.title_edit)
        layout.addRow("Command:", self.command_edit)
        layout.addRow("Working Dir:", self.working_edit)
        layout.addRow("Icon Path:", self.icon_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate_from_item(self, item: ProgramItem) -> None:
        self.title_edit.setText(item.title)
        self.command_edit.setText(item.command)
        self.working_edit.setText(item.working_dir)
        self.icon_edit.setText(item.icon_path)

    def get_item(self) -> Optional[ProgramItem]:
        if self.exec() != QDialog.DialogCode.Accepted:
            return None

        title = self.title_edit.text().strip()
        command = self.command_edit.text().strip()
        working = self.working_edit.text().strip()
        icon = self.icon_edit.text().strip()

        if not title or not command:
            QMessageBox.warning(
                self,
                "Invalid Item",
                "Title and Command are required.",
            )
            return None

        if self._item is None:
            return ProgramItem(
                title=title,
                command=command,
                working_dir=working,
                icon_path=icon,
            )

        self._item.title = title
        self._item.command = command
        self._item.working_dir = working
        self._item.icon_path = icon
        return self._item


class QLineEditWithBrowse(QWidget):
    """
    Simple composite widget: QLineEdit + optional 'Browse' button.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        enabled_browse: bool = True,
        browse_label: str = "Browse...",
        file_filter: str = "All Files (*)",
        dir_mode: bool = False,
    ) -> None:
        super().__init__(parent)
        from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton

        self.dir_mode = dir_mode
        self.file_filter = file_filter

        self.edit = QLineEdit(self)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.edit)

        if enabled_browse:
            self.button = QPushButton(browse_label, self)
            self.button.clicked.connect(self._on_browse)
            layout.addWidget(self.button)
        else:
            self.button = None

    def _on_browse(self) -> None:
        if self.dir_mode:
            directory = QFileDialog.getExistingDirectory(self, "Select Working Directory")
            if directory:
                self.edit.setText(directory)
        else:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Select File",
                "",
                self.file_filter,
            )
            if filename:
                self.edit.setText(filename)

    def text(self) -> str:
        return self.edit.text()

    def setText(self, value: str) -> None:
        self.edit.setText(value)


# -----------------------------
# Group Window (MDI Child)
# -----------------------------


class GroupWindow(QWidget):
    """
    A group window that shows program items as icons.
    """

    def __init__(
        self,
        group: ProgramGroup,
        launcher: Launcher,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.group = group
        self.launcher = launcher

        self.list_widget = QListWidget(self)
        self._setup_list()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.list_widget)

        self.refresh_items()

    def _setup_list(self) -> None:
        self.list_widget.setViewMode(QListView.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(32, 32))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setSpacing(10)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)

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
            return QIcon(item.icon_path)
        # Fallback: no icon or default
        return None

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

    def _edit_program(self, lw_item: QListWidgetItem) -> None:
        item: ProgramItem = lw_item.data(Qt.ItemDataRole.UserRole)
        dlg = ProgramItemDialog(self, item=item)
        updated_item = dlg.get_item()
        if updated_item is None:
            return
        self.refresh_items()

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


# -----------------------------
# Main Window
# -----------------------------


class MainWindow(QMainWindow):
    """
    Main Program Manager-like window.
    """

    def __init__(self, model: AppModel) -> None:
        super().__init__()
        self.model = model
        self.launcher = Launcher()

        self.mdi = QMdiArea(self)
        self.setCentralWidget(self.mdi)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self._build_ui()
        self._load_groups()

        self.setWindowTitle("Program Manager (progman.py)")
        self.resize(900, 600)

    # ----- UI setup -----

    def _build_ui(self) -> None:
        self._build_menubar()
        self._build_toolbar()

    def _build_menubar(self) -> None:
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        new_group_act = QAction("New Group...", self)
        save_act = QAction("&Save", self)
        exit_act = QAction("E&xit", self)

        new_group_act.triggered.connect(self._new_group)
        save_act.triggered.connect(self._save)
        exit_act.triggered.connect(self.close)

        file_menu.addAction(new_group_act)
        file_menu.addSeparator()
        file_menu.addAction(save_act)
        file_menu.addSeparator()
        file_menu.addAction(exit_act)

        # Group menu
        group_menu = menubar.addMenu("&Group")
        rename_group_act = QAction("&Rename Group...", self)
        delete_group_act = QAction("&Delete Group", self)

        rename_group_act.triggered.connect(self._rename_current_group)
        delete_group_act.triggered.connect(self._delete_current_group)

        group_menu.addAction(rename_group_act)
        group_menu.addAction(delete_group_act)

        # Window menu (tile/cascade)
        window_menu = menubar.addMenu("&Window")
        tile_act = QAction("&Tile", self)
        cascade_act = QAction("&Cascade", self)

        tile_act.triggered.connect(self.mdi.tileSubWindows)
        cascade_act.triggered.connect(self.mdi.cascadeSubWindows)

        window_menu.addAction(tile_act)
        window_menu.addAction(cascade_act)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(True)
        self.addToolBar(toolbar)

        new_group_act = QAction("New Group", self)
        new_group_act.triggered.connect(self._new_group)

        save_act = QAction("Save", self)
        save_act.triggered.connect(self._save)

        toolbar.addAction(new_group_act)
        toolbar.addAction(save_act)

    # ----- Groups handling -----

    def _load_groups(self) -> None:
        self.mdi.closeAllSubWindows()
        for group in self.model.groups:
            self._add_group_window(group)

    def _add_group_window(self, group: ProgramGroup) -> QMdiSubWindow:
        widget = GroupWindow(group, self.launcher, self.mdi)
        sub = QMdiSubWindow()
        sub.setWidget(widget)
        sub.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        sub.setWindowTitle(group.title)
        self.mdi.addSubWindow(sub)
        sub.show()
        return sub

    def _current_group_window(self) -> Optional[GroupWindow]:
        sub = self.mdi.activeSubWindow()
        if sub is None:
            return None
        widget = sub.widget()
        if isinstance(widget, GroupWindow):
            return widget
        return None

    def _new_group(self) -> None:
        text, ok = QInputDialog.getText(self, "New Group", "Group name:")
        if not ok or not text.strip():
            return
        group = ProgramGroup(title=text.strip(), items=[])
        self.model.groups.append(group)
        self._add_group_window(group)

    def _rename_current_group(self) -> None:
        gw = self._current_group_window()
        if gw is None:
            return
        group = gw.group
        text, ok = QInputDialog.getText(
            self,
            "Rename Group",
            "New group name:",
            text=group.title,
        )
        if not ok or not text.strip():
            return
        group.title = text.strip()

        # Update window title
        sub = self.mdi.activeSubWindow()
        if sub is not None:
            sub.setWindowTitle(group.title)

    def _delete_current_group(self) -> None:
        gw = self._current_group_window()
        if gw is None:
            return

        group = gw.group
        reply = QMessageBox.question(
            self,
            "Delete Group",
            f"Delete group '{group.title}' and all its items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Remove from model
        self.model.groups = [g for g in self.model.groups if g is not group]

        # Close the subwindow
        sub = self.mdi.activeSubWindow()
        if sub is not None:
            sub.close()

    def _save(self) -> None:
        self.model.save()
        self.status_bar.showMessage("Configuration saved.", 3000)

    # ----- Close handling -----

    def closeEvent(self, event) -> None:
        # Auto-save on close
        self.model.save()
        super().closeEvent(event)


# -----------------------------
# Entry point
# -----------------------------


def main() -> None:
    app = QApplication(sys.argv)

    model = AppModel()
    window = MainWindow(model)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

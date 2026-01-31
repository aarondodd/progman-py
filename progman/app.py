"""Main application window for Program Manager."""

import json
from typing import Optional

from PyQt6.QtCore import QRect, QTimer, Qt
from PyQt6.QtGui import QAction, QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMdiArea,
    QMdiSubWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
)

from PyQt6.QtCore import QThread, pyqtSignal

from .models.app_model import AppModel
from .models.program_group import ProgramGroup
from .models.program_item import ProgramItem
from .utils.icons import make_group_icon
from .utils.launcher import Launcher
from .utils.theme import ThemeManager
from .version import __version__
from .widgets.group_window import GroupWindow
from .widgets.scan_dialog import ScanForProgramsDialog


class UpgradeWorker(QThread):
    """Worker thread for running upgrade in background."""

    progress = pyqtSignal(str, str)  # stage, message
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, github_config: dict, parent=None):
        super().__init__(parent)
        self._github_config = github_config

    def run(self):
        from .utils.updater import upgrade

        def progress_callback(stage, message):
            self.progress.emit(stage, message)

        success, message = upgrade(self._github_config, progress_callback)
        self.finished.emit(success, message)


class UpgradeProgressDialog(QDialog):
    """Dialog showing upgrade progress with build output."""

    def __init__(self, github_config: dict, parent=None, dark_mode: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Upgrading Program Manager")
        self.setMinimumSize(600, 400)
        self.setModal(True)

        self._success = False
        self._message = ""

        layout = QVBoxLayout(self)

        self.status_label = QLabel("Starting upgrade...")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.output_text)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.close_button = QPushButton("Close")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self._worker = UpgradeWorker(github_config)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, stage: str, message: str):
        if stage == "build_output":
            self.output_text.append(message)
            scrollbar = self.output_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        else:
            self.status_label.setText(message)
            self.output_text.append(f"\n=== {message} ===\n")
        QApplication.processEvents()

    def _on_finished(self, success: bool, message: str):
        self._success = success
        self._message = message

        if success:
            self.status_label.setText("Upgrade complete!")
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
            self.output_text.append(f"\n=== SUCCESS ===\n{message}")
        else:
            self.status_label.setText("Upgrade failed!")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
            self.output_text.append(f"\n=== FAILED ===\n{message}")

        self.close_button.setEnabled(True)

    def get_result(self) -> tuple:
        return self._success, self._message

    def closeEvent(self, event):
        if self._worker.isRunning():
            event.ignore()
        else:
            super().closeEvent(event)


class MainWindow(QMainWindow):
    """Main Program Manager window with MDI workspace."""

    def __init__(self, model: AppModel) -> None:
        super().__init__()
        self.model = model
        self.launcher = Launcher()

        self.dark_mode_action: Optional[QAction] = None

        self.mdi = QMdiArea(self)
        self.setCentralWidget(self.mdi)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        ThemeManager.apply_to_mdi(self.mdi, self.model.dark_mode)

        self._build_ui()
        self._load_groups()
        self._restore_layout()

        self.setWindowTitle(f"Program Manager v{__version__}")
        self.resize(900, 600)

        # Auto-check for updates after 2 seconds
        QTimer.singleShot(2000, self._auto_check_for_updates)

    def _build_ui(self) -> None:
        self._build_menubar()

    def _build_menubar(self) -> None:
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_group_act = QAction("New &Group...", self)
        new_group_act.triggered.connect(self._new_group)
        file_menu.addAction(new_group_act)

        scan_act = QAction("&Scan for Programs...", self)
        scan_act.triggered.connect(self._scan_for_programs)
        file_menu.addAction(scan_act)

        file_menu.addSeparator()

        save_act = QAction("&Save", self)
        save_act.triggered.connect(self._save)
        file_menu.addAction(save_act)

        file_menu.addSeparator()

        exit_act = QAction("E&xit", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # View menu
        view_menu = menubar.addMenu("&View")

        self.dark_mode_action = QAction("&Dark Mode", self, checkable=True)
        self.dark_mode_action.setShortcut("Ctrl+D")
        self.dark_mode_action.setChecked(self.model.dark_mode)
        self.dark_mode_action.triggered.connect(self._toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)

        # Group menu
        group_menu = menubar.addMenu("G&roup")

        rename_group_act = QAction("&Rename Group...", self)
        rename_group_act.triggered.connect(self._rename_current_group)
        group_menu.addAction(rename_group_act)

        delete_group_act = QAction("&Delete Group", self)
        delete_group_act.triggered.connect(self._delete_current_group)
        group_menu.addAction(delete_group_act)

        # Window menu
        window_menu = menubar.addMenu("&Window")

        tile_act = QAction("&Tile", self)
        tile_act.triggered.connect(self.mdi.tileSubWindows)
        window_menu.addAction(tile_act)

        cascade_act = QAction("&Cascade", self)
        cascade_act.triggered.connect(self.mdi.cascadeSubWindows)
        window_menu.addAction(cascade_act)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        check_update_act = QAction("Check for &Updates...", self)
        check_update_act.triggered.connect(self._check_for_updates)
        help_menu.addAction(check_update_act)

        upgrade_act = QAction("&Upgrade...", self)
        upgrade_act.triggered.connect(self._upgrade)
        help_menu.addAction(upgrade_act)

        help_menu.addSeparator()

        about_act = QAction("&About", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

    # ── Theme handling ──

    def _toggle_dark_mode(self) -> None:
        self.model.dark_mode = self.dark_mode_action.isChecked()
        ThemeManager.apply(QApplication.instance(), self.model.dark_mode)
        ThemeManager.apply_to_mdi(self.mdi, self.model.dark_mode)

        # Update all group windows
        for sub in self.mdi.subWindowList():
            widget = sub.widget()
            if isinstance(widget, GroupWindow):
                widget.set_dark_mode(self.model.dark_mode)
                sub.setWindowIcon(make_group_icon(dark_mode=self.model.dark_mode))

        self._save()

    # ── Groups handling ──

    def _load_groups(self) -> None:
        self.mdi.closeAllSubWindows()
        for group in self.model.groups:
            self._add_group_window(group)

    def _add_group_window(self, group: ProgramGroup) -> QMdiSubWindow:
        widget = GroupWindow(
            group, self.launcher, dark_mode=self.model.dark_mode, parent=self.mdi
        )
        widget.items_changed.connect(self._save)

        sub = QMdiSubWindow()
        sub.setWidget(widget)
        sub.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        sub.setWindowTitle(group.title)
        sub.setWindowIcon(make_group_icon(dark_mode=self.model.dark_mode))
        self.mdi.addSubWindow(sub)
        sub.show()
        return sub

    def _capture_layout(self) -> None:
        layout = []
        for sub in self.mdi.subWindowList():
            widget = sub.widget()
            if not isinstance(widget, GroupWindow):
                continue

            geom = sub.geometry()
            if geom.isValid():
                geometry = [geom.x(), geom.y(), geom.width(), geom.height()]
            else:
                geometry = None

            if sub.isMaximized():
                state = "maximized"
            elif sub.isMinimized():
                state = "minimized"
            else:
                state = "normal"

            layout.append({
                "title": widget.group.title,
                "geometry": geometry,
                "state": state,
            })

        self.model.layout_state = json.dumps(layout)

    def _restore_layout(self) -> None:
        if not self.model.layout_state:
            return

        try:
            layout = json.loads(self.model.layout_state)
        except Exception:
            return

        layout_by_title = {
            entry.get("title"): entry for entry in layout if isinstance(entry, dict)
        }

        for sub in self.mdi.subWindowList():
            widget = sub.widget()
            if not isinstance(widget, GroupWindow):
                continue

            data = layout_by_title.get(widget.group.title)
            if not data:
                continue

            geometry = data.get("geometry")
            if isinstance(geometry, list) and len(geometry) == 4:
                rect = QRect(*geometry)
                if rect.isValid():
                    sub.setGeometry(rect)

            state = data.get("state", "normal")
            if state == "maximized":
                sub.showMaximized()
            elif state == "minimized":
                sub.showMinimized()
            else:
                sub.showNormal()

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
        self._save()

    def _rename_current_group(self) -> None:
        gw = self._current_group_window()
        if gw is None:
            return
        group = gw.group
        text, ok = QInputDialog.getText(
            self, "Rename Group", "New group name:", text=group.title
        )
        if not ok or not text.strip():
            return
        group.title = text.strip()

        sub = self.mdi.activeSubWindow()
        if sub is not None:
            sub.setWindowTitle(group.title)
        self._save()

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

        self.model.groups = [g for g in self.model.groups if g is not group]

        sub = self.mdi.activeSubWindow()
        if sub is not None:
            sub.close()
        self._save()

    # ── Scan for programs ──

    def _scan_for_programs(self) -> None:
        dialog = ScanForProgramsDialog(self.model.groups, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected = dialog.get_selected_items()
        if not selected:
            return

        # Group selected apps by their group name
        groups_map = {}
        for app in selected:
            groups_map.setdefault(app.group, []).append(app)

        # Find or create groups and add items
        existing_groups = {g.title: g for g in self.model.groups}

        for group_name, apps in groups_map.items():
            if group_name in existing_groups:
                group = existing_groups[group_name]
            else:
                group = ProgramGroup(title=group_name, items=[])
                self.model.groups.append(group)
                existing_groups[group_name] = group
                self._add_group_window(group)

            for app in apps:
                item = ProgramItem(
                    title=app.name,
                    command=app.command,
                    icon_path=app.icon_path,
                )
                group.items.append(item)

        # Refresh all group windows
        for sub in self.mdi.subWindowList():
            widget = sub.widget()
            if isinstance(widget, GroupWindow):
                widget.refresh_items()

        self._save()
        self.status_bar.showMessage(
            f"Added {len(selected)} program(s).", 3000
        )

    # ── Update checking ──

    def _auto_check_for_updates(self) -> None:
        """Automatically check for updates on startup (respects 7-day interval)."""
        from .utils.updater import check_for_updates

        result = check_for_updates(self.model.github)
        if result:
            local_version, remote_version = result
            self.status_bar.showMessage(
                f"Update available: v{remote_version} (current: v{local_version})"
            )
            QMessageBox.information(
                self,
                "Update Available",
                f"A new version of Program Manager is available!\n\n"
                f"Current version: {local_version}\n"
                f"Latest version: {remote_version}\n\n"
                "Use Help > Upgrade to install the update.",
            )

    def _check_for_updates(self) -> None:
        """Manual update check from Help menu."""
        from .utils.updater import get_latest_release, is_newer_version

        self.status_bar.showMessage("Checking for updates...")
        QApplication.processEvents()

        release_info = get_latest_release(self.model.github)

        if not release_info:
            QMessageBox.information(
                self,
                "Check for Updates",
                "Could not check for updates.\n\n"
                "Please check your internet connection.",
            )
            self.status_bar.showMessage("Ready")
            return

        remote_version = release_info["tag_name"]

        if is_newer_version(remote_version, __version__):
            result = QMessageBox.question(
                self,
                "Update Available",
                f"A new version is available!\n\n"
                f"Current version: {__version__}\n"
                f"Latest version: {remote_version}\n\n"
                "Would you like to upgrade now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if result == QMessageBox.StandardButton.Yes:
                self._upgrade()
        else:
            QMessageBox.information(
                self,
                "Check for Updates",
                f"You are running the latest version ({__version__}).",
            )

        self.status_bar.showMessage("Ready")

    def _upgrade(self) -> None:
        """Download and install the latest version."""
        from .utils.updater import get_latest_release, is_newer_version

        self.status_bar.showMessage("Checking for updates...")
        QApplication.processEvents()

        release_info = get_latest_release(self.model.github)

        if not release_info:
            QMessageBox.warning(
                self, "Upgrade", "Could not fetch release information."
            )
            self.status_bar.showMessage("Ready")
            return

        remote_version = release_info["tag_name"]

        if not is_newer_version(remote_version, __version__):
            QMessageBox.information(
                self,
                "Upgrade",
                f"You are already running the latest version ({__version__}).",
            )
            self.status_bar.showMessage("Ready")
            return

        result = QMessageBox.question(
            self,
            "Confirm Upgrade",
            f"Upgrade from {__version__} to {remote_version}?\n\n"
            "This will download the latest release and run the build script.\n"
            "The application will need to be restarted after the upgrade.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:
            self.status_bar.showMessage("Ready")
            return

        dialog = UpgradeProgressDialog(
            self.model.github, parent=self, dark_mode=self.model.dark_mode
        )
        dialog.exec()

        success, message = dialog.get_result()

        if success:
            QMessageBox.information(
                self,
                "Upgrade Complete",
                f"{message}\n\nPlease restart the application to use the new version.",
            )

        self.status_bar.showMessage("Ready")

    # ── About ──

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Program Manager",
            f"Program Manager v{__version__}\n\n"
            "A cross-platform recreation of the\n"
            "Windows 3.x Program Manager.\n\n"
            "Built with PyQt6.",
        )

    # ── Save / Close ──

    def _save(self) -> None:
        self._capture_layout()
        self.model.save()
        self.status_bar.showMessage("Configuration saved.", 3000)

    def closeEvent(self, event) -> None:
        self._save()
        super().closeEvent(event)

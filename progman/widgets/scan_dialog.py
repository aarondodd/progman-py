"""Dialog for scanning and adding discovered programs."""

from typing import Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models.program_group import ProgramGroup
from ..models.program_item import ProgramItem
from ..utils.scanner import DiscoveredApp
from ..workers.scan_worker import ScanWorker


class ScanForProgramsDialog(QDialog):
    """Dialog that scans for installed programs and lets the user select which to add."""

    def __init__(self, existing_groups: List[ProgramGroup], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Scan for Programs")
        self.setMinimumSize(700, 500)

        self._existing_groups = existing_groups
        self._discovered: List[DiscoveredApp] = []
        self._selected_items: List[DiscoveredApp] = []

        self._build_ui()
        self._start_scan()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.status_label = QLabel("Scanning for programs...")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)

        # Tree view with columns: Checkbox, Name, Command, Group
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Command", "Group"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)

        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.tree)

        # Select All / Deselect All buttons
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all)
        select_layout.addWidget(select_all_btn)
        select_layout.addWidget(deselect_all_btn)
        select_layout.addStretch()
        layout.addLayout(select_layout)

        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Add Selected")
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _start_scan(self) -> None:
        self._worker = ScanWorker()
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.start()

    def _on_scan_finished(self, apps: list) -> None:
        self._discovered = apps
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)

        if not apps:
            self.status_label.setText("No programs found.")
            return

        self.status_label.setText(f"Found {len(apps)} programs. Select items to add:")

        # Build existing command set to pre-exclude already-added items
        existing_commands = set()
        for group in self._existing_groups:
            for item in group.items:
                existing_commands.add(item.command)

        for app in apps:
            tree_item = QTreeWidgetItem()
            tree_item.setFlags(
                tree_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable
            )
            already_exists = app.command in existing_commands
            tree_item.setCheckState(0, Qt.CheckState.Unchecked)
            tree_item.setText(0, app.name)
            tree_item.setText(1, app.command)
            tree_item.setText(2, app.group)
            tree_item.setData(0, Qt.ItemDataRole.UserRole, app)

            if already_exists:
                tree_item.setForeground(0, Qt.GlobalColor.gray)
                tree_item.setForeground(1, Qt.GlobalColor.gray)
                tree_item.setToolTip(0, "Already added")

            self.tree.addTopLevelItem(tree_item)

        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def _select_all(self) -> None:
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(0, Qt.CheckState.Checked)

    def _deselect_all(self) -> None:
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(0, Qt.CheckState.Unchecked)

    def _on_accept(self) -> None:
        self._selected_items = []
        for i in range(self.tree.topLevelItemCount()):
            tree_item = self.tree.topLevelItem(i)
            if tree_item.checkState(0) == Qt.CheckState.Checked:
                app = tree_item.data(0, Qt.ItemDataRole.UserRole)
                # Use the potentially-edited group name from column 2
                app.group = tree_item.text(2)
                self._selected_items.append(app)
        self.accept()

    def get_selected_items(self) -> List[DiscoveredApp]:
        """Return the list of selected DiscoveredApp entries after dialog closes."""
        return self._selected_items

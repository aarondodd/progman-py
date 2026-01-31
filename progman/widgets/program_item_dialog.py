"""Dialog for creating and editing program items."""

import sys
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from ..models.program_item import ProgramItem


class QLineEditWithBrowse(QWidget):
    """Composite widget: QLineEdit + optional Browse button."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        enabled_browse: bool = True,
        browse_label: str = "Browse...",
        file_filter: str = "All Files (*)",
        dir_mode: bool = False,
    ) -> None:
        super().__init__(parent)
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
            directory = QFileDialog.getExistingDirectory(
                self, "Select Working Directory"
            )
            if directory:
                self.edit.setText(directory)
        else:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Select File", "", self.file_filter
            )
            if filename:
                self.edit.setText(filename)

    def text(self) -> str:
        return self.edit.text()

    def setText(self, value: str) -> None:
        self.edit.setText(value)


class ProgramItemDialog(QDialog):
    """Dialog to create or edit a ProgramItem."""

    def __init__(
        self, parent: Optional[QWidget] = None, item: Optional[ProgramItem] = None
    ) -> None:
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
                self, "Invalid Item", "Title and Command are required."
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

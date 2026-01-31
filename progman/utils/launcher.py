"""Cross-platform process launcher for Program Manager."""

import subprocess

from PyQt6.QtWidgets import QMessageBox

from ..models.program_item import ProgramItem


class Launcher:
    """Cross-platform process launcher."""

    @staticmethod
    def launch(item: ProgramItem) -> None:
        if not item.command:
            return

        cwd = item.working_dir or None

        try:
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

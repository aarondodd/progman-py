#!/usr/bin/env python3
"""Program Manager - entry point.

A cross-platform PyQt6-based recreation of the Windows 3.x Program Manager.
"""

import sys

from PyQt6.QtWidgets import QApplication

from progman.app import MainWindow
from progman.models import AppModel
from progman.utils.theme import ThemeManager


def main() -> None:
    app = QApplication(sys.argv)

    model = AppModel()
    ThemeManager.apply(app, model.dark_mode)

    window = MainWindow(model)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

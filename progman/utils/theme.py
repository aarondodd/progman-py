"""Centralized theme management for Program Manager.

Provides light and dark mode stylesheets applied globally via QApplication.
All colors are defined here as the single source of truth.
"""

from PyQt6.QtGui import QBrush, QColor, QPalette
from PyQt6.QtWidgets import QApplication, QMdiArea


class ThemeManager:
    """Manages light and dark theme switching for the application."""

    # ── Dark mode colors ──
    DARK_BG_PRIMARY = "#1e1e1e"
    DARK_BG_SECONDARY = "#2d2d2d"
    DARK_BG_INPUT = "#3c3c3c"
    DARK_BG_HOVER = "#454545"
    DARK_BG_PRESSED = "#505050"
    DARK_TEXT = "#d4d4d4"
    DARK_TEXT_DISABLED = "#666666"
    DARK_BORDER = "#3d3d3d"
    DARK_SELECTION = "#264f78"
    DARK_ACCENT = "#0078d4"
    DARK_MDI_BG = "#252526"
    DARK_STATUSBAR = "#2d2d2d"

    # ── Light mode colors ──
    LIGHT_BG_PRIMARY = "#ffffff"
    LIGHT_BG_SECONDARY = "#f3f3f3"
    LIGHT_BG_INPUT = "#ffffff"
    LIGHT_BG_HOVER = "#e8e8e8"
    LIGHT_BG_PRESSED = "#d0d0d0"
    LIGHT_TEXT = "#1e1e1e"
    LIGHT_TEXT_DISABLED = "#a0a0a0"
    LIGHT_BORDER = "#d4d4d4"
    LIGHT_SELECTION = "#cce8ff"
    LIGHT_ACCENT = "#0078d4"
    LIGHT_MDI_BG = "#c0c0c0"
    LIGHT_STATUSBAR = "#f3f3f3"

    DARK_STYLESHEET = f"""
    QMainWindow, QWidget {{
        background-color: {DARK_BG_PRIMARY};
        color: {DARK_TEXT};
    }}
    QMenuBar {{
        background-color: {DARK_BG_SECONDARY};
        color: {DARK_TEXT};
        border-bottom: 1px solid {DARK_BORDER};
    }}
    QMenuBar::item:selected {{
        background-color: {DARK_SELECTION};
    }}
    QMenu {{
        background-color: {DARK_BG_SECONDARY};
        color: {DARK_TEXT};
        border: 1px solid {DARK_BORDER};
    }}
    QMenu::item:selected {{
        background-color: {DARK_SELECTION};
    }}
    QMenu::separator {{
        height: 1px;
        background: {DARK_BORDER};
        margin: 4px 8px;
    }}
    QMdiArea {{
        background-color: {DARK_MDI_BG};
    }}
    QMdiSubWindow {{
        background-color: {DARK_BG_PRIMARY};
        color: {DARK_TEXT};
    }}
    QListWidget {{
        background-color: {DARK_BG_PRIMARY};
        color: {DARK_TEXT};
        border: 1px solid {DARK_BORDER};
    }}
    QListWidget::item:selected {{
        background-color: {DARK_SELECTION};
        color: {DARK_TEXT};
    }}
    QLineEdit {{
        background-color: {DARK_BG_INPUT};
        color: {DARK_TEXT};
        border: 1px solid {DARK_BORDER};
        padding: 3px;
    }}
    QLineEdit:focus {{
        border: 1px solid {DARK_ACCENT};
    }}
    QPushButton {{
        background-color: {DARK_BG_INPUT};
        color: {DARK_TEXT};
        border: 1px solid {DARK_BORDER};
        padding: 5px 15px;
        border-radius: 3px;
    }}
    QPushButton:hover {{
        background-color: {DARK_BG_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {DARK_BG_PRESSED};
    }}
    QPushButton:disabled {{
        background-color: {DARK_BG_PRIMARY};
        color: {DARK_TEXT_DISABLED};
    }}
    QDialogButtonBox QPushButton {{
        min-width: 70px;
    }}
    QStatusBar {{
        background-color: {DARK_STATUSBAR};
        color: {DARK_TEXT};
        border-top: 1px solid {DARK_BORDER};
    }}
    QStatusBar::item {{
        border: none;
    }}
    QLabel {{
        color: {DARK_TEXT};
        background-color: transparent;
    }}
    QInputDialog QLabel {{
        color: {DARK_TEXT};
    }}
    QMessageBox {{
        background-color: {DARK_BG_PRIMARY};
        color: {DARK_TEXT};
    }}
    QMessageBox QLabel {{
        color: {DARK_TEXT};
    }}
    QTextEdit {{
        background-color: {DARK_BG_PRIMARY};
        color: {DARK_TEXT};
        border: 1px solid {DARK_BORDER};
    }}
    QScrollBar:vertical {{
        background-color: {DARK_BG_PRIMARY};
        width: 14px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background-color: {DARK_BG_HOVER};
        min-height: 20px;
        border-radius: 3px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {DARK_BG_PRESSED};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: {DARK_BG_PRIMARY};
        height: 14px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {DARK_BG_HOVER};
        min-width: 20px;
        border-radius: 3px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {DARK_BG_PRESSED};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QHeaderView::section {{
        background-color: {DARK_BG_SECONDARY};
        color: {DARK_TEXT};
        border: 1px solid {DARK_BORDER};
        padding: 4px;
    }}
    QTreeWidget {{
        background-color: {DARK_BG_PRIMARY};
        color: {DARK_TEXT};
        border: 1px solid {DARK_BORDER};
        alternate-background-color: {DARK_BG_SECONDARY};
    }}
    QTreeWidget::item {{
        color: {DARK_TEXT};
    }}
    QTreeWidget::item:selected {{
        background-color: {DARK_SELECTION};
    }}
    QCheckBox {{
        color: {DARK_TEXT};
        spacing: 5px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
    }}
    QProgressBar {{
        background-color: {DARK_BG_INPUT};
        border: 1px solid {DARK_BORDER};
        border-radius: 3px;
        text-align: center;
        color: {DARK_TEXT};
    }}
    QProgressBar::chunk {{
        background-color: {DARK_ACCENT};
        border-radius: 2px;
    }}
    """

    LIGHT_STYLESHEET = f"""
    QMainWindow, QWidget {{
        background-color: {LIGHT_BG_PRIMARY};
        color: {LIGHT_TEXT};
    }}
    QMenuBar {{
        background-color: {LIGHT_BG_SECONDARY};
        color: {LIGHT_TEXT};
        border-bottom: 1px solid {LIGHT_BORDER};
    }}
    QMenuBar::item:selected {{
        background-color: {LIGHT_SELECTION};
    }}
    QMenu {{
        background-color: {LIGHT_BG_PRIMARY};
        color: {LIGHT_TEXT};
        border: 1px solid {LIGHT_BORDER};
    }}
    QMenu::item:selected {{
        background-color: {LIGHT_SELECTION};
    }}
    QMenu::separator {{
        height: 1px;
        background: {LIGHT_BORDER};
        margin: 4px 8px;
    }}
    QMdiArea {{
        background-color: {LIGHT_MDI_BG};
    }}
    QMdiSubWindow {{
        background-color: {LIGHT_BG_PRIMARY};
        color: {LIGHT_TEXT};
    }}
    QListWidget {{
        background-color: {LIGHT_BG_PRIMARY};
        color: {LIGHT_TEXT};
        border: 1px solid {LIGHT_BORDER};
    }}
    QListWidget::item:selected {{
        background-color: {LIGHT_SELECTION};
        color: {LIGHT_TEXT};
    }}
    QLineEdit {{
        background-color: {LIGHT_BG_INPUT};
        color: {LIGHT_TEXT};
        border: 1px solid {LIGHT_BORDER};
        padding: 3px;
    }}
    QLineEdit:focus {{
        border: 1px solid {LIGHT_ACCENT};
    }}
    QPushButton {{
        background-color: {LIGHT_BG_SECONDARY};
        color: {LIGHT_TEXT};
        border: 1px solid {LIGHT_BORDER};
        padding: 5px 15px;
        border-radius: 3px;
    }}
    QPushButton:hover {{
        background-color: {LIGHT_BG_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {LIGHT_BG_PRESSED};
    }}
    QPushButton:disabled {{
        background-color: {LIGHT_BG_SECONDARY};
        color: {LIGHT_TEXT_DISABLED};
    }}
    QDialogButtonBox QPushButton {{
        min-width: 70px;
    }}
    QStatusBar {{
        background-color: {LIGHT_STATUSBAR};
        color: {LIGHT_TEXT};
        border-top: 1px solid {LIGHT_BORDER};
    }}
    QStatusBar::item {{
        border: none;
    }}
    QLabel {{
        color: {LIGHT_TEXT};
        background-color: transparent;
    }}
    QInputDialog QLabel {{
        color: {LIGHT_TEXT};
    }}
    QMessageBox {{
        background-color: {LIGHT_BG_PRIMARY};
        color: {LIGHT_TEXT};
    }}
    QMessageBox QLabel {{
        color: {LIGHT_TEXT};
    }}
    QTextEdit {{
        background-color: {LIGHT_BG_PRIMARY};
        color: {LIGHT_TEXT};
        border: 1px solid {LIGHT_BORDER};
    }}
    QScrollBar:vertical {{
        background-color: {LIGHT_BG_SECONDARY};
        width: 14px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background-color: {LIGHT_BORDER};
        min-height: 20px;
        border-radius: 3px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {LIGHT_BG_HOVER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: {LIGHT_BG_SECONDARY};
        height: 14px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {LIGHT_BORDER};
        min-width: 20px;
        border-radius: 3px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {LIGHT_BG_HOVER};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QHeaderView::section {{
        background-color: {LIGHT_BG_SECONDARY};
        color: {LIGHT_TEXT};
        border: 1px solid {LIGHT_BORDER};
        padding: 4px;
    }}
    QTreeWidget {{
        background-color: {LIGHT_BG_PRIMARY};
        color: {LIGHT_TEXT};
        border: 1px solid {LIGHT_BORDER};
        alternate-background-color: {LIGHT_BG_SECONDARY};
    }}
    QTreeWidget::item {{
        color: {LIGHT_TEXT};
    }}
    QTreeWidget::item:selected {{
        background-color: {LIGHT_SELECTION};
    }}
    QCheckBox {{
        color: {LIGHT_TEXT};
        spacing: 5px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
    }}
    QProgressBar {{
        background-color: {LIGHT_BG_SECONDARY};
        border: 1px solid {LIGHT_BORDER};
        border-radius: 3px;
        text-align: center;
        color: {LIGHT_TEXT};
    }}
    QProgressBar::chunk {{
        background-color: {LIGHT_ACCENT};
        border-radius: 2px;
    }}
    """

    @staticmethod
    def apply(app: QApplication, dark_mode: bool) -> None:
        """Apply the appropriate theme to the application.

        Args:
            app: The QApplication instance.
            dark_mode: True for dark mode, False for light mode.
        """
        if dark_mode:
            app.setStyleSheet(ThemeManager.DARK_STYLESHEET)
        else:
            app.setStyleSheet(ThemeManager.LIGHT_STYLESHEET)

    @staticmethod
    def apply_to_mdi(mdi: QMdiArea, dark_mode: bool) -> None:
        """Explicitly set the QMdiArea background brush.

        QMdiArea ignores the background-color QSS property, so the
        background must be set via setBackground() directly.
        """
        if dark_mode:
            mdi.setBackground(QBrush(QColor(ThemeManager.DARK_MDI_BG)))
        else:
            mdi.setBackground(QBrush(QColor(ThemeManager.LIGHT_MDI_BG)))

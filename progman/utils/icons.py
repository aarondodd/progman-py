"""Icon generation utilities for Program Manager."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPixmap


def make_classic_fallback_icon(title: str, dark_mode: bool = False) -> QIcon:
    """Generate a simple 32x32 retro-ish fallback icon.

    Args:
        title: The program title (first letter is used).
        dark_mode: Whether to use dark mode colors.
    """
    size = 32
    pm = QPixmap(size, size)

    if dark_mode:
        bg_color = QColor("#3c3c3c")
        border_color = QColor("#e0e0e0")
        highlight_light = QColor("#555555")
        highlight_dark = QColor("#2b2b2b")
        text_color = QColor("#569cd6")
    else:
        bg_color = QColor("#C0C0C0")
        border_color = QColor("#000000")
        highlight_light = QColor("#FFFFFF")
        highlight_dark = QColor("#808080")
        text_color = QColor("#000080")

    pm.fill(bg_color)

    p = QPainter(pm)
    p.setPen(border_color)
    p.drawRect(0, 0, size - 1, size - 1)

    # Inner raised look
    p.setPen(highlight_light)
    p.drawLine(1, 1, size - 2, 1)
    p.drawLine(1, 1, 1, size - 2)
    p.setPen(highlight_dark)
    p.drawLine(1, size - 2, size - 2, size - 2)
    p.drawLine(size - 2, 1, size - 2, size - 2)

    ch = (title.strip()[:1] or "?").upper()
    p.setPen(text_color)
    font = QFont()
    font.setBold(True)
    font.setPointSize(14)
    p.setFont(font)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, ch)

    p.end()
    return QIcon(pm)


def make_group_icon(dark_mode: bool = False) -> QIcon:
    """Generate a simple 16x16 group/folder icon for MDI sub-windows.

    Args:
        dark_mode: Whether to use dark mode colors.
    """
    size = 16
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    if dark_mode:
        outline_color = QColor("#e0e0e0")
        folder_color = QColor("#d4a017")
    else:
        outline_color = QColor("#000000")
        folder_color = QColor("#FFFF00")

    p.setPen(outline_color)
    p.setBrush(QBrush(folder_color))

    # Folder tab
    p.drawRect(2, 2, 5, 2)
    # Folder body
    p.drawRect(2, 4, 12, 10)

    p.end()
    return QIcon(pm)

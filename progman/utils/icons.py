"""Icon generation utilities for Program Manager."""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QFileInfo, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QFileIconProvider

# Extensions that may contain embedded icons on Windows
_EXECUTABLE_EXTENSIONS = {".exe", ".dll", ".ico"}


def icon_for_executable(path: str) -> Optional[QIcon]:
    """Extract an icon from a Windows executable, DLL, or .ico file.

    Uses Qt's QFileIconProvider which delegates to the native platform
    icon lookup.  On Windows this extracts the embedded icon from PE
    files.  Returns None if the file does not exist or has no icon.
    """
    if not path or not Path(path).is_file():
        return None

    try:
        provider = QFileIconProvider()
        icon = provider.icon(QFileInfo(path))
        # QFileIconProvider always returns *something* (at minimum the
        # platform's generic file icon).  Check that it has pixel data
        # of a reasonable size to filter out blank results.
        pixmap = icon.pixmap(32, 32)
        if pixmap.isNull() or pixmap.width() < 8:
            return None
        return icon
    except Exception:
        return None


def is_executable_icon(path: str) -> bool:
    """Return True if *path* looks like a Windows executable icon source."""
    return Path(path).suffix.lower() in _EXECUTABLE_EXTENSIONS


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


def icon_for_uwp_app(aumid: str) -> Optional[QIcon]:
    """Extract icon from a UWP app's package assets.

    Args:
        aumid: Application User Model ID (e.g., Microsoft.WindowsTerminal_8wekyb3d8bbwe!App)

    Returns:
        QIcon if found, None otherwise.
    """
    if "!" not in aumid:
        return None

    package_family = aumid.split("!")[0]

    # Find install location
    install_path = _find_uwp_install_path(package_family)
    if not install_path:
        return None

    manifest_path = Path(install_path) / "AppxManifest.xml"
    if not manifest_path.exists():
        return None

    # Parse manifest for logo path
    logo_path = _parse_manifest_logo(manifest_path, install_path)
    if logo_path and Path(logo_path).exists():
        return QIcon(logo_path)

    return None


def _find_uwp_install_path(package_family: str) -> Optional[str]:
    """Find the install path for a UWP package.

    Searches the WindowsApps directory for matching package folders.
    """
    windows_apps = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "WindowsApps"

    if not windows_apps.exists():
        return None

    try:
        # Package folders are named: PackageName_Version_Architecture_ResourceId_PublisherHash
        # Package family is: PackageName_PublisherHash
        for folder in windows_apps.iterdir():
            if not folder.is_dir():
                continue
            folder_name = folder.name
            # Check if this folder matches the package family pattern
            parts = folder_name.split("_")
            if len(parts) >= 2:
                # Reconstruct family name: first part + last part
                reconstructed = f"{parts[0]}_{parts[-1]}"
                if reconstructed == package_family:
                    return str(folder)
    except PermissionError:
        # WindowsApps is often protected
        pass

    return None


def _parse_manifest_logo(manifest_path: Path, install_path: str) -> Optional[str]:
    """Parse AppxManifest.xml to find the app logo.

    Args:
        manifest_path: Path to AppxManifest.xml
        install_path: Root installation path of the package

    Returns:
        Resolved path to the logo file, or None if not found.
    """
    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()

        # Handle namespaces - AppxManifest uses several
        ns = {
            "default": "http://schemas.microsoft.com/appx/manifest/foundation/windows10",
            "uap": "http://schemas.microsoft.com/appx/manifest/uap/windows10",
            "uap3": "http://schemas.microsoft.com/appx/manifest/uap/windows10/3",
        }

        # Also try without namespace prefix for older manifests
        for app in root.findall(".//default:Application", ns):
            visual = app.find("uap:VisualElements", ns)
            if visual is not None:
                # Try different logo attributes in preference order
                for attr in ["Square44x44Logo", "Square150x150Logo", "Square71x71Logo"]:
                    logo = visual.get(attr)
                    if logo:
                        resolved = _resolve_uwp_logo(install_path, logo)
                        if resolved:
                            return resolved

        # Try without namespace (fallback for older manifests)
        for app in root.iter():
            if app.tag.endswith("VisualElements"):
                for attr in ["Square44x44Logo", "Square150x150Logo", "Square71x71Logo"]:
                    logo = app.get(attr)
                    if logo:
                        resolved = _resolve_uwp_logo(install_path, logo)
                        if resolved:
                            return resolved

    except ET.ParseError:
        pass
    except Exception:
        pass

    return None


def _resolve_uwp_logo(install_path: str, logo_relative: str) -> Optional[str]:
    """Resolve a UWP logo path with scale variants.

    UWP apps often have multiple versions of logos at different scales.
    This function tries to find the best available version.

    Args:
        install_path: Root installation path
        logo_relative: Relative path from manifest (e.g., "Assets\\Square44x44Logo.png")

    Returns:
        Absolute path to the logo file, or None if not found.
    """
    base = Path(install_path) / logo_relative

    # Try exact path first
    if base.exists():
        return str(base)

    # Try scale variants
    parent = base.parent
    stem = base.stem
    suffix = base.suffix

    if not parent.exists():
        return None

    # Try scale variants (smaller first for icons)
    for scale in ["scale-100", "scale-125", "scale-150", "scale-200", "scale-400"]:
        candidate = parent / f"{stem}.{scale}{suffix}"
        if candidate.exists():
            return str(candidate)

    # Try targetsize variants (commonly used for app icons)
    for size in [44, 48, 32, 64, 24, 16, 256]:
        candidate = parent / f"{stem}.targetsize-{size}{suffix}"
        if candidate.exists():
            return str(candidate)
        # Also try with _altform-unplated suffix
        candidate_unplated = parent / f"{stem}.targetsize-{size}_altform-unplated{suffix}"
        if candidate_unplated.exists():
            return str(candidate_unplated)

    # Try contrast variants
    for contrast in ["contrast-white", "contrast-black"]:
        candidate = parent / f"{stem}.{contrast}{suffix}"
        if candidate.exists():
            return str(candidate)

    return None

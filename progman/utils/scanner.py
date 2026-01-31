"""Platform-specific application discovery for Program Manager.

Scans the system for installed applications and returns them as
potential ProgramItem candidates grouped by category.
"""

import configparser
import os
import platform
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DiscoveredApp:
    """Represents an application found on the system."""

    name: str
    command: str
    icon_path: str = ""
    group: str = "Uncategorized"


# FreeDesktop category -> friendly group name mapping
CATEGORY_MAP = {
    "AudioVideo": "Multimedia",
    "Audio": "Multimedia",
    "Video": "Multimedia",
    "Development": "Development",
    "Education": "Education",
    "Game": "Games",
    "Graphics": "Graphics",
    "Network": "Internet",
    "Office": "Office",
    "Science": "Science",
    "Settings": "Settings",
    "System": "System Tools",
    "Utility": "Accessories",
    "Accessories": "Accessories",
}


def scan_applications() -> List[DiscoveredApp]:
    """Scan for installed applications on the current platform."""
    system = platform.system()
    if system == "Linux":
        return _scan_linux()
    elif system == "Windows":
        return _scan_windows()
    elif system == "Darwin":
        return _scan_macos()
    return []


def _scan_linux() -> List[DiscoveredApp]:
    """Scan .desktop files on Linux."""
    apps = []
    search_dirs = [
        Path("/usr/share/applications"),
        Path("/usr/local/share/applications"),
        Path.home() / ".local/share/applications",
        Path("/var/lib/flatpak/exports/share/applications"),
        Path.home() / ".local/share/flatpak/exports/share/applications",
        Path("/var/lib/snapd/desktop/applications"),
    ]

    seen_commands = set()

    for app_dir in search_dirs:
        if not app_dir.is_dir():
            continue

        for desktop_file in app_dir.glob("*.desktop"):
            app = _parse_desktop_file(desktop_file)
            if app and app.command not in seen_commands:
                seen_commands.add(app.command)
                apps.append(app)

    apps.sort(key=lambda a: a.name.lower())
    return apps


def _parse_desktop_file(path: Path) -> Optional[DiscoveredApp]:
    """Parse a .desktop file and return a DiscoveredApp if valid."""
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str  # Preserve case

    try:
        config.read(str(path), encoding="utf-8")
    except (configparser.Error, UnicodeDecodeError):
        return None

    if "Desktop Entry" not in config:
        return None

    entry = config["Desktop Entry"]

    # Skip hidden or non-display entries
    if entry.get("NoDisplay", "false").lower() == "true":
        return None
    if entry.get("Hidden", "false").lower() == "true":
        return None
    if entry.get("Type", "") != "Application":
        return None

    name = entry.get("Name", "")
    exec_cmd = entry.get("Exec", "")
    icon = entry.get("Icon", "")
    categories = entry.get("Categories", "")

    if not name or not exec_cmd:
        return None

    # Strip field codes from Exec
    exec_cmd = re.sub(r"\s+%[fFuUdDnNickvm]", "", exec_cmd).strip()

    # Determine group from categories
    group = "Uncategorized"
    if categories:
        for cat in categories.split(";"):
            cat = cat.strip()
            if cat in CATEGORY_MAP:
                group = CATEGORY_MAP[cat]
                break

    # Resolve icon path
    icon_path = _resolve_linux_icon(icon)

    return DiscoveredApp(
        name=name,
        command=exec_cmd,
        icon_path=icon_path,
        group=group,
    )


def _resolve_linux_icon(icon: str) -> str:
    """Try to resolve an icon name to an absolute path."""
    if not icon:
        return ""

    # Already an absolute path
    if os.path.isabs(icon) and os.path.exists(icon):
        return icon

    # Search common icon directories for the icon name
    icon_dirs = [
        Path("/usr/share/icons/hicolor"),
        Path("/usr/share/pixmaps"),
        Path.home() / ".local/share/icons/hicolor",
    ]

    preferred_sizes = ["48x48", "32x32", "64x64", "128x128", "scalable", "256x256"]
    extensions = [".png", ".svg", ".xpm"]

    for icon_dir in icon_dirs:
        if not icon_dir.is_dir():
            continue

        for size in preferred_sizes:
            for category in ["apps", "devices", "mimetypes"]:
                for ext in extensions:
                    candidate = icon_dir / size / category / f"{icon}{ext}"
                    if candidate.exists():
                        return str(candidate)

    # Check pixmaps directly
    pixmaps_dir = Path("/usr/share/pixmaps")
    if pixmaps_dir.is_dir():
        for ext in extensions:
            candidate = pixmaps_dir / f"{icon}{ext}"
            if candidate.exists():
                return str(candidate)

    return ""


def _scan_windows() -> List[DiscoveredApp]:
    """Scan Start Menu folders on Windows."""
    apps = []
    start_menu_dirs = []

    # Common start menu locations
    program_data = os.environ.get("ProgramData", r"C:\ProgramData")
    appdata = os.environ.get("APPDATA", "")

    start_menu_dirs.append(
        Path(program_data) / "Microsoft/Windows/Start Menu/Programs"
    )
    if appdata:
        start_menu_dirs.append(
            Path(appdata) / "Microsoft/Windows/Start Menu/Programs"
        )

    seen_names = set()

    for start_dir in start_menu_dirs:
        if not start_dir.is_dir():
            continue

        for lnk_file in start_dir.rglob("*.lnk"):
            app = _parse_lnk_file(lnk_file, start_dir)
            if app and app.name not in seen_names:
                seen_names.add(app.name)
                apps.append(app)

    apps.sort(key=lambda a: a.name.lower())
    return apps


def _parse_lnk_file(lnk_path: Path, start_dir: Path) -> Optional[DiscoveredApp]:
    """Parse a Windows .lnk shortcut using PowerShell."""
    try:
        ps_cmd = (
            f'(New-Object -ComObject WScript.Shell)'
            f'.CreateShortcut("{lnk_path}") | '
            f'Select-Object -Property TargetPath,WorkingDirectory,IconLocation | '
            f'ConvertTo-Json'
        )
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        import json
        data = json.loads(result.stdout)

        target = data.get("TargetPath", "")
        if not target:
            return None

        # Skip uninstallers and system utilities
        lower_target = target.lower()
        if any(skip in lower_target for skip in ["uninstall", "unins0"]):
            return None

        name = lnk_path.stem
        icon_loc = data.get("IconLocation", "")
        icon_path = ""
        if icon_loc and "," in icon_loc:
            icon_path = icon_loc.split(",")[0].strip()
            if icon_path and not os.path.exists(icon_path):
                icon_path = ""

        # Determine group from subfolder
        relative = lnk_path.parent.relative_to(start_dir)
        group = str(relative) if str(relative) != "." else "Programs"

        return DiscoveredApp(
            name=name,
            command=target,
            icon_path=icon_path,
            group=group,
        )

    except Exception:
        return None


def _scan_macos() -> List[DiscoveredApp]:
    """Scan /Applications on macOS."""
    apps = []
    app_dirs = [
        Path("/Applications"),
        Path.home() / "Applications",
    ]

    seen_names = set()

    for app_dir in app_dirs:
        if not app_dir.is_dir():
            continue

        for app_bundle in app_dir.glob("*.app"):
            app = _parse_macos_app(app_bundle)
            if app and app.name not in seen_names:
                seen_names.add(app.name)
                apps.append(app)

    apps.sort(key=lambda a: a.name.lower())
    return apps


def _parse_macos_app(app_bundle: Path) -> Optional[DiscoveredApp]:
    """Parse a macOS .app bundle's Info.plist."""
    import plistlib

    plist_path = app_bundle / "Contents/Info.plist"
    if not plist_path.exists():
        return None

    try:
        with open(plist_path, "rb") as f:
            plist = plistlib.load(f)

        name = plist.get("CFBundleDisplayName") or plist.get("CFBundleName", "")
        if not name:
            name = app_bundle.stem

        command = f'open -a "{app_bundle}"'

        # Icon
        icon_file = plist.get("CFBundleIconFile", "")
        icon_path = ""
        if icon_file:
            if not icon_file.endswith(".icns"):
                icon_file += ".icns"
            candidate = app_bundle / "Contents/Resources" / icon_file
            if candidate.exists():
                icon_path = str(candidate)

        return DiscoveredApp(
            name=name,
            command=command,
            icon_path=icon_path,
            group="Applications",
        )

    except Exception:
        return None

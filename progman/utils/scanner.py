"""Platform-specific application discovery for Program Manager.

Scans the system for installed applications and returns them as
potential ProgramItem candidates grouped by category.
"""

import configparser
import os
import platform
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


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

# Windows app AUMID prefix -> category mapping
WINDOWS_APP_CATEGORIES = {
    "Microsoft.WindowsCalculator": "Accessories",
    "Microsoft.WindowsTerminal": "System Tools",
    "Microsoft.Paint": "Accessories",
    "Microsoft.Photos": "Multimedia",
    "Microsoft.WindowsCamera": "Multimedia",
    "Microsoft.WindowsNotepad": "Accessories",
    "Microsoft.WindowsStore": "System Tools",
    "Microsoft.MicrosoftEdge": "Internet",
    "Microsoft.ScreenSketch": "Accessories",
    "Microsoft.Windows.DevHome": "Development",
    "Microsoft.VisualStudio": "Development",
    "Microsoft.VSCode": "Development",
    "Microsoft.ZuneMusic": "Multimedia",
    "Microsoft.ZuneVideo": "Multimedia",
    "Microsoft.Windows.Photos": "Multimedia",
    "Microsoft.WindowsMaps": "Accessories",
    "Microsoft.WindowsAlarms": "Accessories",
    "Microsoft.BingWeather": "Accessories",
    "Microsoft.BingNews": "Internet",
    "Microsoft.GetHelp": "System Tools",
    "Microsoft.MicrosoftStickyNotes": "Accessories",
    "Microsoft.Todos": "Office",
    "Microsoft.Office": "Office",
    "Microsoft.MicrosoftOfficeHub": "Office",
    "Microsoft.PowerAutomateDesktop": "Office",
    "Microsoft.Xbox": "Games",
    "Microsoft.GamingApp": "Games",
    "Microsoft.XboxGamingOverlay": "Games",
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


def _categorize_windows_app(name: str, aumid: str) -> str:
    """Categorize a Windows app based on its name or AUMID."""
    # Check AUMID prefix against known categories
    for prefix, category in WINDOWS_APP_CATEGORIES.items():
        if aumid.startswith(prefix):
            return category

    # Fallback heuristics based on name
    name_lower = name.lower()
    if any(kw in name_lower for kw in ["game", "xbox"]):
        return "Games"
    if any(kw in name_lower for kw in ["office", "word", "excel", "powerpoint", "outlook"]):
        return "Office"
    if any(kw in name_lower for kw in ["visual studio", "code", "developer", "studio"]):
        return "Development"
    if any(kw in name_lower for kw in ["browser", "edge", "chrome", "firefox", "internet"]):
        return "Internet"
    if any(kw in name_lower for kw in ["media", "player", "music", "video", "photo"]):
        return "Multimedia"

    return "Programs"


def is_aumid(command: str) -> bool:
    """Check if command looks like a UWP Application User Model ID (AUMID).

    AUMIDs have the format: PackageFamilyName!ApplicationId
    Example: Microsoft.WindowsTerminal_8wekyb3d8bbwe!App
    """
    if "!" not in command:
        return False
    # If the part before '!' is an existing file path, it's not an AUMID
    prefix = command.split("!")[0]
    return not os.path.exists(prefix)


def _scan_windows_shell() -> List[DiscoveredApp]:
    """Scan shell:AppsFolder for all launchable applications using COM.

    This enumerates the virtual shell folder that contains all installed
    applications, including both traditional Win32 apps and modern UWP/MSIX apps.
    """
    from win32com.shell import shell, shellcon

    apps = []
    seen_names = set()

    # Get desktop folder as entry point
    desktop = shell.SHGetDesktopFolder()

    # Parse shell:AppsFolder to get its PIDL
    # ParseDisplayName returns (pidl, eaten, attributes) - we only need pidl
    result = desktop.ParseDisplayName(0, None, "shell:AppsFolder")
    pidl = result[0] if isinstance(result, tuple) else result

    # Bind to AppsFolder
    apps_folder = desktop.BindToObject(pidl, None, shell.IID_IShellFolder)

    # Enumerate all items (non-folders = apps)
    enum = apps_folder.EnumObjects(0, shellcon.SHCONTF_NONFOLDERS)

    while True:
        pidls = enum.Next(1)
        if not pidls:
            break

        item_pidl = pidls[0]

        try:
            # Get display name (user-visible)
            name = apps_folder.GetDisplayNameOf(item_pidl, shellcon.SHGDN_NORMAL)

            # Get parsing name (AUMID for UWP or exe path for traditional)
            aumid = apps_folder.GetDisplayNameOf(item_pidl, shellcon.SHGDN_FORPARSING)

            if name in seen_names:
                continue
            seen_names.add(name)

            # Skip uninstallers
            if "uninstall" in name.lower():
                continue

            # Get icon path (for traditional apps, use the exe path)
            icon_path = ""
            if not is_aumid(aumid) and os.path.exists(aumid):
                icon_path = aumid

            # Categorize the app
            group = _categorize_windows_app(name, aumid)

            apps.append(DiscoveredApp(
                name=name,
                command=aumid,
                icon_path=icon_path,
                group=group,
            ))
        except Exception:
            continue

    return sorted(apps, key=lambda a: a.name.lower())


def _scan_windows_lnk() -> List[DiscoveredApp]:
    """Scan Start Menu folders on Windows for .lnk shortcuts.

    This is the fallback method when pywin32 is not available.
    """
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


def _scan_windows() -> List[DiscoveredApp]:
    """Scan for Windows applications.

    Tries shell namespace enumeration first (discovers all apps including UWP),
    falls back to .lnk scanning if pywin32 is not available.
    """
    try:
        return _scan_windows_shell()
    except ImportError:
        # pywin32 not available, fall back to .lnk scanning
        return _scan_windows_lnk()
    except Exception:
        # Shell enumeration failed, fall back
        return _scan_windows_lnk()


def _parse_lnk_file(lnk_path: Path, start_dir: Path) -> Optional[DiscoveredApp]:
    """Parse a Windows .lnk shortcut by reading the binary format directly.

    Implements the MS-SHLLINK binary format (Shell Link) using struct.
    No subprocess or COM calls needed.
    """
    data = _parse_lnk_binary(lnk_path)
    if data is None:
        return None

    target = data.get("target_path", "")
    if not target:
        return None

    # Skip uninstallers and system utilities
    lower_target = target.lower()
    if any(skip in lower_target for skip in ["uninstall", "unins0"]):
        return None

    name = lnk_path.stem
    icon_path = data.get("icon_location", "")
    if icon_path and "," in icon_path:
        icon_path = icon_path.split(",")[0].strip()
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


def _parse_lnk_binary(lnk_path: Path) -> Optional[dict]:
    """Parse the MS-SHLLINK binary format and extract target path and icon.

    Reference: [MS-SHLLINK] Shell Link Binary File Format
    https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-shllink/
    """
    try:
        with open(lnk_path, "rb") as f:
            buf = f.read()
    except OSError:
        return None

    # ShellLinkHeader is 76 bytes; first 4 bytes are header size (must be 0x4C)
    if len(buf) < 76:
        return None
    header_size = struct.unpack_from("<I", buf, 0)[0]
    if header_size != 0x4C:
        return None

    flags = struct.unpack_from("<I", buf, 20)[0]
    has_target_id_list = bool(flags & 0x01)
    has_link_info = bool(flags & 0x02)
    has_name = bool(flags & 0x04)
    has_relative_path = bool(flags & 0x08)
    has_working_dir = bool(flags & 0x10)
    has_arguments = bool(flags & 0x20)
    has_icon_location = bool(flags & 0x40)
    is_unicode = bool(flags & 0x80)

    offset = 76

    # Skip LinkTargetIDList
    if has_target_id_list:
        if offset + 2 > len(buf):
            return None
        id_list_size = struct.unpack_from("<H", buf, offset)[0]
        offset += 2 + id_list_size

    # Parse LinkInfo for local base path
    target_path = ""
    if has_link_info:
        if offset + 28 > len(buf):
            return None
        link_info_size = struct.unpack_from("<I", buf, offset)[0]
        link_info_start = offset
        link_info_header_size = struct.unpack_from("<I", buf, offset + 4)[0]
        link_info_flags = struct.unpack_from("<I", buf, offset + 8)[0]

        if link_info_flags & 0x01:  # VolumeIDAndLocalBasePath
            local_base_path_off = struct.unpack_from("<I", buf, offset + 16)[0]
            path_start = link_info_start + local_base_path_off
            if path_start < len(buf):
                # Null-terminated ANSI string
                end = buf.index(b"\x00", path_start)
                target_path = buf[path_start:end].decode("cp1252", errors="replace")

            # Prefer Unicode local base path if available
            if link_info_header_size >= 0x24 and offset + 32 <= len(buf):
                unicode_off = struct.unpack_from("<I", buf, offset + 28)[0]
                if unicode_off:
                    upath_start = link_info_start + unicode_off
                    if upath_start < len(buf):
                        target_path = _read_utf16z(buf, upath_start)

        offset = link_info_start + link_info_size

    # Parse StringData sections (order is fixed by the spec)
    def _read_counted_string() -> str:
        nonlocal offset
        if offset + 2 > len(buf):
            return ""
        count = struct.unpack_from("<H", buf, offset)[0]
        offset += 2
        if is_unicode:
            byte_count = count * 2
            if offset + byte_count > len(buf):
                return ""
            s = buf[offset : offset + byte_count].decode(
                "utf-16-le", errors="replace"
            )
            offset += byte_count
        else:
            if offset + count > len(buf):
                return ""
            s = buf[offset : offset + count].decode("cp1252", errors="replace")
            offset += count
        return s

    name_string = _read_counted_string() if has_name else ""
    relative_path = _read_counted_string() if has_relative_path else ""
    working_dir = _read_counted_string() if has_working_dir else ""
    arguments = _read_counted_string() if has_arguments else ""
    icon_location = _read_counted_string() if has_icon_location else ""

    # Relative path as fallback for target
    if not target_path and relative_path:
        target_path = relative_path

    return {
        "target_path": target_path,
        "working_dir": working_dir,
        "icon_location": icon_location,
    }


def _read_utf16z(buf: bytes, offset: int) -> str:
    """Read a null-terminated UTF-16LE string from *buf* at *offset*."""
    chars = []
    while offset + 1 < len(buf):
        code_unit = struct.unpack_from("<H", buf, offset)[0]
        if code_unit == 0:
            break
        chars.append(chr(code_unit))
        offset += 2
    return "".join(chars)


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

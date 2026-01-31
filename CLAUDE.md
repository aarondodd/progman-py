# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A cross-platform PyQt6-based recreation of the Windows 3.x Program Manager. Structured as a Python package (`progman/`) with a thin `main.py` entry point.

## Development Commands

### Running the application
```bash
python main.py
```

### Running tests
```bash
source .venv/bin/activate
QT_QPA_PLATFORM=offscreen pytest tests/ -v
```

### Building executable
```bash
# Linux/macOS
./build.sh

# Windows (PowerShell)
./build.ps1

# Manual build command
pyinstaller --noconfirm --clean --windowed --onefile --name progman --collect-all PyQt6 main.py
```

The built executable appears in `dist/progman` (or `dist/progman.exe` on Windows).

### Installing dependencies
```bash
pip install -r requirements.txt

# For development/testing
pip install -r requirements-dev.txt

# For building executables
pip install pyinstaller
```

## Architecture

### Package Structure
```
progman-py/
├── main.py                           # Thin entry point: creates QApp, AppModel, MainWindow
├── progman/
│   ├── __init__.py                   # Re-exports __version__
│   ├── version.py                    # Single source of truth: "1.0.0"
│   ├── app.py                        # MainWindow + UpgradeWorker + UpgradeProgressDialog
│   ├── models/
│   │   ├── program_item.py           # ProgramItem dataclass
│   │   ├── program_group.py          # ProgramGroup dataclass
│   │   └── app_model.py              # AppModel (config load/save/migration)
│   ├── widgets/
│   │   ├── group_window.py           # GroupWindow (MDI child) with drag-and-drop
│   │   ├── program_item_dialog.py    # ProgramItemDialog + QLineEditWithBrowse
│   │   └── scan_dialog.py            # ScanForProgramsDialog
│   ├── utils/
│   │   ├── config.py                 # Config dir, version check timestamps
│   │   ├── icons.py                  # make_classic_fallback_icon(), make_group_icon()
│   │   ├── launcher.py               # Launcher class
│   │   ├── scanner.py                # Platform-specific app discovery
│   │   ├── theme.py                  # ThemeManager with light/dark stylesheets
│   │   └── updater.py                # GitHub-based update checker
│   └── workers/
│       └── scan_worker.py            # Background program scanning
└── tests/
    ├── conftest.py                   # QApp fixture, tmp_config, offscreen setup
    ├── test_models.py
    ├── test_config_migration.py
    ├── test_launcher.py
    ├── test_scanner.py
    ├── test_theme.py
    ├── test_updater.py
    ├── test_widgets.py
    └── test_drag_drop.py
```

### Key Components

**version.py**
- Single source of truth for version number
- Exports `__version__`, `VERSION_TUPLE`, `get_version()`

**AppModel** (`models/app_model.py`)
- Config load/save with JSON persistence at `~/.progman.json`
- Config migration system: `config_version` field, `_migrate_v0_to_v1()` for old format upgrade
- Fields: `dark_mode` (bool), `layout_state` (JSON string), `groups`, `github` (dict)

**ThemeManager** (`utils/theme.py`)
- Static class with centralized color constants
- `DARK_STYLESHEET` and `LIGHT_STYLESHEET` as class-level QSS strings
- `apply(app, dark_mode)` sets the application-wide stylesheet
- All colors defined as class constants (e.g., `DARK_BG_PRIMARY`, `LIGHT_ACCENT`)

**GroupWindow** (`widgets/group_window.py`)
- MDI child window with QListWidget in IconMode
- Drag-and-drop: within-group reorder + cross-group transfer
- Module-level `_drag_state` dict tracks active drag for cross-group moves
- `items_changed` signal triggers auto-save

**Scanner** (`utils/scanner.py`)
- Platform-specific: `_scan_linux()`, `_scan_windows()`, `_scan_macos()`
- Linux: parses .desktop files, maps FreeDesktop categories
- Windows: PowerShell-based .lnk parsing (no pywin32)
- macOS: plistlib-based Info.plist parsing

**Updater** (`utils/updater.py`)
- GitHub public API (no auth): `GET /repos/{owner}/{repo}/releases/latest`
- 7-day check interval via timestamp file at `~/.progman/.version_check`
- Version comparison via tuple comparison
- Download/extract/build pipeline with progress callbacks

**MainWindow** (`app.py`)
- QMainWindow with QMdiArea
- Menus: File (new group, scan, save, exit), View (dark mode), Group (rename, delete), Window (tile, cascade), Help (updates, about)
- `UpgradeWorker` (QThread) + `UpgradeProgressDialog` for self-upgrade
- Auto-check for updates 2s after startup

### Data Flow

1. **Startup**: `main.py` → `AppModel()` loads config → `ThemeManager.apply()` → `MainWindow()` creates MDI windows
2. **Config migration**: `AppModel.load()` detects `config_version < 1` → `_migrate_v0_to_v1()` → auto-save
3. **Theme toggle**: View menu → `_toggle_dark_mode()` → `ThemeManager.apply()` → updates all GroupWindows → save
4. **Launch item**: Double-click → `GroupWindow._on_item_double_clicked()` → `Launcher.launch()` → `subprocess.Popen()`
5. **Drag-drop**: Source sets `_drag_state` → target receives item → source removes → both emit `items_changed` → auto-save
6. **Scan programs**: File menu → `ScanWorker` (QThread) → `ScanForProgramsDialog` → creates groups/items → save
7. **Update check**: `QTimer.singleShot(2000)` → `check_for_updates()` → shows notification if newer version available

### Configuration Format (v1)

```json
{
  "config_version": 1,
  "dark_mode": false,
  "layout_state": "[{\"title\": \"...\", \"geometry\": [x,y,w,h], \"state\": \"normal\"}]",
  "github": {"owner": "aarondodd", "repo": "progman-py"},
  "groups": [...]
}
```

## Important Constraints

- **Virtual environment**: Always activate `.venv` before running or testing (`source .venv/bin/activate`)
- **Cross-platform**: Test changes work on Windows (shell commands, paths) and Linux/macOS
- **Theme centralization**: All colors defined in `ThemeManager` class constants. Don't add colors elsewhere
- **Config migration**: When changing config format, increment `CONFIG_VERSION` and add a migration function
- **Tests run headless**: `QT_QPA_PLATFORM=offscreen` is set in `conftest.py`
- **Tests use temp configs**: Never touch `~/.progman.json` in tests - use `tmp_path` fixtures

## Common Patterns

### Adding a new menu action
1. Create QAction in `MainWindow._build_menubar()` in `app.py`
2. Connect to handler method
3. Call `self._save()` if state changes

### Adding a config field
1. Add field to `AppModel.__init__()`
2. Read it in `AppModel.load()`
3. Write it in `AppModel.save()`
4. If format change: increment `CONFIG_VERSION`, add migration function

### Modifying theme colors
1. Update the color constant in `ThemeManager` (e.g., `DARK_BG_PRIMARY`)
2. The constant is used in the stylesheet template automatically

### Adding a new widget
1. Create in `progman/widgets/`
2. Import in `progman/widgets/__init__.py`
3. Add tests in `tests/`

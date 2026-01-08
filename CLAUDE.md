# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A cross-platform PyQt6-based recreation of the Windows 3.x Program Manager. Single-file application (`progman.py`) that provides a retro MDI interface for organizing and launching programs.

## Development Commands

### Running the application
```bash
python progman.py
```

### Building executable
```bash
# Linux/macOS
./build.sh

# Windows
build.cmd

# Manual build command
pyinstaller --noconfirm --clean --windowed --onefile --name progman progman.py
```

The built executable appears in `dist/progman` (or `dist/progman.exe` on Windows).

### Installing dependencies
```bash
pip install -r requirements.txt

# For building executables
pip install pyinstaller
```

## Architecture

### Single-File Design
The entire application lives in `progman.py` (~865 lines). All UI, models, and logic are in this one file. When making changes, be aware that:
- No module imports from other project files
- All classes and functions are in the same namespace
- Changes ripple through the entire application in one file

### Key Components (in order of appearance in file)

**ThemeManager** (lines 62-122)
- Static class managing application-wide theme switching
- Two themes: "system" (Qt defaults) and "classic" (Win 3.x palette)
- `apply()` method modifies QApplication palette and stylesheet globally
- Classic theme uses hardcoded hex colors (#C0C0C0, #000080, etc.)

**make_classic_fallback_icon()** (lines 124-156)
- Generates 32×32 QIcon at runtime when no custom icon provided
- Creates retro-style tile with raised border and blue initial letter
- Used by every item without an `icon_path`

**Data Models** (lines 164-273)
- `ProgramItem`: Dataclass for individual launchable programs (title, command, working_dir, icon_path)
- `ProgramGroup`: Container for lists of ProgramItems
- `AppModel`: Global application state holding all groups, theme choice, and MDI window layout
- All models have `to_dict()`/`from_dict()` for JSON serialization
- Config stored in `~/.progman.json` by default

**Launcher** (lines 280-305)
- Static class with single `launch()` method
- Uses `subprocess.Popen()` with `shell=True` for cross-platform compatibility
- Shows QMessageBox on launch failures

**ProgramItemDialog** (lines 313-402)
- Modal dialog for creating/editing program items
- Uses composite `QLineEditWithBrowse` widgets (lines 405-457) for file/directory selection
- Enforces required fields (title and command) before accepting

**GroupWindow** (lines 465-570)
- MDI child window displaying one ProgramGroup
- Icon view using QListWidget in IconMode
- Context menu for New/Edit/Delete operations on items
- Double-click launches the program
- Stores reference to `ProgramItem` in list item's UserRole data

**MainWindow** (lines 578-843)
- QMainWindow with QMdiArea as central widget
- Creates one QMdiSubWindow per group
- Menu structure: File (new group, save, exit), View (colors), Group (rename, delete), Window (tile, cascade)
- `_capture_layout()` / `_restore_layout()` serialize/deserialize window positions and states
- Auto-saves on close via `closeEvent()`

### Data Flow

1. **Startup**: `main()` → `AppModel()` loads `~/.progman.json` → `MainWindow()` creates MDI windows for each group
2. **Launch Item**: Double-click item → `GroupWindow._on_item_double_clicked()` → `Launcher.launch()` → `subprocess.Popen()`
3. **Edit Item**: Context menu → `ProgramItemDialog` → modifies `ProgramItem` in-place → `GroupWindow.refresh_items()` updates UI
4. **Theme Switch**: Menu action → `MainWindow._set_theme()` → `ThemeManager.apply()` → modifies QApplication palette/stylesheet → auto-saves
5. **Save**: Any action triggers `MainWindow._save()` → `_capture_layout()` → `AppModel.save()` → writes JSON

### Configuration Format

`~/.progman.json` structure:
```json
{
  "theme": "system" | "classic",
  "layout_state": "[{\"title\": \"...\", \"geometry\": [x,y,w,h], \"state\": \"normal|minimized|maximized\"}]",
  "groups": [
    {
      "title": "Group Name",
      "items": [
        {
          "title": "Item Title",
          "command": "executable path or shell command",
          "working_dir": "optional working directory",
          "icon_path": "optional icon file path"
        }
      ]
    }
  ]
}
```

## Important Constraints

- **Single file**: Don't split into modules. All code must remain in `progman.py`.
- **Cross-platform**: Test changes work on Windows (shell commands, paths) and Linux/macOS.
- **No external icon assets required**: Fallback icons are always generated at runtime.
- **shell=True**: Commands are executed through the shell for user convenience. Be mindful of security if accepting untrusted input (current design assumes trusted local config).
- **Theme applies globally**: Changing theme affects entire QApplication immediately, not just MainWindow.
- **MDI layout persistence**: Window positions/states are saved as JSON string in config.

## Common Patterns

### Adding a new menu action
1. Create QAction in `MainWindow._build_menubar()`
2. Connect to handler method (e.g., `action.triggered.connect(self._my_handler)`)
3. Implement handler as `MainWindow._my_handler(self)`
4. Call `self._save()` if state changes

### Modifying a ProgramItem
1. Get item reference from QListWidgetItem's UserRole data
2. Edit item fields directly (items are mutable dataclass instances)
3. Call `GroupWindow.refresh_items()` to update UI
4. Changes auto-save when MainWindow saves

### Changing theme behavior
1. Modify `ThemeManager.CLASSIC_STYLESHEET` for stylesheet changes
2. Modify `ThemeManager.apply()` palette setup for color changes
3. Theme applies immediately via `QApplication.instance()` reference

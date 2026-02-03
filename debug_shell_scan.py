#!/usr/bin/env python3
"""Diagnostic script to test Windows shell:AppsFolder enumeration."""

import sys
import traceback


def test_pywin32_import():
    """Test if pywin32 is installed and importable."""
    print("=" * 60)
    print("Step 1: Testing pywin32 import")
    print("=" * 60)
    try:
        from win32com.shell import shell, shellcon
        print("✓ Successfully imported win32com.shell")
        print(f"  shell module: {shell}")
        print(f"  shellcon module: {shellcon}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import win32com.shell: {e}")
        print("\nTo install pywin32, run:")
        print("  pip install pywin32")
        return False


def test_shell_folder_access():
    """Test accessing the desktop shell folder."""
    print("\n" + "=" * 60)
    print("Step 2: Testing shell folder access")
    print("=" * 60)
    try:
        from win32com.shell import shell
        desktop = shell.SHGetDesktopFolder()
        print(f"✓ Got desktop folder: {desktop}")
        return desktop
    except Exception as e:
        print(f"✗ Failed to get desktop folder: {e}")
        traceback.print_exc()
        return None


def test_apps_folder_parse(desktop):
    """Test parsing the shell:AppsFolder path."""
    print("\n" + "=" * 60)
    print("Step 3: Testing shell:AppsFolder parsing")
    print("=" * 60)
    try:
        pidl, flags = desktop.ParseDisplayName(0, None, "shell:AppsFolder")
        print(f"✓ Parsed shell:AppsFolder")
        print(f"  PIDL: {pidl}")
        print(f"  Flags: {flags}")
        return pidl
    except Exception as e:
        print(f"✗ Failed to parse shell:AppsFolder: {e}")
        traceback.print_exc()
        return None


def test_bind_to_apps_folder(desktop, pidl):
    """Test binding to the AppsFolder."""
    print("\n" + "=" * 60)
    print("Step 4: Testing bind to AppsFolder")
    print("=" * 60)
    try:
        from win32com.shell import shell
        apps_folder = desktop.BindToObject(pidl, None, shell.IID_IShellFolder)
        print(f"✓ Bound to AppsFolder: {apps_folder}")
        return apps_folder
    except Exception as e:
        print(f"✗ Failed to bind to AppsFolder: {e}")
        traceback.print_exc()
        return None


def test_enumerate_apps(apps_folder):
    """Test enumerating applications."""
    print("\n" + "=" * 60)
    print("Step 5: Testing app enumeration")
    print("=" * 60)
    try:
        from win32com.shell import shellcon

        # Try with SHCONTF_NONFOLDERS
        print("Trying EnumObjects with SHCONTF_NONFOLDERS...")
        enum = apps_folder.EnumObjects(0, shellcon.SHCONTF_NONFOLDERS)
        print(f"✓ Got enumerator: {enum}")

        apps = []
        count = 0
        while True:
            try:
                pidls = enum.Next(1)
                if not pidls:
                    break

                item_pidl = pidls[0]
                count += 1

                try:
                    # Get display name
                    name = apps_folder.GetDisplayNameOf(item_pidl, shellcon.SHGDN_NORMAL)
                    # Get parsing name (AUMID or path)
                    aumid = apps_folder.GetDisplayNameOf(item_pidl, shellcon.SHGDN_FORPARSING)

                    apps.append((name, aumid))

                    if count <= 10:
                        print(f"  [{count}] {name}")
                        print(f"       AUMID: {aumid}")
                except Exception as e:
                    print(f"  [{count}] Error getting name: {e}")

            except Exception as e:
                print(f"Error during enumeration: {e}")
                break

        print(f"\n✓ Found {len(apps)} applications")

        # Show some UWP apps specifically
        uwp_apps = [(n, a) for n, a in apps if "!" in a]
        print(f"\nUWP apps (with '!' in AUMID): {len(uwp_apps)}")
        for name, aumid in uwp_apps[:5]:
            print(f"  - {name}: {aumid}")

        return apps

    except Exception as e:
        print(f"✗ Failed to enumerate: {e}")
        traceback.print_exc()
        return None


def test_current_scanner():
    """Test what the current scanner returns."""
    print("\n" + "=" * 60)
    print("Step 6: Testing current scanner implementation")
    print("=" * 60)
    try:
        from progman.utils.scanner import _scan_windows, _scan_windows_shell, _scan_windows_lnk

        print("Testing _scan_windows_shell()...")
        try:
            shell_apps = _scan_windows_shell()
            print(f"✓ _scan_windows_shell returned {len(shell_apps)} apps")
            uwp_apps = [a for a in shell_apps if "!" in a.command]
            print(f"  UWP apps: {len(uwp_apps)}")
            for app in uwp_apps[:5]:
                print(f"    - {app.name}: {app.command}")
        except Exception as e:
            print(f"✗ _scan_windows_shell failed: {e}")
            traceback.print_exc()

        print("\nTesting _scan_windows_lnk()...")
        try:
            lnk_apps = _scan_windows_lnk()
            print(f"✓ _scan_windows_lnk returned {len(lnk_apps)} apps")
        except Exception as e:
            print(f"✗ _scan_windows_lnk failed: {e}")
            traceback.print_exc()

        print("\nTesting _scan_windows() (combined)...")
        try:
            all_apps = _scan_windows()
            print(f"✓ _scan_windows returned {len(all_apps)} apps")
            uwp_apps = [a for a in all_apps if "!" in a.command]
            print(f"  UWP apps: {len(uwp_apps)}")
        except Exception as e:
            print(f"✗ _scan_windows failed: {e}")
            traceback.print_exc()

    except ImportError as e:
        print(f"✗ Could not import scanner module: {e}")


def main():
    print("Windows Shell AppsFolder Diagnostic")
    print("====================================\n")

    import platform
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")

    if platform.system() != "Windows":
        print("\n⚠ This script should be run on Windows!")
        return

    # Step 1: Test pywin32 import
    if not test_pywin32_import():
        return

    # Step 2: Get desktop folder
    desktop = test_shell_folder_access()
    if not desktop:
        return

    # Step 3: Parse shell:AppsFolder
    pidl = test_apps_folder_parse(desktop)
    if not pidl:
        return

    # Step 4: Bind to AppsFolder
    apps_folder = test_bind_to_apps_folder(desktop, pidl)
    if not apps_folder:
        return

    # Step 5: Enumerate apps
    apps = test_enumerate_apps(apps_folder)

    # Step 6: Test current scanner
    test_current_scanner()

    print("\n" + "=" * 60)
    print("Diagnostic complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

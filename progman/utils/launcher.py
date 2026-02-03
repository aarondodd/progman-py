"""Cross-platform process launcher for Program Manager."""

import os
import platform
import subprocess

from PyQt6.QtWidgets import QMessageBox

from ..models.program_item import ProgramItem


def _is_aumid(command: str) -> bool:
    """Check if command looks like a UWP Application User Model ID (AUMID).

    AUMIDs have the format: PackageFamilyName!ApplicationId
    Example: Microsoft.WindowsTerminal_8wekyb3d8bbwe!App
    """
    if "!" not in command:
        return False
    # If the part before '!' is an existing file path, it's not an AUMID
    prefix = command.split("!")[0]
    return not os.path.exists(prefix)


class Launcher:
    """Cross-platform process launcher."""

    @staticmethod
    def launch(item: ProgramItem) -> None:
        if not item.command:
            return

        cwd = item.working_dir or None

        try:
            # Check if this is a UWP app (AUMID format on Windows)
            if platform.system() == "Windows" and _is_aumid(item.command):
                # Launch UWP apps via explorer shell protocol
                subprocess.Popen(
                    ["explorer.exe", f"shell:AppsFolder\\{item.command}"],
                    shell=False,
                )
            else:
                # Traditional app launch
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

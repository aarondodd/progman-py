"""Tests for the Launcher class."""

from unittest.mock import patch, MagicMock

from progman.models.program_item import ProgramItem
from progman.utils.launcher import Launcher, _is_aumid


class TestLauncher:
    def test_launch_calls_popen(self, qapp):
        item = ProgramItem(title="Test", command="echo hello")
        with patch("progman.utils.launcher.subprocess.Popen") as mock_popen:
            Launcher.launch(item)
            mock_popen.assert_called_once_with(
                "echo hello", shell=True, cwd=None
            )

    def test_launch_with_working_dir(self, qapp):
        item = ProgramItem(
            title="Test", command="echo hello", working_dir="/tmp"
        )
        with patch("progman.utils.launcher.subprocess.Popen") as mock_popen:
            Launcher.launch(item)
            mock_popen.assert_called_once_with(
                "echo hello", shell=True, cwd="/tmp"
            )

    def test_launch_empty_command_does_nothing(self, qapp):
        item = ProgramItem(title="Empty", command="")
        with patch("progman.utils.launcher.subprocess.Popen") as mock_popen:
            Launcher.launch(item)
            mock_popen.assert_not_called()

    def test_launch_error_shows_messagebox(self, qapp):
        item = ProgramItem(title="Bad", command="nonexistent")
        with patch("progman.utils.launcher.subprocess.Popen", side_effect=OSError("fail")):
            with patch("progman.utils.launcher.QMessageBox.critical") as mock_msg:
                Launcher.launch(item)
                mock_msg.assert_called_once()
                args = mock_msg.call_args
                assert "Launch Error" in args[0][1]

    def test_launch_uwp_app_on_windows(self, qapp):
        """UWP apps on Windows should launch via explorer shell protocol."""
        item = ProgramItem(
            title="Windows Terminal",
            command="Microsoft.WindowsTerminal_8wekyb3d8bbwe!App"
        )
        with patch("progman.utils.launcher.platform.system", return_value="Windows"):
            with patch("progman.utils.launcher.subprocess.Popen") as mock_popen:
                Launcher.launch(item)
                mock_popen.assert_called_once_with(
                    ["explorer.exe", "shell:AppsFolder\\Microsoft.WindowsTerminal_8wekyb3d8bbwe!App"],
                    shell=False,
                )

    def test_launch_traditional_app_on_windows(self, qapp):
        """Traditional apps should launch directly even on Windows."""
        item = ProgramItem(title="Notepad", command="notepad.exe")
        with patch("progman.utils.launcher.platform.system", return_value="Windows"):
            with patch("progman.utils.launcher.subprocess.Popen") as mock_popen:
                Launcher.launch(item)
                mock_popen.assert_called_once_with(
                    "notepad.exe",
                    shell=True,
                    cwd=None,
                )

    def test_aumid_not_detected_on_linux(self, qapp):
        """On non-Windows platforms, AUMID-like commands should launch directly."""
        item = ProgramItem(
            title="Test",
            command="Microsoft.Something_abc!App"
        )
        with patch("progman.utils.launcher.platform.system", return_value="Linux"):
            with patch("progman.utils.launcher.subprocess.Popen") as mock_popen:
                Launcher.launch(item)
                # Should use shell=True (traditional launch), not explorer.exe
                mock_popen.assert_called_once_with(
                    "Microsoft.Something_abc!App",
                    shell=True,
                    cwd=None,
                )


class TestAumidDetection:
    def test_is_aumid_true(self):
        """Valid AUMIDs return True."""
        assert _is_aumid("Microsoft.WindowsTerminal_8wekyb3d8bbwe!App") is True
        assert _is_aumid("Company.App_hash!Id") is True

    def test_is_aumid_false_no_exclamation(self):
        """Commands without '!' are not AUMIDs."""
        assert _is_aumid("notepad.exe") is False
        assert _is_aumid(r"C:\Path\to\app.exe") is False

    def test_is_aumid_false_existing_path(self, tmp_path):
        """If prefix exists as a file path, it's not an AUMID."""
        test_file = tmp_path / "testfile"
        test_file.touch()
        assert _is_aumid(f"{test_file}!Something") is False

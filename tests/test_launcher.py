"""Tests for the Launcher class."""

from unittest.mock import patch, MagicMock

from progman.models.program_item import ProgramItem
from progman.utils.launcher import Launcher


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

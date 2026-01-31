"""Background worker for scanning installed programs."""

from PyQt6.QtCore import QThread, pyqtSignal

from ..utils.scanner import scan_applications


class ScanWorker(QThread):
    """Worker thread for scanning installed programs."""

    finished = pyqtSignal(list)  # List[DiscoveredApp]

    def run(self) -> None:
        apps = scan_applications()
        self.finished.emit(apps)

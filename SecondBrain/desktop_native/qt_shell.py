from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from typing import Any

from secondbrain.version import get_version


VIEWS = (
    "Dashboard", "Assistant", "Tasks", "Projects", "Documents", "Search", "Memory",
    "Knowledge Graph", "Calendar", "Mail", "Briefings", "Jobs", "Connectors", "Agents",
    "Approvals", "Backups", "Settings", "Diagnostics",
)


@dataclass(frozen=True, slots=True)
class ShellCapabilities:
    qt_available: bool
    tray_available: bool
    degraded_mode: bool
    reason: str = ""


def capabilities() -> ShellCapabilities:
    # Importing Qt widgets before QApplication exists can crash some Windows Qt
    # builds. Discovery therefore has no imports or GUI side effects.
    if find_spec("PySide6") is None:
        return ShellCapabilities(False, False, True, "PySide6 ist nicht installiert")
    return ShellCapabilities(True, False, False, "Tray wird nach QApplication-Start geprüft")


def create_window(action_callback: Any = None) -> Any:
    """Create the optional Qt shell without importing Qt during normal CLI startup."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel, QListWidget, QMainWindow, QStatusBar, QVBoxLayout, QWidget

    class JarvisWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle(f"Jarvis SecondBrain {get_version()}")
            self.resize(1280, 800)
            panel = QWidget(self)
            layout = QVBoxLayout(panel)
            layout.addWidget(QLabel("JARVIS · Native Desktop"))
            navigation = QListWidget()
            navigation.addItems(VIEWS)
            if action_callback:
                navigation.itemActivated.connect(lambda item: action_callback(item.text()))
            layout.addWidget(navigation)
            self.setCentralWidget(panel)
            status = QStatusBar(self)
            status.showMessage("Voice: IDLE · Provider: degraded-safe · Approvals: 0")
            self.setStatusBar(status)
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        def closeEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
            self.hide()
            event.ignore()

    return JarvisWindow()

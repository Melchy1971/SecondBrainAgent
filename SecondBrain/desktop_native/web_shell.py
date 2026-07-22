"""Nativer Desktop, der die Web-GUI pixelgleich anzeigt.

Statt die Web-Oberflaeche als Qt-Widgets nachzubauen, laedt ein natives Fenster
das bestehende Web-HUD ueber ``QWebEngineView``. Der Inhalt ist damit exakt die
Web-GUI -- dieselbe HTML/CSS --, nur in einem eigenstaendigen Fenster mit
nativem Rahmen.

Aufbau (bewusst wie in qt_shell.py):
* Keine Qt-Importe auf Modulebene. ``capabilities()`` prueft nur per find_spec
  und kann daher gefahrlos vor jeder QApplication laufen.
* Die Orchestrierung (Server sicherstellen, URL bilden, Fenster oeffnen) ist
  ueber injizierbare Callables testbar, ohne echtes Display.

Fallback: fehlt ``QtWebEngine``, meldet ``run_web_shell`` ``webengine_missing``,
damit der Aufrufer auf die klassische Shell zurueckfallen kann.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Callable

from secondbrain.version import get_version

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8851


@dataclass(frozen=True, slots=True)
class WebShellCapabilities:
    pyside6: bool
    webengine: bool
    reason: str = ""

    @property
    def usable(self) -> bool:
        return self.pyside6 and self.webengine


def capabilities() -> WebShellCapabilities:
    """Ohne Qt-Import: nur Verfuegbarkeit pruefen."""
    if find_spec("PySide6") is None:
        return WebShellCapabilities(False, False, "PySide6 ist nicht installiert")
    # QtWebEngine steckt im PySide6-Metapaket (Addons), ist aber separat ladbar.
    if find_spec("PySide6.QtWebEngineWidgets") is None:
        return WebShellCapabilities(True, False, "PySide6.QtWebEngineWidgets fehlt")
    return WebShellCapabilities(True, True, "")


def hud_url(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    return f"http://{host}:{port}"


def _default_ensure_server(project_root: Path, host: str, port: int) -> dict[str, Any]:
    """Startet das Web-HUD, ohne einen Browser zu oeffnen."""
    from secondbrain.gui.launch import start_web_hud
    return start_web_hud(project_root, open_browser=False, quiet=True, host=host, port=port)


def _default_open_window(url: str, *, title: str) -> int:  # pragma: no cover - benoetigt Display
    from PySide6.QtCore import QUrl
    from PySide6.QtWidgets import QApplication, QMainWindow
    from PySide6.QtWebEngineWidgets import QWebEngineView

    app = QApplication.instance() or QApplication([])

    window = QMainWindow()
    window.setWindowTitle(title)
    window.resize(1280, 800)
    view = QWebEngineView(window)
    view.setUrl(QUrl(url))
    window.setCentralWidget(view)
    window.show()
    return int(app.exec())


def run_web_shell(
    project_root: str | Path = ".",
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    ensure_server: Callable[[Path, str, int], dict[str, Any]] | None = None,
    open_window: Callable[..., int] | None = None,
    caps: WebShellCapabilities | None = None,
) -> dict[str, Any]:
    """Stellt das HUD sicher und oeffnet es in einem nativen WebEngine-Fenster.

    ``ensure_server`` und ``open_window`` sind injizierbar, damit die
    Orchestrierung ohne echten Server und ohne Display pruefbar ist.
    """
    root = Path(project_root).resolve()
    caps = caps or capabilities()
    url = hud_url(host, port)

    if not caps.usable:
        return {
            "ok": False,
            "status": "webengine_missing",
            "reason": caps.reason,
            "fallback": "native_widget_shell",
            "url": url,
        }

    ensure = ensure_server or _default_ensure_server
    server = ensure(root, host, port)
    if not server.get("ok"):
        return {"ok": False, "status": "server_unavailable", "server": server, "url": url}

    opener = open_window or _default_open_window
    title = f"Jarvis SecondBrain {get_version()}"
    exit_code = opener(url, title=title)
    return {
        "ok": True,
        "status": "closed",
        "url": url,
        "exit_code": int(exit_code),
        "server_action": server.get("action"),
    }

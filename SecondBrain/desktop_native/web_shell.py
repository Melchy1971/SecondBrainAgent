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

import re
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


# --------------------------------------------------------------------------
# Fenstergeometrie -- reine Helfer, teilen das Format mit WindowStateStore
# --------------------------------------------------------------------------

# Gleiches X11-Format wie SecondBrain/desktop_native/lifecycle.py: WxH+X+Y.
_GEOMETRY = re.compile(r"^(\d{3,5})x(\d{3,5})([+-]\d{1,6})([+-]\d{1,6})$")


def format_geometry(width: int, height: int, x: int, y: int) -> str:
    """Qt-Fensterrechteck -> WxH+X+Y (z. B. 1280x800+100+50)."""
    return f"{int(width)}x{int(height)}{int(x):+d}{int(y):+d}"


def parse_geometry(value: str) -> tuple[int, int, int, int] | None:
    """WxH+X+Y -> (width, height, x, y). ``None`` bei ungueltigem Format."""
    match = _GEOMETRY.fullmatch(str(value or ""))
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)))


# --------------------------------------------------------------------------
# System-Tray -- Menuestruktur als testbare Spezifikation
# --------------------------------------------------------------------------

TRAY_TOOLTIP = "Jarvis SecondBrain"


def tray_menu_spec() -> tuple[dict[str, str], ...]:
    """Menuepunkte des Tray-Icons. Der Qt-Bauer verdrahtet sie gegen Aktionen.

    Bewusst schlank gehalten: nur belegbare Aktionen. Voice-/Job-/Approval-
    Eintraege waeren ohne echte Anbindung Fiktion.
    """
    return (
        {"id": "show", "label": "Öffnen"},
        {"id": "hide", "label": "In den Tray"},
        {"id": "quit", "label": "Beenden"},
    )


def _default_ensure_server(project_root: Path, host: str, port: int) -> dict[str, Any]:
    """Startet das Web-HUD, ohne einen Browser zu oeffnen."""
    from secondbrain.gui.launch import start_web_hud
    return start_web_hud(project_root, open_browser=False, quiet=True, host=host, port=port)


def _default_open_window(url: str, *, title: str, project_root: Path | None = None) -> int:  # pragma: no cover - benoetigt Display
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QAction, QIcon
    from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon
    from PySide6.QtWebEngineWidgets import QWebEngineView

    from secondbrain.desktop_native.lifecycle import WindowStateStore

    root = Path(project_root or ".").resolve()
    store = WindowStateStore(root)

    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)  # Schliessen soll in den Tray, nicht beenden

    window = QMainWindow()
    window.setWindowTitle(title)

    # -- Geometrie wiederherstellen -----------------------------------------
    saved = parse_geometry(store.load().get("geometry", ""))
    if saved:
        w, h, x, y = saved
        window.setGeometry(x, y, w, h)
    else:
        window.resize(1280, 800)

    view = QWebEngineView(window)
    view.setUrl(QUrl(url))
    window.setCentralWidget(view)

    # -- System-Tray --------------------------------------------------------
    tray = QSystemTrayIcon(window)
    tray.setIcon(window.windowIcon() or QIcon())
    tray.setToolTip(TRAY_TOOLTIP)
    menu = QMenu()
    handlers = {
        "show": lambda: (window.showNormal(), window.raise_(), window.activateWindow()),
        "hide": window.hide,
        "quit": app.quit,
    }
    for item in tray_menu_spec():
        action = QAction(item["label"], menu)
        action.triggered.connect(handlers[item["id"]])
        menu.addAction(action)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: handlers["show"]() if reason == QSystemTrayIcon.ActivationReason.Trigger else None
    )
    tray.show()

    def _persist_geometry() -> None:
        rect = window.geometry()
        store.save(geometry=format_geometry(rect.width(), rect.height(), rect.x(), rect.y()),
                   view=store.load().get("view", "Dashboard"))

    def _close_to_tray(event: Any) -> None:
        _persist_geometry()
        window.hide()
        event.ignore()  # nicht beenden -- nur in den Tray

    window.closeEvent = _close_to_tray  # type: ignore[assignment]
    app.aboutToQuit.connect(_persist_geometry)

    window.show()
    return int(app.exec())


def _default_lock(project_root: Path):
    from secondbrain.desktop_native.lifecycle import SingleInstanceLock
    return SingleInstanceLock(project_root)


def run_web_shell(
    project_root: str | Path = ".",
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    ensure_server: Callable[[Path, str, int], dict[str, Any]] | None = None,
    open_window: Callable[..., int] | None = None,
    caps: WebShellCapabilities | None = None,
    lock_factory: Callable[[Path], Any] | None = None,
) -> dict[str, Any]:
    """Stellt das HUD sicher und oeffnet es in einem nativen WebEngine-Fenster.

    Single-Instance: ein zweiter Start meldet ``already_running`` statt ein
    zweites Fenster und einen zweiten HUD-Server zu erzeugen.

    ``ensure_server``, ``open_window`` und ``lock_factory`` sind injizierbar,
    damit die Orchestrierung ohne echten Server, ohne Display und ohne echte
    Instanzsperre pruefbar ist.
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

    from secondbrain.desktop_native.lifecycle import InstanceAlreadyRunning

    lock = (lock_factory or _default_lock)(root)
    try:
        lock.acquire()
    except InstanceAlreadyRunning as exc:
        # Zweiter Start: kein zweites Fenster, keine zweite Server-Instanz.
        return {"ok": True, "status": "already_running", "detail": str(exc), "url": url}

    try:
        ensure = ensure_server or _default_ensure_server
        server = ensure(root, host, port)
        if not server.get("ok"):
            return {"ok": False, "status": "server_unavailable", "server": server, "url": url}

        opener = open_window or _default_open_window
        title = f"Jarvis SecondBrain {get_version()}"
        exit_code = opener(url, title=title, project_root=root)
        return {
            "ok": True,
            "status": "closed",
            "url": url,
            "exit_code": int(exit_code),
            "server_action": server.get("action"),
        }
    finally:
        lock.release()

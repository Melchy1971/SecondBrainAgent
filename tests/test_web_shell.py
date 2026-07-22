"""Orchestrierung des nativen WebEngine-Desktops -- ohne Display.

Der eigentliche Fensteraufbau (QWebEngineView) laesst sich headless nicht
pruefen. Getestet wird die Logik davor und danach: Capability-Erkennung,
Server-Ensure, URL-Bildung, Fallback bei fehlendem QtWebEngine und die
Weitergabe des Exit-Codes. Der Fensteroeffner ist injizierbar.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# desktop_native/__init__.py zieht ueber .app das tkinter-Modul, das in reinen
# Headless-Umgebungen fehlt. web_shell selbst braucht es nicht -- daher direkt
# per Dateipfad laden, am Paket-__init__ vorbei. Registrierung in sys.modules,
# damit dataclass(slots=True) das Modul aufloesen kann.
_NAME = "_web_shell_under_test"
_PATH = Path(__file__).resolve().parents[1] / "SecondBrain" / "desktop_native" / "web_shell.py"
_spec = importlib.util.spec_from_file_location(_NAME, _PATH)
ws = importlib.util.module_from_spec(_spec)
sys.modules[_NAME] = ws
_spec.loader.exec_module(ws)


def test_hud_url_shape() -> None:
    assert ws.hud_url() == "http://127.0.0.1:8851"
    assert ws.hud_url("0.0.0.0", 9000) == "http://0.0.0.0:9000"


def test_capabilities_do_not_import_qt() -> None:
    # capabilities() darf nur find_spec nutzen, nie Qt importieren.
    import ast
    import inspect

    source = inspect.getsource(ws.capabilities)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        assert not isinstance(node, (ast.Import, ast.ImportFrom)), (
            "capabilities() darf keine Importe enthalten"
        )


def _caps(pyside: bool, webengine: bool) -> ws.WebShellCapabilities:
    return ws.WebShellCapabilities(pyside, webengine, "" if (pyside and webengine) else "missing")


# --------------------------------------------------------------------------
# Fallback wenn QtWebEngine fehlt
# --------------------------------------------------------------------------


def test_missing_webengine_reports_fallback() -> None:
    result = ws.run_web_shell(
        ".", caps=_caps(True, False),
        ensure_server=lambda *a: {"ok": True},
        open_window=lambda *a, **k: 0,
    )
    assert result["status"] == "webengine_missing"
    assert result["fallback"] == "native_widget_shell"
    assert result["ok"] is False


def test_missing_pyside_reports_fallback() -> None:
    result = ws.run_web_shell(".", caps=_caps(False, False),
                              ensure_server=lambda *a: {"ok": True},
                              open_window=lambda *a, **k: 0)
    assert result["status"] == "webengine_missing"


def test_window_is_not_opened_without_webengine() -> None:
    opened = []
    ws.run_web_shell(".", caps=_caps(True, False),
                     ensure_server=lambda *a: {"ok": True},
                     open_window=lambda *a, **k: opened.append(True) or 0)
    assert not opened, "Ohne QtWebEngine darf kein Fenster geoeffnet werden"


# --------------------------------------------------------------------------
# Server-Ensure vor Fensteraufbau
# --------------------------------------------------------------------------


def test_server_is_ensured_before_window() -> None:
    order = []

    def ensure(root, host, port):
        order.append("server")
        return {"ok": True, "action": "started"}

    def opener(url, *, title):
        order.append("window")
        return 0

    ws.run_web_shell(".", caps=_caps(True, True), ensure_server=ensure, open_window=opener)
    assert order == ["server", "window"], "Der HUD-Server muss vor dem Fenster laufen"


def test_window_not_opened_when_server_fails() -> None:
    opened = []
    result = ws.run_web_shell(
        ".", caps=_caps(True, True),
        ensure_server=lambda *a: {"ok": False, "error": "bootstrap blocked"},
        open_window=lambda *a, **k: opened.append(True) or 0,
    )
    assert result["status"] == "server_unavailable"
    assert not opened


def test_url_is_passed_to_window() -> None:
    seen = {}

    def opener(url, *, title):
        seen["url"] = url
        seen["title"] = title
        return 7

    result = ws.run_web_shell(
        ".", host="127.0.0.1", port=8851, caps=_caps(True, True),
        ensure_server=lambda *a: {"ok": True, "action": "already_running"},
        open_window=opener,
    )
    assert seen["url"] == "http://127.0.0.1:8851"
    assert "Jarvis SecondBrain" in seen["title"]
    assert result["exit_code"] == 7
    assert result["ok"] is True


def test_ensure_server_does_not_open_browser() -> None:
    """Der native Shell-Pfad darf keinen zusaetzlichen Browser aufmachen."""
    import ast
    import inspect

    source = inspect.getsource(ws._default_ensure_server)
    assert "open_browser=False" in source

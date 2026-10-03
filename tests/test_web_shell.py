"""Orchestrierung des nativen WebEngine-Desktops -- ohne Display.

Der eigentliche Fensteraufbau (QWebEngineView) laesst sich headless nicht
pruefen. Getestet wird die Logik davor und danach: Capability-Erkennung,
Server-Ensure, URL-Bildung, Fallback bei fehlendem QtWebEngine und die
Weitergabe des Exit-Codes. Der Fensteroeffner ist injizierbar.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

_DN = Path(__file__).resolve().parents[1] / "SecondBrain" / "desktop_native"


def _load_isolated(mod_name: str, file_name: str):
    """Laedt ein desktop_native-Modul ohne dessen Paket-__init__.

    ``desktop_native/__init__.py`` zieht ueber ``.app`` tkinter, das in reinen
    Headless-Umgebungen fehlt. lifecycle und web_shell brauchen es nicht -- sie
    werden direkt per Dateipfad geladen und in sys.modules registriert, damit
    lazy Imports untereinander sowie dataclass(slots=True) aufloesen.
    """
    spec = importlib.util.spec_from_file_location(mod_name, _DN / file_name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


# Stub-Elternpaket, damit die echten Modulpfade aufloesen, ohne das reale
# __init__ (tkinter) auszufuehren.
if "secondbrain.desktop_native" not in sys.modules:
    _pkg = types.ModuleType("secondbrain.desktop_native")
    _pkg.__path__ = [str(_DN)]
    sys.modules["secondbrain.desktop_native"] = _pkg

_load_isolated("secondbrain.desktop_native.lifecycle", "lifecycle.py")
ws = _load_isolated("secondbrain.desktop_native.web_shell", "web_shell.py")


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

    def opener(url, *, title, **_kw):
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

    def opener(url, *, title, **_kw):
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


# --------------------------------------------------------------------------
# Single-Instance
# --------------------------------------------------------------------------


class _FakeLock:
    def __init__(self, *, taken: bool = False) -> None:
        self.taken = taken
        self.released = 0

    def acquire(self) -> None:
        from secondbrain.desktop_native.lifecycle import InstanceAlreadyRunning
        if self.taken:
            raise InstanceAlreadyRunning("Jarvis Desktop laeuft bereits (PID 4321)")

    def release(self) -> None:
        self.released += 1


def test_second_instance_does_not_open_window() -> None:
    opened = []
    result = ws.run_web_shell(
        ".", caps=_caps(True, True),
        ensure_server=lambda *a: {"ok": True, "action": "started"},
        open_window=lambda *a, **k: opened.append(True) or 0,
        lock_factory=lambda root: _FakeLock(taken=True),
    )
    assert result["status"] == "already_running"
    assert not opened, "Zweite Instanz darf kein Fenster oeffnen"


def test_second_instance_does_not_start_server() -> None:
    started = []
    ws.run_web_shell(
        ".", caps=_caps(True, True),
        ensure_server=lambda *a: started.append(True) or {"ok": True},
        open_window=lambda *a, **k: 0,
        lock_factory=lambda root: _FakeLock(taken=True),
    )
    assert not started, "Zweite Instanz darf keinen zweiten HUD-Server starten"


def test_lock_is_released_after_window_closes() -> None:
    lock = _FakeLock(taken=False)
    ws.run_web_shell(
        ".", caps=_caps(True, True),
        ensure_server=lambda *a: {"ok": True, "action": "started"},
        open_window=lambda *a, **k: 0,
        lock_factory=lambda root: lock,
    )
    assert lock.released == 1, "Instanzsperre muss nach Fensterschluss freigegeben werden"


def test_lock_released_even_when_server_fails() -> None:
    lock = _FakeLock(taken=False)
    ws.run_web_shell(
        ".", caps=_caps(True, True),
        ensure_server=lambda *a: {"ok": False},
        open_window=lambda *a, **k: 0,
        lock_factory=lambda root: lock,
    )
    assert lock.released == 1


# --------------------------------------------------------------------------
# Fenstergeometrie
# --------------------------------------------------------------------------


def test_geometry_format() -> None:
    assert ws.format_geometry(1280, 800, 100, 50) == "1280x800+100+50"
    assert ws.format_geometry(1280, 800, -5, -20) == "1280x800-5-20"


def test_geometry_roundtrip() -> None:
    for w, h, x, y in [(1280, 800, 100, 50), (640, 480, 0, 0), (1920, 1080, -10, -20)]:
        assert ws.parse_geometry(ws.format_geometry(w, h, x, y)) == (w, h, x, y)


@pytest.mark.parametrize("bad", ["", "abc", "1280x800", "1280x800+100", "10x10+0+0", "not+a+geo"])
def test_parse_geometry_rejects_invalid(bad: str) -> None:
    assert ws.parse_geometry(bad) is None


def test_geometry_shares_format_with_window_state_store() -> None:
    """Der Helfer und der vorhandene WindowStateStore muessen dasselbe Format nutzen.

    Sonst speichert das Fenster eine Geometrie, die der Store beim naechsten
    Start als ungueltig verwirft -- die Groesse ginge still verloren.
    """
    import importlib

    lifecycle = importlib.import_module("secondbrain.desktop_native.lifecycle")
    geo = ws.format_geometry(1280, 800, 100, 50)
    assert lifecycle.WindowStateStore.valid_geometry(geo)
    assert ws.parse_geometry(geo) is not None


def test_window_state_store_roundtrip(tmp_path) -> None:
    import importlib

    lifecycle = importlib.import_module("secondbrain.desktop_native.lifecycle")
    store = lifecycle.WindowStateStore(tmp_path)
    store.save(geometry="1280x800+100+50", view="Dashboard")
    loaded = store.load()
    assert loaded["geometry"] == "1280x800+100+50"
    assert ws.parse_geometry(loaded["geometry"]) == (1280, 800, 100, 50)


# --------------------------------------------------------------------------
# System-Tray
# --------------------------------------------------------------------------


def test_tray_menu_has_show_hide_quit() -> None:
    ids = [item["id"] for item in ws.tray_menu_spec()]
    assert ids == ["show", "hide", "quit"]
    for item in ws.tray_menu_spec():
        assert item["label"], "jeder Tray-Eintrag braucht ein Label"


def test_tray_spec_only_lists_backed_actions() -> None:
    """Keine Fiktion: nur Aktionen, die der Fensterbauer wirklich verdrahtet."""
    ids = {item["id"] for item in ws.tray_menu_spec()}
    assert ids == {"show", "hide", "quit"}


def test_ensure_server_does_not_open_browser() -> None:
    """Der native Shell-Pfad darf keinen zusaetzlichen Browser aufmachen."""
    import ast
    import inspect

    source = inspect.getsource(ws._default_ensure_server)
    assert "open_browser=False" in source

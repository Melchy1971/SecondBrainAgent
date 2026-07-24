from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from secondbrain.desktop_native.app import NAV_ITEMS
from secondbrain.jarvis_hud_server import native_view_payload


ROOT = Path(__file__).resolve().parents[1]


class _NavLabels(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_nav_item = False
        self.current: list[str] = []
        self.labels: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = dict(attrs).get("class", "").split()
        if tag == "a" and "nav-item" in classes:
            self.in_nav_item = True
            self.current = []

    def handle_data(self, data: str) -> None:
        if self.in_nav_item:
            self.current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_nav_item:
            label = "".join(self.current).replace("NEW", "").strip()
            self.labels.append(label)
            self.in_nav_item = False


def test_web_gui_contains_every_native_menu_item() -> None:
    parser = _NavLabels()
    parser.feed((ROOT / "web" / "jarvis_hud" / "index.html").read_text(encoding="utf-8"))

    assert set(NAV_ITEMS).issubset(parser.labels)


def test_web_gui_wires_every_added_native_module() -> None:
    html = (ROOT / "web" / "jarvis_hud" / "index.html").read_text(encoding="utf-8")
    for view in ("tasks", "projects", "calendar", "mail", "briefings", "backups", "diagnostics", "production"):
        assert f'id="nav-{view}"' in html
        assert f'"{view}"' in html
    assert "/api/native-view?view=" in html


def test_native_view_endpoint_rejects_unknown_modules(tmp_path: Path) -> None:
    assert native_view_payload("unknown", tmp_path) == {
        "ok": False,
        "module": "unknown",
        "status": "unknown_view",
    }


def test_briefing_endpoint_reads_real_artifact_names_without_paths(tmp_path: Path) -> None:
    folder = tmp_path / "SecondBrain" / "10_DailyBriefings"
    folder.mkdir(parents=True)
    (folder / "2026-07-23_daily.md").write_text("# Daily", encoding="utf-8")

    payload = native_view_payload("briefings", tmp_path)

    assert payload["ok"] is True
    assert payload["items"] == ["2026-07-23_daily.md"]

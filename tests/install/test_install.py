"""Tests for the Windows install helpers (Task 5)."""

from __future__ import annotations

from pathlib import Path

from secondbrain.install.app_home import DATA_SUBDIRS, ensure_layout, resolve_home
from secondbrain.install.migrate import MARKER, migrate_local_data
from secondbrain.install.smoke import run_smoke_test


# --- home resolution -----------------------------------------------------------

def test_jarvis_home_env_wins(tmp_path):
    home = resolve_home({"JARVIS_HOME": str(tmp_path / "h"), "APPDATA": str(tmp_path / "appdata")})
    assert home == tmp_path / "h"


def test_appdata_fallback():
    home = resolve_home({"APPDATA": r"C:\\Users\\Markus\\AppData\\Roaming"})
    assert home.name == "Jarvis"
    assert "Roaming" in str(home)


def test_home_fallback_when_no_appdata(tmp_path):
    home = resolve_home({"HOME": str(tmp_path)})
    assert home == tmp_path / ".jarvis"


def test_ensure_layout_creates_subdirs(tmp_path):
    home = ensure_layout(tmp_path / "jh")
    for sub in DATA_SUBDIRS:
        assert (home / sub).is_dir()


# --- migration -----------------------------------------------------------------

def _seed_source(root: Path) -> Path:
    (root / "config").mkdir(parents=True)
    (root / "config" / "settings.json").write_text('{"a":1}', encoding="utf-8")
    (root / "data").mkdir()
    (root / "data" / "db.sqlite3").write_text("olddata", encoding="utf-8")
    (root / "SecondBrain").mkdir()
    (root / "SecondBrain" / "note.md").write_text("note", encoding="utf-8")
    return root


def test_migration_copies_known_dirs(tmp_path):
    source = _seed_source(tmp_path / "src")
    home = tmp_path / "home"
    report = migrate_local_data(source, home, version="30.77.0")
    assert set(report["migrated"]) >= {"config", "data", "SecondBrain"}
    assert (home / "config" / "settings.json").read_text(encoding="utf-8") == '{"a":1}'
    assert (home / MARKER).exists()


def test_migration_is_idempotent_and_preserves_user_data(tmp_path):
    source = _seed_source(tmp_path / "src")
    home = tmp_path / "home"
    migrate_local_data(source, home, version="1")
    # user changes data after first install
    (home / "data" / "db.sqlite3").write_text("USERCHANGED", encoding="utf-8")
    # update re-runs migration from the (old) source
    report = migrate_local_data(source, home, version="2")
    assert "data" in report["skipped"]
    assert (home / "data" / "db.sqlite3").read_text(encoding="utf-8") == "USERCHANGED"
    history = __import__("json").loads((home / MARKER).read_text(encoding="utf-8"))["history"]
    assert len(history) == 2


def test_migration_overwrite_flag(tmp_path):
    source = _seed_source(tmp_path / "src")
    home = tmp_path / "home"
    migrate_local_data(source, home)
    (home / "config" / "settings.json").write_text("changed", encoding="utf-8")
    migrate_local_data(source, home, overwrite=True)
    assert (home / "config" / "settings.json").read_text(encoding="utf-8") == '{"a":1}'


# --- smoke test ----------------------------------------------------------------

def test_smoke_test_passes_on_prepared_home(tmp_path):
    home = ensure_layout(tmp_path / "home")
    report = run_smoke_test(home)
    assert report["ok"] is True
    assert report["status"] == "pass"
    assert all(c["ok"] for c in report["checks"])


def test_smoke_test_fails_without_layout(tmp_path):
    report = run_smoke_test(tmp_path / "empty_home")
    assert report["ok"] is False
    assert any(c["name"].startswith("subdir:") and not c["ok"] for c in report["checks"])

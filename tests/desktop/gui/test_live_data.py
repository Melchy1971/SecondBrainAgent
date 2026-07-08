"""Tests fuer die Live-Daten-Bindung der Desktop-GUI."""
import pytest

from secondbrain.desktop.gui.data_providers import LiveDataService
from secondbrain.desktop.gui.module_registry import ModuleRegistry
from secondbrain.desktop.gui.startup_checks import StartupChecks
from secondbrain.desktop.gui.gui_app import GuiApp


@pytest.fixture
def project(tmp_path):
    agent = tmp_path / "SecondBrain-Agent"
    (agent / "config").mkdir(parents=True)
    (agent / "runtime").mkdir(parents=True)
    (agent / "data" / "desktop_app").mkdir(parents=True)
    (agent / "data" / "desktop_app" / "settings.json").write_text(
        '{"theme":"dark","accent":"blue"}', encoding="utf-8")
    (agent / "config" / "connectors.yaml").write_text(
        "imap:\n  enabled: false\nollama:\n  enabled: true\n", encoding="utf-8")
    (agent / "config" / "connectors_v104.json").write_text(
        '{"connectors":[{"name":"gmail","kind":"local_json","enabled":true}]}',
        encoding="utf-8")
    (agent / "runtime" / "jobs.jsonl").write_text(
        '{"id":"j1","ok":true}\n', encoding="utf-8")
    vault = tmp_path / "SecondBrain"
    (vault / "01_Projekte").mkdir(parents=True)
    (vault / "01_Projekte" / "note.md").write_text(
        "# Telekom Prozess\nSAP Jira Abnahme Live-Lauf", encoding="utf-8")
    (vault / "02_Wissen").mkdir(parents=True)
    (vault / "02_Wissen" / "wiki.md").write_text("# Wissen\nmyWiki", encoding="utf-8")
    (tmp_path / "SecondBrain-Inbox").mkdir()
    (tmp_path / "SecondBrain-Inbox" / "drop.txt").write_text("x", encoding="utf-8")
    return agent


def test_dashboard_live_counts(project):
    vm = LiveDataService(project).dashboard()
    assert vm["vault_exists"] is True
    assert vm["markdown_files"] == 2
    assert vm["connectors_total"] >= 3
    assert vm["connectors_enabled"] >= 2
    assert vm["status"] == "ready"


def test_documents_live(project):
    vm = LiveDataService(project).documents()
    assert vm["total"] == 2
    assert vm["folders"] == 2
    assert all("name" in i and "modified" in i for i in vm["items"])


def test_search_live_hit_and_miss(project):
    svc = LiveDataService(project)
    hit = svc.search("telekom")
    assert hit["result_count"] >= 1
    assert hit["hits"][0]["note"].endswith("note.md")
    miss = svc.search("zzzznotpresent")
    assert miss["result_count"] == 0


def test_connectors_settings_jobs_status_notifications(project):
    svc = LiveDataService(project)
    assert svc.connectors()["enabled"] >= 2
    assert svc.settings()["desktop"]["theme"] == "dark"
    assert svc.jobs()["total"] >= 1
    assert svc.status()["overall"] in {"GREEN", "YELLOW", "RED"}
    assert svc.notifications()["count"] >= 1


def test_module_registry_live(project):
    reg = ModuleRegistry.live(project)
    assert reg.has("desktop_foundation")
    assert len(reg.list_modules()) == 9
    assert all(m.factory is not None for m in reg.list_modules())


def test_startup_checks_live_pass(project):
    checks = StartupChecks.live(project)
    results = checks.run()
    assert all(r.status == "PASS" for r in results)
    assert checks.is_blocked(results) is False


def test_startup_checks_live_blocks_without_vault(tmp_path):
    agent = tmp_path / "SecondBrain-Agent"
    (agent / "config").mkdir(parents=True)
    results = StartupChecks.live(agent).run()
    assert StartupChecks.live(agent).is_blocked(results) is True


def test_gui_app_create_live(project):
    app = GuiApp.create_live(project)
    assert app.start().status == "READY"
    assert app.navigate("dashboard").route == "/dashboard"
    view = app.render_active_live()
    assert view["module"] == "dashboard"
    assert view["markdown_files"] == 2


def test_render_module_live_unknown(project):
    app = GuiApp.create_live(project)
    app.start()
    assert app.render_module_live("does-not-exist")["error"] == "unknown module"


def test_render_module_live_guards_failure(project):
    app = GuiApp.create_live(project)
    app.start()
    boom = app.registry.get("dashboard")
    object.__setattr__(boom, "factory", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    result = app.render_module_live("dashboard")
    assert result["error"] == "render failed"
    assert "dashboard" in app.error_boundary.disabled_modules


def test_default_contract_unchanged():
    assert len(ModuleRegistry.defaults().list_modules()) == 8
    results = StartupChecks().run()
    assert all(r.status == "PASS" for r in results)

from secondbrain.desktop.app import DesktopApp
from secondbrain.gui.p1_control_panel import P1ControlPanel
from secondbrain.gui.production_dashboard import ProductionDashboard
from secondbrain.gui.rag_explorer import RagExplorer
from secondbrain.gui.settings_center import SettingsCenter


def test_p1_control_panel_exposes_new_runtime_actions():
    panel = P1ControlPanel()
    rendered = panel.render()
    commands = {action["command"] for actions in rendered["groups"].values() for action in actions}

    assert rendered["schema"] == "secondbrain.gui.p1_control_panel.v1"
    assert "p1-rag-ingest-dir" in commands
    assert "p1-rag-migrate-postgres" in commands
    assert "p1-provider-health" in commands
    assert "p1-embedding-config" in commands
    assert "p1-vector-index-repair" in commands
    assert "p1-golden-eval" in commands
    assert "p1-production" in commands
    assert "p1.embedding.repair" in rendered["confirmation_required"]


def test_settings_center_renders_embedding_and_store_settings():
    settings = SettingsCenter()
    settings.set("SECONDBRAIN_EMBEDDING_PROVIDER", "ollama")
    rendered = settings.render_embedding_settings()

    fields = {field["key"]: field for field in rendered["fields"]}
    assert fields["SECONDBRAIN_EMBEDDING_PROVIDER"]["value"] == "ollama"
    assert fields["DATABASE_URL"]["secret"] is True
    assert "p1-embedding-config" in rendered["commands"]
    assert "p3-pgvector-readiness" in rendered["commands"]


def test_rag_explorer_surfaces_parser_and_vector_states():
    explorer = RagExplorer()
    import_view = explorer.render_import_center({"parse_status": "OCR_REQUIRED"})
    index_view = explorer.render_index_center({"status": "blocked", "blockers": ["missing_vectors"]})

    assert import_view["status"] == "blocked"
    assert "p1-rag-ingest-dir" in import_view["commands"]
    assert index_view["blockers"] == ["missing_vectors"]
    assert "p1-vector-index-repair" in index_view["commands"]


def test_production_dashboard_p1_sections():
    dashboard = ProductionDashboard()
    rendered = dashboard.render_p1(provider_health={"ok": False, "status": "blocked"})

    assert rendered["status"] == "blocked"
    assert "provider_health" in rendered["blockers"]
    assert "p1-production" in rendered["primary_commands"]


def test_desktop_app_registers_p1_gui_views_and_commands(tmp_path):
    app = DesktopApp(tmp_path / "state.json")

    assert app.shell.open_view("p1-control")["schema"] == "secondbrain.gui.p1_control_panel.v1"
    assert app.shell.open_view("rag-import")["schema"] == "secondbrain.gui.rag_import_center.v1"
    assert app.shell.open_view("rag-index")["schema"] == "secondbrain.gui.rag_index_center.v1"
    assert app.shell.open_view("production")["schema"] == "secondbrain.gui.production_dashboard.p1.v1"
    assert app.shell.open_view("settings-p1")["schema"] == "secondbrain.gui.settings.embedding.v1"
    assert app.commands.execute("action.p1.embedding.config")["command"] == "p1-embedding-config"

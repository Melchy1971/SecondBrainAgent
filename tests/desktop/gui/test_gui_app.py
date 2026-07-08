from secondbrain.desktop.gui.gui_app import GuiApp

def test_gui_app_start_navigate_shutdown_flow():
    app = GuiApp.create()
    assert app.start().status == "READY"
    assert app.navigate("connectors").route == "/connectors"
    shell = app.render_shell()
    assert shell.active_module == "connectors"
    result = app.shutdown()
    assert result.status == "STOPPED"
    assert result.saved_state["active_module"] == "connectors"

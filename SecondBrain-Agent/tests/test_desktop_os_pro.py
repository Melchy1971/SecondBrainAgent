from secondbrain.desktop_pro import DesktopOSPro


def test_status(tmp_path):
    d = DesktopOSPro(tmp_path)
    assert d.status()["gui_backend"] == "pyside6_ready"


def test_command_palette(tmp_path):
    d = DesktopOSPro(tmp_path)
    found = d.commands.search("dashboard")
    assert found
    assert d.commands.execute(found[0]["id"])["ok"] is True


def test_knowledge_and_memory(tmp_path):
    d = DesktopOSPro(tmp_path)
    d.knowledge.ingest_node("Jarvis Architecture", tags=["jarvis"])
    d.memory.add_memory("Markus uses SecondBrain", "profile")
    assert d.knowledge.search("jarvis")
    assert d.memory.search("secondbrain")


def test_kanban_and_projects(tmp_path):
    d = DesktopOSPro(tmp_path)
    card = d.kanban.add_card("Build GUI")
    moved = d.kanban.move(card["id"], "doing")
    assert moved["column"] == "doing"
    d.projects.add_project("Desktop OS Pro", risk="high")
    assert d.projects.summary()["high_risk"] == 1


def test_layout_visibility(tmp_path):
    d = DesktopOSPro(tmp_path)
    changed = d.layout.set_window_visible("kanban", True)
    assert changed["visible"] is True

from secondbrain.desktop_app import DesktopAppRuntime


def test_status(tmp_path):
    assert DesktopAppRuntime(tmp_path).status()["version"] == "16.0"


def test_seed(tmp_path):
    rt = DesktopAppRuntime(tmp_path)
    status = rt.seed()
    assert status["tasks"] == 1
    assert status["notifications"] == 1


def test_chat(tmp_path):
    rt = DesktopAppRuntime(tmp_path)
    rt.chat("Hallo")
    assert len(rt.messages()) == 2


def test_knowledge(tmp_path):
    rt = DesktopAppRuntime(tmp_path)
    rt.add_knowledge("Jarvis", "System", ["ai"])
    assert rt.search_knowledge("ai")


def test_task_notify_settings(tmp_path):
    rt = DesktopAppRuntime(tmp_path)
    rt.add_task("Test", priority="high")
    rt.notify("A", "B")
    rt.set_setting("theme", "light")
    assert rt.settings()["theme"] == "light"
    assert rt.tasks()
    assert rt.notifications()

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


def test_complete_task_resolves_id_and_is_idempotent(tmp_path):
    rt = DesktopAppRuntime(tmp_path)
    created = rt.add_task("Review")

    completed = rt.complete_task(created["id"])
    repeated = rt.complete_task(created["id"])

    assert completed["column"] == "done"
    assert completed["completed_at"]
    assert repeated["completed_at"] == completed["completed_at"]


def test_complete_task_accepts_unique_title_and_rejects_ambiguity(tmp_path):
    rt = DesktopAppRuntime(tmp_path)
    rt.add_task("Review")
    assert rt.complete_task("  review  ")["column"] == "done"

    rt.add_task("Doppelt")
    rt.add_task("DOPPELT")
    try:
        rt.complete_task("doppelt")
    except ValueError as exc:
        assert str(exc) == "task reference is ambiguous"
    else:
        raise AssertionError("ambiguous task title was accepted")
    assert [task["column"] for task in rt.tasks() if task["title"].casefold() == "doppelt"] == [
        "backlog", "backlog",
    ]


def test_complete_task_rejects_missing_reference_without_write(tmp_path):
    rt = DesktopAppRuntime(tmp_path)
    rt.add_task("Review")
    before = rt.tasks()

    try:
        rt.complete_task("Unbekannt")
    except LookupError as exc:
        assert str(exc) == "task not found"
    else:
        raise AssertionError("missing task reference was accepted")
    assert rt.tasks() == before

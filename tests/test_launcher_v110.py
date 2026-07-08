from secondbrain.launcher_runtime_v108 import SecondBrainLauncher


def test_launcher_autonomous_status_and_run(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "config").mkdir()
    (project / "config" / "runtime.yaml").write_text("runtime:\n  services:\n    autonomous_agent: true\n", encoding="utf-8")
    launcher = SecondBrainLauncher(project)

    status = launcher.autonomous_status()
    result = launcher.autonomous_run("Analysiere den aktuellen Stand", max_steps=3)

    assert status["runs"] == 0
    assert result["status"] == "completed"
    assert any(step["action"] == "ai.ask" for step in result["steps"])

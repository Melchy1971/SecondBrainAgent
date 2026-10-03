from __future__ import annotations

import importlib.util
from pathlib import Path


LAUNCHER_PATH = Path(__file__).resolve().parents[1] / "launcher.py"
SPEC = importlib.util.spec_from_file_location("secondbrain_agent_launcher", LAUNCHER_PATH)
assert SPEC is not None and SPEC.loader is not None
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


def test_hud_delegates_to_workspace_launcher(monkeypatch):
    calls: list[tuple[list[str], object]] = []

    def fake_run(command, *, cwd, check):
        calls.append((command, cwd))
        return type("Result", (), {"returncode": 0})()

    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    assert launcher.main(["hud"]) == 0
    workspace_launcher = launcher.Path(launcher.__file__).resolve().parents[1] / "launcher.py"
    assert calls == [
        ([launcher.sys.executable, str(workspace_launcher), "hud"], workspace_launcher.parent)
    ]

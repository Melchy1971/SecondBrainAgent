from pathlib import Path
import json

from secondbrain.launcher_runtime_v108 import SecondBrainLauncher, load_runtime_yaml


def test_runtime_yaml_loader_reads_nested_config(tmp_path):
    path = tmp_path / "runtime.yaml"
    path.write_text("""
runtime:
  profile: safe
  services:
    connectors: true
    gui: false
  paths:
    runtime: runtime
""", encoding="utf-8")
    data = load_runtime_yaml(path)
    assert data["runtime"]["profile"] == "safe"
    assert data["runtime"]["services"]["connectors"] is True
    assert data["runtime"]["services"]["gui"] is False


def test_launcher_init_and_health(tmp_path):
    root = tmp_path / "SecondBrain-Agent"
    (root / "config").mkdir(parents=True)
    (root / "config" / "runtime.yaml").write_text("""
runtime:
  profile: test
  paths:
    vault: vault
    runtime: runtime
    events: events/runtime
  services:
    connectors: true
    ai_runtime: true
    agent_kernel: true
    desktop_commands: true
    security: true
""", encoding="utf-8")
    (root / "config" / "ai_runtime_v105.yaml").write_text("""
ai_runtime:
  default_provider: echo
  ollama_enabled: false
""", encoding="utf-8")
    (root / "config" / "connectors_v104.json").write_text(json.dumps({"connectors": []}), encoding="utf-8")

    launcher = SecondBrainLauncher(root)
    boot = launcher.init_runtime()
    health = launcher.health()

    assert Path(boot["runtime_dir"]).exists()
    assert health["profile"] == "test"
    assert any(s["name"] == "ai_runtime" and s["status"] == "ok" for s in health["services"])


def test_launcher_capture_notify_and_ask(tmp_path):
    root = tmp_path / "SecondBrain-Agent"
    (root / "config").mkdir(parents=True)
    (root / "config" / "runtime.yaml").write_text("""
runtime:
  paths:
    vault: vault
    runtime: runtime
    events: events/runtime
""", encoding="utf-8")
    (root / "config" / "ai_runtime_v105.yaml").write_text("""
ai_runtime:
  default_provider: echo
  ollama_enabled: false
""", encoding="utf-8")
    (root / "config" / "connectors_v104.json").write_text(json.dumps({"connectors": []}), encoding="utf-8")

    launcher = SecondBrainLauncher(root)
    capture = launcher.quick_capture("Merken", "Test Capture")
    note = launcher.notify("Hallo", "info")
    answer = launcher.ask("Status?", task="health")

    assert capture.exists()
    assert note.exists()
    assert answer.startswith("[echo:health]")


def test_launcher_job_submit_and_tick(tmp_path):
    root = tmp_path / "SecondBrain-Agent"
    (root / "config").mkdir(parents=True)
    (root / "config" / "runtime.yaml").write_text("""
runtime:
  paths:
    vault: vault
    runtime: runtime
    events: events/runtime
""", encoding="utf-8")
    (root / "config" / "ai_runtime_v105.yaml").write_text("""
ai_runtime:
  default_provider: echo
  ollama_enabled: false
""", encoding="utf-8")
    (root / "config" / "connectors_v104.json").write_text(json.dumps({"connectors": []}), encoding="utf-8")

    launcher = SecondBrainLauncher(root)
    job = launcher.submit("desktop.notify", {"message": "Job läuft", "severity": "info"})
    result = launcher.tick()

    assert job.action == "desktop.notify"
    assert result["processed"] == 1

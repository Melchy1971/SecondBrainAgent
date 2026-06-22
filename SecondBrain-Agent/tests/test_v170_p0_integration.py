from __future__ import annotations

from secondbrain.module_registry import ModuleRegistry
from launcher import main


def test_registry_has_command_index_for_primary_p0_modules():
    registry = ModuleRegistry()
    index = registry.command_index()
    assert index["desktop-status"] == "desktop"
    assert index["graph-status"] == "graph"
    assert index["voice-status2"] == "voice"
    assert index["mobile16-status"] == "mobile"


def test_launcher_modules_command_returns_success(capsys):
    rc = main(["modules"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "command_index" in captured
    assert "desktop-status" in captured


def test_launcher_runtime_health_returns_success(tmp_path, capsys):
    rc = main(["--project-root", str(tmp_path), "health"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "runtime_health" in captured
    assert "desktop" in captured


def test_registry_resolves_known_command_to_module():
    registry = ModuleRegistry()
    assert registry.resolve_command("desktop-dashboard").key == "desktop"
    assert registry.resolve_command("voice-wake").key == "voice"


def test_launcher_command_index_command_returns_success(capsys):
    rc = main(["command-index"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "desktop-status" in captured
    assert "mobile16-status" in captured


def test_launcher_unknown_module_returns_clear_error(capsys):
    rc = main(["module-status", "does-not-exist"])
    captured = capsys.readouterr().out
    assert rc == 2
    assert "unknown module" in captured
    assert "desktop" in captured


def test_p0_doctor_publishes_event_and_reports_config(tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "settings.yaml").write_text("runtime_dir: runtime\n", encoding="utf-8")
    (config_dir / "runtime.yaml").write_text("runtime_dir: runtime\n", encoding="utf-8")
    (config_dir / "production.yaml").write_text("enabled: false\n", encoding="utf-8")
    (config_dir / "security.yaml").write_text("privacy_mode: false\n", encoding="utf-8")
    (config_dir / "connectors.yaml").write_text("connectors:\n", encoding="utf-8")
    rc = main(["--project-root", str(tmp_path), "p0-doctor"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "doctor_event_id" in captured
    assert "runtime.p0_doctor" in (tmp_path / "runtime" / "events_v121" / "events.jsonl").read_text(encoding="utf-8")


def test_p0_gate_blocks_missing_required_config(tmp_path, capsys):
    rc = main(["--project-root", str(tmp_path), "p0-gate"])
    captured = capsys.readouterr().out
    assert rc == 1
    assert '"status": "blocked"' in captured
    assert "required_config_files" in captured


def test_p0_gate_passes_with_required_config(tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "settings.yaml").write_text("runtime_dir: runtime\n", encoding="utf-8")
    (config_dir / "runtime.yaml").write_text("runtime_dir: runtime\n", encoding="utf-8")
    (config_dir / "production.yaml").write_text("enabled: false\n", encoding="utf-8")
    (config_dir / "security.yaml").write_text("privacy_mode: false\n", encoding="utf-8")
    (config_dir / "connectors.yaml").write_text("connectors: []\n", encoding="utf-8")
    rc = main(["--project-root", str(tmp_path), "p0-gate"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert '"status": "pass"' in captured
    assert "runtime_dir_writable" in captured


def _write_required_config(root):
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "settings.yaml").write_text("runtime_dir: runtime\n", encoding="utf-8")
    (config_dir / "runtime.yaml").write_text("runtime_dir: runtime\n", encoding="utf-8")
    (config_dir / "production.yaml").write_text("enabled: false\n", encoding="utf-8")
    (config_dir / "security.yaml").write_text("privacy_mode: false\n", encoding="utf-8")
    (config_dir / "connectors.yaml").write_text("connectors: []\n", encoding="utf-8")


def test_p0_report_persists_latest_gate_report(tmp_path, capsys):
    _write_required_config(tmp_path)
    rc = main(["--project-root", str(tmp_path), "p0-report"])
    captured = capsys.readouterr().out
    report = tmp_path / "runtime" / "reports" / "p0_gate_latest.json"
    assert rc == 0
    assert report.exists()
    assert "p0_gate_latest.json" in captured
    assert '"schema": "secondbrain.p0_gate.v1"' in report.read_text(encoding="utf-8")


def test_p0_gate_write_report_flag_persists_full_payload(tmp_path, capsys):
    _write_required_config(tmp_path)
    rc = main(["--project-root", str(tmp_path), "p0-gate", "--write-report"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "report" in captured
    assert (tmp_path / "runtime" / "reports" / "p0_gate_latest.json").exists()


def test_registry_reports_no_command_conflicts():
    registry = ModuleRegistry()
    assert registry.command_conflicts() == []
    assert any(module["key"] == "core" for module in registry.critical_modules())


def test_p0_smoke_writes_report(tmp_path, capsys):
    _write_required_config(tmp_path)
    rc = main(["--project-root", str(tmp_path), "p0-smoke", "--write-report"])
    captured = capsys.readouterr().out
    report = tmp_path / "runtime" / "reports" / "p0_smoke_latest.json"
    assert rc == 0
    assert report.exists()
    assert '"schema": "secondbrain.p0_smoke.v1"' in captured
    assert "runtime.p0_smoke" in (tmp_path / "runtime" / "events_v121" / "events.jsonl").read_text(encoding="utf-8")


def test_p0_contract_validates_launcher_surface(tmp_path, capsys):
    _write_required_config(tmp_path)
    (tmp_path / "launcher.py").write_text("# probe\n", encoding="utf-8")
    rc = main(["--project-root", str(tmp_path), "p0-contract", "--write-report"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert '"schema": "secondbrain.p0_contract.v1"' in captured
    assert '"status": "pass"' in captured
    assert (tmp_path / "runtime" / "reports" / "p0_contract_latest.json").exists()


def test_p0_gate_includes_launcher_contract(tmp_path, capsys):
    _write_required_config(tmp_path)
    (tmp_path / "launcher.py").write_text("# probe\n", encoding="utf-8")
    rc = main(["--project-root", str(tmp_path), "p0-gate"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "p0_launcher_contract" in captured
    assert '"contract": {' in captured


def test_command_index_includes_p0_contract():
    registry = ModuleRegistry()
    assert registry.command_index()["p0-contract"] == "core"
    assert registry.resolve_command("p0-contract").key == "core"


def test_p0_readiness_reports_runtime_dependencies(tmp_path, capsys):
    _write_required_config(tmp_path)
    rc = main(["--project-root", str(tmp_path), "p0-readiness", "--write-report"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert '"schema": "secondbrain.p0_readiness.v1"' in captured
    assert "database_readiness" in captured
    assert "event_bus_readiness" in captured
    assert (tmp_path / "runtime" / "reports" / "p0_readiness_latest.json").exists()
    assert (tmp_path / "runtime" / "state" / "runtime_recovery.json").exists()


def test_p0_bootstrap_creates_minimal_required_config(tmp_path, capsys):
    rc = main(["--project-root", str(tmp_path), "p0-bootstrap", "--write-report"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert '"schema": "secondbrain.p0_bootstrap.v1"' in captured
    assert (tmp_path / "config" / "settings.yaml").exists()
    assert (tmp_path / "config" / "secrets.template.yaml").exists()
    assert (tmp_path / "runtime" / "reports" / "p0_bootstrap_latest.json").exists()


def test_p0_gate_includes_runtime_readiness(tmp_path, capsys):
    _write_required_config(tmp_path)
    rc = main(["--project-root", str(tmp_path), "p0-gate"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "p0_runtime_readiness" in captured
    assert '"readiness": {' in captured


def test_p0_audit_blocks_before_reports_exist(tmp_path, capsys):
    _write_required_config(tmp_path)
    (tmp_path / "launcher.py").write_text("# probe\n", encoding="utf-8")
    (tmp_path / "secondbrain").mkdir()
    (tmp_path / "secondbrain" / "p0_runtime.py").write_text("# probe\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_v170_p0_integration.py").write_text("# probe\n", encoding="utf-8")
    rc = main(["--project-root", str(tmp_path), "p0-audit", "--write-report"])
    captured = capsys.readouterr().out
    assert rc == 1
    assert '"schema": "secondbrain.p0_artifact_audit.v1"' in captured
    assert "report_present:gate" in captured


def test_p0_production_gate_persists_full_p0_evidence(tmp_path, capsys):
    (tmp_path / "launcher.py").write_text("# probe\n", encoding="utf-8")
    (tmp_path / "secondbrain").mkdir()
    (tmp_path / "secondbrain" / "p0_runtime.py").write_text("# probe\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_v170_p0_integration.py").write_text("# probe\n", encoding="utf-8")
    rc = main(["--project-root", str(tmp_path), "p0-production", "--write-report"])
    captured = capsys.readouterr().out
    reports = tmp_path / "runtime" / "reports"
    assert rc == 0
    assert '"schema": "secondbrain.p0_production_gate.v1"' in captured
    assert (reports / "p0_production_gate_latest.json").exists()
    assert (reports / "p0_artifact_audit_latest.json").exists()
    assert (reports / "p0_gate_latest.json").exists()
    assert (reports / "p0_smoke_latest.json").exists()


def test_command_index_includes_p0_production_and_audit():
    registry = ModuleRegistry()
    assert registry.command_index()["p0-production"] == "core"
    assert registry.command_index()["p0-audit"] == "core"
    assert registry.resolve_command("p0-production").key == "core"

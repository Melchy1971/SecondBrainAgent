import json

from secondbrain.desktop_native.native_voice_app_gate import run_native_voice_app_gate


def test_expanded_gate_replaces_placeholder_groups_with_real_checks(tmp_path):
    native = tmp_path / "SecondBrain" / "desktop_native"
    native.mkdir(parents=True)
    (native / "app.py").write_text("", encoding="utf-8")
    report = run_native_voice_app_gate(tmp_path)
    assert report["status"] == "PASS"
    assert report["blocked"] == []
    assert report["metrics"]["navigation_views"] == 18
    assert {item["name"] for item in report["checks"]} == {
        "application_shell", "service_integration", "voice_input", "voice_output", "wake_word",
        "intent_coverage", "dialog_state", "confirmation", "approval", "privacy",
        "workspace_isolation", "recovery", "windows_integration", "accessibility", "performance",
    }


def test_written_gate_report_is_redacted_and_omits_local_report_path(tmp_path):
    native = tmp_path / "SecondBrain" / "desktop_native"
    native.mkdir(parents=True)
    (native / "app.py").write_text("", encoding="utf-8")
    report = run_native_voice_app_gate(tmp_path)
    persisted = json.loads((tmp_path / "runtime" / "reports" / "native_voice_app_gate.json").read_text(encoding="utf-8"))
    assert "report_path" not in persisted
    assert "redacted@example.invalid" not in repr(persisted)
    assert report["report_path"].endswith("native_voice_app_gate.json")

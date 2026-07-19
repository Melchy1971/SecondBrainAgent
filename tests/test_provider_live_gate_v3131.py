import json
from launcher import main
from secondbrain.release.provider_live_gate import BLOCKED, CONDITIONAL_PASS, PASS, _safe_error, run_provider_live_gate


def test_optional_unconfigured_providers_are_conditional(tmp_path):
    report = run_provider_live_gate(tmp_path, env={})
    assert report["status"] == CONDITIONAL_PASS
    assert {p["readiness"] for p in report["providers"]} == {"not_configured"}


def test_required_unconfigured_provider_blocks(tmp_path):
    report = run_provider_live_gate(tmp_path, env={"REQUIRED_LIVE_PROVIDERS": "openai"})
    assert report["status"] == BLOCKED and report["failed_providers"] == ["openai"]


def test_configured_providers_use_probe_without_secrets(tmp_path):
    def probe(config, _env):
        return {"name": config["name"], "readiness": "ready", "model": config["model"], "capabilities": {"chat": True},
                "timeout_seconds": 20, "latency_ms": 1, "usage": {}, "estimated_cost": 0.001,
                "error_code": None, "retryable": False, "source": config["source"]}
    report = run_provider_live_gate(tmp_path, env={"OPENAI_API_KEY": "secret-key", "OPENAI_LIVE_MODEL": "gpt-test",
        "OLLAMA_LIVE_MODEL": "local-test"}, probe=probe)
    assert report["status"] == PASS and "secret-key" not in json.dumps(report)


def test_cost_limit_blocks_expensive_probe(tmp_path):
    def probe(config, _env):
        return {"name": config["name"], "readiness": "ready", "estimated_cost": 2.0}
    report = run_provider_live_gate(tmp_path, env={"OPENAI_API_KEY": "x", "OPENAI_LIVE_MODEL": "m",
        "PROVIDER_LIVE_MAX_COST": "0.01"}, probe=probe)
    assert report["status"] == BLOCKED and report["providers"][0]["error_code"] == "cost_limit_exceeded"


def test_strict_privacy_blocks_cloud_without_calling_probe(tmp_path):
    def probe(_config, _env):
        raise AssertionError("cloud probe must not run")
    report = run_provider_live_gate(tmp_path, env={"OPENAI_API_KEY": "x", "OPENAI_LIVE_MODEL": "m",
        "PRIVACY_MODE": "strict"}, probe=probe)
    assert report["status"] == BLOCKED
    assert report["providers"][0]["error_code"] == "privacy_mode_strict"


def test_provider_errors_are_redacted():
    assert _safe_error(RuntimeError("OPENAI_API_KEY=secret host=private.example"))["message"] == "provider request failed"


def test_launcher_returns_success_for_optional_unconfigured(tmp_path, monkeypatch, capsys):
    for key in ("OPENAI_API_KEY", "OPENAI_LIVE_MODEL", "OLLAMA_LIVE_MODEL", "REQUIRED_LIVE_PROVIDERS"):
        monkeypatch.delenv(key, raising=False)
    assert main(["provider-live-gate", "--project-root", str(tmp_path)]) == 0
    assert '"status": "CONDITIONAL_PASS"' in capsys.readouterr().out

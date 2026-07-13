from __future__ import annotations

from pathlib import Path


def test_runtime_truth_endpoint_function_shape():
    from secondbrain.jarvis_hud_server import runtime_truth

    payload = runtime_truth()

    assert payload["ok"] is True
    assert payload["schema"] == "secondbrain.gui.runtime_truth.v1"
    assert payload["version"] == "v30.22"
    assert "database" in payload
    assert "embedding" in payload
    assert "gates" in payload
    assert "security" in payload


def test_hud_contains_runtime_truth_surface():
    html = Path("web/jarvis_hud/index.html").read_text(encoding="utf-8")

    assert "/api/runtime-truth" in html
    assert "Runtime Truth" in html
    assert "truth-db" in html
    assert "truth-emb" in html
    assert "truth-golden" in html


def test_hud_settings_contains_p1_runtime_fields():
    html = Path("web/jarvis_hud/index.html").read_text(encoding="utf-8")

    for field in [
        "set-database_url_env",
        "set-embedding_provider_env",
        "set-openai_key_env",
        "set-golden_quality_status",
        "set-migration_status",
        "set-secret_vault_status",
        "set-connector_runtime_status",
    ]:
        assert field in html

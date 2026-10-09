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


HUD_HTML = Path("web/jarvis_hud/index.html")

# Status-Elemente, die ausschliesslich aus /api/system-truth befuellt werden.
SYSTEM_TRUTH_ELEMENTS = [
    "p-health", "p-gate", "p-emb", "p-db",
    "i-env", "i-db", "i-emb", "i-ollama", "i-mem", "i-queue",
    "a-gate", "a-emb", "a-db", "a-pgvector", "a-ollama", "a-backup", "a-vindex", "a-queue",
]


def test_hud_status_surface_is_fed_by_system_truth():
    html = HUD_HTML.read_text(encoding="utf-8")

    assert 'getJSON("/api/system-truth")' in html
    for element in SYSTEM_TRUTH_ELEMENTS:
        assert f'id="{element}">—<' in html, f"{element} muss neutral initialisiert sein"


def test_hud_contains_no_fabricated_status_values():
    html = HUD_HTML.read_text(encoding="utf-8")

    for fake in ["EXCELLENT", "BLOCKING 0", "All Systems Operational", "PostgreSQL 16 + pgvector",
                 "Redis Queue", "LangGraph + Memory Store", "Letztes: 15:23", "OpenAI (1536)"]:
        assert fake not in html
    # Platzhalter-Elemente ohne Datenanbindung duerfen nicht zurueckkehren.
    assert 'id="runtime-truth" hidden' not in html
    assert "set-log_level" not in html

"""Tests fuer den Jarvis-HUD-Server (Routing, RAG, Allowlist, Settings)."""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

import secondbrain.hud_core as hud_core
import secondbrain.jarvis_hud_server as srv


@pytest.fixture
def hud(tmp_path, monkeypatch):
    agent = tmp_path / "SecondBrain-Agent"
    (agent / "config").mkdir(parents=True)
    (agent / "logs").mkdir(parents=True)
    (agent / "web" / "jarvis_hud").mkdir(parents=True)
    (agent / "web" / "jarvis_hud" / "index.html").write_text(
        "<html><body>HUD</body></html>", encoding="utf-8")
    vault = tmp_path / "SecondBrain"
    (vault / "01_Projekte").mkdir(parents=True)
    (vault / "01_Projekte" / "telekom.md").write_text(
        "# Telekom\nProzess SAP Abnahme", encoding="utf-8")
    monkeypatch.setattr(hud_core, "ROOT", agent)
    monkeypatch.setattr(hud_core, "VAULT", vault)
    monkeypatch.setattr(hud_core, "INBOX", tmp_path / "SecondBrain-Inbox")
    monkeypatch.setattr(hud_core, "LOG_DIR", agent / "logs")
    monkeypatch.setattr(srv, "ROOT", agent)
    monkeypatch.setattr(srv, "VAULT", vault)
    monkeypatch.setattr(srv, "HUD_HTML", agent / "web" / "jarvis_hud" / "index.html")
    monkeypatch.setattr(srv, "SETTINGS_FILE", agent / "config" / "hud_settings.json")
    return agent


def test_rag_answer_hit_and_miss(hud):
    hit = srv.rag_answer("telekom prozess")
    assert hit["ok"] is True
    assert hit["hits"][0]["note"].endswith("telekom.md")
    miss = srv.rag_answer("zzzznotpresent")
    assert miss["ok"] is False
    assert miss["hits"] == []


def test_rag_answer_empty(hud):
    assert srv.rag_answer("")["ok"] is False


def test_rag_source_path_can_be_opened_as_document(hud):
    hit = srv.rag_answer("telekom prozess")["hits"][0]

    document = srv.document_read(hit["note"])

    assert document["ok"] is True
    assert document["path"] == hit["note"].replace("\\", "/")
    assert "Prozess SAP Abnahme" in document["content"]


def test_assistant_source_chip_opens_document_center():
    html = Path("web/jarvis_hud/index.html").read_text(encoding="utf-8")

    assert 'document.createElement("button")' in html
    assert 'openAssistantSource(s.note)' in html
    assert 'showView("documents")' in html
    assert 'await docsOpen(path, null)' in html


def test_run_allowed_script_blocks_unknown(hud):
    r = srv.run_allowed_script("rm_everything.py")
    assert r["ok"] is False
    assert "Nicht freigegeben" in r["output"]


def test_run_allowed_script_empty(hud):
    assert srv.run_allowed_script("")["ok"] is False


def test_settings_roundtrip(hud):
    saved = srv.save_settings({"place": "Bonn", "news_max": 5, "ignored": "x"})
    assert saved["place"] == "Bonn"
    assert saved["news_max"] == 5
    assert "ignored" not in saved
    assert srv.load_settings()["place"] == "Bonn"


def test_settings_log_redacts_api_keys(hud, monkeypatch):
    events = []
    monkeypatch.setattr(srv, "log_event", lambda event, payload: events.append((event, payload)))

    secret = "test-secret-value"
    saved = srv.save_settings({"place": "Bonn", "openai_api_key": secret})

    assert saved["openai_api_key"] == secret
    assert events == [
        ("hud.settings_saved", {**saved, "openai_api_key": "[redacted]"})
    ]
    assert secret not in json.dumps(events)


def test_assistant_uses_first_configured_model_when_active_model_is_empty(hud, monkeypatch):
    srv.save_settings({
        "assistant_engine": "ollama",
        "assistant_model": "",
        "assistant_models": "llama3.1, gemma4:31b",
    })
    selected = {}

    def fake_llm_chat(engine, model, prompt, temperature):
        selected.update(engine=engine, model=model)
        return "Antwort", model

    monkeypatch.setattr(srv, "_assistant_retrieve", lambda *_args: [])
    monkeypatch.setattr(srv, "_llm_chat", fake_llm_chat)

    result = srv.assistant_chat("Test")

    assert selected == {"engine": "ollama", "model": "llama3.1"}
    assert result["llm_ok"] is True
    assert result["model"] == "llama3.1"


def test_assistant_models_reports_same_default_as_chat(hud, monkeypatch):
    srv.save_settings({
        "assistant_model": "",
        "assistant_models": "llama3.1, gemma4:31b",
    })
    monkeypatch.setattr(srv, "_ollama_models", lambda _base: ["gemma4:31b", "llama3.1:latest"])

    result = srv.assistant_models()

    assert result["active"] == "llama3.1"


@pytest.fixture
def server(hud):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _get(base, path):
    with urllib.request.urlopen(base + path, timeout=10) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read().decode("utf-8")


def _post(base, path, payload):
    req = urllib.request.Request(
        base + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.read().decode("utf-8")


def test_http_index(server):
    st, ct, body = _get(server, "/")
    assert st == 200 and "text/html" in ct and "HUD" in body


@pytest.mark.parametrize("path", [
    "/api/clock", "/api/status", "/api/dashboards", "/api/settings", "/api/logs",
])
def test_http_json_endpoints(server, path):
    st, ct, body = _get(server, path)
    assert st == 200 and "application/json" in ct
    assert isinstance(json.loads(body), dict)


def test_http_rag(server):
    st, ct, body = _get(server, "/api/rag?q=telekom")
    data = json.loads(body)
    assert st == 200 and "hits" in data


def test_http_run_blocked(server):
    st, ct, body = _get(server, "/api/run?script=evil.py")
    data = json.loads(body)
    assert data["ok"] is False and "Nicht freigegeben" in data["output"]


def test_http_unknown_path_returns_json_error(server):
    st, ct, body = _get(server, "/api/nope")
    assert json.loads(body)["ok"] is False


def test_http_post_settings(server):
    st, body = _post(server, "/api/settings", {"place": "Koeln", "news_max": 7})
    data = json.loads(body)
    assert data["ok"] is True
    assert data["settings"]["place"] == "Koeln"
    assert data["settings"]["news_max"] == 7


LEGACY_STATUS_SETTINGS = {
    "version": "v30.21", "environment": "production", "system_health": "EXCELLENT",
    "postgres_status": "ONLINE", "database": "PostgreSQL 16 + pgvector",
    "release_blocking": 0, "queue_pending": 3, "backup_last": "15:23", "vector_index": "OK",
    "log_level": "INFO",
}


def test_legacy_status_settings_are_ignored_and_purged(hud):
    srv.SETTINGS_FILE.write_text(json.dumps({**LEGACY_STATUS_SETTINGS, "place": "Koeln"}), encoding="utf-8")

    loaded = srv.load_settings()
    assert loaded["place"] == "Koeln"
    assert not set(LEGACY_STATUS_SETTINGS) & set(loaded)

    srv.save_settings({"postgres_status": "ONLINE", "news_max": 5})
    stored = json.loads(srv.SETTINGS_FILE.read_text(encoding="utf-8"))
    assert not set(LEGACY_STATUS_SETTINGS) & set(stored)
    assert stored["news_max"] == 5


def test_http_system_truth_endpoint(server, monkeypatch):
    from secondbrain.gui.system_truth import CachedSystemTruth

    monkeypatch.setattr(srv, "_SYSTEM_TRUTH", CachedSystemTruth(lambda: {"ok": True, "schema": "x"}))
    st, ct, body = _get(server, "/api/system-truth")
    assert st == 200 and json.loads(body) == {"ok": True, "schema": "x"}


def test_system_truth_failure_returns_error_payload(monkeypatch):
    from secondbrain.gui.system_truth import CachedSystemTruth

    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(srv, "_SYSTEM_TRUTH", CachedSystemTruth(boom))
    assert srv.system_truth() == {"ok": False, "error": "RuntimeError"}


@pytest.mark.parametrize("method,host,origin,expected", [
    ("GET", "127.0.0.1:8851", None, True),
    ("GET", "localhost:8851", None, True),
    ("GET", "[::1]:8851", None, True),
    ("GET", "evil.example:8851", None, False),          # DNS-Rebinding
    ("GET", None, None, False),
    ("POST", "127.0.0.1:8851", None, True),             # CLI/Tests ohne Origin
    ("POST", "127.0.0.1:8851", "http://127.0.0.1:8851", True),
    ("POST", "127.0.0.1:8851", "http://localhost:8851", True),
    ("POST", "127.0.0.1:8851", "https://evil.example", False),  # CSRF
    ("POST", "127.0.0.1:8851", "http://127.0.0.1:3000", False),  # anderer lokaler Dienst
    ("POST", "127.0.0.1:8851", "null", False),
])
def test_request_allowed(method, host, origin, expected):
    assert srv.request_allowed(method, host, origin, "127.0.0.1", 8851) is expected


def test_http_post_rejects_foreign_origin(server):
    req = urllib.request.Request(
        server + "/api/settings", data=json.dumps({"place": "Evil"}).encode(),
        headers={"Content-Type": "text/plain", "Origin": "https://evil.example"}, method="POST")

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=10)

    assert exc_info.value.code == 403
    assert srv.load_settings()["place"] != "Evil"


def test_http_get_rejects_foreign_host(server):
    req = urllib.request.Request(server + "/api/status", headers={"Host": "evil.example"})

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=10)

    assert exc_info.value.code == 403


def test_http_post_settings_returns_json_write_error(server, monkeypatch):
    def fail_save(_body):
        raise OSError("disk full")

    monkeypatch.setattr(srv, "save_settings", fail_save)
    req = urllib.request.Request(
        server + "/api/settings", data=b"{}",
        headers={"Content-Type": "application/json"}, method="POST")

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req, timeout=10)

    assert exc_info.value.code == 500
    payload = json.loads(exc_info.value.read().decode("utf-8"))
    assert payload == {
        "ok": False,
        "error": "Einstellungen konnten nicht gespeichert werden.",
    }


def test_run_uses_threading_http_server(hud, monkeypatch):
    created = {}

    class FakeThreadingServer:
        def __init__(self, address, handler):
            created["address"] = address
            created["handler"] = handler

        def serve_forever(self):
            created["served"] = True

        def server_close(self):
            created["closed"] = True

    monkeypatch.delenv("HUD_HOST", raising=False)
    monkeypatch.delenv("HUD_PORT", raising=False)
    monkeypatch.delenv("HUD_RELOAD", raising=False)
    monkeypatch.setattr(srv, "ThreadingHTTPServer", FakeThreadingServer)
    monkeypatch.setattr(srv, "log_event", lambda *_args: None)

    srv.run("127.0.0.1", 9876)

    assert created == {
        "address": ("127.0.0.1", 9876),
        "handler": srv.Handler,
        "served": True,
        "closed": True,
    }

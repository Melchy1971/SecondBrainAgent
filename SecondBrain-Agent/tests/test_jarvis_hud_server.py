"""Tests fuer den Jarvis-HUD-Server (Routing, RAG, Allowlist, Settings)."""
import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

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

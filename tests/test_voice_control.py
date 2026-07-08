"""Voice Control v20 - hardware-freie Unit-Tests.

Deckt die reine Logik ab: Intent-Routing, Wake-Word, Diktat-Writer,
HUD-Bruecke (gemockt) und Controller.handle_text. Kein Mikrofon/Whisper/TTS.
"""
import json

from secondbrain.voice import (
    VoiceConfig, VoiceController, VoiceCommandRouter, WakeWordEngine, write_dictation,
)
from secondbrain.voice.hud_bridge import HudBridge


# --- Router --------------------------------------------------------------
def test_router_rag():
    i = VoiceCommandRouter().parse("frage: was steht zu Offshoring")
    assert i.kind == "rag"
    assert "offshoring" in i.payload.lower()


def test_router_dictation_strips_trigger():
    i = VoiceCommandRouter().parse("notiz Rückruf bei Lieferant einplanen")
    assert i.kind == "dictation"
    assert i.payload == "Rückruf bei Lieferant einplanen"


def test_router_script_maps_to_allowlist():
    i = VoiceCommandRouter().parse("bitte index bauen")
    assert i.kind == "run_script"
    assert i.payload == "build_vector_rag.py"


def test_router_stop():
    assert VoiceCommandRouter().parse("stopp").kind == "stop"


def test_router_status():
    assert VoiceCommandRouter().parse("systemstatus bitte").kind == "status"


def test_router_unknown_falls_back_to_query():
    i = VoiceCommandRouter().parse("Telekom SAP Migration")
    assert i.kind == "unknown"
    assert i.payload == "Telekom SAP Migration"


def test_router_backcompat_route():
    r = VoiceCommandRouter()
    assert r.route("zeig mir die mail") == "gmail"
    assert r.route("kalender heute") == "calendar"


# --- Wake-Word -----------------------------------------------------------
def test_wake_word_detect_and_strip():
    w = WakeWordEngine("jarvis")
    assert w.detect("Hey Jarvis, status")
    assert not w.detect("status ohne anrede")
    assert w.strip("Jarvis, systemstatus") == "systemstatus"
    assert w.strip("hey jarvis status") == "status"


# --- Diktat --------------------------------------------------------------
def test_write_dictation(tmp_path):
    p = write_dictation("Lieferantenwechsel dokumentieren", tmp_path)
    assert p.exists()
    body = p.read_text(encoding="utf-8")
    assert "type: dictation" in body
    assert "Lieferantenwechsel dokumentieren" in body


def test_write_dictation_empty_raises(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        write_dictation("   ", tmp_path)


# --- HUD-Bridge (gemockt) ------------------------------------------------
def _fake_opener(responses):
    def _open(url):
        for needle, payload in responses.items():
            if needle in url:
                return json.dumps(payload)
        return json.dumps({"ok": False, "error": "unmocked"})
    return _open


def test_hud_bridge_rag_mocked():
    bridge = HudBridge(opener=_fake_opener({
        "/api/rag": {"ok": True, "answer": "2 Notizen gefunden.", "hits": [1, 2]},
    }))
    res = bridge.rag("offshoring")
    assert res["ok"] and "Notizen" in res["answer"]


def test_hud_bridge_network_error_is_clean():
    def boom(url):
        raise OSError("connection refused")
    bridge = HudBridge(opener=boom)
    res = bridge.rag("x")
    assert res["ok"] is False and "connection refused" in res["error"]


# --- Controller ----------------------------------------------------------
def _ctrl(tmp_path, responses, allow=False):
    cfg = VoiceConfig()
    cfg.dictation_dir = tmp_path / "dict"
    cfg.sessions_log = tmp_path / "sessions.json"
    cfg.allow_system_actions = allow
    return VoiceController(cfg, hud=HudBridge(opener=_fake_opener(responses)))


def test_controller_rag_speaks_answer(tmp_path):
    c = _ctrl(tmp_path, {"/api/rag": {"ok": True, "answer": "Top-Treffer: A, B."}})
    r = c.handle_text("frage: SAP Migration")
    assert r.intent == "rag" and r.ok and "Top-Treffer" in r.speech


def test_controller_dictation_writes_file(tmp_path):
    c = _ctrl(tmp_path, {})
    r = c.handle_text("notiz Angebot bis Freitag pruefen")
    assert r.intent == "dictation" and r.ok
    assert (tmp_path / "dict").exists()
    assert r.data["path"].endswith(".md")


def test_controller_script_blocked_by_default(tmp_path):
    c = _ctrl(tmp_path, {"/api/run": {"ok": True}})
    r = c.handle_text("index bauen")
    assert r.intent == "run_script" and r.ok is False
    assert r.data.get("blocked") is True


def test_controller_script_runs_when_allowed(tmp_path):
    c = _ctrl(tmp_path, {"/api/run": {"ok": True, "script": "build_vector_rag.py"}}, allow=True)
    r = c.handle_text("index bauen")
    assert r.intent == "run_script" and r.ok is True


def test_controller_stop(tmp_path):
    c = _ctrl(tmp_path, {})
    assert c.handle_text("beenden").intent == "stop"


def test_controller_logs_session(tmp_path):
    c = _ctrl(tmp_path, {"/api/rag": {"ok": True, "answer": "ok"}})
    r = c.handle_text("frage: test")
    c.log_session("frage: test", r)
    entries = json.loads((tmp_path / "sessions.json").read_text(encoding="utf-8"))
    assert entries and entries[-1]["intent"] == "rag"


# --- Config --------------------------------------------------------------
def test_config_load_merges_old_settings(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({
        "wake_word": "jarvis", "mode": "push_to_talk",
        "stt_provider": "manual", "tts_provider": "console",
        "allow_system_actions": False,
    }), encoding="utf-8")
    cfg = VoiceConfig.load(p)
    assert cfg.mode == "push_to_talk"
    assert cfg.stt_provider == "manual"
    assert cfg.allow_system_actions is False


def test_hud_bridge_is_up_false_on_error():
    def boom(url):
        raise OSError("refused")
    assert HudBridge(opener=boom).is_up() is False


def test_hud_bridge_is_up_true_on_status():
    bridge = HudBridge(opener=_fake_opener({"/api/status": {"ok": True, "cpu": 3}}))
    assert bridge.is_up() is True

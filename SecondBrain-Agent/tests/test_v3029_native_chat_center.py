from __future__ import annotations

import json
from pathlib import Path

from secondbrain.native.chat import NativeChatMessage, NativeChatService, NativeChatStore, native_chat_status
from secondbrain.native.runtime_snapshot import build_native_view_model


def test_native_chat_store_roundtrip(tmp_path: Path):
    store = NativeChatStore(tmp_path)
    store.append(NativeChatMessage(role="user", content="Hallo Jarvis", ts=1.0))
    store.append({"role": "assistant", "content": "Bereit", "ts": 2.0})
    status = store.status(limit=10)
    assert status["ok"] is True
    assert status["total_messages"] == 2
    assert status["messages"][-1]["content"] == "Bereit"


def test_native_chat_clear(tmp_path: Path):
    store = NativeChatStore(tmp_path)
    store.append({"role": "user", "content": "x", "ts": 1})
    assert store.status()["total_messages"] == 1
    assert store.clear()["ok"] is True
    assert store.status()["total_messages"] == 0


def test_native_chat_service_empty_question_is_blocked(tmp_path: Path):
    service = NativeChatService(tmp_path)
    result = service.ask("   ")
    assert result["ok"] is False
    assert result["status"] == "empty_question"


def test_native_view_model_exposes_chat(tmp_path: Path):
    NativeChatStore(tmp_path).append({"role": "user", "content": "Projektstatus", "ts": 1})
    model = build_native_view_model(tmp_path)
    assert model["schema"] == "secondbrain.native.view_model.v30_29"
    assert model["version"] == "30.29"
    assert model["chat"]["schema"] == "secondbrain.native.chat.v30_29"


def test_native_chat_status_function(tmp_path: Path):
    payload = native_chat_status(tmp_path)
    assert payload["ok"] is True
    assert payload["status"] == "ready"

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.ai_runtime_v105 import EchoProvider, ModelRouter, build_context
from secondbrain.connector_runtime_v104 import registry_from_config, sync_all
from secondbrain.normalizer_v104 import normalize_calendar_event, normalize_document, normalize_email
from secondbrain.runtime_events_v104 import JsonlEventStore, RuntimeEvent


def test_runtime_event_store_roundtrip(tmp_path):
    store = JsonlEventStore(tmp_path)
    event = RuntimeEvent(event_type="test.created", source="unit", payload={"value": 1})
    store.append(event)
    loaded = store.read_all()
    assert len(loaded) == 1
    assert loaded[0].payload["value"] == 1
    assert store.summarize()["event_count"] == 1


def test_normalizers_create_stable_records():
    email = normalize_email({"subject": " Test ", "from": "a@example.local", "body": "Hallo   Welt"})
    calendar = normalize_calendar_event({"title": "Termin", "start": "2026-01-01", "end": "2026-01-02"})
    document = normalize_document({"title": "Dok", "text": "Inhalt"})
    assert email.record_type == "email"
    assert calendar.record_type == "calendar_event"
    assert document.to_dict()["content_hash"]


def test_connector_registry_syncs_local_json(tmp_path):
    payload = tmp_path / "items.json"
    payload.write_text(json.dumps({"items": [{"id": "1", "title": "Dok", "text": "Inhalt"}]}), encoding="utf-8")
    cfg = {"connectors": [{"name": "docs", "kind": "local_json", "record_type": "document", "path": str(payload), "enabled": True}]}
    registry = registry_from_config(Path("/"), cfg)
    store = JsonlEventStore(tmp_path / "events")
    results = sync_all(registry, store)
    assert results[0].normalized == 1
    assert store.filter(event_type="connector.record.normalized")[0].payload["title"] == "Dok"


def test_ai_router_echo_and_context_builder():
    router = ModelRouter({"echo": EchoProvider()}, default_provider="echo")
    answer = router.run("unit", "Hallo")
    assert answer.startswith("[echo:unit]")
    context = build_context([{"title": "A", "body": "B"}])
    assert "## A" in context

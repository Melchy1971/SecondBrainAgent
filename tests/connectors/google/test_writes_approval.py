import pytest
from secondbrain.connectors.scaffold.approval import ApprovalGate, ApprovalRequired, InMemoryApprovalStore
from secondbrain.connectors.google.registry import build_writers, RESOURCE_NAMES
from secondbrain.connectors.google.resources import gmail
from secondbrain.connectors.scaffold.transport import FakeTransport


def test_gmail_send_blocked_then_approved(config, authed):
    tp = FakeTransport()
    tp.on("POST", "messages/send", lambda u, m, h, b: tp.json_response(200, {"id": "sent1"}))
    _, client = authed(config, tp, {"t": 1000.0})
    gate = ApprovalGate(InMemoryApprovalStore())
    writer = gmail.GmailWriter(client, gate)
    with pytest.raises(ApprovalRequired):
        writer.send(["a@b.de"], "S", "body")
    assert not any("send" in c["url"] for c in tp.calls)
    gate.approve(gate.pending()[0].request_id)
    resp = writer.send(["a@b.de"], "S", "body")
    assert resp.status == 200


REPRESENTATIVE = {
    "gmail": lambda w: w.send(["a@b.de"], "s", "body"),
    "calendar": lambda w: w.create_event("s", "2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z"),
    "drive": lambda w: w.upload_text("f.txt", "hi"),
    "contacts": lambda w: w.create("A", "B", ["a@b.de"]),
    "tasks": lambda w: w.create_task("L1", "t"),
}


@pytest.mark.parametrize("resource", list(RESOURCE_NAMES))
def test_every_google_write_is_gated(config, authed, resource):
    tp = FakeTransport()
    _, client = authed(config, tp, {"t": 1000.0})
    gate = ApprovalGate(InMemoryApprovalStore())
    writers = build_writers(client, gate)
    with pytest.raises(ApprovalRequired):
        REPRESENTATIVE[resource](writers[resource])
    assert all(c["method"] == "GET" or "/token" in c["url"] for c in tp.calls)
    assert len(gate.pending()) == 1

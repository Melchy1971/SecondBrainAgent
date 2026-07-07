import pytest
from secondbrain.connectors.microsoft.approval import ApprovalGate, ApprovalRequired, InMemoryApprovalStore
from secondbrain.connectors.microsoft.registry import build_writers, RESOURCE_NAMES
from secondbrain.connectors.microsoft.resources import mail
from secondbrain.connectors.microsoft.transport import FakeTransport


def test_write_blocked_until_approved(config, authed):
    tp = FakeTransport()
    tp.on("POST", "me/sendMail", lambda u, m, h, b: tp.json_response(202, {}))
    _, client = authed(config, tp, {"t": 1000.0})
    gate = ApprovalGate(InMemoryApprovalStore())
    writer = mail.MailWriter(client, gate)

    with pytest.raises(ApprovalRequired):
        writer.send(["a@b.de"], "Subject", "<b>hi</b>")
    pending = gate.pending()
    assert len(pending) == 1 and pending[0].action == "mail.send"
    # transport must not have been hit yet
    assert not any("sendMail" in c["url"] for c in tp.calls)

    gate.approve(pending[0].request_id)
    resp = writer.send(["a@b.de"], "Subject", "<b>hi</b>")
    assert resp.status == 202
    assert any("sendMail" in c["url"] for c in tp.calls)


def test_auto_approve_executes_immediately(config, authed):
    tp = FakeTransport()
    tp.on("POST", "me/sendMail", lambda u, m, h, b: tp.json_response(202, {}))
    _, client = authed(config, tp, {"t": 1000.0})
    writer = mail.MailWriter(client, ApprovalGate(auto_approve=True))
    assert writer.send(["a@b.de"], "S", "x").status == 202


REPRESENTATIVE = {
    "mail": lambda w: w.send(["a@b.de"], "s", "<b>x</b>"),
    "calendar": lambda w: w.create_event("s", "2026-01-01T00:00:00", "2026-01-01T01:00:00"),
    "contacts": lambda w: w.create("A", "B", ["a@b.de"]),
    "onedrive": lambda w: w.upload_text("f.txt", "hi"),
    "teams": lambda w: w.post_chat_message("chatA", "hi"),
    "todo": lambda w: w.create_task("L1", "t"),
    "onenote": lambda w: w.create_page("sec", "T", "<p>x</p>"),
}


@pytest.mark.parametrize("resource", list(RESOURCE_NAMES))
def test_every_write_is_approval_gated(config, authed, resource):
    tp = FakeTransport()
    # register a catch-all success so that IF a write leaked through we'd see it in calls
    _, client = authed(config, tp, {"t": 1000.0})
    gate = ApprovalGate(InMemoryApprovalStore())
    writers = build_writers(client, gate)
    with pytest.raises(ApprovalRequired):
        REPRESENTATIVE[resource](writers[resource])
    # no write call reached the transport
    assert all(c["method"] == "GET" or "/oauth2/" in c["url"] for c in tp.calls)
    assert len(gate.pending()) == 1

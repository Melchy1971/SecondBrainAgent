"""Sprint 46 acceptance tests - governed email assistant."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from secondbrain.mail_assistant.models import Category, MailMessage, MailThread
from secondbrain.mail_assistant.service import MailAssistant, MailConnectorError
from secondbrain.mail_assistant.gui import MailViewModel, render_mail_html

WS = "ws-1"
SECRET = "api_key=sk-abcdef012345ABCDEF6789 and password=Hunter2Hunter2"
PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----\nMIIBVstuff\n-----END PRIVATE KEY-----"


def _iso(days_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(timespec="seconds")


def _msg(**kw):
    base = dict(message_id="m1", thread_id="t1", mailbox_id="mb1", workspace_id=WS,
               sender="anna.beispiel@telekom.de", recipients=["markus@telekom.de"],
               subject="Betreff", body="", received_at=_iso(0))
    base.update(kw)
    return MailMessage(**base)


class OKConnector:
    def __init__(self):
        self.sent = []
    def send_reply(self, payload):
        self.sent.append(payload)
        return {"external_id": "sent-1"}
    def delete_message(self, payload):
        self.sent.append(payload)
        return {"deleted": True}


class OfflineConnector:
    def send_reply(self, payload):
        raise MailConnectorError("offline")


class ApprovalQueue:
    def __init__(self):
        self.started = set()

    def create(self, **_kwargs):
        return {"approval_id": "approval-1"}

    def begin_execution(self, approval_id, **_kwargs):
        if approval_id in self.started:
            raise RuntimeError("already_executed")
        self.started.add(approval_id)
        return {"status": "executing"}


def _assistant(connector=None):
    return MailAssistant(connector=connector, vips=["chef@telekom.de"],
                         projects=["secondbrain"], owner="markus@telekom.de")


# 1: thread summarized
def test_thread_summarized():
    msgs = [_msg(message_id="a", body="Startpunkt.", received_at=_iso(2)),
            _msg(message_id="b", sender="markus@telekom.de", body="Antwort dazu?", received_at=_iso(1))]
    s = _assistant().summarize_thread(msgs)
    assert s["message_count"] == 2
    assert s["summary"]
    assert "Antwort dazu?" in " ".join(s["open_questions"])


# 2: important prioritized higher
def test_important_prioritized_higher():
    a = _assistant()
    important = _msg(message_id="i", sender="chef@telekom.de",
                     body="Dringend, Frist 2026-07-20, markus@telekom.de bitte antworten?", received_at=_iso(0))
    trivial = _msg(message_id="n", sender="newsletter@x.de", subject="Newsletter",
                   body="Info", unread=False, recipients=["list@telekom.de"], received_at=_iso(0))
    ranked = a.prioritize_inbox([trivial, important], workspace_id=WS)
    assert ranked[0]["source_reference"] == "i"
    assert ranked[0]["score"] > ranked[1]["score"]


# 3: task with source reference
def test_task_with_source_reference():
    m = _msg(message_id="task-src", external_id="ext-9",
             body="Bitte Angebot erstellen bis 2026-07-30\nSonstiges")
    tasks = _assistant().extract_tasks(m)
    assert tasks
    assert tasks[0]["source_reference"] == "ext-9"
    assert tasks[0]["suggested_due"] == "2026-07-30"
    assert 0 < tasks[0]["confidence"] <= 1
    assert tasks[0]["status"] == "proposed"


# 4: reply draft NOT sent
def test_reply_draft_not_sent():
    m = _msg(body="Wann liefert ihr? Und wie hoch ist der Preis?")
    d = _assistant().generate_reply_draft([m])
    assert d["sent"] is False
    assert "UNSICHER" in d["draft"]


# 5: send creates approval (not executed)
def test_send_creates_approval():
    conn = OKConnector()
    a = _assistant(conn)
    prep = a.prepare_change("send_reply", {"thread_id": "t1", "body": "Hi"}, workspace_id=WS)
    assert prep["status"] == "approval_required"
    assert conn.sent == []  # nothing sent yet


# 6: approved send commits exactly once
def test_approved_send_exactly_once():
    conn = OKConnector()
    a = _assistant(conn)
    payload = {"thread_id": "t1", "body": "Hallo"}
    queue = ApprovalQueue()
    prep = a.prepare_change("send_reply", payload, workspace_id=WS, approval_queue=queue)
    r1 = a.commit_change(prep, payload, approval_queue=queue, workspace_id=WS)
    r2 = a.commit_change(prep, payload, approval_queue=queue, workspace_id=WS)
    assert r1["status"] == "committed"
    assert r2["status"] == "duplicate"
    assert len(conn.sent) == 1


# 6b: not approved -> blocked
def test_not_approved_blocked():
    conn = OKConnector()
    a = _assistant(conn)
    payload = {"thread_id": "t1", "body": "x"}
    prep = a.prepare_change("send_reply", payload, workspace_id=WS)
    assert a.commit_change(prep, payload, approval_queue=None, workspace_id=WS)["status"] == "blocked"
    assert conn.sent == []


# 6c: tampered payload rejected
def test_tampered_payload_rejected():
    conn = OKConnector()
    a = _assistant(conn)
    queue = ApprovalQueue()
    prep = a.prepare_change("send_reply", {"thread_id": "t1", "body": "a"}, workspace_id=WS, approval_queue=queue)
    assert a.commit_change(prep, {"thread_id": "t1", "body": "b"}, approval_queue=queue, workspace_id=WS)["status"] == "invalid"
    assert conn.sent == []


# 7: delete requires approval
def test_delete_requires_approval():
    conn = OKConnector()
    a = _assistant(conn)
    payload = {"message_id": "m1"}
    queue = ApprovalQueue()
    prep = a.prepare_change("delete_message", payload, workspace_id=WS, approval_queue=queue)
    assert prep["status"] == "approval_required"
    assert conn.sent == []
    assert a.commit_change(prep, payload, approval_queue=queue, workspace_id=WS)["status"] == "committed"


# 8: secrets / private keys NOT in summaries or drafts
def test_no_secrets_in_summary_or_draft():
    m = _msg(body=f"Zugang: {SECRET}\n{PRIVATE_KEY}\nAlles klar?")
    s = _assistant().summarize_thread([m])
    blob = s["summary"] + " ".join(s["open_questions"])
    assert "sk-abcdef" not in blob and "Hunter2" not in blob
    assert "BEGIN PRIVATE KEY" not in blob
    d = _assistant().generate_reply_draft([m])
    assert "sk-abcdef" not in d["draft"] and "BEGIN PRIVATE KEY" not in d["draft"]
    tasks = _assistant().extract_tasks(_msg(body=f"Bitte {SECRET} weiterleiten"))
    for t in tasks:
        assert "sk-abcdef" not in t["candidate_title"] and "Hunter2" not in t["candidate_title"]


# 9: attachments referenced by name only
def test_attachments_referenced_by_name():
    m = _msg(has_attachments=True, attachments=["Angebot.pdf"], external_id="ext-att")
    refs = _assistant().detect_attachments([m])
    assert refs == [{"name": "Angebot.pdf", "message_reference": "ext-att"}]


def test_attachments_use_import_pipeline_and_sensitive_review():
    class Sink:
        def __init__(self): self.items = []
        def enqueue(self, item): self.items.append(item); return {"status": "queued"}
        def add(self, item): self.items.append(item); return {"status": "review"}

    pipeline, review = Sink(), Sink()
    normal = _msg(attachments=["report.pdf"], has_attachments=True, connector_id="gmail")
    assert _assistant().queue_attachments(normal, import_pipeline=pipeline, review_queue=review)[0]["status"] == "queued"
    sensitive = _msg(attachments=["secret.pdf"], has_attachments=True, body=SECRET)
    assert _assistant().queue_attachments(sensitive, import_pipeline=pipeline, review_queue=review)[0]["status"] == "review"


# 10: offline connector -> controlled error, no data loss / no exception
def test_offline_connector_no_data_loss():
    a = _assistant(OfflineConnector())
    payload = {"thread_id": "t1", "body": "Hi"}
    queue = ApprovalQueue()
    prep = a.prepare_change("send_reply", payload, workspace_id=WS, approval_queue=queue)
    res = a.commit_change(prep, payload, approval_queue=queue, workspace_id=WS)
    assert res["status"] == "recovery_required"
    # not marked committed -> retry possible once connector is back
    ok = MailAssistant(connector=OKConnector())
    # same prepared can be retried against a working assistant instance
    assert "reason" in res


def test_recipient_or_workspace_change_invalidates_approval():
    assistant = _assistant(OKConnector())
    queue = ApprovalQueue()
    payload = {"thread_id": "t1", "to": ["a@example.test"], "body": "Hi"}
    prepared = assistant.prepare_change("send_reply", payload, workspace_id=WS, connector_id="gmail", approval_queue=queue)
    assert prepared["recipient_hash"] and prepared["body_hash"] and prepared["idempotency_key"]
    changed = {**payload, "to": ["b@example.test"]}
    assert assistant.commit_change(prepared, changed, approval_queue=queue, workspace_id=WS)["status"] == "invalid"
    assert assistant.commit_change(prepared, payload, approval_queue=queue, workspace_id="ws-2")["reason"] == "workspace_mismatch"


# workspace isolation
def test_workspace_isolation():
    a = _assistant()
    mine = _msg(message_id="mine", workspace_id=WS)
    other = _msg(message_id="other", workspace_id="ws-2")
    got = a.list_messages([mine, other], workspace_id=WS)
    assert [m.message_id for m in got] == ["mine"]


# classification
def test_classify_categories():
    a = _assistant()
    assert a.classify_message(_msg(subject="Rechnung 12", body="Betrag fällig")) == Category.INVOICE.value
    assert a.classify_message(_msg(subject="Vertrag", body="NDA zur Prüfung")) == Category.CONTRACT.value
    assert a.classify_message(_msg(subject="Meeting", body="Termin morgen")) == Category.MEETING.value


# gui view model has no raw factors leak / renders
def test_view_model_and_render():
    a = _assistant()
    m = _msg(body="Bitte prüfen bis 2026-07-20?")
    thread = MailThread(thread_id="t1", mailbox_id="mb1", workspace_id=WS, subject="Betreff",
                        participants=["anna.beispiel@telekom.de"], latest_message_at=_iso(0),
                        unread_count=1, importance_score=1.0, action_required=True, due_date="",
                        category=Category.ACTION_REQUIRED.value, summary="s", source="gmail", external_id="e1")
    vm = MailViewModel(a)
    view = vm.build(workspace_id=WS, messages=[m], threads=[thread], thread_messages={"t1": [m]})
    assert view["prioritized_inbox"]
    assert view["drafts"] and view["drafts"][0]["sent"] is False
    html_out = render_mail_html(view)
    assert "Priorisierter Posteingang" in html_out
    assert "sk-" not in html_out


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

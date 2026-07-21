import pytest

from secondbrain.calendar_assistant.service import CalendarService
from secondbrain.desktop_native.action_bus import NativeActionBus
from secondbrain.mail_assistant.service import MailAssistant


class _MailConnector:
    def __init__(self):
        self.sent = []

    def send_new_message(self, payload):
        self.sent.append(dict(payload))
        return {"external_id": "mail-1"}


class _CalendarConnector:
    def __init__(self):
        self.created = []

    def create_event(self, payload):
        self.created.append(dict(payload))
        return {"external_id": "event-1"}


def _mail_bus(tmp_path, connector):
    return NativeActionBus(
        tmp_path,
        workspace_id="alpha",
        mail_assistant=MailAssistant(connector=connector),
    )


def test_approved_mail_executes_once_and_completes_persistent_lease(tmp_path):
    connector = _MailConnector()
    bus = _mail_bus(tmp_path, connector)
    proposal = bus.submit("sende mail", {"recipient": "a@example.test", "body": "Hallo"})

    pending = bus.submit("freigabe genehmigen", {"approval": proposal["approval_id"]})
    assert pending["status"] == "confirmation_required"
    result = bus.confirm()

    assert result["status"] == "executed"
    assert result["result"]["status"] == "completed"
    assert connector.sent == [{"recipients": ["a@example.test"], "subject": "", "body": "Hallo"}]
    assert bus.approvals.get(proposal["approval_id"])["status"] == "completed"
    with pytest.raises(ValueError, match="not pending"):
        bus.decide_approval(proposal["approval_id"], approved=True)


def test_approved_calendar_executes_service_bound_payload(tmp_path):
    connector = _CalendarConnector()
    bus = NativeActionBus(
        tmp_path,
        workspace_id="alpha",
        calendar_service=CalendarService(connector),
    )
    proposal = bus.submit("erstelle termin", {"title": "Arzt", "when": "2026-07-22T14:00:00+02:00"})

    bus.submit("freigabe genehmigen", {"approval": proposal["approval_id"]})
    result = bus.confirm()

    assert result["status"] == "executed"
    assert connector.created == [{
        "event_id": "",
        "title": "Arzt",
        "start": "2026-07-22T14:00:00+02:00",
        "end": "2026-07-22T15:00:00+02:00",
    }]
    assert bus.approvals.get(proposal["approval_id"])["status"] == "completed"


def test_unresolved_calendar_time_requests_correction_before_approval(tmp_path):
    connector = _CalendarConnector()
    bus = NativeActionBus(
        tmp_path,
        workspace_id="alpha",
        calendar_service=CalendarService(connector),
    )
    result = bus.submit("erstelle termin", {"title": "Arzt", "when": "morgen um zwei"})

    assert result["status"] == "slots_required"
    assert result["error"] == "calendar_time_unresolved"
    assert connector.created == []
    assert bus.approvals.list() == []


def test_rejected_external_write_never_invokes_connector(tmp_path):
    connector = _MailConnector()
    bus = _mail_bus(tmp_path, connector)
    proposal = bus.submit("sende mail", {"recipient": "a@example.test", "body": "Hallo"})

    bus.submit("freigabe ablehnen", {"approval": proposal["approval_id"]})
    result = bus.confirm()

    assert result["status"] == "executed"
    assert result["result"]["status"] == "rejected"
    assert connector.sent == []
    assert bus.approvals.get(proposal["approval_id"])["status"] == "rejected"


def test_missing_connector_leaves_approval_pending(tmp_path):
    bus = NativeActionBus(tmp_path, workspace_id="alpha")
    proposal = bus.submit("sende mail", {"recipient": "a@example.test", "body": "Hallo"})

    bus.submit("freigabe genehmigen", {"approval": proposal["approval_id"]})
    result = bus.confirm()

    assert result["status"] == "error"
    assert "connector" in result["error"]
    assert bus.approvals.get(proposal["approval_id"])["status"] == "pending"


def test_approval_decision_rejects_workspace_crossing(tmp_path):
    connector = _MailConnector()
    owner = _mail_bus(tmp_path, connector)
    proposal = owner.submit("sende mail", {"recipient": "a@example.test", "body": "Hallo"})
    other_workspace = NativeActionBus(
        tmp_path,
        workspace_id="beta",
        mail_assistant=MailAssistant(connector=connector),
    )

    with pytest.raises(PermissionError, match="workspace mismatch"):
        other_workspace.decide_approval(proposal["approval_id"], approved=True)

    assert connector.sent == []
    assert owner.approvals.get(proposal["approval_id"])["status"] == "pending"


def test_competing_executor_lease_is_never_finalized(tmp_path, monkeypatch):
    connector = _MailConnector()
    assistant = MailAssistant(connector=connector)
    bus = NativeActionBus(tmp_path, workspace_id="alpha", mail_assistant=assistant)
    proposal = bus.submit("sende mail", {"recipient": "a@example.test", "body": "Hallo"})

    def competing_commit(prepared, _payload, *, approval_queue, workspace_id):
        assert workspace_id == "alpha"
        approval_queue.begin_execution(
            prepared["approval_id"],
            executor_id="competing-worker",
            idempotency_key=prepared["idempotency_key"],
        )
        return {"status": "blocked", "reason": "approval_not_executable"}

    monkeypatch.setattr(assistant, "commit_change", competing_commit)
    bus.submit("freigabe genehmigen", {"approval": proposal["approval_id"]})
    result = bus.confirm()

    assert result["status"] == "error"
    active = bus.approvals.get(proposal["approval_id"])
    assert active["status"] == "executing"
    assert active["owner"] == "competing-worker"
    assert connector.sent == []


def test_tampered_approval_payload_is_rejected_before_decision(tmp_path):
    connector = _MailConnector()
    bus = _mail_bus(tmp_path, connector)
    proposal = bus.submit("sende mail", {"recipient": "a@example.test", "body": "Hallo"})
    row = bus.approvals.get(proposal["approval_id"])
    payload = dict(row["payload"])
    payload["execution_payload"] = {**payload["execution_payload"], "body": "Manipuliert"}
    bus.approvals.update_metadata(proposal["approval_id"], {"payload": payload})

    bus.submit("freigabe genehmigen", {"approval": proposal["approval_id"]})
    result = bus.confirm()

    assert result["status"] == "error"
    assert "payload changed" in result["error"]
    assert connector.sent == []
    assert bus.approvals.get(proposal["approval_id"])["status"] == "pending"


def test_tampered_approval_action_is_rejected_before_decision(tmp_path):
    connector = _MailConnector()
    connector.delete_message = lambda payload: connector.sent.append(dict(payload))
    bus = _mail_bus(tmp_path, connector)
    proposal = bus.submit("sende mail", {"recipient": "a@example.test", "body": "Hallo"})
    row = bus.approvals.get(proposal["approval_id"])
    payload = {**row["payload"], "action": "delete_message"}
    bus.approvals.update_metadata(proposal["approval_id"], {"payload": payload})

    bus.submit("freigabe genehmigen", {"approval": proposal["approval_id"]})
    result = bus.confirm()

    assert result["status"] == "error"
    assert "action binding changed" in result["error"]
    assert connector.sent == []
    assert bus.approvals.get(proposal["approval_id"])["status"] == "pending"

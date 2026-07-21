import base64
from email import policy
from email.parser import BytesParser
from types import SimpleNamespace

import pytest

from secondbrain.calendar_assistant.service import CalendarService
from secondbrain.desktop_native.action_bus import NativeActionBus
from secondbrain.desktop_native.external_action_connectors import (
    PROVIDER_ENV,
    build_external_action_connectors,
)
from secondbrain.mail_assistant.service import MailAssistant


class _Response:
    def __init__(self, status=200, payload=None):
        self.status = status
        self.payload = payload or {}

    def json(self):
        return dict(self.payload)


class _Client:
    def __init__(self):
        self.posts = []

    def post(self, path, payload):
        self.posts.append((path, payload))
        external_id = "event-1" if "event" in path else "message-1"
        return _Response(201 if "event" in path else 202, {"id": external_id})


class _Auth:
    def __init__(self, authenticated):
        self.authenticated = authenticated

    def is_authenticated(self):
        return self.authenticated


class _BrokenAuth:
    def is_authenticated(self):
        raise ValueError("corrupt token with secret")


def _factory(client, *, authenticated=True):
    def build(_root, *, env):
        assert PROVIDER_ENV in env
        return SimpleNamespace(auth=_Auth(authenticated), client=client)

    return build


def test_provider_is_explicitly_disabled_by_default(tmp_path):
    bundle = build_external_action_connectors(tmp_path, env={})

    assert bundle.status() == {
        "provider": "disabled",
        "configured": False,
        "authenticated": False,
        "calendar_write": False,
        "mail_write": False,
        "reason": "disabled",
    }


def test_unsupported_provider_is_blocked_without_echoing_value(tmp_path):
    bundle = build_external_action_connectors(tmp_path, env={PROVIDER_ENV: "secret-provider-name"})

    assert bundle.provider == "unsupported"
    assert bundle.reason == "unsupported_provider"
    assert "secret-provider-name" not in repr(bundle.status())


def test_configured_but_unauthenticated_provider_exposes_no_writers(tmp_path):
    client = _Client()
    bundle = build_external_action_connectors(
        tmp_path,
        env={PROVIDER_ENV: "google"},
        google_runtime_factory=_factory(client, authenticated=False),
    )

    assert bundle.configured is True
    assert bundle.authenticated is False
    assert bundle.reason == "authentication_required"
    assert bundle.calendar is None and bundle.mail is None


def test_missing_provider_credentials_are_a_safe_configuration_error(tmp_path):
    bundle = build_external_action_connectors(tmp_path, env={PROVIDER_ENV: "google"})

    assert bundle.reason == "configuration_error"
    assert bundle.status()["calendar_write"] is False


def test_corrupt_authentication_state_does_not_block_desktop_startup(tmp_path):
    def factory(_root, *, env):
        assert env[PROVIDER_ENV] == "google"
        return SimpleNamespace(auth=_BrokenAuth(), client=_Client())

    bundle = build_external_action_connectors(
        tmp_path,
        env={PROVIDER_ENV: "google"},
        google_runtime_factory=factory,
    )

    assert bundle.configured is True
    assert bundle.reason == "authentication_status_unavailable"
    assert "secret" not in repr(bundle.status())


def test_google_adapters_translate_calendar_and_mail_payloads(tmp_path):
    client = _Client()
    bundle = build_external_action_connectors(
        tmp_path,
        env={PROVIDER_ENV: "google"},
        google_runtime_factory=_factory(client),
    )

    calendar_result = bundle.calendar.create_event({
        "title": "Arzt",
        "start": "2026-07-22T14:00:00+02:00",
        "end": "2026-07-22T15:00:00+02:00",
    })
    mail_result = bundle.mail.send_new_message({
        "recipients": ["a@example.test"],
        "subject": "Status",
        "body": "Hallo",
    })

    calendar_path, calendar_payload = client.posts[0]
    assert calendar_path == "calendar/v3/calendars/primary/events"
    assert calendar_payload["start"]["dateTime"] == "2026-07-22T14:00:00+02:00"
    mail_path, mail_payload = client.posts[1]
    assert mail_path.endswith("/users/me/messages/send")
    message = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(mail_payload["raw"]))
    assert message["To"] == "a@example.test"
    assert message["Subject"] == "Status"
    assert message.get_body().get_content().strip() == "Hallo"
    assert calendar_result == {"provider": "google", "external_id": "event-1", "http_status": 201}
    assert mail_result["provider"] == "google"


def test_m365_adapters_normalize_calendar_to_utc_and_send_plain_text(tmp_path):
    client = _Client()
    bundle = build_external_action_connectors(
        tmp_path,
        env={PROVIDER_ENV: "microsoft"},
        m365_runtime_factory=_factory(client),
    )

    bundle.calendar.create_event({
        "title": "Arzt",
        "start": "2026-07-22T14:00:00+02:00",
        "end": "2026-07-22T15:00:00+02:00",
    })
    bundle.mail.send_new_message({
        "recipients": ["a@example.test"],
        "subject": "Status",
        "body": "Hallo",
    })

    assert client.posts[0] == (
        "me/events",
        {
            "subject": "Arzt",
            "start": {"dateTime": "2026-07-22T12:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2026-07-22T13:00:00", "timeZone": "UTC"},
        },
    )
    assert client.posts[1][1]["message"]["body"] == {"contentType": "Text", "content": "Hallo"}


def test_adapter_rejects_header_injection_and_invalid_calendar_bounds(tmp_path):
    client = _Client()
    bundle = build_external_action_connectors(
        tmp_path,
        env={PROVIDER_ENV: "google"},
        google_runtime_factory=_factory(client),
    )

    with pytest.raises(ValueError, match="subject is invalid"):
        bundle.mail.send_new_message({
            "recipients": ["a@example.test"],
            "subject": "Status\r\nBcc: hidden@example.test",
            "body": "Hallo",
        })
    with pytest.raises(ValueError, match="recipients are invalid"):
        bundle.mail.send_new_message({
            "recipients": ["a@example.test, hidden@example.test"],
            "subject": "Status",
            "body": "Hallo",
        })
    with pytest.raises(ValueError, match="start before end"):
        bundle.calendar.create_event({
            "title": "Arzt",
            "start": "2026-07-22T15:00:00+02:00",
            "end": "2026-07-22T14:00:00+02:00",
        })
    assert client.posts == []


def test_google_adapter_executes_through_persistent_native_approval(tmp_path):
    client = _Client()
    bundle = build_external_action_connectors(
        tmp_path,
        env={PROVIDER_ENV: "google"},
        google_runtime_factory=_factory(client),
    )
    bus = NativeActionBus(
        tmp_path,
        workspace_id="alpha",
        calendar_service=CalendarService(bundle.calendar),
        mail_assistant=MailAssistant(connector=bundle.mail),
    )
    proposal = bus.submit("sende mail", {"recipient": "a@example.test", "body": "Hallo"})

    bus.submit("freigabe genehmigen", {"approval": proposal["approval_id"]})
    result = bus.confirm()

    assert result["status"] == "executed"
    assert bus.approvals.get(proposal["approval_id"])["status"] == "completed"
    assert len(client.posts) == 1

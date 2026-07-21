from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass
from datetime import timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Callable, Mapping

from secondbrain.calendar_assistant.models import parse_dt
from secondbrain.connectors.google.config import GoogleConfigError
from secondbrain.connectors.google.runtime import GoogleRuntime
from secondbrain.connectors.microsoft.config import GraphConfigError
from secondbrain.connectors.microsoft.runtime import M365Runtime
from secondbrain.env_loader import load_env_file

PROVIDER_ENV = "SECONDBRAIN_EXTERNAL_ACTION_PROVIDER"
_DISABLED_PROVIDERS = {"", "disabled", "none", "off"}
_PROVIDER_ALIASES = {"google": "google", "m365": "m365", "microsoft": "m365"}
_GOOGLE_CALENDAR_ENDPOINT = "calendar/v3/calendars/primary/events"
_GOOGLE_MAIL_ENDPOINT = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
_MAILBOX = re.compile(r"^[^@\s,;<>]+@[^@\s,;<>]+$")


@dataclass(frozen=True)
class ExternalActionConnectors:
    provider: str = "disabled"
    configured: bool = False
    authenticated: bool = False
    calendar: Any | None = None
    mail: Any | None = None
    reason: str = "disabled"

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "configured": self.configured,
            "authenticated": self.authenticated,
            "calendar_write": self.calendar is not None,
            "mail_write": self.mail is not None,
            "reason": self.reason,
        }


class GoogleCalendarActionConnector:
    def __init__(self, client: Any) -> None:
        self.client = client

    def create_event(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        title, start, end = _calendar_values(payload)
        response = self.client.post(
            _GOOGLE_CALENDAR_ENDPOINT,
            {
                "summary": title,
                "start": {"dateTime": start},
                "end": {"dateTime": end},
            },
        )
        return _safe_result(response, provider="google")


class GoogleMailActionConnector:
    def __init__(self, client: Any) -> None:
        self.client = client

    def send_new_message(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        recipients, subject, body = _mail_values(payload)
        message = EmailMessage()
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message.set_content(body)
        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        response = self.client.post(_GOOGLE_MAIL_ENDPOINT, {"raw": encoded})
        return _safe_result(response, provider="google")


class M365CalendarActionConnector:
    def __init__(self, client: Any) -> None:
        self.client = client

    def create_event(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        title, start, end = _calendar_values(payload)
        response = self.client.post(
            "me/events",
            {
                "subject": title,
                "start": {"dateTime": _graph_datetime(start), "timeZone": "UTC"},
                "end": {"dateTime": _graph_datetime(end), "timeZone": "UTC"},
            },
        )
        return _safe_result(response, provider="m365")


class M365MailActionConnector:
    def __init__(self, client: Any) -> None:
        self.client = client

    def send_new_message(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        recipients, subject, body = _mail_values(payload)
        response = self.client.post(
            "me/sendMail",
            {
                "message": {
                    "subject": subject,
                    "body": {"contentType": "Text", "content": body},
                    "toRecipients": [
                        {"emailAddress": {"address": recipient}}
                        for recipient in recipients
                    ],
                },
                "saveToSentItems": True,
            },
        )
        return _safe_result(response, provider="m365")


def build_external_action_connectors(
    project_root: str | Path,
    *,
    env: Mapping[str, str] | None = None,
    google_runtime_factory: Callable[..., Any] = GoogleRuntime,
    m365_runtime_factory: Callable[..., Any] = M365Runtime,
) -> ExternalActionConnectors:
    root = Path(project_root).resolve()
    if env is None:
        load_env_file(root)
        source: Mapping[str, str] = os.environ
    else:
        source = env
    requested = str(source.get(PROVIDER_ENV) or "").strip().casefold()
    if requested in _DISABLED_PROVIDERS:
        return ExternalActionConnectors()
    provider = _PROVIDER_ALIASES.get(requested)
    if provider is None:
        return ExternalActionConnectors(provider="unsupported", reason="unsupported_provider")

    try:
        runtime = (
            google_runtime_factory(root, env=dict(source))
            if provider == "google"
            else m365_runtime_factory(root, env=dict(source))
        )
    except (GoogleConfigError, GraphConfigError):
        return ExternalActionConnectors(provider=provider, reason="configuration_error")
    except Exception:  # noqa: BLE001 - desktop startup must remain available
        return ExternalActionConnectors(provider=provider, reason="initialization_failed")

    try:
        authenticated = bool(runtime.auth.is_authenticated())
    except Exception:  # noqa: BLE001 - corrupt token state must not block desktop startup
        return ExternalActionConnectors(
            provider=provider,
            configured=True,
            reason="authentication_status_unavailable",
        )
    if not authenticated:
        return ExternalActionConnectors(
            provider=provider,
            configured=True,
            reason="authentication_required",
        )
    calendar, mail = (
        (GoogleCalendarActionConnector(runtime.client), GoogleMailActionConnector(runtime.client))
        if provider == "google"
        else (M365CalendarActionConnector(runtime.client), M365MailActionConnector(runtime.client))
    )
    return ExternalActionConnectors(
        provider=provider,
        configured=True,
        authenticated=True,
        calendar=calendar,
        mail=mail,
        reason="ready",
    )


def _calendar_values(payload: Mapping[str, Any]) -> tuple[str, str, str]:
    title = _required_text(payload, "title")
    start = _required_text(payload, "start")
    end = _required_text(payload, "end")
    start_at = parse_dt(start)
    end_at = parse_dt(end)
    if (
        start_at is None
        or end_at is None
        or start_at.tzinfo is None
        or end_at.tzinfo is None
        or end_at <= start_at
    ):
        raise ValueError("calendar payload requires timezone-aware start before end")
    return title, start, end


def _mail_values(payload: Mapping[str, Any]) -> tuple[list[str], str, str]:
    raw_recipients = payload.get("recipients")
    if not isinstance(raw_recipients, (list, tuple)) or not raw_recipients:
        raise ValueError("mail payload requires recipients")
    recipients = [str(value).strip() for value in raw_recipients]
    if any(not _MAILBOX.fullmatch(value) for value in recipients):
        raise ValueError("mail recipients are invalid")
    subject = str(payload.get("subject") or "")
    if "\r" in subject or "\n" in subject:
        raise ValueError("mail subject is invalid")
    body = _required_text(payload, "body")
    return recipients, subject, body


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise ValueError(f"external action payload requires {key}")
    return value


def _graph_datetime(value: str) -> str:
    parsed = parse_dt(value)
    if parsed is None or parsed.tzinfo is None:
        raise ValueError("Graph calendar time must include a timezone")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


def _safe_result(response: Any, *, provider: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except Exception:  # noqa: BLE001 - successful empty provider responses are valid
        payload = {}
    external_id = str(payload.get("id") or "") if isinstance(payload, Mapping) else ""
    return {
        "provider": provider,
        "external_id": external_id,
        "http_status": int(getattr(response, "status", 0)),
    }

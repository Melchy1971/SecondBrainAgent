"""v30.4 - webhook receiver."""

from __future__ import annotations

import hmac
import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class WebhookEvent:
    provider: str
    event_type: str
    payload: dict


class WebhookReceiver:
    def verify_github_signature(self, body: bytes, signature: str, secret: str) -> bool:
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        expected = f"sha256={digest}"
        return hmac.compare_digest(expected, signature)

    def receive(self, provider: str, headers: dict, payload: dict) -> WebhookEvent:
        event_type = headers.get("X-GitHub-Event") or headers.get("event_type") or "unknown"
        return WebhookEvent(provider=provider, event_type=event_type, payload=payload)

"""Google Workspace configuration (loaded from environment / .env). No secrets invented."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEVICECODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE_URL = "https://www.googleapis.com"

DEFAULT_SCOPES: tuple[str, ...] = (
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/tasks",
)


class GoogleConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class GoogleConfig:
    client_id: str
    client_secret: str
    scopes: tuple[str, ...] = DEFAULT_SCOPES
    api_base_url: str = API_BASE_URL
    devicecode_url: str = DEVICECODE_URL
    token_url: str = TOKEN_URL
    token_store_path: str = "runtime/connectors/google_tokens.json"
    cursor_store_path: str = "runtime/connectors/google_cursors.json"
    approval_store_path: str = "runtime/connectors/google_approvals.json"

    def scope_string(self) -> str:
        return " ".join(self.scopes)

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "GoogleConfig":
        source = os.environ if env is None else env
        client_id = (source.get("GOOGLE_CLIENT_ID") or "").strip()
        client_secret = (source.get("GOOGLE_CLIENT_SECRET") or "").strip()
        if not client_id or not client_secret:
            raise GoogleConfigError(
                "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set. Create an OAuth 2.0 client "
                "(type: TV and Limited Input / Installed app) in Google Cloud Console, enable "
                "Gmail/Calendar/Drive/People/Tasks APIs, and set both in .env. "
                "See docs/releases/v30_79_google_workspace.md."
            )
        raw = (source.get("GOOGLE_SCOPES") or "").strip()
        scopes = tuple(s for s in raw.split() if s) if raw else DEFAULT_SCOPES
        return cls(client_id=client_id, client_secret=client_secret, scopes=scopes)

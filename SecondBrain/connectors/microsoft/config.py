"""M365 Graph configuration (loaded from environment / .env).

No client_id is ever invented. If required values are missing the loader raises
GraphConfigError with an explicit message and the exact .env keys to set.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
LOGIN_BASE_URL = "https://login.microsoftonline.com"

# Per-resource delegated scopes (write scope chosen: all resources writable).
DEFAULT_SCOPES: tuple[str, ...] = (
    "offline_access",
    "User.Read",
    "Mail.ReadWrite",
    "Mail.Send",
    "Calendars.ReadWrite",
    "Contacts.ReadWrite",
    "Files.ReadWrite",
    "Tasks.ReadWrite",       # Microsoft To Do
    "Notes.ReadWrite",       # OneNote
    "Chat.ReadWrite",        # Teams chat messages
    "ChannelMessage.Send",   # Teams channel messages
)


class GraphConfigError(RuntimeError):
    """Raised when mandatory Graph configuration is missing or invalid."""


@dataclass(frozen=True)
class GraphConfig:
    client_id: str
    tenant_id: str = "common"
    scopes: tuple[str, ...] = DEFAULT_SCOPES
    graph_base_url: str = GRAPH_BASE_URL
    login_base_url: str = LOGIN_BASE_URL
    token_store_path: str = "runtime/connectors/m365_tokens.json"
    cursor_store_path: str = "runtime/connectors/m365_cursors.json"
    approval_store_path: str = "runtime/connectors/m365_approvals.json"

    @property
    def devicecode_url(self) -> str:
        return f"{self.login_base_url}/{self.tenant_id}/oauth2/v2.0/devicecode"

    @property
    def token_url(self) -> str:
        return f"{self.login_base_url}/{self.tenant_id}/oauth2/v2.0/token"

    def scope_string(self) -> str:
        return " ".join(self.scopes)

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "GraphConfig":
        source = os.environ if env is None else env
        client_id = (source.get("M365_CLIENT_ID") or "").strip()
        if not client_id:
            raise GraphConfigError(
                "M365_CLIENT_ID is not set. Register an Azure AD app (public client, "
                "'Allow public client flows' = Yes) and set M365_CLIENT_ID (and optionally "
                "M365_TENANT_ID) in .env. See docs/releases/v30_78_m365_graph.md."
            )
        tenant_id = (source.get("M365_TENANT_ID") or "common").strip() or "common"
        raw_scopes = (source.get("M365_SCOPES") or "").strip()
        scopes = tuple(s for s in raw_scopes.split() if s) if raw_scopes else DEFAULT_SCOPES
        return cls(client_id=client_id, tenant_id=tenant_id, scopes=scopes)

"""GitHub connector configuration (PAT or device-flow OAuth)."""

from __future__ import annotations

import os
from dataclasses import dataclass

API_BASE = "https://api.github.com"
DEVICE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"


class GitHubConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubConfig:
    token: str = ""
    client_id: str = ""
    scopes: tuple[str, ...] = ("repo", "read:user")
    api_base: str = API_BASE
    token_store_path: str = "runtime/connectors/github_tokens.json"

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "GitHubConfig":
        src = os.environ if env is None else env
        token = (src.get("GITHUB_TOKEN") or "").strip()
        client_id = (src.get("GITHUB_CLIENT_ID") or "").strip()
        if not token and not client_id:
            raise GitHubConfigError(
                "Set GITHUB_TOKEN (personal access token) or GITHUB_CLIENT_ID (device flow).")
        return cls(token=token, client_id=client_id)

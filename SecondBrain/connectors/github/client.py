"""Minimal GitHub REST client with retry (uses the scaffold transport)."""

from __future__ import annotations

import json
import time
from typing import Any, Callable

from secondbrain.connectors.retry_backoff import ConnectorRetryBackoff
from secondbrain.connectors.scaffold.transport import Transport, UrllibTransport
from secondbrain.connectors.github.config import GitHubConfig


class GitHubApiError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"GitHub {status}: {message}")
        self.status = status


class GitHubClient:
    def __init__(self, config: GitHubConfig, token_provider, *, transport: Transport | None = None,
                 retry: ConnectorRetryBackoff | None = None, sleeper: Callable[[float], None] = time.sleep,
                 max_retries: int = 4) -> None:
        self.config = config
        self.token_provider = token_provider
        self.transport = transport or UrllibTransport()
        self.retry = retry or ConnectorRetryBackoff()
        self.sleeper = sleeper
        self.max_retries = max_retries

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token_provider.access_token()}",
                "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

    def request(self, method: str, path: str, *, params=None, json_body=None) -> Any:
        url = path if path.startswith("http") else f"{self.config.api_base}/{path.lstrip('/')}"
        if params:
            import urllib.parse
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        body = json.dumps(json_body).encode("utf-8") if json_body is not None else None
        headers = self._headers()
        if body is not None:
            headers["Content-Type"] = "application/json"
        attempt = 0
        while True:
            resp = self.transport.request(method, url, headers=headers, body=body)
            if 200 <= resp.status < 300:
                return resp.json() if resp.body else {}
            if (resp.status == 429 or resp.status >= 500) and attempt < self.max_retries:
                self.sleeper(self.retry.next_delay(attempt)); attempt += 1; continue
            raise GitHubApiError(resp.status, _err(resp))

    def get(self, path, *, params=None):
        return self.request("GET", path, params=params)

    def post(self, path, json_body):
        return self.request("POST", path, json_body=json_body)


def _err(resp) -> str:
    try:
        return resp.json().get("message", "request failed")
    except Exception:
        return "request failed"

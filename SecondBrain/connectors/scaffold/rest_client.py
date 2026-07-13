"""Generic authenticated REST client: retry/backoff, 401 re-auth, configurable paging."""

from __future__ import annotations

import json
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Callable

from secondbrain.connectors.retry_backoff import ConnectorRetryBackoff
from secondbrain.connectors.scaffold.transport import HttpResponse, Transport, UrllibTransport
from secondbrain.connectors.scaffold.oauth2 import OAuth2Authenticator


@dataclass(frozen=True)
class PagingConfig:
    items_key: str = "value"                 # Graph: value ; Google: items
    next_key: str = "@odata.nextLink"        # Graph nextLink ; Google: nextPageToken
    delta_key: str = "@odata.deltaLink"      # Graph deltaLink ; Google: nextSyncToken
    next_is_url: bool = True                 # Graph next is a full URL ; Google is a token
    next_param: str = "$skiptoken"           # used when next_is_url is False
    top_param: str = "$top"


GRAPH_PAGING = PagingConfig()
GOOGLE_PAGING = PagingConfig(items_key="items", next_key="nextPageToken",
                             delta_key="nextSyncToken", next_is_url=False,
                             next_param="pageToken", top_param="maxResults")


class RestApiError(RuntimeError):
    def __init__(self, status: int, message: str, payload: Any = None) -> None:
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.payload = payload


class RestClient:
    def __init__(
        self,
        base_url: str,
        auth: OAuth2Authenticator,
        *,
        transport: Transport | None = None,
        paging: PagingConfig | None = None,
        retry: ConnectorRetryBackoff | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        max_retries: int = 5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.transport = transport or auth.transport or UrllibTransport()
        self.paging = paging or GRAPH_PAGING
        self.retry = retry or ConnectorRetryBackoff()
        self.sleeper = sleeper
        self.max_retries = max_retries

    def _abs(self, path_or_url: str, params: dict[str, Any] | None = None) -> str:
        url = path_or_url if path_or_url.startswith("http") else f"{self.base_url}/{path_or_url.lstrip('/')}"
        if params:
            sep = "&" if "?" in url else "?"
            url = url + sep + urllib.parse.urlencode(params)
        return url

    def request(self, method, path_or_url, *, params=None, json_body=None, raw_body=None, headers=None) -> HttpResponse:
        url = self._abs(path_or_url, params)
        if raw_body is not None:
            body = raw_body
        elif json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
        else:
            body = None
        reauthed = False
        attempt = 0
        while True:
            base_headers = {"Authorization": f"Bearer {self.auth.access_token()}", "Accept": "application/json"}
            if body is not None and raw_body is None:
                base_headers["Content-Type"] = "application/json"
            if headers:
                base_headers.update(headers)
            resp = self.transport.request(method, url, headers=base_headers, body=body)
            if 200 <= resp.status < 300:
                return resp
            if resp.status == 401 and not reauthed:
                reauthed = True
                token = self.auth.token_repo.load_all().get(self.auth.provider) or {}
                if token.get("refresh_token"):
                    self.auth.refresh(token["refresh_token"])
                continue
            if resp.status == 429 or 500 <= resp.status < 600:
                if attempt >= self.max_retries:
                    raise RestApiError(resp.status, self._err(resp), self._safe_json(resp))
                delay = self._retry_after(resp) or self.retry.next_delay(attempt)
                self.sleeper(delay)
                attempt += 1
                continue
            raise RestApiError(resp.status, self._err(resp), self._safe_json(resp))

    def get(self, path, *, params=None, headers=None) -> Any:
        return self.request("GET", path, params=params, headers=headers).json()

    def post(self, path, json_body, *, headers=None) -> HttpResponse:
        return self.request("POST", path, json_body=json_body, headers=headers)

    def patch(self, path, json_body, *, headers=None) -> HttpResponse:
        return self.request("PATCH", path, json_body=json_body, headers=headers)

    def delete(self, path, *, headers=None) -> HttpResponse:
        return self.request("DELETE", path, headers=headers)

    def follow_collection(self, path_or_url, *, params=None, delta=False, prefer=None, max_pages=50, paging=None):
        """Follow pages per PagingConfig. Returns (items, cursor).

        cursor is the delta token/link when delta=True, else None.
        """
        pg = paging or self.paging
        headers = {"Prefer": prefer} if prefer else None
        items: list[dict] = []
        delta_cursor: str | None = None
        url = path_or_url
        current = dict(params) if params else None
        for _ in range(max_pages):
            payload = self.request("GET", url, params=current, headers=headers).json()
            items.extend(payload.get(pg.items_key, []))
            delta_cursor = payload.get(pg.delta_key) or delta_cursor
            nxt = payload.get(pg.next_key)
            if nxt:
                if pg.next_is_url:
                    url, current = nxt, None
                else:
                    current = {**(current or {}), pg.next_param: nxt}
                continue
            break
        return items, (delta_cursor if delta else None)

    @staticmethod
    def _retry_after(resp: HttpResponse) -> float | None:
        raw = resp.header("Retry-After")
        if raw is None:
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    @staticmethod
    def _safe_json(resp: HttpResponse) -> Any:
        try:
            return resp.json()
        except Exception:
            return None

    @staticmethod
    def _err(resp: HttpResponse) -> str:
        data = RestClient._safe_json(resp)
        if isinstance(data, dict) and isinstance(data.get("error"), dict):
            return data["error"].get("message", "request failed")
        return "request failed"

"""v30.0 minimal JSON HTTP transport.

Uses stdlib urllib to keep the provider layer dependency-light. Tests can inject
FakeTransport objects with the same post_json signature.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from secondbrain.providers.base.provider_exception import ProviderError


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    data: dict[str, Any]


class JsonHttpTransport:
    def post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None, timeout: float = 60.0) -> HttpResponse:
        body = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(url, data=body, headers={"Content-Type": "application/json", **(headers or {})}, method="POST")
        try:
            with urlrequest.urlopen(req, timeout=timeout) as resp:  # nosec - user-configured provider URLs
                raw = resp.read().decode("utf-8")
                return HttpResponse(status_code=resp.status, data=json.loads(raw or "{}"))
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise ProviderError("http", raw or exc.reason, retryable=exc.code in {429, 500, 502, 503, 504}, status_code=exc.code) from exc
        except URLError as exc:
            raise ProviderError("http", str(exc.reason), retryable=True) from exc

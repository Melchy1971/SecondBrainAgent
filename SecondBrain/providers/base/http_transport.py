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

from secondbrain.providers.base.provider_exception import ProviderError, ProviderRateLimitError, ProviderTimeoutError


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
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ProviderError("http", "invalid_response", retryable=False)
                return HttpResponse(status_code=resp.status, data=data)
        except HTTPError as exc:
            code = "rate_limit" if exc.code == 429 else "http_error"
            if exc.code == 429:
                try:
                    detail = json.loads(exc.read(65536)).get("error", {})
                    if isinstance(detail, dict):
                        # Only known machine codes survive; never retain response text.
                        for value in (detail.get("code"), detail.get("type")):
                            if value in ("insufficient_quota", "rate_limit_exceeded"):
                                code = value
                                break
                except (ValueError, AttributeError, OSError):
                    pass
            error = ProviderRateLimitError if exc.code == 429 else ProviderError
            raise error("http", code, error_code=code,
                        retryable=exc.code in {429, 500, 502, 503, 504} and code != "insufficient_quota", status_code=exc.code) from None
        except TimeoutError:
            raise ProviderTimeoutError("http", "timeout", retryable=True) from None
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise ProviderTimeoutError("http", "timeout", retryable=True) from None
            raise ProviderError("http", "connection_failed", retryable=True) from None
        except (ValueError, UnicodeError):
            raise ProviderError("http", "invalid_response", retryable=False) from None

"""HTTP transport boundary for Graph.

Real network access uses stdlib urllib. Tests inject FakeTransport so nothing
touches the network. Both implement the Transport protocol.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    body: bytes

    def json(self) -> Any:
        if not self.body:
            return {}
        return json.loads(self.body.decode("utf-8"))

    def header(self, name: str, default: str | None = None) -> str | None:
        lname = name.lower()
        for key, value in self.headers.items():
            if key.lower() == lname:
                return value
        return default


class Transport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ) -> HttpResponse: ...


class UrllibTransport:
    """Stdlib transport. Never used in tests."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def request(self, method, url, *, headers=None, body=None) -> HttpResponse:
        req = urllib.request.Request(url=url, method=method.upper(), data=body)
        for key, value in (headers or {}).items():
            req.add_header(key, value)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return HttpResponse(
                    status=resp.status,
                    headers={k: v for k, v in resp.headers.items()},
                    body=resp.read(),
                )
        except urllib.error.HTTPError as exc:  # non-2xx still carries a body we need
            return HttpResponse(
                status=exc.code,
                headers={k: v for k, v in (exc.headers or {}).items()},
                body=exc.read() or b"",
            )


Route = Callable[[str, str, dict[str, str], bytes | None], HttpResponse]


class FakeTransport:
    """Deterministic transport for tests.

    Register handlers by (method, url-substring). Records every call.
    """

    def __init__(self) -> None:
        self._routes: list[tuple[str, str, Route]] = []
        self.calls: list[dict[str, Any]] = []

    def on(self, method: str, url_contains: str, handler: Route) -> "FakeTransport":
        self._routes.append((method.upper(), url_contains, handler))
        return self

    def json_response(self, status: int, payload: Any, headers: dict[str, str] | None = None) -> HttpResponse:
        return HttpResponse(status, headers or {"Content-Type": "application/json"},
                            json.dumps(payload).encode("utf-8"))

    def request(self, method, url, *, headers=None, body=None) -> HttpResponse:
        self.calls.append({"method": method.upper(), "url": url, "headers": dict(headers or {}), "body": body})
        for rmethod, needle, handler in self._routes:
            if rmethod == method.upper() and needle in url:
                return handler(url, method.upper(), dict(headers or {}), body)
        return HttpResponse(404, {}, json.dumps({"error": {"code": "no_route", "message": url}}).encode("utf-8"))

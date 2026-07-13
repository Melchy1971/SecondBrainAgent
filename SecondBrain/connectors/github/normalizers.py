"""GitHub payloads -> ConnectorItem."""

from __future__ import annotations

from typing import Any, Mapping

from secondbrain.connectors.adapter_contract import ConnectorItem, parse_datetime


def issue(p: Mapping[str, Any], *, repo: str = "") -> ConnectorItem | None:
    if "pull_request" in p:            # skip PRs surfaced via the issues API
        return None
    return ConnectorItem(
        external_id=str(p.get("id") or p.get("number")),
        source="github_issues",
        title=str(p.get("title") or f"#{p.get('number')}"),
        content=str(p.get("body") or p.get("title") or ""),
        updated_at=parse_datetime(p.get("updated_at") or 0),
        uri=p.get("html_url"),
        metadata={"number": p.get("number"), "state": p.get("state"), "repo": repo,
                  "labels": [l.get("name") for l in (p.get("labels") or []) if isinstance(l, dict)]})


def commit(p: Mapping[str, Any], *, repo: str = "") -> ConnectorItem | None:
    c = p.get("commit") or {}
    return ConnectorItem(
        external_id=str(p.get("sha", "")),
        source="github_commits",
        title=str((c.get("message") or "").splitlines()[0] if c.get("message") else p.get("sha", "")),
        content=str(c.get("message") or ""),
        updated_at=parse_datetime((c.get("author") or {}).get("date") or 0),
        uri=p.get("html_url"),
        metadata={"repo": repo, "author": (c.get("author") or {}).get("name")})

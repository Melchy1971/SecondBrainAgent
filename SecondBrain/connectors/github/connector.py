"""GitHub issues connector (incremental via `since` watermark) + approval-gated writer."""

from __future__ import annotations

from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.scaffold.writer import ApprovalGatedWriter
from secondbrain.connectors.github import normalizers


class GitHubIssuesConnector:
    name = "github_issues"

    def __init__(self, client, owner: str, repo: str) -> None:
        self.client = client
        self.owner = owner
        self.repo = repo

    def fetch_since(self, cursor: str | None, limit: int) -> FetchBatch:
        params = {"state": "all", "sort": "updated", "direction": "asc", "per_page": limit}
        if cursor:
            params["since"] = cursor
        rows = self.client.get(f"repos/{self.owner}/{self.repo}/issues", params=params)
        items, newest = [], cursor
        for row in rows if isinstance(rows, list) else []:
            ci = normalizers.issue(row, repo=f"{self.owner}/{self.repo}")
            if ci is None:
                continue
            updated = row.get("updated_at")
            if newest is None or (updated and updated > newest):
                newest = updated
            items.append(FetchedItem(id=ci.external_id, payload=ci, cursor=updated))
        return FetchBatch(items=items, next_cursor=newest, has_more=False)


def connector(client, owner: str, repo: str) -> GitHubIssuesConnector:
    return GitHubIssuesConnector(client, owner, repo)


class GitHubWriter(ApprovalGatedWriter):
    resource = "github"

    def create_issue(self, owner: str, repo: str, title: str, body: str = ""):
        payload = {"title": title, "body": body}
        return self._guarded("github.create_issue", "POST", f"{owner}/{repo}", payload,
                             lambda: self.client.post(f"repos/{owner}/{repo}/issues", payload))

    def comment(self, owner: str, repo: str, number: int, body: str):
        payload = {"body": body}
        return self._guarded("github.comment", "POST", f"{owner}/{repo}#{number}", payload,
                             lambda: self.client.post(f"repos/{owner}/{repo}/issues/{number}/comments", payload))

"""v30.4 - GitHub sync service."""

from __future__ import annotations

from secondbrain.connectors.sync_models import SyncItem, SyncResult


class GitHubSyncService:
    connector = "github"

    def __init__(self, client, checkpoint_store=None):
        self.client = client
        self.checkpoint_store = checkpoint_store

    def sync_repository(self, owner: str, repo: str, since: str | None = None) -> SyncResult:
        issues = self.client.list_issues(owner, repo, since=since)
        prs = self.client.list_pull_requests(owner, repo, since=since)
        commits = self.client.list_commits(owner, repo, since=since)

        items = []
        for kind, rows in [("issue", issues), ("pull_request", prs), ("commit", commits)]:
            for row in rows:
                items.append(SyncItem(
                    external_id=str(row.get("id") or row.get("sha")),
                    source=self.connector,
                    kind=kind,
                    payload=row,
                ))

        cursor = items[-1].external_id if items else since
        if self.checkpoint_store and cursor:
            self.checkpoint_store.save_checkpoint(f"{self.connector}:{owner}/{repo}", cursor)
        return SyncResult(self.connector, "PASS", len(items), cursor)

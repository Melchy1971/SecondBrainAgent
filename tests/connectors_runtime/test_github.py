import pytest
from secondbrain.connectors.scaffold.transport import FakeTransport
from secondbrain.connectors.scaffold.approval import ApprovalGate, ApprovalRequired, InMemoryApprovalStore
from secondbrain.connectors.github.config import GitHubConfig
from secondbrain.connectors.github.auth import PatTokenProvider
from secondbrain.connectors.github.client import GitHubClient
from secondbrain.connectors.github.connector import GitHubIssuesConnector, GitHubWriter


def _client(tp):
    return GitHubClient(GitHubConfig(token="pat"), PatTokenProvider("pat"), transport=tp, sleeper=lambda _s: None)


def test_issues_incremental_skips_pull_requests():
    tp = FakeTransport()
    tp.on("GET", "/issues", lambda u, m, h, b: tp.json_response(200, [
        {"id": 1, "number": 7, "title": "Bug", "body": "x", "updated_at": "2026-01-02T00:00:00Z", "labels": []},
        {"id": 2, "number": 8, "title": "PR", "pull_request": {}, "updated_at": "2026-01-03T00:00:00Z"},
    ]))
    conn = GitHubIssuesConnector(_client(tp), "me", "repo")
    batch = conn.fetch_since(None, 50)
    assert [i.payload.title for i in batch.items] == ["Bug"]         # PR skipped
    assert batch.next_cursor == "2026-01-02T00:00:00Z"


def test_write_is_approval_gated():
    tp = FakeTransport()
    tp.on("POST", "/issues", lambda u, m, h, b: tp.json_response(201, {"number": 9}))
    writer = GitHubWriter(_client(tp), ApprovalGate(InMemoryApprovalStore()))
    with pytest.raises(ApprovalRequired):
        writer.create_issue("me", "repo", "New", "body")
    assert not any("/issues" in c["url"] and c["method"] == "POST" for c in tp.calls)


def test_client_retries_5xx():
    tp = FakeTransport()
    state = {"n": 0}
    def handler(u, m, h, b):
        state["n"] += 1
        return tp.json_response(200, []) if state["n"] > 1 else tp.json_response(503, {"message": "down"})
    tp.on("GET", "/issues", handler)
    _client(tp).get("repos/me/repo/issues")
    assert state["n"] == 2

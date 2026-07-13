"""Tests for the productive connector runtime (Task 3)."""

from __future__ import annotations

from pathlib import Path


from secondbrain.connector_runtime import (
    AuthError,
    CallableReindex,
    ConnectorRuntime,
    GmailConnector,
    JobState,
    LocalFolderConnector,
    PermanentError,
    RateLimitError,
    RetryPolicy,
    SourceStatus,
    TransientError,
    VaultTokenProvider,
)
from secondbrain.vault import crypto
from secondbrain.vault.store import SecretVault

TOKEN = "ya29.SECRET-ACCESS-TOKEN-should-only-live-in-vault"
NOSLEEP = lambda _s: None  # noqa: E731


def _vault(tmp_path: Path) -> SecretVault:
    return SecretVault(tmp_path / "vault", env={"SECONDBRAIN_VAULT_KEY": crypto.b64e(bytes(range(32)))})


def _runtime(tmp_path: Path, **kw) -> ConnectorRuntime:
    return ConnectorRuntime(tmp_path / "rt", sleeper=NOSLEEP,
                            retry_policy=RetryPolicy(max_attempts=3, base_delay=0.0), **kw)


# --- fake network clients ------------------------------------------------------

class FakeGmailClient:
    def __init__(self, pages=None, raise_first=None):
        self.pages = pages or [{"messages": [
            {"id": "m1", "subject": "Hello", "from": "a@x.de", "snippet": "hi", "internalDate": "1000"},
        ], "next_cursor": "c1", "has_more": False}]
        self.raise_first = raise_first
        self.calls = 0

    def list_messages(self, token, cursor):
        self.calls += 1
        assert token == TOKEN  # runtime must supply the vault token
        if self.raise_first and self.calls == 1:
            raise self.raise_first
        return self.pages[min(self.calls - 1, len(self.pages) - 1)]


class AlwaysFailsClient:
    def __init__(self, exc):
        self.exc = exc

    def list_messages(self, token, cursor):
        raise self.exc


# --- local folder --------------------------------------------------------------

def test_local_folder_produces_documents_incrementally(tmp_path):
    src = tmp_path / "vault_notes"
    src.mkdir()
    (src / "a.md").write_text("first note", encoding="utf-8")
    rt = _runtime(tmp_path)
    rt.register("notes", LocalFolderConnector("notes", src))
    out1 = rt.sync("notes")
    assert out1.job.state == JobState.SUCCEEDED
    assert len(out1.documents) == 1
    assert out1.documents[0].kind == "file"

    # second sync without changes -> no new documents (incremental cursor)
    out2 = rt.sync("notes")
    assert len(out2.documents) == 0

    # add a file -> only the new one is produced
    (src / "b.txt").write_text("second note", encoding="utf-8")
    import os
    import time as _t
    os.utime(src / "b.txt", (_t.time() + 5, _t.time() + 5))
    out3 = rt.sync("notes")
    assert [d.external_id for d in out3.documents] == ["b.txt"]


# --- gmail with vault token ----------------------------------------------------

def test_gmail_sync_uses_vault_token_and_produces_documents(tmp_path):
    vault = _vault(tmp_path)
    tokens = VaultTokenProvider(vault)
    tokens.store_token("gmail-main", TOKEN, refresh_token="refresh-xyz")
    rt = _runtime(tmp_path, token_provider=tokens)
    rt.register("gmail-main", GmailConnector("gmail-main", FakeGmailClient()))
    out = rt.sync("gmail-main")
    assert out.job.state == JobState.SUCCEEDED
    assert out.documents[0].external_id == "m1"


def test_tokens_never_leave_the_vault(tmp_path):
    vault = _vault(tmp_path)
    tokens = VaultTokenProvider(vault)
    tokens.store_token("gmail-main", TOKEN)
    rt = _runtime(tmp_path, token_provider=tokens)
    rt.register("gmail-main", GmailConnector("gmail-main", FakeGmailClient()))
    rt.sync("gmail-main")
    for name in ("cursors.json", "jobs.jsonl", "audit.jsonl", "dead_letter.jsonl"):
        p = tmp_path / "rt" / name
        if p.exists():
            assert TOKEN not in p.read_text(encoding="utf-8")


def test_missing_token_fails_job(tmp_path):
    vault = _vault(tmp_path)
    rt = _runtime(tmp_path, token_provider=VaultTokenProvider(vault))
    rt.register("gmail-main", GmailConnector("gmail-main", FakeGmailClient()))
    out = rt.sync("gmail-main")
    assert out.job.state == JobState.FAILED
    assert out.status == SourceStatus.ERROR


# --- simulated API errors ------------------------------------------------------

def test_rate_limit_is_retried_then_succeeds(tmp_path):
    vault = _vault(tmp_path)
    tokens = VaultTokenProvider(vault)
    tokens.store_token("gmail-main", TOKEN)
    rt = _runtime(tmp_path, token_provider=tokens)
    client = FakeGmailClient(raise_first=RateLimitError(retry_after=0.0))
    rt.register("gmail-main", GmailConnector("gmail-main", client))
    out = rt.sync("gmail-main")
    assert client.calls == 2
    assert out.job.state == JobState.SUCCEEDED
    assert len(out.documents) == 1


def test_transient_exhausted_goes_partial_and_dead_letters(tmp_path):
    vault = _vault(tmp_path)
    tokens = VaultTokenProvider(vault)
    tokens.store_token("gmail-main", TOKEN)
    rt = _runtime(tmp_path, token_provider=tokens)
    rt.register("gmail-main", GmailConnector("gmail-main", AlwaysFailsClient(TransientError("500 upstream"))))
    out = rt.sync("gmail-main")
    assert out.job.state == JobState.PARTIAL
    assert rt.dead_letters.count() == 1
    assert out.dead_letters[0].attempts == 3


def test_permanent_error_fails_and_dead_letters(tmp_path):
    vault = _vault(tmp_path)
    tokens = VaultTokenProvider(vault)
    tokens.store_token("gmail-main", TOKEN)
    rt = _runtime(tmp_path, token_provider=tokens)
    rt.register("gmail-main", GmailConnector("gmail-main", AlwaysFailsClient(PermanentError("404 gone"))))
    out = rt.sync("gmail-main")
    assert out.job.state == JobState.FAILED
    assert rt.dead_letters.count() == 1
    assert out.status == SourceStatus.ERROR


def test_auth_error_during_fetch_fails(tmp_path):
    vault = _vault(tmp_path)
    tokens = VaultTokenProvider(vault)
    tokens.store_token("gmail-main", TOKEN)
    rt = _runtime(tmp_path, token_provider=tokens)
    rt.register("gmail-main", GmailConnector("gmail-main", AlwaysFailsClient(AuthError("401"))))
    out = rt.sync("gmail-main")
    assert out.job.state == JobState.FAILED


# --- status, reindex, lifecycle ------------------------------------------------

def test_source_status_transitions(tmp_path):
    src = tmp_path / "n"
    src.mkdir()
    (src / "a.md").write_text("x", encoding="utf-8")
    rt = _runtime(tmp_path)
    rt.register("notes", LocalFolderConnector("notes", src), freshness_seconds=3600)
    assert rt.status("notes")["status"] == SourceStatus.NEVER_SYNCED.value
    rt.sync("notes")
    assert rt.status("notes")["status"] == SourceStatus.FRESH.value


def test_reindex_hook_called_with_documents(tmp_path):
    src = tmp_path / "n"
    src.mkdir()
    (src / "a.md").write_text("x", encoding="utf-8")
    seen = {}
    rt = _runtime(tmp_path, reindex=CallableReindex(lambda docs: seen.update(n=len(docs)) or {"reindexed": len(docs)}))
    rt.register("notes", LocalFolderConnector("notes", src))
    rt.sync("notes")
    assert seen["n"] == 1


def test_job_lifecycle_is_persisted(tmp_path):
    src = tmp_path / "n"
    src.mkdir()
    (src / "a.md").write_text("x", encoding="utf-8")
    rt = _runtime(tmp_path)
    rt.register("notes", LocalFolderConnector("notes", src))
    rt.sync("notes")
    jobs = rt.jobs.entries()
    assert jobs and jobs[-1]["state"] == JobState.SUCCEEDED.value
    actions = {e["action"] for e in rt.audit.entries()}
    assert {"sync_started", "sync_completed"} <= actions

"""Productive connector runtime.

Turns connectors into real data sources: registry, OAuth via the Secret Vault,
incremental sync, source status (fresh/stale/error), import-job lifecycle,
retry/backoff, dead-letter queue, rate limiting, audit trail, and a RAG reindex
hook after each sync.
"""

from secondbrain.connector_runtime.center import ConnectorCenterController
from secondbrain.connector_runtime.connectors import (
    Connector,
    GitHubConnector,
    GmailConnector,
    GoogleCalendarConnector,
    GoogleDriveConnector,
    LocalFolderConnector,
)
from secondbrain.connector_runtime.models import (
    AuthError,
    ConnectorError,
    DeadLetter,
    Document,
    FetchPage,
    ImportJob,
    JobState,
    PermanentError,
    RateLimitError,
    SourceStatus,
    SyncOutcome,
    TransientError,
    compute_status,
)
from secondbrain.connector_runtime.oauth import VaultTokenProvider
from secondbrain.connector_runtime.resilience import (
    DeadLetterQueue,
    RateLimiter,
    RetryPolicy,
    run_with_retry,
)
from secondbrain.connector_runtime.runtime import (
    CallableReindex,
    ConnectorRegistry,
    ConnectorRuntime,
    NullReindex,
    ReindexHook,
)

__all__ = [
    "AuthError",
    "CallableReindex",
    "Connector",
    "ConnectorCenterController",
    "ConnectorError",
    "ConnectorRegistry",
    "ConnectorRuntime",
    "DeadLetter",
    "DeadLetterQueue",
    "Document",
    "FetchPage",
    "GitHubConnector",
    "GmailConnector",
    "GoogleCalendarConnector",
    "GoogleDriveConnector",
    "ImportJob",
    "JobState",
    "LocalFolderConnector",
    "NullReindex",
    "PermanentError",
    "RateLimitError",
    "RateLimiter",
    "ReindexHook",
    "RetryPolicy",
    "SourceStatus",
    "SyncOutcome",
    "TransientError",
    "VaultTokenProvider",
    "compute_status",
    "run_with_retry",
]

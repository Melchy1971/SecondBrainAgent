"""Microsoft 365 / Graph integration (v30.78).

Built on the existing connector runtime: ConnectorItem (adapter_contract),
IncrementalSyncRunner (incremental_runner), ConnectorImportBridge (import_bridge),
CursorStore (cursor_store), OAuth token persistence (token_repository).

Stdlib-only. All network I/O goes through an injectable Transport, so the whole
package is unit-testable offline with a fake transport.
"""

from secondbrain.connectors.microsoft.config import GraphConfig, GraphConfigError
from secondbrain.connectors.microsoft.graph_auth import (
    DeviceCodeStart,
    GraphAuthenticator,
    GraphAuthError,
)
from secondbrain.connectors.microsoft.graph_client import GraphClient, GraphApiError
from secondbrain.connectors.microsoft.approval import (
    ApprovalGate,
    ApprovalRequired,
    ApprovalRequest,
    JsonApprovalStore,
    InMemoryApprovalStore,
)

__all__ = [
    "GraphConfig",
    "GraphConfigError",
    "DeviceCodeStart",
    "GraphAuthenticator",
    "GraphAuthError",
    "GraphClient",
    "GraphApiError",
    "ApprovalGate",
    "ApprovalRequired",
    "ApprovalRequest",
    "JsonApprovalStore",
    "InMemoryApprovalStore",
]

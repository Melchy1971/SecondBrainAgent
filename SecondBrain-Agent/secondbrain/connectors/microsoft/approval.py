"""M365 approval gate (canonical implementation lives in the scaffold)."""
from secondbrain.connectors.scaffold.approval import (
    ApprovalRequired, ApprovalRequest, ApprovalStore,
    InMemoryApprovalStore, JsonApprovalStore, ApprovalGate,
)
__all__ = ["ApprovalRequired", "ApprovalRequest", "ApprovalStore",
           "InMemoryApprovalStore", "JsonApprovalStore", "ApprovalGate"]

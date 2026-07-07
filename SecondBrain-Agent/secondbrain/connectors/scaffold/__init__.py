"""Provider-agnostic connector scaffold (v30.79).

Generalizes the M365 pattern so every OAuth2 + delta-sync connector reuses the
same auth, REST, paging, approval, background-sync and CLI machinery. Stdlib-only;
all network I/O flows through an injectable Transport for offline testing.
"""
from secondbrain.connectors.scaffold.transport import (
    HttpResponse, Transport, UrllibTransport, FakeTransport,
)
from secondbrain.connectors.scaffold.approval import (
    ApprovalGate, ApprovalRequired, ApprovalRequest, JsonApprovalStore, InMemoryApprovalStore,
)
from secondbrain.connectors.scaffold.oauth2 import OAuth2Config, OAuth2Authenticator, DeviceCodeStart, OAuth2Error
from secondbrain.connectors.scaffold.rest_client import RestClient, RestApiError, PagingConfig
from secondbrain.connectors.scaffold.delta_connector import DeltaCollectionConnector, max_watermark
from secondbrain.connectors.scaffold.writer import ApprovalGatedWriter
from secondbrain.connectors.scaffold.sync import BackgroundSync
from secondbrain.connectors.scaffold.runtime_base import ConnectorRuntime

__all__ = [
    "HttpResponse", "Transport", "UrllibTransport", "FakeTransport",
    "ApprovalGate", "ApprovalRequired", "ApprovalRequest", "JsonApprovalStore", "InMemoryApprovalStore",
    "OAuth2Config", "OAuth2Authenticator", "DeviceCodeStart", "OAuth2Error",
    "RestClient", "RestApiError", "PagingConfig",
    "DeltaCollectionConnector", "max_watermark", "ApprovalGatedWriter",
    "BackgroundSync", "ConnectorRuntime",
]

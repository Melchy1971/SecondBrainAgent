"""Google Workspace runtime facade (google-login/sync/status/disconnect)."""

from __future__ import annotations

from pathlib import Path

from secondbrain.connectors.cursor_store import JsonCursorStore
from secondbrain.connectors.token_repository import TokenRepository
from secondbrain.connectors.import_bridge import ImportJobSink, InMemoryImportJobSink
from secondbrain.connectors.scaffold.transport import Transport, UrllibTransport
from secondbrain.connectors.scaffold.approval import ApprovalGate, JsonApprovalStore
from secondbrain.connectors.scaffold.runtime_base import ConnectorRuntime
from secondbrain.connectors.google.config import GoogleConfig
from secondbrain.connectors.google.auth import GoogleAuthenticator
from secondbrain.connectors.google.client import GoogleClient
from secondbrain.connectors.google.registry import build_connectors, build_writers, RESOURCE_NAMES


class GoogleRuntime(ConnectorRuntime):
    def __init__(self, project_root="." , *, transport: Transport | None = None,
                 config: GoogleConfig | None = None, auto_approve: bool = False,
                 sink: ImportJobSink | None = None, env: dict | None = None) -> None:
        self.project_root = Path(project_root)
        if config is None:
            try:
                from secondbrain.env_loader import load_env_file
                load_env_file()
            except Exception:
                pass
            config = GoogleConfig.from_env(env)
        self.config = config
        transport = transport or UrllibTransport()
        token_repo = TokenRepository(str(self._p(config.token_store_path)))
        auth = GoogleAuthenticator(config, transport=transport, token_repo=token_repo)
        client = GoogleClient(config, auth, transport=transport)
        cursor_store = JsonCursorStore(self._p(config.cursor_store_path))
        gate = ApprovalGate(JsonApprovalStore(self._p(config.approval_store_path)), auto_approve=auto_approve)
        super().__init__(provider="google", resource_names=RESOURCE_NAMES, auth=auth, client=client,
                         cursor_store=cursor_store, gate=gate, sink=sink or InMemoryImportJobSink(),
                         build_connectors=build_connectors, build_writers=build_writers, cursor_prefix="google")

    def _p(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else self.project_root / p

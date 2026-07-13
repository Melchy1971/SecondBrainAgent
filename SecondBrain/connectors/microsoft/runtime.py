"""M365 runtime facade used by the launcher (m365-login/sync/status/disconnect)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from secondbrain.connectors.cursor_store import JsonCursorStore
from secondbrain.connectors.sync_audit import SyncAudit
from secondbrain.connectors.token_repository import TokenRepository
from secondbrain.connectors.import_bridge import ImportJobSink, InMemoryImportJobSink
from secondbrain.connectors.microsoft.config import GraphConfig
from secondbrain.connectors.microsoft.transport import Transport, UrllibTransport
from secondbrain.connectors.microsoft.graph_auth import GraphAuthenticator
from secondbrain.connectors.microsoft.graph_client import GraphClient
from secondbrain.connectors.microsoft.approval import ApprovalGate, JsonApprovalStore
from secondbrain.connectors.microsoft.registry import build_connectors, build_writers, RESOURCE_NAMES
from secondbrain.connectors.microsoft.background_sync import M365BackgroundSync


class M365Runtime:
    def __init__(
        self,
        project_root: str | Path = ".",
        *,
        transport: Transport | None = None,
        config: GraphConfig | None = None,
        auto_approve: bool = False,
        sink: ImportJobSink | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        if config is None:
            try:
                from secondbrain.env_loader import load_env_file
                load_env_file()  # best effort: populate os.environ from .env
            except Exception:
                pass
            config = GraphConfig.from_env(env)  # raises GraphConfigError if unset
        self.config = config
        self.transport = transport or UrllibTransport()
        self.token_repo = TokenRepository(str(self._path(config.token_store_path)))
        self.auth = GraphAuthenticator(config, transport=self.transport, token_repo=self.token_repo)
        self.client = GraphClient(config, self.auth, transport=self.transport)
        self.cursor_store = JsonCursorStore(self._path(config.cursor_store_path))
        self.gate = ApprovalGate(JsonApprovalStore(self._path(config.approval_store_path)), auto_approve=auto_approve)
        self.sink = sink or InMemoryImportJobSink()
        self.audit = SyncAudit()

    def _path(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else self.project_root / p

    # ---- launcher operations ---------------------------------------------
    def login(self, *, printer: Callable[[str], None] | None = None, wait: bool = True,
              sleeper: Callable[[float], None] = time.sleep) -> dict[str, Any]:
        start = self.auth.begin_device_login()
        message = start.message or f"Open {start.verification_uri} and enter code {start.user_code}"
        if printer:
            printer(message)
        if not wait:
            return {"status": "pending", "instructions": start.to_public_dict()}
        self.auth.complete_device_login(start, sleeper=sleeper)
        return {"status": "ok", **self.auth.status()}

    def sync(self, resources=None) -> dict[str, Any]:
        connectors = build_connectors(self.client, resources)
        bg = M365BackgroundSync(connectors, sink=self.sink, cursor_store=self.cursor_store, audit=self.audit)
        return {"status": "ok", "results": bg.run_once()}

    def status(self) -> dict[str, Any]:
        st = self.auth.status()
        st["resources"] = list(RESOURCE_NAMES)
        st["pending_approvals"] = len(self.gate.pending())
        cursors = {}
        for name in RESOURCE_NAMES:
            cur = self.cursor_store.get(f"m365_{name}")
            cursors[name] = cur.value if cur else None
        st["cursors"] = cursors
        return st

    def disconnect(self, *, purge_cursors: bool = True) -> dict[str, Any]:
        was_auth = self.auth.forget()
        if purge_cursors:
            for name in RESOURCE_NAMES:
                self.cursor_store.delete(f"m365_{name}")
        return {"status": "ok", "was_authenticated": was_auth}

    # ---- writers + approvals ---------------------------------------------
    def writers(self) -> dict[str, Any]:
        return build_writers(self.client, self.gate)

    def pending_approvals(self) -> list[dict]:
        return [r.to_dict() for r in self.gate.pending()]

    def approve(self, request_id: str) -> dict[str, Any]:
        r = self.gate.approve(request_id)
        return {"status": "ok" if r else "not_found", "request": r.to_dict() if r else None}

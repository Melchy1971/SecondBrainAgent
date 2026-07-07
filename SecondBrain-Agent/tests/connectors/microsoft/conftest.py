import json
import pytest

from secondbrain.connectors.microsoft.config import GraphConfig
from secondbrain.connectors.microsoft.transport import FakeTransport
from secondbrain.connectors.microsoft.graph_auth import GraphAuthenticator
from secondbrain.connectors.microsoft.graph_client import GraphClient


@pytest.fixture
def config(tmp_path):
    return GraphConfig(
        client_id="test-client",
        tenant_id="common",
        token_store_path=str(tmp_path / "tok.json"),
        cursor_store_path=str(tmp_path / "cur.json"),
        approval_store_path=str(tmp_path / "app.json"),
    )


@pytest.fixture
def transport():
    return FakeTransport()


@pytest.fixture
def clock():
    state = {"t": 1000.0}
    return state


def make_authed(config, transport, clock_state, *, expires_in=3600):
    auth = GraphAuthenticator(config, transport=transport, clock=lambda: clock_state["t"])
    # expiry must be based on real wall-clock: TokenRefreshService.should_refresh
    # uses time.time(), independent of the injected fake clock.
    import time as _time
    auth.token_repo.save("m365", {
        "access_token": "AT-1",
        "refresh_token": "RT-1",
        "expires_at": _time.time() + expires_in,
        "scope": config.scope_string(),
    })
    client = GraphClient(config, auth, transport=transport, sleeper=lambda _s: None)
    return auth, client


@pytest.fixture
def authed():
    return make_authed

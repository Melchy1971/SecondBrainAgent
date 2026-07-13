import time
import pytest
from secondbrain.connectors.google.config import GoogleConfig
from secondbrain.connectors.google.auth import GoogleAuthenticator
from secondbrain.connectors.google.client import GoogleClient


@pytest.fixture
def config(tmp_path):
    return GoogleConfig(
        client_id="cid", client_secret="csecret",
        token_store_path=str(tmp_path / "tok.json"),
        cursor_store_path=str(tmp_path / "cur.json"),
        approval_store_path=str(tmp_path / "app.json"),
    )


def make_authed(config, transport, clock_state=None, *, expires_in=3600):
    auth = GoogleAuthenticator(config, transport=transport, clock=lambda: (clock_state or {"t": 1000.0})["t"])
    auth.token_repo.save("google", {"access_token": "AT", "refresh_token": "RT",
                                    "expires_at": time.time() + expires_in, "scope": config.scope_string()})
    client = GoogleClient(config, auth, transport=transport, sleeper=lambda _s: None)
    return auth, client


@pytest.fixture
def authed():
    return make_authed

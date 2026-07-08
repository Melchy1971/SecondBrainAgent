import pytest
from secondbrain.connectors.google.config import GoogleConfig, GoogleConfigError
from secondbrain.connectors.google.auth import GoogleAuthenticator
from secondbrain.connectors.scaffold.transport import FakeTransport


def test_config_requires_id_and_secret():
    with pytest.raises(GoogleConfigError):
        GoogleConfig.from_env({"GOOGLE_CLIENT_ID": "x"})  # missing secret
    cfg = GoogleConfig.from_env({"GOOGLE_CLIENT_ID": "x", "GOOGLE_CLIENT_SECRET": "y"})
    assert cfg.client_id == "x" and cfg.client_secret == "y"


def test_device_login_includes_client_secret_and_handles_verification_url(config):
    tp = FakeTransport()
    tp.on("POST", "/device/code", lambda u, m, h, b: tp.json_response(200, {
        "device_code": "DC", "user_code": "WXYZ", "verification_url": "https://www.google.com/device",
        "expires_in": 900, "interval": 1}))
    seen = {"secret": False}
    def token(u, m, h, b):
        if b and b"client_secret=csecret" in b:
            seen["secret"] = True
        return tp.json_response(200, {"access_token": "AT", "refresh_token": "RT", "expires_in": 3600})
    tp.on("POST", "/token", token)
    auth = GoogleAuthenticator(config, transport=tp, clock=lambda: 1000.0)
    start = auth.begin_device_login()
    assert start.verification_uri == "https://www.google.com/device"
    auth.complete_device_login(start, sleeper=lambda _s: None)
    assert auth.is_authenticated() and seen["secret"]

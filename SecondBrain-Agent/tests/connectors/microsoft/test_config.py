import pytest
from secondbrain.connectors.microsoft.config import GraphConfig, GraphConfigError, DEFAULT_SCOPES


def test_from_env_requires_client_id():
    with pytest.raises(GraphConfigError) as exc:
        GraphConfig.from_env({})
    assert "M365_CLIENT_ID" in str(exc.value)


def test_from_env_parses_scopes_and_tenant():
    cfg = GraphConfig.from_env({"M365_CLIENT_ID": "abc", "M365_TENANT_ID": "tid", "M365_SCOPES": "Mail.Read Files.Read"})
    assert cfg.client_id == "abc"
    assert cfg.tenant_id == "tid"
    assert cfg.scopes == ("Mail.Read", "Files.Read")
    assert cfg.token_url.endswith("/tid/oauth2/v2.0/token")
    assert cfg.devicecode_url.endswith("/tid/oauth2/v2.0/devicecode")


def test_defaults_include_write_scopes():
    cfg = GraphConfig.from_env({"M365_CLIENT_ID": "abc"})
    assert cfg.tenant_id == "common"
    assert cfg.scopes == DEFAULT_SCOPES
    assert "Mail.Send" in cfg.scopes and "Tasks.ReadWrite" in cfg.scopes

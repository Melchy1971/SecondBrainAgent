from secondbrain.security.secret_vault import SecretVault
from secondbrain.security.approval_policies import ApprovalPolicies


def test_secret_vault():
    vault = SecretVault()
    vault.put("api", "123")
    assert vault.get("api") == "123"


def test_approval_policies():
    assert ApprovalPolicies().requires_approval("delete")

from secondbrain.production_core import ProductionCore


def test_status(tmp_path):
    prod = ProductionCore(tmp_path)
    assert prod.status()["version"] == "15.0"


def test_runtime_watchdog_recover(tmp_path):
    prod = ProductionCore(tmp_path)
    prod.stop_runtime()
    scan = prod.watchdog.scan()
    assert scan["status"] == "degraded"
    recovered = prod.watchdog.recover()
    assert "restart_runtime" in recovered["actions"]


def test_secrets_redacted(tmp_path):
    prod = ProductionCore(tmp_path)
    prod.vault.put("api_key", "secret")
    listed = prod.vault.list()[0]
    assert "value_enc" not in listed


def test_audit_redacts_metadata(tmp_path):
    prod = ProductionCore(tmp_path)
    event = prod.audit.log("user", "test", "target", {"token": "abc"})
    assert event["metadata"]["token"] == "***REDACTED***"


def test_approval_flow(tmp_path):
    prod = ProductionCore(tmp_path)
    req = prod.approvals.request("agent", "file_write", "high")
    decision = prod.approvals.decide(req["id"], "approved")
    assert decision["status"] == "approved"


def test_backup_verify_restore_plan(tmp_path):
    prod = ProductionCore(tmp_path)
    prod.start_runtime()
    backup = prod.backups.create("test")
    verified = prod.backups.verify(backup["id"])
    assert verified["ok"] is True
    plan = prod.backups.restore_plan(backup["id"])
    assert plan["can_restore"] is True


def test_deployment_manifest(tmp_path):
    prod = ProductionCore(tmp_path)
    manifest = prod.deployment.installer_manifest()
    assert manifest["version"] == "15.0"

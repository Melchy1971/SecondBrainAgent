from secondbrain.service_runtime import ServiceRuntime


def test_lifecycle(tmp_path):
    rt = ServiceRuntime(tmp_path)
    rt.start()
    assert rt.health()["status"] == "healthy"
    rt.stop()
    assert rt.health()["status"] == "degraded"


def test_logs_metrics(tmp_path):
    rt = ServiceRuntime(tmp_path)
    rt.log("warning", "test")
    assert rt.metrics()["warnings"] == 1


def test_http_manifest(tmp_path):
    rt = ServiceRuntime(tmp_path)
    assert "/health" in rt.http_manifest()["endpoints"]


def test_service_script_and_manifest(tmp_path):
    rt = ServiceRuntime(tmp_path)
    assert rt.service_manifest()["service_name"] == "SecondBrainOS"
    assert rt.generate_service_script()["path"].endswith("secondbrain_service.py")


def test_nssm_commands(tmp_path):
    rt = ServiceRuntime(tmp_path)
    assert any("nssm install" in c for c in rt.nssm_commands()["commands"])

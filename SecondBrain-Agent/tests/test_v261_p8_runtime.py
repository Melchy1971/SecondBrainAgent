from secondbrain.operations.audit_center import AuditCenter
from secondbrain.operations.monitoring import MonitoringService
from secondbrain.gates.p8_completion_report import build_p8_completion_report


def test_audit_center():
    audit = AuditCenter()
    audit.record("security", "login")
    assert len(audit.list()) == 1


def test_monitoring():
    result = MonitoringService().health({"db": True, "redis": False})
    assert result["status"] == "FAIL"


def test_completion_report():
    report = build_p8_completion_report()
    assert report["status"] == "PASS"
    assert report["next_phase"] == "GA_HARDENING"

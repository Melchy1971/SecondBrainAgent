"""Sprint 38 (v30.99) acceptance tests - unified operations monitoring."""

from __future__ import annotations

import time

import pytest

from secondbrain.monitoring.operations_monitor import (
    HealthCheckResult, OperationalStatus, OperationsMonitor, map_health_status, worst_status,
)


class FakeTimeline:
    def __init__(self):
        self.records = []
    def record(self, component, status, detail=""):
        self.records.append((component, status, detail))


def _mon(checks, **kw):
    return OperationsMonitor(checks, **kw)


# 1: failed DB shows as BLOCKED
def test_db_failure_blocked():
    mon = _mon({"PostgreSQL": lambda: {"status": "critical", "message": "connection refused"}})
    view = mon.system_view()
    db = next(c for c in view["components"] if c["component"] == "PostgreSQL")
    assert db["status"] == OperationalStatus.BLOCKED.value
    assert view["overall"] == OperationalStatus.BLOCKED.value


# 2: provider offline shows as unavailable
def test_provider_unavailable():
    mon = _mon({"LLM Provider": lambda: {"status": "unavailable", "message": "offline"}})
    view = mon.system_view()
    p = next(c for c in view["components"] if c["component"] == "LLM Provider")
    assert p["status"] == OperationalStatus.UNAVAILABLE.value


# 3: GUI stays functional when a module check crashes (fault isolation)
def test_fault_isolation():
    def boom():
        raise RuntimeError("module exploded")
    mon = _mon({"Broken": boom, "RAG": lambda: {"status": "ok"}})
    view = mon.system_view()  # must not raise
    broken = next(c for c in view["components"] if c["component"] == "Broken")
    rag = next(c for c in view["components"] if c["component"] == "RAG")
    assert broken["status"] == OperationalStatus.UNAVAILABLE.value
    assert rag["status"] == OperationalStatus.READY.value  # unaffected
    assert "module exploded" not in str(view)  # no stacktrace/detail in main view


# 4: status history is recorded (uses injected timeline)
def test_history_recorded():
    tl = FakeTimeline()
    mon = _mon({"DB": lambda: {"status": "ok"}}, timeline=tl)
    mon.evaluate()
    assert tl.records and tl.records[0][0] == "DB"


# 5: health checks run with a timeout
def test_check_timeout():
    def slow():
        time.sleep(2.0)
        return {"status": "ok"}
    mon = _mon({"Slow": slow}, default_timeout_s=0.2)
    result = mon.evaluate()[0]
    assert result.status == OperationalStatus.UNAVAILABLE.value if False else result.status == OperationalStatus.UNAVAILABLE
    assert result.message == "check_timeout"


# 6: no secrets in export
def test_no_secrets_in_export():
    mon = _mon({"Vault": lambda: {"status": "ok", "message": "token=sk-abcdef123456 leaked",
                                  "metrics": {"api_key": "sk-zzz999888777"}}})
    export = mon.export()
    blob = str(export)
    assert "sk-abcdef123456" not in blob and "sk-zzz999888777" not in blob


# 7: monitoring reuses existing components (map_health_status over traffic-light)
def test_reuses_traffic_light_mapping():
    assert map_health_status("ok") == OperationalStatus.READY
    assert map_health_status("warn") == OperationalStatus.DEGRADED
    assert map_health_status("critical") == OperationalStatus.BLOCKED
    assert map_health_status("unavailable") == OperationalStatus.UNAVAILABLE


# 8: maintenance mode suppresses expected warnings traceably
def test_maintenance_suppresses_warnings():
    mon = _mon({"DB": lambda: {"status": "warn", "message": "planned reindex", "warnings": ["slow"]}})
    mon.set_maintenance("DB", True)
    result = mon.evaluate()[0]
    assert result.status == OperationalStatus.MAINTENANCE
    assert result.warnings == []                       # suppressed
    assert "maintenance" in result.message.lower()     # traceable
    # maintenance component produces no alert
    assert mon.alerts([result]) == []


# recovering overlay on improvement
def test_recovering_after_blocked():
    state = {"s": "critical"}
    mon = _mon({"DB": lambda: {"status": state["s"]}})
    assert mon.evaluate()[0].status == OperationalStatus.BLOCKED
    state["s"] = "ok"
    assert mon.evaluate()[0].status == OperationalStatus.RECOVERING


# worst-state ignores neutral states
def test_worst_state():
    results = [
        HealthCheckResult("a", OperationalStatus.READY),
        HealthCheckResult("b", OperationalStatus.UNAVAILABLE),
        HealthCheckResult("c", OperationalStatus.DEGRADED),
    ]
    assert worst_status(results) == OperationalStatus.DEGRADED
    results.append(HealthCheckResult("d", OperationalStatus.BLOCKED))
    assert worst_status(results) == OperationalStatus.BLOCKED


# acknowledge silences alert
def test_acknowledge_silences_alert():
    mon = _mon({"DB": lambda: {"status": "critical", "message": "down"}})
    assert mon.alerts(mon.evaluate())  # alert present
    mon.acknowledge("DB")
    assert mon.alerts(mon.evaluate()) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

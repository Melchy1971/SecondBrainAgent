import json

from secondbrain.desktop_native.storage_alerts import read_vector_validation, storage_alert_labels


def test_vector_validation_reads_only_bounded_fields(tmp_path) -> None:
    reports = tmp_path / "runtime" / "reports"
    reports.mkdir(parents=True)
    (reports / "p1_rag_validation_latest.json").write_text(
        json.dumps({"ok": True, "blockers": 0, "warnings": 2, "path": "secret", "findings": ["payload"]}),
        encoding="utf-8",
    )
    assert read_vector_validation(tmp_path) == {
        "available": True, "ok": True, "blockers": 0, "warnings": 2,
    }


def test_missing_or_invalid_vector_report_is_unavailable(tmp_path) -> None:
    assert read_vector_validation(tmp_path) == {"available": False}
    reports = tmp_path / "runtime" / "reports"
    reports.mkdir(parents=True)
    (reports / "p1_rag_validation_latest.json").write_text("not-json", encoding="utf-8")
    assert read_vector_validation(tmp_path) == {"available": False}


def test_storage_labels_report_healthy_snapshots_without_details() -> None:
    result = storage_alert_labels(
        backup={"backup_center": {"backup_count": 3, "status": "PASS", "latest_backup": {"path": "secret"}}},
        vector={"available": True, "ok": True, "blockers": 0, "warnings": 0},
    )
    assert result == {"backup": "3 / PASS", "vector_index": "Ready"}
    assert "secret" not in str(result)


def test_storage_labels_expose_empty_warning_and_blocked_states() -> None:
    assert storage_alert_labels(backup={"backup_center": {"backup_count": 0}}, vector={"available": False}) == {
        "backup": "No backups", "vector_index": "Not checked",
    }
    assert storage_alert_labels(
        backup={}, vector={"available": True, "ok": True, "blockers": 0, "warnings": 2}
    ) == {"backup": "Unavailable", "vector_index": "Warning (2)"}
    assert storage_alert_labels(
        backup={}, vector={"available": True, "ok": False, "blockers": 4, "warnings": 0}
    )["vector_index"] == "Blocked (4)"

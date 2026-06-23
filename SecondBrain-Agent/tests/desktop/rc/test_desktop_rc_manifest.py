from secondbrain.desktop.rc import DesktopRCManifestBuilder, DesktopRCStatusSnapshot


def test_manifest_builder_creates_reproducible_build_id_shape():
    manifest = DesktopRCManifestBuilder().build(
        rc_version="2.1.7-rc1",
        gate_status="PASS",
        test_summary={"passed": 531, "failed": 0},
    )

    assert manifest.build_id == "desktop-rc-2-1-7-rc1-8"
    assert "desktop.jobs" in manifest.desktop_modules
    assert manifest.to_dict()["test_summary"]["passed"] == 531


def test_status_snapshot_aggregates_warning():
    snapshot = DesktopRCStatusSnapshot.from_components(
        {"shell": "PASS", "jobs": "WARNING"},
        metrics={"queue_length": 0},
    )

    assert snapshot.status.value == "WARNING"
    assert snapshot.to_dict()["components"]["jobs"] == "WARNING"

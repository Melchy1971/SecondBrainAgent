from pathlib import Path

from secondbrain.release_manifest import build_release_manifest, discover_patch_records, write_release_manifest


def test_discovers_patch_reports_in_numeric_order(tmp_path: Path):
    (tmp_path / "PATCH_P1_3_7_REPORT.md").write_text("# Ingestion Index Bridge\n\nValidation: `519 passed in 19.05s`", encoding="utf-8")
    (tmp_path / "PATCH_P0_6_REPORT.md").write_text("# Secrets Vault\n\nValidation: `395 passed in 18.43s`", encoding="utf-8")

    records = discover_patch_records(tmp_path)

    assert [record.key for record in records] == ["P0_6", "P1_3_7"]
    assert records[-1].passed_count == 519
    assert records[-1].duration_seconds == 19.05


def test_build_release_manifest_derives_highest_test_count(tmp_path: Path):
    (tmp_path / "PATCH_P1_1_1_REPORT.md").write_text("# Embedding Abstraction\n\n`402 tests collected`", encoding="utf-8")
    (tmp_path / "PATCH_P1_3_7_REPORT.md").write_text("# Ingestion Index Bridge\n\n`519 passed in 19.05s`", encoding="utf-8")

    manifest = build_release_manifest(tmp_path, current_version="P1.4.1")

    assert manifest.summary()["current_version"] == "P1.4.1"
    assert manifest.summary()["test_count"] == 519
    assert manifest.summary()["latest_patch"] == "P1_3_7"


def test_write_release_manifest_outputs_markdown(tmp_path: Path):
    (tmp_path / "PATCH_P1_2_5_REPORT.md").write_text("# Connector Lifecycle\n\n`467 passed in 15.06s`", encoding="utf-8")

    path = write_release_manifest(tmp_path, current_version="P1.4.1", test_count=520, release_state="PASS_CANDIDATE")

    text = path.read_text(encoding="utf-8")
    assert "Current version: `P1.4.1`" in text
    assert "Release state: `PASS_CANDIDATE`" in text
    assert "| `P1_2_5` | Connector Lifecycle | 467 passed in 15.06s |" in text

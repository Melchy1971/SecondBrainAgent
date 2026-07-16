from __future__ import annotations

import json
from pathlib import Path

from secondbrain.release.personal_jarvis_gate import (
    BLOCKED,
    CONDITIONAL_PASS,
    PASS,
    ModuleContract,
    run_personal_jarvis_gate,
)


def test_gate_passes_with_valid_contracts(tmp_path: Path) -> None:
    contracts = (
        ModuleContract("json_available", "core", "json", ("loads",), "JSON available"),
        ModuleContract("path_available", "core", "pathlib", ("Path",), "Path available"),
    )
    report = run_personal_jarvis_gate(tmp_path, contracts=contracts)
    assert report["overall_status"] == PASS
    assert report["ok"] is True
    stored = json.loads((tmp_path / "runtime" / "reports" / "personal_jarvis_gate.json").read_text(encoding="utf-8"))
    assert stored["schema"] == "secondbrain.personal_jarvis_gate.v1"


def test_optional_missing_contract_is_warning(tmp_path: Path) -> None:
    contracts = (
        ModuleContract("optional", "knowledge", "module_does_not_exist_xyz", ("Service",), "Optional", hard_blocker=False),
    )
    report = run_personal_jarvis_gate(tmp_path, contracts=contracts, write_report=False)
    assert report["overall_status"] == CONDITIONAL_PASS
    assert report["warnings"] == ["optional"]


def test_required_missing_contract_blocks(tmp_path: Path) -> None:
    contracts = (
        ModuleContract("required", "mail", "module_does_not_exist_xyz", ("Service",), "Required", hard_blocker=True),
    )
    report = run_personal_jarvis_gate(tmp_path, contracts=contracts, write_report=False)
    assert report["overall_status"] == BLOCKED
    assert report["release_recommendation"] == "DO_NOT_RELEASE"


def test_extra_probe_is_defensive(tmp_path: Path) -> None:
    def broken_probe():
        raise RuntimeError("boom")

    report = run_personal_jarvis_gate(
        tmp_path,
        contracts=(),
        write_report=False,
        extra_probes={"journey": ("journeys", "Journey probe", broken_probe, True)},
    )
    assert report["overall_status"] == BLOCKED
    assert report["checks"][0]["detail"] == "probe_error:RuntimeError"


def test_report_does_not_expose_probe_payload(tmp_path: Path) -> None:
    secret = "sk-secret-value"
    report = run_personal_jarvis_gate(
        tmp_path,
        contracts=(),
        write_report=False,
        extra_probes={"safe": ("security", "Safe probe", lambda: {"ok": True, "secret": secret}, True)},
    )
    assert secret not in json.dumps(report)

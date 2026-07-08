import json

from secondbrain.desktop.search.release import SearchMetricsSnapshot, SearchRC1Gate, SearchRC1GateInput


def _all_capabilities():
    return {k: True for k in [
        "search_service", "hybrid_search", "preview", "highlighting", "saved_searches", "persistence", "history"
    ]}


def _all_flags():
    return {k: True for k in [
        "foundation", "hybrid_search_ui", "preview_highlighting", "saved_searches", "persistence", "tests", "no_critical_blockers"
    ]}


def test_search_rc1_gate_passes_with_complete_inputs():
    result = SearchRC1Gate().evaluate(SearchRC1GateInput(
        version="p2.4.5",
        capabilities=_all_capabilities(),
        checklist_flags=_all_flags(),
        metrics=SearchMetricsSnapshot(result_count=5, history_size=2),
    ))
    assert result.passed
    assert result.to_dict()["status"] == "PASS"


def test_search_rc1_gate_writes_reports(tmp_path):
    gate = SearchRC1Gate()
    result = gate.evaluate(SearchRC1GateInput("p2.4.5", _all_capabilities(), _all_flags(), SearchMetricsSnapshot()))
    files = gate.write_reports(result, tmp_path)
    assert set(files) == {"search_rc1_report", "search_metrics", "search_validation", "search_checklist"}
    assert json.loads(files["search_rc1_report"].read_text())["passed"] is True


def test_search_rc1_gate_blocks_on_missing_checklist_item():
    flags = _all_flags()
    flags["tests"] = False
    result = SearchRC1Gate().evaluate(SearchRC1GateInput("p2.4.5", _all_capabilities(), flags, SearchMetricsSnapshot()))
    assert not result.passed
    assert result.to_dict()["status"] == "BLOCKED"

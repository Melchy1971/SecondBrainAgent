from secondbrain.desktop.search.release import (
    SearchCheckStatus,
    SearchMetricsSnapshot,
    build_default_search_checklist,
    create_search_health_report,
    validate_required_capabilities,
)


def test_health_report_is_pass_when_validation_and_checklist_pass():
    capabilities = {k: True for k in [
        "search_service", "hybrid_search", "preview", "highlighting", "saved_searches", "persistence", "history"
    ]}
    flags = {k: True for k in [
        "foundation", "hybrid_search_ui", "preview_highlighting", "saved_searches", "persistence", "tests", "no_critical_blockers"
    ]}
    report = create_search_health_report(
        version="p2.4.5",
        validation=validate_required_capabilities(capabilities),
        checklist=build_default_search_checklist(flags),
        metrics=SearchMetricsSnapshot(result_count=1),
    )
    assert report.status == SearchCheckStatus.PASS
    assert report.to_dict()["status"] == "PASS"

from secondbrain.desktop.search.release import SearchCheckStatus, validate_required_capabilities


def test_required_capabilities_pass_when_all_present():
    report = validate_required_capabilities({
        "search_service": True,
        "hybrid_search": True,
        "preview": True,
        "highlighting": True,
        "saved_searches": True,
        "persistence": True,
        "history": True,
    })
    assert report.status == SearchCheckStatus.PASS
    assert report.blockers == ()


def test_missing_required_capability_fails_gate():
    report = validate_required_capabilities({"search_service": True})
    assert report.status == SearchCheckStatus.FAIL
    assert report.blockers

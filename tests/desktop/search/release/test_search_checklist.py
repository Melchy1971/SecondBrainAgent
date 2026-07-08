from secondbrain.desktop.search.release import build_default_search_checklist


def test_default_checklist_detects_missing_required_items():
    checklist = build_default_search_checklist({"foundation": True, "tests": False})
    assert not checklist.complete
    assert "tests" in checklist.missing_required()

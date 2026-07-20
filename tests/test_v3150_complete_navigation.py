from secondbrain.desktop_native.action_registry import build_core_registry
from secondbrain.desktop_native.app import NAV_ITEMS
from secondbrain.desktop_native.navigation import NAVIGATION_VIEWS, VIEWS, display_view
from secondbrain.desktop_native.qt_shell import VIEWS as QT_VIEWS


def test_tk_qt_and_canonical_navigation_share_all_required_views():
    assert len(VIEWS) == 18
    assert QT_VIEWS == VIEWS
    assert set(VIEWS).issubset(NAV_ITEMS)


def test_registry_exposes_navigation_action_for_every_view():
    registry = build_core_registry(lambda payload: payload)
    for view_id, _display, spoken in NAVIGATION_VIEWS:
        assert registry.get(f"navigation.{view_id}")
        assert registry.resolve_alias(f"öffne {spoken.lower()}").id == f"navigation.{view_id}"


def test_action_view_ids_map_back_to_exact_desktop_labels():
    assert display_view("knowledge_graph") == "Knowledge Graph"
    assert display_view("approvals") == "Approvals"
    assert display_view("unknown_view") == "Unknown View"

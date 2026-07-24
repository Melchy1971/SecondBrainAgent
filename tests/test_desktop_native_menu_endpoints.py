from __future__ import annotations

import pytest

from secondbrain.desktop_native.app import NAV_ITEMS, JarvisNativeApp
from secondbrain.desktop_native.navigation import MENU_ENDPOINTS, endpoint_for_view


def test_every_visible_menu_item_has_exactly_one_real_endpoint() -> None:
    assert set(NAV_ITEMS) == set(MENU_ENDPOINTS)
    assert len(NAV_ITEMS) == len(set(NAV_ITEMS))
    assert all(endpoint.kind in {"native", "workspace", "live_data", "external", "launcher"}
               for endpoint in MENU_ENDPOINTS.values())
    assert all(endpoint.target for endpoint in MENU_ENDPOINTS.values())


@pytest.mark.parametrize("view", NAV_ITEMS)
def test_every_visible_menu_item_resolves(view: str) -> None:
    assert endpoint_for_view(view) == MENU_ENDPOINTS[view]


def test_unknown_menu_item_cannot_fall_back_to_fake_ready_state() -> None:
    with pytest.raises(ValueError, match="unknown desktop view"):
        endpoint_for_view("Not a real view")


class _GridWidget:
    def __init__(self) -> None:
        self.removed = False
        self.config: dict[str, object] = {}

    def grid_remove(self) -> None:
        self.removed = True

    def grid(self) -> None:
        self.removed = False

    def grid_configure(self, **kwargs: object) -> None:
        self.config = kwargs


def test_menu_selection_promotes_endpoint_to_primary_content_surface() -> None:
    app = object.__new__(JarvisNativeApp)
    app.left_column = _GridWidget()
    app.center_column = _GridWidget()
    app.right_column = _GridWidget()
    app.console = _GridWidget()

    app._activate_content_surface("Projects")

    assert app.left_column.removed
    assert app.center_column.removed
    assert app.right_column.removed
    assert app.console.config == {
        "row": 0,
        "column": 0,
        "columnspan": 3,
        "rowspan": 4,
        "sticky": "nsew",
        "pady": 0,
    }

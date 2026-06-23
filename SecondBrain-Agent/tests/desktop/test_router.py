import pytest
from secondbrain.desktop.router import DesktopRouter


def test_router_navigates_registered_route():
    router = DesktopRouter()
    router.register("dashboard", "Dashboard", lambda: "ok")

    assert router.navigate("dashboard") == "ok"
    assert router.current == "dashboard"


def test_router_rejects_unknown_route():
    router = DesktopRouter()
    with pytest.raises(KeyError):
        router.navigate("missing")

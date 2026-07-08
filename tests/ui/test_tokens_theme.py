import pytest
from secondbrain.ui import tokens
from secondbrain.ui.theme import ThemeRegistry, ttk_style_map


@pytest.mark.parametrize("name", ["dark", "light"])
def test_palettes_complete(name):
    assert tokens.missing_roles(tokens.palette(name)) == []


def test_theme_registry_toggle_and_set():
    reg = ThemeRegistry("dark")
    assert reg.active().name == "dark"
    assert reg.toggle().name == "light"
    assert reg.set("dark").name == "dark"
    with pytest.raises(ValueError):
        reg.set("neon")


def test_style_map_has_core_styles():
    m = ttk_style_map(ThemeRegistry("dark").active())
    assert "TButton" in m and "Primary.TButton" in m and "Status.TLabel" in m

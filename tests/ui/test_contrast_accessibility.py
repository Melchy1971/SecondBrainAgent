import pytest
from secondbrain.ui import tokens
from secondbrain.ui.contrast import contrast_ratio, passes_aa, audit_pairs


def test_known_ratios():
    assert round(contrast_ratio("#FFFFFF", "#000000"), 1) == 21.0
    assert round(contrast_ratio("#FFFFFF", "#FFFFFF"), 1) == 1.0


def test_invalid_hex_raises():
    with pytest.raises(ValueError):
        contrast_ratio("nope", "#000000")


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_palette_meets_wcag_aa(theme):
    p = tokens.palette(theme)
    assert passes_aa(p["fg"], p["bg"])            # body text AA
    assert passes_aa(p["fg_muted"], p["bg"])      # muted text AA
    assert passes_aa(p["on_primary"], p["primary"])   # text on accent AA
    audit = audit_pairs([("fg", p["fg"], p["bg"]), ("muted", p["fg_muted"], p["bg"])])
    assert audit["passes_aa"] is True

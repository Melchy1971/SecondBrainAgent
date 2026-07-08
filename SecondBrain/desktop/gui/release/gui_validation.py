from __future__ import annotations

from .gui_rc1_gate import GuiRc1Input, GuiRc1Gate, GuiRc1Report


def validate_gui_rc1(payload: GuiRc1Input) -> GuiRc1Report:
    return GuiRc1Gate().evaluate(payload)

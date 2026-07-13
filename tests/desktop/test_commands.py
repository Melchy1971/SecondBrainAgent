import pytest
from secondbrain.desktop.commands import Command, CommandPalette


def test_command_palette_executes_and_searches():
    palette = CommandPalette()
    palette.register(Command("import.file", "Import File", lambda: "done"))

    assert palette.execute("import.file") == "done"
    assert [cmd.id for cmd in palette.search("import")] == ["import.file"]


def test_command_palette_rejects_unknown_command():
    palette = CommandPalette()
    with pytest.raises(KeyError):
        palette.execute("missing")

"""Schutz gegen undeklarierte GUI-Laufzeitabhaengigkeiten.

Hintergrund: ``SecondBrain/desktop_native/qt_shell.py`` importierte PySide6,
ohne dass das Paket in ``pyproject.toml`` oder einer ``requirements``-Datei
deklariert war. Die Anwendung stuerzte dadurch nicht ab -- ``capabilities()``
faellt sauber in den Degraded Mode -- aber die Qt-Oberflaeche fehlte auf jeder
frischen Installation und im Windows-Paket, ohne dass es auffiel.

Dieser Test faengt denselben Fehler fuer jedes GUI-Toolkit erneut ab.
"""

from __future__ import annotations

import ast
import re
from functools import lru_cache
from pathlib import Path

import pytest

GUI_TOOLKITS = ("PySide6", "PySide2", "PyQt5", "PyQt6")
SOURCE_ROOT = "SecondBrain"


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _pyproject() -> dict:
    text = (_root() / "pyproject.toml").read_text(encoding="utf-8")
    try:
        import tomllib
    except ModuleNotFoundError:  # Python < 3.11, nur ausserhalb der CI relevant
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ModuleNotFoundError:
            pytest.skip("Weder tomllib noch tomli verfuegbar")
    return tomllib.loads(text)


def _declared_requirements() -> set[str]:
    """Alle in requirements-Dateien und pyproject deklarierten Paketnamen."""
    names: set[str] = set()

    for req in _root().glob("requirements*.txt"):
        for line in req.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                names.add(re.split(r"[<>=!~\[]", line, 1)[0].strip().lower())

    data = _pyproject()
    project = data.get("project", {})
    for spec in project.get("dependencies", []):
        names.add(re.split(r"[<>=!~\[]", str(spec), 1)[0].strip().lower())
    for group in project.get("optional-dependencies", {}).values():
        for spec in group:
            names.add(re.split(r"[<>=!~\[]", str(spec), 1)[0].strip().lower())

    return names


@lru_cache(maxsize=1)
def _toolkit_importers() -> dict[str, tuple[Path, ...]]:
    """Einmaliger Baumdurchlauf: Toolkit -> importierende Module.

    Der Baum wird bewusst nur einmal geparst. Ein Durchlauf je Toolkit dauert
    auf gemounteten Dateisystemen ein Vielfaches der Testlaufzeit.
    """
    found: dict[str, list[Path]] = {t: [] for t in GUI_TOOLKITS}
    wanted = set(GUI_TOOLKITS)

    for path in (_root() / SOURCE_ROOT).rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])

        for toolkit in roots & wanted:
            found[toolkit].append(path)

    return {toolkit: tuple(paths) for toolkit, paths in found.items()}


def _modules_importing(toolkit: str) -> tuple[Path, ...]:
    return _toolkit_importers()[toolkit]


# --------------------------------------------------------------------------


@pytest.mark.parametrize("toolkit", GUI_TOOLKITS)
def test_imported_gui_toolkit_is_declared(toolkit: str) -> None:
    """Jedes importierte GUI-Toolkit muss deklariert sein."""
    importers = _modules_importing(toolkit)
    if not importers:
        return

    declared = _declared_requirements()
    assert toolkit.lower() in declared, (
        f"{toolkit} wird importiert, ist aber nirgends deklariert.\n"
        "Importierende Module:\n"
        + "\n".join(f"  {p.relative_to(_root())}" for p in importers)
    )


def test_pyside6_is_declared_in_desktop_extra() -> None:
    extras = _pyproject()["project"]["optional-dependencies"]
    desktop = {re.split(r"[<>=!~\[]", s, 1)[0].strip().lower() for s in extras["desktop"]}
    assert "pyside6" in desktop, "PySide6 fehlt im desktop-Extra"

    everything = {re.split(r"[<>=!~\[]", s, 1)[0].strip().lower() for s in extras["all"]}
    assert "pyside6" in everything, "PySide6 fehlt im all-Extra"


def test_requirements_desktop_matches_desktop_extra() -> None:
    """requirements-desktop.txt und das desktop-Extra duerfen nicht auseinanderlaufen."""
    req_file = _root() / "requirements-desktop.txt"
    assert req_file.exists(), "requirements-desktop.txt fehlt"

    from_file = set()
    for line in req_file.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            from_file.add(re.split(r"[<>=!~\[]", line, 1)[0].strip().lower())

    extras = _pyproject()["project"]["optional-dependencies"]["desktop"]
    from_extra = {re.split(r"[<>=!~\[]", s, 1)[0].strip().lower() for s in extras}

    assert from_file == from_extra, (
        "requirements-desktop.txt weicht vom desktop-Extra ab.\n"
        f"  nur in Datei: {sorted(from_file - from_extra)}\n"
        f"  nur im Extra: {sorted(from_extra - from_file)}"
    )


def test_windows_build_pins_pyside6() -> None:
    """Ohne Pin landet die Qt-Shell nicht reproduzierbar im Windows-Paket."""
    constraints = (_root() / "packaging" / "windows" / "constraints.txt").read_text(encoding="utf-8")
    assert re.search(r"(?mi)^PySide6==", constraints), (
        "packaging/windows/constraints.txt pinnt PySide6 nicht"
    )


def test_qt_shell_degrades_instead_of_crashing() -> None:
    """Die Discovery darf Qt nicht importieren und muss ohne PySide6 tragen."""
    source = (_root() / SOURCE_ROOT / "desktop_native" / "qt_shell.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    capabilities = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "capabilities"),
        None,
    )
    assert capabilities is not None, "qt_shell.capabilities() fehlt"

    body = ast.dump(capabilities)
    assert "find_spec" in body, "capabilities() prueft PySide6 nicht per find_spec"
    for node in ast.walk(capabilities):
        assert not isinstance(node, (ast.Import, ast.ImportFrom)), (
            "capabilities() darf Qt nicht importieren -- das kann Windows-Qt-Builds zum "
            "Absturz bringen, bevor eine QApplication existiert"
        )

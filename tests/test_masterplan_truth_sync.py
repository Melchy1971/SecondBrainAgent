"""Konsistenztest zwischen Masterplan und tatsaechlichem Codebestand.

Zweck: verhindern, dass bereits gemergte Funktionen weiterhin als
``pending_merge`` dokumentiert bleiben, und verhindern, dass ein einmal als
veraltet entfernter Blocker unbemerkt zurueckkehrt.

Der Test bewertet ausschliesslich Dokumentationswahrheit. Er trifft keine
Aussage darueber, ob eine Funktion live zertifiziert ist -- diese Trennung
ist selbst Gegenstand einer der Pruefungen.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PENDING_MARKERS = ("pending_merge", "branch_merge_pending", "branches_pending")


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def masterplan() -> dict:
    path = _root() / "docs" / "09_MASTERPLAN_STATUS.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _capabilities(masterplan: dict) -> list[dict]:
    return [item for item in masterplan["completed_capabilities"] if isinstance(item, dict)]


# --------------------------------------------------------------------------
# Kernregel: kein gemergtes Feature darf als pending gefuehrt werden
# --------------------------------------------------------------------------


def test_no_capability_claims_pending_merge_when_code_exists(masterplan: dict) -> None:
    """Eine Capability mit vorhandenem Codepfad darf nicht als pending gelten."""
    root = _root()
    offenders: list[str] = []

    for item in _capabilities(masterplan):
        status = str(item.get("status", ""))
        if not any(marker in status for marker in PENDING_MARKERS):
            continue
        evidence = item.get("evidence_path")
        if evidence and (root / str(evidence)).exists():
            offenders.append(
                f"{item.get('release')}: status={status!r}, aber {evidence} existiert auf main"
            )

    assert not offenders, "Gemergte Capabilities als pending dokumentiert:\n" + "\n".join(offenders)


def test_no_blocker_claims_pending_merge_for_removed_entries(masterplan: dict) -> None:
    """Ein als veraltet entfernter Blocker darf nicht wieder auftauchen."""
    remaining = {str(b) for b in masterplan["remaining_blockers"]}
    removed = {str(entry["blocker"]) for entry in masterplan.get("removed_blockers", [])}

    returned = remaining & removed
    assert not returned, f"Bereits entfernte Blocker sind zurueckgekehrt: {sorted(returned)}"


def test_removed_blockers_are_justified_by_existing_code(masterplan: dict) -> None:
    """Jede Blocker-Entfernung mit Evidenzpfad muss diesen Pfad auch belegen koennen."""
    root = _root()
    unjustified: list[str] = []

    for entry in masterplan.get("removed_blockers", []):
        evidence = entry.get("evidence_path")
        if not evidence:
            continue
        if not (root / str(evidence)).exists():
            unjustified.append(f"{entry['blocker']}: {evidence} fehlt")

    assert not unjustified, (
        "Blocker wurden mit einem Evidenzpfad entfernt, der nicht existiert:\n"
        + "\n".join(unjustified)
    )


def test_removed_blockers_carry_reason_and_date(masterplan: dict) -> None:
    for entry in masterplan.get("removed_blockers", []):
        assert entry.get("reason"), f"{entry.get('blocker')}: Begruendung fehlt"
        assert entry.get("removed_at"), f"{entry.get('blocker')}: Entfernungsdatum fehlt"


# --------------------------------------------------------------------------
# Echte Blocker duerfen nicht stillschweigend verschwinden
# --------------------------------------------------------------------------


def test_open_live_certifications_remain_blockers(masterplan: dict) -> None:
    """Solange kein Gate zertifiziert ist, muessen die Nachweis-Blocker stehen."""
    live_gates = masterplan.get("live_gates", {})
    if live_gates.get("certified"):
        pytest.skip("Mindestens ein Live-Gate ist zertifiziert; Regel greift nicht mehr pauschal")

    remaining = {str(b) for b in masterplan["remaining_blockers"]}
    required = {
        "postgresql_pgvector_live_validation_pending",
        "provider_live_validation_openai_ollama_pending",
        "connector_e2e_live_certification_pending",
    }
    missing = required - remaining
    assert not missing, f"Offene Live-Zertifizierungen ohne Blocker: {sorted(missing)}"


def test_missing_gates_are_not_declared_certified(masterplan: dict) -> None:
    live_gates = masterplan.get("live_gates", {})
    overlap = set(live_gates.get("missing", [])) & set(live_gates.get("certified", []))
    assert not overlap, f"Gate gleichzeitig als fehlend und zertifiziert gefuehrt: {sorted(overlap)}"


# --------------------------------------------------------------------------
# Maschinenlesbarkeit und Trennung Implementierung / Live-Nachweis
# --------------------------------------------------------------------------


def test_capabilities_separate_implementation_from_live_evidence(masterplan: dict) -> None:
    """``live_certified`` darf nie implizit aus dem Status abgeleitet werden."""
    for item in _capabilities(masterplan):
        if "live_certified" not in item:
            continue
        assert isinstance(item["live_certified"], bool), (
            f"{item.get('release')}: live_certified muss boolesch sein, "
            f"ist {type(item['live_certified']).__name__}"
        )


def test_capability_inventory_is_referenced_and_present(masterplan: dict) -> None:
    inventory = masterplan.get("capability_inventory", {})
    assert inventory, "capability_inventory fehlt im Masterplan"

    path = inventory.get("path")
    assert path, "capability_inventory.path fehlt"
    assert (_root() / str(path)).exists(), f"Inventar {path} fehlt im Repository"


def test_evidence_paths_resolve(masterplan: dict) -> None:
    """Jeder angegebene Evidenzpfad muss existieren -- sonst ist er wertlos."""
    root = _root()
    broken = [
        f"{item.get('release')}: {item['evidence_path']}"
        for item in _capabilities(masterplan)
        if item.get("evidence_path") and not (root / str(item["evidence_path"])).exists()
    ]
    assert not broken, "Evidenzpfade zeigen ins Leere:\n" + "\n".join(broken)


def test_release_readiness_states_are_known(masterplan: dict) -> None:
    readiness = masterplan["release_readiness"]
    allowed = {
        "BLOCKED",
        "CONDITIONAL_READY",
        "IMPLEMENTATION_AHEAD_OF_CERTIFICATION",
        "READY",
    }
    assert readiness["state"] in allowed, f"Unbekannter Readiness-Status: {readiness['state']!r}"


def test_documented_feature_level_is_not_behind_recorded_capabilities(masterplan: dict) -> None:
    """Die dokumentierte Feature-Stufe darf nicht hinter den Eintraegen zurueckbleiben."""

    def _highest(label: str) -> tuple[int, int]:
        best = (0, 0)
        for token in str(label).replace("-", " ").split():
            if not token.startswith("v"):
                continue
            parts = token[1:].split(".")
            if len(parts) < 2:
                continue
            try:
                candidate = (int(parts[0]), int(parts[1]))
            except ValueError:
                continue
            best = max(best, candidate)
        return best

    documented = _highest(masterplan["documented_feature_level"])
    recorded = max((_highest(item.get("release", "")) for item in _capabilities(masterplan)), default=(0, 0))

    assert documented >= recorded, (
        f"documented_feature_level {masterplan['documented_feature_level']} liegt hinter "
        f"der hoechsten erfassten Capability v{recorded[0]}.{recorded[1]}"
    )

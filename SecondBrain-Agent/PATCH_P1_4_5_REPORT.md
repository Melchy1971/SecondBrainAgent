# PATCH P1.4.5 — Release Candidate RC1

## Inhalt

- `secondbrain/release/release_candidate.py`
  - RC-Datenmodell für Blocker, Kriterien, Checklisten und Summary
  - Release-Gate-, Packaging- und Upgrade-Status als RC-Kriterien
  - Test-Schwellenwert als harter RC-Blocker
  - bekannte Issues mit Trennung nach Blocker/Warning
  - JSON-Export nach `release/release_candidate.json`

- `secondbrain/release/__init__.py`
  - Export der RC-Funktionen
  - isolationssicher für Delta-Anwendung

- `tests/test_p1_4_5_release_candidate.py`
  - PASS-Szenario
  - Test-Schwellenwert-Blocker
  - Packaging-/Upgrade-Blocker
  - Conditional-Pass bei Warnungen
  - manuelle Blocker
  - JSON-Export

## Ergebnis

P1.4.5 erzeugt einen prüfbaren Release-Candidate-Status aus Gate-, Packaging-, Upgrade- und Testsignalen.

## Validierung

`8 passed`

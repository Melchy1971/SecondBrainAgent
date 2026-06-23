# PATCH P1.4.2 — Release Gate V2 Consolidation

## Ziel

Release-Entscheidungen über maschinenlesbare Metadaten statt lose Doku-Fragmente absichern.

## Änderungen

- Neues Package `secondbrain/release/`
- `version.py` mit normalisierter Version `P1.4.2`
- `build_info.py` mit Source-Hash, Build-ID und Build-Metadaten
- `manifest_generator.py` mit Patch-Historie und höchstem Teststand
- `consistency_validator.py` mit Versionsprüfung über README, Manifest und Build-Dateien
- `release_gate_v2.py` mit Gate-Ergebnis `PASS`, `CONDITIONAL_PASS` oder `FAIL`
- Tests für Version, Manifest, Konsistenzprüfung, Gate-Auswertung und Output-Dateien

## Nutzen

- Release-Wahrheit wird reproduzierbar
- Versionsdrift wird automatisch sichtbar
- fehlende Build-/Manifest-Dateien werden als Risiken ausgewiesen
- Gate-Status ist maschinenlesbar und CI-fähig

## Validierung

Delta-Test:

`5 passed in 0.24s`

Hinweis: Das Paket ist als Delta ausgelegt. Es ergänzt Release-Gate-Code und überschreibt keine bestehenden P1.3/P1.4.1 Module.

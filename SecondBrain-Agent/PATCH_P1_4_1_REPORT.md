# PATCH P1.4.1 — Release Manifest Consolidation

## Ziel

Eine eindeutige Versions- und Release-Wahrheit für den aktuellen Delta-Stand herstellen.

## Änderungen

- Neues Modul `secondbrain/release_manifest.py`
- Patch-Discovery für `PATCH_*_REPORT.md`
- numerische Patch-Sortierung über P0/P1-Hierarchie
- Extraktion von Validierungsdaten aus Patch-Reports
- ableitbarer Teststand über höchste bekannte `passed`-Zahl
- Markdown-Export als `RELEASE_MANIFEST.md`
- Tests für Discovery, Ableitung und Export

## Nutzen

- reduziert widersprüchliche Doku-Stände
- macht Delta-Kette prüfbar
- schafft Grundlage für Release-Gate und RC/GA-Entscheidung

## Validierung

Delta-Test:

`3 passed in 0.90s`

Hinweis: Vollständiger Testlauf wurde in diesem isolierten Delta-Arbeitsstand nicht belastbar gewertet, weil der lokale zusammengesetzte Arbeitsordner nicht alle unveränderten Basisdateien des Originalprojekts enthält. Dieses Paket verändert keine bestehenden Imports außer dem neuen Modul.

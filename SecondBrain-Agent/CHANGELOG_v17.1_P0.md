# CHANGELOG v17.1 P0 Integration Core

## Ziel
P0-Entwicklung fortsetzen: Launcher, Registry und Health-Schicht von reiner Import-Prüfung zu belastbarer Betriebsprüfung erweitern.

## Änderungen
- `secondbrain/module_registry.py` erweitert:
  - vollständiger Command Index für Core, Desktop, Voice, Graph und Mobile
  - Command-Auflösung über exakte Commands und Prefixe
  - Runtime-Healthcheck mit optionaler Instanziierung der jeweiligen Runtime
  - Status-Zusammenfassung je Modul zur stabilen CLI-Ausgabe
- `launcher.py` erweitert:
  - `health` führt jetzt Runtime-Checks aus
  - `modules`/`module-status` liefern Command Index und Registry-Daten
  - `module-health` als expliziter Runtime-Health-Alias ergänzt
  - selektive Modulansicht über `python launcher.py module-status <module>`
- Tests ergänzt:
  - Command Index für P0-Hauptmodule
  - Launcher `modules`
  - Launcher `health` mit temporärem Project Root
  - Registry Command Resolution

## Validierung
- `python launcher.py health`: PASS
- `python launcher.py module-status desktop`: PASS
- `python -m pytest -q`: 231 passed

## Status
P0 Fortschritt: Launcher/Registry/Health sind jetzt konsistenter. Nächster P0-Block bleibt echte gemeinsame Config/Event-Bus-Verdrahtung über alle Module.

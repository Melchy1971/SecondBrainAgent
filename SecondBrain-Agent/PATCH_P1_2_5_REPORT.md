# PATCH P1.2.5 – Connector Lifecycle Orchestration

## Ziel
Die bisherigen Connector-Bausteine aus P1.2.1 bis P1.2.4 werden zu einem ausführbaren Lifecycle-Service verbunden.

## Geändert

### Neu
- `secondbrain/connectors/adapter_lifecycle.py`
- `tests/test_p1_2_5_connector_lifecycle.py`

## Enthaltene Fähigkeiten
- `ConnectorLifecycleRegistry` für Adapter-Registrierung
- Duplicate-Schutz beim Registrieren
- Enable/Disable von Connectoren
- `ConnectorLifecycleService` als Orchestrierungsschicht
- Adaptervertrag aus `adapter_contract.py` wird vor Nutzung validiert
- Cursor-State wird nur bei erfolgreichem oder partiellem Lauf geschrieben
- Fetch-Fehler stoppen den Lauf ohne Cursor-Fortschritt
- Item-Fehler werden isoliert und in Dead-Letter-Queue geschrieben
- Source-Mismatch wird blockiert und nicht verarbeitet
- Health-Reporting nach jedem Lauf
- `run_enabled()` für alle aktivierten Connectoren

## Validierung
- Einzeltest: `7 passed`
- Volltest: `467 passed in 15.06s`

## Release-Wirkung
- Connectoren sind nicht mehr nur Einzelmodule, sondern über einen stabilen Lifecycle ausführbar.
- Fehlerpfade sind messbar, isoliert und cursor-sicher.
- Neue echte Adapter können später gegen denselben Vertrag registriert werden.

## Nächster Schritt
P1.2.6 – konkrete File-System/Local-Folder Adapter-Implementierung als erster echter produktionsnaher Connector.

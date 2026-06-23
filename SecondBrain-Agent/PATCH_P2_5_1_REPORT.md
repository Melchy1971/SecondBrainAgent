# PATCH P2.5.1 – Connector Center Foundation

## Ziel
Desktop Connector-Center als bedienbare Foundation bereitstellen.

## Enthalten
- Connector-Statusmodell
- Connector-Descriptor und Config-Modell
- Connector-Registry
- Connector-Konfigurationsspeicher
- Connector-Center-Service
- Sync-Action-Fassade
- Health-Snapshot
- Secret-sanitized View-Model
- Tests für Registrierung, Konfiguration, Sync, Health, Fehlerpfad und Persistenz

## Geänderte/Neue Dateien
- `secondbrain/desktop/connectors/__init__.py`
- `secondbrain/desktop/connectors/connector_models.py`
- `secondbrain/desktop/connectors/connector_registry.py`
- `secondbrain/desktop/connectors/connector_config_store.py`
- `secondbrain/desktop/connectors/connector_actions.py`
- `secondbrain/desktop/connectors/connector_center_service.py`
- `tests/desktop/connectors/test_connector_center.py`
- `pytest.ini`

## Validierung
`7 passed in 0.27s`

## Ergebnis
P2.5.1 ist als Delta abgeschlossen.

# PATCH P2.5.2 — Connector Configuration

## Inhalt

- Validiertes Connector-Konfigurationsschema
- Feldtypen: Text, Boolean, Integer, Select, Secret
- Secret-Referenzen nur als `secret://...`
- Enable-/Disable-Flows im Connector-Center
- Sanitized Config View ohne Secret-Leakage
- Tests für Validierung, Fehlerpfade und Toggle-Flows

## Geänderte/Neue Dateien

- `secondbrain/desktop/connectors/connector_configuration.py`
- `secondbrain/desktop/connectors/connector_center_service.py`
- `secondbrain/desktop/connectors/__init__.py`
- `tests/desktop/connectors/test_connector_configuration.py`

## Validierung

- `10 passed in 0.28s`

# PATCH P1.2.4 – Connector Adapter Contract

## Ziel
Connector-Sync produktionsnäher machen, indem externe Adapter nicht mehr beliebige Vendor-Payloads in die Pipeline geben, sondern einen stabilen internen Vertrag erfüllen.

## Geändert

### Neu
- `secondbrain/connectors/adapter_contract.py`
- `tests/test_p1_2_4_connector_adapter_contract.py`

## Enthaltene Fähigkeiten
- `ConnectorItem` als normalisiertes internes Connector-Datenmodell
- `ConnectorAdapter` Protocol für Adapter-Vertrag
- stabile `ConnectorErrorCode` Fehlerklassen
- `ConnectorContractError` für Validierungsfehler
- `normalize_item()` mit Alias-Support für Gmail/Drive/File-nahe Payloads
- `parse_datetime()` mit UTC-Normalisierung
- `validate_adapter()` zur frühen Contract-Prüfung
- deterministischer `content_hash` für spätere Incremental-Sync-Entscheidungen

## Validierung
- `6 passed`

## Release-Wirkung
- reduziert Kopplung zwischen externen APIs und interner Sync-/RAG-Pipeline
- verhindert technische Vendor-Felder in nachgelagerten Services
- schafft stabile Basis für echte Gmail/Drive/File/Notion-Adapter

## Nächster Schritt
P1.2.5 – Connector Registry + Adapter Lifecycle.

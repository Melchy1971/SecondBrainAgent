# PATCH P1.2.6 — Connector Import Bridge

## Ziel
Connector-Sync-Ergebnisse werden in ingestion-fähige Dokument-Importaufträge überführt.

## Geänderte Dateien
- `secondbrain/connectors/import_bridge.py`
- `tests/test_p1_2_6_connector_import_bridge.py`

## Implementiert
- `ConnectorImportJob` als stabiler Ingestion-Vertrag
- deterministische `job_id` für Idempotenz
- stabile `document_key` für gleiche Quelle/External-ID über Inhaltsänderungen hinweg
- `ImportJobSink` Protocol
- `InMemoryImportJobSink` für Tests und lokale Läufe
- `ConnectorImportBridge` mit Filter, Submit, Snapshot
- `run_connector_import()` als Lifecycle-Integration
- `summarize_import_run()` für Release-/Health-Gates
- Fehlerisolation über bestehende Lifecycle-Dead-Letter-Mechanik

## Validierung
- `6 passed`

## Nächster sinnvoller Schritt
P1.2.7 — echte Adapter-Stubs für lokale Dateien/Gmail/Drive mit einheitlichem Contract.

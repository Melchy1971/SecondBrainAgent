# PATCH P1.2.7 - Connector Index Bridge

## Ziel
Connector-Importjobs aus P1.2.6 werden in inkrementelle RAG-Indexierung überführt.

## Geänderte Dateien
- `secondbrain/connectors/index_bridge.py`
- `tests/test_p1_2_7_connector_index_bridge.py`

## Inhalt
- `ConnectorIndexDocument` als normalisiertes RAG-Dokument
- `ConnectorIndexBridge` für ImportJob → DocumentSnapshot → ReindexService
- `IndexDocumentSink` als Boundary für echte Chunk-/Vector-Indexierung
- `InMemoryIndexDocumentSink` für Tests und Dry-Run
- Skip-Logik für nicht importierte Jobs
- Reindex bei Content-Hash-Änderung
- Delete-Pfad für gelöschte Connector-Dokumente
- Snapshot-Metriken für Release-Gates

## Risiko reduziert
- Connector-Items bleiben nicht mehr nur Sync-/Import-Metadaten.
- Geänderte Inhalte erzeugen deterministisch Reindex-Operationen.
- Unveränderte Inhalte werden ohne Vektor-Neuberechnung übersprungen.
- Indexfehler werden pro Dokument isoliert und messbar.

## Validierung
- `tests/test_p1_2_7_connector_index_bridge.py`: 6 passed
- Vollständiger Testlauf im Delta-Arbeitsstand: siehe Antwortnachricht

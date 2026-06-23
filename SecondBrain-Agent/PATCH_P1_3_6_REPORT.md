# PATCH P1.3.6 - Ingestion Pipeline Orchestration

## Ziel
Parser-Orchestrierung, Ingestion-Quality-Gate und Text-Ingestion-Runtime zu einem deterministischen Service verbinden.

## Geänderte Dateien
- `secondbrain/document_understanding/ingestion_pipeline.py`
- `secondbrain/document_understanding/__init__.py`
- `tests/test_p1_3_6_ingestion_pipeline.py`

## Implementiert
- `DocumentIngestionPipeline`
- `IngestionPipelineStatus`
- `IngestionPipelineResult`
- Parser-Ausführung über `MultiFormatParserOrchestrator`
- Quality-Gate-Auswertung vor Side Effects
- Reject ohne Runtime-Aufruf
- Accept/Review mit Runtime-Aufruf
- Legacy-Kompatibilität für `ingest_text(title, text, source_path, mime_type)`
- Metadata-aware Runtime-Unterstützung mit Parser-/Quality-Metadaten
- Fehlerzustand `INGESTION_FAILED` für Runtime-Ausnahmen und `ok=False`

## Validierung
- Pipeline akzeptiert valide Textdateien
- Pipeline rejectet unsupported Dateien ohne Side Effect
- Review-Dokumente werden ingestiert und markiert
- Legacy-Runtime bleibt kompatibel
- Runtime-Fehler werden stabil als Status zurückgegeben

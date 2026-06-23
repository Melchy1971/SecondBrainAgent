# PATCH P1.1.7 - Incremental Reindex

## Ziel
RAG-Index nur für geänderte Dokumente neu aufbauen. Unveränderte Dokumente werden übersprungen, gelöschte Dokumente aus dem Index entfernt.

## Neue Dateien
- `secondbrain/rag/indexing/__init__.py`
- `secondbrain/rag/indexing/change_detector.py`
- `secondbrain/rag/indexing/reindex_service.py`
- `tests/test_p1_1_7_incremental_reindex.py`

## Implementiert
- `DocumentSnapshot` mit stabilem Content-Hash
- `ChangeDetector` mit Aktionen `skip`, `reindex`, `delete`
- `ReindexPlan` mit Summary-Zählern
- `ReindexService` zur Anwendung des Plans
- `InMemoryIndexRepository` für lokale Tests/Fallback
- Hash-Normalisierung für CRLF/LF

## Validierung
- Einzeltest: `3 passed in 0.55s`
- Volltest: `436 passed in 20.79s`

## Risiko
- Persistente DB-Anbindung ist noch nicht Bestandteil dieses Delta-Pakets.
- Chunk-/Vector-Löschung ist über Repository-Kontrakt vorbereitet, aber konkrete pgvector-Implementierung folgt separat.

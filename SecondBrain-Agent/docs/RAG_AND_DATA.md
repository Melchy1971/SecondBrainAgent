# RAG, Dokumente und Daten

## Aktueller Datenfluss

```text
Datei oder Text
  -> Parser und Source Record
  -> Chunks und Metadaten
  -> Embedding Provider
  -> SQLite oder pgvector RAG Store
  -> Keyword-, Vector- und Hybrid-Suche
  -> Antwort mit Quellen
```

## Kernbefehle

```powershell
python launcher.py p1-rag-status
python launcher.py p1-rag-ingest-file .\sample_docs\demo.md
python launcher.py p1-rag-ingest-dir .\sample_docs
python launcher.py p1-rag-search Jarvis
python launcher.py p1-rag-vector-search Jarvis
python launcher.py p1-rag-hybrid-search Jarvis
python launcher.py p1-rag-answer "Was weiss Jarvis?"
python launcher.py p1-rag-sources
python launcher.py p1-rag-validate
python launcher.py p1-rag-quality
```

## Embeddings und Reindex

```powershell
python launcher.py p1-embedding-config
python launcher.py p1-embedding-status
python launcher.py p1-provider-health
python launcher.py p1-vector-provider-audit
python launcher.py p1-vector-index-repair
python launcher.py p1-rag-reindex --write-report
```

Der lokale deterministische Provider ist fuer Entwicklung und Tests geeignet, aber kein Nachweis produktiver semantischer Qualitaet. Provider, Modell und Dimension bilden gemeinsam die Index-Identitaet; ein Wechsel erfordert Audit und normalerweise Reindex.

## PostgreSQL/pgvector

Relevante Variablen:

- `SECONDBRAIN_PGVECTOR_ENABLED`
- `SECONDBRAIN_PGVECTOR_DSN` oder `DATABASE_URL`
- `SECONDBRAIN_PGVECTOR_SCHEMA`
- `SECONDBRAIN_PGVECTOR_TABLE_PREFIX`
- `SECONDBRAIN_PGVECTOR_DIMENSIONS`

```powershell
python launcher.py p3-pgvector-readiness
python launcher.py p3-pgvector-readiness --live
python launcher.py p3-rag-store-status
python launcher.py p3-p1-store-bridge
```

`--apply` ist eine explizite Schemaaenderung. Vorher SQL-Preview, Ziel-DSN, Backup und Dimensionen pruefen.

## Knowledge Graph und Memory

```powershell
python launcher.py graph-status
python launcher.py graph-ingest-text "Jarvis nutzt RAG"
python launcher.py graph-search Jarvis
python launcher.py graph-neighbors Jarvis
python launcher.py graph-timeline
python launcher.py graph-contradictions
python launcher.py graph-export
```

Graph und Long-Term Memory sind lokale Foundations. Ein produktiver Graph Store, automatische Konsolidierung, Privacy-Klassifizierung und Vergessen sind noch offen.

## KI-Exportimport

Einzelimporte:

```powershell
python scripts\import_chatgpt_export.py "C:\Downloads\chatgpt-export.zip"
python scripts\import_gemini_export.py "C:\Downloads\gemini-export.zip"
python scripts\import_perplexity_export.py "C:\Downloads\perplexity-export.zip"
```

Sammelimport:

```powershell
python scripts\import_ai_exports.py
```

Exporte koennen alternativ in die passenden Unterordner von `SecondBrain-Inbox` gelegt werden. Importer duerfen Quelldaten nicht loeschen; Fehler muessen als Report sichtbar werden.

## Dokumentformate

Text und Markdown sind der stabile Basispfad. PDF, Office, OCR und Tabellen benoetigen optionale Abhaengigkeiten und muessen mit realen Beispieldokumenten qualitaetsgeprueft werden.

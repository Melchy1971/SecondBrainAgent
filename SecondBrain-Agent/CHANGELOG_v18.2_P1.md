# SecondBrain-Agent v18.2 P1

## Ziel
P1-RAG von reiner Such-/Antwortfunktion auf prüfbare Qualitätssicherung und Antwortsicherheitslogik erweitern.

## Änderungen
- `p1-rag-validate` ergänzt.
- `p1-rag-quality` ergänzt.
- Index-Validierung ergänzt:
  - ungültige Quellen
  - leere Dokumenttitel
  - leere Chunks
  - ungültige Zeichenbereiche
  - ungültiges Token-JSON
  - Token-Count-Abweichungen
  - verwaiste Chunks
  - doppelte Content-Hashes
- Antwort-Sicherheitsprüfung ergänzt:
  - Antworten ohne Evidenz müssen explizit `no_evidence` liefern.
  - Antworten mit Evidenz müssen Citations enthalten.
- `p1-gate` auf Schema `secondbrain.p1_gate.v3` gehoben.
- Gate prüft jetzt zusätzlich Index-Validierung und Qualitäts-Policy.
- Reports ergänzt:
  - `runtime/reports/p1_rag_validation_latest.json`
  - `runtime/reports/p1_rag_quality_latest.json`
  - `runtime/reports/p1_gate_latest.json`
- Tests ergänzt: `tests/test_v182_p1_rag_quality.py`.

## Validierung
- `p1-rag-validate --write-report`: PASS
- `p1-rag-quality "RAG Qualität" --write-report`: PASS
- `p1-gate --write-report`: PASS
- `pytest`: 261 passed

## Offene P1-Punkte
- echte Embeddings statt deterministischem TF-IDF
- Hybrid Search mit pgvector/PostgreSQL
- Reranking
- Dokumentparser für PDF/HTML/Office
- Source Trust Model
- Memory-Kompression

# Performance Report - v30.97

- Zeitpunkt: 2026-07-14T10:01:57+00:00
- Gate: **PASS** (Schwelle 10.0 %, 0 verglichen)
- Baseline: keine (erste Messung = neue Baseline)
- psutil: ja
- Cases: 5 gemessen, 9 benoetigen Dienste, 0 Fehler

## Messwerte

| Komponente | Case | Status | Zeit/Iter (ms) | CPU % | RAM Δ (MB) | IO R (KB) | IO W (KB) | DB (ms) | Δ Baseline % |
|---|---|---|---|---|---|---|---|---|---|
| Chunking | chunk_text_23k_chars | ok | 0.0166 | 0 | 0 | 0 | 0 | 0 | — |
| Approval | create_and_transition | ok | 2.105 | 114 | 0.242 | 0 | 1520 | 0 | — |
| Memory | extract_and_submit | ok | 0.3608 | 110.9 | 0.143 | 0 | 24 | 0 | — |
| Agent Planner | create_chat_plan | ok | 0.0066 | 0 | 0 | 0 | 0 | 0 | — |
| Metriken | export | ok | 0.4254 | 0 | 0.049 | 0 | 0 | 0 | — |
| Import | import_pipeline | requires_service | — | — | — | — | — | — |  |
| OCR | ocr_extract | requires_service | — | — | — | — | — | — |  |
| Embedding | embed_batch | requires_service | — | — | — | — | — | — |  |
| Vector Search | vector_topk | requires_service | — | — | — | — | — | — |  |
| Hybrid Search | hybrid_topk | requires_service | — | — | — | — | — | — |  |
| GUI | render_native_gui | requires_service | — | — | — | — | — | — |  |
| Connector Sync | connector_incremental_sync | requires_service | — | — | — | — | — | — |  |
| Dashboard | dashboard_snapshot | requires_service | — | — | — | — | — | — |  |
| RAG | rag_answer | requires_service | — | — | — | — | — | — |  |

## Benoetigen Dienste (auf provisionierter Maschine messen)

- Import / import_pipeline: PostgreSQL + Datei-/AI-Import-Pipeline
- OCR / ocr_extract: OCR-Engine (Tesseract/PaddleOCR)
- Embedding / embed_batch: Ollama/OpenAI Embedding-Provider
- Vector Search / vector_topk: pgvector
- Hybrid Search / hybrid_topk: pgvector + Embeddings + BM25
- GUI / render_native_gui: Tk-Display
- Connector Sync / connector_incremental_sync: Connector-Credentials
- Dashboard / dashboard_snapshot: native Desktop-Runtime
- RAG / rag_answer: Embeddings + Vector Store

## History

- Laeufe insgesamt: 1

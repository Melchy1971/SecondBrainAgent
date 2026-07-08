# Release Notes v30.40 – Native Dashboard Center

## Neu
- Native Dashboard Center
- Runtime-Snapshot für Desktop, PostgreSQL/pgvector, Embeddings, Security und native Module
- Aktivitätsprotokoll unter `runtime/native/dashboard_center/dashboard_activity.jsonl`
- Dashboard-GUI mit Statuskarten und Detailansicht
- Integration in AI Workspace Navigation

## Validierung
- `pytest tests/test_v3040_native_dashboard_center.py -q`
- `python -m compileall secondbrain/native/dashboard_center secondbrain/native/ai_workspace launcher.py`

# v30.13 P1 Golden Quality Gate

## Ziel
Golden Retrieval nicht nur als technischer Such-Smoke, sondern als fachliches Qualitätsgate nutzen.

## Änderungen
- `p1_golden_retrieval` auf Schema v2 angehoben.
- Trennung von `technical_ok` und `quality_ok`.
- `min_hit_count` je Golden Query ergänzt.
- optionale `expected_sources` und `expected_titles` ergänzt.
- Lineage-Prüfung für erwartete Quellen/Titel ergänzt.
- Failure-Reasons je Query ergänzt.
- Production Gate zeigt Golden-Metriken detaillierter: Passrate, Recall, MRR, nDCG, Technical/Quality OK.
- `config/golden_retrieval.json` um Quality Policy erweitert.

## Akzeptanz
- `p1-golden-eval` blockiert fachliche Qualitätsfehler auch dann, wenn die Suche technisch ausführbar ist.
- `p1-production` kann Retrieval-Qualität, Provider-Reife und Vector-Audit getrennt reporten.

## Validierung
- `pytest --collect-only -q` -> 996 Tests gesammelt.
- Fokus-Suite: `tests/test_v3013_p1_golden_quality_gate.py` + `tests/test_v3012_p1_provider_health_gate.py` -> 10 PASS.

## Bekannte offene Punkte
- Volltest ohne Sandbox-Timeout noch offen.
- Live-VPS pgvector Migration/Audit noch offen.
- Produktiver Semantic-Embedding-Provider noch offen.

# SecondBrain-Agent v8.0

SecondBrain OS Ausbau auf Basis v6.4.1.

## Neu in v8.0

- Semantic Search Engine
- Hybrid Search Index
- Full Knowledge Graph
- Agent Memory v2
- Project Intelligence
- Decision Intelligence v2
- Meeting Intelligence v2
- Calendar Intelligence
- Personal Data Warehouse v2
- MCP Ecosystem Registry
- Digital Twin v5
- Self-Improving Knowledge System
- SecondBrain OS Dashboard

## Start

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\menu.py
```

## Wichtigster Lauf

```powershell
python scripts\run_secondbrain_os_cycle.py
```

## Sicherheitsmodell

- keine destruktiven Änderungen
- keine externen Aktionen ohne Aktivierung
- alle Ergebnisse als Markdown
- Markdown bleibt Source of Truth

## v10.4/v10.5 Foundation

Neu ergänzt in diesem Paket:

- `secondbrain/runtime_events_v104.py`
- `secondbrain/normalizer_v104.py`
- `secondbrain/connector_runtime_v104.py`
- `secondbrain/ai_runtime_v105.py`
- `scripts/run_v104_connector_sync.py`
- `scripts/run_v105_ai_runtime.py`
- `docs/CONNECTOR_RUNTIME_v10.4.md`
- `docs/AI_RUNTIME_v10.5.md`

Validierung:

```bash
pytest -q tests/unit/test_runtime_v104_v105.py tests/test_smoke.py
python scripts/run_v104_connector_sync.py
python scripts/run_v105_ai_runtime.py
```

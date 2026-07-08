# Delta v30.64 anwenden – Agent Memory Injection

## 1. Dateien übernehmen

Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren, bestehende Dateien überschreiben.

Neu:

- `secondbrain/agent/memory_injection/__init__.py`
- `secondbrain/agent/memory_injection/models.py`
- `secondbrain/agent/memory_injection/budget.py`
- `secondbrain/agent/memory_injection/filters.py`
- `secondbrain/agent/memory_injection/ranking.py`
- `secondbrain/agent/memory_injection/conflicts.py`
- `secondbrain/agent/memory_injection/injector.py`
- `secondbrain/agent/memory_injection/audit.py`
- `secondbrain/agent/memory_injection/service.py`
- `secondbrain/agent/memory_injection/cli.py`
- `tests/_mem_helpers.py`
- `tests/test_memory_injection.py`
- `tests/test_memory_budget.py`
- `tests/test_memory_privacy.py`
- `tests/test_memory_conflicts.py`
- `docs/releases/v30_64_memory_injection.md`

Geändert:

- `launcher.py` (Dispatch `agent-memory-*`)
- `README_PATCH.md`, `RELEASE_NOTES.md`

## 2. Qualität prüfen

```powershell
python -m compileall .
pytest -q
```

Gezielt:

```powershell
pytest tests/test_memory_injection.py tests/test_memory_budget.py tests/test_memory_privacy.py tests/test_memory_conflicts.py -q
```

Erwartung: 25 passed. Zielinterpreter Python 3.11+.

## 3. Funktion prüfen

`mem.json` (Beispiel):

```json
[
 {"text":"Die SAP Migration hat hohe Prioritaet","visibility":"public","metadata":{"source":"wiki-1"}},
 {"text":"Der API Key ist sk-abcdefghijklmnop1234","metadata":{"source":"leak"}},
 {"text":"Privater Hinweis","visibility":"private","metadata":{"source":"note-9"}}
]
```

```powershell
python launcher.py agent-memory-preview --query "SAP" --memories mem.json --privacy
python launcher.py agent-memory-inject  --query "SAP" --memories mem.json --agent-id agent-7
python launcher.py agent-memory-audit   --agent-id agent-7
```

## 4. Hinweise

- **Keine zweite Memory Engine**: liest die bestehende `secondbrain.agent.memory` (`InMemoryMemoryStore`).
- Sicherheitsreihenfolge: Secrets → Privacy → Quellenpflicht → Ranking → Budget → Konflikte.
- Der Secret-Detektor ist bewusst streng (Textmuster inkl. lange Hex-Blobs) – im Zweifel Ausschluss.
- Audit unter `runtime/agent/memory_injection/audit.jsonl`; nur `inject` schreibt, `preview` nicht.

# Delta v30.68 anwenden – Reasoning Engine

## 1. Dateien übernehmen

Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren, bestehende Dateien überschreiben.

Neu:

- `secondbrain/agent/reasoning/__init__.py`
- `secondbrain/agent/reasoning/models.py`
- `secondbrain/agent/reasoning/evidence.py`
- `secondbrain/agent/reasoning/session.py`
- `secondbrain/agent/reasoning/history.py`
- `tests/test_reasoning.py`
- `tests/test_evidence.py`
- `tests/test_decisions.py`
- `docs/releases/v30_68_reasoning_engine.md`

Geändert: `README_PATCH.md`, `RELEASE_NOTES.md`.

Kein Launcher-/GUI-Eingriff (Library-Ebene, wie im Auftrag).

## 2. Qualität prüfen

```powershell
python -m compileall .
pytest -q
```

Gezielt:

```powershell
pytest tests/test_reasoning.py tests/test_evidence.py tests/test_decisions.py -q
```

Erwartung: 22 passed. Zielinterpreter Python 3.11+.

## 3. Nutzung

```python
from secondbrain.agent.reasoning import ReasoningSession
from secondbrain.agent.reasoning.models import Evidence, SUPPORT

s = ReasoningSession("Postgres oder SQLite?", project_root=".")
s.think("intern: Skalierung + Team-Know-how")             # Chain of Thought (intern)
dec = s.decide("DB-Wahl", ["Postgres", "SQLite"], evidence_by_option={
    "Postgres": [Evidence.create("skaliert", source="wiki", confidence=0.9, stance=SUPPORT),
                 Evidence.create("Team-Know-how", source="team", confidence=0.8, stance=SUPPORT)],
    "SQLite":   [Evidence.create("einfach", source="blog", confidence=0.4, stance=SUPPORT)],
})
# dec.chosen, dec.confidence, dec.evidence, dec.sources, dec.alternatives, dec.risk,
# dec.uncertainties, dec.conflicts
s.save()   # ReasoningHistory: runtime/agent/reasoning/history.jsonl
```

## 4. Hinweise

- Keine zweite Agent-/Memory-Engine: Evidenz kommt über die v30.64 `MemoryInjector`; Konflikte über den v30.64 `MemoryConflictDetector`.
- Deterministisch, kein LLM-Aufruf: strukturiert und auditiert den Lösungsprozess.
- Jede Entscheidung trägt Confidence, Evidence, Sources, Alternatives, Risk (+ uncertainties, conflicts).

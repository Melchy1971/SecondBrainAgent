# Delta v30.70 anwenden – ToolChain

## 1. Dateien übernehmen

Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren, bestehende Dateien überschreiben.

Neu:

- `secondbrain/agent/toolchain/__init__.py`
- `secondbrain/agent/toolchain/models.py`
- `secondbrain/agent/toolchain/executor.py`
- `secondbrain/agent/toolchain/visual.py`
- `secondbrain/agent/toolchain/chain.py`
- `tests/_toolchain_fakes.py`
- `tests/test_toolchain.py`
- `tests/test_toolchain_control_flow.py`
- `tests/test_toolchain_recovery.py`
- `docs/releases/v30_70_toolchain.md`

Geändert: `README_PATCH.md`, `RELEASE_NOTES.md`.

Kein Launcher-/GUI-Eingriff (Library-Ebene).

## 2. Qualität prüfen

```powershell
python -m compileall .
pytest -q
```

Gezielt:

```powershell
pytest tests/test_toolchain.py tests/test_toolchain_control_flow.py tests/test_toolchain_recovery.py -q
```

Erwartung: 20 passed. Zielinterpreter Python 3.11+.

## 3. Nutzung

```python
from secondbrain.agent.toolchain import ToolChain, ToolChainExecutor, ToolStep

ch = (ToolChain("import_und_index")
      .tool("fetch", output_var="doc", max_attempts=3, fallback=ToolStep.create("fetch_cache"))
      .conditional({"var": "doc", "op": "truthy"},
                   then_steps=[ToolStep.create("index", rollback_tool="deindex")])
      .foreach("chunks", body=[ToolStep.create("embed", inputs={"c": "$item"})]))

ex = ToolChainExecutor(project_root)            # nutzt ToolRegistry.run
run = ex.run(ch, {"chunks": [1, 2, 3]})         # run.status / run.results / run.rolled_back
print(ch.visualize().mermaid())                 # Visual Workflow
```

## 4. Hinweise

- Tools laufen über die bestehende `ToolRegistry` (`ToolRegistry.run`); kein zweiter Executor.
- Fehlerbehandlung je ToolStep: Retry → Fallback → (Chain) Rollback der abgeschlossenen kompensierbaren Schritte (umgekehrte Reihenfolge).
- `max_iterations` schützt While-/Foreach-Schleifen; `rollback_on_error=False` deaktiviert Kompensation.
- Abgrenzung zur v30.62 Workflow Engine: ToolChain ist leichtgewichtige in-memory Tool-Komposition mit reichem Kontrollfluss + Visualisierung; die Workflow Engine bleibt für checkpoint-/approval-/crash-sichere Plan-Ausführung.

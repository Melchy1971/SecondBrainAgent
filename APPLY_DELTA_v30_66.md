# Delta v30.66 anwenden – Native Agent Control GUI

## 1. Dateien übernehmen

Inhalt aus `SecondBrain-Agent/` in dein Projektverzeichnis `SecondBrain-Agent/` kopieren, bestehende Dateien überschreiben.

Neu:

- `secondbrain/native/agent_control/__init__.py`
- `secondbrain/native/agent_control/service.py`
- `secondbrain/native/agent_control/gui.py`
- `secondbrain/native/agent_control/cli.py`
- `tests/test_agent_control_gui.py`
- `tests/test_agent_workspace_integration.py`
- `docs/releases/v30_66_native_agent_control_gui.md`

Geändert:

- `secondbrain/native/ai_workspace/service.py` (Modul `agent_control` registriert)
- `launcher.py` (Dispatch `agent-control-center*`)
- `README_PATCH.md`, `RELEASE_NOTES.md`

## 2. Qualität prüfen

```powershell
python -m compileall .
pytest -q
```

Gezielt:

```powershell
pytest tests/test_agent_control_gui.py tests/test_agent_workspace_integration.py -q
```

Erwartung: 14 passed. Zielinterpreter Python 3.11+.

## 3. Funktion prüfen

```powershell
python launcher.py agent-control-center
python launcher.py agent-control-plan-create --goal "Importiere test.pdf"
python launcher.py agent-control-area plans
python launcher.py ai-workspace-navigation   # enthält agent_control
python launcher.py agent-control-center-gui   # Panel (benötigt Tkinter)
```

## 4. Hinweise

- Keine zweite GUI: der AI Workspace wird um das Modul `agent_control` erweitert; bestehende Module bleiben unverändert.
- Keine zweite Engine: alle Bereiche/Aktionen komponieren die Bestands-Subsysteme (Planner, Workflow, Background Agents, Safety/Approvals, Goals).
- Jeder Bereich degradiert defensiv (Fehler-Stub) statt die Oberfläche zu brechen.
- GUI-Logik ist UI-frei über `view_model()`/`build_tabs()` getestet; Tkinter wird lazy importiert.

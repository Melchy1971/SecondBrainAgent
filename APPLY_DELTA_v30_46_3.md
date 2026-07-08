# APPLY DELTA v30.46.3 - AI Workspace (Vier-Zonen-Shell)

## Inhalt

- Die bestehende Desktop-GUI (`AIWorkspaceApp`) wird zum AI Workspace;
  keine neue GUI, keine zweite Navigation, keine zweite Toolbar.
- LINKS: bestehende Modul-Navigation (Dashboard, Workspace, Dokumente,
  Memory, Agenten, Voice, weitere Module).
- MITTE: Conversation / Streaming / Markdown (`AIChatWorkspaceFrame`,
  jetzt reines Transkript-Panel mit Kontextquellen-Auswahl).
- RECHTS: Notebook mit Quellen (Zitat-Tabelle), Memory, Dokumente
  (Auswahl + Anhaenge), Runtime (`WorkspaceRightPanel`).
- UNTEN: eine Leiste mit Prompt, Anhaengen, Sprache, Provider/Modell
  (`WorkspaceBottomBar`); Sprache springt in das bestehende Voice-Modul.
- Neue UI-freie Panel-Modelle in `secondbrain/native/ai_workspace/panels.py`
  (ChatPanel, SourcePanel, MemoryPanel, DocumentPanel, RuntimePanel,
  PromptBar) — headless testbar, konsumieren CitationRenderer und
  ApplicationState aus dem Bestand.

## Neue Tests

```text
tests/test_workspace_gui.py     Vier-Zonen-Shell (Tk-Smoke mit Display-Skip)
tests/test_chat_panel.py        Transkript-Markdown + Zitat-Extraktion
tests/test_runtime_panel.py     Runtime-Snapshot/Zeilen
tests/test_source_panel.py      Quellen-/Memory-/Dokument-Zeilen
```

## Akzeptanz

```bash
python -m compileall .
pytest -q
python launcher.py gui-doctor
python launcher.py native-desktop-health
```

# PATCH P2.1.6 — Workspace Persistenz und Multi-Workspace-Support

## Ziel
Desktop-Zustand und Datenpfade werden pro Workspace trennbar. Der Desktop erhält eine persistente Workspace-Registry mit Default-Workspace, aktivem Workspace und robustem Umschalten.

## Geänderte/Neue Dateien

- `secondbrain/desktop/workspace_manager.py`
- `secondbrain/desktop/workspaces/__init__.py`
- `secondbrain/desktop/workspaces/workspace_state.py`
- `secondbrain/desktop/workspaces/workspace_store.py`
- `secondbrain/desktop/workspaces/workspace_registry.py`
- `tests/desktop/workspaces/test_workspace_registry.py`
- `tests/desktop/workspaces/test_workspace_manager.py`

## Umsetzung

- `WorkspaceRef` als serialisierbares Workspace-Modell
- `WorkspaceStore` für JSON-Persistenz
- `WorkspaceRegistry` mit Default-Workspace, Duplikatprüfung, Remove-Schutz und Switch-Tracking
- `WorkspaceManager` als Desktop-Fassade
- Pfadauflösung relativ zum aktiven Workspace

## Validierung

```text
6 passed in 0.31s
```

## Ergebnis

P2.1 Desktop Foundation unterstützt jetzt mehrere Workspaces mit persistenter Registry und aktivem Workspace.

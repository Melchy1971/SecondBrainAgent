# v30.48 - Projekte im AI Workspace

- Der bestehende `desktop_pro.ProjectCenter` bleibt der einzige Projektkatalog.
- Der AI Workspace integriert Projekte, Workspaces, Favoriten, Tags, Archiv und Papierkorb.
- Suche und Filter arbeiten auf demselben Projektbestand.
- Benutzer, Rollen und Rechte verwenden das bestehende RBAC mit persistenter Ablage.
- JSON-Import und -Export sind direkt im eingebetteten Workspace-Panel erreichbar.

Validierung: `python -m compileall .` und `pytest`.

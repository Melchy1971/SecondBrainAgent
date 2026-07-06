# APPLY DELTA v30.60 – Unified Tool Registry

## Ergebnis

Jarvis verwendet genau eine `ToolRegistry` und einen gemeinsamen Toolvertrag. Die früheren Importpfade `secondbrain.tool_registry_v121` und `secondbrain.agent.tools.tool_registry` sind reine Kompatibilitätsimporte derselben Implementierung.

## Toolvertrag

- `ToolDefinition`
- `ToolInputSchema`
- `ToolResult`
- `ToolRiskLevel`
- `ToolCapability`
- `ToolRegistry`
- `ToolDiscovery`
- `ToolHealth`

Definitionen enthalten Name, Beschreibung, Kategorie, Input-/Output-Schema, Risiko, Approval-Anforderung, Enable-Status und Handler. Der vorhandene v121-Manifest- und Audit-Pfad unter `runtime/tools_v121` bleibt erhalten.

## Entdeckte Bestandsmodule

Suche, Dokumente, Import, Memory, Agenten, Jobs, Notifications, Settings, Voice, Updates, GitHub und Filesystem werden über bestehende Services eingebunden. Schreibende Tools sind approval-pflichtig; Filesystem-Zugriffe bleiben auf den Projektordner begrenzt.

## Launcher

```powershell
python launcher.py tool-list
python launcher.py tool-show search.query
python launcher.py tool-health
python launcher.py tool-run filesystem.list '{"path":"."}'
python launcher.py tool-disable memory.add
python launcher.py tool-enable memory.add
```

## Validierung

```powershell
python -m compileall .
pytest -q
python launcher.py repo-doctor
```

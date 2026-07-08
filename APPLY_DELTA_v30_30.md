# APPLY_DELTA_v30_30.md

## Paket

`SecondBrainAgent_delta_v30_30_native_workspace_center.zip`

## Zweck

Rekonstruktion des fehlenden v30.30-Deltas: Native Workspace Center.

## Einspielen

ZIP im Repository-Root entpacken. Erwartete Struktur:

```text
SecondBrain-Agent/secondbrain/native/workspace_center.py
SecondBrain-Agent/secondbrain/native/workspace_center_gui.py
SecondBrain-Agent/tests/test_v3030_native_workspace_center.py
SecondBrain-Agent/docs/releases/v30_30_native_workspace_center.md
SecondBrain-Agent/launcher.py
```

## Prüfen

```bash
cd SecondBrain-Agent
python launcher.py workspace-status
python launcher.py workspace-open documents
python launcher.py workspace-log "v30.30 geprüft" --section developer --kind validation
pytest tests/test_v3030_native_workspace_center.py -q
```

## Neue Startbefehle

```bash
python launcher.py workspace
python launcher.py workspace-status
python launcher.py workspace-activity
```

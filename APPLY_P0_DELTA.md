# P0 Delta anwenden

Kopiere den Inhalt dieses ZIPs in die Repository-Wurzel. Danach die Pfade aus `DELTA_MANIFEST_P0.json.delete_paths` löschen.

Validierung:

```bash
cd SecondBrain-Agent
python scripts/p0_cleanup_artifacts.py --project-root .
python launcher.py repo-doctor --execute-runtime-checks
pytest --collect-only -q
pytest -q
```

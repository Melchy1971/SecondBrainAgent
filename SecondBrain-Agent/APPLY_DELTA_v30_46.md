# APPLY DELTA v30.46 - Native Desktop Health Gate

## Akzeptanz
```bash
python launcher.py native-desktop-health
python launcher.py job-queue-status
python -m pytest tests/test_v3046_native_desktop_health.py -q
python -m compileall -q launcher.py secondbrain tests
```

Status und Doctor bleiben read-only. Nur `native-desktop-report` schreibt einen Bericht.

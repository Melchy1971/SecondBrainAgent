# Patch: fehlende v9 Scripts

## Zielordner

Diese ZIP in folgenden Ordner entpacken:

```text
H:\SecondBrainAgent\SecondBrain-Agent
```

Danach müssen vorhanden sein:

```text
H:\SecondBrainAgent\SecondBrain-Agent\scripts\release_gate_v9.py
H:\SecondBrainAgent\SecondBrain-Agent\scripts\run_regression_tests_v9.py
```

## Test

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\release_gate_v9.py
python scripts\run_regression_tests_v9.py
```

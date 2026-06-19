# v10.6 Delta Package

Dieses Paket baut auf `SecondBrain_OS_v10.5_Foundation_Code.zip` auf.

## Neu

- Agent Kernel
- Persistenter Agent State
- JSONL Job Queue
- Permission Policy
- Approval Gate
- Desktop Quick Capture
- Desktop Notification Log
- Smoke Runner
- Unit Tests

## Ausführen

```bash
cd SecondBrain-Agent
python scripts/run_v106_agent_kernel.py
python -m pytest tests/unit/test_runtime_v106.py
```

## Erwartung

```text
4 passed
{'processed': 1, 'failed': 0, 'blocked': 0}
```

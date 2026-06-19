# SecondBrain OS v10.7 – Security & Governance Layer

## Zweck
v10.7 verhindert, dass Agenten, Desktop-Kommandos oder Connectoren Aktionen ohne Governance ausführen.

## Pipeline

```text
Command / Agent Job
↓
Policy Engine
↓
Risk Scorer
↓
Approval Store
↓
Audit Logger
↓
Handler Execution
```

## Sicherheitslogik

| Level | Bedeutung | Default |
|---|---|---|
| 1 | Read | erlaubt |
| 2 | Write | erlaubt |
| 3 | Execute | blockiert oder approvalpflichtig |
| 4 | System | blockiert |

## Neue Dateien

```text
secondbrain/security_v107.py
secondbrain/secure_agent_kernel_v107.py
config/security_v107.yaml
scripts/run_v107_security_gate.py
tests/unit/test_security_v107.py
```

## Risiko-Scoring

Ein Score entsteht aus:

- Berechtigungslevel
- destruktiver Aktion
- externem Seiteneffekt
- Secret Detection
- PII Detection

Ab Score 60 wird Approval verlangt. Ab Score 95 wird blockiert.

## Audit

Audit-Events landen als JSONL in:

```text
SecondBrain/99_System/security/audit_v107.jsonl
```

Secrets werden vor dem Schreiben redacted.

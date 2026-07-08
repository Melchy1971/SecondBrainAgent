# v30.61 – Agent Approval & Safety Layer

## Zweck

Zentrale Freigabe- und Sicherheitslogik für riskante Agent-Aktionen. Jede riskante Aktion wird klassifiziert, gegen eine Policy geprüft und – falls nötig – über die **bestehende** native Approval Queue zur Freigabe gestellt. Es wird **keine zweite Queue** eingeführt.

## Wiederverwendete Bestandsobjekte

| Objekt | Datei | Rolle |
|--------|-------|-------|
| `NativeApprovalQueue` | `secondbrain/native/approval.py` | Kanonische Approval Queue (`runtime/native/approval_queue.jsonl`) |
| `NativeActionAuditLog` | `secondbrain/native/approval.py` | Gemeinsamer Audit-Trail (`runtime/native/action_audit.jsonl`) |
| `ApprovalRequest` | `secondbrain/native/approval.py` | Datensatz-Schema – aus der Safety-Schicht re-exportiert, nicht neu definiert |

`NativeApprovalQueue.create()` wurde rückwärtskompatibel um die optionalen Keyword-Argumente `risk_level` und `reason` erweitert. Bestehende Aufrufer (u.a. `AgentPlanService`) bleiben unverändert; ohne die neuen Argumente entsteht exakt der bisherige Datensatz.

## Neue Komponenten

Modul: `secondbrain/agent/safety/`

| Klasse | Datei | Aufgabe |
|--------|-------|---------|
| `RiskClassifier` | `risk.py` | Aktion → Risk Level |
| `SafetyPolicy` | `policy.py` | Risk Level → `allow` / `require_approval` / `block` |
| `ActionGuard` | `guard.py` | Einstiegspunkt: klassifiziert, prüft Policy, stellt bei Bedarf einen Approval-Request in die bestehende Queue |
| `SafetyService` | `guard.py` | Approval-Lebenszyklus: request / approve / reject / expire / audit / policy_check |
| `ApprovalAudit` | `audit.py` | Schreibt Safety-Events in den gemeinsamen native Audit-Trail |
| `ApprovalDecision`, `GuardDecision`, `PolicyVerdict` | `models.py`, `policy.py` | Value Objects der Entscheidungen |

## Risk Levels

Vertragliche Reihenfolge (aufsteigendes Risiko):

`read` → `low` → `medium` → `high` → `destructive` → `external`

Default-Zuordnung der freigabepflichtigen Aktionen:

| Aktion | Risk Level | Default-Verdikt |
|--------|-----------|-----------------|
| Dateiänderung (`file.write`, `file.modify`) | `medium` | require_approval |
| Löschaktion (`file.delete`, `delete`) | `destructive` | require_approval |
| Externe API (`api.external`, `http.request`) | `external` | require_approval |
| E-Mail senden (`email.send`) | `high` | require_approval |
| Kalender ändern (`calendar.modify`) | `high` | require_approval |
| Datenbankmigration (`db.migrate`) | `destructive` | require_approval |
| Index-Reparatur (`index.repair`) | `high` | require_approval |
| Bulk Import (`import.bulk`) | `high` | require_approval |
| Shell Command (`shell.exec`) | `destructive` | require_approval |
| Lesen/Status (`file.read`, `status`, …) | `read` | allow |

`read` und `low` laufen ohne Freigabe. Alles ab `medium` ist freigabepflichtig. Unbekannte Aktionen fallen auf `low` zurück (safe-by-default: nie stille Ausführung als `read`). Klassifikator, Policy, Blocklist/Allowlist und TTL sind per `from_config(...)` überschreibbar.

## Launcher-Kommandos

```
python launcher.py approval-list    [--status pending|approved|rejected|expired]
python launcher.py approval-show    <approval_id>
python launcher.py approval-approve <approval_id> [--by NAME]
python launcher.py approval-reject  <approval_id> [--by NAME]
python launcher.py approval-audit   [--limit N] [--all]
python launcher.py approval-expire  [--ttl SECONDS] [--by NAME]
```

## Tests

- `tests/test_agent_safety.py` – End-to-End, Re-Export des kanonischen `ApprovalRequest`, Rückwärtskompatibilität von `create()`, CLI, gemeinsamer Audit-Trail.
- `tests/test_approval_policy.py` – Klassifikation aller Brief-Aktionen, Policy-Verdikte, Blocklist/Allowlist, safe-by-default.
- `tests/test_action_guard.py` – Guard-Fluss, Queue-Wiederverwendung (identischer Dateipfad), Deduplizierung, approve/reject/expire, TTL-Grenze.

## Qualitätsnachweis

```
python -m compileall secondbrain/agent/safety secondbrain/native/approval.py launcher.py
pytest tests/test_agent_safety.py tests/test_approval_policy.py tests/test_action_guard.py -q
```

Erwartung: 41 passed. Zielinterpreter Python 3.11+ (Repo nutzt `enum.StrEnum`).

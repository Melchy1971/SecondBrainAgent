# SecondBrain OS v10.6 Agent Kernel

## Ziel
v10.6 verbindet Runtime, Job Queue, Permission Gate und Desktop-Kommandos. Das Paket ist bewusst klein gehalten: keine neue Feature-Insel, sondern ein ausführbarer Kern für kontrollierte Aktionen.

## Komponenten

- `agent_kernel_v106.py`: persistenter Agentzustand, Handler-Registry, Tick-Zyklus
- `job_queue_v106.py`: JSONL-basierte Queue mit Statusmodell
- `permissions_v106.py`: Level-Modell und Approval-Gate
- `desktop_commands_v106.py`: Quick Capture und Notifications als erste Desktop-Aktionen
- `run_v106_agent_kernel.py`: ausführbarer Smoke-Zyklus

## Sicherheitsmodell

| Level | Bedeutung | Default |
|---|---|---|
| 1 | Read | erlaubt |
| 2 | Write | erlaubt in v10.6 Runner |
| 3 | Execute | Approval erforderlich |
| 4 | System | blockiert |

## Statusmodell Jobs

```text
queued -> running -> done
queued -> running -> retry -> failed
queued -> running -> blocked
```

## Nächster Ausbau

1. EventBus-Integration pro Jobstatus
2. Desktop Tray an `desktop.quick_capture` anbinden
3. Connector Sync als geplanten Job registrieren
4. AI Runtime als `ai.answer` und `ai.review_note` Handler registrieren
5. Approval UI vor Level 3/4 Aktionen ergänzen

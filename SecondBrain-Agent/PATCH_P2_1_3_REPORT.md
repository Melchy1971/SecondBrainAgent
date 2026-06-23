# PATCH P2.1.3 — Desktop Command Execution

## Ziel
Desktop-Kommandos werden nicht mehr direkt aus der CommandPalette ausgeführt, sondern über eine robuste Ausführungsschicht mit einheitlichen Events, Notifications, Status-Updates und Fehlerisolation.

## Geänderte/Neue Dateien

- `secondbrain/desktop/command_executor.py`
- `tests/desktop/test_command_executor.py`

## Implementiert

- `DesktopCommandExecutor`
- `CommandExecutionResult`
- Erfolgs- und Fehlerpfad
- `JOB_STARTED` / `JOB_FINISHED` Events
- `ERROR_OCCURRED` Event bei Fehlern
- Statusintegration über `StatusService`
- Success/Error Notifications
- Ausführungshistorie mit Limit
- Fehlerisolation: defekte Commands brechen die Desktop-Shell nicht

## Validierung

```text
python -m pytest tests/desktop/test_command_executor.py -q
4 passed in 0.32s
```

```text
python -m pytest tests/desktop -q
21 passed in 0.42s
```

## Risiko
Niedrig. Neue Schicht ist UI-toolkit-neutral und verändert bestehende CommandPalette-Semantik nicht.

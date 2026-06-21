# SecondBrain OS v13.0 – Persistent Personal AGI OS

## Ziel
v13.0 verbindet Runtime, Jobs, Ziele, Empfehlungen, Benachrichtigungen und proaktive Assistenz zu einem persistenten Personal OS.

## Komponenten
- Runtime Supervisor
- Background Job Scheduler
- Goal Engine
- Recommendation Engine
- Notification Engine
- Proactive Assistant
- Personal AGI OS Orchestrator

## Launcher-Befehle
```powershell
python launcher.py os-status
python launcher.py os-start
python launcher.py os-health
python launcher.py os-services
python launcher.py os-run-jobs
python launcher.py os-briefing
python launcher.py os-review
python launcher.py os-recommendations
python launcher.py os-goal-add "TTR 1200" 1200 1147 points --deadline-days 120 --priority 4
python launcher.py os-goal-forecast
python launcher.py os-notify "Jarvis" "System bereit"
python launcher.py os-stop
```

## Betriebsmodell
1. Runtime Supervisor startet Services in Dependency-Reihenfolge.
2. Background Jobs führen wiederkehrende Systemaufgaben aus.
3. Goal Engine berechnet Ziel-Forecasts.
4. Recommendation Engine bewertet Risiken.
5. Proactive Assistant erstellt Briefings und Reviews.
6. Notification Engine verteilt Hinweise.

## Grenzen
- Kein echter 24/7-Daemon.
- Keine echten externen Connectoren.
- Jobs werden deterministisch simuliert.
- Keine automatische Codeänderung.

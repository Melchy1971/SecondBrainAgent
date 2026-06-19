# SecondBrain OS v12.1 – Core Runtime Foundation

## Ziel
v12.1 ersetzt direkte Modulaufrufe schrittweise durch einen entkoppelten Kern:

```text
Event Bus → Tool Registry → Long Running Runtime
```

## Neue CLI-Befehle

### Gesamtstatus
```powershell
python launcher.py core-status
```

### Event Bus
```powershell
python launcher.py bus-status
python launcher.py bus-publish connector.gmail.synced '{"count":3}'
python launcher.py bus-events --topic "connector.*"
python launcher.py bus-subscribe "agent.*" audit-agent
python launcher.py bus-dlq
```

### Tool Registry
```powershell
python launcher.py tool-status
python launcher.py tools
python launcher.py tool-execute system.status '{}' --scopes system.read
python launcher.py tool-execute agent.run '{"objective":"Teste Agent"}' --scopes agent.execute --approved
python launcher.py tool-audit
```

### Long Running Runtime
```powershell
python launcher.py runtime-status
python launcher.py runtime-start
python launcher.py runtime-tick
python launcher.py runtime-recover
python launcher.py runtime-stop
python launcher.py runtime-runs
```

## Architekturentscheidung
v12.1 ist bewusst lokal und dateibasiert. Dadurch bleibt das System ohne Redis, RabbitMQ oder Datenbank lauffähig. Externe Infrastruktur kann später hinter denselben Interfaces ergänzt werden.

## Grenzen
- Kein echter 24/7 Windows-Service.
- Keine parallele Prozesssteuerung.
- Keine WebSocket-Events.
- Keine produktive OAuth-Connector-Ausführung.

Diese Punkte gehören in v12.2 und v12.3.

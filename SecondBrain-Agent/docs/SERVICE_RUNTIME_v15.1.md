# SecondBrain OS v15.1 – Service Runtime

## Komponenten
- Service Runtime
- Structured JSON Logs
- Health / Ready / Metrics
- HTTP Health Server
- pywin32 Service Script Scaffold
- NSSM Command Generator
- Service Runner

## Befehle
```powershell
python launcher.py svc-status
python launcher.py svc-start
python launcher.py svc-health
python launcher.py svc-ready
python launcher.py svc-metrics
python launcher.py svc-log warning "Testmeldung"
python launcher.py svc-logs
python launcher.py svc-http-manifest
python launcher.py svc-http-start --port 8765
python launcher.py svc-service-manifest
python launcher.py svc-generate-service-script
python launcher.py svc-nssm-commands
python launcher.py svc-run --ticks 5
python launcher.py svc-stop
```

## Windows Service
### pywin32
```powershell
pip install pywin32
python launcher.py svc-generate-service-script
python scripts\secondbrain_service.py install
python scripts\secondbrain_service.py start
```

### NSSM
```powershell
python launcher.py svc-nssm-commands
```

## Grenzen
- Kein MSI Installer.
- pywin32-Datei ist Scaffold.
- HTTP-Server läuft im Prozess.

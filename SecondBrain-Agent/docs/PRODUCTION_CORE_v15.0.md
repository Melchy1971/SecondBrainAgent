# SecondBrain OS v15.0 – Production Core

## Ziel
v15.0 schließt die wichtigsten Produktionslücken: Service-Betrieb, Watchdog, Healthchecks, Secrets, Audit, Approval, Backup und Deployment-Planung.

## Komponenten
- Windows Service Manager Foundation
- Watchdog
- Runtime Recovery
- Secrets Vault Scaffold
- Audit Trail
- Approval Workflow
- Health / Ready Endpoint
- Metrics Collector
- Backup Manager
- Restore Plan
- Installer Manifest
- Migration Plan

## Befehle
```powershell
python launcher.py prod-status
python launcher.py prod-start
python launcher.py prod-health
python launcher.py prod-ready
python launcher.py prod-watchdog
python launcher.py prod-recover
python launcher.py prod-metrics

python launcher.py prod-service-plan
python launcher.py prod-service-mark-installed
python launcher.py prod-service-state

python launcher.py prod-secret-put OPENAI_API_KEY demo
python launcher.py prod-secrets
python launcher.py prod-secret-rotate OPENAI_API_KEY demo2

python launcher.py prod-approval-request agent file_write --risk high
python launcher.py prod-approvals
python launcher.py prod-approval-decide <REQUEST_ID> approved

python launcher.py prod-backup --label before_update
python launcher.py prod-backups
python launcher.py prod-backup-verify <BACKUP_ID>
python launcher.py prod-restore-plan <BACKUP_ID>

python launcher.py prod-installer-manifest
python launcher.py prod-migration-plan 14.0
python launcher.py prod-stop
```

## Sicherheitsgrenzen
- Secrets Vault nutzt Base64-Platzhalter, keine echte Verschlüsselung.
- Windows Service ist eine Foundation, kein echter pywin32-Service.
- Restore führt noch keine destruktive Wiederherstellung aus, sondern erzeugt einen Plan.
- Health/Ready sind CLI-Endpunkte, keine HTTP-Endpunkte.

## Nächster Schritt
v15.1: echter Windows Service mit pywin32, HTTP Health Server, strukturierte Logs und Service Installer.

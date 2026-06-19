# Deployment v3.1

## Windows Autostart

PowerShell als Administrator:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
.\deploy\windows\install_task_scheduler.ps1
```

Entfernen:

```powershell
.\deploy\windows\remove_task_scheduler.ps1
```

## Linux systemd

```bash
sudo cp deploy/linux/secondbrain-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable secondbrain-agent
sudo systemctl start secondbrain-agent
```

## macOS LaunchAgent

```bash
cp deploy/macos/com.secondbrain.agent.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.secondbrain.agent.plist
```

## Docker

```bash
cd deploy/docker
docker compose up -d
```

## REST API

```bash
python scripts/rest_api.py
```

Endpoints:

```text
GET /status
GET /run/import
GET /run/intelligence
GET /run/governance
```

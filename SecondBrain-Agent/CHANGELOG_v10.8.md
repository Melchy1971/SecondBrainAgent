# CHANGELOG v10.8 - Unified Launcher

## Neu

- Einheitlicher `launcher.py`
- `secondbrain.launcher_runtime_v108`
- Runtime-Konfiguration `config/runtime.yaml`
- Healthcheck
- Init-Befehl
- Start-Befehl
- Connector Sync über Launcher
- AI Ask über Launcher
- Desktop Quick Capture über Launcher
- Notification über Launcher
- Job Submit + Tick über SecureAgentKernel
- Dokumentation `docs/LAUNCHER_v10.8.md`

## Architekturwirkung

Vorher: Einzelmodule mussten direkt gestartet werden.

Nachher: Ein Startpunkt orchestriert Event Store, Connector Runtime, AI Runtime, Agent Kernel, Security und Desktop Commands.

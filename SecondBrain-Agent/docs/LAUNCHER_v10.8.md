# SecondBrain OS v10.8 Unified Launcher

## Ziel

Ein Startpunkt für das lokale SecondBrain OS.

```bash
python launcher.py health
python launcher.py init
python launcher.py start
```

## Startbefehle

### Healthcheck

```bash
python launcher.py health
```

Prüft:

- Event Store
- Desktop Commands
- Agent Kernel
- AI Runtime
- Connector Registry

### Initialisierung

```bash
python launcher.py init
```

Erzeugt:

- `runtime/`
- `events/runtime/`
- Vault-Pfad aus `config/runtime.yaml`

### Einmaliger Systemstart

```bash
python launcher.py start
```

Führt aus:

1. Runtime initialisieren
2. Healthcheck
3. Connector Sync
4. Agent Tick

### Connector Sync

```bash
python launcher.py sync
```

Liest `config/connectors_v104.json`, normalisiert Datensätze und schreibt Runtime Events.

### KI-Aufruf

```bash
python launcher.py ask "Fasse den aktuellen Systemzustand zusammen" --task system_summary
```

Standardprovider ist `echo`, damit das System offline und testbar startet.

### Quick Capture

```bash
python launcher.py capture "Neue Idee für Jarvis" --title "Jarvis Idee"
```

Schreibt eine Markdown-Notiz in den Vault.

### Notification

```bash
python launcher.py notify "System gestartet" --severity info
```

Schreibt eine lokale Benachrichtigung in den Vault.

### Job einreichen

```bash
python launcher.py submit desktop.notify '{"message":"Hallo","severity":"info"}'
python launcher.py tick
```

## Konfiguration

Datei:

```text
config/runtime.yaml
```

Relevante Felder:

```yaml
runtime:
  profile: safe
  paths:
    vault: ../SecondBrain
    runtime: runtime
    events: events/runtime
  services:
    connectors: true
    ai_runtime: true
    agent_kernel: true
    desktop_commands: true
    security: true
```

## Architektur

```text
launcher.py
↓
Launcher Runtime
↓
Config Loader
↓
Event Store
↓
Connector Runtime
↓
AI Runtime
↓
Secure Agent Kernel
↓
Desktop Commands
```

## Sicherheitslogik

Alle Job-Aktionen laufen über den `SecureAgentKernel`.

Auswirkungen:

- Aktionen haben Level und Risk Score.
- Riskante Aktionen benötigen Approval.
- Entscheidungen werden in `runtime/audit_v107.jsonl` protokolliert.
- PII/Secrets werden im Audit redacted.

## Windows Start

```powershell
cd D:\SecondBrainAgent\SecondBrain-Agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python launcher.py health
python launcher.py start
```

## Ergebnis

v10.8 verbindet die vorhandenen Module zu einer gemeinsamen lokalen Runtime. Das System ist dadurch nicht mehr nur eine Sammlung einzelner Skripte, sondern über einen stabilen Einstiegspunkt bedienbar.

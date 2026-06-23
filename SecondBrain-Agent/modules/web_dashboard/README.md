# web_dashboard

Lokales HTTP-Dashboard ohne externe Abhängigkeiten.

## Start

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\web_dashboard.py
```

Browser:

```text
http://localhost:8765
```

## Funktionen

- zeigt Vault-, Inbox- und Projektpfade
- zählt Markdown-Dateien im Vault und Dateien in der Inbox
- startet vorhandene Skripte für Import, Intelligence Cycle, Governance,
  Quality Report, Conflict Report und Sync Health

## Abgrenzung

Das Dashboard auf Port `8765` ist eine einfache Aktionsseite. Die aktuelle
primäre GUI ist das Jarvis HUD:

```powershell
python scripts\start_hud.py
```

Browser: `http://127.0.0.1:8851`

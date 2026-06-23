# v10.2 Jarvis Control Center GUI

Hinweis: `scripts\start_gui.py` ist aus Kompatibilitätsgründen erhalten,
leitet aber auf das aktuelle Jarvis HUD um. Die aktive Oberfläche läuft auf
Port `8851`, nicht mehr auf `8850`.

## Start

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\start_gui.py
```

Browser öffnen:

```text
http://127.0.0.1:8851
```

## Funktionen

- Systemstatus
- Import AI Exports
- v10 Cycle
- v10.1 Cycle
- Path Check
- Release Gate
- Regression Tests
- Vector RAG Index
- RAG Frage
- Dashboard-Pfade
- Logs

## Menü

```powershell
python scripts\menu.py
```

Option:

```text
8 = Jarvis HUD starten (Port 8851)
```

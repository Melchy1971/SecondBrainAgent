# Jarvis HUD GUI (Iron-Man / Stark Look)

Eigenstaendige HUD-Oberflaeche im Stil der Rainmeter-Iron-Man-Desktops.
Laeuft parallel zur bestehenden GUI (`gui_backend_v102`, Port 8850), ohne sie zu
veraendern. Wiederverwendung von deren Skript-Runner und Status-Funktionen.

## Start

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\start_hud.py
```

Browser:

```text
http://127.0.0.1:8851
```

## Voraussetzung

```powershell
pip install psutil
```

Ohne `psutil` startet die GUI trotzdem; die Live-Metrik-Ringe zeigen dann 0 und
den Hinweis "psutil fehlt".

## Dateien

- `secondbrain/jarvis_hud_server.py` - HTTP-Server (Port 8851) + JSON-API
- `web/jarvis_hud/index.html` - Single-File-Frontend (HTML/CSS/JS, keine Build-Tools)
- `scripts/start_hud.py` - Starter

## Endpoints

- `GET /` - HUD-Seite
- `GET /api/metrics` - CPU/RAM/SWAP/Disk/Uptime/Netz (psutil)
- `GET /api/weather` - Open-Meteo (kein API-Key)
- `GET /api/news` - Tagesschau-RSS
- `GET /api/status` - `system_status()` (Vault/Inbox/MD-Anzahl)
- `GET /api/dashboards` - `dashboard_links()`
- `GET /api/run?script=NAME` - Skript ausfuehren (review-first)
- `GET /api/rag?q=FRAGE` - RAG-Frage an das Vault
- `GET /api/logs` - Tail von `jarvis_gui.log`

## Aktualisierung im Browser

- Uhr/Datum: lokal, jede Sekunde
- Metriken: alle 2 s
- Status: alle 30 s
- Wetter: alle 15 min
- News: alle 10 min

## Konfiguration

In `secondbrain/jarvis_hud_server.py`:

- `WEATHER_LAT`, `WEATHER_LON`, `WEATHER_PLACE` - Standardort Bonn
- `NEWS_RSS` - RSS-Quelle (Standard Tagesschau)
- `NEWS_MAX` - Anzahl Schlagzeilen

## Hinweise

- Keine Loeschaktionen; Aktionen rufen nur vorhandene Skripte in `scripts/`.
- Wetter/News brauchen Internet. Ohne Verbindung zeigen die Panels "offline";
  der Rest der GUI bleibt funktionsfaehig.
- Port 8851 gewaehlt, damit kein Konflikt mit der alten GUI (8850) entsteht.

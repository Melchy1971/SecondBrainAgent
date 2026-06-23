# Jarvis HUD GUI (Iron-Man / Stark Look)

HUD-Oberflaeche im Stil der Rainmeter-Iron-Man-Desktops. **Einzige GUI** des
Systems (Konsolidierung 2026-06-23). Die alte Control-Center-GUI auf Port 8850
wird nicht mehr als Oberflaeche gestartet.

- `scripts/start_gui.py` leitet auf das HUD um (Rueckwaerts-Kompatibilitaet).
- `scripts/menu.py` Punkt 8 startet das HUD (Port 8851).
- `secondbrain/hud_core.py` ist seit Phase 2 das **neutrale Kernmodul** mit der
  GUI-unabhaengigen Logik (`run_script`, `system_status`, `dashboard_links`,
  `log_event`, Pfade). Sowohl das HUD als auch die alte GUI importieren von hier.
- `secondbrain/gui_backend_v102.py` ist nur noch Praesentationsschicht (HTML +
  Server 8850) und importiert die Logik aus `hud_core`. Kein Frontend haengt mehr
  an einem anderen Frontend; Single Source of Truth ist `hud_core`.

## Start / Stop (Befehle Jarvis / Jarvis-stop)

```text
Jarvis        startet das HUD im Hintergrund und oeffnet den Browser
Jarvis-stop   stoppt das HUD
```

- `Jarvis.bat` startet `pythonw scripts\start_hud.py` ohne Konsolenfenster,
  prueft per PID-Datei ob schon eine Instanz laeuft und oeffnet `http://127.0.0.1:8851`.
- `Jarvis-stop.bat` beendet den Prozess ueber `runtime\jarvis_hud.pid`,
  mit Fallback ueber den Port 8851.

Damit die Befehle von ueberall funktionieren, den Projektordner einmalig zur
PATH-Variable hinzufuegen (PowerShell, dauerhaft fuer den Nutzer):

```powershell
[Environment]::SetEnvironmentVariable("Path",
  $env:Path + ";H:\SecondBrainAgent\SecondBrain-Agent", "User")
```

Danach neue Konsole oeffnen. Ohne PATH-Eintrag aus dem Ordner heraus aufrufen:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
.\Jarvis.bat
.\Jarvis-stop.bat
```

## Desktop-Verknuepfung + Autostart

Einmalig einrichten (legt Desktop-Icon und Login-Autostart an):

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
powershell -ExecutionPolicy Bypass -File install_jarvis.ps1
```

Ergebnis:

- Desktop: "Jarvis HUD" - Doppelklick startet das HUD und oeffnet den Browser.
- Autostart (Login): startet das HUD im Hintergrund ohne Browser (`/quiet`).
  Liegt im Ordner `shell:startup` des Nutzers.

Wieder entfernen:

```powershell
powershell -ExecutionPolicy Bypass -File uninstall_jarvis.ps1
```

Hinweise:

- `Jarvis /quiet` startet nur den Server (kein Browser) - genau das nutzt der Autostart.
- Icon der Verknuepfung: in `install_jarvis.ps1` ueber `IconLocation` aenderbar.
- Der Autostart oeffnet bewusst keinen Browser; das HUD ist nach dem Login direkt
  unter `http://127.0.0.1:8851` erreichbar.

## Manueller Start (Konsole bleibt offen)

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

- `secondbrain/hud_core.py` - neutrales Kernmodul (geteilte Logik)
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
- `GET /api/settings` - aktuelle Einstellungen lesen
- `POST /api/settings` - Einstellungen speichern (JSON-Body, validiert)

## Einstellungen (Menuepunkt "⚙ Einstellungen")

Button in der Aktionsleiste oeffnet ein Modal. Konfigurierbar:

- Ort (Anzeige), Breitengrad, Laengengrad (speist Open-Meteo)
- News-Feed (RSS-URL), Anzahl Schlagzeilen (1-20)
- Wetter-Intervall (Minuten, 1-720)
- Akzentfarbe (CSS-Variable der GUI)

Persistenz serverseitig in `config/hud_settings.json` (ueberlebt Neustart).
Eingaben werden im Backend validiert und begrenzt; unbekannte Felder verworfen.
Aenderungen wirken sofort (Wetter/News werden neu geladen, Akzentfarbe sofort gesetzt).

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

# Installation v0.4 für Anfänger

## 1. ZIP entpacken

Nach:

```text
H:\SecondBrainAgent
```

## 2. In den Projektordner wechseln

PowerShell öffnen:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

Wichtig: Nicht in `H:\SecondBrainAgent` bleiben. `requirements.txt` und
`launcher.py` liegen im Unterordner `SecondBrain-Agent`.

## 3. Zusatzpakete installieren

```powershell
python -m pip install -r requirements.txt
```

Fallback, falls nur die Basis-Importer genutzt werden:

```powershell
python -m pip install pypdf requests beautifulsoup4
```

## 4. Healthcheck ausführen

```powershell
python scripts\healthcheck.py
```

## 5. Menü starten

```powershell
python scripts\menu.py
```

## 6. Web-UI starten

Aktuelles Jarvis HUD:

```powershell
python scripts\start_hud.py
```

Browser:

```text
http://127.0.0.1:8851
```

Einfaches Dashboard:

```powershell
python scripts\web_dashboard.py
```

Browser:

```text
http://localhost:8765
```

## 7. Launcher-Beispiele

```powershell
python launcher.py health
python launcher.py desktop16-status
python launcher.py agent16-migrate
python launcher.py agent16-task-create "Sprint" "Plane den nächsten Sprint"
python launcher.py agent16-tasks
```

## 8. Import testen

Dateien in die passenden Inbox-Ordner legen:

```text
H:\SecondBrainAgent\SecondBrain-Inbox\PDFs
H:\SecondBrainAgent\SecondBrain-Inbox\Webseiten
H:\SecondBrainAgent\SecondBrain-Inbox\ChatGPT
```

Dann Menüoption 1 ausführen.

# SecondBrain Agent

Minimaler, sicherer Ausgangspunkt fuer einen lokalen Wissensassistenten.

## Start

Node.js 20+ installieren, `.env.example` optional nach `.env` kopieren und Werte anpassen. Der Entry Point laedt diese Datei, falls sie existiert; bereits gesetzte Umgebungsvariablen haben Vorrang. `.env` bleibt durch `.gitignore` unveroeffentlicht. Danach `npm install` und `npm start` ausfuehren. Alternativ: `python launcher.py --install` einmalig, danach `python launcher.py`. Innerhalb des gemeinsamen Workspaces startet `python launcher.py hud` das uebergeordnete Web-HUD.

Der Server bindet standardmaessig nur an `127.0.0.1:3000`. Endpunkte: `GET /health`, `POST /chat`, `GET /tools`. Ohne konfigurierten Provider arbeitet der Agent im sicheren Mock-Modus. Terminal, E-Mail, Kalender und Sprache sind standardmaessig deaktiviert. `.env`, Laufzeitdatenbanken und Uploads werden nicht versioniert.

Tests: `npm test`


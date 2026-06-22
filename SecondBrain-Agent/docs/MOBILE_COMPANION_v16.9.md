# SecondBrain OS v16.9 – Mobile Companion

## Ziel
v16.9 ergänzt die Backend-Grundlage für iOS/Android/PWA Companion Apps.

## Enthalten
- Device Pairing
- Trusted Devices
- Offline Capture Queue
- Voice Notes
- Camera OCR Scaffold
- Push Outbox
- Push Delivery Simulation
- Mobile Widgets
- Sync Runs
- Remote Sessions
- SQLite Persistence
- App Manifest

## Befehle
```powershell
python launcher.py mobile16-migrate
python launcher.py mobile16-status
python launcher.py mobile16-manifest
python launcher.py mobile16-pair-request "iPhone Markus" ios
python launcher.py mobile16-pairing-requests
python launcher.py mobile16-pair-approve <REQUEST_ID>
python launcher.py mobile16-devices
python launcher.py mobile16-voice-note "Neue mobile Notiz"
python launcher.py mobile16-camera-ocr image://demo
python launcher.py mobile16-offline-replay
python launcher.py mobile16-push "Jarvis" "System bereit"
python launcher.py mobile16-widgets
python launcher.py mobile16-sync
```

## Grenzen
- Keine native iOS/Android App.
- Push ist simuliert.
- OCR ist Scaffold.
- Sync ist deterministisch, ohne Konflikt-Merge.

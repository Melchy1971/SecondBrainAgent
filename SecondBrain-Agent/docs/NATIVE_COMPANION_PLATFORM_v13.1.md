# SecondBrain OS v13.1 – Native Companion Platform

## Ziel
v13.1 erweitert SecondBrain/Jarvis zu einer geräteübergreifenden Companion Platform.

## Komponenten
- Device Mesh
- Identity Service
- Device Pairing
- Sync Engine v2
- Push Service
- Offline Engine
- Remote Sessions
- Widget Engine
- Web Runtime

## Befehle
```powershell
python launcher.py companion-status
python launcher.py identity-create "Markus"
python launcher.py device-pair "iPhone Markus" ios
python launcher.py device-pairing-requests
python launcher.py device-pair-approve <REQUEST_ID>
python launcher.py device-list
python launcher.py sync-status
python launcher.py sync-now --device-id <DEVICE_ID>
python launcher.py push-send "Jarvis" "System bereit" --channel mobile
python launcher.py push-deliver
python launcher.py offline-capture <DEVICE_ID> note "Mobile Notiz"
python launcher.py offline-replay
python launcher.py session-create "Recherche" --device-id desktop
python launcher.py session-list
python launcher.py widgets
python launcher.py web-start
python launcher.py web-manifest
```

## Sicherheitsgrenzen
- Pairing erzeugt zunächst eine explizite Anfrage.
- Trust Level wird separat geführt.
- Push und Sync sind lokale Simulationen.
- Keine Cloud-Abhängigkeit.
- Keine echten iOS/Android-Binaries.

## Nächster Schritt
v13.2 Real Connector Ecosystem mit OAuth, Delta Sync und Webhooks.

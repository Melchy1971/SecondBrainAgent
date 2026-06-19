# SecondBrain OS v12.8 – Mobile App Foundation

## Ziel
v12.8 bereitet echte iOS/Android-Clients vor, ohne bereits native Apps vorauszusetzen.

## Komponenten
- Device Registry
- Trusted Device Model
- Biometric Capability Flag
- Offline Command Queue
- Push Outbox
- Mobile Widget Registry
- Mobile Sync Protocol

## Befehle
```powershell
python launcher.py mobile2-status
python launcher.py mobile2-register iphone "iPhone Markus" --platform ios --trusted --biometric
python launcher.py mobile2-devices
python launcher.py mobile2-command iphone capture --payload "{\"text\":\"Mobile Notiz\"}"
python launcher.py mobile2-queue
python launcher.py mobile2-drain
python launcher.py mobile2-push "Jarvis" "System bereit"
python launcher.py mobile2-push-outbox
python launcher.py mobile2-widgets
python launcher.py mobile2-widget-enable voice true
python launcher.py mobile2-sync iphone
```

## Sicherheitslogik
Remote-Kommandos werden nur für Trusted Devices akzeptiert.
Biometrie wird als Capability gespeichert, aber nicht lokal simuliert.

## Nächster Schritt
v12.9 Learning Engine: Experience Store, Episode Memory, Reflection, Skill Metrics.

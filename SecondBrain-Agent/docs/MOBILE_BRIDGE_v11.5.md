# SecondBrain OS v11.5 – Mobile Bridge

## Ziel

Die Mobile Bridge macht Jarvis mobil anschlussfähig, ohne sofort eine native App zu erzwingen. Die Runtime stellt lokale Queues bereit, die später durch eine iOS-, Android- oder Web-App synchronisiert werden können.

## Komponenten

```text
runtime/mobile/
├── devices.json
├── push_outbox.json
├── approval_inbox.json
├── captures.json
└── settings.json
```

## Befehle

```powershell
python launcher.py mobile-status
python launcher.py mobile-register "iPhone Markus" ios --trusted
python launcher.py mobile-devices
python launcher.py mobile-push <device_id> "Titel" "Nachricht"
python launcher.py mobile-capture <device_id> note "Titel" "Inhalt"
python launcher.py mobile-approval-request <device_id> system.restart "Runtime neu starten?" --risk 4
python launcher.py mobile-approvals
python launcher.py mobile-approval-decide <approval_id> approved
```

## Sicherheitsgrenzen

- Mobile Geräte führen keine lokalen Systemaktionen direkt aus.
- Approval Requests benötigen standardmäßig ein vertrauenswürdiges Gerät.
- Push ist nur Outbox, kein externer Push-Dienst.
- Captures sind sichere Eingänge in das Wissenssystem, keine Command Execution.

## Nächste Ausbaustufe

- FastAPI Bridge Server
- Token-basierte Device Auth
- QR Pairing
- Web Companion Dashboard
- Native Push Provider

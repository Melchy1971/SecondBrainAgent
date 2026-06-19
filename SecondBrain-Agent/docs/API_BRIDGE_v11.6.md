# API Bridge v11.6

## Zweck
Die API Bridge macht SecondBrain OS lokal automatisierbar, ohne die Governance zu umgehen.

## Start
```powershell
python launcher.py api-serve
```

## Token erstellen
```powershell
python launcher.py api-token-create "Local Dashboard" --scopes read:status,read:metrics,read:mobile,write:capture,write:notify
```

Der ausgegebene Token wird nur einmal angezeigt.

## API testen
```powershell
python launcher.py api-dispatch GET /status --internal
python launcher.py api-dispatch POST /capture --internal --payload '{"title":"API Test","text":"Testnotiz"}'
```

## HTTP Beispiel
```powershell
$token = "sb_xxx"
Invoke-RestMethod -Uri http://127.0.0.1:8765/status -Headers @{Authorization="Bearer $token"}
```

## Sicherheitsmodell
| Ebene | Kontrolle |
|---|---|
| Auth | Bearer Token |
| Rechte | Scopes |
| Risiko | Risk Score |
| Ausführung | Approval bei Risk >= 3 |
| Nachvollziehbarkeit | Audit JSONL |

## Wichtige Routen
- `GET /manifest`
- `GET /health`
- `GET /status`
- `GET /metrics`
- `GET /mobile/status`
- `GET /voice/status`
- `GET /twin/status`
- `POST /capture`
- `POST /notify`
- `POST /agent/run`
- `POST /workflow/run`

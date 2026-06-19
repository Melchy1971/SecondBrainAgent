# SecondBrain OS v12.2 – Real Connectors Foundation

## Ziel
v12.2 ersetzt Demo-Sync durch eine belastbare Connector-Laufzeit:

- Connector Registry
- OAuth-Konfigurationsvorlagen
- Delta Cursor
- Offline Queue
- Retry/Backoff
- Webhook Inbox
- Event-Bus-Publishing
- Tool Registry Integration

## Start

```powershell
python launcher.py connectors-status
python launcher.py connectors-list
python launcher.py connector-sync gmail
python launcher.py connector-sync-all
```

## OAuth Templates

```powershell
python launcher.py connector-oauth-templates
```

Die Ausgabe definiert die benötigten ENV-Variablen:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `MS_CLIENT_ID`
- `MS_CLIENT_SECRET`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`

## Webhook Test

```powershell
python launcher.py connector-webhook gmail '{"message_id":"demo"}'
python launcher.py connector-webhooks
```

## Event Bus Integration
Jeder Sync erzeugt Events:

```text
connector.<name>.item
connector.<name>.webhook
```

Replay:

```powershell
python launcher.py bus-events --topic connector.gmail.item
```

## Nächster Ausbau
v12.2 enthält noch keine produktiven API-Adapter. Die Adapter-Grenze ist bewusst vorbereitet:

```python
adapter.pull(cursor, limit) -> (items, next_cursor)
```

Produktive Adapter folgen in v12.2.x:

- Gmail API Adapter
- Google Calendar Adapter
- Google Drive Adapter
- Microsoft Graph Adapter
- GitHub Adapter
- Paperless API Adapter
- Home Assistant Adapter

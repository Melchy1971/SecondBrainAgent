# SecondBrain OS v13.2 – Real Connector Ecosystem

## Ziel
v13.2 legt das produktionsnahe Connector-Fundament: OAuth, Token Store, Delta Sync, Webhooks, Connector Registry und Provider-Stubs.

## Komponenten
- Connector Registry
- OAuth Runtime
- Secure Token Store
- Delta Sync Engine
- Webhook Inbox
- Provider-Stubs:
  - Gmail
  - Google Calendar
  - GitHub
  - Paperless-ngx
  - Obsidian Registry Entry

## Befehle
```powershell
python launcher.py connector13-status
python launcher.py connector13-list
python launcher.py connector13-enable gmail
python launcher.py connector13-oauth-templates
python launcher.py connector13-oauth-request gmail --scopes gmail.readonly
python launcher.py connector13-token-store gmail demo-token --scopes gmail.readonly
python launcher.py connector13-sync gmail
python launcher.py connector13-sync-all
python launcher.py connector13-runs
python launcher.py connector13-webhook gmail message.created --payload "{\"id\":\"1\"}"
python launcher.py connector13-webhooks
python launcher.py connector13-webhook-drain
```

## Grenzen
- OAuth ist noch kein echter Browser-Flow.
- Tokens werden nur base64-kodiert, nicht produktiv verschlüsselt.
- Provider liefern Demo-Deltas.
- Echte APIs folgen in v13.2.x / v13.3 Integration.

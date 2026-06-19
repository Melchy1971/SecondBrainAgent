# SecondBrain OS v11.6 – Web/API Bridge

## Neu
- Lokale REST API Bridge
- Token Store mit gehashten API Tokens
- Scope-basiertes Berechtigungsmodell
- Risk Gate für Remote-Ausführung
- API Audit Log
- API Manifest
- Launcher-Kommandos:
  - `api-status`
  - `api-manifest`
  - `api-token-create`
  - `api-token-list`
  - `api-dispatch`
  - `api-serve`
  - `api-audit`

## Designentscheidung
Die API ist standardmäßig lokal auf `127.0.0.1` gebunden. Remote-Zugriff muss später explizit über Reverse Proxy, TLS und Approval-Regeln aktiviert werden.

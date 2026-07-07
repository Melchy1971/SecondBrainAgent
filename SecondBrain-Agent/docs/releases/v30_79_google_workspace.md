# v30.79 — Google Workspace + Connector-Scaffold

## Zwei Lieferungen
1. **Connector-Scaffold** (`secondbrain/connectors/scaffold/`): provider-agnostische Basis, aus dem
   M365-Muster extrahiert. Enthält transport, oauth2 (Device-Code + Auth-Code), rest_client
   (konfigurierbare Paging-Keys via PagingConfig), delta_connector (3 Modi: path_suffix,
   sync_token_param, watermark), writer (Approval-Gate), approval, sync, runtime_base, cli.
   **M365 wurde auf dieses Scaffold umgestellt — 33 Tests weiterhin grün, kein Verhaltensbruch.**
2. **Google Workspace** (`secondbrain/connectors/google/`): Gmail, Calendar, Drive, Contacts, Tasks.

## Delta-Strategien (Google-spezifisch, ehrlich benannt)
- Calendar, Contacts: natives `syncToken` (nextSyncToken) — echtes Delta.
- Drive: Changes-API (startPageToken -> changes -> newStartPageToken).
- Gmail: messages.list (+ `after:` Watermark) + Einzelabruf. History-API-Delta = Folge-Ausbau.
- Tasks: tasklists + `updatedMin`-Watermark.
- **Google Keep: keine offizielle API -> nicht implementiert.** Optionaler Weg später: Takeout-Export-Bridge.

## OAuth2
Device-Code-Flow (`oauth2.googleapis.com/device/code`). Google verlangt `client_secret` auch für
Installed-Apps; wird mitgesendet. Ohne `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` -> `config_error`.

## Konfiguration (du legst den OAuth-Client an)
1. Google Cloud Console -> APIs aktivieren: Gmail, Calendar, Drive, People, Tasks.
2. OAuth-Client erstellen (Typ: „TV and Limited Input" / Installed App).
3. `.env`:
   ```
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   # GOOGLE_SCOPES=...   # optional
   ```

## Launcher (Python 3.11+)
```
python launcher.py google-login
python launcher.py google-sync --resources gmail,calendar
python launcher.py google-status
python launcher.py google-disconnect
```

## Schreibende Aktionen
Approval-gated (identisch zu M365): Gmail send, Kalender-Event anlegen/löschen, Drive-Upload/Delete,
Kontakt anlegen, Task anlegen/erledigen. Default DENY bis `approve(request_id)`.

## Validierung
`compileall` grün; `pytest tests/connectors -q` -> **52 passed** (33 M365 + 19 Google), offline via FakeTransport.
Echter `google-login` + Live-Sync laufen auf deiner Maschine (Netz + OAuth-Client).

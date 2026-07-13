# v30.67 — Connector-Runtime-Luecken geschlossen

Baut auf dem Connector-Scaffold auf. **Nur das echt Fehlende** — Gmail/Drive/Calendar (v30.79) und
OneDrive/Outlook-Mail (v30.78) existieren bereits; `dead_letter.py`, `health.py` (Source-Status) und
`conflict_resolution.py` blieben unangetastet und wurden erweitert statt ersetzt.

## Neu
- **GitHub** (`connectors/github/`): Auth per **Personal Access Token** oder **Device-Flow** (Scaffold-OAuth2),
  REST-Client mit Retry (429/5xx), **Issues-Connector** inkrementell via `since`-Watermark (PRs werden
  uebersprungen), **approval-gated Writer** (Issue anlegen, kommentieren). Offline via FakeTransport getestet.
- **Lokaler Ordner** (`connectors/local_folder.py`): Filesystem-Sync, inkrementell per **mtime-Watermark**,
  Extension-Filter + max_bytes, emittiert `ConnectorItem` in dieselbe Import-Bridge.
- **Outlook PST** (`connectors/outlook_pst.py`): `PstReader`-Port + `PypffPstReader` (lazy libpff,
  Integration-only) + `FakePstReader` (Tests). Watermark auf `received`.
- **Persistente Dead-Letter-Queue** (`connectors/dead_letter_store.py`): `JsonDeadLetterQueue` +
  `replay(queue, handler)` — Erfolg entfernt den Eintrag, Fehler erhoeht `attempts` und behaelt ihn.
- **Conflict-Detection** (`connectors/conflict_detection.py`): `detect(local, remote, base=...)` klassifiziert
  none/local_only/remote_only/identical/local_ahead/remote_ahead/**both_changed** (echter Konflikt -> manual).

## Launcher
```
python launcher.py local-folder-sync --path /pfad/zum/ordner
GITHUB_TOKEN=... python launcher.py github-issues --owner me --repo projekt
```

## Tests (16 passed, 1 skipped)
Lokaler Ordner (Filter/Inkrement/max_bytes), DLQ (Persistenz + Replay mit attempt-Increment), Conflict
(7 Typen + Timestamp-Fallback), GitHub (Issues incremental via FakeTransport, PR-Skip, Writer approval-gated,
Retry auf 5xx). `pypff`-PST-Test nur mit installiertem libpff, sonst skip.

## Grenzen (ehrlich)
- Echter `github-login`/Live-Sync + PST-Parsing (libpff) laufen nur auf deiner Maschine (Netz/Token bzw.
  native Abhaengigkeit). Hier via Fakes getestet.
- GitHub-Paginierung ueber den `Link`-Header ist noch nicht implementiert (aktuell erste Seite via
  `per_page`); fuer grosse Repos ein Folge-Ausbau. Scheduler/Jobs/Progress nutzen die vorhandene
  Scaffold-BackgroundSync bzw. `health.py`-Source-Status.

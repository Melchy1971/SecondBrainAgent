# Technical Debt Report — SecondBrain-Agent v30.77
Stand: 2026-07-07

## 1. Kennzahlen
- Statische Orphan-Module (kein statischer Importeur): **127**
- Davon nach Cross-Check gegen Registry/`__init__`-Re-Exports/dynamische Importe/String-Referenzen verbleibende **Quarantäne-Kandidaten: 100**
- Als referenziert zurückgestellt (nicht anfassen): **25**
- Doppelte Klassennamen: **84**
- Versionierte Modulfamilien (Parallelstände): **6** (bis zu 17 Stände in `launcher_runtime`)
- Prozess-Altlast: **20** `DELTA_MANIFEST_*.json` im oberen Repo + 50+ `APPLY_DELTA_*`/`RELEASE_NOTES_*` im Code-Root.

## 2. Schuldenklassen (priorisiert)

### P1 — Struktur/Build-Risiko
- Zwei parallele Bäume + zwei verschachtelte Git-Repos → uneindeutige Quelle der Wahrheit.
- Defekt benannter Ordner `H:\SecondBrainAgent\SecondBrain-Agent` im Code-Root.

### P2 — Duplikate/Konsolidierung
- 17-fach-Kette `launcher_runtime_vNN` (live, nur via Konsolidierungs-Release auflösbar).
- Weitere Ketten: `digital_twin` (v2/v5/v9/v113), `workflow_engine` (v9/v112), `event_bus` (v95/v121), `connectors` (v13/v95), `chief_of_staff` (v2/v98).
- 84 doppelte Klassennamen; Top: `Handler`(8), `JsonStore`(7), `ConnectorRegistry`(4), `ContextBuilder`(4), `Store`(4).

### P3 — Verwaiste Module (Quarantäne-Kandidaten, 100)
Verteilung nach Bereich:

| Bereich | Kandidaten |
|---|---|
| `rag` | 11 |
| `agent` | 10 |
| `connectors` | 10 |
| `gui` | 10 |
| `cli` | 8 |
| `dashboard` | 8 |
| `storage` | 7 |
| `gates` | 6 |
| `mobile` | 6 |
| `native` | 5 |
| `root` | 4 |
| `memory` | 4 |
| `ga` | 3 |
| `voice` | 3 |
| `operations` | 2 |
| `desktop` | 1 |
| `privacy` | 1 |
| `security` | 1 |

**Wichtig:** Diese Liste ist ein *„kein statischer Importeur"*-Signal, **kein** Beweis für toten Code. Bereiche `connectors`, `gui`, `native`, `cli`, `gates` sind stark registry-/dispatch-geladen. Umsetzung ausschließlich reversibel (Verschiebung nach `archive/v30_77_quarantine/`) und **nur bei grünem pytest + GUI-/Launcher-Smoke** (siehe `DELTA_MANIFEST_v30_77.json` + `apply_v30_77.ps1`).

### P4 — Prozess-Altlast
- 20 Delta-Manifeste + zahlreiche `APPLY_DELTA_*`/`RELEASE_NOTES_*` im Code-Root. Anforderung: nach `docs/releases/` archivieren, Root entschlacken.

## 3. Empfohlene Reihenfolge
1. P1 bereinigen (Ordner-Artefakt, Repo-Grenzen) — risikoarm.
2. P3 Quarantäne über self-gating Skript auf Windows (grüner Lauf = Abnahme).
3. P2 Ketten-Konsolidierung als eigene Releases v30.78+.
4. P4 Doku-Archivierung.

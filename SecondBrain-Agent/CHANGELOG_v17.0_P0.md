# CHANGELOG v17.0 P0 Integration Core

## Ziel
P0-Blocker aus dem aktuellen Code-Stand reduzieren: Launcher wieder als zentralen Einstiegspunkt nutzbar machen, Test-Collection reparieren und eine minimale Modul-Registry als Integrationsanker einführen.

## Änderungen

### 1. Unified Launcher wiederhergestellt
- `launcher.py` ist nicht mehr ausschließlich auf `mobile16-*` beschränkt.
- Unterstützte Einstiegspunkte:
  - `health`
  - `status`
  - `modules`
  - `desktop-*`
  - `voice-*`
  - `graph-*`
  - `mobile16-*`
  - Legacy-Delegation an `secondbrain.launcher_runtime_v126`
- Mobile Companion bleibt vollständig erreichbar.

### 2. Test-Collection-Blocker behoben
- Datei: `secondbrain/connectors_v13/webhooks.py`
- Problem: Methode `list()` überschattete Builtin `list`; Annotation `list[dict]` brach bei Class Creation.
- Fix:
  - `from __future__ import annotations`
  - neue interne Methode `list_items()`
  - kompatible Methode `list()` bleibt erhalten.

### 3. Module Registry eingeführt
- Neue Datei: `secondbrain/module_registry.py`
- Enthält deklarative Registry für:
  - Core Runtime
  - Desktop OS
  - Realtime Voice
  - Knowledge Graph
  - Mobile Companion
- `launcher.py health` nutzt die Registry für Import-Health und Modulübersicht.

## Validierung

```text
python -m pytest --collect-only -q
227 tests collected

python -m pytest -q
227 passed in 6.04s
```

Smoke Commands geprüft:

```text
python launcher.py health
python launcher.py desktop-status
python launcher.py voice-status2
python launcher.py mobile16-status
```

## Status nach v17.0 P0

| Bereich | Ergebnis |
|---|---|
| Test Collection | PASS |
| Gesamttests | PASS, 227/227 |
| Launcher Health | PASS |
| Desktop CLI | PASS |
| Voice CLI | PASS |
| Mobile CLI | PASS |
| Integration Core | begonnen |

## Verbleibende P0-Lücken

1. Registry ist aktuell deklarativ/importbasiert, noch kein vollständiger Runtime-Lifecycle-Orchestrator.
2. Health prüft Modulimporte, aber noch nicht DB, Connector-Tokens, Event Bus Persistence, RAG Index und Write-Policy-End-to-End.
3. Keine zentrale Config-Normalisierung über alle Modulversionen.
4. Keine einheitliche Start/Stop/Tick-Orchestrierung über Desktop, Voice, Mobile, Graph, Connectors, RAG.
5. Production Security bleibt offen: echte Secret-Verschlüsselung, Approval UI, Policy-Gates, DSGVO Export/Löschung.

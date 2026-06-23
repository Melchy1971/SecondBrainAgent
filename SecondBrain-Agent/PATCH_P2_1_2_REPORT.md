# PATCH P2.1.2 – Desktop Shell Integration

## Ziel
Desktop Foundation aus P2.1.1 zu einer startbaren Desktop-Fassade erweitern.

## Änderungen
- `ViewRegistry` eingeführt
- `NavigationModel` und `NavigationItem` eingeführt
- `DesktopShell` um Sidebar-, Menü- und Render-Funktionen erweitert
- `DesktopApp` um `start()`, `stop()`, `is_started` und zentrale View-Registrierung erweitert
- Default Views konsolidiert: Dashboard, Documents, Search, RAG, Connectors, Settings
- Default Commands erweitert: Dashboard, Documents, Search, Settings, Workspace Create

## Validierung
- `python3 -m pytest -q tests/desktop`
- Ergebnis: `17 passed in 0.24s`

## Risiko
Niedrig. Keine externen Abhängigkeiten. GUI bleibt headless/testbar.

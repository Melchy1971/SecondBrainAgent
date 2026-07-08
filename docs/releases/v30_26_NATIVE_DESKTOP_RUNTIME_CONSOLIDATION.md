# v30.26 Native Desktop Runtime Consolidation

## Ziel

Jarvis/SecondBrain startet nicht mehr primaer als Web-HUD, sondern als eigenstaendige Desktop-Anwendung. Das Web-HUD bleibt nur als sekundärer Diagnose-/Fallback-Pfad erhalten.

## Umsetzung

- Neues Paket `secondbrain.native`.
- Native Tkinter-App mit Tabs: Dashboard, Dokumente, Gedächtnis, RAG/Produktion, Sprache DE, Einstellungen, Developer.
- `python launcher.py`, `python launcher.py jarvis`, `python launcher.py native-gui` starten native Desktop-App.
- Web-HUD nur noch über `python launcher.py hud` oder `python launcher.py gui-web`.
- Deutsche Sprachsteuerung als deterministischer Offline-Intent-Parser.
- Runtime-Truth wird direkt in das native ViewModel geladen.
- Windows-Startdateien starten native App.

## Neue Befehle

```bash
python launcher.py native-gui
python launcher.py native-status
python launcher.py voice-parse "Jarvis Status"
python launcher.py hud
python launcher.py gui-web
```

## Deutsche Sprachbefehle

- `Jarvis Status`
- `Öffne Dokumente`
- `Suche nach <Begriff>`
- `Frage <Frage>`
- `Repariere Index`
- `Production Gate`
- `Notiere <Text>`

## Akzeptanz

```bash
pytest tests/test_v3026_native_desktop_consolidation.py -q
python launcher.py native-status
python launcher.py voice-parse "Jarvis Status"
```

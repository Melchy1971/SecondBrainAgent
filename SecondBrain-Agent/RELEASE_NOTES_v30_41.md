# Release Notes v30.41 – Native Docking Layout

## Neu
- Native Layout Center für gespeicherte Arbeitslayouts.
- Presets: Standard, Entwicklung, Dokumente, Chat, Analyse, Vollbild.
- Layout-Verwaltung über CLI und Tkinter-GUI.
- AI Workspace zeigt Layout als eigenes Modul.
- Layout-Historie für Änderungen und Aktivierungen.

## Technische Wirkung
- Trennung von UI-Zustand und Modulfunktion.
- Grundlage für dockbare Fenster, Seitenleisten und Arbeitsbereiche.
- Keine Tool-Ausführung beim reinen Statusaufbau.

## Validierung
- `pytest tests/test_v3041_native_docking_layout.py -q`
- `python -m compileall launcher.py secondbrain/native/layout_center secondbrain/native/ai_workspace`
- ZIP-Integrität geprüft.

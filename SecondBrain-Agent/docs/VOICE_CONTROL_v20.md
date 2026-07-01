# Voice Control

Der Dateiname bleibt wegen bestehender Code-Verweise erhalten. Dieses Dokument beschreibt die aktuelle konsolidierte Voice-Pipeline.

## Betriebsarten

1. Native deutsche Textkommandos ohne Audio-Abhaengigkeiten.
2. Launcher-Voice-Foundations fuer Status, Parsing, Sessions und Events.
3. Optionale Mikrofon-/STT-/TTS-Pipeline unter `secondbrain/voice/`.

## Architektur

```text
Mikrofon oder Text
  -> VAD / STT
  -> Wake Word
  -> Intent Router
  -> Risk und Approval Boundary
  -> Launcher / HUD / Diktat
  -> Antwort / TTS / Audit
```

## Native Textkommandos

Beispiele:

```text
Jarvis Status
Suche PostgreSQL pgvector
Frage was fehlt noch
Oeffne Dokumente
Oeffne Einstellungen
Repariere Index
Importiere Datei C:\Pfad\datei.pdf
```

Schreibende Aktionen wie Import und Indexreparatur verlangen Bestaetigung.

## Launcher-Befehle

```powershell
python launcher.py voice-status
python launcher.py voice-parse "Jarvis Status"
python launcher.py voice-status2
python launcher.py voice-session2
python launcher.py voice-wake "Jarvis Status"
python launcher.py voice-transcribe "Jarvis" "zeige" "Status"
python launcher.py voice-parse2 "Jarvis erstelle eine Notiz"
python launcher.py voice-handle2 "Jarvis zeige Status"
python launcher.py voice-speak2 "System bereit"
python launcher.py voice-interrupt --reason user_stop
python launcher.py voice-events
python launcher.py voice-memory
```

## Optionale Audio-Pipeline

```powershell
pip install -e ".[voice]"
python scripts\jarvis_voice.py --diagnose
python scripts\jarvis_voice.py --text "frage: was steht zu pgvector"
python scripts\jarvis_voice.py --once
```

Die Pipeline verwendet austauschbare Adapter. Ohne Audio-Pakete bleibt der Textpfad nutzbar.

## Sicherheit

- Keine beliebige Shell-Ausfuehrung.
- Systemaktionen nur ueber Allowlist und explizite Freigabe.
- Riskante Intents werden blockiert oder approvalpflichtig.
- Diktate werden als neue Inbox-Dateien angelegt und loeschen keine Quelldaten.
- Voice-Sessions und Events duerfen keine Secrets enthalten.

## Bekannte Grenzen

- Mikrofon, STT, TTS und Wake Word muessen auf Zielhardware live abgenommen werden.
- Console-/Manual-Adapter sind kein Nachweis fuer produktive Audioqualitaet.
- Historische Voice-Module bleiben teilweise als Kompatibilitaetsschicht im Code.

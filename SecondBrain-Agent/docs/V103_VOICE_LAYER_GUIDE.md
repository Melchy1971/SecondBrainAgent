# v10.3 Voice Layer

## Enthalten

- Voice Status
- Diktat Import
- Voice Command Router
- Review-first Ausführung
- Hotword vorbereitet
- STT/TTS vorbereitet

## Start

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\run_v103_cycle.py
```

## Diktat importieren

Dateien ablegen:

```text
H:\SecondBrainAgent\SecondBrain-Inbox\Voice\Dictation
```

Dann:

```powershell
python scripts\import_dictation_v103.py
```

## Voice Command prüfen

```powershell
python scripts\voice_command_v103.py "Starte v10 Cycle"
```

## Voice Command ausführen

```powershell
python scripts\voice_command_v103.py "Starte v10 Cycle" --execute
```

## Ergebnisse

```text
133_VoiceLayer
134_VoiceCommands
135_DictationInbox
```

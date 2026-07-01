# Delta v30.35 – Native Voice Control Center

## Inhalt
- Deutsche Voice-Control-Zentrale für native Desktop-App
- Wake-/Push-to-talk-Konfigurationsmodell
- Mikrofon-/TTS-/STT-Statusmodell
- Voice Command History
- Launcher-Befehle für Voice Center
- Tests für Parser, Status und Audit

## Anwenden
ZIP im Repo-Root entpacken. Danach ausführen:

```bash
python launcher.py voice-center-status
python launcher.py voice-command "Jarvis Status"
python launcher.py voice-history
pytest tests/test_v3035_native_voice_control_center.py -q
```

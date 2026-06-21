# SecondBrain OS v13.5 – Voice Companion

## Ziel
v13.5 macht den Voice Layer dialogfähig und bereitet echte Realtime-Sprachsteuerung vor.

## Komponenten
- Wake Word Detector
- Streaming STT Adapter
- Streaming TTS Adapter
- Realtime Conversation
- Voice Memory
- Interrupt Handling
- Voice Command Router
- Approval Boundary für riskante Befehle

## Befehle
```powershell
python launcher.py voice13-status
python launcher.py voice13-wake "Jarvis status"
python launcher.py voice13-transcribe "Jarvis" "zeige" "Status"
python launcher.py voice13-say "System bereit"
python launcher.py voice13-parse "zeige status"
python launcher.py voice13-handle "zeige status"
python launcher.py voice13-remember "Tischtennis Fokus Rückschlag"
python launcher.py voice13-recall Tischtennis
python launcher.py voice13-interrupt --reason user_stop
```

## Grenzen
- Kein echtes Mikrofonstreaming.
- Kein lokales Wake-Word-Modell.
- Keine echte Audiodatei-Erzeugung.
- Adapter sind bewusst austauschbar.

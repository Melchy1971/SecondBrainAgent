# Voice Control v20

Konsolidierte Sprachsteuerung fuer Jarvis. Ersetzt die verstreuten Stub-Module
(`voice_assistant_v9`, `voice_layer_v103`, `voice_runtime_v114`, `voice_realtime`,
`voice_companion`, `realtime_voice`) durch ein Paket: `secondbrain/voice/`.

## Architektur

Pipeline: Mikrofon -> VAD -> STT (Whisper) -> Wake-Word -> Intent-Router ->
Ausfuehrung (HUD/Diktat) -> TTS.

| Baustein | Datei | Aufgabe |
|----------|-------|---------|
| Konfiguration | `voice/config.py` | `VoiceConfig`, Laden aus `runtime/voice/settings.json`, Pfade aus `hud_core` |
| Mikrofon | `voice/audio_stream.py` | `MicrophoneStream` (sounddevice), Aufnahme bis Stille |
| VAD | `voice/vad.py` | Energie-RMS-Schwelle |
| STT | `voice/stt_engine.py` | faster-whisper -> whisper -> manueller Fallback |
| Wake-Word | `voice/wake_word_engine.py` | Substring-Erkennung + `strip()` |
| Routing | `voice/command_router.py` | Text -> `Intent` (rag/run_script/dictation/status/stop) |
| HUD-Bruecke | `voice/hud_bridge.py` | GET auf `/api/rag`, `/api/run`, `/api/status` (Port 8851) |
| Diktat | `voice/dictation.py` | Markdown-Notiz in `SecondBrain-Inbox/Voice/Dictation` |
| Orchestrierung | `voice/controller.py` | `handle_text` (rein), `run_once`/`run_loop` (Hardware) |
| CLI | `scripts/jarvis_voice.py` | `--text` / `--once` / `--loop` / `--diagnose` |
| Launcher | `Jarvis-Voice.bat` | Windows-Start |

## Funktionen

1. **Wake-Word** "Jarvis" aktiviert die Verarbeitung (Modus `wake_word`).
2. **RAG per Stimme**: gesprochene Frage -> `/api/rag` -> Antwort wird vorgelesen.
   Trigger: "frage", "such", "finde", "wo steht", "zeig mir". Unbekannte Aussagen
   werden ebenfalls als Vault-Frage behandelt.
3. **Befehle -> HUD-Aktionen**: bilden auf die HUD-Allowlist ab. Trigger-Beispiele:
   "index bauen" -> `build_vector_rag.py`, "ki import" -> `import_ai_exports.py`,
   "pfade pruefen" -> `check_paths_v9.py`. Standardmaessig **gesperrt**
   (`allow_system_actions=false`); Freigabe mit `--allow-system-actions`.
4. **Diktat in die Inbox**: Trigger "notiz"/"diktiere"/"merke" -> Markdown-Notiz
   (Frontmatter kompatibel zum v103-Diktatimport).

## Sicherheit

- Keine destruktiven Aktionen. Skriptausfuehrung nur ueber die HUD-Allowlist
  und nur bei explizit gesetztem `allow_system_actions`.
- Entspricht `config/voice_layer_v103.yaml` (safety) und der CLAUDE.md-Vorgabe.

## Installation (Windows)

```
pip install -r requirements-voice.txt
```

Optionale Abhaengigkeiten. Ohne sie laeuft nur `--text`. Logik und Tests sind
abhaengigkeitsfrei.

## Bedienung

```
Jarvis.bat                          # HUD starten (Voraussetzung fuer RAG/Status/Skripte)
Jarvis-Voice.bat diagnose           # Provider- und HUD-Status pruefen
Jarvis-Voice.bat                     # Dauerbetrieb mit Wake-Word
python scripts/jarvis_voice.py --text "frage: was steht zu Offshoring"
python scripts/jarvis_voice.py --once
python scripts/jarvis_voice.py --loop --allow-system-actions
```

## Tests

`tests/test_voice_control.py` (19 Tests, hardware-frei): Router, Wake-Word,
Diktat, HUD-Bruecke (gemockt), Controller, Config.

```
python -m pytest tests/test_voice_control.py -q
```

## Altlasten

- Archiviert nach `archive/voice_legacy_v20/`: `voice_companion`, `realtime_voice`
  (nur von eigenen Tests referenziert).
- **Nicht** archiviert, mit Deprecation-Hinweis versehen, da tragend verdrahtet:
  `voice_layer_v103` (v103-Skripte), `voice_runtime_v114` (launcher_runtime_v115),
  `voice_realtime` (launcher_runtime_v126 -> Haupt-`launcher.py`), `voice_assistant_v9`.
  Ein tieferer Refactor dieser Ketten ist separat zu entscheiden.

## Bekannte Grenzen

- STT/TTS/Mikrofon wurden nicht auf Audio-Hardware getestet (Build-Umgebung ohne
  Mikrofon). Die Hardware-Pfade liegen hinter Interfaces mit Fallback; Abnahme per
  `Jarvis-Voice.bat diagnose` und Live-Lauf auf dem Zielrechner erforderlich.
- `hud_core` haelt absolute Pfade (`H:\SecondBrainAgent\...`). Voice-Control erbt
  diese; bei abweichendem Speicherort dort anpassen.

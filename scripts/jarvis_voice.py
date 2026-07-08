"""Voice Control v20 - CLI-Einstieg.

Modi:
  --text "..."   Einmalige Verarbeitung von Text (kein Mikrofon, fuer Tests/Tippen).
  --once         Eine gesprochene Aeusserung aufnehmen, verarbeiten, antworten.
  --loop         Dauerbetrieb mit Wake-Word (Standard).
  --diagnose     Verfuegbare STT/TTS/Audio-Provider und HUD-Status anzeigen.

Beispiele:
  python scripts/jarvis_voice.py --diagnose
  python scripts/jarvis_voice.py --text "frage: was steht zu Offshoring im Vault"
  python scripts/jarvis_voice.py --loop
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from secondbrain.voice import VoiceConfig, VoiceController  # noqa: E402


def diagnose(cfg: VoiceConfig) -> int:
    from secondbrain.voice.stt_engine import SpeechToTextEngine
    from secondbrain.voice.tts_engine import TextToSpeechEngine
    from secondbrain.voice.audio_stream import MicrophoneStream

    print("Voice Control v20 - Diagnose")
    print(f"  Wake-Word        : {cfg.wake_word}")
    print(f"  Modus            : {cfg.mode}")
    print(f"  STT-Provider     : {cfg.stt_provider} (Modell {cfg.stt_model})")
    print(f"  TTS-Provider     : {cfg.tts_provider}")
    print(f"  HUD              : {cfg.hud_url}")
    print(f"  Diktat-Ordner    : {cfg.dictation_dir}")
    print(f"  Systemaktionen   : {'erlaubt' if cfg.allow_system_actions else 'gesperrt'}")
    print(f"  STT verfuegbar   : {SpeechToTextEngine.available_providers()}")
    print(f"  TTS verfuegbar   : {TextToSpeechEngine.available_providers()}")
    print(f"  Mikrofon bereit  : {MicrophoneStream.available()}")
    ctrl = VoiceController(cfg)
    print(f"  HUD erreichbar   : {ctrl.hud.is_up()}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Jarvis Voice Control v20")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--text", help="Text einmalig verarbeiten")
    g.add_argument("--once", action="store_true", help="Eine Aeusserung aufnehmen")
    g.add_argument("--loop", action="store_true", help="Dauerbetrieb mit Wake-Word")
    g.add_argument("--diagnose", action="store_true", help="Provider-Status zeigen")
    ap.add_argument("--allow-system-actions", action="store_true",
                    help="Skriptausfuehrung freischalten (sonst gesperrt)")
    args = ap.parse_args(argv)

    cfg = VoiceConfig.load()
    if args.allow_system_actions:
        cfg.allow_system_actions = True

    if args.diagnose:
        return diagnose(cfg)

    ctrl = VoiceController(cfg)

    if args.text is not None:
        resp = ctrl.handle_text(args.text)
        ctrl.log_session(args.text, resp)
        print(f"[intent] {resp.intent}  [ok] {resp.ok}")
        print(f"[antwort] {resp.speech}")
        if resp.data and resp.data.get("path"):
            print(f"[datei] {resp.data['path']}")
        return 0 if resp.ok else 1

    if args.once:
        resp = ctrl.run_once()
        print(f"[intent] {resp.intent}  [antwort] {resp.speech}")
        return 0 if resp.ok else 1

    # Standard: Loop.
    try:
        ctrl.run_loop()
    except KeyboardInterrupt:
        print("\nBeendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

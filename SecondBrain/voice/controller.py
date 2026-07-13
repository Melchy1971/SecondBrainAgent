"""Voice Control v20 - Orchestrierung.

Verbindet Wake-Word, STT, Intent-Routing, HUD-Bruecke, Diktat und TTS zu einer
Sprachsteuerung. ``handle_text`` ist die reine, hardware-freie Kernlogik
(testbar). ``run_once``/``run_loop`` ergaenzen Mikrofon und Sprachausgabe.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from .command_router import Intent, VoiceCommandRouter
from .config import VoiceConfig
from .dictation import write_dictation
from .hud_bridge import HudBridge
from .wake_word_engine import WakeWordEngine


@dataclass
class Response:
    intent: str
    speech: str          # Text fuer die Sprachausgabe
    ok: bool = True
    data: dict | None = None


class VoiceController:
    def __init__(self, config: VoiceConfig | None = None, hud: HudBridge | None = None,
                 stt=None, tts=None):
        self.cfg = config or VoiceConfig.load()
        self.router = VoiceCommandRouter()
        self.wake = WakeWordEngine(self.cfg.wake_word)
        self.hud = hud or HudBridge(self.cfg.hud_url, self.cfg.hud_timeout)
        self._stt = stt          # lazy - nur fuer Mikrofonbetrieb noetig
        self._tts = tts

    # --- reine Kernlogik (hardware-frei, testbar) ----------------------------
    def handle_text(self, text: str) -> Response:
        intent = self.router.parse(text)
        if intent.kind == "stop":
            return Response("stop", "Beende die Sprachsteuerung.", ok=True)
        if intent.kind == "rag" or intent.kind == "unknown":
            return self._do_rag(intent)
        if intent.kind == "run_script":
            return self._do_script(intent)
        if intent.kind == "dictation":
            return self._do_dictation(intent)
        if intent.kind == "status":
            return self._do_status(intent)
        return Response("unknown", "Das habe ich nicht verstanden.", ok=False)

    def _do_rag(self, intent: Intent) -> Response:
        query = intent.payload or intent.raw
        res = self.hud.rag(query)
        if not res or res.get("ok") is False and "hits" not in res:
            return Response("rag", f"Die Wissensabfrage ist fehlgeschlagen: "
                            f"{res.get('error', 'HUD nicht erreichbar')}.",
                            ok=False, data=res)
        answer = res.get("answer") or "Keine Antwort erhalten."
        return Response("rag", answer, ok=bool(res.get("ok", False)), data=res)

    def _do_script(self, intent: Intent) -> Response:
        if not self.cfg.allow_system_actions:
            return Response("run_script",
                            f"Skriptausfuehrung ist gesperrt (allow_system_actions=false). "
                            f"Vorgesehen war: {intent.payload}.",
                            ok=False, data={"script": intent.payload, "blocked": True})
        res = self.hud.run(intent.payload)
        ok = bool(res.get("ok"))
        msg = ("Skript ausgefuehrt: " if ok else "Skript fehlgeschlagen: ") + intent.payload
        return Response("run_script", msg, ok=ok, data=res)

    def _do_dictation(self, intent: Intent) -> Response:
        text = intent.payload
        if not text:
            return Response("dictation", "Es gab nichts zu notieren.", ok=False)
        path = write_dictation(text, self.cfg.dictation_dir)
        return Response("dictation", "Notiz gespeichert.", ok=True,
                        data={"path": str(path)})

    def _do_status(self, intent: Intent) -> Response:
        res = self.hud.status()
        if not res or res.get("ok") is False:
            return Response("status", "Systemstatus nicht verfuegbar.", ok=False, data=res)
        return Response("status", "Systemstatus abgerufen.", ok=True, data=res)

    # --- Session-Log ---------------------------------------------------------
    def log_session(self, text: str, resp: Response) -> None:
        try:
            path = self.cfg.sessions_log
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                entries = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(entries, list):
                    entries = []
            except Exception:
                entries = []
            entries.append({
                "ts": datetime.now().isoformat(timespec="seconds"),
                "heard": text, "intent": resp.intent,
                "ok": resp.ok, "speech": resp.speech,
            })
            path.write_text(json.dumps(entries[-500:], ensure_ascii=False, indent=2),
                            encoding="utf-8")
        except Exception:
            pass

    # --- Mikrofonbetrieb (Hardware) ------------------------------------------
    def _get_stt(self):
        if self._stt is None:
            from .stt_engine import SpeechToTextEngine
            self._stt = SpeechToTextEngine(self.cfg.stt_provider, self.cfg.stt_model,
                                           self.cfg.language)
        return self._stt

    def _get_tts(self):
        if self._tts is None:
            from .tts_engine import TextToSpeechEngine
            self._tts = TextToSpeechEngine(self.cfg.tts_provider, self.cfg.tts_rate,
                                           self.cfg.language)
        return self._tts

    def say(self, text: str) -> None:
        self._get_tts().speak(text)

    def listen_once(self) -> str:
        from .audio_stream import MicrophoneStream
        mic = MicrophoneStream(self.cfg.sample_rate, self.cfg.silence_threshold,
                               self.cfg.silence_duration, self.cfg.max_utterance_seconds)
        audio = mic.record_utterance()
        return self._get_stt().transcribe_audio(audio, self.cfg.sample_rate)

    def run_once(self, speak: bool = True) -> Response:
        text = self.listen_once()
        if self.cfg.mode == "wake_word" and not self.wake.detect(text):
            return Response("idle", "", ok=True, data={"heard": text})
        if self.cfg.mode == "wake_word":
            text = self.wake.strip(text)
        resp = self.handle_text(text)
        self.log_session(text, resp)
        if speak and resp.speech:
            self.say(resp.speech)
        return resp

    def run_loop(self) -> None:
        self.say(f"Sprachsteuerung aktiv. Sag {self.cfg.wake_word}.")
        while True:
            resp = self.run_once()
            if resp.intent == "stop":
                break

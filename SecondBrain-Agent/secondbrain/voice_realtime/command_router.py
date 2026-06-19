from __future__ import annotations
from .models import VoiceCommand

class VoiceCommandRouter:
    def parse(self, text: str) -> VoiceCommand:
        raw = (text or '').strip()
        low = raw.lower()
        normalized = low.replace('jarvis', '').replace('second brain', '').strip(' ,.:;')
        if any(k in normalized for k in ['status', 'zustand', 'systemstatus']):
            return VoiceCommand('status', raw, 'core-status', {}, 1, False)
        if any(k in normalized for k in ['dashboard', 'übersicht', 'uebersicht']):
            return VoiceCommand('dashboard', raw, 'desktop.dashboard', {}, 1, False)
        if any(k in normalized for k in ['notiz', 'merken', 'capture', 'speichere']):
            return VoiceCommand('capture', raw, 'capture', {'text': raw, 'title': 'Voice Capture'}, 2, False)
        if any(k in normalized for k in ['lösche', 'loesche', 'delete', 'shutdown', 'stoppe', 'beende']):
            return VoiceCommand('risky_action', raw, 'approval.required', {'text': raw}, 4, True)
        return VoiceCommand('ask', raw, 'agent.run', {'task': raw}, 2, False)

"""P5 v23.2 / v30.46.1 - Kompatibilitaets-Alias.

Die Implementierung lebt seit v30.46.1 in secondbrain.chat.streaming.
Bestehende Importe (ChatStream) bleiben gueltig.
"""
from secondbrain.chat.streaming import StreamingManager as ChatStream

__all__ = ["ChatStream"]

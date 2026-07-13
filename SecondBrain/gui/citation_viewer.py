"""P5 v23.2 / v30.46.1 - Kompatibilitaets-Alias.

Die Implementierung lebt seit v30.46.1 in secondbrain.chat.citations.
Der bisherige Kontrakt (render(citations) -> {count, citations}) bleibt.
"""
from secondbrain.chat.citations import CitationRenderer as CitationViewer

__all__ = ["CitationViewer"]

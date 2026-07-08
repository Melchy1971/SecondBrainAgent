"""Voice Control v20 - Bruecke zum Jarvis-HUD.

Ruft die bestehenden, lokalen HUD-Endpoints (127.0.0.1:8851) ueber HTTP GET auf.
Keine neue Logik dupliziert - RAG, Skript-Allowlist und Status leben im HUD.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request


class HudBridge:
    def __init__(self, base_url: str = "http://127.0.0.1:8851", timeout: float = 8.0,
                 opener=None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # opener injizierbar fuer Tests (Standard: urllib).
        self._open = opener or self._urlopen

    def _urlopen(self, url: str) -> str:
        with urllib.request.urlopen(url, timeout=self.timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = self.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        try:
            body = self._open(url)
            return json.loads(body) if body else {}
        except Exception as exc:  # Netzfehler -> sauberes Fehlerobjekt
            return {"ok": False, "error": str(exc), "url": url}

    def is_up(self) -> bool:
        res = self._get("/api/status")
        return bool(res) and "error" not in res

    def rag(self, query: str, limit: int = 5) -> dict:
        return self._get("/api/rag", {"q": query, "limit": limit})

    def run(self, script: str) -> dict:
        return self._get("/api/run", {"script": script})

    def status(self) -> dict:
        return self._get("/api/status")

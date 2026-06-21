"""Jarvis HUD Server (Iron-Man / Stark Look).

Eigenstaendiger HTTP-Server, der die HUD-Oberflaeche ausliefert und Live-Daten
als JSON bereitstellt. Dockt lose an die bestehende GUI (gui_backend_v102) an
und verwendet deren Skript-Runner und Status-Funktionen wieder.

Start:
    python scripts/start_hud.py
    http://127.0.0.1:8851

Endpoints:
    GET /                 -> HUD-Seite (web/jarvis_hud/index.html)
    GET /api/metrics      -> CPU/RAM/SWAP/Disk/Uptime (psutil, mit Fallback)
    GET /api/clock        -> Serverzeit (Browser nutzt primaer lokale Uhr)
    GET /api/weather      -> Open-Meteo (schluesselfrei, Standardort Bonn)
    GET /api/news         -> Tagesschau-RSS Schlagzeilen
    GET /api/status       -> system_status() aus gui_backend_v102
    GET /api/dashboards   -> dashboard_links() aus gui_backend_v102
    GET /api/run?script=  -> Skript ausfuehren (review-first, keine Loeschungen)
    GET /api/rag?q=       -> RAG-Frage an das Vault
    GET /api/logs         -> Tail des GUI-Logs
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

# Funktionen der bestehenden GUI wiederverwenden (DRY, kein Doppelcode).
from secondbrain.gui_backend_v102 import (  # noqa: E402
    LOG_DIR,
    ROOT,
    dashboard_links,
    log_event,
    run_script,
    system_status,
)

HUD_HTML = ROOT / "web" / "jarvis_hud" / "index.html"

# --- Konfiguration -----------------------------------------------------------
# Standardort: Bonn (Telekom-Zentrale). Anpassen, falls gewuenscht.
WEATHER_LAT = 50.7374
WEATHER_LON = 7.0982
WEATHER_PLACE = "Bonn"
NEWS_RSS = "https://www.tagesschau.de/index~rss2.xml"
NEWS_MAX = 8
HTTP_TIMEOUT = 6

# WMO-Wettercodes -> Kurztext (Open-Meteo). Reduziert auf das Wesentliche.
WMO = {
    0: "Klar", 1: "Heiter", 2: "Bewoelkt", 3: "Bedeckt",
    45: "Nebel", 48: "Reifnebel",
    51: "Niesel", 53: "Niesel", 55: "Niesel",
    61: "Regen", 63: "Regen", 65: "Starkregen",
    71: "Schnee", 73: "Schnee", 75: "Schneefall",
    80: "Schauer", 81: "Schauer", 82: "Starkschauer",
    95: "Gewitter", 96: "Gewitter", 99: "Gewitter",
}

try:
    import psutil  # type: ignore
    _HAS_PSUTIL = True
except Exception:  # pragma: no cover - Fallback ohne psutil
    psutil = None  # type: ignore
    _HAS_PSUTIL = False


# --- Datenfunktionen ---------------------------------------------------------
def _disk_path() -> str:
    """Pfad fuer disk_usage: Laufwerk von ROOT, sonst vorhandener Fallback."""
    for cand in (ROOT.anchor, str(ROOT), os.getcwd(), "/"):
        if cand and os.path.exists(cand):
            return cand
    return os.getcwd()


_LAST_NET = {"t": 0.0, "sent": 0, "recv": 0}


def _net_rates() -> dict:
    """Grobe Netzraten (KB/s) zwischen zwei Aufrufen."""
    try:
        io = psutil.net_io_counters()
        now = time.time()
        dt = max(now - _LAST_NET["t"], 1e-6)
        up = (io.bytes_sent - _LAST_NET["sent"]) / dt / 1024
        down = (io.bytes_recv - _LAST_NET["recv"]) / dt / 1024
        first = _LAST_NET["t"] == 0
        _LAST_NET.update(t=now, sent=io.bytes_sent, recv=io.bytes_recv)
        if first:
            return {"up": 0.0, "down": 0.0}
        return {"up": round(max(up, 0), 1), "down": round(max(down, 0), 1)}
    except Exception:
        return {"up": 0.0, "down": 0.0}


def metrics() -> dict:
    """Live-Systemmetriken. Nutzt psutil; faellt sonst auf Minimalwerte zurueck."""
    if not _HAS_PSUTIL:
        return {
            "ok": False,
            "psutil": False,
            "note": "psutil nicht installiert (pip install psutil)",
            "cpu": 0, "ram": 0, "swap": 0,
            "disk_used": 0, "disk_total": 0, "disk_free": 0, "disk_pct": 0,
            "uptime": "n/a", "net": {"up": 0.0, "down": 0.0},
        }
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    disk = psutil.disk_usage(_disk_path())
    up = int(time.time() - psutil.boot_time())
    d, rem = divmod(up, 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    return {
        "ok": True,
        "psutil": True,
        "cpu": round(psutil.cpu_percent(interval=0.2), 1),
        "ram": round(vm.percent, 1),
        "ram_used_gb": round(vm.used / 1e9, 1),
        "ram_total_gb": round(vm.total / 1e9, 1),
        "swap": round(sw.percent, 1),
        "disk_used": round(disk.used / 1e9, 1),
        "disk_total": round(disk.total / 1e9, 1),
        "disk_free": round(disk.free / 1e9, 1),
        "disk_pct": round(disk.percent, 1),
        "uptime": f"{d}d {h}h {m}min",
        "net": _net_rates(),
    }


def weather() -> dict:
    """Aktuelles Wetter + 5-Tage-Vorschau via Open-Meteo (kein API-Key)."""
    params = {
        "latitude": WEATHER_LAT,
        "longitude": WEATHER_LON,
        "current": "temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "timezone": "Europe/Berlin",
        "forecast_days": 5,
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))
        cur = data.get("current", {})
        daily = data.get("daily", {})
        days = []
        labels = ["Heute", "Morgen", "Tag 3", "Tag 4", "Tag 5"]
        for i, date in enumerate(daily.get("time", [])[:5]):
            days.append({
                "label": labels[i] if i < len(labels) else date,
                "date": date,
                "max": round(daily["temperature_2m_max"][i]),
                "min": round(daily["temperature_2m_min"][i]),
                "text": WMO.get(daily["weather_code"][i], "?"),
            })
        return {
            "ok": True,
            "place": WEATHER_PLACE,
            "temp": round(cur.get("temperature_2m", 0)),
            "text": WMO.get(cur.get("weather_code"), "?"),
            "humidity": round(cur.get("relative_humidity_2m", 0)),
            "wind": round(cur.get("wind_speed_10m", 0)),
            "days": days,
        }
    except Exception as exc:  # offline / blockiert
        return {"ok": False, "place": WEATHER_PLACE, "error": str(exc)}


def news() -> dict:
    """Schlagzeilen aus dem Tagesschau-RSS."""
    try:
        req = urllib.request.Request(NEWS_RSS, headers={"User-Agent": "JarvisHUD/1.0"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            root = ET.fromstring(r.read())
        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "").strip()
            if title:
                items.append(title)
            if len(items) >= NEWS_MAX:
                break
        return {"ok": True, "source": "tagesschau.de", "items": items}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "items": []}


def tail_log(limit: int = 12000) -> str:
    log = LOG_DIR / "jarvis_gui.log"
    if not log.exists():
        return "Noch keine Logs."
    return log.read_text(encoding="utf-8", errors="ignore")[-limit:]


# --- HTTP-Handler ------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # ruhiger Output
        pass

    def _send(self, body: bytes, ctype: str, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data):
        self._send(json.dumps(data, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        try:
            if path in ("/", "/index.html"):
                if HUD_HTML.exists():
                    self._send(HUD_HTML.read_bytes(), "text/html; charset=utf-8")
                else:
                    self._send(b"index.html fehlt: web/jarvis_hud/index.html",
                               "text/plain; charset=utf-8", 404)
            elif path == "/api/metrics":
                self._json(metrics())
            elif path == "/api/clock":
                self._json({"time": datetime.now().strftime("%H:%M:%S"),
                            "date": datetime.now().strftime("%Y-%m-%d")})
            elif path == "/api/weather":
                self._json(weather())
            elif path == "/api/news":
                self._json(news())
            elif path == "/api/status":
                self._json(system_status())
            elif path == "/api/dashboards":
                self._json(dashboard_links())
            elif path == "/api/run":
                script = qs.get("script", [""])[0]
                if not script:
                    self._json({"ok": False, "output": "Kein Skript angegeben."})
                else:
                    self._json(run_script(script))
            elif path == "/api/rag":
                q = qs.get("q", [""])[0]
                self._json(run_script("rag_answer.py", q) if q
                           else {"ok": False, "output": "Keine Frage uebergeben."})
            elif path == "/api/logs":
                self._json({"log": tail_log()})
            else:
                self._send(b"404", "text/plain", 404)
        except Exception as exc:  # nichts soll den Server killen
            log_event("hud.error", {"path": path, "error": str(exc)})
            self._json({"ok": False, "error": str(exc)})


def start(host: str = "127.0.0.1", port: int = 8851):
    log_event("hud.start", {"host": host, "port": port, "psutil": _HAS_PSUTIL})
    print(f"Jarvis HUD: http://{host}:{port}  (psutil={_HAS_PSUTIL})")
    HTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    start()

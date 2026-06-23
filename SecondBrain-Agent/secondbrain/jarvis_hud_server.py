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

# Geteilte, GUI-neutrale Logik aus dem Kernmodul (Phase 2).
from secondbrain.hud_core import (  # noqa: E402
    LOG_DIR,
    ROOT,
    VAULT,
    dashboard_links,
    now,
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


# --- Einstellungen (persistent) ---------------------------------------------
SETTINGS_FILE = ROOT / "config" / "hud_settings.json"

DEFAULT_SETTINGS = {
    "place": WEATHER_PLACE,
    "lat": WEATHER_LAT,
    "lon": WEATHER_LON,
    "news_rss": NEWS_RSS,
    "news_max": NEWS_MAX,
    "weather_min": 15,   # Wetter-Refresh im Browser (Minuten)
    "accent": "#2fe6ff",  # HUD-Akzentfarbe
}
# Welche Felder duerfen ueberschrieben werden + Typ/Begrenzung.
_NUM = {"lat": (-90, 90), "lon": (-180, 180), "news_max": (1, 20), "weather_min": (1, 720)}


def load_settings() -> dict:
    """Settings aus Datei, fehlende Werte aus DEFAULT_SETTINGS."""
    data = dict(DEFAULT_SETTINGS)
    try:
        if SETTINGS_FILE.exists():
            data.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
    except Exception as exc:
        log_event("hud.settings_read_error", {"error": str(exc)})
    return data


def save_settings(incoming: dict) -> dict:
    """Validiert eingehende Werte, mischt mit Bestand, schreibt Datei."""
    current = load_settings()
    for key, val in (incoming or {}).items():
        if key not in DEFAULT_SETTINGS:
            continue
        if key in _NUM:
            try:
                num = float(val)
            except (TypeError, ValueError):
                continue
            lo, hi = _NUM[key]
            num = max(lo, min(hi, num))
            current[key] = int(num) if key in ("news_max", "weather_min") else num
        else:
            current[key] = str(val)[:300]
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    log_event("hud.settings_saved", current)
    return current


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
    cfg = load_settings()
    place = cfg["place"]
    params = {
        "latitude": cfg["lat"],
        "longitude": cfg["lon"],
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
            "place": place,
            "temp": round(cur.get("temperature_2m", 0)),
            "text": WMO.get(cur.get("weather_code"), "?"),
            "humidity": round(cur.get("relative_humidity_2m", 0)),
            "wind": round(cur.get("wind_speed_10m", 0)),
            "days": days,
        }
    except Exception as exc:  # offline / blockiert
        return {"ok": False, "place": place, "error": str(exc)}


def news() -> dict:
    """Schlagzeilen aus dem konfigurierten RSS-Feed."""
    cfg = load_settings()
    try:
        req = urllib.request.Request(cfg["news_rss"], headers={"User-Agent": "JarvisHUD/1.0"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            root = ET.fromstring(r.read())
        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "").strip()
            if title:
                items.append(title)
            if len(items) >= cfg["news_max"]:
                break
        return {"ok": True, "source": cfg["news_rss"], "items": items}
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


    # --- HTML / statische Auslieferung ------------------------------------
    def _html(self, path: Path):
        try:
            body = path.read_text(encoding="utf-8").encode("utf-8")
        except Exception as exc:
            self._send(f"HUD-Seite nicht gefunden: {exc}".encode("utf-8"),
                       "text/plain; charset=utf-8", code=500)
            return
        self._send(body, "text/html; charset=utf-8")

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self._html(HUD_HTML)
        elif path == "/api/metrics":
            self._json(metrics())
        elif path == "/api/clock":
            self._json({"ok": True, "time": now(),
                        "iso": datetime.now().isoformat(timespec="seconds")})
        elif path == "/api/weather":
            self._json(weather())
        elif path == "/api/news":
            self._json(news())
        elif path == "/api/status":
            self._json(system_status())
        elif path == "/api/dashboards":
            self._json({"ok": True, "links": dashboard_links()})
        elif path == "/api/settings":
            self._json({"ok": True, "settings": load_settings()})
        elif path == "/api/logs":
            self._json({"ok": True, "log": tail_log()})
        elif path == "/api/run":
            script = (qs.get("script", [""])[0] or "").strip()
            self._json(run_allowed_script(script))
        elif path == "/api/rag":
            query = (qs.get("q", [""])[0] or "").strip()
            self._json(rag_answer(query))
        else:
            self._json({"ok": False, "error": f"Unbekannter Pfad: {path}"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/api/settings":
            saved = save_settings(body)
            self._json({"ok": True, "settings": saved})
        elif path == "/api/rag":
            query = str(body.get("q", "")).strip()
            self._json(rag_answer(query))
        elif path == "/api/run":
            script = str(body.get("script", "")).strip()
            self._json(run_allowed_script(script))
        else:
            self._json({"ok": False, "error": f"Unbekannter Pfad: {path}"})


# --- Skript-Runner (Allowlist, review-first) ---------------------------------
# Nur explizit freigegebene Skripte. Keine Loeschaktionen, keine freie Eingabe.
ALLOWED_SCRIPTS = {
    "run_v10_cycle.py",
    "run_v101_cycle.py",
    "import_ai_exports.py",
    "build_vector_rag.py",
    "check_paths_v9.py",
    "release_gate_v9.py",
    "run_regression_tests_v9.py",
}


def run_allowed_script(script: str) -> dict:
    """Fuehrt nur Skripte aus der Allowlist aus (review-first, keine Loeschungen)."""
    if not script:
        return {"ok": False, "script": script, "output": "Kein Skript angegeben."}
    if script not in ALLOWED_SCRIPTS:
        log_event("hud.run_blocked", {"script": script})
        return {"ok": False, "script": script,
                "output": f"Nicht freigegeben: {script}. Erlaubt: {sorted(ALLOWED_SCRIPTS)}"}
    return run_script(script)


# --- RAG ueber das Vault -----------------------------------------------------
# Robust und dependency-frei: Keyword-Retrieval ueber die echten Vault-Notizen.
_STOPWORDS = {
    "der", "die", "das", "und", "oder", "ein", "eine", "ist", "im", "in", "am",
    "an", "auf", "fuer", "fur", "mit", "von", "zu", "den", "dem", "des", "wie",
    "was", "wer", "wo", "wann", "warum", "welche", "welcher", "welches", "the",
    "and", "or", "a", "an", "is", "of", "to", "for", "in", "on", "with", "what",
}


def _tokenize(text: str) -> list:
    out, word = [], []
    for ch in text.lower():
        if ch.isalnum() or ch in "äöüß":
            word.append(ch)
        elif word:
            out.append("".join(word))
            word = []
    if word:
        out.append("".join(word))
    return out


def rag_answer(query: str, limit: int = 5) -> dict:
    """Beantwortet eine Vault-Frage. Liefert beste Treffer + kurze Synthese."""
    query = (query or "").strip()
    if not query:
        return {"ok": False, "query": query, "answer": "Keine Frage angegeben.", "hits": []}

    terms = [t for t in _tokenize(query) if t not in _STOPWORDS and len(t) > 1]
    if not terms:
        terms = _tokenize(query)
    if not VAULT.exists():
        return {"ok": False, "query": query,
                "answer": f"Vault nicht gefunden: {VAULT}", "hits": []}

    scored = []
    term_set = set(terms)
    for note in VAULT.rglob("*.md"):
        if "99_System" in note.parts:
            continue
        try:
            text = note.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        low = text.lower()
        score = sum(low.count(t) for t in term_set)
        score += sum(3 for t in term_set if t in note.stem.lower())
        if score > 0:
            idx = min((low.find(t) for t in term_set if t in low), default=0)
            start = max(0, idx - 120)
            preview = text[start:start + 320].replace("\n", " ").strip()
            scored.append((score, note, preview))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]
    hits = [{
        "note": str(note.relative_to(VAULT)),
        "score": score,
        "preview": preview,
    } for score, note, preview in top]

    if not hits:
        answer = f"Keine Treffer im Vault fuer: {query}"
    else:
        names = ", ".join(h["note"] for h in hits[:3])
        answer = f"{len(hits)} relevante Notiz(en) gefunden. Top-Treffer: {names}."
    log_event("hud.rag", {"query": query, "hits": len(hits)})
    return {"ok": bool(hits), "query": query, "answer": answer, "hits": hits}


# --- Server-Bootstrap --------------------------------------------------------
def run(host: str = "127.0.0.1", port: int = 8851) -> None:
    port = int(os.environ.get("HUD_PORT", port))
    host = os.environ.get("HUD_HOST", host)
    server = HTTPServer((host, port), Handler)
    log_event("hud.start", {"host": host, "port": port})
    print(f"Jarvis HUD laeuft: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nHUD gestoppt.")
    finally:
        server.server_close()
        log_event("hud.stop", {"host": host, "port": port})


# Kompatibler Alias fuer Aufrufer (z. B. scripts/start_hud.py).
start = run


if __name__ == "__main__":
    run()

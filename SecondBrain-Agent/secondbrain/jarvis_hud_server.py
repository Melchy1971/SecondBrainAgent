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
    GET /api/assistant/models  -> verfuegbare Ollama-Modelle
    POST /api/assistant        -> RAG-gestuetzter Chat (query, history)
    POST /api/assistant/note   -> Assistant-Antwort als Notiz speichern
    GET /api/documents?path=   -> Vault-Ordner listen (read-only)
    GET /api/document?path=    -> Notiz-Inhalt lesen (read-only)
    GET /api/documents/stats   -> echter Markdown-Bestand
    GET /api/document-center/status -> P1 Document Center Runtime Truth
    GET /api/memory            -> Vault-Memory-Ordner gruppiert (read-only)
    GET /api/memory/stats      -> echter Memory-Bestand
    GET /api/memory-center/status -> Memory Center Runtime Truth
    GET /api/knowledge/stats   -> Wissensgraph-Kennzahlen
    GET /api/knowledge/entities-> Entitaeten (Suche/Typ/Limit, dedupliziert)
    GET /api/knowledge/entity  -> Entitaet-Detail (Beziehungen + Quellnotiz)
    GET /api/search?q=&type=&tag= -> Volltextsuche mit Facetten
    GET /api/search/facets     -> verfuegbare Typen + Tags
    GET /api/imports/status    -> Inbox-Quellen + letzte Import-Reports
    POST /api/imports/zip      -> ZIP-Upload (base64) + Import der gewaehlten Quelle
    GET /api/jobs              -> Allowlist-Jobs + Lauf-Historie aus dem Log
    GET /api/connectors        -> Connector-Konfig-Status + Ollama-Live-Check
    GET /api/agents            -> Agent-Registry-Katalog (read-only)
    GET /api/dev/info          -> Developer-Diagnose + Endpunkt-Katalog
    GET /api/coding/models     -> verfuegbare Coding-Modelle
    POST /api/coding/generate  -> Code generieren (Ollama, kein Ausfuehren)
    POST /api/coding/save      -> generierten Code als Datei speichern
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
from secondbrain.gui.document_center_runtime import document_center_status  # noqa: E402
from secondbrain.gui.memory_center_runtime import memory_center_status  # noqa: E402
from secondbrain.hud_core import (  # noqa: E402
    INBOX,
    LOG_DIR,
    ROOT,
    VAULT,
    dashboard_links,
    now,
    log_event,
    run_script,
    system_status,
)
from secondbrain.security_cameras import (  # noqa: E402
    cameras_overview,
    cameras_save,
    cameras_discover,
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
    # --- Standort / Wetter / News / Darstellung ---
    "place": WEATHER_PLACE,
    "lat": WEATHER_LAT,
    "lon": WEATHER_LON,
    "news_rss": NEWS_RSS,
    "news_max": NEWS_MAX,
    "weather_min": 15,   # Wetter-Refresh im Browser (Minuten)
    "accent": "#2fe6ff",  # HUD-Akzentfarbe
    # --- Identitaet / Header ---
    "version": "v30.21",
    "environment": "production",
    "log_level": "INFO",
    "system_health": "EXCELLENT",
    "system_status_text": "All Systems Operational",
    "user_name": "Jarvis",
    "user_role": "Administrator",
    # --- Datenbank / Stack ---
    "database": "PostgreSQL 16 + pgvector",
    "postgres_status": "ONLINE",
    "pgvector_version": "1.0.5",
    "embedding_provider": "OpenAI",
    "embedding_model": "text-embedding-3-small",
    "embedding_dim": 1536,
    "ollama_url": "http://localhost:11434",
    "ollama_models": 7,
    "memory_engine": "LangGraph + Memory Store",
    # --- Queue / Release Gate ---
    "queue_name": "Redis Queue",
    "queue_pending": 3,
    "release_blocking": 0,
    # --- Statusleiste / Zaehler ---
    "backup_active": "Aktiv",
    "sync_active": "Aktiv",
    "connectors": 8,
    "agents_active": 3,
    "vectors": 1248932,
    "documents": 4392,
    "memories": 12845,
    "backup_last": "15:23",
    "backup_next": "Heute, 22:00",
    "vector_index": "OK",
    # --- Assistant (Chat) ---
    "assistant_engine": "ollama",          # ollama | openai
    "assistant_model": "",                 # leer = erstes verfuegbares Ollama-Modell
    "assistant_models": "llama3.1, qwen, deepseek-coder, gemma",  # Auswahl rechts (Komma-getrennt)
    "assistant_temperature": 0.2,
    "assistant_context_chunks": 5,
    # --- Coding ---
    "coding_engine": "ollama",             # ollama | openai | gemini | anthropic
    "coding_model": "deepseek-coder",      # leer = erstes verfuegbares (bevorzugt coder)
    "coding_temperature": 0.1,
    # --- API-Keys (Klartext, lokal) ---
    "openai_api_key": "",
    "gemini_api_key": "",
    "anthropic_api_key": "",
}
# Welche Zahlenfelder duerfen ueberschrieben werden + erlaubter Bereich.
_NUM = {
    "lat": (-90, 90), "lon": (-180, 180),
    "news_max": (1, 20), "weather_min": (1, 720),
    "embedding_dim": (1, 100000), "ollama_models": (0, 10000),
    "queue_pending": (0, 1000000), "release_blocking": (0, 1000000),
    "connectors": (0, 100000), "agents_active": (0, 100000),
    "vectors": (0, 10 ** 12), "documents": (0, 10 ** 12), "memories": (0, 10 ** 12),
    "assistant_temperature": (0, 2), "assistant_context_chunks": (1, 20),
    "coding_temperature": (0, 2),
}
# Zahlenfelder, die als Ganzzahl gespeichert werden (Rest bleibt float).
_INT = {
    "news_max", "weather_min", "embedding_dim", "ollama_models",
    "queue_pending", "release_blocking", "connectors", "agents_active",
    "vectors", "documents", "memories", "assistant_context_chunks",
}


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
            current[key] = int(num) if key in _INT else num
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
        elif path == "/api/assistant/models":
            self._json(assistant_models())
        elif path == "/api/documents":
            self._json(documents_list((qs.get("path", [""])[0] or "")))
        elif path == "/api/document":
            self._json(document_read((qs.get("path", [""])[0] or "")))
        elif path == "/api/documents/stats":
            self._json(documents_stats())
        elif path == "/api/document-center/status":
            self._json(document_center_status(ROOT))
        elif path == "/api/memory":
            self._json(memory_list())
        elif path == "/api/memory/stats":
            self._json(memory_stats())
        elif path == "/api/memory-center/status":
            self._json(memory_center_status(ROOT))
        elif path == "/api/knowledge/stats":
            self._json(knowledge_stats())
        elif path == "/api/knowledge/entities":
            self._json(knowledge_entities(qs.get("q", [""])[0], qs.get("type", [""])[0],
                                          qs.get("limit", ["50"])[0], qs.get("offset", ["0"])[0]))
        elif path == "/api/knowledge/entity":
            self._json(knowledge_entity(qs.get("name", [""])[0]))
        elif path == "/api/search":
            self._json(search_query(qs.get("q", [""])[0], qs.get("type", [""])[0],
                                    qs.get("tag", [""])[0], qs.get("limit", ["50"])[0]))
        elif path == "/api/search/facets":
            self._json(search_facets())
        elif path == "/api/imports/status":
            self._json(imports_status())
        elif path == "/api/jobs":
            self._json(jobs_overview())
        elif path == "/api/connectors":
            self._json(connectors_overview())
        elif path == "/api/agents":
            self._json(agents_overview())
        elif path == "/api/dev/info":
            self._json(dev_info())
        elif path == "/api/stats":
            self._json(hud_stats())
        elif path == "/api/coding/models":
            self._json(coding_models())
        elif path == "/api/security/cameras":
            self._json(cameras_overview())
        elif path == "/api/security/discover":
            self._json(cameras_discover())
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
        elif path == "/api/assistant":
            query = str(body.get("query", "")).strip()
            history = body.get("history") if isinstance(body.get("history"), list) else []
            self._json(assistant_chat(query, history))
        elif path == "/api/assistant/note":
            self._json(assistant_save_note(str(body.get("title", "")),
                                           str(body.get("content", ""))))
        elif path == "/api/imports/zip":
            self._json(imports_zip(body))
        elif path == "/api/coding/generate":
            self._json(coding_generate(str(body.get("prompt", "")),
                                       str(body.get("language", "")), str(body.get("model", "")),
                                       str(body.get("engine", ""))))
        elif path == "/api/coding/save":
            self._json(coding_save(str(body.get("filename", "")), str(body.get("content", ""))))
        elif path == "/api/security/cameras":
            self._json(cameras_save(body))
        else:
            self._json({"ok": False, "error": f"Unbekannter Pfad: {path}"})


# --- Skript-Runner (Allowlist, review-first) ---------------------------------
# Nur explizit freigegebene Skripte. Keine Loeschaktionen, keine freie Eingabe.
ALLOWED_SCRIPTS = {
    # Zyklen
    "run_v10_cycle.py",
    "run_v101_cycle.py",
    "run_os_cycle.py",
    "run_secondbrain_os_cycle.py",
    "run_intelligence_cycle.py",
    # Gates & Qualitaet
    "release_gate_v9.py",
    "production_gate.py",
    "production_ready_gate_v96.py",
    "run_quality_gate.py",
    "run_quality_report.py",
    "run_regression_tests_v9.py",
    "run_tests.py",
    # Checks & Health
    "check_paths_v9.py",
    "ai_healthcheck.py",
    "healthcheck.py",
    "run_sync_health.py",
    "run_conflict_report.py",
    "run_governance.py",
    # Index & Import
    "build_vector_rag.py",
    "reindex.py",
    "import_ai_exports.py",
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


# --- Assistant (RAG-gestuetzter Chat) ----------------------------------------
# Retrieval ueber den vorhandenen Token-Chunk-Index (search_rag), Generierung
# ueber das lokale Ollama. Embeddings sind hier bewusst NICHT im Spiel: der
# Index speichert Tokens, keine Vektoren. Sobald build_rag_index echte
# Embeddings ablegt, kann _assistant_retrieve auf Vektorsuche umgestellt werden
# (Seam). Bis dahin ist dies ehrlich ein Token-Retrieval, kein Vektor-RAG.

def _vault_settings() -> dict:
    """Minimal-Settings fuer secondbrain.rag.search_rag."""
    return {"vault_path": str(VAULT), "vault_folders": {"system": "99_System"}}


def _assistant_retrieve(query: str, limit: int) -> list:
    """Top-Chunks aus dem Vault. Faellt bei Importfehlern leise auf []."""
    try:
        from secondbrain.rag import search_rag  # lazy: haelt Serverstart frei
        return search_rag(_vault_settings(), query, limit=limit)
    except Exception as exc:  # pragma: no cover - defensive
        log_event("hud.assistant_retrieve_error", {"error": str(exc)})
        return []


def _ollama_models(base_url: str) -> list:
    """Verfuegbare Ollama-Modelle (Namen). Leere Liste, wenn nicht erreichbar."""
    try:
        url = base_url.rstrip("/") + "/api/tags"
        with urllib.request.urlopen(url, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


def _ollama_chat(base_url: str, model: str, prompt: str, temperature: float) -> str:
    """Generierung ueber Ollama /api/generate (dependency-frei)."""
    url = base_url.rstrip("/") + "/api/generate"
    payload = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": float(temperature)},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8")).get("response", "").strip()


def _openai_chat(model: str, prompt: str, temperature: float) -> str:
    """Generierung ueber OpenAI (= ChatGPT). Key aus Settings oder OPENAI_API_KEY."""
    key = load_settings().get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Kein OpenAI-Key (Einstellungen oder OPENAI_API_KEY)")
    url = "https://api.openai.com/v1/chat/completions"
    payload = json.dumps({
        "model": model or "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": float(temperature),
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def _gemini_chat(model: str, prompt: str, temperature: float) -> str:
    """Generierung ueber Google Gemini. Key aus Settings oder GEMINI_API_KEY."""
    key = (load_settings().get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
           or os.environ.get("GOOGLE_API_KEY"))
    if not key:
        raise RuntimeError("Kein Gemini-Key (Einstellungen oder GEMINI_API_KEY)")
    model = model or "gemini-1.5-flash"
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": float(temperature)},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    cands = data.get("candidates") or []
    if not cands:
        raise RuntimeError("Gemini: keine Antwort")
    parts = (cands[0].get("content") or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts).strip()


def _anthropic_chat(model: str, prompt: str, temperature: float) -> str:
    """Generierung ueber Anthropic Claude. Key aus Settings oder ANTHROPIC_API_KEY."""
    key = load_settings().get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("Kein Anthropic-Key (Einstellungen oder ANTHROPIC_API_KEY)")
    model = model or "claude-3-5-sonnet-latest"
    url = "https://api.anthropic.com/v1/messages"
    payload = json.dumps({
        "model": model, "max_tokens": 4096, "temperature": float(temperature),
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json", "x-api-key": key,
        "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    blocks = data.get("content") or []
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()


def _llm_chat(engine: str, model: str, prompt: str, temperature: float):
    """Routet zur gewaehlten Engine. Liefert (text, model_used)."""
    engine = (engine or "ollama").lower()
    if engine == "openai":
        m = model or "gpt-4o-mini"
        return _openai_chat(m, prompt, temperature), m
    if engine == "gemini":
        m = model or "gemini-1.5-flash"
        return _gemini_chat(m, prompt, temperature), m
    if engine in ("anthropic", "claude"):
        m = model or "claude-3-5-sonnet-latest"
        return _anthropic_chat(m, prompt, temperature), m
    # Ollama (Default)
    cfg = load_settings()
    base = cfg.get("ollama_url") or "http://localhost:11434"
    m = model or ""
    if not m:
        avail = _ollama_models(base)
        m = avail[0] if avail else ""
    if not m:
        raise RuntimeError("kein Ollama-Modell verfuegbar")
    return _ollama_chat(base, m, prompt, temperature), m


def _build_prompt(query: str, chunks: list, history: list) -> str:
    parts = [
        "Du bist der SecondBrain-Assistant. Antworte praezise auf Deutsch,",
        "ausschliesslich gestuetzt auf den folgenden Kontext aus dem Vault.",
        "Reicht der Kontext nicht, sag das offen. Erfinde nichts.",
        "Verweise im Text mit [1], [2] ... auf die genutzten Quellen.",
        "",
    ]
    for turn in (history or [])[-6:]:
        role = "Nutzer" if turn.get("role") == "user" else "Assistant"
        parts.append(f"{role}: {str(turn.get('content',''))[:600]}")
    if history:
        parts.append("")
    parts.append("Kontext:")
    if chunks:
        for i, c in enumerate(chunks, 1):
            parts.append(f"[{i}] {c.get('note','?')}: {str(c.get('preview',''))[:500]}")
    else:
        parts.append("(kein Kontext gefunden)")
    parts += ["", f"Frage: {query}", "", "Antwort:"]
    return "\n".join(parts)


def assistant_chat(query: str, history: list | None = None) -> dict:
    """RAG-gestuetzte Chat-Antwort. Retrieval + Generierung, mit Fallback."""
    query = (query or "").strip()
    if not query:
        return {"ok": False, "answer": "Keine Frage angegeben.", "sources": [],
                "llm_ok": False, "engine": "", "model": ""}
    cfg = load_settings()
    engine = (cfg.get("assistant_engine") or "ollama").lower()
    temp = cfg.get("assistant_temperature", 0.2)
    limit = int(cfg.get("assistant_context_chunks", 5) or 5)
    chunks = _assistant_retrieve(query, limit)
    sources = [{"note": c.get("note", ""), "score": c.get("score", 0),
                "chunk_id": c.get("chunk_id", 0),
                "preview": str(c.get("preview", ""))[:240]} for c in chunks]
    prompt = _build_prompt(query, chunks, history)

    model = cfg.get("assistant_model") or ""
    llm_ok, answer = False, ""
    try:
        answer, model = _llm_chat(engine, model, prompt, temp); llm_ok = True
    except Exception as exc:
        log_event("hud.assistant_llm_error", {"engine": engine, "error": str(exc)})
        if sources:
            names = ", ".join(s["note"] for s in sources[:3])
            answer = (f"LLM nicht erreichbar ({exc}). {len(sources)} Treffer im "
                      f"Vault. Top: {names}.")
        else:
            answer = f"LLM nicht erreichbar ({exc}) und keine Vault-Treffer."

    log_event("hud.assistant", {"query": query, "sources": len(sources),
                                "engine": engine, "llm_ok": llm_ok})
    return {"ok": True, "answer": answer, "sources": sources,
            "llm_ok": llm_ok, "engine": engine, "model": model}


def assistant_save_note(title: str, content: str) -> dict:
    """Speichert einen Assistant-Output als NEUE Notiz im Inbox-Ordner.
    Review-first: legt nur an, ueberschreibt/loescht nie."""
    content = (content or "").strip()
    if not content:
        return {"ok": False, "error": "Kein Inhalt."}
    folder = VAULT / "00_Inbox"
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"ok": False, "error": f"Inbox nicht beschreibbar: {exc}"}
    base = "".join(c if c.isalnum() else "-" for c in (title or "assistant").lower())
    base = base.strip("-")[:60] or "assistant"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = folder / f"{stamp}_{base}.md"
    n = 1
    while target.exists():  # niemals ueberschreiben
        target = folder / f"{stamp}_{base}_{n}.md"; n += 1
    head = f"# {title or 'Assistant-Notiz'}\n\n_Quelle: Jarvis Assistant · {now()}_\n\n"
    try:
        target.write_text(head + content + "\n", encoding="utf-8")
    except Exception as exc:
        return {"ok": False, "error": f"Schreibfehler: {exc}"}
    log_event("hud.assistant_note", {"file": str(target.relative_to(VAULT))})
    return {"ok": True, "file": str(target.relative_to(VAULT))}


def assistant_models() -> dict:
    """Modelle fuer die UI: konfigurierte (Settings) + live aus Ollama, vereinigt.
    Konfigurierte zuerst, damit die Auswahl auch ohne laufendes Ollama steht."""
    cfg = load_settings()
    base = cfg.get("ollama_url") or "http://localhost:11434"
    configured = [m.strip() for m in str(cfg.get("assistant_models", "")).split(",") if m.strip()]
    live = _ollama_models(base)
    merged = list(dict.fromkeys(configured + live))
    return {"ok": True, "engine": cfg.get("assistant_engine", "ollama"),
            "active": cfg.get("assistant_model", ""),
            "configured": configured, "live": live, "models": merged}


# --- Documents (Vault-Browser, read-only) ------------------------------------
# Liest ausschliesslich innerhalb des Vault. Jeder Pfad wird gegen Ausbruch
# (path traversal) geprueft: nur Pfade unterhalb von VAULT sind zulaessig.

def _safe_vault_path(rel: str):
    """Loest rel relativ zum Vault auf und stellt Containment sicher."""
    base = VAULT.resolve()
    try:
        target = (base / (rel or "")).resolve()
    except Exception:
        return None
    if target == base or base in target.parents:
        return target
    return None


def _doc_rel(p) -> str:
    try:
        return str(p.relative_to(VAULT.resolve())).replace("\\", "/")
    except Exception:
        return ""


def documents_list(rel: str = "") -> dict:
    """Listet die direkten Kinder eines Vault-Ordners (Ordner + .md-Dateien)."""
    base = VAULT.resolve()
    target = _safe_vault_path(rel)
    if target is None or not target.exists() or not target.is_dir():
        return {"ok": False, "error": "Pfad ungueltig", "path": rel, "entries": []}
    dirs, files = [], []
    for child in sorted(target.iterdir(), key=lambda c: c.name.lower()):
        if child.name.startswith("."):
            continue
        try:
            st = child.stat()
        except Exception:
            continue
        entry = {"name": child.name, "path": _doc_rel(child), "mtime": int(st.st_mtime)}
        if child.is_dir():
            entry["type"] = "dir"
            dirs.append(entry)
        elif child.suffix.lower() == ".md":
            entry["type"] = "file"
            entry["size"] = st.st_size
            files.append(entry)
    return {"ok": True, "path": ("" if target == base else _doc_rel(target)),
            "entries": dirs + files}


def document_read(rel: str) -> dict:
    """Liefert den Inhalt einer einzelnen .md-Notiz (read-only, pfadgeschuetzt)."""
    target = _safe_vault_path(rel)
    if (target is None or not target.exists() or not target.is_file()
            or target.suffix.lower() != ".md"):
        return {"ok": False, "error": "Datei ungueltig"}
    try:
        text = target.read_text(encoding="utf-8", errors="ignore")
        st = target.stat()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "path": _doc_rel(target), "content": text,
            "size": st.st_size, "mtime": int(st.st_mtime)}


def documents_stats() -> dict:
    """Echter Markdown-Bestand im Vault (ohne 99_System und versteckte Ordner)."""
    base = VAULT.resolve()
    count = 0
    try:
        for p in base.rglob("*.md"):
            parts = p.parts
            if "99_System" in parts or any(s.startswith(".") for s in parts):
                continue
            count += 1
    except Exception as exc:
        return {"ok": False, "error": str(exc), "count": 0}
    return {"ok": True, "count": count}


# --- Memory (Vault-Erinnerungsordner, read-only) -----------------------------
# Einzige real befuellte Quelle sind die Memory-Ordner im Vault. Der JSON-/DB-
# Store (DesktopStore, sqlite-Tabelle 'memories') ist Geruest ohne Daten und
# wird hier bewusst NICHT als Quelle ausgegeben.
_MEMORY_DIRS = ("22_Memory", "48_AgentMemory", "100_MemoryEngine")


def memory_list() -> dict:
    """Erinnerungen aus den Vault-Memory-Ordnern, nach Kategorie gruppiert."""
    base = VAULT.resolve()
    groups, total = [], 0
    for d in _MEMORY_DIRS:
        folder = base / d
        if not folder.exists() or not folder.is_dir():
            continue
        entries = []
        for p in sorted(folder.rglob("*.md"), key=lambda c: c.name.lower()):
            if any(s.startswith(".") for s in p.parts):
                continue
            try:
                st = p.stat()
            except Exception:
                continue
            entries.append({"name": p.stem, "file": p.name, "path": _doc_rel(p),
                            "size": st.st_size, "mtime": int(st.st_mtime)})
        total += len(entries)
        groups.append({"category": d, "count": len(entries), "entries": entries})
    return {"ok": True, "groups": groups, "count": total}


def memory_stats() -> dict:
    """Echter Memory-Bestand (Summe der Notizen in den Memory-Ordnern)."""
    return {"ok": True, "count": memory_list().get("count", 0)}


# --- Knowledge (Wissensgraph, read-only) -------------------------------------
# Quelle sind die generierten Graph-Artefakte unter 99_System: entity_index,
# relationships, full_knowledge_graph. Die Extraktion ist teils verrauscht,
# daher _kg_valid als Rauschfilter. JSONs werden nach mtime gecacht (gross).
_KG_CACHE = {}


def _kg_json(rel_path: str):
    p = VAULT / "99_System" / rel_path
    try:
        st = p.stat()
    except Exception:
        return None
    key = str(p)
    cached = _KG_CACHE.get(key)
    if cached and cached[0] == st.st_mtime:
        return cached[1]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    _KG_CACHE[key] = (st.st_mtime, data)
    return data


def _kg_valid(s) -> bool:
    """Rauschfilter: keine rohen Steuerzeichen/Zeilenumbrueche (Extraktionsmuell),
    min. 2 Zeichen, min. ein alphanumerisches Zeichen."""
    if not isinstance(s, str):
        return False
    if any(ord(c) < 32 for c in s):   # roh pruefen: faengt '\nI thin\n' u. ae.
        return False
    t = s.strip()
    if len(t) < 2:
        return False
    if not any(c.isalnum() for c in t):
        return False
    return True


def _doc_rel_from_abs(abs_path: str) -> str:
    if not abs_path:
        return ""
    try:
        return _doc_rel(Path(abs_path))
    except Exception:
        return ""


def knowledge_stats() -> dict:
    from collections import Counter
    ents = _kg_json("entities/entity_index.json") or []
    rels = _kg_json("relationships/relationships.json") or []
    graph = _kg_json("knowledge_graph/full_knowledge_graph.json") or {}
    v_ents = [e for e in ents if isinstance(e, dict) and _kg_valid(e.get("entity"))]
    v_rels = [r for r in rels if isinstance(r, dict)
              and _kg_valid(r.get("source")) and _kg_valid(r.get("target"))]
    types = Counter((e.get("type") or "unbekannt") for e in v_ents)
    # eindeutige Entitaeten (nach Name) fuer ehrliche Zaehlung
    uniq = len({e.get("entity", "").lower() for e in v_ents})
    return {"ok": True,
            "entities": uniq, "entities_rows": len(v_ents), "entities_raw": len(ents),
            "relationships": len(v_rels), "relationships_raw": len(rels),
            "nodes": len(graph.get("nodes", [])) if isinstance(graph, dict) else 0,
            "edges": len(graph.get("edges", [])) if isinstance(graph, dict) else 0,
            "types": [{"type": t, "count": c} for t, c in types.most_common()]}


def knowledge_entities(query="", etype="", limit=50, offset=0) -> dict:
    try:
        limit = max(1, min(500, int(limit)))
    except Exception:
        limit = 50
    try:
        offset = max(0, int(offset))
    except Exception:
        offset = 0
    ents = _kg_json("entities/entity_index.json") or []
    q = (query or "").strip().lower()
    etype = (etype or "").strip().lower()
    agg = {}
    for e in ents:
        if not isinstance(e, dict):
            continue
        name = e.get("entity")
        if not _kg_valid(name):
            continue
        t = e.get("type", "") or ""
        if etype and t.lower() != etype:
            continue
        if q and q not in name.lower():
            continue
        key = name.lower()
        a = agg.get(key)
        if not a:
            a = {"entity": name, "type": t, "count": 0, "notes": []}
            agg[key] = a
        a["count"] += 1
        n = e.get("note")
        if n and n not in a["notes"] and len(a["notes"]) < 20:
            a["notes"].append(n)
    items = sorted(agg.values(), key=lambda x: (-x["count"], x["entity"].lower()))
    total = len(items)
    return {"ok": True, "total": total, "offset": offset, "limit": limit,
            "entities": items[offset:offset + limit]}


def knowledge_entity(name="") -> dict:
    name = (name or "").strip()
    if not name:
        return {"ok": False, "error": "Kein Name angegeben."}
    nl = name.lower()
    rels = _kg_json("relationships/relationships.json") or []
    outgoing, incoming = [], []
    for r in rels:
        if not isinstance(r, dict):
            continue
        s, t = r.get("source"), r.get("target")
        if not (_kg_valid(s) and _kg_valid(t)):
            continue
        ty, w = r.get("type", ""), r.get("weight", 1)
        if s.lower() == nl:
            outgoing.append({"target": t, "type": ty, "weight": w})
        elif t.lower() == nl:
            incoming.append({"source": s, "type": ty, "weight": w})
    outgoing.sort(key=lambda x: -(x.get("weight") or 0))
    incoming.sort(key=lambda x: -(x.get("weight") or 0))
    note = path = etype = ""
    for e in (_kg_json("entities/entity_index.json") or []):
        if isinstance(e, dict) and e.get("entity", "").lower() == nl:
            etype = e.get("type", "") or etype
            note = e.get("note", "") or note
            path = e.get("path", "") or path
            if note:
                break
    return {"ok": True, "entity": name, "type": etype, "note": note,
            "path": _doc_rel_from_abs(path),
            "out_total": len(outgoing), "in_total": len(incoming),
            "outgoing": outgoing[:100], "incoming": incoming[:100]}


# --- Search (Volltext + Facetten, read-only) ---------------------------------
# Kandidatenkatalog ist der semantic_index (Notiz -> Typ/Tags); gewertet wird
# per Stichwort gegen den echten Notizinhalt. Keine Vektor-Semantik.

def _search_index():
    return _kg_json("semantic_search/semantic_index.json") or []


def search_facets() -> dict:
    from collections import Counter
    idx = _search_index()
    types, tags = Counter(), Counter()
    for e in idx:
        if not isinstance(e, dict):
            continue
        if e.get("type"):
            types[e["type"]] += 1
        for t in (e.get("tags") or []):
            if _kg_valid(t):
                tags[str(t)] += 1
    return {"ok": True,
            "types": [{"type": k, "count": v} for k, v in types.most_common()],
            "tags": [{"tag": k, "count": v} for k, v in tags.most_common(60)]}


def search_query(query="", etype="", tag="", limit=50) -> dict:
    try:
        limit = max(1, min(200, int(limit)))
    except Exception:
        limit = 50
    q = (query or "").strip()
    etype = (etype or "").strip().lower()
    tag = (tag or "").strip().lower()
    idx = _search_index()
    base = VAULT.resolve()
    terms = [t for t in _tokenize(q) if t not in _STOPWORDS and len(t) > 1] if q else []
    results = []
    for e in idx:
        if not isinstance(e, dict):
            continue
        etype_e = e.get("type") or ""
        tags_e = [str(t) for t in (e.get("tags") or [])]
        if etype and etype_e.lower() != etype:
            continue
        if tag and tag not in [x.lower() for x in tags_e]:
            continue
        rel = str(e.get("path", "")).replace("\\", "/")
        if not rel:
            continue
        score, snippet = 0, ""
        if terms:
            try:
                text = (base / rel).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
            low = text.lower()
            score = sum(low.count(t) for t in terms)
            score += sum(3 for t in terms if t in str(e.get("stem", "")).lower())
            score += sum(2 for t in terms for tg in tags_e if t in tg.lower())
            if score <= 0:
                continue
            pos = min((low.find(t) for t in terms if t in low), default=0)
            start = max(0, pos - 90)
            snippet = text[start:start + 260].replace("\n", " ").strip()
        else:
            snippet = str(e.get("preview", ""))[:200]
        results.append({"path": rel, "stem": e.get("stem", ""), "type": etype_e,
                        "tags": tags_e[:8], "score": score, "snippet": snippet})
    if terms:
        results.sort(key=lambda x: -x["score"])
    else:
        results.sort(key=lambda x: str(x["stem"]).lower())
    return {"ok": True, "query": q, "total": len(results), "results": results[:limit]}


# --- Imports (Inbox-Status + Reports, Auslösen via Skript-Runner) -------------
# Read-only-Status. Das Ausloesen selbst laeuft ueber den vorhandenen,
# allowlisted /api/run (import_ai_exports.py) - kein zusaetzlicher Schreibweg.

def imports_status() -> dict:
    sources = []
    try:
        for child in sorted(INBOX.iterdir(), key=lambda c: c.name.lower()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            cnt = 0
            for f in child.rglob("*"):
                if f.is_file() and not any(p.lower() == "processed" for p in f.parts):
                    cnt += 1
            sources.append({"name": child.name, "pending": cnt})
    except Exception as exc:
        log_event("hud.imports_status_error", {"error": str(exc)})
    reports = []
    sysdir = VAULT / "99_System"
    try:
        for jf in sysdir.rglob("*.json"):
            if "import" not in jf.parent.name.lower():
                continue
            try:
                d = json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(d, dict) or ("imported_count" not in d and "source" not in d):
                continue
            reports.append({
                "source": d.get("source", jf.parent.name),
                "time": d.get("time", ""),
                "imported": d.get("imported_count", len(d.get("imported", []) or [])),
                "errors": d.get("error_count", len(d.get("errors", []) or [])),
                "file": _doc_rel(jf),
            })
    except Exception:
        pass
    reports.sort(key=lambda r: str(r.get("time", "")), reverse=True)
    return {"ok": True, "inbox": str(INBOX), "sources": sources,
            "pending_total": sum(s["pending"] for s in sources),
            "reports": reports[:12]}


# Quelle -> Export-Skript (nimmt einen ZIP-Pfad als Argument).
_IMPORT_SCRIPTS = {
    "chatgpt": "import_chatgpt_export.py",
    "gemini": "import_gemini_export.py",
    "perplexity": "import_perplexity_export.py",
}
_ZIP_MAX = 400 * 1024 * 1024  # 400 MB


def imports_zip(body: dict) -> dict:
    """Nimmt ein base64-ZIP entgegen, validiert es, fuehrt den passenden
    Export-Importer aus und entfernt die temporaere Datei wieder."""
    import base64
    body = body or {}
    source = str(body.get("source", "")).strip().lower()
    script = _IMPORT_SCRIPTS.get(source)
    if not script:
        return {"ok": False, "error": f"Unbekannte Quelle: {source}. "
                f"Erlaubt: {sorted(_IMPORT_SCRIPTS)}"}
    data_b64 = body.get("data_b64", "")
    if not data_b64:
        return {"ok": False, "error": "Keine Datei empfangen."}
    try:
        raw = base64.b64decode(data_b64)
    except Exception as exc:
        return {"ok": False, "error": f"Base64-Fehler: {exc}"}
    if len(raw) > _ZIP_MAX:
        return {"ok": False, "error": "Datei zu gross (max. 400 MB)."}
    if raw[:2] != b"PK":
        return {"ok": False, "error": "Keine gueltige ZIP-Datei (PK-Signatur fehlt)."}
    updir = ROOT / "data" / "_zip_uploads"
    try:
        updir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"ok": False, "error": f"Upload-Ordner nicht beschreibbar: {exc}"}
    fname = str(body.get("filename", "") or f"{source}-export.zip")
    safe = "".join(c if (c.isalnum() or c in "._-") else "_" for c in fname)[:80] or "export.zip"
    if not safe.lower().endswith(".zip"):
        safe += ".zip"
    target = updir / f"{datetime.now():%Y%m%d_%H%M%S}_{safe}"
    try:
        target.write_bytes(raw)
    except Exception as exc:
        return {"ok": False, "error": f"Schreibfehler: {exc}"}
    try:
        result = run_script(script, str(target))
    finally:
        try:
            target.unlink()
        except Exception:
            pass
    log_event("hud.imports_zip", {"source": source, "bytes": len(raw),
                                  "ok": result.get("ok")})
    return {"ok": result.get("ok", False), "source": source, "script": script,
            "output": result.get("output", "")}


# --- Jobs (ausfuehrbare Skripte + Lauf-Historie aus dem Log) ------------------
# Ehrlich: kein Queue-Dienst, sondern die Allowlist als Jobliste plus die
# script.run-Eintraege aus jarvis_gui.log. Ausgefuehrt wird ueber /api/run.

def jobs_overview() -> dict:
    logf = LOG_DIR / "jarvis_gui.log"
    last, history = {}, []
    try:
        if logf.exists():
            for line in logf.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if row.get("type") != "script.run":
                    continue
                p = row.get("payload", {}) or {}
                sc = p.get("script", "")
                ev = {"time": row.get("time", ""), "script": sc, "ok": bool(p.get("ok"))}
                if sc:
                    last[sc] = ev
                history.append(ev)
    except Exception as exc:
        log_event("hud.jobs_error", {"error": str(exc)})
    history = history[-25:][::-1]  # neueste zuerst
    jobs = []
    for sc in sorted(ALLOWED_SCRIPTS):
        l = last.get(sc)
        jobs.append({"script": sc,
                     "last_time": l["time"] if l else "",
                     "last_ok": l["ok"] if l else None})
    return {"ok": True, "jobs": jobs, "history": history}


# --- Connectoren (Konfig-Status + Live-Check, read-only) ---------------------
# Liest config/connectors.yaml (dependency-frei via load_simple_yaml).
# Secrets/Zugangsdaten werden NICHT ausgegeben. Live geprueft wird nur, was
# wirklich pingbar ist (Ollama). Der Rest ist Konfig-Status, kein "verbunden".

def _connector_detail(val: dict) -> str:
    parts = []
    for k, v in val.items():
        kl = str(k).lower()
        if k == "enabled" or "secret" in kl or "pass" in kl or "user" in kl or "token" in kl or "key" in kl:
            continue
        sv = str(v).strip().strip('"').strip("'")
        if sv in ("", "None", "[]", "{}"):
            continue
        parts.append(f"{k}: {sv}")
    return " · ".join(parts[:5])


def connectors_overview() -> dict:
    try:
        from secondbrain.config import load_simple_yaml
        cfg = load_simple_yaml(ROOT / "config" / "connectors.yaml") or {}
    except Exception as exc:
        log_event("hud.connectors_error", {"error": str(exc)})
        return {"ok": False, "error": str(exc), "connectors": []}
    if isinstance(cfg.get("connectors"), dict):  # production-Variante
        cfg = cfg["connectors"]
    out = []
    for name, val in cfg.items():
        if not isinstance(val, dict):
            out.append({"name": name, "enabled": bool(val), "detail": "", "live": None})
            continue
        enabled = bool(val.get("enabled", False))
        live = None
        if name == "ollama" and enabled:
            base = val.get("base_url") or "http://localhost:11434"
            models = _ollama_models(base)
            live = {"reachable": bool(models),
                    "info": (f"{len(models)} Modelle erreichbar" if models else "nicht erreichbar")}
        out.append({"name": name, "enabled": enabled,
                    "detail": _connector_detail(val), "live": live})
    return {"ok": True, "connectors": out,
            "enabled_count": sum(1 for c in out if c["enabled"]), "total": len(out)}


# --- Agents (Registry-Katalog, read-only) ------------------------------------
# Quelle: persistierte swarm-Registry (runtime/swarm_v124/agents.json), sonst
# der Default-Katalog aus secondbrain.swarm.registry. Kein Ausloesen.

def agents_overview() -> dict:
    agents = None
    runtime_file = ROOT / "runtime" / "swarm_v124" / "agents.json"
    source = "runtime"
    try:
        if runtime_file.exists():
            data = json.loads(runtime_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                agents = data
    except Exception:
        agents = None
    if not agents:
        try:
            from dataclasses import asdict
            from secondbrain.swarm.registry import DEFAULT_AGENTS
            agents = [asdict(a) for a in DEFAULT_AGENTS]
            source = "default"
        except Exception as exc:
            log_event("hud.agents_error", {"error": str(exc)})
            return {"ok": False, "error": str(exc), "agents": []}
    out = []
    for a in agents:
        if not isinstance(a, dict):
            continue
        out.append({"name": a.get("name", ""), "role": a.get("role", ""),
                    "capabilities": list(a.get("capabilities", []) or []),
                    "risk_level": a.get("risk_level", 1),
                    "enabled": bool(a.get("enabled", True))})
    return {"ok": True, "source": source, "agents": out, "total": len(out),
            "enabled_count": sum(1 for a in out if a["enabled"])}


# --- Developer (Diagnose + Endpunkt-Katalog, read-only) ----------------------
_API_ENDPOINTS = [
    ("GET", "/api/metrics", "CPU/RAM/Swap/Disk/Uptime/Netz"),
    ("GET", "/api/status", "Vault/Inbox/Markdown-Status"),
    ("GET", "/api/weather", "Wetter (Open-Meteo)"),
    ("GET", "/api/news", "Tagesschau-RSS"),
    ("GET", "/api/dashboards", "Dashboard-Links"),
    ("GET/POST", "/api/settings", "Einstellungen lesen/speichern"),
    ("GET", "/api/logs", "Log-Tail"),
    ("GET/POST", "/api/run?script=", "Allowlist-Skript ausfuehren"),
    ("GET/POST", "/api/rag?q=", "Stichwortsuche im Vault"),
    ("GET", "/api/assistant/models", "Ollama-Modelle"),
    ("POST", "/api/assistant", "RAG-Chat"),
    ("POST", "/api/assistant/note", "Antwort als Notiz speichern"),
    ("GET", "/api/documents?path=", "Vault-Ordner listen"),
    ("GET", "/api/document?path=", "Notiz lesen"),
    ("GET", "/api/documents/stats", "Markdown-Bestand"),
    ("GET", "/api/memory", "Memory-Ordner"),
    ("GET", "/api/memory/stats", "Memory-Bestand"),
    ("GET", "/api/knowledge/stats", "Graph-Kennzahlen"),
    ("GET", "/api/knowledge/entities", "Entitaeten (Suche/Filter)"),
    ("GET", "/api/knowledge/entity", "Entitaet-Detail"),
    ("GET", "/api/search", "Volltextsuche mit Facetten"),
    ("GET", "/api/search/facets", "Such-Facetten"),
    ("GET", "/api/imports/status", "Inbox + Reports"),
    ("POST", "/api/imports/zip", "ZIP-Upload + Import"),
    ("GET", "/api/jobs", "Jobs + Lauf-Historie"),
    ("GET", "/api/connectors", "Connector-Status"),
    ("GET", "/api/agents", "Agent-Registry"),
    ("GET", "/api/dev/info", "Developer-Diagnose"),
    ("GET", "/api/coding/models", "Coding-Modelle"),
    ("POST", "/api/coding/generate", "Code generieren (Ollama)"),
    ("POST", "/api/coding/save", "Code als Datei speichern"),
    ("GET", "/api/security/cameras", "Kameras + Stream-URLs"),
    ("GET", "/api/security/discover", "ONVIF/WS-Discovery"),
    ("POST", "/api/security/cameras", "Kamera-Konfig speichern"),
]


def hud_stats() -> dict:
    """Reale Kennzahlen fuer die untere Statusleiste (keine Platzhalter)."""
    out = {"ok": True}
    try:
        co = connectors_overview()
        out["connectors_enabled"] = co.get("enabled_count", 0)
        out["connectors_total"] = co.get("total", 0)
    except Exception:
        out["connectors_enabled"] = 0
    try:
        out["agents_enabled"] = agents_overview().get("enabled_count", 0)
    except Exception:
        out["agents_enabled"] = 0
    try:
        out["documents"] = documents_stats().get("count", 0)
    except Exception:
        out["documents"] = 0
    try:
        out["memories"] = memory_stats().get("count", 0)
    except Exception:
        out["memories"] = 0
    try:
        out["entities"] = knowledge_stats().get("entities", 0)
    except Exception:
        out["entities"] = 0
    return out


def dev_info() -> dict:
    s = load_settings()
    st = system_status()
    return {"ok": True,
            "version": s.get("version", ""), "environment": s.get("environment", ""),
            "log_level": s.get("log_level", ""),
            "host": os.environ.get("HUD_HOST", "127.0.0.1"),
            "port": int(os.environ.get("HUD_PORT", 8851)),
            "reload": _reload_enabled(),
            "python": st.get("python", ""), "psutil": _HAS_PSUTIL,
            "paths": {"root": st.get("root", ""), "vault": st.get("vault", ""),
                      "inbox": st.get("inbox", ""),
                      "root_exists": st.get("root_exists"),
                      "vault_exists": st.get("vault_exists"),
                      "inbox_exists": st.get("inbox_exists")},
            "markdown_files": st.get("markdown_files", 0),
            "database": s.get("database", ""),
            "embedding": f"{s.get('embedding_provider','')} {s.get('embedding_model','')} "
                         f"({s.get('embedding_dim','')})",
            "ollama_url": s.get("ollama_url", ""), "ollama_models": s.get("ollama_models", 0),
            "allowed_scripts": len(ALLOWED_SCRIPTS), "settings_keys": len(DEFAULT_SETTINGS),
            "endpoints": [{"method": me, "path": pa, "desc": de} for me, pa, de in _API_ENDPOINTS]}


# --- Coding (LLM-Codegenerierung, review-first, KEIN Ausfuehren) --------------
# Generiert Code ueber das lokale Ollama (Standard deepseek-coder) und speichert
# ihn auf Wunsch als NEUE Datei unter data/coding_output. Ausgefuehrt wird nichts.

def _strip_code_fences(text: str) -> str:
    t = (text or "").strip()
    if "```" not in t:
        return t
    import re
    m = re.search(r"```[a-zA-Z0-9_+#-]*\n(.*?)```", t, re.S)
    if m:
        return m.group(1).strip()
    return t.replace("```", "").strip()


def coding_generate(prompt_text: str, language: str = "", model: str = "", engine: str = "") -> dict:
    task = (prompt_text or "").strip()
    if not task:
        return {"ok": False, "error": "Keine Aufgabe angegeben.", "llm_ok": False}
    cfg = load_settings()
    language = (language or "").strip() or "Python"
    temp = cfg.get("coding_temperature", 0.1)
    engine = (engine or cfg.get("coding_engine") or "ollama").strip().lower()
    model = (model or "").strip() or cfg.get("coding_model") or ""
    if engine == "ollama" and not model:  # cod-bevorzugte Auto-Wahl
        base = cfg.get("ollama_url") or "http://localhost:11434"
        avail = _ollama_models(base)
        model = next((m for m in avail if "cod" in m.lower()), avail[0] if avail else "")
        if not model:
            return {"ok": False, "error": "Kein Ollama-Modell verfuegbar.", "llm_ok": False}
    sys_p = (f"Du bist ein praeziser Coding-Assistent. Erzeuge ausschliesslich "
             f"lauffaehigen Quellcode in {language}. Keine Erklaerungen ausserhalb "
             f"des Codes, nur kurze Inline-Kommentare.")
    full = sys_p + "\n\nAufgabe:\n" + task + "\n\nCode:"
    try:
        raw, model = _llm_chat(engine, model, full, temp)
    except Exception as exc:
        log_event("hud.coding_error", {"error": str(exc), "engine": engine, "model": model})
        return {"ok": False, "error": f"LLM nicht erreichbar: {exc}", "llm_ok": False}
    code = _strip_code_fences(raw)
    log_event("hud.coding", {"language": language, "engine": engine, "model": model, "chars": len(code)})
    return {"ok": True, "code": code, "model": model, "engine": engine,
            "language": language, "llm_ok": True}


def coding_save(filename: str, content: str) -> dict:
    content = content or ""
    if not content.strip():
        return {"ok": False, "error": "Kein Inhalt."}
    folder = ROOT / "data" / "coding_output"
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {"ok": False, "error": f"Ordner nicht beschreibbar: {exc}"}
    base = "".join(c if (c.isalnum() or c in "._-") else "_" for c in (filename or "code.txt"))
    base = base.strip("_")[:80] or "code.txt"
    if "." not in base:
        base += ".txt"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = folder / f"{stamp}_{base}"
    n = 1
    while target.exists():  # niemals ueberschreiben
        stem, dot, ext = base.rpartition(".")
        target = folder / (f"{stamp}_{stem}_{n}.{ext}" if dot else f"{stamp}_{base}_{n}")
        n += 1
    try:
        target.write_text(content, encoding="utf-8")
    except Exception as exc:
        return {"ok": False, "error": f"Schreibfehler: {exc}"}
    try:
        rel = str(target.relative_to(ROOT)).replace("\\", "/")
    except Exception:
        rel = str(target)
    log_event("hud.coding_save", {"file": rel})
    return {"ok": True, "file": rel}


def coding_models() -> dict:
    cfg = load_settings()
    base = cfg.get("ollama_url") or "http://localhost:11434"
    configured = [m.strip() for m in str(cfg.get("assistant_models", "")).split(",") if m.strip()]
    live = _ollama_models(base)
    merged = list(dict.fromkeys(configured + live))
    return {"ok": True, "models": merged,
            "active": cfg.get("coding_model", "") or "deepseek-coder",
            "engine": cfg.get("coding_engine", "ollama")}


# --- Auto-Reload (optionaler Dev-Modus) --------------------------------------
# Aktiv mit Umgebungsvariable HUD_RELOAD=1 oder Argument --reload.
# Muster: Monitor-Prozess startet den Server als Kindprozess neu, sobald sich
# eine .py-Datei aendert (Kind beendet sich mit Code 3). Ohne HUD_RELOAD bleibt
# das Verhalten exakt wie zuvor (kein Overhead, kein zusaetzlicher Prozess).

def _reload_enabled() -> bool:
    return (os.environ.get("HUD_RELOAD", "").lower() in ("1", "true", "yes", "on")
            or "--reload" in sys.argv)


def _reload_watch_files():
    roots = [Path(__file__).resolve().parent, ROOT / "scripts"]
    files = []
    for r in roots:
        try:
            files += [p for p in r.rglob("*.py") if "__pycache__" not in p.parts]
        except Exception:
            pass
    return files


def _start_reload_watch(interval: float = 1.5) -> None:
    import threading
    import time as _time

    def loop():
        mtimes = {}
        for p in _reload_watch_files():
            try:
                mtimes[p] = p.stat().st_mtime
            except Exception:
                pass
        while True:
            _time.sleep(interval)
            for p in _reload_watch_files():
                try:
                    m = p.stat().st_mtime
                except Exception:
                    continue
                if mtimes.get(p) != m:
                    print(f"[reload] Aenderung erkannt ({p.name}) - Neustart ...", flush=True)
                    os._exit(3)  # Monitor startet neu

    threading.Thread(target=loop, daemon=True).start()


def _reload_monitor() -> None:
    import subprocess
    print("[reload] Dev-Modus aktiv - Server startet bei Code-Aenderung neu. Stop mit Strg+C.",
          flush=True)
    while True:
        env = dict(os.environ)
        env["HUD_RELOAD_CHILD"] = "true"
        try:
            ret = subprocess.run([sys.executable] + sys.argv, env=env).returncode
        except KeyboardInterrupt:
            break
        if ret != 3:   # nur Code 3 = "wegen Aenderung neu starten"
            break


# --- Server-Bootstrap --------------------------------------------------------
def run(host: str = "127.0.0.1", port: int = 8851) -> None:
    if _reload_enabled() and os.environ.get("HUD_RELOAD_CHILD") != "true":
        _reload_monitor()
        return
    if _reload_enabled():
        _start_reload_watch()
    port = int(os.environ.get("HUD_PORT", port))
    host = os.environ.get("HUD_HOST", host)
    server = HTTPServer((host, port), Handler)
    log_event("hud.start", {"host": host, "port": port})
    print(f"Jarvis HUD laeuft: http://{host}:{port}"
          + ("  [Auto-Reload]" if _reload_enabled() else ""))
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

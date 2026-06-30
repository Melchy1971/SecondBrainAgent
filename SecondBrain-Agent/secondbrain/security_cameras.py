"""Security / Kameraverwaltung fuer das Jarvis Control Center.

Verwaltet Webcams und IP-Kameras und liefert die Daten fuer das Security-Panel
der Oberflaeche. Bewusst dependency-arm: der Kern nutzt nur die Standardbibliothek.
ONVIF/WS-Discovery ist optional und degradiert sauber, wenn die Pakete fehlen.

Sicherheitsprinzip
------------------
In config/cameras.json werden KEINE Zugangsdaten gespeichert. Die Datei enthaelt
nur Anzeige- und Routing-Metadaten (Name, Ort, Host, Stream-Pfad im Gateway).
Die RTSP-Zugangsdaten der Kameras liegen ausschliesslich in der Konfiguration des
Stream-Gateways (z. B. MediaMTX, mediamtx.yml). Der Browser erhaelt vom Gateway
eine zugangsdatenfreie WebRTC-/HLS-URL. So gelangt kein Kamera-Passwort ins Repo.

Streaming-Architektur
----------------------
Browser koennen RTSP nicht direkt abspielen. Ein lokales Gateway (MediaMTX)
zieht den RTSP-Stream jeder Kamera und veroeffentlicht ihn als WebRTC (WHEP) und
HLS auf localhost. Pro Kamera wird hier nur der Gateway-Pfad gespeichert; die
Wiedergabe-URL wird daraus gebaut:
    HLS:    {gateway_hls}/{stream_path}/index.m3u8
    WebRTC: {gateway_webrtc}/{stream_path}/whep
"""
from __future__ import annotations

import json
import re
import socket
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CAMERAS_FILE = ROOT / "config" / "cameras.json"

# Felder, die niemals gespeichert werden (Zugangsdaten gehoeren ins Gateway).
_SECRET_KEYS = {"user", "username", "password", "pass", "secret", "token", "auth"}

DEFAULTS = {
    "gateway_webrtc": "http://127.0.0.1:8889",
    "gateway_hls": "http://127.0.0.1:8888",
    "cameras": [],
}

_ID_RE = re.compile(r"[^a-z0-9_]+")


def _slug(value: str) -> str:
    s = _ID_RE.sub("_", (value or "").strip().lower()).strip("_")
    return s or "cam"


def _tcp_reachable(host: str, port: int, timeout: float = 0.6) -> bool:
    """Best-effort-Erreichbarkeitstest ohne Zugangsdaten."""
    if not host:
        return False
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


def _clean_camera(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Validiert einen Kameraeintrag und entfernt etwaige Zugangsdaten."""
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name", "")).strip()
    if not name:
        return None
    cam_id = _slug(str(raw.get("id") or name))
    try:
        rtsp_port = int(raw.get("rtsp_port", 554))
    except (TypeError, ValueError):
        rtsp_port = 554
    mode = str(raw.get("mode", "hls")).lower()
    if mode not in ("hls", "webrtc"):
        mode = "hls"
    cam = {
        "id": cam_id,
        "name": name[:80],
        "location": str(raw.get("location", "")).strip()[:80],
        "host": str(raw.get("host", "")).strip()[:120],
        "rtsp_port": max(1, min(65535, rtsp_port)),
        "stream_path": _slug(str(raw.get("stream_path") or cam_id)),
        "mode": mode,
        "snapshot_url": str(raw.get("snapshot_url", "")).strip()[:300],
        "onvif_port": int(raw.get("onvif_port", 80)) if str(raw.get("onvif_port", "")).strip().isdigit() else 80,
        "enabled": bool(raw.get("enabled", True)),
    }
    return cam


def _stream_urls(cam: dict[str, Any], cfg: dict[str, Any]) -> dict[str, str]:
    path = cam["stream_path"]
    hls = f'{cfg["gateway_hls"].rstrip("/")}/{path}/index.m3u8'
    webrtc = f'{cfg["gateway_webrtc"].rstrip("/")}/{path}/whep'
    return {"hls": hls, "webrtc": webrtc}


def load_config() -> dict[str, Any]:
    cfg = dict(DEFAULTS)
    cfg["cameras"] = []
    try:
        if CAMERAS_FILE.exists():
            data = json.loads(CAMERAS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cfg["gateway_webrtc"] = str(data.get("gateway_webrtc", cfg["gateway_webrtc"]))
                cfg["gateway_hls"] = str(data.get("gateway_hls", cfg["gateway_hls"]))
                raw_list = data.get("cameras") if isinstance(data.get("cameras"), list) else []
                for raw in raw_list:
                    cam = _clean_camera(raw)
                    if cam:
                        cfg["cameras"].append(cam)
    except Exception:
        # Defekte Datei nicht fatal werden lassen.
        pass
    return cfg


def cameras_overview() -> dict[str, Any]:
    """Liefert Kameras inkl. gebauter Stream-URLs und Erreichbarkeit."""
    try:
        cfg = load_config()
        out = []
        for cam in cfg["cameras"]:
            entry = dict(cam)
            entry["stream_urls"] = _stream_urls(cam, cfg)
            entry["reachable"] = _tcp_reachable(cam["host"], cam["rtsp_port"]) if cam["host"] else None
            out.append(entry)
        return {
            "ok": True,
            "gateway_webrtc": cfg["gateway_webrtc"],
            "gateway_hls": cfg["gateway_hls"],
            "cameras": out,
            "active_count": sum(1 for c in out if c["enabled"]),
            "total": len(out),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "cameras": []}


def cameras_save(body: dict[str, Any]) -> dict[str, Any]:
    """Speichert die Kamera-Konfiguration. Zugangsdaten werden verworfen."""
    try:
        body = body or {}
        cfg = {
            "gateway_webrtc": str(body.get("gateway_webrtc", DEFAULTS["gateway_webrtc"]))[:200],
            "gateway_hls": str(body.get("gateway_hls", DEFAULTS["gateway_hls"]))[:200],
            "cameras": [],
        }
        seen = set()
        for raw in (body.get("cameras") or []):
            if isinstance(raw, dict):
                for k in list(raw.keys()):
                    if k.lower() in _SECRET_KEYS:
                        raw.pop(k, None)
            cam = _clean_camera(raw)
            if not cam:
                continue
            if cam["id"] in seen:
                cam["id"] = f'{cam["id"]}_{len(seen)}'
            seen.add(cam["id"])
            cfg["cameras"].append(cam)
        CAMERAS_FILE.parent.mkdir(parents=True, exist_ok=True)
        CAMERAS_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        return cameras_overview()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def cameras_discover(timeout: float = 4.0) -> dict[str, Any]:
    """ONVIF/WS-Discovery im lokalen Netz. Degradiert ohne optionale Pakete.

    Liefert gefundene Geraete (IP, Adresse, Typen). Das Anlegen bleibt manuell —
    es werden keine Zugangsdaten ermittelt oder gespeichert.
    """
    try:
        from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery  # type: ignore
    except Exception:
        return {
            "ok": False,
            "available": False,
            "devices": [],
            "error": "WS-Discovery nicht installiert.",
            "hint": "pip install WSDiscovery  (optional zusaetzlich: onvif-zeep). "
                    "Ohne dieses Paket Kameras manuell anlegen.",
        }
    wsd = None
    try:
        wsd = WSDiscovery()
        wsd.start()
        services = wsd.searchServices(timeout=timeout)
        devices = []
        for svc in services:
            xaddrs = list(getattr(svc, "getXAddrs", lambda: [])() or [])
            types = [str(t) for t in (getattr(svc, "getTypes", lambda: [])() or [])]
            host = ""
            if xaddrs:
                m = re.search(r"https?://([^/:]+)", xaddrs[0])
                host = m.group(1) if m else ""
            is_cam = any("NetworkVideoTransmitter" in t or "onvif" in t.lower() for t in types)
            devices.append({
                "host": host,
                "xaddr": xaddrs[0] if xaddrs else "",
                "types": types,
                "likely_camera": is_cam,
            })
        return {"ok": True, "available": True, "devices": devices, "count": len(devices)}
    except Exception as exc:
        return {"ok": False, "available": True, "devices": [], "error": str(exc)}
    finally:
        try:
            if wsd:
                wsd.stop()
        except Exception:
            pass

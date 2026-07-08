# Security Cameras

Das lokale Security-Panel verwaltet IP-Kamera-Metadaten und zeigt Streams ueber ein separates Gateway. Es speichert keine Kamera-Zugangsdaten.

## Architektur

```text
IP-Kamera (RTSP)
  -> MediaMTX oder kompatibles Gateway
  -> WebRTC/WHEP oder HLS auf localhost
  -> Jarvis Web-HUD
```

Browser koennen RTSP nicht direkt wiedergeben. Der `stream_path` in Jarvis muss dem Pfadnamen der Gateway-Konfiguration entsprechen.

Standard-URLs:

- WebRTC: `http://127.0.0.1:8889/{stream_path}/whep`
- HLS: `http://127.0.0.1:8888/{stream_path}/index.m3u8`

## MediaMTX-Beispiel

Zugangsdaten stehen ausschliesslich in der lokalen, nicht versionierten Gateway-Konfiguration:

```yaml
paths:
  haustuer:
    source: rtsp://BENUTZER:PASSWORT@192.168.1.50:554/STREAM
```

`config/cameras.json` enthaelt nur Anzeige-, Host- und Routing-Metadaten. Das Backend verwirft Felder wie `user`, `password` oder `token` beim Speichern.

## Kamera-Metadaten

| Feld | Bedeutung |
|---|---|
| `id` | eindeutiger lokaler Schluessel |
| `name`, `location` | Anzeige im Panel |
| `host`, `rtsp_port` | TCP-Erreichbarkeitspruefung |
| `stream_path` | Gateway-Pfad |
| `mode` | `webrtc` oder `hls` |
| `onvif_port` | optionaler ONVIF-Port |
| `enabled` | lokale Aktivierung |

Vorlage: `config/cameras.example.json`.

## ONVIF-/WS-Discovery

```powershell
pip install WSDiscovery onvif-zeep
```

Die aktuelle Discovery verwendet `WSDiscovery`; `onvif-zeep` ist fuer weitergehende ONVIF-Kommunikation optional. Discovery ermittelt Hosts und Service-Adressen, aber keine Zugangsdaten.

## Lokale API

- `GET /api/security/cameras` - Kameras, Stream-URLs und Erreichbarkeit.
- `POST /api/security/cameras` - validierte Metadaten speichern.
- `GET /api/security/discover` - WS-Discovery im lokalen Netz.

## Grenzen

- Ohne Gateway kein Live-Bild.
- Echte Kamera, WebRTC/HLS und Discovery muessen im Zielnetz validiert werden.
- Aufzeichnung, Bewegungserkennung und Snapshot-Archiv sind nicht enthalten.
- Die lokale HUD-API ist nicht als gehaertete Internet-Schnittstelle freigegeben.

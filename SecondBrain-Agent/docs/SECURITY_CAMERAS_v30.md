# Security / Kameraverwaltung (v30.21)

Der Menüpunkt **Security** im Jarvis Control Center verwaltet und zeigt Webcams
und IP-Kameras. Verwaltung (Anlegen, Auflisten, ONVIF-Discovery, Entfernen) läuft
über das HUD; die Live-Bilder kommen über ein lokales Stream-Gateway.

## Architektur

Browser können RTSP nicht direkt abspielen. Deshalb sitzt zwischen Kamera und
Oberfläche ein Gateway, das den RTSP-Stream jeder Kamera nach **WebRTC (WHEP)**
und **HLS** auf localhost umsetzt:

```
IP-Kamera (RTSP)  ->  Gateway (MediaMTX)  ->  Browser (WebRTC/HLS)
```

Empfohlen ist **MediaMTX** (ein einzelnes Binary). Pro Kamera wird im HUD nur der
Gateway-Pfad gespeichert; die Wiedergabe-URL wird daraus gebaut:

- HLS: `{gateway_hls}/{stream_path}/index.m3u8`  (Standard `http://127.0.0.1:8888`)
- WebRTC: `{gateway_webrtc}/{stream_path}/whep`  (Standard `http://127.0.0.1:8889`)

WebRTC bietet die geringste Latenz und ist für Live-Überwachung die erste Wahl;
HLS ist robuster bei restriktiven Netzen.

## Sicherheitsprinzip — keine Passwörter im Repo

`config/cameras.json` enthält **keine Zugangsdaten**, nur Anzeige- und
Routing-Metadaten. Die RTSP-Zugangsdaten der Kameras liegen ausschließlich in der
Gateway-Konfiguration (`mediamtx.yml`). Das Backend verwirft beim Speichern aktiv
alle Felder wie `user`, `password`, `token`. So gelangt kein Kamera-Passwort in
das Vault oder die Versionsverwaltung.

## Gateway einrichten (MediaMTX)

1. MediaMTX herunterladen (offizielles Release-Binary) und starten.
2. In `mediamtx.yml` je Kamera einen Pfad anlegen — hier liegen die Zugangsdaten:

```yaml
paths:
  haustuer:
    source: rtsp://BENUTZER:PASSWORT@192.168.1.50:554/h264Preview_01_main
  hof:
    source: rtsp://BENUTZER:PASSWORT@192.168.1.51:554/h264Preview_01_main
```

Der Pfadname (`haustuer`, `hof`) muss dem `stream_path` im HUD entsprechen.
Reolink-Beispiel-URLs: Hauptstream `…/h264Preview_01_main`, Substream
`…/h264Preview_01_sub`. WebRTC ist bei MediaMTX standardmäßig auf Port 8889,
HLS auf 8888.

3. MediaMTX läuft auf demselben Rechner wie das HUD (localhost). Sollen die Ports
   abweichen, im Security-Panel bzw. in `cameras.json` `gateway_webrtc` /
   `gateway_hls` anpassen.

## ONVIF-Discovery (optional)

Die Schaltfläche „Im Netz suchen“ nutzt WS-Discovery. Dafür ein Paket installieren:

```powershell
pip install WSDiscovery
```

Ohne das Paket bleibt die manuelle Anlage über das Formular nutzbar; das Panel
zeigt dann einen entsprechenden Hinweis. Discovery ermittelt nur Geräte-IPs —
keine Zugangsdaten. Gefundene Hosts lassen sich per Klick ins Formular übernehmen.

## Konfiguration

`config/cameras.json` (Vorlage: `config/cameras.example.json`). Felder je Kamera:

| Feld | Bedeutung |
|------|-----------|
| `id` | Eindeutiger Schlüssel (wird aus dem Namen abgeleitet). |
| `name`, `location` | Anzeige im Panel. |
| `host`, `rtsp_port` | Für den Erreichbarkeitstest (TCP), nicht für die Wiedergabe. |
| `stream_path` | Pfadname im Gateway (= Schlüssel in `mediamtx.yml`). |
| `mode` | `webrtc` oder `hls`. |
| `onvif_port` | Optionaler ONVIF-Port (Standard 80). |
| `enabled` | Kamera aktiv ja/nein. |

## API-Endpunkte

- `GET /api/security/cameras` — Kameras inkl. gebauter Stream-URLs und TCP-Erreichbarkeit.
- `POST /api/security/cameras` — Konfiguration speichern (Zugangsdaten werden verworfen).
- `GET /api/security/discover` — ONVIF/WS-Discovery (degradiert ohne Paket).

## Grenzen

- Das HUD speichert und verwaltet keine Kamera-Passwörter; diese gehören in das Gateway.
- Ohne laufendes Gateway zeigt jede Kachel einen Hinweis statt Video; Verwaltung und Discovery funktionieren weiterhin.
- Aufzeichnung/Bewegungserkennung sind nicht Teil dieses Panels (übernimmt die Kamera bzw. das Gateway).

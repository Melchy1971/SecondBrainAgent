---
title: "OpenClaw Installation Unraid"
type: chatgpt_conversation
source: chatgpt
source_id: "69dcac95-33d4-8391-9462-0e6a75764e42"
created: 2026-04-13
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# OpenClaw Installation Unraid

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69dcac95-33d4-8391-9462-0e6a75764e42`
- Nachrichten: 8

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Assistent

Zielsystem: **entity["software","OpenClaw","AI agent framework"] auf Unraid**.  
Primäre Abhängigkeiten: Containerisierung, GPU/CPU-Ressourcen, API-Zugänge.

---

# 1. Architektur-Entscheidung (vor Installation)

## Option A: Cloud-LLM (einfach, schnell)
- Externe Modelle über APIs
- Keine lokale GPU erforderlich
- Kosten pro Anfrage

## Option B: Lokale Modelle (komplex, unabhängig)
- Läuft über z. B. entity["software","Ollama","local LLM runtime"] oder entity["software","LM Studio","local LLM UI tool"]  
- GPU (NVIDIA bevorzugt) oder starke CPU notwendig  
- Keine laufenden API-Kosten, aber Hardwarelimit

**Trade-off**
- Cloud: schnell, skalierbar, abhängig von externen Diensten  
- Lokal: volle Kontrolle, aber Setup + Performance kritisch

---

# 2. Unraid-spezifische Anforderungen

## Container-Basis
- Nutzung von Docker (Unraid Standard)
- Image: entweder offizielles OpenClaw Image oder manuell gebaut

## Ressourcen
- RAM: ≥16 GB empfohlen (bei lokalen Modellen eher 32 GB)
- CPU: ≥4 Cores
- GPU (optional, aber relevant für lokal):
  - NVIDIA + Unraid NVIDIA Plugin
  - CUDA-Unterstützung erforderlich

## Netzwerk
- Bridge oder Custom Network
- Portfreigaben für Web UI/API

---

# 3. API Keys (abhängig vom Setup)

## Minimal (Cloud-Setup)
Du brauchst mindestens:

- entity["company","OpenAI","AI company"] API Key  
  - für GPT-Modelle (z. B. GPT-4/5 Varianten)

Optional / Alternativen:

- entity["company","Anthropic","AI company"] API Key  
  - Claude-Modelle

- entity["company","Google","technology company"] API Key  
  - Gemini-Modelle

- entity["company","Mistral AI","AI company"] API Key  
  - kostengünstigere Modelle

**Empfehlung (robust):**
- mindestens 2 Anbieter → Failover / Kostenoptimierung

---

## Lokal (kein externer API-Key notwendig)
Stattdessen:
- Lokale Endpoint-URL (z. B. `http://ollama:11434`)
- Modelle lokal geladen (z. B. LLaMA, Mistral)

---

# 4. Installation auf Unraid (konzeptioneller Ablauf)

## Schrittfolge

1. Docker Container bereitstellen
   - Repository klonen oder Image ziehen
2. Environment Variablen definieren:
   - `OPENAI_API_KEY=...`
   - optional weitere Keys
3. Volumes mappen:
   - Config
   - Logs
   - Modelle (bei lokal)
4. Netzwerk konfigurieren
5. Container starten
6. Web UI öffnen

---

# 5. Kritische Punkte / Failure Modes

## 1. Ressourcenengpass
- Symptom: langsame Antworten / Abstürze  
- Ursache: RAM / VRAM zu gering  
- Lösung: kleinere Modelle oder Cloud wechseln

## 2. GPU passthrough falsch
- Symptom: keine Beschleunigung  
- Ursache: fehlendes NVIDIA Runtime Mapping  
- Lösung: `--gpus all` / Unraid Plugin prüfen

## 3. API Limits / Kosten
- OpenAI:
  - Rate Limits
  - Tokenkosten
- Risiko: unkontrollierte Kostenexplosion

**Mitigation:**
- Hard Limits definieren
- Logging aktivieren

## 4. Netzwerk / CORS
- UI kann API nicht erreichen
- Lösung: korrekte Base URLs + Ports

---

# 6. Sicherheitsaspekte

- API Keys nur als ENV, nicht im Code
- Zugriff auf UI:
  - Reverse Proxy + Auth (z. B. Nginx)
- Keine offenen Ports ohne Authentifizierung

---

# 7. Skalierung / Erweiterung

- Multi-Model Routing (Kosten vs Qualität)
- Task-Splitting (Agentenarchitektur)
- Persistente Speicher (Vector DB optional)

---

# Kernaussage

**Minimal Setup**
- Docker Container
- OpenAI API Key

**Fortgeschritten**
- Multi-API + lokale Modelle (Ollama)
- GPU + Routing + Kostenkontrolle

**Hauptentscheidungshebel**
- Kosten vs Kontrolle
- Latenz vs Qualität
- Hardware vs API-Abhängigkeit

### 2. Benutzer

ich möchte openclauw auf meine unraid server installieren was muss ich beachten und welche api key benötige ich

### 3. Assistent

Der **Gateway Token** ist **kein externer API-Key**.  
Er wird **lokal von dir erzeugt** und dient nur zur **Authentifizierung zwischen UI und Backend** von entity["software","OpenClaw","AI agent framework"].

---

# Erzeugung (Standardweg)

Im Terminal (z. B. Unraid Console):

```bash
openssl rand -hex 24
```

Ergebnis:
- 48 Zeichen langer Hex-String  
- Beispiel:
  ```
  a3f9c1e8b7d4... (gekürzt)
  ```

Diesen Wert setzt du als:

```
OPENCLAW_GATEWAY_TOKEN=<dein_token>
```

---

# Alternativen

## Manuell
- Beliebiger zufälliger String möglich  
- Anforderungen:
  - ≥32 Zeichen
  - hohe Entropie (keine einfachen Wörter)

## Passwort-Generator
- z. B. Bitwarden / 1Password
- Format: hex oder base64

---

# Funktion im System

- schützt den **Control UI Zugriff**
- verhindert unautorisierte Requests
- wirkt wie ein **Shared Secret**

---

# Failure Modes

## Token fehlt
- UI kann nicht verbinden
- Fehler: Unauthorized / 401

## Token falsch
- gleiche Symptome wie oben

## Token öffentlich geleakt
- vollständiger Zugriff auf Control UI möglich

---

# Deployment-Kontext (Unraid)

Setzen als:
- Docker ENV Variable oder
- Unraid Template Variable

Keine Persistenz außerhalb Container nötig  
Keine Registrierung bei externem Anbieter erforderlich

---

# Kernaussage

- **Nicht von OpenAI / Anthropic etc.**
- **Wird lokal generiert**
- **Einmal setzen → konsistent verwenden**

### 4. Benutzer

{"asset_pointer": "sediment://file_00000000744072469bcdbfecc4afa93d", "content_type": "image_asset_pointer", "fovea": null, "height": 96, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 12465, "width": 942}
wo bekome ich den

### 5. Assistent

Fehlerursache klar: **CORS / Origin Restriction im Gateway** von entity["software","OpenClaw","AI agent framework"].

---

# Problem

```
origin not allowed
```

Bedeutung:
- Dein Browser (`http://192.168.x.x`) ist **nicht in der erlaubten Origin-Liste**
- Gateway blockiert die Verbindung aktiv

---

# Lösung

## Option 1 (sauber): Allowed Origins setzen

Im Container ENV:

```bash
OPENCLAW_GATEWAY_CONTROLUI_ALLOWEDORIGINS=http://192.168.2.178:18789
```

oder generisch:

```bash
OPENCLAW_GATEWAY_CONTROLUI_ALLOWEDORIGINS=*
```

---

## Option 2 (empfohlen für Unraid LAN)

Setze:

```bash
OPENCLAW_GATEWAY_CONTROLUI_ALLOWEDORIGINS=http://192.168.2.178:*
```

→ erlaubt alle Ports auf deinem Host

---

## Option 3 (Quick & Dirty)

```bash
OPENCLAW_GATEWAY_CONTROLUI_ALLOWEDORIGINS=*
```

Risiko:
- Jeder Origin darf zugreifen
- nur im privaten LAN akzeptabel

---

# Zweiter Fehlerpunkt (im Screenshot sichtbar)

## WebSocket URL

Aktuell:
```
ws://192.168.2.178:18789
```

Check:
- Port muss exakt dem Gateway-Port entsprechen
- Container-Port-Mapping korrekt?

Typischer Fehler:
- UI läuft auf anderem Port als Gateway

---

# Gateway Token

Feld ist optional → aber wenn gesetzt im Container:

```bash
OPENCLAW_GATEWAY_TOKEN=xyz
```

→ exakt gleichen Wert im UI eintragen

Mismatch ⇒ 401 / keine Verbindung

---

# Validierungslogik (System)

Connection erfolgreich nur wenn:

1. Origin ∈ allowedOrigins
2. Token stimmt (falls gesetzt)
3. WebSocket erreichbar
4. Port-Mapping korrekt

---

# Minimal funktionierendes Setup

```bash
OPENCLAW_GATEWAY_CONTROLUI_ALLOWEDORIGINS=*
OPENCLAW_GATEWAY_TOKEN=<token>
```

UI:
- gleiche WS URL
- gleicher Token

---

# Kernaussage

Dein aktueller Blocker ist **nicht der Token**, sondern **Origin Whitelist**.  
Fix = ENV Variable setzen + Container neu starten.

### 6. Benutzer

{"asset_pointer": "sediment://file_00000000a4007243b2de53190d652f75", "content_type": "image_asset_pointer", "fovea": null, "height": 836, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 41893, "width": 602}

### 7. Assistent

Status aus Screenshot:

- `OPENCLAW_GATEWAY_CONTROLUI_ALLOWEDORIGINS = http://192.168.2.178:*` → korrekt  
- `OPENCLAW_GATEWAY_TOKEN` gesetzt → korrekt  
- mehrere API-Key Slots vorhanden → aktuell leer (bis auf OpenAI evtl.)

---

# Bewertung Setup

## 1. Gateway / Verbindung
- CORS-Problem ist gelöst (Origin korrekt gesetzt)
- Token vorhanden → Zugriff abgesichert

**Restfehlerquelle (falls noch keine Verbindung):**
- Token im UI nicht identisch
- falscher WebSocket-Port

---

## 2. API-Key Struktur

Du hast mehrere Provider gleichzeitig konfigurierbar:

| Provider | Zweck | Priorität |
|----------|------|----------|
| OpenAI | stabil, beste Qualität | hoch |
| OpenRouter | Multi-Model Routing | hoch |
| Gemini | Alternative (Google) | optional |
| Groq | extrem schnell (Inference) | situativ |
| xAI | experimentell | niedrig |
| Z.AI | niche | niedrig |

---

# Minimal funktionierendes Setup

Nur notwendig:

```bash
OPENAI_API_KEY=<key>
OPENCLAW_GATEWAY_TOKEN=<token>
OPENCLAW_GATEWAY_CONTROLUI_ALLOWEDORIGINS=http://192.168.2.178:*
```

Alles andere optional.

---

# Entscheidungslogik API Keys

## Variante A: Einfach / stabil
- Nur entity["company","OpenAI","AI company"]
- geringster Setup-Aufwand
- höchste Modellqualität

## Variante B: Kostenoptimiert / flexibel
- entity["company","OpenRouter","AI model aggregator"] + OpenAI
- Routing zwischen günstigen und teuren Modellen

## Variante C: Performance-getrieben
- zusätzlich entity["company","Groq","AI inference company"]
- Vorteil: sehr geringe Latenz
- Nachteil: Modell-Auswahl eingeschränkt

---

# Typische Fehler jetzt (nach deinem Stand)

## 1. Verbindung klappt nicht trotz Fix
Ursache:
- Container nicht neu gestartet  
- falscher Port exposed

## 2. UI verbindet, aber keine Antworten
Ursache:
- kein API-Key gesetzt  
- falscher Provider ausgewählt

## 3. Timeout / Hänger
Ursache:
- Provider nicht erreichbar  
- falsches Model Mapping

---

# Hidden Dependency

OpenClaw benötigt:
- mindestens **einen funktionierenden LLM Provider**
- sonst: UI funktioniert, aber keine Execution

---

# Empfehlung (robust)

Setze:

- OpenAI Key
- optional OpenRouter als Fallback

Deaktiviere:
- alle anderen Keys (reduziert Komplexität + Fehlerfläche)

---

# Kernaussage

Dein System ist **infrastrukturseitig korrekt konfiguriert**.  
Nächster Engpass ist **LLM-Provider (API-Key + Modellrouting)**, nicht mehr Netzwerk oder Gateway.

### 8. Benutzer

{"asset_pointer": "sediment://file_0000000023447243a8c5831a0cc1dfe0", "content_type": "image_asset_pointer", "fovea": null, "height": 773, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 78170, "width": 1073}

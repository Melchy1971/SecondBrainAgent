---
title: "n8n Aufruf VPS"
type: chatgpt_conversation
source: chatgpt
source_id: "69f30711-bf28-8386-b599-a6574416712f"
created: 2026-04-30
tags:
  - chatgpt
  - code
  - import
  - ki
---


# n8n Aufruf VPS

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69f30711-bf28-8386-b599-a6574416712f`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich habe n8n auf den vps installiert wie rufe ich n8n auf

### 2. Assistent

Rufe n8n im Browser so auf:

```text
http://SERVER-IP:5678
```

Beispiel:

```text
http://123.45.67.89:5678
```

Falls du eine Domain hast:

```text
http://deine-domain.de:5678
```

Prüfen, ob n8n läuft:

```bash
docker ps
```

oder bei systemd-Installation:

```bash
systemctl status n8n
```

Firewall-Port öffnen, falls nicht erreichbar:

```bash
ufw allow 5678/tcp
ufw status
```

Wenn du n8n produktiv nutzen willst: besser über HTTPS + Domain + Reverse Proxy aufrufen:

```text
https://n8n.deine-domain.de
```

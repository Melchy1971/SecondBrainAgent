---
title: "n8n Cloud Server IONOS"
type: chatgpt_conversation
source: chatgpt
source_id: "682ee774-1d6c-8007-9487-1c5f0893c493"
created: 2025-05-22
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
  - verein
---


# n8n Cloud Server IONOS

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `682ee774-1d6c-8007-9487-1c5f0893c493`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

wie richte ich bei ionos einen cloud server für n8n ein

### 2. Assistent

Hier ein praxisbewährtes Schritt-für-Schritt-Leitfaden (auf Deutsch) für die Einrichtung eines IONOS-Cloud-Servers als sichere, selbst-gehostete n8n-Instanz (inkl. HTTPS).  

---

## 1 | IONOS-Server anlegen  

| Schritt | Was tun? |
|---------|----------|
| Cloud Panel → **Server & Cloud** | „Cloud Server“ erstellen. |
| **Image** | Ubuntu 22.04 LTS (x64) – LTS vereinfacht Updates. |
| **Größe** | Mind. 2 vCPU / 4 GB RAM (für kleine Workflows ausreichend). |
| **SSH-Key** | Gleich beim Anlegen hinterlegen → passwortlose Anmeldung. |
| **Firewall-Richtlinie** | Öffne TCP-Ports 22 (SSH), 80 (HTTP), 443 (HTTPS). Port 5678 bleibt intern; n8n läuft später hinter einem Reverse Proxy. |

---

## 2 | Basis-Software (Docker & Compose)

```bash
# System aktualisieren
sudo apt update && sudo apt -y full-upgrade

# Docker Engine installieren (offizielles Repo)
for pkg in docker.io docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove -y $pkg; done
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update && sudo apt -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```  
IONOS beschreibt die gleichen Schritte in seinem Ubuntu-Leitfaden. citeturn1search0

*Optional*: Benutzer zur `docker`-Gruppe hinzufügen  
```bash
sudo usermod -aG docker $USER && exec sg docker newgrp
```

Docker Compose-Plugin ist nun als Unterbefehl `docker compose` verfügbar. citeturn1search5

---

## 3 | DNS aufsetzen

* Lege in der IONOS-Domainverwaltung einen **A-Record** an, z. B.  
  ```
  Subdomain:  n8n
  Typ:        A
  Ziel:       <öffentliche_IP_des_Servers>
  ```  
* Warte, bis der Record weltweit propagiert ist (i. d. R. < 10 Min.).

---

## 4 | Projekt­verzeichnis & `.env`

```bash
mkdir -p ~/n8n-docker && cd ~/n8n-docker
nano .env
```

Mindest-Variablen (beispielhaft):

```
# .env
DOMAIN_NAME=example.com
SUBDOMAIN=n8n
GENERIC_TIMEZONE=Europe/Berlin
N8N_USER=admin
N8N_PASSWORD=<starkes_passwort>
SSL_EMAIL=markus@example.com        # für Let's Encrypt
```

---

## 5 | Docker-Compose mit Traefik (automatisches HTTPS)

Die offizielle n8n-Doku liefert ein fertiges Compose-Beispiel, das Traefik gleich als Reverse-Proxy + Zertifikats-Manager mitbringt. citeturn4view0  
`docker-compose.yml` (Minimal-Variante, auf deine Domain anpassen):

```yaml
version: "3.8"

services:
  traefik:
    image: traefik:v2.11
    restart: always
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.le.acme.tlschallenge=true"
      - "--certificatesresolvers.le.acme.email=${SSL_EMAIL}"
      - "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_data:/letsencrypt

  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    restart: always
    # Port nur intern (Traefik routed extern weiter)
    ports:
      - "127.0.0.1:5678:5678"
    environment:
      - N8N_HOST=${SUBDOMAIN}.${DOMAIN_NAME}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://${SUBDOMAIN}.${DOMAIN_NAME}/
      - GENERIC_TIMEZONE=${GENERIC_TIMEZONE}
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  traefik_data:
  n8n_data:
```

---

## 6 | Container starten

```bash
docker compose up -d
```

*Traefik* holt beim ersten Start automatisch ein Let’s-Encrypt-Zertifikat (Port 80/443 müssen erreichbar sein). Anschließend ist deine Instanz unter `https://n8n.example.com` erreichbar.

---

## 7 | n8n einrichten

1. **Login** mit den im `.env`-File gesetzten Zugangsdaten.  
2. Zeitzone prüfen (⚙ → Einstellungen).  
3. Unter „Settings → User Management“ ggf. weitere Benutzerkonten anlegen.  
4. **Webhooks** testen: neuer Workflow → Trigger „Webhook“ → URL prüfen (soll `https://n8n.example.com/webhook/...` lauten).

---

## 8 | Wartung & Updates

| Aufgabe | Befehl |
|---------|--------|
| Container-Updates | `docker compose pull && docker compose up -d` |
| Logs anzeigen | `docker compose logs -f --tail=100 n8n` |
| IONOS-Snapshots | Cloud Panel → Backups/Snapshots einrichten. |
| System-Updates | `sudo apt update && sudo apt -y full-upgrade` |

---

## 9 | Optionale Hardening-Tipps

* Fail2Ban oder UFW aktivieren (IONOS-Firewall filtert nur eingehend).  
* Backup-Strategie für `~/n8n-docker/n8n_data` (enthält DB & Encryption Key).  
* Für Multi-User-Teams empfiehlt sich Postgres statt SQLite (einfach in der Compose-Datei ergänzen).  
* Wer Nginx statt Traefik bevorzugt, kann der Let’s-Encrypt-/Nginx-Anleitung folgen. citeturn2search1  

---

**Damit läuft deine n8n-Instanz auf einem eigenständigen, automatisch abgesicherten IONOS-Cloud-Server – bereit für produktive Workflows.** Viel Erfolg beim Automatisieren!

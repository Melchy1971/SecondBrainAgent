---
title: "Unraid Docker Icon vergeben"
type: chatgpt_conversation
source: chatgpt
source_id: "6818bc2c-04c8-8007-9cc2-975b37c483c3"
created: 2025-05-05
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# Unraid Docker Icon vergeben

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6818bc2c-04c8-8007-9cc2-975b37c483c3`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

wie kann ich einem unraid docker einem tool ein icon vergeben

### 2. Assistent

**So vergibst du einem Docker‑Container in Unraid ein eigenes Icon**

### 1 . Direkt im Unraid‑GUI  
1. Docker‑Tab öffnen → beim gewünschten Container **Bearbeiten** klicken.  
2. Oben rechts den Schieberegler **„Erweiterte Ansicht“** aktivieren.  
3. Es erscheint das Feld **„Icon URL“**.  
   * Trage hier entweder  
     * eine **HTTP/HTTPS‑Adresse** zu einer PNG‑Datei (z. B. ein Raw‑Link auf GitHub) oder  
     * einen **lokalen Pfad** wie `/mnt/user/icons/meinicon.png` ein. citeturn0search0turn0search11  
4. Speichern → der Container startet neu, Unraid lädt das Icon herunter und zeigt es sofort an.

### 2 . Per *docker‑compose* (Compose Manager oder Unraid 6.12+)  
In der `docker-compose.yml` brauchst du nur ein Label in der jeweiligen Service‑Definition:  

```yaml
services:
  postgres:
    image: postgres:16
    labels:
      net.unraid.docker.icon: '/mnt/user/icons/postgres.png'
```

Beim nächsten `docker compose up -d` übernimmt Unraid das Icon automatisch. citeturn0search0turn0search2turn1search5  

### 3 . Welche Dateien funktionieren am besten?  
* **PNG** ist heutzutage am zuverlässigsten; ab Unraid 6.13 funktionieren auch SVG/WebP, aber PNG (transparenter Hintergrund, quadratisch) ist kompatibel mit allen Versionen.  
* Typische Größen: **96 × 96 px – 128 × 128 px**. Größer geht auch, wird aber nur herunterskaliert.  

### 4 . Wenn das neue Icon nicht erscheint  
* **Browser‑Cache** leeren bzw. Hard‑Refresh (Strg + F5). citeturn0search0  
* Unraid legt eine Kopie im Ordner `/boot/config/plugins/dockerMan/images/` an. Lösche dort die alte PNG (oder ersetze sie) und klicke anschließend im Docker‑Tab auf **Neu laden**. citeturn1search2  

### 5 . Bonus: Icon‑Sammlungen & Folder‑Plugin  
Für hübschere Sets lohnt sich das **Docker Folder‑Plugin**: Es erlaubt eigene Icons für Gruppenordner und verlinkt zu großen Community‑Sammlungen, die du einfach in `/boot/config/plugins/docker.folder/icons/` ablegen kannst. citeturn1search0  

Damit hast du in wenigen Klicks oder einer kurzen Compose‑Zeile dein persönliches Icon im Unraid‑Dashboard!

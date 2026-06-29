---
title: "Unraid Immich Backup Script"
type: chatgpt_conversation
source: chatgpt
source_id: "681a1022-10b0-8007-8df5-3e93aaa4f391"
created: 2025-05-06
tags:
  - chatgpt
  - code
  - import
  - ki
---


# Unraid Immich Backup Script

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `681a1022-10b0-8007-8df5-3e93aaa4f391`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

erstelle mir für unraid ein backupscript für immich welches als compose installiert ist

### 2. Assistent

Hier ist ein schlankes Bash‑Skript, das Du unter Unraid (z. B. über das User Scripts‑Plugin) ausführen kannst, um Deine Immich‑Installation, die per docker‑compose läuft, zu sichern. Passe die Variablen im Kopfbereich einmalig an Deine Verzeichnisse / Container‑Namen an.

```bash
#!/bin/bash
# Immich‑Backup für Unraid – Version 2025‑05‑06
# ------------------------------------------------------------
# Sichert:
#   • komplette Postgres‑Datenbank (pg_dumpall)
#   • Upload‑Ordner (Fotos/Videos)
#   • docker‑compose.yml und .env
# Beibehaltung: 14 Tage
# ------------------------------------------------------------

set -euo pipefail

######################  KONFIGURATION  ######################
COMPOSE_DIR="/mnt/user/appdata/immich"      # Pfad zum compose‑Stack
UPLOADS_DIR="/mnt/user/immich/uploads"      # Ordner mit Medien
BACKUP_DIR="/mnt/user/backups/immich"       # Ziel für Backups
RETENTION_DAYS=14                           # Aufbewahrungsdauer
POSTGRES_USER="postgres"                    # DB‑Benutzer

# Container‑ID des Postgres‑Dienstes aus dem Compose‑Stack ermitteln
DB_CONTAINER="$(docker compose -f "${COMPOSE_DIR}/docker-compose.yml" ps -q db)"

######################  BACKUP‑LOGIK  ########################
DATE="$(date +'%Y-%m-%d_%H-%M-%S')"
TARGET_DIR="${BACKUP_DIR}/${DATE}"
mkdir -p "${TARGET_DIR}"

echo "▶️  Starte Datenbank‑Dump (${DATE}) …"
docker exec "${DB_CONTAINER}" \
  pg_dumpall -U "${POSTGRES_USER}" | gzip > "${TARGET_DIR}/immich_db_${DATE}.sql.gz"

echo "📂  Kopiere Uploads …"
rsync -a --delete "${UPLOADS_DIR}/" "${TARGET_DIR}/uploads/"

echo "⚙️  Sichere docker-compose.yml und .env …"
cp "${COMPOSE_DIR}/docker-compose.yml" "${TARGET_DIR}/"
[[ -f "${COMPOSE_DIR}/.env" ]] && cp "${COMPOSE_DIR}/.env" "${TARGET_DIR}/"

echo "🧹  Entferne Backups, die älter als ${RETENTION_DAYS} Tage sind …"
find "${BACKUP_DIR}" -maxdepth 1 -type d -mtime +"${RETENTION_DAYS}" -exec rm -rf {} \;

echo "✅  Backup abgeschlossen: ${TARGET_DIR}"
```

### So setzt Du das Skript ein

1. **Speichern**  
   Lege die Datei z. B. unter  
   `/boot/config/plugins/user.scripts/scripts/immich_backup/immich_backup.sh`  
   ab und mache sie ausführbar:  
   ```bash
   chmod +x /boot/config/plugins/user.scripts/scripts/immich_backup/immich_backup.sh
   ```

2. **Testlauf**  
   Starte das Skript einmal manuell über das User Scripts‑Plugin oder per SSH, um zu prüfen, ob alles korrekt durchläuft.

3. **Planung**  
   Im User Scripts‑Plugin „Scheduling“ aktivieren, z. B. täglich um 03:00 Uhr:  
   ```
   Custom cron schedule: 0 3 * * *
   ```

4. **Wiederherstellung**  
   - **Datenbank**:  
     ```bash
     zcat immich_db_<DATUM>.sql.gz | docker exec -i <db_container> psql -U postgres
     ```  
   - **Uploads** zurückkopieren:  
     ```bash
     rsync -a <TARGET_DIR>/uploads/ /mnt/user/immich/uploads/
     ```  
   - **compose‑Dateien** bei Bedarf zurück ins Compose‑Verzeichnis legen.

---

**Tipps**

- Für eine «perfekt konsistente» Sicherung könntest Du vor dem Dump die Immich‑Container kurz stoppen (`docker compose stop`) und danach wieder starten. In der Praxis reicht der Online‑Dump in den meisten Fällen.  
- Wenn Du mehrere Compose‑Stacks oder benutzerdefinierte Container‑Namen hast, ersetze den Service‑Alias `db` in `DB_CONTAINER="$(docker compose … ps -q db)"` entsprechend.

Viel Erfolg — und sichere Deine Fotos regelmäßig! 😉

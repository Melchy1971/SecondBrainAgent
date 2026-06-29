---
title: "n8n Email Spam Filter"
type: chatgpt_conversation
source: chatgpt
source_id: "6821af84-363c-8007-abcd-ad0d285a626d"
created: 2025-05-12
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# n8n Email Spam Filter

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6821af84-363c-8007-abcd-ad0d285a626d`
- Nachrichten: 8

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich möchte einen email agenten mit n8n erstellen welcher meinen email account bei ionos ausliest und nach spam durchsucht und diese löscht.

### 2. Assistent

Hier findest du eine praxisbewährte Vorgehens­weise, um mit **n8n** einen Agenten zu bauen, der dein IONOS‑Postfach per IMAP nach Spam durch­sucht und diese Mails automatisch entfernt.

---

## 1 | Vorbereitungen

| Was | Details |
|---|---|
| IONOS‑Serverdaten | `imap.ionos.de`, Port 993, SSL/TLS, Benutzername = vollständige Mailadresse, Passwort / App‑Passwort citeturn6search5 |
| n8n‑Version | mind. v1.30 (ältere Versionen gehen auch, Community‑Node siehe unten) |
| IMAP‑Credentials in n8n | **Credentials → IMAP** anlegen, Auth‑Methode *User account* citeturn8search7 |

> **Tipp:** Lege das Passwort als Umgebungs­variable (`N8N_IMAP_PASSWORD`) an, damit es nicht im Klartext in der Workflow‑JSON steckt.

---

## 2 | Grund­workflow: „Spam‑Ordner leeren“

Die einfachste Lösung nutzt den Spam‑Ordner, den IONOS von Haus aus erstellt und befüllt citeturn6search1:

1. **Cron‑Trigger**  
   *Alle 30 Minuten* oder dein bevorzugtes Intervall.

2. **Email IMAP Node** (built‑in)  
   - **Mailbox Name:** `Spam`  
   - **Action:** *Receive*  
   - **Mark as Read:** egal (wird gleich gelöscht)  
   - **Download Attachments:** *off* (spart Traffic)

3. **Email IMAP Node (zweites Exemplar)**  
   - **Operation:** *Delete*  
     > Falls deine n8n‑Version hier noch kein **Delete** anbietet, nimm stattdessen **Move** → Ziel‑Mailbox `Trash`. Bei IONOS wird der Papierkorb regel­mäßig geleert.

4. **Optional:**  
   - **IF‑Node** → lösche nur, wenn die Mail älter als X Tage ist  
   - **Slack/Telegram/E-Mail** → kurzes Log, wie viele Mails gelöscht wurden.

---

## 3 | Eigenes Spam‑Scoring (wenn du lieber selbst entscheidest)

Wenn du erst nach bestimmten Kriterien löschen möchtest:

1. **Email IMAP Node**  
   - **Mailbox Name:** `INBOX` (oder ein beliebiger Ordner)  
   - **Custom Search Query:**  
     ```text
     HEADER X-Spam-Flag YES
     ```  
     (IONOS setzt einen *X‑Spam‑Score*‑Header; > 5 Punkte ist meist Spam)

2. **IF‑Node**  
   ```js
   {{ $json.headers['X-Spam-Flag'] === 'YES' || Number($json.headers['X-Spam-Score']) > 5 }}
   ```

3. **Community‑Node „n8n‑nodes‑imap“** installieren (Settings → Community nodes) – der Node kann Mails verschieben oder hart löschen citeturn9search2.  
   - **Operation:** *Move* → `Spam` *oder* *Delete permanently*

4. **Fallback**, falls du keine Community‑Nodes verwenden willst:  
   - **Code‑Node (JavaScript)** und das n8n‑interne `imap`‑Wrapper‑Paket nutzen, um `addFlags("\\Deleted")` + `expunge()` auszuführen (Beispiel siehe README des Wrappers citeturn9search7).

---

## 4 | Workflow‑Beispiel (gekürzt)

```json
{
  "nodes": [
    {
      "parameters": { "triggerTimes": { "item": [{ "hour": "*/1", "minute": 15 }] } },
      "id": "Cron"
    },
    {
      "parameters": {
        "mailbox": "INBOX",
        "options": { "customSearch": "HEADER X-Spam-Flag YES" },
        "markAsRead": true
      },
      "id": "IMAP‑Read",
      "credentials": { "imap": "IONOS‑IMAP" }
    },
    {
      "parameters": {
        "expression": "{{ $json.headers['X-Spam-Flag'] === 'YES' }}"
      },
      "id": "IF‑Spam"
    },
    {
      "parameters": {
        "operation": "Delete"
      },
      "id": "IMAP‑Delete",
      "credentials": { "imap": "IONOS‑IMAP" }
    }
  ],
  "connections": {
    "Cron": { "main": [["IMAP‑Read"]] },
    "IMAP‑Read": { "main": [["IF‑Spam"]] },
    "IF‑Spam": { "main": [{ "true": ["IMAP‑Delete"] }] }
  }
}
```

---

## 5 | Wichtige Stolperfallen & Best Practices

| Thema | Empfehlung |
|---|---|
| **Doppelte Verarbeitung** | IMAP‑Node liest standard­mäßig nur *ungelesene* Mails. Setze „Mark as Read“ = *_auf jeden Fall_* auf *true*, sonst holt er dieselbe Mail wieder citeturn9search5. |
| **Limits** | IONOS erlaubt ~30 Verbindungen / Minute pro Konto. Bei hohem Intervall ggf. `keepAlive: true` im Community‑Node setzen. |
| **Testing** | Starte den Workflow zunächst manuell und lasse ihn bei einer Test‑Mail stoppen, um zu sehen, welche Header ankommen. |
| **Rollback** | Statt „Delete“ kannst du zuerst „Move → Spam“ nutzen. Läuft alles stabil, änderst du die letzte Node auf „Delete“. |
| **Protokoll** | Logge die IDs gelöschter Mails in eine Datenbank oder ein Spreadsheet; so kannst du versehentliche Löschungen nachvollziehen (Community‑Beitrag zum Löschen nach Absender citeturn0search0). |

---

## 6 | Ausblick

- **Trainierbarer Filter:** Schicke verdächtige Mails via HTTP Request an einen selbst gehosteten SpamAssassin oder SaaS‑Dienst und nutze dessen Score.
- **KI‑Ansatz:** Nutze den OpenAI‑Modell‑Node, gib Betreff + Auszug als Prompt und lasse die KI entscheiden („spam“ vs. „ham“).  
- **Mehrere Postfächer:** Packe das Ganze in eine Sub‑Workflow‑Funktion und rufe sie aus einem Loop mit verschiedenen IMAP‑Credentials auf.

Viel Erfolg beim Aufräumen deines Postfachs! 🎉

### 3. Benutzer

erstelle mir eine importdatei für n8n

### 4. Assistent

Hier ist die fertige **n8n‑Importdatei** für deinen Spam‑Cleaner‑Workflow. Lade sie einfach in n8n hoch (Settings → Import) und hinterlege anschließend dein IMAP‑Credential „IONOS IMAP“.

[Download die Workflow‑Datei](sandbox:/mnt/data/n8n_ionos_spam_cleaner.json)

### 5. Benutzer

wie installiere ich private note´s in meiner n8n docker installation

### 6. Assistent

### Schnellüberblick  

> **Community‑/Private‑Nodes** lassen sich in Docker‑Setups nicht per Klick installieren. Du musst sie *manuell* in den Container bringen oder dir gleich ein eigenes Image bauen. Die zweite Variante ist dauerhaft sauberer.

---

## Variante A – „Einmal eben schnell“ (nicht updatesicher)

1. **In den laufenden Container einloggen**  
   ```bash
   docker exec -it n8n sh
   ```

2. **Verzeichnis anlegen** (falls noch nicht vorhanden) und hinein­wechseln  
   ```bash
   mkdir -p ~/.n8n/nodes && cd ~/.n8n/nodes
   ```

3. **Node installieren** – Beispiel  
   ```bash
   npm i n8n-nodes-meinPrivatesPaket
   ```

4. **Container neu starten** (`docker restart n8n`) – danach taucht der Node im Editor auf.  
   citeturn3view0  

> ⚠️ Sobald du das Basis‑Image aktualisierst oder den Container neu baust, ist der Node wieder weg.

---

## Variante B – Eigenes Docker‑Image (empfohlen)

### 1 | Dockerfile anlegen

```Dockerfile
# basierend auf dem offiziellen n8n‑Image
FROM n8nio/n8n:latest

### Root‑Rechte nur zum Installieren verwenden
USER root

# → aus privater Registry, GitHub Package Registry, oder lokaler *.tgz
RUN npm_config_user=root \
    npm install -g n8n-nodes-meinPrivatesPaket

# n8n soll wissen, wo die gebauten Dateien liegen
ENV N8N_CUSTOM_EXTENSIONS="/usr/local/lib/node_modules/n8n-nodes-meinPrivatesPaket"

# zurück zum Standard‑User
USER node
```

*Bauen & taggen*  
```bash
docker build -t n8n-custom:1.0 .
```  
citeturn5view0  

### 2 | docker‑compose.yml anpassen

```yaml
services:
  n8n:
    image: n8n-custom:1.0
    container_name: n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_CUSTOM_EXTENSIONS=/usr/local/lib/node_modules/n8n-nodes-meinPrivatesPaket
      - TZ=Europe/Berlin
    volumes:
      - n8n_data:/home/node/.n8n
volumes:
  n8n_data:
```

*Warum die ENV‑Variable?*  
Ohne explizite Angabe scannt n8n nur `~/.n8n/custom`. Mit `N8N_CUSTOM_EXTENSIONS` kannst du beliebige Verzeichnisse – per Semikolon getrennt – angeben (z. B. mehrere private Pakete oder ein gemountetes Volume). citeturn6view0  

### 3 | Container starten

```bash
docker compose up -d
```

---

## Authentifizierung bei privaten npm‑Registries

- **Token als Build‑Arg**  
  ```Dockerfile
  ARG NPM_TOKEN
  RUN npm set //registry.npmjs.org/:_authToken=$NPM_TOKEN \
      && npm install -g <dein‑paket>
  ```
  Dann beim Build:  
  `docker build --build-arg NPM_TOKEN=$NPM_TOKEN -t n8n-custom .`

- **SSH‑Deploy‑Keys** oder `.npmrc` per `COPY` ins Image legen (nicht vergessen: `.npmrc` wieder löschen oder in mehrstufigem Build).

---

## Typische Stolperfallen & Tipps

| Problem | Lösung |
|---|---|
| Node erscheint nicht | Prüfe im Log (`docker logs n8n`) auf Meldungen wie *“Could not load custom extension”*. Oft fehlt der `dist/`‑Ordner (vergiss bei TypeScript‑Nodes das `npm run build` nicht). |
| Container‑Updates löschen den Node | Immer **eigene Images** fahren oder ein Volume mit dem kompilierten Node mounten und den Pfad in `N8N_CUSTOM_EXTENSIONS` setzen. |
| Queue‑Mode | Installation *muss* manuell erfolgen – UI ist hier disabled. Vorgehen wie oben. |
| Mehrere private Nodes | Pfade in `N8N_CUSTOM_EXTENSIONS` mit Semikolon trennen, z. B. `/custom/nodes/pkg1;/custom/nodes/pkg2`. |
| Performance | Custom‑Nodes werden nur beim Start geladen; ein Neustart ist ausreichend, ein kompletter Re‑Build erst bei Versions‑Updates nötig. |

Damit hast du eine saubere, reproduzierbare Lösung, bei der deine privaten Nodes jedes Mal automatisch verfügbar sind – egal wann du das Basis‑Image aktualisierst. Viel Erfolg beim Basteln! 🎉

### 7. Benutzer

stelle mir bitte alle dateien zum download bereit

### 8. Assistent

Hier sind alle aktuellen Dateien zum Herunterladen:

- **n8n‑Workflow (Spam‑Cleaner)**  
  [Download n8n_ionos_spam_cleaner.json](sandbox:/mnt/data/n8n_ionos_spam_cleaner.json)

- **Dockerfile** – eigenes n8n‑Image mit privaten Nodes  
  [Download Dockerfile](sandbox:/mnt/data/Dockerfile)

- **docker‑compose.yml** – Beispiel‑Setup zum Starten des Containers  
  [Download docker-compose.yml](sandbox:/mnt/data/docker-compose.yml)

Zieh die drei Dateien auf deinen Host, passe ggf. Paketnamen, Tokens und Umgebungs­variablen an und baue dann mit:

```bash
docker compose build        # eigenes Image erstellen
docker compose up -d        # n8n starten
```

Viel Erfolg beim Einrichten! 🎉

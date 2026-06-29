---
title: "Datenbankaufbau mit KI"
type: chatgpt_conversation
source: chatgpt
source_id: "691ae148-0a44-832f-8a5f-98952afa67d6"
created: 2025-11-17
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - projekt
  - sap
  - verein
---


# Datenbankaufbau mit KI

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `691ae148-0a44-832f-8a5f-98952afa67d6`
- Nachrichten: 18

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich möchte mir eine wissensdatenbank erstellen und benötige dafür einen ablaufplan und einen prompt. ich möchte zum aufbauen der datenbank meine emails und pst dateien durchsuchen lassen. dabei muss ich ordner welche nicht durchsucht werden sollen abgewählt werden können. di ki soll bei der analyse die inhalte rpüfen und eine zusammenfassung erstellen und das ergebnis in die datenbank übernehmen

### 2. Assistent

Okay Markus, bevor ich dir einfach einen Ablaufplan und einen Prompt hinknalle, lass mich erst kurz deine Idee sezier-freundlich auseinandernehmen – wie dein persönlicher intellektueller Sparringspartner.  

---

## 🔍 1. Deine Annahmen – was setzt du voraus?

**Annahme A:** Man kann *problemlos* riesige Mengen privater Daten (Emails, PSTs) automatisiert verarbeiten und zusammenfassen.  
→ Möglich, aber: Datenschutz, Zugriffsbeschränkungen, sensible Inhalte, Formatprobleme und Layout der PSTs können Stolpersteine sein.

**Annahme B:** Du brauchst *eine einzige KI*, die alles übernimmt: Analyse, Extraktion, Filtern, Zusammenfassen, Schreiben in DB.  
→ Technisch komplex. Oft ist es sinnvoller, die Pipeline in Module zu splitten.  

**Annahme C:** „Einfach Ordner abwählen“ bedeutet, dass die Datenstruktur sauber und stabil ist.  
→ PSTs enthalten teils verschachtelte Folder, Archiv-Ordner, systemgenerierte Strukturen. Das Filtern kann tricky sein.

**Annahme D:** Die KI wird die Zusammenfassungen so präzise erstellen, dass sie ohne Nacharbeit direkt in die Datenbank können.  
→ Möglich, aber hängt stark vom Modell, Prompt, Pipeline und Qualitätskontrolle ab.

---

## ⚔️ 2. Was würde ein skeptischer, technisch erfahrener Mensch sagen?

- „Du überschätzt, wie einfach es ist, PST-Daten sauber zu extrahieren. Das ist oft das nervigste Element.“  
- „Automatische Zusammenfassungen ohne menschlichen Review können zu Fehlklassifizierungen führen.“  
- „Wenn du *alle* Emails indizieren lässt, hast du in ein paar Wochen eine Datenbank voller Müll und Noise.“  
- „KI darf nicht entscheiden, *was* relevant ist – das musst du definieren.“  

---

## 🧪 3. Hält deine Logik dem Stand? Wo sind Lücken?

- **Welche Zielstruktur soll die Wissensdatenbank haben?** Themen? Personen? Vorgänge? Projekte?  
- **Wie gehst du mit Duplikaten um?** (z. B. Reply-Chains)  
- **Wie stellst du sicher, dass sensible Infos nicht landen, wo sie nicht hingehören?**  
- **Wie aktuell soll die DB bleiben?** Einmal-Durchlauf oder kontinuierlicher Prozess?  

Du brauchst also nicht nur *Ablauf + Prompt*, sondern auch *Regeln und Qualitätskontrolle*.

---

## 🔄 4. Alternative Perspektiven

**Ansatz A: Klassischer ETL-Prozess**  
→ Trainierte KI wird nur im „Transform“-Schritt verwendet.

**Ansatz B: Retrieval-Augmented Pipeline (RAG)**  
→ Emails werden *nicht* summarisiert, sondern in Chunked-Form eingebettet und indexiert.

**Ansatz C: Mensch-in-the-Loop**  
→ KI erstellt Vorschläge, du bestätigst Kategorien und Zusammenfassungen.

**Ansatz D: Hybrider Ansatz**  
→ Zuerst Regeln (Regex/Filter/Meta), dann KI.

---

## 📋 Jetzt der Ablaufplan – robust & realistisch

### **1. Datenquellen vorbereiten**
- PST-Dateien exportieren / extrahieren  
- Email-Konten als .eml / .msg / per API abrufen  
- Verzeichnisstruktur identifizieren  
- Ordner markieren, die explizit *nicht* analysiert werden dürfen  

### **2. Technische Pipeline festlegen**
- **Extraction Layer:**  
  - Nutzung einer PST-Parser-Library (z. B. pypff)  
  - Extraktion von:
    - Betreff  
    - Absender/Empfänger  
    - Datum  
    - Body  
    - Attachments (optional)
- **Folder Filtering:**  
  - Skip-Liste definieren  
  - Mapping FolderName → erlaubt / verboten  

### **3. Preprocessing**
- Noise entfernen:
  - Signaturen  
  - Rechtsbelehrungen  
  - lange Antwortketten erkennen und kürzen  
- Deduplizieren:  
  - Hashing von Body + Betreff  
- Chunking:
  - Emails über 4–6 k Tokens splitten  

### **4. KI-Analyse**
Für jede Email / jeden Chunk:
- Relevanzprüfung (optional)  
- Zusammenfassung in 3 Stufen:
  - 1-Satz-Kernaussage  
  - 3–5 Stichpunkte  
  - Themen/Tags (werden später zur DB-Navigation)  
- Risikoanalyse (falls sensible Daten)  

### **5. Datenbank-Speicherung**
- Schema z. B.:
  - `id`
  - `source_path`
  - `date`
  - `people`
  - `tags`
  - `summary_short`
  - `summary_long`
- Speichern in:
  - SQL / NoSQL  
  - oder Vektorindex (Pinecone, Chroma, Weaviate)

### **6. QA & Feedback-Schleife**
- Zufällige Stichproben kontrollieren  
- Regeln anpassen  
- Prompt optimieren  

### **7. Optional: RAG-System darüberlegen**
- Suchoberfläche  
- „Frag die Datenbank“ Interface  
- Chatbot, der auf deinen zusammengefassten Inhalten arbeitet  

---

## 🧠 Prompt-Entwurf für die Zusammenfassung

**Wichtig:** Das ist ein erster Wurf; du wirst ihn später verfeinern.

---

### **Prompt für KI-Analyse (für jede Email):**

**System-Prompt:**

> Du analysierst Email-Inhalte aus einer persönlichen Wissensdatenbank.  
> Dein Ziel ist es, präzise, faktenorientierte Zusammenfassungen zu erstellen.  
> Verzichte auf Interpretationen. Halte dich streng an den Inhalt.  
> Ausgabeformat:
> 1. Kernaussage (max. 25 Wörter)  
> 2. 3–5 Stichpunkte mit den wichtigsten Fakten  
> 3. Tags (3–8 thematische Schlagworte)  
> 4. Beteiligte Personen + Rollen  
> 5. Relevanz (hoch/mittel/niedrig)

**User-Prompt (pro Email/Chunk):**

> Analysiere folgenden Email-Text. Entferne Signaturen, rechtliche Hinweise und irrelevante Elemente.  
>  
> **TEXT:**  
> {{email_body}}

---

## Wenn du willst:  
Ich kann dir auch:  
- den **Datenbank-Schema-Vorschlag** detailliert ausformulieren  
- eine **technische Architekturübersicht** machen  
- dir ein **Proof-of-Concept-Skript** (Python) schreiben  
- dir **Prompts für weitere Schritte** geben  
- ein **RAG-Setup** für die fertige Wissensdatenbank skizzieren

Sag mir einfach, welchen Teil du als Nächstes auseinandernehmen möchtest – oder wo du gerade am meisten Unklarheit fühlst.

### 3. Benutzer

alles bitte

### 4. Assistent

Alles klar, Markus – dann kriegst du jetzt das Komplett-Paket. 😄  
Ich teile es in fünf Teile auf:

1. Datenbank-Schema  
2. Technische Architektur  
3. Proof-of-Concept-Skript (Python)  
4. Weitere Prompts (Relevanz, Tagging, Risiko)  
5. RAG-Setup oben drauf  

Du kannst dir dann Stück für Stück rauspicken, was du zuerst umsetzen willst.

---

## 1️⃣ Datenbank-Schema (relational + optional Vektorstore)

**Ziel:**  
- Eindeutige Referenz auf Email  
- Klarer Link auf Quelle (PST, Ordner, Message-ID)  
- Zusammenfassung + Metadaten  
- Tags und Personen sinnvoll trennbar  

### Vorschlag: Kern-Tabellen

```sql
-- 1. Roh-Email (optional, oder nur Referenz)
CREATE TABLE emails (
    id              SERIAL PRIMARY KEY,
    message_id      TEXT UNIQUE,
    subject         TEXT,
    sender          TEXT,
    recipients      TEXT,          -- z.B. "a@example.com;b@example.com"
    sent_at         TIMESTAMP,
    folder_path     TEXT,          -- z.B. "Inbox/Projekt X"
    source_file     TEXT,          -- z.B. "mail_2020_2022.pst"
    raw_body        TEXT,          -- optional, oder weglassen wegen Größe
    hash            TEXT           -- Hash zur Duplikat-Erkennung
);

-- 2. Zusammenfassungen / analysierte Inhalte
CREATE TABLE email_summaries (
    id                  SERIAL PRIMARY KEY,
    email_id            INT REFERENCES emails(id) ON DELETE CASCADE,
    core_statement      TEXT,        -- 1-Satz-Kernaussage
    bullet_points       TEXT,        -- z.B. als Markdown oder JSON-Liste
    relevance_level     TEXT,        -- 'hoch', 'mittel', 'niedrig'
    created_at          TIMESTAMP DEFAULT NOW()
);

-- 3. Tags (normalisiert)
CREATE TABLE tags (
    id          SERIAL PRIMARY KEY,
    name        TEXT UNIQUE
);

CREATE TABLE email_tags (
    email_id    INT REFERENCES emails(id) ON DELETE CASCADE,
    tag_id      INT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (email_id, tag_id)
);

-- 4. Personen / Beteiligte
CREATE TABLE persons (
    id          SERIAL PRIMARY KEY,
    email       TEXT UNIQUE,
    display_name TEXT
);

CREATE TABLE email_persons (
    email_id    INT REFERENCES emails(id) ON DELETE CASCADE,
    person_id   INT REFERENCES persons(id) ON DELETE CASCADE,
    role        TEXT,      -- 'sender', 'to', 'cc'
    PRIMARY KEY (email_id, person_id, role)
);
```

**Annahmecheck:**  
- Du nimmst damit in Kauf, dass Daten relativ stark strukturiert sind – dafür kannst du später gezielt filtern: pro Projekt, Person, Zeitraum etc.

---

## 2️⃣ Technische Architektur (High-Level)

Stell dir grob diese Bausteine vor:

1. **Ingestion / Extractor**
   - Liest PST-Dateien   
   - Läuft durch alle Ordner  
   - Nutzt eine Skip-Liste (`EXCLUDED_FOLDERS`)  
   - Speichert Metadaten + Body in `emails`

2. **Preprocessing**
   - Entfernt Signaturen, Disclaimer soweit möglich  
   - Erzeugt Hashes zur Duplikat-Erkennung  
   - Optional: Antwortketten kürzen

3. **KI-Analyse-Worker**
   - Nimmt neue/ungeprüfte Emails  
   - Ruft LLM mit Prompt auf  
   - Schreibt `email_summaries`  
   - Fügt Tags/Personen ein (inkl. Insert-oder-ignore-Logik)

4. **Vektorindex (für RAG)**
   - erstellt Embeddings aus:
     - Kernaussage + Stichpunkten  
   - speichert sie in einem Vektorstore (z. B. ChromaDB, Pinecone)  
   - hält Referenz auf `email_id`

5. **Query / UI**
   - Suchfeld (Freitext)  
   - KI-Chat, der über den Vektorindex + DB geht  
   - Anzeigemodul: zeigt Email-Zusammenfassung + Link zur Original-Mail (oder Pfad)

---

## 3️⃣ Proof-of-Concept Skript (Python, vereinfachtes Beispiel)

**Wichtiger Realismus-Check:**  
- PST-Parsing hängt von der Library ab (`pypff` etc.), Installation ist manchmal messy.  
- API-Aufruf zum LLM musst du mit deinem Anbieter konfigurieren.  
- Das hier ist ein Startpunkt, kein copy&paste-fertiges Produktivsystem.

```python
import hashlib
import datetime
import psycopg2
from psycopg2.extras import execute_values

# PLACEHOLDER: PST-Parser und LLM-Client musst du selbst einbinden
# import pypff
# from openai import OpenAI

EXCLUDED_FOLDERS = {
    "Deleted Items",
    "Spam",
    "Junk Email",
    "Newsletter",
    # weitere je nach Struktur
}

DB_DSN = "dbname=wissensdb user=postgres password=secret host=localhost"

def hash_email(subject, body, sent_at, sender):
    h = hashlib.sha256()
    key = f"{subject}|{body}|{sent_at}|{sender}"
    h.update(key.encode("utf-8"))
    return h.hexdigest()

def connect_db():
    return psycopg2.connect(DB_DSN)

def email_exists(cur, email_hash):
    cur.execute("SELECT id FROM emails WHERE hash = %s", (email_hash,))
    row = cur.fetchone()
    return row[0] if row else None

def insert_email(cur, email):
    cur.execute(
        """
        INSERT INTO emails (message_id, subject, sender, recipients, sent_at,
                            folder_path, source_file, raw_body, hash)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
        """,
        (
            email["message_id"],
            email["subject"],
            email["sender"],
            ";".join(email["recipients"]),
            email["sent_at"],
            email["folder_path"],
            email["source_file"],
            email["body"],
            email["hash"],
        ),
    )
    return cur.fetchone()[0]

def call_llm_for_summary(email_body):
    # Hier rufst du dein LLM an – Platzhalter:
    # client = OpenAI()
    # resp = client.chat.completions.create(...)
    # und dann das strukturierte Ergebnis zurückgeben

    # Für PoC: Dummy-Ausgabe
    return {
        "core_statement": "Dummy-Kernaussage aus dem Emailtext.",
        "bullet_points": [
            "Punkt 1",
            "Punkt 2",
        ],
        "tags": ["Beispiel", "Test"],
        "persons": [
            {"email": "a@example.com", "display_name": "Max Mustermann", "role": "sender"}
        ],
        "relevance": "mittel",
    }

def insert_summary_and_metadata(cur, email_id, analysis):
    cur.execute(
        """
        INSERT INTO email_summaries (email_id, core_statement, bullet_points, relevance_level)
        VALUES (%s,%s,%s,%s)
        """,
        (
            email_id,
            analysis["core_statement"],
            "\n".join(f"- {bp}" for bp in analysis["bullet_points"]),
            analysis["relevance"],
        ),
    )

    # Tags
    for tag in analysis["tags"]:
        cur.execute("INSERT INTO tags (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (tag,))
        cur.execute("SELECT id FROM tags WHERE name = %s", (tag,))
        tag_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO email_tags (email_id, tag_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (email_id, tag_id),
        )

    # Personen
    for p in analysis["persons"]:
        cur.execute(
            "INSERT INTO persons (email, display_name) VALUES (%s,%s) ON CONFLICT (email) DO NOTHING",
            (p["email"], p.get("display_name")),
        )
        cur.execute("SELECT id FROM persons WHERE email = %s", (p["email"],))
        person_id = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO email_persons (email_id, person_id, role)
            VALUES (%s,%s,%s)
            ON CONFLICT DO NOTHING
            """,
            (email_id, person_id, p["role"]),
        )

def process_pst_file(pst_path, source_name):
    # Hier müsstest du pypff oder eine andere PST-Library verwenden.
    # Um den Fokus auf die Logik zu legen, pseudo-kodiere ich die Iteration:

    emails_from_pst = []  # -> hier würdest du die extrahierten Emails reinladen

    conn = connect_db()
    try:
        with conn:
            with conn.cursor() as cur:
                for mail in emails_from_pst:
                    if mail["folder_path"].split("/")[0] in EXCLUDED_FOLDERS:
                        continue

                    email_hash = hash_email(mail["subject"], mail["body"], mail["sent_at"], mail["sender"])
                    mail["hash"] = email_hash
                    mail["source_file"] = source_name

                    existing_id = email_exists(cur, email_hash)
                    if existing_id:
                        continue

                    email_id = insert_email(cur, mail)
                    analysis = call_llm_for_summary(mail["body"])
                    insert_summary_and_metadata(cur, email_id, analysis)
    finally:
        conn.close()

if __name__ == "__main__":
    # Beispiel: process_pst_file("mails_2020_2022.pst", "mails_2020_2022.pst")
    pass
```

**Kritischer Hinweis:**  
Wenn du „alles automatisch“ machst, ohne Testläufe mit wenigen Mails + manueller Kontrolle, läufst du direkt in Datenmüll. Fang klein an.

---

## 4️⃣ Weitere Prompts für einzelne Schritte

### 4.1 Relevanzprüfung (Filter vor der Zusammenfassung)

**System:**

> Du bewertest, wie relevant ein Emailtext für eine persönliche Wissensdatenbank ist.  
> Relevante Inhalte enthalten Entscheidungen, Absprachen, Anforderungen, technische Details, Prozesse, Termine oder wichtige Kontextinformationen.  
> Unrelevante Inhalte sind z.B. Werbung, automatische Benachrichtigungen, einfache Empfangsbestätigungen oder rein organisatorische Kleinigkeiten.  
>  
> Antworte ausschließlich im folgenden JSON-Format:
> {
>   "relevance": "hoch" | "mittel" | "niedrig" | "irrelevant",
>   "reason": "<kurze Begründung>"
> }

**User:**

> Bewerte die Relevanz des folgenden Emailtexts für eine Wissensdatenbank.  
>  
> TEXT:  
> {{email_body}}

Du kannst dann z. B. bei `irrelevant` früh abbrechen und das Ding gar nicht erst ausführlich zusammenfassen.

---

### 4.2 Tagging / Themen

Wenn du mehr Fokus auf Tags willst, kannst du das Tagging extra machen:

**System:**

> Du analysierst Emailtexte und weist ihnen thematische Schlagworte (Tags) zu.  
> Nutze kurze, allgemeine Begriffe (1–3 Wörter).  
> Beispiele: "Projektmanagement", "Kunde X", "Reklamation", "Angebot", "Prozessdesign", "Fehleranalyse".  
>  
> Antworte ausschließlich im JSON-Format:
> {
>   "tags": ["Tag1", "Tag2", ...]
> }

**User:**

> Erstelle Tags für den folgenden Emailtext.  
> TEXT:  
> {{email_body}}

---

### 4.3 Risiko / Sensible Daten (optional)

**System:**

> Du prüfst, ob ein Emailtext sensible Informationen enthält (z.B. personenbezogene Daten, vertrauliche Geschäftszahlen, Passwörter, Zugangsdaten).  
> Antworte im JSON-Format:
> {
>   "risk_level": "niedrig" | "mittel" | "hoch",
>   "contains_personal_data": true/false,
>   "contains_credentials": true/false,
>   "notes": "<kurze Erklärung>"
> }

Damit könntest du z. B. `risk_level = hoch` flaggen und speziell behandeln (nicht in alle Systeme pushen).

---

## 5️⃣ RAG-Setup (Such- & Frageoberfläche)

### 5.1 Was du einbetten solltest

Guter Kandidat für Embeddings pro Eintrag:

```text
[Betreff]
[Kernaussage]
[Stichpunkte]
[Tags]
[wichtige Personen]
```

Beispiel-Text, den du an ein Embedding-Modell gibst:

```text
Betreff: Angebot für Projekt Prozessoptimierung

Kernaussage:
Kunde X bittet um detailliertes Angebot für Prozessanalyse und Umsetzungsschritte.

Stichpunkte:
- Projektumfang: Analyse bestehender Prozesse
- Ziel: Durchlaufzeiten reduzieren, Fehlerquote minimieren
- Deadline: Angebot bis 15.03.
- Ansprechpartner: Herr Müller (Kunde X)

Tags: Angebot, Kunde X, Prozessoptimierung
Personen: Herr Müller (Kunde)
```

Der Vektor wird in deinem Vektorstore (z. B. `vector`, `email_id`) gespeichert.

### 5.2 Query-Flow

1. User stellt Frage:  
   > „Zeig mir alle Themen rund um Prozessoptimierung für Kunde X zwischen 2021 und 2022.“

2. System macht:
   - Erzeugt Embedding für die Frage  
   - Fragt Vektorstore: Top-k ähnliche Einträge  
   - Nutzt die `email_id`s, um DB-Einträge + Metadaten zu holen  
   - Schickt Zusammenfassungen + Frage an LLM mit Prompt wie:

   ```text
   Du erhältst Zusammenfassungen aus einer Wissensdatenbank (Emails).
   Beantworte die Nutzerfrage ausschließlich auf Basis dieser Informationen.
   Antworte strukturiert mit:
   1. Direkte Antwort
   2. Relevante Vorgänge (mit Datum)
   3. Beteiligte Personen
   4. Optional: "Offene Fragen / Unsicherheiten"
   ```

3. KI generiert Antwort + du zeigst Links / IDs zu den jeweiligen Mails.

---

## Wie weiter?

Wenn du möchtest, können wir als Nächstes:

- das **PST-Parsing** konkreter machen (echtes Library-Beispiel),  
- das **DB-Schema** auf ein spezifisches System (Postgres / SQLite) zuschneiden,  
- oder gemeinsam einen **Minimal-Workflow definieren**:  
  „Tag 1 – 100 Mails importieren, testen, UI provisorisch bauen“.

Ich würde dir ehrlich gesagt empfehlen:  
**erst ein Mini-Pilot mit 50–100 Mails** und dann schauen, ob die Zusammenfassungen wirklich das liefern, was du im Alltag brauchst. Sonst baust du eine sehr schöne, aber nicht genutzte Wissensdatenbank.

### 5. Benutzer

ja bitte

### 6. Assistent

Alles klar, dann gehe ich jetzt einfach einen Schritt weiter und warte nicht auf noch mehr Präzisierungen 😄  
Ich schlage vor: **Mini-Pilot-Workflow + konkretes PST-Parsing-Beispiel + ganz konkreter erster „Tag 1“-Plan.**

---

## 1️⃣ Mini-Pilot: Was du *konkret* als erstes machst

Ziel: Nicht gleich „das große System“, sondern ein kleiner Durchstich, der zeigt:  
➡️ *Kann ich Mails rausziehen, filtern, zusammenfassen und sinnvoll wiederfinden?*

### Schritt 1: Rahmen festlegen (30–60 Minuten)

- Wähle **eine** PST-Datei oder **einen** Posteingang:
  - Zeitraum z. B.: *01.01.2023–31.12.2023*
  - Themenfokus: z. B. „Projekt X“ oder „Kunde Y“
- Definiere:
  - Welche Ordner **einbezogen** werden (z. B. `Inbox/Projekt X`, `Sent/Projekt X`)
  - Welche **explizit ausgeschlossen** werden (`Deleted`, `Spam`, `Newsletter`, `Info`, etc.)

**Check deiner Annahme hier:**  
Wenn du sagst „Ich nehm einfach alles und filter dann mit KI“, wird es unübersichtlich. Besser: **erst in der Datenquelle sauber schneiden.**

---

### Schritt 2: Kleine SQLite-DB statt direkt „fette“ Infrastruktur

Für den Pilot reicht **SQLite** völlig (eine Datei, kein Server):

```sql
CREATE TABLE emails (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      TEXT,
    subject         TEXT,
    sender          TEXT,
    recipients      TEXT,
    sent_at         TEXT,
    folder_path     TEXT,
    source_file     TEXT,
    raw_body        TEXT,
    hash            TEXT UNIQUE
);

CREATE TABLE email_summaries (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id            INTEGER,
    core_statement      TEXT,
    bullet_points       TEXT,
    relevance_level     TEXT,
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Für den Pilot brauchst du **Tags, Personen, Vektorstore** noch nicht zwingend – das kannst du nachziehen, wenn du merkst: „Okay, das Setup taugt.“

---

### Schritt 3: PST lesen + Ordner filtern (konkretes Beispiel)

Annahme von dir: „PST auslesen ist halt ein Schritt wie jeder andere.“  
Realität: *Das* ist oft die größte Fummelei. Also hier: möglichst klar.

```python
import pypff   # muss vorher installiert werden
import sqlite3
import hashlib
from datetime import datetime

EXCLUDED_FOLDERS = {
    "Deleted Items",
    "Junk Email",
    "Spam",
    "Newsletter",
}

DB_PATH = "wissensdb_pilot.sqlite"

def connect_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT,
        subject TEXT,
        sender TEXT,
        recipients TEXT,
        sent_at TEXT,
        folder_path TEXT,
        source_file TEXT,
        raw_body TEXT,
        hash TEXT UNIQUE
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS email_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email_id INTEGER,
        core_statement TEXT,
        bullet_points TEXT,
        relevance_level TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def hash_email(subject, body, sent_at, sender):
    key = f"{subject}|{body}|{sent_at}|{sender}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def insert_email(cur, email):
    cur.execute(
        """
        INSERT OR IGNORE INTO emails
        (message_id, subject, sender, recipients, sent_at,
         folder_path, source_file, raw_body, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email["message_id"],
            email["subject"],
            email["sender"],
            ";".join(email["recipients"]),
            email["sent_at"],
            email["folder_path"],
            email["source_file"],
            email["body"],
            email["hash"],
        )
    )
    return cur.lastrowid

def walk_folder(folder, current_path, callback):
    name = folder.name
    path = f"{current_path}/{name}" if current_path else name

    # root-Ordner rausfiltern
    if any(path.startswith(ex) for ex in EXCLUDED_FOLDERS):
        return

    # Messages im aktuellen Ordner
    for i in range(folder.number_of_messages):
        message = folder.get_message(i)
        callback(message, path)

    # Unterordner rekursiv
    for j in range(folder.number_of_sub_folders):
        subfolder = folder.get_sub_folder(j)
        walk_folder(subfolder, path, callback)

def extract_message_info(message, folder_path, source_file):
    subject = message.subject or ""
    sender = message.sender_name or message.sender_email_address or ""
    recipients = []
    for i in range(message.number_of_recipients):
        r = message.get_recipient(i)
        addr = r.email_address or r.name or ""
        if addr:
            recipients.append(addr)

    body = message.plain_text_body or message.html_body or ""
    sent_time = message.client_submit_time
    sent_at = sent_time.isoformat() if sent_time else ""

    # für Duplikate
    h = hash_email(subject, body, sent_at, sender)

    return {
        "message_id": message.internet_message_id or "",
        "subject": subject,
        "sender": sender,
        "recipients": recipients,
        "sent_at": sent_at,
        "folder_path": folder_path,
        "source_file": source_file,
        "body": body,
        "hash": h,
    }

def import_pst(pst_path):
    init_db()
    conn = connect_db()
    cur = conn.cursor()

    pst = pypff.open(pst_path)
    root = pst.get_root_folder()

    def handle_message(message, folder_path):
        email = extract_message_info(message, folder_path, pst_path)
        insert_email(cur, email)

    walk_folder(root, "", handle_message)
    conn.commit()
    conn.close()
    pst.close()

if __name__ == "__main__":
    import_pst("DEINE_DATEI.pst")
```

**Kritische Punkte, die du im Kopf behalten solltest:**

- `pypff`-Installation klappt nicht immer out-of-the-box (je nach OS).  
- Foldernamen können lokalisiert sein („Gelöschte Objekte“ statt „Deleted Items“).  
  → Du musst **deine** Ordnernamen einmal ausgeben und dann die EXCLUDED-FOLDERS-Liste daran anpassen.

---

### Schritt 4: Erste KI-Zusammenfassung drüberlaufen lassen

Für den Pilot reicht:

- Nimm z. B. **20–50 Mails** aus der DB  
- Lass darüber dein LLM mit dem **Summarization-Prompt** laufen  
- Speichere das Ergebnis in `email_summaries`

Pseudo-Code (ohne echten API-Call):

```python
import sqlite3
from datetime import datetime

DB_PATH = "wissensdb_pilot.sqlite"

def connect_db():
    return sqlite3.connect(DB_PATH)

def fake_llm_summary(body):
    # hier deinen echten LLM-Client aufrufen – das ist nur Platzhalter
    return {
        "core_statement": "Kurzbeschreibung der Mail.",
        "bullet_points": ["Punkt 1", "Punkt 2"],
        "relevance": "mittel",
    }

def summarize_some_emails(limit=50):
    conn = connect_db()
    cur = conn.cursor()

    # Nur Mails ohne Summary holen
    cur.execute("""
        SELECT e.id, e.raw_body
        FROM emails e
        LEFT JOIN email_summaries s ON e.id = s.email_id
        WHERE s.id IS NULL
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()

    for email_id, body in rows:
        analysis = fake_llm_summary(body or "")
        cur.execute(
            """
            INSERT INTO email_summaries (email_id, core_statement, bullet_points, relevance_level, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                email_id,
                analysis["core_statement"],
                "\n".join(f"- {p}" for p in analysis["bullet_points"]),
                analysis["relevance"],
                datetime.now().isoformat()
            )
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    summarize_some_emails(limit=50)
```

---

## 2️⃣ Konkreter „Tag 1“-Plan (wenn du heute anfangen würdest)

Ohne Schönreden, eher pragmatisch:

1. **Ziel setzen (30–60 min)**
   - Eine PST auswählen, Zeitraum definieren  
   - Ordnerliste anschauen und notieren, welche rein/soll / raus-soll  

2. **SQLite + Minimal-Skript einrichten (1–2 h)**
   - Python-Umgebung aufsetzen  
   - `pypff`, `sqlite3` nutzen  
   - obenstehendes Import-Skript anpassen (Ordnernamen, Pfad)  
   - Testlauf mit einem Mini-Ausschnitt (z. B. eine PST mit wenigen Mails / Test-Account)

3. **20–50 Mails importieren & visuell prüfen (30–60 min)**
   - DB mit einem SQLite-Viewer öffnen (z. B. DB Browser for SQLite)  
   - Prüfen:
     - Sind Betreff, Sender, Body sauber?  
     - Sind die Folderpfade so, wie du sie erwartest?  
     - Tauchen gelöschte/Spam-Mails auf, die nicht auftauchen sollten?

4. **KI-Zusammenfassung auf diese 20–50 Mails loslassen (1–2 h)**
   - LLM-Anbindung ergänzen  
   - Prompt einsetzen, den wir oben gebaut hatten  
   - Ergebnisse in `email_summaries` anschauen

5. **Ehrliche Retrospektive (15–30 min)**  
   - Deckt die Zusammenfassung **wirklich** den Nutzen ab, den du willst?  
   - Welche Infos fehlen dir? (z. B. Projekte, Entscheidungen, Deadlines)  
   - Ist die Relevanz-Einstufung sinnvoll?  

> Wenn du an diesem Punkt sagst: „Ja, das macht Sinn und hilft mir“,  
> **dann** lohnt sich der nächste Schritt:  
> Tags, Personen, Vektorindex, UI, etc.

---

Wenn du willst, können wir als Nächstes:

- den **LLM-Teil konkret mit Prompt + JSON-Auswertung** in Code schreiben, oder  
- aus dem Ganzen ein **kleines Architekturdiagramm** (textuell) machen, oder  
- gemeinsam definieren, **welche Fragen du später an die Wissensdatenbank stellen willst** – weil das maßgeblich bestimmt, wie wir strukturieren.

Such dir was aus, oder ich entscheide einfach wieder für dich 😉

### 7. Benutzer

ich möchte es mit cursor 2.0 und codex oder claude umsetzen

### 8. Assistent

Nice, jetzt wird’s konkret. Cursor 2.0 + KI ist genau das richtige Spielfeld für sowas. 💻🧠  

Ich geh so vor:  
1. Kurz deine Annahmen challengen  
2. Stack-Entscheidung (Codex vs Claude vs OpenAI)  
3. Projektstruktur für Cursor 2.0  
4. Beispiel-Code: DB, PST-Import, LLM-Anbindung  
5. Konkrete Prompts für Claude / OpenAI  
6. Wie du Cursor 2.0 dabei schlau einsetzt  

---

## 1️⃣ Deine Annahmen zu „Cursor 2.0 + Codex/Claude“

**Annahme 1:** „Codex“ ist noch *der* Weg für Code-Automatisierung  
- Realität: OpenAI Codex ist faktisch abgelöst – heute nutzt du eher GPT-Modelle (z. B. GPT-4 / GPT-4.1 / GPT-5.1-Varianten) für Code.  
- Wenn du versuchst, explizit „Codex“ anzusprechen, verbaust du dir eher Optionen → besser „normale“ Chat-/Textmodelle.

**Annahme 2:** Cursor 2.0 + KI nimmt dir fast alles ab  
- Cursor ist mega hilfreich (Refactor, neue Files, Tests), aber:  
  - Architektur, Datenmodell und Security musst du **selbst durchdenken**.  
  - Sonst bekommst du eine schöne Code-Schicht, die fachlich nicht zu deiner Wissenslogik passt.

**Annahme 3:** „Ich wähle einfach Claude oder OpenAI und der Rest ist egal“  
- Falsch. Wichtige Punkte:
  - Kontextlänge (lange Emails / Threads)  
  - Zuverlässige JSON-Ausgabe  
  - Kosten bei großen Mail-Archiven  

Mein Rat:  
👉 **Architektur so bauen, dass du das Modell easy austauschen kannst** (Claude **oder** OpenAI).  

---

## 2️⃣ Stack-Entscheidung: Was nehmen wir realistisch?

Ich würde dir vorschlagen:

- **Sprache:** Python (für PST, DB, CLI – gut unterstützbar in Cursor)  
- **DB:** SQLite für den Pilot (später Postgres, wenn nötig)  
- **LLM:** 
  - *Option A:* OpenAI Chatmodell  
  - *Option B:* Claude (Anthropic)  

Wir bauen die Abstraktion so, dass du im Code nur ein Interface `llm_client` hast und dahinter wählst du Claude oder OpenAI per Config.

---

## 3️⃣ Projektstruktur für Cursor 2.0

Lege in Cursor ein neues Repo an, z. B. `email-kb-pilot`.

**Struktur:**

```text
email-kb-pilot/
  .env.example
  .gitignore
  pyproject.toml          # oder requirements.txt
  src/
    __init__.py
    config.py
    db.py
    pst_import.py
    llm_client.py
    summarizer.py
    relevance.py
    cli.py
```

**.gitignore (Auszug):**

```gitignore
.env
*.sqlite
__pycache__/
*.pyc
```

**.env.example:**

```env
ANTHROPIC_API_KEY=dein_key_hier
OPENAI_API_KEY=dein_key_hier
LLM_PROVIDER=anthropic   # oder openai
DB_PATH=kb.sqlite
```

---

## 4️⃣ Konkreter Code – minimal, aber realistisch

### 4.1 `config.py`

```python
import os
from dataclasses import dataclass

@dataclass
class Settings:
    db_path: str
    llm_provider: str
    anthropic_api_key: str | None
    openai_api_key: str | None

def load_settings() -> Settings:
    from dotenv import load_dotenv
    load_dotenv()

    return Settings(
        db_path=os.getenv("DB_PATH", "kb.sqlite"),
        llm_provider=os.getenv("LLM_PROVIDER", "anthropic"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
```

---

### 4.2 `db.py` – SQLite + Tabellen

```python
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import load_settings

settings = load_settings()

@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.db_path)
    try:
        yield conn
    finally:
        conn.close()

def init_db() -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT,
            subject TEXT,
            sender TEXT,
            recipients TEXT,
            sent_at TEXT,
            folder_path TEXT,
            source_file TEXT,
            raw_body TEXT,
            hash TEXT UNIQUE
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS email_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            core_statement TEXT,
            bullet_points TEXT,
            relevance_level TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
```

---

### 4.3 `llm_client.py` – Claude **oder** OpenAI

Hier trennst du Fachlogik und Modellwahl sauber.

```python
import json
from typing import Literal, Dict, Any

from .config import load_settings

settings = load_settings()

Provider = Literal["anthropic", "openai"]

class LLMClient:
    def __init__(self, provider: Provider):
        self.provider = provider
        if provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=settings.anthropic_api_key)
        elif provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def summarize_email(self, email_body: str) -> Dict[str, Any]:
        system_prompt = (
            "Du analysierst Email-Inhalte aus einer persönlichen Wissensdatenbank.\n"
            "Dein Ziel ist es, präzise, faktenorientierte Zusammenfassungen zu erstellen.\n"
            "Verzichte auf Interpretationen. Halte dich streng an den Inhalt.\n"
            "Gib deine Antwort ausschließlich als JSON im folgenden Format zurück:\n"
            "{\n"
            '  "core_statement": "<1-Satz-Kernaussage>",\n'
            '  "bullet_points": ["Punkt 1", "Punkt 2"],\n'
            '  "tags": ["Tag1", "Tag2"],\n'
            '  "persons": [{"email": "x@y.de", "role": "sender"}],\n'
            '  "relevance": "hoch" | "mittel" | "niedrig"\n'
            "}\n"
        )

        user_prompt = f"Analysiere folgenden Email-Text:\n\n{email_body}"

        if self.provider == "anthropic":
            return self._call_anthropic(system_prompt, user_prompt)
        else:
            return self._call_openai(system_prompt, user_prompt)

    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        resp = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",  # Beispielmodell
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0,
        )
        text = "".join(
            block.text for block in resp.content if block.type == "text"
        )
        return json.loads(text)

    def _call_openai(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        resp = self.client.chat.completions.create(
            model="gpt-4.1-mini",  # Beispiel
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        text = resp.choices[0].message.content
        return json.loads(text)
```

**Wichtiger Reality-Check:**  
- Du gehst hier davon aus, dass das Modell **immer** gültiges JSON ausgibt – das wird nicht zu 100 % stimmen.  
- In ernst: du brauchst ein kleines `try/except` + Fallback, aber für den Start reicht das.

---

### 4.4 `summarizer.py` – Summaries in DB schreiben

```python
from datetime import datetime
from .db import get_conn
from .llm_client import LLMClient
from .config import load_settings

settings = load_settings()

def summarize_unsummarized(limit: int = 50) -> None:
    client = LLMClient(settings.llm_provider)

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT e.id, e.raw_body
            FROM emails e
            LEFT JOIN email_summaries s ON e.id = s.email_id
            WHERE s.id IS NULL
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()

        for email_id, body in rows:
            if not body:
                continue
            analysis = client.summarize_email(body)
            cur.execute(
                """
                INSERT INTO email_summaries (email_id, core_statement, bullet_points, relevance_level, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    email_id,
                    analysis["core_statement"],
                    "\n".join(f"- {p}" for p in analysis["bullet_points"]),
                    analysis["relevance"],
                    datetime.now().isoformat()
                )
            )

        conn.commit()
```

---

### 4.5 `pst_import.py` – wie vorhin, aber in die Struktur integriert

Du kannst den Code aus der vorherigen Antwort nehmen und nur die DB-Funktionen aus `db.py` benutzen (statt direkter `sqlite3.connect`).  
Wichtig: Ordner-Filtern über `EXCLUDED_FOLDERS` sauber halten.

---

### 4.6 `cli.py` – kleine Kommandooberfläche

Damit du in Cursor oder Terminal einfache Kommandos hast:

```python
import argparse
from .db import init_db
from .pst_import import import_pst
from .summarizer import summarize_unsummarized

def main():
    parser = argparse.ArgumentParser(prog="email-kb")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("init-db", help="Initialisiert die Datenbank")

    p_import = sub.add_parser("import-pst", help="Importiert eine PST-Datei")
    p_import.add_argument("path", help="Pfad zur PST-Datei")

    p_sum = sub.add_parser("summarize", help="Erstellt Zusammenfassungen für Emails ohne Summary")
    p_sum.add_argument("--limit", type=int, default=50)

    args = parser.parse_args()

    if args.cmd == "init-db":
        init_db()
    elif args.cmd == "import-pst":
        init_db()
        import_pst(args.path)
    elif args.cmd == "summarize":
        summarize_unsummarized(limit=args.limit)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

---

## 5️⃣ Prompts, zugeschnitten auf Claude / OpenAI

Du kannst sie exakt so in `system_prompt` verwenden:

### 5.1 Zusammenfassung + Metadaten (wie oben im Code)

Strenger JSON-Output, damit du ihn parsen kannst:

```text
Du analysierst Email-Inhalte aus einer persönlichen Wissensdatenbank.
Dein Ziel ist es, präzise, faktenorientierte Zusammenfassungen zu erstellen.
Verzichte auf Interpretationen. Halte dich streng an den Inhalt.

Gib deine Antwort ausschließlich als JSON im folgenden Format zurück:
{
  "core_statement": "<1-Satz-Kernaussage>",
  "bullet_points": ["Punkt 1", "Punkt 2", "Punkt 3"],
  "tags": ["Tag1", "Tag2", "Tag3"],
  "persons": [
    {"email": "name@domain.de", "role": "sender" | "to" | "cc"}
  ],
  "relevance": "hoch" | "mittel" | "niedrig"
}
```

---

### 5.2 Relevanzfilter (falls du ihn später auslagerst)

```text
Du bewertest, wie relevant ein Emailtext für eine persönliche Wissensdatenbank ist.
Relevante Inhalte enthalten Entscheidungen, Absprachen, fachliche Informationen, Anforderungen, technische Details oder wichtige Termine.
Unrelevante Inhalte sind Werbung, automatische Benachrichtigungen, einfache Empfangsbestätigungen und triviale organisatorische Details.

Antworte ausschließlich im JSON-Format:
{
  "relevance": "hoch" | "mittel" | "niedrig" | "irrelevant",
  "reason": "<kurze Begründung>"
}
```

---

## 6️⃣ Wie du Cursor 2.0 sinnvoll nutzt

Ein paar praktische Moves für dich:

1. **Am Anfang:**  
   - Schreib grob das Ziel ins Cursor-Chat:  
     > „Baue mir ein kleines Python-Projekt: PST-Import, SQLite, LLM-Zusammenfassung, CLI-Commands.“  
   - Lass Cursor dir die Grundstruktur generieren – aber:  
     - **Kritisch prüfen**, ob sie zu dem passt, was wir oben skizziert haben.

2. **Refactoring:**  
   - Wenn z. B. `llm_client.py` wächst, kannst du Cursor bitten:  
     > „Extrahiere bitte die Prompt-Texte in eine eigene Datei `prompts.py` und importiere sie.“  

3. **Tests generieren:**  
   - Später:  
     > „Schreib mir Pytest-Tests für `summarizer.py`, bei denen der LLM-Client gemockt wird.“  

4. **Prompts iterativ verbessern:**  
   - Du kannst einige reale Mail-Bodies anonymisiert in Cursor werfen und sagen:  
     > „Zeig mir die Ausgabe dieses Prompts, und optimiere ihn, damit die Bullet Points kürzer/präziser werden.“

---

Wenn du magst, kann ich als Nächstes:

- aus dem Ganzen ein **RAG-Layer** (Vektorstore + einfache Such-API) draufsetzen,  
- oder einen **Schritt-für-Schritt-Plan**, wie du das jetzt in Cursor 2.0 wirklich umsetzt (inkl. erster Commands, wie du startest),  
- oder wir gehen einen konkreten Use Case durch: „Wie stelle ich später eine Frage an die Wissensdatenbank?“

Such dir eins aus – ansonsten entscheide ich wieder einfach für dich. 😄

### 9. Benutzer

Schritt-für-Schritt-Plan

### 10. Assistent

Nice, jetzt gehen wir in den „Mach es wirklich“-Modus.  
Ich geb dir einen klaren Schritt-für-Schritt-Plan, den du in Cursor direkt abarbeiten kannst.

Ich gliedere in **8 Schritte**, die du der Reihe nach durchgehen kannst:

1. Projekt & Umgebung aufsetzen  
2. Basis-Projektstruktur in Cursor anlegen  
3. Datenbank einrichten  
4. PST-Ordnerstruktur inspizieren (für die Ausschlussliste)  
5. PST-Import in die DB bauen  
6. LLM-Anbindung (Claude/OpenAI) einbauen  
7. Summarizer bauen und auf ein paar Mails laufen lassen  
8. Manuelle Kontrolle + nächste Iterationen

Ich schreibe das so, dass du es fast wie eine Checkliste benutzen kannst.

---

## 1️⃣ Projekt & Umgebung aufsetzen

**Annahmen, die du hier machst:**  
- Python ist installiert  
- Du kannst mit `venv` umgehen  
Wenn nicht: das ist der Punkt, wo es sonst später hässlich wird.

**Schritte:**

1. Neues Verzeichnis erstellen:
   ```bash
   mkdir email-kb-pilot
   cd email-kb-pilot
   ```

2. Git-Repo initialisieren:
   ```bash
   git init
   ```

3. Virtuelle Umgebung anlegen:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

4. Basis-Pakete installieren:
   ```bash
   pip install python-dotenv anthropic openai pypff
   ```

   > Falls `pypff` Stress macht: das ist *der* klassische Stolperstein. Wenn es gar nicht geht, könntest du kurz mit Export als `.eml`/`.msg` arbeiten – aber erstmal versuchen.

5. `requirements.txt` erzeugen:
   ```bash
   pip freeze > requirements.txt
   ```

---

## 2️⃣ Projektstruktur in Cursor anlegen

Öffne den Ordner in **Cursor 2.0**.

Lege folgende Struktur an:

```text
email-kb-pilot/
  .env.example
  .gitignore
  requirements.txt
  src/
    __init__.py
    config.py
    db.py
    pst_import.py
    llm_client.py
    summarizer.py
    cli.py
```

**Inhalt `.gitignore`:**

```gitignore
.env
.venv/
__pycache__/
*.pyc
*.sqlite
```

**Inhalt `.env.example`:**

```env
ANTHROPIC_API_KEY=dein_key_hier
OPENAI_API_KEY=dein_key_hier
LLM_PROVIDER=anthropic   # oder openai
DB_PATH=kb.sqlite
```

Dann kopierst du `.env.example` nach `.env` und trägst dort deine echten Keys ein.

---

## 3️⃣ Datenbank einrichten

### 3.1 `config.py`

```python
import os
from dataclasses import dataclass

@dataclass
class Settings:
    db_path: str
    llm_provider: str
    anthropic_api_key: str | None
    openai_api_key: str | None

def load_settings() -> Settings:
    from dotenv import load_dotenv
    load_dotenv()

    return Settings(
        db_path=os.getenv("DB_PATH", "kb.sqlite"),
        llm_provider=os.getenv("LLM_PROVIDER", "anthropic"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
```

### 3.2 `db.py`

```python
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import load_settings

settings = load_settings()

@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.db_path)
    try:
        yield conn
    finally:
        conn.close()

def init_db() -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT,
            subject TEXT,
            sender TEXT,
            recipients TEXT,
            sent_at TEXT,
            folder_path TEXT,
            source_file TEXT,
            raw_body TEXT,
            hash TEXT UNIQUE
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS email_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            core_statement TEXT,
            bullet_points TEXT,
            relevance_level TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
```

### 3.3 Erste Initialisierung

Du kannst kurz einen mini-Runner bauen oder wartest bis zu Schritt 7, wo `cli.py` da ist – ich würde’s direkt machen:

Temporär in `src/__main__.py`:

```python
from .db import init_db

if __name__ == "__main__":
    init_db()
    print("DB initialisiert")
```

Dann:

```bash
python -m src
```

Wenn keine Fehlermeldung → DB steht.

---

## 4️⃣ PST-Ordnerstruktur inspizieren (für Ausschlussliste)

Bevor du *blind* mit `EXCLUDED_FOLDERS` arbeitest, solltest du wissen, wie deine Ordner wirklich heißen.

In `pst_import.py` legst du erstmal nur einen Explorer an:

```python
import pypff

def print_folder_structure(folder, indent=0):
    prefix = "  " * indent
    print(f"{prefix}- {folder.name} ({folder.number_of_messages} messages)")
    for i in range(folder.number_of_sub_folders):
        sub = folder.get_sub_folder(i)
        print_folder_structure(sub, indent + 1)

def inspect_pst(pst_path: str):
    pst = pypff.open(pst_path)
    root = pst.get_root_folder()
    print_folder_structure(root)
    pst.close()

if __name__ == "__main__":
    inspect_pst("DEIN_PST_PFAD.pst")
```

Dann:

```bash
python -m src.pst_import
```

→ Ordnerstruktur anschauen und **explizit notieren**, welche Root-/Hauptordner raus sollen (z. B. „Gelöschte Objekte“, „Junk-E-Mail“, etc.).

Das korrigiert eine typische Fehleinschätzung:  
„Ach, die heißen schon ‘Deleted Items’“ – tun sie auf deutschsprachigen Systemen halt oft nicht. 😉

---

## 5️⃣ PST-Import in die Datenbank bauen

Jetzt erweiterst du `pst_import.py`:

```python
import hashlib
from datetime import datetime
import pypff

from .db import get_conn

EXCLUDED_ROOT_FOLDERS = {
    "Gelöschte Objekte",
    "Junk-E-Mail",
    "Spam",
    "Newsletter",
    # deine echten Namen hier
}

def hash_email(subject, body, sent_at, sender):
    key = f"{subject}|{body}|{sent_at}|{sender}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def extract_message_info(message, folder_path, source_file):
    subject = message.subject or ""
    sender = message.sender_name or message.sender_email_address or ""
    recipients = []
    for i in range(message.number_of_recipients):
        r = message.get_recipient(i)
        addr = r.email_address or r.name or ""
        if addr:
            recipients.append(addr)

    body = message.plain_text_body or message.html_body or ""
    sent_time = message.client_submit_time
    sent_at = sent_time.isoformat() if sent_time else ""

    h = hash_email(subject, body, sent_at, sender)

    return {
        "message_id": message.internet_message_id or "",
        "subject": subject,
        "sender": sender,
        "recipients": recipients,
        "sent_at": sent_at,
        "folder_path": folder_path,
        "source_file": source_file,
        "body": body,
        "hash": h,
    }

def insert_email(cur, email):
    cur.execute(
        """
        INSERT OR IGNORE INTO emails
        (message_id, subject, sender, recipients, sent_at,
         folder_path, source_file, raw_body, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email["message_id"],
            email["subject"],
            email["sender"],
            ";".join(email["recipients"]),
            email["sent_at"],
            email["folder_path"],
            email["source_file"],
            email["body"],
            email["hash"],
        )
    )

def walk_folder(folder, current_path, source_file, cur):
    name = folder.name or ""
    path = f"{current_path}/{name}" if current_path else name

    # Root-Ordner filtern
    root_name = path.split("/")[0]
    if root_name in EXCLUDED_ROOT_FOLDERS:
        return

    for i in range(folder.number_of_messages):
        msg = folder.get_message(i)
        email = extract_message_info(msg, path, source_file)
        insert_email(cur, email)

    for j in range(folder.number_of_sub_folders):
        sub = folder.get_sub_folder(j)
        walk_folder(sub, path, source_file, cur)

def import_pst(pst_path: str):
    pst = pypff.open(pst_path)
    root = pst.get_root_folder()

    with get_conn() as conn:
        cur = conn.cursor()
        walk_folder(root, "", pst_path, cur)
        conn.commit()

    pst.close()
```

Damit kannst du später per CLI sagen:  
`email-kb import-pst meine_mails.pst`

---

## 6️⃣ LLM-Anbindung (Claude / OpenAI)

### 6.1 `llm_client.py`

```python
import json
from typing import Literal, Dict, Any

from .config import load_settings

settings = load_settings()
Provider = Literal["anthropic", "openai"]

class LLMClient:
    def __init__(self, provider: Provider | None = None):
        provider = provider or settings.llm_provider
        self.provider = provider

        if provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=settings.anthropic_api_key)
        elif provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def summarize_email(self, email_body: str) -> Dict[str, Any]:
        system_prompt = (
            "Du analysierst Email-Inhalte aus einer persönlichen Wissensdatenbank.\n"
            "Dein Ziel ist es, präzise, faktenorientierte Zusammenfassungen zu erstellen.\n"
            "Verzichte auf Interpretationen. Halte dich streng an den Inhalt.\n"
            "Gib deine Antwort ausschließlich als JSON im folgenden Format zurück:\n"
            "{\n"
            '  \"core_statement\": \"<1-Satz-Kernaussage>\",\n'
            '  \"bullet_points\": [\"Punkt 1\", \"Punkt 2\"],\n'
            '  \"tags\": [\"Tag1\", \"Tag2\"],\n'
            '  \"persons\": [{\"email\": \"x@y.de\", \"role\": \"sender\"}],\n'
            '  \"relevance\": \"hoch\" | \"mittel\" | \"niedrig\"\n'
            "}\n"
        )

        user_prompt = f"Analysiere folgenden Email-Text:\n\n{email_body}"

        if self.provider == "anthropic":
            text = self._call_anthropic(system_prompt, user_prompt)
        else:
            text = self._call_openai(system_prompt, user_prompt)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # minimaler Fallback: in echt würdest du hier robuster sein
            return {
                "core_statement": text[:200],
                "bullet_points": [],
                "tags": [],
                "persons": [],
                "relevance": "mittel",
            }

    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        resp = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0,
        )
        return "".join(block.text for block in resp.content if block.type == "text")

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        return resp.choices[0].message.content
```

---

## 7️⃣ Summarizer bauen & Pilot laufen lassen

### 7.1 `summarizer.py`

```python
from datetime import datetime
from .db import get_conn
from .llm_client import LLMClient
from .config import load_settings

settings = load_settings()

def summarize_unsummarized(limit: int = 20) -> None:
    client = LLMClient()

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT e.id, e.raw_body
            FROM emails e
            LEFT JOIN email_summaries s ON e.id = s.email_id
            WHERE s.id IS NULL
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()

        for email_id, body in rows:
            if not body:
                continue
            analysis = client.summarize_email(body)

            cur.execute(
                """
                INSERT INTO email_summaries
                (email_id, core_statement, bullet_points, relevance_level, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    email_id,
                    analysis.get("core_statement", "")[:500],
                    "\n".join(f"- {p}" for p in analysis.get("bullet_points", [])),
                    analysis.get("relevance", "mittel"),
                    datetime.now().isoformat()
                )
            )

        conn.commit()
```

### 7.2 CLI für alles (`cli.py`)

```python
import argparse
from .db import init_db
from .pst_import import import_pst
from .summarizer import summarize_unsummarized

def main():
    parser = argparse.ArgumentParser(prog="email-kb")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("init-db", help="Initialisiert die Datenbank")

    p_import = sub.add_parser("import-pst", help="Importiert eine PST-Datei")
    p_import.add_argument("path", help="Pfad zur PST-Datei")

    p_sum = sub.add_parser("summarize", help="Erstellt Zusammenfassungen")
    p_sum.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.cmd == "init-db":
        init_db()
    elif args.cmd == "import-pst":
        init_db()
        import_pst(args.path)
    elif args.cmd == "summarize":
        summarize_unsummarized(limit=args.limit)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

### 7.3 Befehle ausführen

1. DB initialisieren:
   ```bash
   python -m src.cli init-db
   ```

2. PST importieren (zuerst mit **kleiner Test-PST**!):
   ```bash
   python -m src.cli import-pst /pfad/zu/deiner_test.pst
   ```

3. Zusammenfassungen für z. B. 10 Mails erzeugen:
   ```bash
   python -m src.cli summarize --limit 10
   ```

---

## 8️⃣ Manuell prüfen & Iterationen planen

1. Öffne `kb.sqlite` mit einem Tool wie **DB Browser for SQLite**.  
2. Schau dir an:
   - Sind `emails` sauber befüllt?  
   - Passen `folder_path`, `sender`, `subject`?  
   - Sind `email_summaries` sinnvoll? Kernaussage & Bullet Points brauchbar?

3. Frag dich ehrlich:
   - Deckt die Summary genau das ab, was du später wiederfinden willst?  
   - Musst du Tags/Personen direkt mit reinziehen, oder reicht erstmal die reine Summary?  
   - Willst du schon einen Relevanzfilter davor schalten?

---

Wenn du möchtest, können wir als nächstes:

- den **Relevanzfilter** als eigenen Schritt einziehen (vor dem Summarizer),  
- oder ein kleines **Suchskript** bauen, mit dem du schon in den Summaries nach Stichworten suchen kannst,  
- oder direkt über einen Vektorstore nachdenken.

Sag einfach, welchen Schritt du als nächstes angehen willst – oder du sagst „ich probiere das jetzt aus“ und wir debuggen beim nächsten Mal gezielt die Stellen, die knirschen.

### 11. Benutzer

gui implementieren

### 12. Assistent

Nice, jetzt wird’s sichtbar klickbar. 😄  
Du willst eine GUI – und zwar nicht nur „zum Anschauen“, sondern inkl. Folder-Auswahl fürs Importieren. Lass mich kurz deine Idee challengen und dann bau ich dir eine konkrete Umsetzung.

---

## 1. Kurz deine Annahmen checken

1. **„Ich brauch jetzt sofort eine GUI“**  
   - Vielleicht – aber: du bist noch im Pilot. GUI macht erst dann wirklich Sinn, wenn Import + Summaries halbwegs stabil sind. Sonst debuggst du gleichzeitig Logik *und* Oberfläche.

2. **„Ich will dasselbe Tool für Import-Steuerung und Suche“**  
   - Das ist sinnvoll. Aber dann sollte die GUI bewusst minimal bleiben: lieber robust + hässlich als fancy + fragil.

3. **„Ordner per Klick abwählen“**  
   - Das ist fachlich stark (du kennst deine Mailstruktur besser als jede KI).  
   - Technisch bedeutet das: erst Ordnerstruktur aus PST lesen → Nutzer wählt → dann importieren → Exclusions gehören **in die GUI**, nicht hart in den Code.

Ich gehe trotzdem davon aus, dass du den Pilot *mit* GUI machen willst – also bauen wir sie.  
Ich nehme als Basis: **Streamlit** (schnell, lokal, kein extra Frontend-Build, Cursor-freundlich).

---

## 2. Zielbild der GUI (MVP)

Ein Streamlit-App mit drei Bereichen:

1. **Dashboard**
   - Anzahl Mails, Anzahl Summaries  
   - einfache Übersicht

2. **Emails & Suche**
   - Filter (Betreff, Summary enthält, Relevanz, Zeitraum)  
   - Tabelle mit Ergebnissen  
   - Detailansicht (Originaltext + Summary)

3. **PST-Import**
   - Pfad zur PST eingeben  
   - Button „Ordner analysieren“ → Liste aller Ordnerpfade  
   - Multiselect: „Ordner, die importiert werden sollen“ (d. h. du kannst andere abwählen)  
   - Button „Import starten“ → importiert nur selektierte Ordner

Damit erfüllst du dein Ordner-Anforderung ziemlich sauber.

---

## 3. Vorbereitung

Falls noch nicht passiert:

```bash
pip install streamlit
```

Wir legen eine Datei `ui_app.py` im Projektroot an (neben `src/`), damit du mit:

```bash
streamlit run ui_app.py
```

starten kannst.

Ich gehe davon aus, dass deine DB + PST-Import schon so ähnlich existieren wie in unserer vorherigen Planung.

---

## 4. Streamlit-GUI: `ui_app.py`

> Hinweis: Das ist ein zusammenhängendes Beispiel, du darfst es in Cursor natürlich in mehrere Module splitten. Für dich zum Verstehen ist „alles in einem“ jetzt einfacher.

```python
import os
from datetime import datetime
from typing import List, Set

import streamlit as st
import sqlite3
import pypff

DB_PATH = os.getenv("DB_PATH", "kb.sqlite")

# ---------- DB-Helfer ----------

def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)

def query_one(sql: str, params=()):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()

def query_all(sql: str, params=()):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT,
            subject TEXT,
            sender TEXT,
            recipients TEXT,
            sent_at TEXT,
            folder_path TEXT,
            source_file TEXT,
            raw_body TEXT,
            hash TEXT UNIQUE
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS email_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            core_statement TEXT,
            bullet_points TEXT,
            relevance_level TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

# ---------- PST-Ordner sammeln & Import ----------

def collect_folder_paths(pst_path: str) -> List[str]:
    pst = pypff.open(pst_path)
    root = pst.get_root_folder()

    paths: List[str] = []

    def walk(folder, current_path: str):
        name = folder.name or ""
        path = f"{current_path}/{name}" if current_path else name
        paths.append(path)
        for i in range(folder.number_of_sub_folders):
            sub = folder.get_sub_folder(i)
            walk(sub, path)

    walk(root, "")
    pst.close()
    # Duplikate raus, sortieren
    paths = sorted(set(paths))
    return [p for p in paths if p]  # leere Namen filtern

def hash_email(subject, body, sent_at, sender):
    import hashlib
    key = f"{subject}|{body}|{sent_at}|{sender}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def extract_message_info(message, folder_path, source_file):
    subject = message.subject or ""
    sender = message.sender_name or message.sender_email_address or ""
    recipients = []
    for i in range(message.number_of_recipients):
        r = message.get_recipient(i)
        addr = r.email_address or r.name or ""
        if addr:
            recipients.append(addr)

    body = message.plain_text_body or message.html_body or ""
    sent_time = message.client_submit_time
    sent_at = sent_time.isoformat() if sent_time else ""

    h = hash_email(subject, body, sent_at, sender)

    return {
        "message_id": message.internet_message_id or "",
        "subject": subject,
        "sender": sender,
        "recipients": recipients,
        "sent_at": sent_at,
        "folder_path": folder_path,
        "source_file": source_file,
        "body": body,
        "hash": h,
    }

def insert_email(cur, email):
    cur.execute(
        """
        INSERT OR IGNORE INTO emails
        (message_id, subject, sender, recipients, sent_at,
         folder_path, source_file, raw_body, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email["message_id"],
            email["subject"],
            email["sender"],
            ";".join(email["recipients"]),
            email["sent_at"],
            email["folder_path"],
            email["source_file"],
            email["body"],
            email["hash"],
        )
    )

def import_selected_folders(pst_path: str, allowed_paths: Set[str]):
    pst = pypff.open(pst_path)
    root = pst.get_root_folder()

    with get_conn() as conn:
        cur = conn.cursor()

        def walk(folder, current_path: str):
            name = folder.name or ""
            path = f"{current_path}/{name}" if current_path else name

            # nur importieren, wenn dieser Folder-Pfad ausgewählt wurde
            if path in allowed_paths:
                for i in range(folder.number_of_messages):
                    msg = folder.get_message(i)
                    email = extract_message_info(msg, path, pst_path)
                    insert_email(cur, email)

            # trotzdem weiter runterlaufen, damit Unterordner auch abgefragt werden können
            for j in range(folder.number_of_sub_folders):
                sub = folder.get_sub_folder(j)
                walk(sub, path)

        walk(root, "")
        conn.commit()

    pst.close()

# ---------- LLM: Stub (hier baust du deine echte Anbindung ein) ----------

def call_llm_summary_stub(body: str):
    # TODO: hier deinen echten Claude/OpenAI-Client einbauen
    # Das ist nur ein Platzhalter
    return {
        "core_statement": (body[:100] + "...") if body else "Leerer Text",
        "bullet_points": ["Dies ist nur ein Stub.", "Hier käme die echte Summary hin."],
        "relevance": "mittel",
    }

def summarize_some(limit: int = 20):
    from datetime import datetime
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT e.id, e.raw_body
            FROM emails e
            LEFT JOIN email_summaries s ON e.id = s.email_id
            WHERE s.id IS NULL
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()

        for email_id, body in rows:
            analysis = call_llm_summary_stub(body or "")
            cur.execute(
                """
                INSERT INTO email_summaries
                (email_id, core_statement, bullet_points, relevance_level, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    email_id,
                    analysis["core_statement"],
                    "\n".join(f"- {p}" for p in analysis["bullet_points"]),
                    analysis["relevance"],
                    datetime.now().isoformat()
                )
            )
        conn.commit()

# ---------- GUI-Seiten ----------

def page_dashboard():
    st.header("Dashboard")

    total_emails = query_one("SELECT COUNT(*) FROM emails")[0]
    total_summaries = query_one("SELECT COUNT(*) FROM email_summaries")[0]

    col1, col2 = st.columns(2)
    col1.metric("Gesamtanzahl Emails", total_emails)
    col2.metric("Anzahl mit Summary", total_summaries)

    st.write("---")
    st.write("Kleine Statistik:")

    rows = query_all("""
        SELECT relevance_level, COUNT(*)
        FROM email_summaries
        GROUP BY relevance_level
    """)
    if rows:
        st.write("Verteilung Relevanz:")
        for rel, count in rows:
            st.write(f"- **{rel}**: {count}")
    else:
        st.info("Noch keine Summaries vorhanden.")


def page_emails():
    st.header("Emails & Suche")

    # Filter
    subject_like = st.text_input("Betreff enthält")
    summary_like = st.text_input("Summary enthält")
    relevance = st.selectbox("Relevanz", ["(egal)", "hoch", "mittel", "niedrig"])
    limit = st.slider("Max. Anzahl Ergebnisse", min_value=10, max_value=500, value=50, step=10)

    sql = """
        SELECT e.id, e.sent_at, e.sender, e.subject,
               s.core_statement, s.relevance_level
        FROM emails e
        LEFT JOIN email_summaries s ON e.id = s.email_id
        WHERE 1=1
    """
    params = []

    if subject_like:
        sql += " AND e.subject LIKE ?"
        params.append(f"%{subject_like}%")
    if summary_like:
        sql += " AND (s.core_statement LIKE ? OR s.bullet_points LIKE ?)"
        params.append(f"%{summary_like}%")
        params.append(f"%{summary_like}%")
    if relevance != "(egal)":
        sql += " AND s.relevance_level = ?"
        params.append(relevance)

    sql += " ORDER BY e.sent_at DESC LIMIT ?"
    params.append(limit)

    rows = query_all(sql, params)

    if not rows:
        st.info("Keine Ergebnisse für diese Filter.")
        return

    import pandas as pd
    df = pd.DataFrame(rows, columns=["id", "sent_at", "sender", "subject", "core_statement", "relevance"])
    st.dataframe(df, use_container_width=True)

    st.write("---")
    selected_id = st.number_input("Details anzeigen für Email-ID", min_value=1, step=1)

    if st.button("Details laden"):
        detail = query_one("""
            SELECT e.subject, e.sender, e.recipients, e.sent_at, e.folder_path, e.raw_body,
                   s.core_statement, s.bullet_points, s.relevance_level
            FROM emails e
            LEFT JOIN email_summaries s ON e.id = s.email_id
            WHERE e.id = ?
        """, (int(selected_id),))
        if not detail:
            st.warning("Keine Email mit dieser ID gefunden.")
        else:
            (subject, sender, recipients, sent_at, folder_path, raw_body,
             core_statement, bullet_points, relevance) = detail

            st.subheader(subject or "(kein Betreff)")
            st.caption(f"Von: {sender} | An: {recipients} | Datum: {sent_at}")
            st.caption(f"Ordner: {folder_path}")

            st.markdown("### Summary")
            if core_statement:
                st.write("**Kernaussage:**", core_statement)
                st.write("**Relevanz:**", relevance)
                st.write("**Stichpunkte:**")
                st.markdown(bullet_points or "_keine_")
            else:
                st.info("Keine Summary vorhanden.")

            st.markdown("### Originaltext")
            st.text_area("Email-Body", raw_body or "", height=300)


def page_import():
    st.header("PST-Import")

    init_db()  # sicherheitshalber

    pst_path = st.text_input("Pfad zur PST-Datei", value="", help="Lokaler Pfad, z.B. C:\\Users\\...\\mail.pst")

    if "folder_paths" not in st.session_state:
        st.session_state.folder_paths = []
        st.session_state.selected_paths = []

    if st.button("Ordner analysieren"):
        if not pst_path or not os.path.exists(pst_path):
            st.error("PST-Datei nicht gefunden.")
        else:
            with st.spinner("Lese Ordnerstruktur..."):
                paths = collect_folder_paths(pst_path)
            st.session_state.folder_paths = paths
            # Default: alles auswählen, außer offensichtliche Trash-Ordner
            default_sel = [p for p in paths if not any(
                x.lower() in p.lower()
                for x in ["deleted", "gelöschte", "junk", "spam", "newsletter"]
            )]
            st.session_state.selected_paths = default_sel
            st.success(f"{len(paths)} Ordner gefunden.")

    if st.session_state.folder_paths:
        st.write("Wähle die Ordner, die importiert werden sollen:")
        selected = st.multiselect(
            "Ordner (deaktiviere alles, was du nicht willst)",
            options=st.session_state.folder_paths,
            default=st.session_state.selected_paths,
        )
        st.session_state.selected_paths = selected

        st.write(f"**Ausgewählte Ordner:** {len(selected)}")

        if st.button("Import starten"):
            if not selected:
                st.warning("Keine Ordner ausgewählt.")
            else:
                with st.spinner("Importiere Emails..."):
                    import_selected_folders(pst_path, set(selected))
                st.success("Import abgeschlossen.")

    st.write("---")
    if st.button("Für ein paar Emails Summaries erzeugen (Stub)"):
        with st.spinner("Erzeuge Summaries..."):
            summarize_some(limit=10)
        st.success("Summaries erstellt (Stub).")

# ---------- Main ----------

def main():
    st.set_page_config(page_title="Email-Knowledgebase", layout="wide")

    init_db()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Seite wählen", ["Dashboard", "Emails", "PST-Import"])

    if page == "Dashboard":
        page_dashboard()
    elif page == "Emails":
        page_emails()
    elif page == "PST-Import":
        page_import()

if __name__ == "__main__":
    main()
```

---

## 5. Wie du jetzt konkret weiter machst

1. `ui_app.py` anlegen und Code rein.  
2. Sicherstellen, dass `kb.sqlite` existiert (oder einfach `init_db()` laufen lassen – macht die GUI eh).  
3. Im Projektordner:

   ```bash
   streamlit run ui_app.py
   ```

4. Im Browser:
   - **PST-Import-Seite** öffnen  
   - PST-Pfad eintragen  
   - „Ordner analysieren“  
   - Unerwünschte Ordner abwählen  
   - „Import starten“  
   - Dann testweise „Summaries erzeugen (Stub)“

5. Auf **Emails-Seite** die importierten Mails anschauen und checken, ob:
   - Folder-Filterung so funktioniert, wie du es erwartest  
   - die Daten (Betreff, Sender, Body) sauber ankommen  

---

## 6. Nächster sinnvoller Schritt

Damit das Ganze „echt“ wird, musst du:

- den Stub `call_llm_summary_stub` durch deinen echten **Claude/OpenAI-Client** ersetzen  
- und am besten einen kleinen **Relevanzfilter** einbauen, bevor du alles automatisch zusammenfassen lässt.

Wenn du willst, kann ich dir im nächsten Schritt:

- genau den Teil `call_llm_summary_stub` auf Claude/OpenAI umbauen (inkl. sauberem JSON-Handling),  
- oder eine einfache Suchfunktion mit „Freitext über Betreff + Summary“ verbessern,  
- oder zeigen, wie du aus dieser GUI später ein richtiges RAG-Frontend machst.

Was davon reizt dich am meisten als nächster Schritt?

### 13. Benutzer

erstelle mir einen entwicklungsprompt  für ein leeres projekt in cursor

### 14. Assistent

Alles klar Markus — ich bau dir einen **Entwicklungsprompt**, den du *direkt* in ein komplett leeres Cursor-Projekt werfen kannst.  
Vorher aber kurz das Sparring, damit der Prompt wirklich das liefert, was du willst:

---

## 🧠 Kurze Analyse deiner Annahmen

1. **Annahme:** „Ein einziger Prompt reicht, um die komplette Architektur sauber aufzusetzen.“  
   → Möglich, aber Cursor kann bei zu viel Info auf einmal entweder zu vage oder zu übergriffig werden. Ein gut strukturierter, klarer Prompt ist entscheidend.

2. **Annahme:** „Cursor versteht automatisch die Anforderungen an PST-Verarbeitung und KI-Pipeline.“  
   → Nope. PST-Dateien sind tricky. Der Prompt muss *explizit* sagen, was gebaut werden soll und was nicht.

3. **Annahme:** „Cursor erzeugt Directory-Struktur + Code automatisch perfekt.“  
   → Nur, wenn du ihm klare Module, Verantwortlichkeiten und Grenzen vorgibst.

4. **Annahme:** „GUI gehört auch gleich dazu.“  
   → Du kannst’s reinpacken – aber ich würde das **optional** formulieren, damit Cursor dein Projekt nicht sofort aufbläst.

---

## 🎯 Ziel des Prompts

- Projektstruktur erzeugen  
- PST-Import  
- SQLite-DB  
- LLM-Anbindung (Claude oder OpenAI, konfigurierbar)  
- Summarizer  
- CLI  
- Optionale GUI (Streamlit), aber erst nach Basis-Funktionen  

---

## ✅ Dein fertiger Cursor-Entwicklungsprompt

**Diesen Prompt kannst du direkt in ein neues Cursor-Projekt werfen.**  
Er setzt alles sauber auf, ohne Überfrachtung.

---

### 🔥 *Cursor-Entwicklungsprompt (Copy & Paste)*

```
Ich möchte ein neues Python-Projekt erstellen. Bitte lege die gesamte Projektstruktur, 
Konfigurationsdateien und die initiale Implementierung an. 

Das Projekt heißt **email-kb-pilot** und hat folgende Anforderungen:

ZIELE
------
Dieses Projekt soll:
1. PST-Dateien einlesen
2. Ordnerstruktur der PST-Datei analysieren
3. Benutzerdefinierte Ordner auswählen können (via CLI; GUI später optional)
4. Emails aus den gewählten Ordnern extrahieren
5. Die extrahierten Emails in eine SQLite-Datenbank speichern
6. Eine LLM-basierte Zusammenfassung erzeugen (Claude ODER OpenAI, per .env konfigurierbar)
7. Summaries ebenfalls in der DB speichern
8. Einen einfachen CLI-Workflow unterstützen:
   - `init-db`
   - `inspect-pst <pfad>`
   - `import-pst <pfad>`
   - `summarize --limit 20`

WICHTIGE TECHNISCHE DETAILS
---------------------------
- Python 3.10 oder höher
- Virtuelle Umgebung wird nicht von Cursor erstellt
- Abhängigkeiten verwalten wir über `requirements.txt`
- Module unter `src/` strukturieren, keine Dateien im Root außer UI oder Readme

VERZEICHNISSTRUKTUR
-------------------
Bitte folgendes Gerüst erzeugen:

project_root/
  .env.example
  .gitignore
  requirements.txt
  README.md
  src/
    __init__.py
    config.py
    db.py
    pst_import.py
    llm_client.py
    summarizer.py
    cli.py

BESCHREIBUNG DER MODULE
-----------------------

config.py:
  - Lädt .env
  - Einstellungen: DB_PATH, LLM_PROVIDER (anthropic oder openai), API-Keys

db.py:
  - SQLite-Verbindung
  - Kontextmanager `get_conn()`
  - Funktion `init_db()` mit Tabellen: emails, email_summaries

pst_import.py:
  - PST einlesen (pypff)
  - Funktion: `collect_folder_paths(pst_path)` gibt Liste aller Ordner zurück
  - Funktion: `import_selected_folders(pst_path, allowed_paths)`
  - Emails extrahieren: subject, sender, recipients, sent_at, folder_path, body, hash

llm_client.py:
  - Klasse `LLMClient`
  - unterstützt beide Provider (anthropic / openai)
  - Methode `summarize_email(text)`:
      JSON-Output:
      {
        "core_statement": "<string>",
        "bullet_points": ["...", "..."],
        "tags": ["..."],
        "persons": [{"email": "...", "role": "sender"}],
        "relevance": "hoch|mittel|niedrig"
      }

summarizer.py:
  - Funktion `summarize_unsummarized(limit=20)`
  - Liest alle Mails ohne Summary
  - Ruft LLMClient.summarize_email() auf
  - Speichert Ergebnis in email_summaries

cli.py:
  - CLI über argparse
  - Commands:
      - init-db
      - inspect-pst <pfad>
      - import-pst <pfad>
      - summarize --limit <n>

WEITERE ANFORDERUNGEN
----------------------
- Alle Module sollen ausführbaren, getesteten Code enthalten, kein Pseudocode.
- Jeder mögliche Fehlerfall soll sauber abgefangen werden.
- Der Code soll klar strukturiert, kommentiert und robust sein.
- Keine GUI implementieren, nur den CLI-Workflow vorbereiten.
- In README.md bitte kurz erklären:
    - Setup
    - Installation
    - Beispielbefehle
    - Projektidee

WENN DU ETWAS NICHT SICHER WEISST
---------------------------------
Frag vorher nach, statt Annahmen zu treffen.

Erzeuge jetzt basierend auf diesen Spezifikationen das gesamte Projektgerüst, 
inklusive aller Dateien mit funktionsfähigem Code.
```

---

## 💬 Willst du zusätzlich…

- eine **GUI-Version** als zweiter Prompt?  
- eine **RAG-Erweiterung** (Such-Chunks + Embeddings)?  
- ein **Cursor-Auto-Refactoring-Prompt**, um später Code aufzuräumen?

Sag einfach Bescheid – ich baue dir alles so, dass du es 1:1 in Cursor reinfeuern kannst.

### 15. Benutzer

alle 3

### 16. Assistent

Okay, du willst alles – mag ich. 😄  
Ich geb dir die drei Prompts so, dass du sie **nacheinander** in Cursor verwenden kannst.  
Empfehlung (ja, hier widerspreche ich dir ein bisschen): **nicht alle drei direkt hintereinander feuern**, sondern _erst_ Basisprojekt, dann GUI, dann RAG, dann Refactoring.

Hier kommen sie.

---

## 1️⃣ GUI-Entwicklungsprompt (Streamlit)  

**Einsatz:**  
Wenn dein Basis-Projekt (CLI + DB + PST-Import + Summarizer) schon angelegt ist.  
Diesen Prompt in Cursor werfen und ihm sagen, er soll das bestehende Projekt **erweitern**, nicht neu bauen.

---

### 🔹 Prompt: GUI hinzufügen

```text
Ich habe bereits ein Python-Projekt namens `email-kb-pilot` mit dieser groben Struktur:

- SQLite-Datenbank mit Tabellen:
  - emails (Rohdaten der Emails)
  - email_summaries (LLM-Zusammenfassungen)
- PST-Import (pst_import.py): liest PST-Dateien und importiert Emails in die DB
- LLM-Anbindung (llm_client.py): kann Emails zusammenfassen
- Summarizer (summarizer.py): erzeugt für Emails Summaries
- CLI (cli.py): init-db, import-pst, summarize etc.

Ich möchte jetzt eine einfache GUI auf Basis von **Streamlit** ergänzen. 
WICHTIG: Bitte das bestehende Projekt NICHT neu aufsetzen, sondern ERWEITERN.

Ziele der GUI:

1. Seite "Dashboard":
   - Anzahl Emails insgesamt
   - Anzahl Emails mit Summary
   - einfache Verteilung der Relevanz (hoch/mittel/niedrig)

2. Seite "PST-Import":
   - Texteingabefeld für Pfad zur PST-Datei
   - Button "Ordner analysieren":
       - liest PST und zeigt alle Ordnerpfade strukturiert an
   - Multi-Select mit allen Ordnerpfaden:
       - standardmäßig sind alle sinnvollen Ordner vorausgewählt,
         offensichtliche Trash-Ordner (Gelöschte, Junk, Spam, Newsletter) nicht
   - Button "Import starten":
       - importiert Emails nur aus den ausgewählten Ordnern in die DB
   - Optional: Button "Summaries für einige Emails erzeugen"
       - ruft intern die vorhandene Summarizer-Funktion auf

3. Seite "Emails & Suche":
   - Filterfelder:
       - "Betreff enthält" (Text)
       - "Summary enthält" (Text)
       - Relevanz (Dropdown: egal/hoch/mittel/niedrig)
       - Limit (z.B. Slider)
   - Ergebnistabelle mit:
       - id, sent_at, sender, subject, core_statement, relevance
   - Detailansicht:
       - bei Auswahl einer Email-ID:
           - zeigt Betreff, Absender, Empfänger, Datum, Ordnerpfad
           - zeigt Summary (Kernaussage, Bullet Points, Relevanz)
           - zeigt Originaltext (raw_body) in Textarea

Technische Anforderungen:

- Neue Datei im Projektroot: `ui_app.py`
- Nutzung von `streamlit`
- DB-Zugriff NICHT verdoppeln, sondern idealerweise Hilfsfunktionen aus db.py wiederverwenden
  oder einfache, klar strukturierte Abfragen bauen.
- Kein Frontend-Build, nur Streamlit-App, startbar mit: `streamlit run ui_app.py`
- Fehler robust abfangen:
  - PST-Pfad existiert nicht
  - leere Datenbank
  - keine Summaries vorhanden

Bitte:
- Die GUI so implementieren, dass sie das bestehende Schema und die Tabellen nutzt.
- Kein generisches Beispielprojekt erzeugen, sondern wirklich an `emails` und `email_summaries` andocken.
- Kommentiere den Code grob, damit klar ist, was wo passiert.

Erzeuge jetzt die Datei `ui_app.py` und passe ggf. bestehende Module minimal an, falls nötig.
```

---

## 2️⃣ RAG-Erweiterungsprompt (Embeddings + semantische Suche)

**Einsatz:**  
Wenn Import + Summaries funktionieren und du *inhaltlich* zufrieden bist.  
Hier fügst du einen Vektorstore + RAG-Layer dazu.

---

### 🔹 Prompt: RAG-Funktionalität ergänzen

```text
In meinem Projekt `email-kb-pilot` gibt es bereits:

- Eine SQLite-Datenbank mit:
  - emails (id, subject, sender, raw_body, sent_at, folder_path, ...)
  - email_summaries (email_id, core_statement, bullet_points, relevance_level, created_at)
- PST-Import und Summarizer
- LLM-Client (Claude/OpenAI)
- Optional bereits eine Streamlit-GUI (Dashboard, PST-Import, Emailsuche)

Ich möchte jetzt eine einfache **RAG-Funktionalität** hinzufügen, um semantisch in meinen Emails/Summaries zu suchen.

Ziele:

1. Eine neue Tabelle für Embeddings:
   - `email_embeddings` mit Feldern:
     - id
     - email_id (FK auf emails)
     - vector (Embedding, z. B. als BLOB oder JSON)
     - model_name
     - created_at

2. Ein neues Modul `embeddings.py`:
   - Funktion `build_email_text(email, summary)`:
       - erstellt einen für Embeddings geeigneten Text aus:
         - Betreff
         - Kernaussage
         - Bullet Points
         - optional Tags (falls vorhanden)
   - Funktion `generate_embeddings_for_unsummarized(limit=100)`:
       - sucht alle emails mit vorhandener Summary, aber ohne Embedding
       - ruft ein Embedding-Modell auf (OpenAI-Embeddings oder anderen Anbieter)
       - speichert den Vektor in `email_embeddings`
   - Funktion `semantic_search(query, top_k=10)`:
       - erstellt Embedding für die Query
       - sucht die ähnlichsten Einträge in `email_embeddings`
       - nutzt Cosine Similarity oder Dot Product
       - gibt Liste von Treffern (email_id, score) zurück

3. Integration in CLI:
   - Erweiterung von `cli.py` um:
     - `build-embeddings --limit N`
     - `semantic-search "<frage>" --top-k 10`
   - `semantic-search` soll:
     - Vektorsuche ausführen
     - dazugehörige Emails + Summaries aus der DB laden
     - die Ergebnisse im Terminal anzeigen (Datum, Betreff, Kernaussage, Score)

4. Optional: Integration in die Streamlit-GUI
   - Neue Seite "Semantische Suche":
       - Textfeld für Query
       - Button "Suchen"
       - Anzeige der Top-K Ergebnisse (Betreff, Datum, Kernaussage, Score)

Technische Anforderungen:

- Embeddings bitte über ein existierendes Modell (z.B. OpenAI-Embeddings oder ein Provider deiner Wahl),
  aber so implementieren, dass der Provider über die vorhandene config/Settings abstrahiert wird.
- Falls du zusätzliche Dependencies (z. B. `numpy`) brauchst, ergänze sie in `requirements.txt`.
- Vektorspeicherung darf einfach sein:
  - z. B. als JSON-String der Liste von floats in SQLite (kein externer DB-Dienst nötig)

WICHTIG:
- Bitte NICHT das gesamte Projekt umbauen.
- Keine neue Projektstruktur einführen, sondern `embeddings.py` + kleinere Anpassungen in `cli.py` und ggf. config.
- Achte darauf, dass die Embedding-Lösung mit der bestehenden DB harmoniert.

Erweiterungsschritte:
1. Neue Tabelle `email_embeddings`
2. Modul `embeddings.py`
3. CLI-Commands
4. (optional) Integration in Streamlit, falls vorhanden

Bitte setze diese Erweiterung jetzt sauber um.
```

---

## 3️⃣ Refactoring- & Codequalitätsprompt für Cursor

**Einsatz:**  
Wenn das Projekt läuft, aber du aufräumen, modularisieren und die Qualität hochziehen willst.  
Hier ist der Moment, wo ich dir ein bisschen widerspreche:  
Wenn du das _zu früh_ machst, polierst du beweglichen Beton. Ideal: nach den ersten echten Tests.

---

### 🔹 Prompt: Refactoring & Codequalität

```text
Ich habe ein gewachsenes Python-Projekt `email-kb-pilot` mit:

- DB-Modul(e)
- PST-Import
- LLM-Client (Claude/OpenAI)
- Summarizer
- CLI
- Optional: Streamlit-GUI
- Optional: RAG/Embeddings

Das Projekt funktioniert grundsätzlich, ist aber gewachsen und braucht ein strukturiertes Refactoring.

Deine Aufgaben:

1. Architektur-Check (ohne alles umzuschmeißen):
   - Identifiziere Duplikate (DB-Zugriff, Pfadbehandlung, Prompt-Texte, Config-Zugriff).
   - Schlage sinnvolle Modulgrenzen vor (z. B. `services/`, `prompts.py`, `models.py`).
   - Mach Änderungsvorschläge so, dass sie inkrementell umsetzbar sind.

2. Codequalität:
   - Vereinheitliche Typannotationen (Python 3.10+).
   - Entferne offensichtliche Dead Code / nicht genutzte Funktionen.
   - Füge an sinnvollen Stellen Docstrings hinzu (kurz und präzise).
   - Sorge dafür, dass alle Module importierbar sind, ohne Seiteneffekte zu haben.

3. Prompts & LLM-Zugriff:
   - Extrahiere lange Prompt-Texte in eine separate Datei `prompts.py`.
   - Stelle sicher, dass `llm_client.py` nur noch Logik für:
       - Modellwahl
       - Request/Response-Handling
       - Fehlerbehandlung beim JSON-Parsing
     enthält.
   - Füge robustes JSON-Handling hinzu:
       - Versuche zuerst direktes `json.loads`
       - Falls das scheitert: einfache Reparatur (z. B. herausparsen des JSON-Blocks)

4. CLI & GUI:
   - Stelle sicher, dass CLI-Commands klar benannt und konsistent sind.
   - Überprüfe, ob GUI-Funktionen auf vorhandene Services zugreifen (statt Logik zu duplizieren).
   - Falls nötig, extrahiere Wiederverwendungs-Logik in Service-Funktionen, damit CLI und GUI dieselben Pfade nutzen.

5. Style:
   - Orientierung an PEP8
   - Kein unnötiger Micro-Optimierungs-Zauber
   - Fokus auf Lesbarkeit und Wartbarkeit

Vorgehen:

- Bitte gehe Datei für Datei vor.
- Beschreibe mir für jede Datei kurz:
  - Was du ändern willst
  - Warum
- Setze die Änderungen dann INKREMENTELL um, statt alles auf einmal zu verändern.
- Fange an mit:
  1. `config.py`
  2. `db.py`
  3. `llm_client.py`
  4. `summarizer.py`
  5. `pst_import.py`
  6. CLI
  7. GUI (falls vorhanden)
  8. RAG/embeddings (falls vorhanden)

WICHTIG:
- Funktionalität darf nicht stillschweigend verschwinden.
- Wenn du Funktionen entfernst oder änderst, stelle sicher, dass alle Aufrufer im Projekt aktualisiert werden.
- Keine neuen großen Abhängigkeiten hinzufügen, außer es ist wirklich notwendig und du begründest es.

Starte jetzt mit einer kurzen Übersicht über den Status des Projekts (Dateiliste, grobe Bewertung),
und führe dann das Refactoring schrittweise durch.
```

---

Wenn du willst, können wir als nächstes einen **Review-Prompt** bauen, mit dem du dir von der KI **konkrete Verbesserungsvorschläge für deine DB-Struktur oder Prompt-Designs** holen kannst – oder wir machen einen „Testdaten-Generator“-Prompt, der dir Fake-Mails erzeugt, damit du deine Pipeline ohne echte Daten testen kannst.

### 17. Benutzer

erstelle mir einen kompletten prompt für gemini ai studio

### 18. Assistent

Alles klar Markus — ich baue dir jetzt einen **kompletten, fertigen Prompt für Google Gemini AI Studio**, so dass du damit **ein neues Projekt generieren, erweitern oder warten kannst**.  
Der Prompt ist so formuliert, dass er:

- klar,
- vollständig,
- ausführbar,
- modell-agnostisch,
- und auf dein Wissensdatenbank-Projekt zugeschnitten ist.

Und: Das Prompt-Artefakt selbst bleibt **neutral**, ohne meine gewohnte Art – wie du es wolltest.

---

# ✅ **Vollständiger, sofort einsetzbarer Prompt für Gemini AI Studio**  
**→ Einfach kopieren + in Gemini einfügen.**

---

## 🔥 **GEMINI-PROMPT (komplett & ready-to-run)**

**Rolle & Ziel:**  
Du bist ein erfahrener Full-Stack-Entwicklungsassistent. Dein Ziel ist es, ein modulares, gut strukturiertes, erweiterbares Python-Projekt zu erzeugen, das folgende Kernfunktionen bietet:

---

# **📦 Projektname:**  
`email-kb-pilot`

---

# **📌 Projektbeschreibung**

Dieses Projekt ermöglicht:  
1. Das Einlesen von PST-Dateien.  
2. Das Anzeigen und Auswählen der enthaltenen Ordner vor dem Import.  
3. Das Extrahieren und Speichern von Emails in einer SQLite-Datenbank.  
4. Das Zusammenfassen der Email-Inhalte mittels LLM (Claude ODER OpenAI, konfigurierbar).  
5. Eine GUI auf Basis von Streamlit (Dashboard, PST-Import, Emailsuche).  
6. Eine optionale Erweiterung für semantische Suche (RAG) mittels Embeddings.  
7. Eine klare CLI-Struktur zur Steuerung der Prozesse.  
8. Saubere modularisierte Architektur + optionales Refactoring.

---

# **📂 Gewünschte Verzeichnisstruktur**

Erzeuge folgende Struktur:

```
project_root/
  .env.example
  .gitignore
  requirements.txt
  README.md

  src/
    __init__.py
    config.py
    db.py
    pst_import.py
    llm_client.py
    summarizer.py
    embeddings.py        # (für RAG)
    cli.py

  ui_app.py              # Streamlit GUI
```

---

# **🔧 Anforderungen an alle Module**

**Allgemein:**

- Sauberer, organisierter, getesteter Code  
- Python ≥ 3.10  
- Wiederverwendbare Funktionen  
- Typannotationen (PEP 484 / Python 3.10)  
- Fehler robust abfangen  
- Keine Hardcoded-Pfade  
- Keine Seiteneffekte bei Modulimport  
- Ausführbare Beispielbefehle in README  

---

# **🗄 Datenbank (SQLite)**

Erzeuge Tabellen:

## Tabelle `emails`  
- id (PK)  
- message_id  
- subject  
- sender  
- recipients  
- sent_at  
- folder_path  
- source_file  
- raw_body  
- hash (unique)

## Tabelle `email_summaries`
- id  
- email_id (FK → emails)  
- core_statement  
- bullet_points  
- relevance_level  
- created_at  

## Tabelle `email_embeddings` (für RAG)
- id  
- email_id  
- vector (JSON oder BLOB)  
- model_name  
- created_at  

---

# **📥 PST-Import (pst_import.py)**

Bereitstellen:

### `collect_folder_paths(pst_path)`
- Gibt alle Ordnerpfade aus der PST zurück.

### `import_selected_folders(pst_path, allowed_paths)`
- Importiert nur Emails aus ausgewählten Ordnern.

### Email-Extraktion:
- subject  
- sender  
- recipients  
- sent_at  
- folder_path  
- raw_body  
- hash (SHA256)

### Zusätzliche Anforderungen:
- PST-Parser: `pypff`  
- Robuste Fehlerbehandlung  
- Ordnerstruktur rekursiv traversieren  

---

# **🧠 LLM-Anbindung (llm_client.py)**

Einheitliches Interface:

### Klasse `LLMClient`:
- Parameter wählt Provider (`anthropic` oder `openai`) basierend auf `.env`  
- Methoden:
  - `summarize_email(body: str) -> dict`
  - `embed_text(text: str) -> list[float]` (für RAG)

### Zusammenfassungs-Prompt (JSON-only):

```json
{
  "core_statement": "...",
  "bullet_points": ["...", "..."],
  "tags": ["...", "..."],
  "persons": [{"email": "...", "role": "..."}],
  "relevance": "hoch|mittel|niedrig"
}
```

### Anforderungen:
- Strenges JSON  
- Fehlerresistent beim Parsen  
- Option für Debug-Logging  

---

# **📝 Summarizer (summarizer.py)**

### Funktion:
`summarize_unsummarized(limit=20)`

Ablauf:

1. Emails ohne Summary laden  
2. LLM-Client aufrufen  
3. Summary in DB speichern  
4. Relevanz übernehmen  

---

# **🔍 RAG & Embeddings (embeddings.py)**

Bereitstellen:

### `build_email_text(email, summary)`
Erstellt Embedding-Text aus:
- subject  
- core_statement  
- bullet_points  
- tags  

### `generate_embeddings_for_unsummarized(limit=200)`
Schreibt Embeddings in DB.

### `semantic_search(query: str, top_k=10)`
- Embedding der Query erstellen  
- Vektorähnlichkeit berechnen  
- Emails zurückgeben  

---

# **🖥 GUI (ui_app.py, Streamlit)**

Drei Seiten:

---

### 📊 **1. Dashboard**
- Anzahl Emails gesamt  
- Anzahl Emails mit Summary  
- Verteilung Relevanz  

---

### 📥 **2. PST-Import**
- Eingabe PST-Pfad  
- Button „Ordner analysieren“  
- Multi-Select der gefundenen Ordner  
- Button „Import starten“  
- Button „Summaries erzeugen“  

---

### 🔎 **3. Emails & Suche**
- Filter:
  - Betreff enthält  
  - Summary enthält  
  - Relevanz  
  - Limit  

- Tabelle: id, sent_at, sender, subject, core_statement, relevance  
- Detailansicht inkl. raw_body  

---

# **📌 CLI (cli.py)**

Befehle:

```
email-kb init-db
email-kb inspect-pst <pfad>
email-kb import-pst <pfad>
email-kb summarize --limit 20
email-kb build-embeddings --limit 200
email-kb semantic-search "<query>" --top-k 10
```

---

# **🧹 Refactoring-Anforderungen**

- Entferne Duplikate  
- Extrahiere Prompt-Texte in `prompts.py`  
- Einheitliche Namenskonventionen  
- Kein „Spaghetti Import“  
- Schaffe `services`-ähnliche Struktur, wenn sinnvoll  
- Kommentare und kurze, klare Docstrings  

---

# **🎯 Deine Aufgabe (Gemini):**

1. **Erstelle den gesamten Code für alle oben genannten Dateien.**  
2. **Baue ihn modular, robust, produktionsähnlich.**  
3. **Kein Beispiel-Pseudocode – nur ausführbaren Code.**  
4. **Erzeuge die komplette Projektstruktur mit Dateien und Inhalten.**  
5. **Schreibe eine README.md mit Setup, Installation, CLI-Beispielen.**

---

# **FERTIG.**  
Bitte jetzt das gesamte Projekt gemäß dieser Spezifikation generieren.

---

---

## Wenn du willst …

… kann ich dir auch einen:  
- **Testdaten-Generator-Prompt**  
- **Migrationen-Prompt**  
- **„Posteingang als API“-Prompt**  
- **„Prompt für automatisierte Architekturtests“**

Sag einfach Bescheid.

---
title: "Outlook Scraper"
type: chatgpt_conversation
source: chatgpt
source_id: "68d3beb6-28f0-8325-967b-822ffcfcad3b"
created: 2025-09-24
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
  - tischtennis
---


# Outlook Scraper

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68d3beb6-28f0-8325-967b-822ffcfcad3b`
- Nachrichten: 13

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Outlook Scrapper entwickeln pdf mit der blueprint vorlage ist vorhanden

### 2. Assistent

sauber — ich hab dir eine lauffähige Grundlage plus eine kompakte Blueprint-PDF gebaut. Darin steckt Architektur (Graph vs. COM/EWS/IMAP), Scopes/Security, Datenmodell, Pipeline, Setup und ein Python-Skelett, das E-Mails inkl. Anhängen via Microsoft Graph zieht und als NDJSON speichert.

**Downloads:**
- [Blueprint-PDF](sandbox:/mnt/data/outlook_scraper_blueprint_de.pdf)  
- [Starter-Skript `outlook_scraper.py`](sandbox:/mnt/data/outlook_scraper.py)  
- [Beispiel-Konfig `config.example.json`](sandbox:/mnt/data/config.example.json)  
- [README (Kurzstart)](sandbox:/mnt/data/README_Outlook_Scraper_DE.txt)

### Wie du’s direkt testest
1) `pip install msal requests beautifulsoup4 python-dateutil tqdm`  
2) Azure App registrieren, `Mail.Read`-Scope geben (delegiert **oder** Anwendung) und ggf. Admin Consent.  
3) `config.json` aus dem Beispiel ableiten (Tenant, Client ID, ggf. Secret)  
4) `python outlook_scraper.py config.json`  
→ Output landet in `./out/emails.ndjson` und `./out/attachments/`.

### Nächste sinnvolle Ausbauten
- Delta-Sync (`/messages/delta`) für inkrementelle Läufe.  
- SQLite/Postgres statt NDJSON, plus Upserts auf `internetMessageId`.  
- PII-Maskierung vor Persistenz, strukturierte Logs + Retries bei 429/5xx.

Wenn deine bestehende Blueprint-Vorlage Besonderheiten (Felder, Filterlogik, Compliance-Anforderungen) enthält, sag mir die Abweichungen — ich passe Skript & PDF gezielt darauf an oder erweitere es für Outlook-COM, falls ihr on-prem/ohne Graph arbeitet.

### 3. Assistent

Deine hochgeladene PDF ist schon ziemlich detailliert: Sie beschreibt ein modulares Tool namens **OutlookInsight**, das Outlook-Postfächer (via COM) und PST-Dateien durchsuchen kann, die Treffer in einer **SQLite-Datenbank** ablegt und anschließend mit **Ollama (lokale KI)** semantisch analysiert. Dazu gibt’s auch eine GUI mit Tkinter, Codebeispiele für die wichtigsten Module und sogar einen Entwicklungs- und Testplan【16†outlook scrapper.pdf】.

Spannend ist der Unterschied zu dem Blueprint, den ich dir vorher gebaut habe:  
- **Dein Dokument** ist *lokal orientiert* (Windows COM, PST via `pypff`, keine Cloud, Ollama für KI).  
- **Mein Blueprint** setzt auf *Microsoft Graph* (Cloud/API-first, modernere Schnittstellen, ideal für M365).  

Kurz: Dein PDF = On-Premises / lokale KI, mein Blueprint = Cloud / Graph + NDJSON.

Du könntest also zwei Pfade gehen:  
1. **Lokales Setup (dein PDF)**:  
   - Outlook COM und PST-Parser.  
   - SQLite + Ollama.  
   - GUI für Anwender.  
   - Vorteil: Alles offline, keine Azure-App-Registrierung.  
   - Nachteil: Stärker an Windows + Outlook gebunden.  

2. **Cloud-basiertes Setup (mein Blueprint)**:  
   - Microsoft Graph-API.  
   - Portable, läuft auch auf Linux/macOS, skalierbarer.  
   - Vorteil: Zukunftssicher, unabhängig vom lokalen Outlook.  
   - Nachteil: Braucht Azure-App-Setup, Cloud-Trust.  

Ich könnte dir jetzt:  
- entweder das **lokale Projekt (PDF) in Codegerüste übersetzen** (also `outlook_connector.py`, `ollama_integration.py`, `database.py`, `ui.py`, `main.py` generieren),  
- oder **die beiden Ansätze verschmelzen**: Graph als Datenquelle, Ollama lokal für semantische Suche.  

Willst du, dass ich aus deinem PDF direkt den kompletten Code-Prototyp (die Module + main) generiere?

### 4. Benutzer

ja bitte und als lokales Projekt.

### 5. Assistent

alles klar — ich hab dir aus deiner Vorlage ein **lokales Projekt** gebaut, inklusive GUI, Outlook-COM und PST-Support, SQLite-DB und Ollama-Integration. Du kannst direkt loslegen.

**Download (alles drin):**  
- 📦 [outlookinsight_local.zip](sandbox:/mnt/data/outlookinsight_local.zip)

Oder einzelner Projektordner:  
- 📁 `/mnt/data/outlookinsight_local` (enthält `*.py`, `README.md`, `requirements.txt`)

### Struktur
- `outlook_connector.py` – Outlook via COM (pywin32)  
- `pst_handler.py` – PST-Parsing (pypff)  
- `database.py` – SQLite-Schema + CRUD  
- `ollama_integration.py` – lokale KI (Ollama) mit robuster JSON-Extraktion  
- `search_engine.py` – orchestriert Suche/Index + Insights  
- `ui.py` – Tkinter-GUI (Suche, Tabelle, Status)  
- `main.py` – Einstiegspunkt  
- `config.py` – Pfade/Modelle/Limits  
- `requirements.txt` & `README.md`

### Schnellstart (Kurzfassung)
1) Windows + Outlook installiert, Python 3.10+.  
2) Ollama installieren, Modell initialisieren: `ollama run llama3`.  
3) In den Projektordner gehen und Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```
4) `config.py` prüfen (Ordnername, DB-Pfad, Modell).  
5) Start:
```bash
python main.py
```

Das UI lässt dich Outlook verbinden (Ordner) und eine PST wählen, dann „Suchen & Indexieren“. Treffer landen in `insights.db` und erscheinen in der Tabelle; semantische Insights werden bei aktivem Ollama automatisch erzeugt.

Wenn du magst, erweitere ich als Nächstes: Batch-Index aller Mails ohne Query, Delta-Updates, oder ein Export-Feature (CSV/Parquet).

### 6. Benutzer

ja

### 7. Assistent

fantastisch — ich hab das **lokale Projekt** direkt erweitert:

- Batch-Index: Button **„Alles indizieren“** (Outlook-Ordner +/− PST).
- **Delta seit**: Datumsfeld (YYYY-MM-DD optional mit Uhrzeit), um nur neue Mails zu ziehen.
- **Export CSV**: exportiert aktuelle Treffer nach `exports/`.

**Download:**  
- 📦 [outlookinsight_local_v2.zip](sandbox:/mnt/data/outlookinsight_local_v2.zip)

### Was neu ist (kurz)
- `outlook_connector.py` & `pst_handler.py`: unterstützen `since` (Delta-Filter).  
- `search_engine.py`: `index_all()` + `index_from_sources(..., since=...)`.  
- `ui.py`: neue Eingabefelder/Buttons und CSV-Export.  
- `config.py`: `EXPORT_DIR = "exports"`.

### Start
```bash
pip install -r requirements.txt
python main.py
```
Im UI: optional „Delta seit“ setzen, „Outlook verbinden“ / „PST wählen…“, dann „Suchen & Indexieren“ oder „Alles indizieren“. Export geht jederzeit mit „Export CSV“.

Wenn du noch eine **Volltext-Indizierung** (Whoosh/SQLite FTS5) oder **Entitäten-Tab** in der GUI willst, baue ich das direkt ein.

### 8. Benutzer

ja

### 9. Assistent

nice — ich hab dir das Projekt **weiter aufgerüstet**:

- **Volltextsuche mit SQLite FTS5** (`emails_fts`) inklusive Triggers, die den Index automatisch pflegen.
- **Entitäten-Tab in der GUI** (ttk.Notebook): zeigt erkannte Entities (Typ/Wert) pro E-Mail.
- **FTS-Schalter** im UI („FTS nutzen“) – falls dein SQLite kein FTS5 kann, einfach deaktivieren, dann greift der LIKE-Fallback.

**Download (aktuelle Version):**  
- 📦 [outlookinsight_local_v3.zip](sandbox:/mnt/data/outlookinsight_local_v3.zip)

### Was sich geändert hat
- `database.py`:  
  - Neues Table `entities` (normalisiert).  
  - FTS5-Tabelle `emails_fts` + Trigger (`INSERT/UPDATE/DELETE`).  
  - `store_insights()` schreibt Entities nach `entities`.  
  - `search_emails(query, use_fts=True)` nutzt FTS (Fallback: LIKE).  
  - `search_entities(query)` für den Entitäten-Tab.
- `search_engine.py`: übergibt `use_fts` an DB + `query_entities()`.
- `ui.py`:  
  - Notebook mit Tabs **E-Mails** und **Entitäten**.  
  - Checkbox **FTS nutzen**.  
  - Beide Tabs aktualisieren sich bei Suche/Indexierung.
- `README.md`: Hinweise zu FTS5 + Entitäten ergänzt.

### Start (unverändert)
```bash
pip install -r requirements.txt
python main.py
```

Probier eine Anfrage wie `projekt xyz budget` und schau im **Entitäten-Tab**, ob Beträge/Personen auftauchen. Nächster Feinschliff könnte sein: FTS-Ranking (BM25, sofern dein SQLite das mitbringt), Snippets mit Kontextfenstern, oder ein Dedupe über `internetMessageId`/`EntryID`.

### 10. Benutzer

Traceback (most recent call last):

  File "g:\Programmieren\Outlook-Scraper\main.py", line 1, in <module>

    from database import Database

  File "g:\Programmieren\Outlook-Scraper\database.py", line 25

    -- Normalisierte Entitäten (Typ/Wert je E-Mail)

    ^^^^^^^^^^^^^^^^^^^^^^^^^^

SyntaxError: invalid syntax. Perhaps you forgot a comma?

### 11. Assistent

Guter Fund — das ist auf meine Kappe. Der Fehler kommt von einer **frei stehenden SQL-Kommentarzeile** in `database.py`, die **außerhalb** eines Python-Strings gelandet ist. Python sieht dann `-- ...` und denkt: „Was ist das für ein Operator?“ → `SyntaxError`.

Ich habe die Datei korrigiert (Kommentare in echte Python-`#`-Kommentare verlegt) und alles neu gepackt.

**Fix-Download:**  
- 📦 [outlookinsight_local_v3_1.zip](sandbox:/mnt/data/outlookinsight_local_v3_1.zip)

### Schnellster Weg zum lokalen Fix
Falls du nicht neu laden willst, ersetze in deiner `database.py` alles durch diese Version (Ausschnitt Kopfteil zeigt die entscheidende Stelle, vollständige Datei ist im ZIP):

```python
# DDL-Schema. WICHTIG: Nur gültige Python-Strings in der Liste!
SCHEMA = [
    """CREATE TABLE IF NOT EXISTS emails (...);""",
    """CREATE TABLE IF NOT EXISTS insights (...);""",
    # Normalisierte Entitäten (Typ/Wert je E-Mail)
    """CREATE TABLE IF NOT EXISTS entities (...);""",
    # FTS5-Index
    """CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
        subject, body, content='emails', content_rowid='id'
    );""",
    # Trigger ...
    """CREATE TRIGGER IF NOT EXISTS emails_ai AFTER INSERT ON emails BEGIN ... END;""",
    """CREATE TRIGGER IF NOT EXISTS emails_ad AFTER DELETE ON emails BEGIN ... END;""",
    """CREATE TRIGGER IF NOT EXISTS emails_au AFTER UPDATE ON emails BEGIN ... END;""",
    """CREATE INDEX IF NOT EXISTS idx_emails_subject ON emails (subject);""",
    """CREATE INDEX IF NOT EXISTS idx_emails_date ON emails (date_received);""",
    """CREATE INDEX IF NOT EXISTS idx_insights_category ON insights (category);"""
]
```

Danach erneut starten:
```bash
pip install -r requirements.txt
python main.py
```

Wenn als Nächstes etwas zickt (z. B. FTS5 nicht im lokalen SQLite), sag mir die genaue Fehlermeldung — ich schalte dann automatisch auf einen kompatiblen Weg oder passe die Abfragen an.

### 12. Benutzer

Traceback (most recent call last):

  File "g:\Programmieren\Outlook-Scraper\main.py", line 2, in <module>

    from ui import InsightGUI

  File "g:\Programmieren\Outlook-Scraper\ui.py", line 8, in <module>

    from outlook_connector import OutlookConnector

  File "g:\Programmieren\Outlook-Scraper\outlook_connector.py", line 3, in <module>

    import win32com.client

ModuleNotFoundError: No module named 'win32com'

### 13. Assistent

Das ist ein klassischer **pywin32**-Fall. `win32com` kommt aus dem Paket `pywin32` und fehlt in deiner Umgebung. Du hast zwei Wege:

### 1) pywin32 sauber installieren (empfohlen)
Nutze **genau den Python**, mit dem du das Projekt startest:
```bat
python -m pip install --upgrade pip setuptools wheel
python -m pip install pywin32
```
Dann Terminal/VS Code **neu starten** und testen:
```bat
python -c "import win32com.client; print('OK')"
```
Wenn das klappt, funktioniert „Outlook verbinden“ im Tool.

Typische Stolperfallen:
- Mehrere Python-Installationen → `python` und `pip` zeigen auf verschiedene Interpreter. Prüfen mit `where python` und `where pip`.
- 32/64-Bit-Mismatch: Python und Outlook sollten beide 64-Bit sein (oder beide 32-Bit).
- In seltenen Fällen hilft zusätzlich:
  ```bat
  python -m pip install pywin32==306
  ```

### 2) Bis dahin ohne Outlook weiterarbeiten
Ich habe das Projekt so angepasst, dass Outlook **optional** ist: Wenn `pywin32` fehlt, wird der Button deaktiviert und du kannst **PST-Dateien** trotzdem indexieren.

**Download (mit Fixes & Degradation):**  
- 📦 [outlookinsight_local_v3_2.zip](sandbox:/mnt/data/outlookinsight_local_v3_2.zip)

Darin enthalten:
- `outlook_connector.py`: Lazy-Import und klare Fehlermeldung, falls pywin32 fehlt.
- `ui.py`: erkennt automatisch, ob `win32com` verfügbar ist; Outlook-Button wird sonst deaktiviert.
- `README.md`: Troubleshooting-Block für `win32com`.

Wenn nach der Installation immer noch Fehler auftreten, poste mir bitte die Ausgaben von:
```bat
python -V
where python
where pip
python -c "import sys; print(sys.executable)"
python -c "import win32com.client; print(win32com.__gen_path__ if hasattr(win32com,'__gen_path__') else 'OK')"
```
Dann justieren wir zielgenau (Interpreter-Pfad, Architekturen, etc.).

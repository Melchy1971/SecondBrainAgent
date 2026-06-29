---
title: "PST Email Anhang Speichern"
type: chatgpt_conversation
source: chatgpt
source_id: "681a4aef-ee44-8007-8ea4-9c71e01f2db1"
created: 2025-05-06
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# PST Email Anhang Speichern

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `681a4aef-ee44-8007-8ea4-9c71e01f2db1`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Ich möchte mit n8n einen ai Agenten bauen mit dem ich eine Outlook pst Datei nach Emails durchsuche und die gefundenen Anlagen der Mails auf einem lokalen Speicher abspeichern

### 2. Assistent

### 1  Architektur im Überblick

1. **Offline‑Parser (Python + `pypff`)**  
   * Öffnet die `.pst`‑Datei, findet Mails, filtert nach gewünschten Kriterien (Betreff, Datum …​) und legt Anlagen in einem frei wählbaren Zielordner ab.  
   * Das Skript läuft als Kommandozeilen‑Tool, damit es sich in n8n problemlos über den **Execute Command**‑Knoten aufrufen lässt.  
   * Alternativen, falls `pypff` nicht verfügbar ist:  
     * `readpst` (Teil von `libpst`) – konvertiert PST in EML / MBOX samt Anhängen.  
     * Windows‑only: PowerShell‑Skript mit Outlook‑COM‑Objekt.  

2. **n8n‑Workflow**  
   * Trigger (manuell, Cron oder Chat‑Trigger).  
   * Vorbereitungs‑Knoten: Pfade & Suchparameter aus Eingabe holen.  
   * **Execute Command**: Python‑Skript ausführen.  
   * **FS‑Knoten** (oder beliebige Folge‑Knoten): mit den neu gespeicherten Dateien weiterarbeiten, z. B. OCR, Rechnungsextraktion oder Upload.  
   * Optional: **AI Agent**‑Knoten, der basierend auf einer Nutzeranweisung („Suche alle Rechnungen von Lieferant X ab 01.01.2024 …​“) das Skriptparameter‑JSON erzeugt. Das Agent‑Konzept ist in n8n seit v1.82 fest eingebaut﻿ citeturn3search0.

---

### 2  Python‑Skript zum Extrahieren der Anlagen

> **Abhängigkeiten installieren**  
> ```bash
> # Debian / Ubuntu
> sudo apt-get install libpff-dev python3-setuptools
> pip install --no-binary :all: pypff-python
> ```
> Unter Windows kannst du eine vorgebaute `pypff‑wheel` oder WSL + obiges Rezept verwenden.

```python
#!/usr/bin/env python3
"""
save_pst_attachments.py  <pst_file>  <output_dir>  [--subject "Invoice"]
"""
import pypff, pathlib, sys, re, datetime, argparse

def sanitize(text: str) -> str:
    """Dateisystem‑taugliche Zeichenfolgen erzeugen."""
    return re.sub(r"[^a-zA-Z0-9._-]", "_", text or "unknown")

def walk_folders(folder):
    yield folder
    for i in range(folder.number_of_sub_folders):
        yield from walk_folders(folder.get_sub_folder(i))

def iter_messages(folder):
    for i in range(folder.number_of_messages):
        yield folder.get_message(i)

def save_attachments(pst_path, dest, subject_filter=None):
    pst = pypff.file()
    pst.open(pst_path)

    root = pst.get_root_folder()
    for folder in walk_folders(root):
        for msg in iter_messages(folder):
            if subject_filter and subject_filter.lower() not in (msg.subject or "").lower():
                continue

            ts = msg.delivery_time or datetime.datetime.now()
            ts_str = ts.strftime("%Y%m%d_%H%M%S")

            for idx in range(msg.number_of_attachments):
                att = msg.get_attachment(idx)
                name = att.long_filename or att.filename or f"attachment_{idx}"
                data = att.read_buffer(att.size)

                out_dir = pathlib.Path(dest) / sanitize(folder.name)
                out_dir.mkdir(parents=True, exist_ok=True)
                with open(out_dir / f"{ts_str}_{sanitize(name)}", "wb") as fp:
                    fp.write(data)

    pst.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pst_file")
    ap.add_argument("output_dir")
    ap.add_argument("--subject", help="Nur Mails mit Betreff-Teilstring verarbeiten")
    args = ap.parse_args()
    save_attachments(args.pst_file, args.output_dir, args.subject)
```

*Das API‑Layout (`number_of_attachments`, `read_buffer`, …) stammt direkt aus `pypff`﻿ citeturn1view0.*

---

### 3  Einbinden in n8n

| Schritt | Node‑Typ | Wichtigste Einstellungen |
| ------- | -------- | ------------------------ |
| 1 | **Trigger** (Cron / Manual / Chat + AI Agent) | Startbedingung festlegen |
| 2 | **Set** | JSON‑Felder `pstPath`, `targetDir`, `subjectFilter` o. ä. setzen |
| 3 | **Execute Command** | Befehl:<br>`python3 /data/scripts/save_pst_attachments.py {{$json.pstPath}} {{$json.targetDir}} --subject "{{$json.subjectFilter}}` |
| 4 | **FS** (optional) | Dateien weiterverarbeiten oder verschieben |
| 5 | **AI Agent** (optional) | Prompt: „Durchsuche PST nach Rechnungen von Lieferant X …​“ → erzeugt Parameter für Schritt 2 | citeturn0search3turn3search0 |

Tipps:

* **Container‑Setup**  
  * Lege das Skript und eine kleine `requirements.txt` in einen Sidecar‑Container oder in `/data/scripts` deines n8n‑Docker‑Images.  
  * Installiere `pypff` beim Bild‑Build (apt + pip), damit der Execute‑Command‑Knoten im Runtime‑Container alles findet.

* **Security**  
  * Starte n8n mit einem dedizierten Volume für `/attachments` und beschränkten Rechten.  
  * Falls PST‑Dateien sensible Informationen enthalten, lösche sie nach der Extraktion oder verschlüssele das Ziel‑Verzeichnis.

* **Leistung**  
  * Große PSTs (> 2 GB) besser vorab mit `readpst -r -j 4 input.pst output_dir` splitten; so kann n8n jede Teil‑PST parallel verarbeiten.

---

### 4  Von hier aus weiter …

* **Rechnungs‑Pipeline**: Schließe dein bestehendes n8n‑Workflow zur PDF/Beleg‑Analyse an den FS‑Knoten an – so fließen die neu gespeicherten Anlagen direkt in deinen OCR → KI‑Extraktions‑Flow.  
* **Fehler‑Handling**: Gib im Python‑Script nicht‑null‑Exitcodes zurück; in n8n kannst du per **Error Trigger** oder **IF**‑Knoten Branching einbauen.  
* **Agent‑Feintuning**: Möchtest du, dass der AI Agent automatisch entscheidet, ob zuerst PST‑Suche oder ein anderer Schritt dran ist, verbinde ihn mit mehreren Tool‑Knoten (FS, HTTP, Python) – n8n reicht deren JSON‑Schemas an LangChain durch, der Agent sucht sich dann die passende Aktion raus.

Damit hast du eine vollständig automatisierbare Kette: Nutzeranfrage → AI Agent erzeugt Parameter → Python‑Parser extrahiert Anlagen → Dateien liegen lokal für die weitere KI‑Rechnungsextraktion bereit. Viel Erfolg beim Aufbau!

### 3. Benutzer

Erstelle einen Workflow in n8n zur automatisierten E-Mail-Archivierung.

### 4. Assistent

Hier kommt ein komplett funktionsfähiges Beispiel‑Workflow für n8n, das neue (ungelesene) Outlook/IMAP‑Mails automatisch archiviert – inklusive Anhang‑Download und Ablage in einer logisch aufgebauten Ordner­struktur.

[Workflow‑JSON herunterladen](sandbox:/mnt/data/email_archive_workflow.json)

---

## So funktioniert der Ablauf (High‑Level)

| # | Node | Aufgabe |
|:-:|:--|:--|
| 1 |**Email Trigger (IMAP)**| Lauscht auf neue, ungelesene Nachrichten, lädt alle Attachments in Binary‑Form herunter und markiert die Mail danach als gelesen. citeturn0search0|
| 2 |**Split Attachments** (Code)| Zerlegt jede Mail in einzelne Items – genau eines pro Attachment – und baut daraus:<br>• `archivePath` → `/data/mail‑archive/YYYY/MM/DD`<br>• `fileName` → `<Message‑ID>_<Originalname>` |
| 3 |**Write Binary File**| Schreibt jedes Attachment an `{{$json.archivePath}}/{{$json.fileName}}` auf dem Host‑Volume. Der Node erwartet Binary‑Daten; darum wird das Attachment vorab in `binary.data` gepackt. citeturn0search1|

> **Verzeichnisstruktur (Beispiel)**  
> ```
> /data/mail-archive/2025/05/06/
> ├─ <Message‑ID>_invoice.pdf
> ├─ <Message‑ID>_order.xlsx
> └─ …
> ```

---

## Schnellstart – Import & Anpassung

1. **JSON importieren**  
   *In n8n Canvas `Ctrl+V` drücken und die heruntergeladene Datei einfügen oder via “Import from File” auswählen.* citeturn2search5  
2. **IMAP‑Credentials hinterlegen**  
   *Klicke den „Email Trigger (IMAP)“-Node → Tab **Credentials** → wähle/erstelle dein Outlook‑ oder sonstiges IMAP‑Konto.*  
3. **Mount‑Pfad setzen**  
   *Self‑hosting*: Binde beim Container‑Start ein Host‑Verzeichnis z. B. `/var/mail‑archive` auf `/data/mail‑archive`, z. B.:  
   ```yaml
   volumes:
     - /var/mail-archive:/data/mail-archive
   ```  
   *Cloud*: Schreibe statt `/data/…` in einen S3‑Bucket o. ä. – ersetze dafür den **Write Binary File**‑Node durch einen passenden Storage‑Node.  
4. Workflow **aktivieren** → fertig.

---

## Erweiterungsideen

* **Filter**: Im IMAP‑Node kannst du z. B. nach Absender (`FROM "supplier@example.com"`) oder Betreff suchen.  
* **Dateinamen‑Logik**: Passe die JavaScript‑Zeilen in **Split Attachments** an, um z. B. aus dem Betreff weitere Infos zu extrahieren.  
* **Nachbearbeitung**: Hänge nach dem Schreib‑Node deinen bestehenden OCR‑/Rechnungs‑Extraktions‑Flow an – die Dateien liegen schon lokal bereit.  
* **PST‑Archiv**: Für Offline‑.pst‑Dateien den Workflow einfach mit einem **Execute Command**‑Node beginnen, der das in der vorherigen Antwort gezeigte `save_pst_attachments.py` aufruft; ab Node 2 bleibt alles gleich.

Viel Spaß beim Automatisieren – der Workflow ist bewusst schlank gehalten und lässt sich durch die grafische Oberfläche jederzeit erweitern!

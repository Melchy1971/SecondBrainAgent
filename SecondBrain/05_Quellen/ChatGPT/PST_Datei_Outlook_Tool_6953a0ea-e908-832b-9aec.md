---
title: "PST Datei Outlook Tool"
type: chatgpt_conversation
source: chatgpt
source_id: "6953a0ea-e908-832b-9aec-c8576feef79c"
created: 2025-12-30
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
---


# PST Datei Outlook Tool

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6953a0ea-e908-832b-9aec-c8576feef79c`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

erstelle mir eine prompt für google ai studio welcher mir ein tool baut mit dem ich eine outlook pst datei öffnen kann und der mir die vorhandenen ordner anzeigt. die emails nach absender sortiert und mir denn für jeden absender einen unterordner mit absendernamen erstellt und die emails in diesen verschiebt.

### 2. Assistent

Klar — ich baue dir dafür einen Prompt, aber ich muss kurz den Realitätscheck machen, damit du nicht mit einem “Tool” endest, das am Ende gar nicht geht.

## Sparringspartner-Check (damit der Prompt technisch sauber ist)

### 1) Annahmen, die evtl. nicht stimmen
- **“Outlook PST öffnen” direkt in einem Google AI Studio Tool**: Ein LLM kann PST-Dateien nicht “einfach so” lesen. PST ist ein proprietäres Format; dafür brauchst du **Code + Bibliothek** (und meist Dateizugriff).
- **“E-Mails verschieben”**: Das geht nur, wenn dein Tool **write access** zur PST hat (und die Bibliothek das unterstützt). Viele Libraries sind eher “read-only” oder unterstützen Schreiben nur eingeschränkt.
- **Umlaut/Sonderzeichen/Slash im Absender**: Ordnernamen dürfen oft nicht alles enthalten. Du brauchst eine **Sanitization-Logik** (z.B. `Max Mustermann <max@x.de>` → `Max Mustermann` und unerlaubte Zeichen ersetzen).
- **Duplikate**: Gleicher Anzeigename bei unterschiedlichen E-Mail-Adressen → Ordnerkollisionen. Sauber ist: Anzeigename + Domain oder nur E-Mail-Adresse.

### 2) Skeptische Gegenargumente
- “Warum nicht gleich PowerShell/Outlook-Interop?” → Für Windows/Office-Umgebungen ist das oft robuster als PST-Libs.
- “Warum PST offline statt Exchange/Graph?” → Wenn die Daten noch in M365 liegen, ist Graph API einfacher. Aber du willst explizit PST, ok.

### 3) Logik-Check
Dein Ziel ist konsistent: PST öffnen → Ordner anzeigen → E-Mails nach Absender gruppieren → Unterordner erstellen → verschieben.  
Aber: **Welche Ordner sollen verarbeitet werden?** Nur Posteingang? Alle Ordner rekursiv? Sonst verschiebst du z.B. “Gesendet” auch um.

### 4) Alternative Perspektiven
- **Dry-run + Report** (erst anzeigen, was verschoben würde) ist Gold wert.
- Statt “nach Absender” könnte man nach Domain oder nach “Absenderadresse” gruppieren (weniger Kollisionen).

---

## Prompt für Google AI Studio (Tool bauen)

> **Hinweis:** Der Prompt setzt voraus, dass du im AI Studio ein Tool/Agent bauen willst, der **Code generiert** (z.B. Python) und lokal oder in einer kontrollierten Umgebung läuft, wo eine PST-Datei als Pfad bereitsteht.  
> Wenn dein Ziel eine rein “LLM-only” Lösung ohne Laufzeit ist, ist es technisch nicht machbar, weil PST parsing/Schreiben Code braucht.

### Copy/Paste Prompt (Deutsch, tool-orientiert)

**Rolle/Goal**
Du bist ein Senior Software Engineer und Tool-Builder. Baue ein Kommandozeilen-Tool, das eine lokale Microsoft Outlook PST-Datei verarbeitet.

**Funktionale Anforderungen**
1. Nimm als Input:
   - `--pst <pfad_zur_pst>`
   - optional `--root-folder <ordnername>` (z.B. “Posteingang”; wenn nicht angegeben: verarbeite nur Posteingang)
   - optional `--recursive true|false` (default: false)
   - optional `--dry-run true|false` (default: true)
2. Öffne die PST-Datei.
3. Zeige die vorhandenen Top-Level-Ordner und (falls `--recursive=true`) die Ordnerstruktur als Baum in der Konsole an.
4. Sammle E-Mails aus dem Zielordner (und optional rekursiv aus Unterordnern).
5. Gruppiere E-Mails nach Absender. Verwende als Schlüssel bevorzugt:
   - Primär: Absender-E-Mail-Adresse (falls verfügbar)
   - Fallback: Anzeigename
6. Erstelle für jeden Absender einen Unterordner unterhalb des Zielordners:
   - Ordnername soll menschlich lesbar sein (z.B. Anzeigename), aber robust:
     - Entferne/ersetze unzulässige Zeichen (`\/:*?"<>|`)
     - Trim, max Länge (z.B. 80 Zeichen)
     - Bei Kollisionen suffix anhängen (`_2`, `_3`) oder Domain ergänzen
7. Verschiebe jede E-Mail in den entsprechenden Absender-Unterordner.
8. Ausgabe/Logging:
   - Zähle pro Absender: Anzahl gefundener E-Mails, Anzahl verschobener E-Mails, Fehler
   - Am Ende eine Zusammenfassung
9. Sicherheit/Qualität:
   - Implementiere `--dry-run`: keine Änderungen, nur Report
   - Implementiere Fehlerbehandlung (PST nicht lesbar, Ordner existiert nicht, fehlende Senderfelder)
   - Schreibe sauberen, kommentierten Code

**Technische Vorgaben**
- Sprache: Python 3.11+
- Verwende eine PST-Library. Wenn Schreib-/Move-Operationen nicht zuverlässig unterstützt werden:
  - Gib ehrlich an, was read-only ist
  - Implementiere als Alternative: Export als .eml in Dateisystem + Struktur nach Absender (wenn PST move nicht geht)
- Erzeuge ein lauffähiges Projekt:
  - `main.py` (CLI)
  - `requirements.txt`
  - `README.md` mit Setup & Beispielen
- Bevor du Code schreibst, entscheide dich für die beste Library-Strategie und begründe kurz.
- Liefere danach den vollständigen Code.

**Abnahmekriterien**
- Ich kann `python main.py --pst "/path/file.pst" --root-folder "Posteingang" --dry-run true` laufen lassen und bekomme Ordnerbaum + Report.
- Bei `--dry-run false` werden Absender-Ordner erstellt und E-Mails verschoben (oder sauberer Fallback, falls PST move nicht möglich ist).

**Zusatz**
- Achte auf Performance (große PST): iteratives Verarbeiten, kein Laden aller Bodies in den RAM.
- Unicode/Deutschzeichen müssen korrekt funktionieren.

---

## Kleiner Bonus: Zwei sinnvolle Optionen, die du im Prompt lassen oder weglassen kannst
- `--sender-mode address|name|name_and_address` (default: address)
- `--include-sent true|false` (default: false)

---

Wenn du mir sagst, **wo** das Tool laufen soll (Windows mit installiertem Outlook vs. Linux/macOS ohne Outlook), kann ich dir den Prompt noch so zuschneiden, dass er *die richtige Technik* erzwingt (z.B. Outlook-Interop/PowerShell auf Windows ist oft am zuverlässigsten fürs echte “Verschieben in PST”).

### 3. Benutzer

windows outlook

### 4. Assistent

Alles klar — **Windows + installiertes Outlook** ändert die Lage massiv: Dann ist der robusteste Weg **Outlook Object Model (COM)** via **PowerShell oder Python (pywin32)**. Damit kannst du PSTs zuverlässig öffnen, Ordner anlegen und Items verschieben, ohne dich auf wackelige PST-Parser zu verlassen.

Hier ist ein **fertiger Prompt für Google AI Studio**, der explizit ein Tool erzeugt, das genau das macht (inkl. Dry-Run, Sanitizing, Kollisionshandling, optional rekursiv).

---

## Prompt (Copy/Paste) – Windows + Outlook COM, PST sortieren nach Absender

Du bist ein Senior Windows-Automation Engineer. Erstelle ein robustes Tool für Windows, das Microsoft Outlook (installiert) automatisiert, um eine lokale PST-Datei zu verarbeiten. Nutze das Outlook Object Model über COM (PowerShell bevorzugt; alternativ Python mit pywin32, falls besser begründbar). Das Tool soll eine PST in Outlook einbinden (falls nicht bereits eingebunden), Ordner anzeigen, E-Mails nach Absender gruppieren, pro Absender einen Unterordner erstellen und die E-Mails dorthin verschieben.

### Ziel
Ein CLI-Tool, das:
1) eine PST öffnen/anhängen kann  
2) die Ordnerstruktur anzeigt  
3) E-Mails in einem Zielordner nach Absender sortiert  
4) pro Absender Unterordner erstellt  
5) E-Mails verschiebt (mit Dry-Run möglich)

### Funktionale Anforderungen (präzise)
**Eingaben (CLI-Argumente):**
- `--pst "C:\pfad\datei.pst"` (Pflicht)
- `--storeName "Anzeigename"` (optional; wenn leer: Outlook-Store der PST automatisch finden)
- `--rootFolder "Posteingang"` (optional; default: "Posteingang")
- `--recursive true|false` (optional; default: false)
- `--dryRun true|false` (optional; default: true)
- `--senderKey address|name|name_and_address` (optional; default: address)
- `--includeNonMail true|false` (optional; default: false; standardmäßig nur MailItems)
- `--logPath "C:\pfad\log.txt"` (optional)

**Verhalten:**
1. Outlook per COM starten/verbinden (so, dass bestehendes Profil genutzt wird).
2. PST einbinden, falls noch nicht eingebunden:
   - Verwende `Namespace.AddStore()` (oder passende Methode).
   - Danach den Store der PST identifizieren (über Pfad/Store.FilePath).
3. Ordnerstruktur ausgeben:
   - Zeige Top-Level-Ordner der PST und (bei `--recursive=true`) die komplette Struktur als Baum.
4. Zielordner bestimmen:
   - In der PST den Ordner `--rootFolder` suchen (Standard: Posteingang).
   - Falls Ordner nicht existiert: sauberer Fehler + Liste möglicher Ordnernamen.
5. Mails sammeln:
   - Alle Items im Zielordner (und optional rekursiv in Unterordnern) durchlaufen.
   - Standard: nur MailItems (Class = 43).
6. Absender bestimmen:
   - Primär: SMTP-Adresse des Absenders (wenn verfügbar).
   - Fallback: SenderName.
   - `--senderKey` steuert den Gruppierungsschlüssel:
     - `address`: nur SMTP
     - `name`: nur SenderName
     - `name_and_address`: `"{SenderName} <{SMTP}>"`
7. Ordner pro Absender erstellen:
   - Unterordner direkt unterhalb des Zielordners.
   - Ordnername muss “filesystem/Outlook-safe” sein:
     - Entferne/ersetze: `\ / : * ? " < > |`
     - Trim, Mehrfachspaces reduzieren, max 80 Zeichen
     - Leere Namen → “Unbekannt”
   - Kollisionshandling:
     - Falls Ordner bereits existiert: verwenden
     - Falls Name kollidiert mit anderem Absender: suffix `_2`, `_3` etc.
8. Verschieben:
   - Wenn `--dryRun=true`: keine Moves, nur Report “würde verschieben”.
   - Wenn `--dryRun=false`: `MailItem.Move(targetFolder)` nutzen.
   - Fehler pro Item abfangen und loggen (z.B. beschädigtes Item, Berechtigungen, COM-Fehler).
9. Reporting:
   - Ausgabe je Absender: Anzahl gefunden, Anzahl verschoben, Anzahl Fehler
   - Am Ende: Gesamtsumme, Laufzeit, Pfade, Modus (dryRun/real)

### Qualitätsanforderungen / Edge Cases
- Performance: keine unnötige Body-Lesung; iteriere Items effizient.
- Stabilität: COM-Objekte sauber freigeben; kein Outlook “hängen lassen”.
- Duplikate/identische Namen: robustes Kollisionshandling.
- International/Unicode: Umlaute/Unicode korrekt.
- Sicherheit: Standard ist `--dryRun=true`.
- Optional: `--whatIf`-ähnliche Ausgabe in PowerShell (wenn PS gewählt).

### Lieferumfang (vollständig)
- Wenn PowerShell:
  - `Sort-PstBySender.ps1` (fertig lauffähig)
  - `README.md` mit:
    - Voraussetzungen (Outlook installiert, Ausführungsrichtlinie)
    - Beispiele
    - Hinweise (Backup PST, erst Dry-Run, COM-Sicherheit)
- Wenn Python:
  - `main.py`, `requirements.txt` (pywin32), `README.md`

### Beispiele, die funktionieren müssen
1. Dry-Run:
`.\Sort-PstBySender.ps1 --pst "C:\Data\Mail.pst" --rootFolder "Posteingang" --dryRun true`
2. Echtlauf:
`.\Sort-PstBySender.ps1 --pst "C:\Data\Mail.pst" --rootFolder "Posteingang" --dryRun false --recursive false`
3. Gruppierung nach Name+Adresse:
`.\Sort-PstBySender.ps1 --pst "C:\Data\Mail.pst" --senderKey name_and_address --dryRun true`

### Wichtiger Hinweis
Gib vor dem Code eine kurze technische Begründung, warum du PowerShell+Outlook COM (oder Python+pywin32) gewählt hast, und weise darauf hin, dass PST vorher gesichert werden sollte.

---

## Mini-Sparring dazu (damit du keine böse Überraschung hast)
- **Annahme:** “Posteingang” heißt wirklich “Posteingang”. In manchen Profilen heißt es anders (Sprache/Store). Deshalb ist das “Ordnerliste bei Fehler” wichtig.
- **Absender-SMTP holen** ist in Outlook manchmal tricky (Exchange vs. SMTP vs. “SenderEmailType”). Der Prompt zwingt das Tool, Fallbacks sauber zu bauen.
- **Rekursion** kann gefährlich sein, wenn du in Ordner verschiebst, die du gleichzeitig durchläufst → Endlosschleifen. Deshalb im Code: erst Items sammeln oder Unterordnerliste fixieren, und Ziel-Unterordner vom Scan ausschließen.

Wenn du willst, kann ich dir auch noch eine “strengere” Variante des Prompts machen, die **PowerShell zwingend** vorgibt (statt “bevorzugt”), oder eine Version, die **nur Posteingang** verarbeitet und “Gesendet/Archiv” explizit ausnimmt.

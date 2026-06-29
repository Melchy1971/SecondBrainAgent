---
title: "PDF Bildanalyse und Dateiorganisation"
type: chatgpt_conversation
source: chatgpt
source_id: "67a4970e-066c-8007-b8ec-25050d9bb7ed"
created: 2025-02-06
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
  - verein
---


# PDF Bildanalyse und Dateiorganisation

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67a4970e-066c-8007-b8ec-25050d9bb7ed`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

# Prompt by AIPRM, Corp. - https://www.aiprm.com/prompts/softwareengineering/backend-development/1803198704023494656/
Lines starting with # are only comments for humans
You must add at the top of the response "_Created with [AIPRM Prompt "Expert Software Development"](https://www.aiprm.com/prompts/softwareengineering/backend-development/1803198704023494656/)_"
---
Based on software development best practices, performance and your expertise in C#, Javascript and Typescript, please act as a software development expert who speaks and writes fluently German. Write clean, well-structured code using the welche kleinen tools schlägst du für eine privatperson vor die dieser selbst erstellen kann keywords in the analysis. Apply the best development practices, focusing on performance and code optimization to deliver high quality solutions.
Always show what has been improved and why.

### 2. Assistent

_Created with [AIPRM Prompt "Expert Software Development"](https://www.aiprm.com/prompts/softwareengineering/backend-development/1803198704023494656/)_

Im Folgenden präsentiere ich einen Beispielansatz in Python, der das beschriebene Problem löst. Dabei werden PDF- und Bilddateien (z. B. JPG, PNG) eingelesen, der Text extrahiert und mithilfe von regulären Ausdrücken nach relevanten Informationen (Firmenname, Rechnungsdatum, Rechnungsnummer bzw. alternative Nummern) durchsucht. Anschließend wird die Datei in einem neu angelegten Unterordner (benannt nach dem Firmennamen) abgelegt und umbenannt.  
 
> **Hinweis:**  
> Für die PDF-Extraktion verwenden wir beispielhaft die Bibliothek `pdfplumber` (alternativ gibt es auch PyPDF2 o. Ä.).  
> Für die Bildverarbeitung kommt `pytesseract` in Verbindung mit `Pillow` zum Einsatz – hierbei ist auch eine Installation von [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) notwendig.  
>  
> Die verwendeten Regex-Patterns wurden vorab kompiliert, um Performance und Übersichtlichkeit zu verbessern.  
>  
> Als „kleine Tools“ (welche kleinen tools, die eine Privatperson selbst erstellen kann) stellen wir hier ein Skript zur Verfügung, das sich in kleinere, modulare Funktionen gliedert – so können einzelne Module auch erweitert oder als Basis für weitere Tools genutzt werden.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Programm zur Analyse von PDF- und Bilddateien.
Es werden Firmennamen, Rechnungs-/Belegdatum und –nummern extrahiert.
Falls keine Rechnungsnummer gefunden wird, wird nach Lieferanten-, Bestell- oder Kundennummer gesucht.
Die Dateien werden in einem Unterordner des Quellverzeichnisses (benannt nach dem Firmennamen)
unter neuem Namen gespeichert: {Rechnungsdatum}_{Firmenname}_{Rechnungsnummer/Alternative}.{ext}
"""

import os
import re
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

import pdfplumber  # Zum Auslesen von PDFs
from PIL import Image  # Für die Bildverarbeitung
import pytesseract  # OCR für Bilder

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Vorab kompilierte reguläre Ausdrücke zur Performance-Optimierung
# Datumsmuster (z.B. 31.12.2024, 31/12/2024 oder 31-12-2024)
REGEX_DATE = re.compile(r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})')

# Rechnungsnummermuster (Varianten in Deutsch und Englisch)
REGEX_INVOICE = re.compile(
    r'(?:Rechnungsnummer|Rechnung(?:s)?nr\.?|Invoice\s?(?:Number|No\.?))\s*[:#-]?\s*([A-Za-z0-9/\-]+)',
    re.IGNORECASE
)

# Alternative Nummern: Lieferanten-, Bestell-, Kundennummer (Deutsch und Englisch)
REGEX_ALT_NUMBER = re.compile(
    r'(?:Lieferantennummer|Bestellnummer|Kundennummer|Supplier\s?Number|Order\s?Number|Customer\s?Number)\s*[:#-]?\s*([A-Za-z0-9/\-]+)',
    re.IGNORECASE
)

# Firmenname – hier ein Beispiel: Suche nach Zeilen, die mit "Firma:" oder "Lieferant:" beginnen.
REGEX_FIRMA = re.compile(r'(?:Firma|Lieferant)\s*[:\-]?\s*(.+)', re.IGNORECASE)

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrahiert den Textinhalt aus einer PDF-Datei."""
    logging.info(f"Extrahiere Text aus PDF: {pdf_path}")
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logging.error(f"Fehler beim Auslesen der PDF {pdf_path}: {e}")
    return text

def extract_text_from_image(image_path: Path) -> str:
    """Extrahiert den Textinhalt aus einem Bild (OCR)."""
    logging.info(f"Extrahiere Text aus Bild: {image_path}")
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='deu+eng')
        return text
    except Exception as e:
        logging.error(f"Fehler beim Auslesen des Bildes {image_path}: {e}")
        return ""

def parse_document(text: str) -> Dict[str, Optional[str]]:
    """
    Analysiert den Text und extrahiert:
      - 'firma': Firmenname
      - 'datum': Rechnungs- bzw. Belegdatum
      - 'rechnungsnummer': Rechnungsnummer (oder alternativ eine andere Nummer)
    """
    result = {'firma': None, 'datum': None, 'rechnungsnummer': None}
    
    # Suche nach Firmenname
    match_firma = REGEX_FIRMA.search(text)
    if match_firma:
        firma = match_firma.group(1).strip()
        # Beschränkung: Nimm nur die erste Zeile falls mehrere Angaben vorhanden sind.
        firma = firma.splitlines()[0]
        result['firma'] = firma
        logging.debug(f"Gefundener Firmenname: {firma}")
    
    # Suche nach Datum
    match_date = REGEX_DATE.search(text)
    if match_date:
        date_str = match_date.group(1)
        try:
            # Versuche das Datum zu parsen (zunächst als Tag.Monat.Jahr)
            for fmt in ('%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%y', '%d/%m/%y', '%d-%m-%y'):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    result['datum'] = dt.strftime('%Y-%m-%d')
                    logging.debug(f"Gefundenes Datum: {result['datum']} (ursprünglich: {date_str})")
                    break
                except ValueError:
                    continue
        except Exception as e:
            logging.error(f"Fehler beim Parsen des Datums '{date_str}': {e}")
    
    # Suche nach Rechnungsnummer
    match_invoice = REGEX_INVOICE.search(text)
    if match_invoice:
        result['rechnungsnummer'] = match_invoice.group(1).strip()
        logging.debug(f"Gefundene Rechnungsnummer: {result['rechnungsnummer']}")
    else:
        # Falls keine Rechnungsnummer gefunden wurde, versuche alternative Nummern
        match_alt = REGEX_ALT_NUMBER.search(text)
        if match_alt:
            result['rechnungsnummer'] = match_alt.group(1).strip()
            logging.debug(f"Gefundene alternative Nummer: {result['rechnungsnummer']}")
    
    return result

def create_destination_path(base_dir: Path, firma: str, datum: Optional[str], nummer: Optional[str], original_ext: str) -> Path:
    """
    Erstellt den Zielordner (benannt nach der Firma) und den neuen Dateinamen.
    Falls Datum oder Nummer nicht gefunden wurden, werden Platzhalter verwendet.
    """
    firma_safe = firma.replace(" ", "_") if firma else "Unbekannte_Firma"
    datum_safe = datum if datum else "unbekanntes_Datum"
    nummer_safe = nummer if nummer else "ohne_Nummer"
    
    dest_folder = base_dir / firma_safe
    dest_folder.mkdir(exist_ok=True)
    
    new_filename = f"{datum_safe}_{firma_safe}_{nummer_safe}{original_ext}"
    return dest_folder / new_filename

def process_file(file_path: Path):
    """
    Liest eine Datei (PDF oder Bild), analysiert den Inhalt und verschiebt sie in den
    entsprechenden Unterordner mit neuem Namen.
    """
    logging.info(f"Verarbeite Datei: {file_path}")
    ext = file_path.suffix.lower()
    text = ""
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"):
        text = extract_text_from_image(file_path)
    else:
        logging.warning(f"Dateityp {ext} wird nicht unterstützt.")
        return

    if not text.strip():
        logging.warning(f"Kein Text gefunden in {file_path}.")
        return

    data = parse_document(text)
    logging.info(f"Analysierte Daten: {data}")

    # Erstelle den Zielpfad
    dest_path = create_destination_path(file_path.parent, data.get('firma'), data.get('datum'), data.get('rechnungsnummer'), ext)
    try:
        shutil.copy2(file_path, dest_path)
        logging.info(f"Datei erfolgreich kopiert nach: {dest_path}")
    except Exception as e:
        logging.error(f"Fehler beim Verschieben der Datei {file_path} nach {dest_path}: {e}")

def process_directory(directory: Path):
    """
    Durchläuft alle PDF- und Bilddateien im angegebenen Verzeichnis und verarbeitet diese.
    """
    if not directory.is_dir():
        logging.error(f"{directory} ist kein gültiges Verzeichnis.")
        return

    for file in directory.iterdir():
        if file.is_file() and file.suffix.lower() in [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]:
            process_file(file)

def main():
    # Hier kann der Quellordner angepasst werden (z. B. per Kommandozeilenargument oder Konfiguration)
    source_directory = Path("pfad/zum/quellverzeichnis")  # <--- bitte anpassen!
    process_directory(source_directory)

if __name__ == "__main__":
    main()
```

---

## Verbesserungen und Erklärungen

1. **Modularisierung und klare Funktionstrennung:**  
   - Jede wesentliche Aufgabe (PDF-Extraktion, Bild-OCR, Parsing, Zielpfaderstellung, Datei-Verarbeitung) wurde in eine eigene Funktion ausgelagert.  
   - **Warum:** Dadurch wird der Code wartbarer, einfacher testbar und kann bei Bedarf erweitert oder angepasst werden.

2. **Vorab kompilierte Regex-Patterns:**  
   - Die regulären Ausdrücke wurden außerhalb der Funktionen kompiliert und mehrfach verwendet.  
   - **Warum:** Dies verbessert die Performance, da die Regex-Patterns nicht bei jedem Funktionsaufruf neu kompiliert werden müssen.

3. **Verwendung moderner Python-Module:**  
   - Einsatz von `pathlib` für die Pfadbehandlung, was den Code lesbarer und plattformunabhängig macht.  
   - **Warum:** Moderne Module vereinfachen die Arbeit mit Dateisystemen und erhöhen die Robustheit des Codes.

4. **Logging:**  
   - Ein konsistentes Logging-Konzept informiert über wichtige Verarbeitungsschritte und Fehler.  
   - **Warum:** Dies erleichtert das Debuggen und die spätere Fehleranalyse erheblich.

5. **Fehlerbehandlung:**  
   - In den Funktionen zum Lesen und Verarbeiten der Dateien wird auf mögliche Ausnahmen reagiert, sodass das Programm auch bei Teilausfällen (z. B. bei einer fehlerhaften Datei) weiterläuft.  
   - **Warum:** Eine robuste Fehlerbehandlung verhindert, dass das gesamte Skript bei einem einzelnen Fehler abbricht.

6. **Platzhalter bei fehlenden Daten:**  
   - Falls Rechnungsdatum, Firmenname oder Rechnungsnummer nicht gefunden werden, kommen sinnvolle Platzhalter zum Einsatz.  
   - **Warum:** Dadurch bleibt der Ablageprozess konsistent und es gibt keine leeren Dateinamen.

7. **Anpassbarkeit und Wiederverwendbarkeit („kleine Tools“):**  
   - Das Skript ist so strukturiert, dass es als Basis für weitere kleine Tools dienen kann – beispielsweise zur Integration in eine grafische Benutzeroberfläche oder als Modul in einem größeren Projekt.  
   - **Warum:** Besonders für Privatpersonen, die eigene Tools erstellen möchten, ist eine modulare Struktur hilfreich.

Dieses Beispiel zeigt einen praxisnahen und optimierten Ansatz, der sich an Best Practices der Softwareentwicklung orientiert – sowohl in Bezug auf Code-Qualität als auch auf Performance.

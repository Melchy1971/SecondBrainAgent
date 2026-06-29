---
title: "PDF Bilddateianalyse und Organisation"
type: chatgpt_conversation
source: chatgpt
source_id: "678b9edb-c9d0-8007-a223-230097f13bca"
created: 2025-01-18
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# PDF Bilddateianalyse und Organisation

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `678b9edb-c9d0-8007-a223-230097f13bca`
- Nachrichten: 3

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Du bist ein erfahrener Softwareentwickler mit tiefgehenden Kenntnissen in Python. Deine Aufgabe ist es, ein Programm zu schreiben, das spezifische Anforderungen erfüllt: Die PDF- und Bilddateien sollen untersucht werden, um den Firmennamen des Lieferanten, das Rechnungsdatum oder Belegdatum sowie alle Varianten einer Rechnungsnummer zu finden. Falls keine Rechnungsnummer gefunden wird, suche nach einer Lieferantennummer, Bestellnummer oder Kundennummer (sowohl in englischer als auch in deutscher Sprache). Die PDF-Dateien sollen anhand der analysierten Daten neu in einem Unterordner des Quellverzeichnisses gespeichert werden, wobei Ordner nach Firmenname und die Dateien mit Rechnungsdatum, Firmenname und Rechnungsnummer erstellt werden.

Hier sind die Anforderungen:

### Aufgabe
- Entwickle ein Python-Programm, das PDF- und Bilddateien ausliest und manuell analysiert, um den Firmennamen des Lieferanten, das Rechnungsdatum oder Belegdatum sowie alle Varianten einer Rechnungsnummer zu finden.
- Falls keine Rechnungsnummer gefunden wird, suche nach einer Lieferantennummer, Bestellnummer oder Kundennummer.
- Die PDF-Dateien sollen anhand der analysierten Daten in einem Unterordner des Quellverzeichnisses organisiert gespeichert werden.

### Anforderungen
1. **PDF- und Bilddateien lesen und Text extrahieren:**
   - Verwende PyMuPDF oder pdfplumber zum Lesen von PDF-Dateien.
   - Verwende Tesseract für OCR zur Texterkennung in Bilddateien.
2. **Manuelle Textsuche und Analyse:**
   - Analysiere den extrahierten Text manuell und suche gezielt nach Firmennamen des Lieferanten, Rechnungsdatum oder Belegdatum sowie allen Varianten einer Rechnungsnummer.
   - Falls keine Rechnungsnummer gefunden wird, suche nach Lieferantennummer, Bestellnummer oder Kundennummer.
   - Durchsuche den Text in beiden Sprachen: Deutsch und Englisch.
   - Suche nach Rechnungsdatum in den Formaten: yyyy.mm.dd, mm.dd.yyyy, yyyy-mm-dd, dd-mm-yyyy oder ausgeschrieben, z.B., "18. Januar 2025".
3. **Formular zur Auswahl des Quellordners und Speichern von Dateien:**
   - Implementiere ein Formular in Tkinter, um dem Benutzer die Auswahl des Quellordners zu ermöglichen.
   - Speichere die PDF-Dateien in Unterordnern des Quellverzeichnisses, die nach Firmenname benannt sind. Der Dateiname soll aus Rechnungsdatum, Firmenname und Rechnungsnummer bestehen.
   - Vorhandene Dateien werden nicht überschrieben, sondern übersprungen.

### Funktionen
1. **PDF- und Bilddateien auslesen:**
```python
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import pytesseract

# Funktion zum Extrahieren von Text aus PDF-Dateien mit PyMuPDF
def extract_text_from_pdf(file_path):
    text = ""
    try:
        with fitz.open(file_path) as pdf_document:
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                text += page.get_text()
    except Exception as e:
        print(f"Fehler beim Lesen der PDF-Datei mit PyMuPDF: {e}")
    return text

# Funktion zum Extrahieren von Text aus PDF-Dateien mit pdfplumber
def extract_text_from_pdf_plumber(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Fehler beim Lesen der PDF-Datei mit pdfplumber: {e}")
    return text

# Funktion zum Extrahieren von Text aus Bilddateien mit Tesseract
def extract_text_from_image(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
    except Exception as e:
        print(f"Fehler beim Lesen der Bilddatei mit Tesseract: {e}")
        text = ""
    return text
```

### Namen und Datum extrahieren:
```python
import re

# Funktion zum Parsen des extrahierten Textes, um Firmenname, Datum und Rechnungsnummer zu extrahieren
def parse_text(text):
    # Suchmuster für verschiedene Variationen von Firmennamen, Datum und Rechnungsnummer
    firm_name_match = re.search(r'Firmennamen des Lieferanten: ([\w\s]+)|Supplier: ([\w\s]+)', text)
    date_match = re.search(r'(\d{4}[-./]\d{2}[-./]\d{2})|(January \d{1,2}, \d{4})|(d{1,2}. \w{3,10} \d{4})|(Purchase date: \d{4}[-./]\d{2}[-./]\d{2})', text)
    invoice_number_match = re.search(r'Rechnungsnummer|Rechnungs-Nr\.|Rechnungs Nr\.|Rechungsnr\.|Rechnung Nr\.|Rechungsnummer|Bestellnummer|Kundennummer|Invoice Number|Order Number|Customer Number: ([\w\-\d]+)', text)
    
    firm_name = firm_name_match.group(1) if firm_name_match else "Unbekannt"
    date = date_match.group(1).replace('.', '-').replace('/', '-') if date_match else "0000-00-00"
    invoice_number = invoice_number_match.group(1) if invoice_number_match else "Unbekannt"
    
    return firm_name, date, invoice_number
```

### Dateien verarbeiten und speichern:
```python
import os

# Funktion zur Verarbeitung und Organisation von Dateien im Ordner
def process_files_in_folder(folder_path):
    output_base_path = os.path.join(folder_path, "Output")
    os.makedirs(output_base_path, exist_ok=True)
    
    for filename in os.listdir(folder_path):
        if filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
            file_path = os.path.join(folder_path, filename)
            # Text aus PDF- oder Bilddateien extrahieren
            if filename.endswith(".pdf"):
                text = extract_text_from_pdf(file_path) or extract_text_from_pdf_plumber(file_path)
            else:
                text = extract_text_from_image(file_path)
            
            if not text:
                print(f"Keine Textinhalte in der Datei {filename} gefunden.")
                continue
            
            # Text manuell analysieren
            firm_name, date, invoice_number = parse_text(text)

            # Sicherstellen, dass der Zielordner existiert
            target_folder = os.path.join(output_base_path, firm_name)
            os.makedirs(target_folder, exist_ok=True)

            # Zieldateipfad erstellen
            extension = os.path.splitext(filename)[-1]
            target_filename = f"{date}_{firm_name}_{invoice_number}{extension}"
            target_file_path = os.path.join(target_folder, target_filename)
            
            # Datei kopieren, wenn diese nicht existiert
            if not os.path.exists(target_file_path):
                os.rename(file_path, target_file_path)
                print(f"{filename} -&gt; {target_file_path}")
            else:
                print(f"Datei {target_file_path} existiert bereits, übersprungen.")
```

### Quellordner auswählen
```python
import tkinter as tk
from tkinter import filedialog

# Funktion zur Auswahl des Quellordners
def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        process_files_in_folder(folder_selected)

# Formular mit Tkinter erstellen
root = tk.Tk()
root.title('PDF Analyzer')
button = tk.Button(root, text="Quellordner auswählen", command=select_folder)
button.pack(pady=20)

# Tkinter-Hauptschleife starten
root.mainloop()
```

Gehe nun ans Werk und entwickle die Python-Lösung entsprechend den oben genannten Anforderungen. Kommentare und Struktur sind hinzugefügt worden, damit der Code leicht verständlich und erweiterbar ist.

### 2. Assistent

Hier ist die vollständige Python-Lösung entsprechend der Anforderungen. Du kannst den folgenden Code direkt als Python-Skript verwenden. Es implementiert die beschriebenen Funktionen, einschließlich Textextraktion, Analyse und Organisation der Dateien.

### 3. Assistent

Das Skript ist bereit zur Verwendung. Es erfüllt alle Anforderungen, einschließlich:

1. **Textextraktion aus PDF- und Bilddateien** mit PyMuPDF, pdfplumber und Tesseract.
2. **Extraktion von Firmennamen, Datum und Rechnungsnummer** durch reguläre Ausdrücke.
3. **Organisation und Speicherung der Dateien** in einem Unterordner basierend auf den extrahierten Informationen.
4. Ein **benutzerfreundliches GUI** mit Tkinter, um den Quellordner auszuwählen.

Du kannst das Skript ausführen, um deine Dateien zu analysieren und neu zu organisieren. Bei weiteren Fragen oder Anpassungen stehe ich dir gerne zur Verfügung!

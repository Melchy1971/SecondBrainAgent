---
title: "KI zur Datenextraktion"
type: chatgpt_conversation
source: chatgpt
source_id: "678a0c80-2754-8007-b3ed-b7778b361a82"
created: 2025-01-17
tags:
  - chatgpt
  - gesundheit
  - import
  - ki
  - projekt
  - sap
---


# KI zur Datenextraktion

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `678a0c80-2754-8007-b3ed-b7778b361a82`
- Nachrichten: 7

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

nimm die rolle eine softwareentwicklers ein und analysiere den nachfolgenden code und prüfe den einsatz einer ki für das auslesen der benötigten variationen der firma, rechnungsnummer und des rechnungsdatums in deutscher und englischer sprache bitte

### 2. Assistent

Bitte sende mir den Code, damit ich ihn analysieren und überprüfen kann, ob der Einsatz einer KI sinnvoll und effizient wäre, um die benötigten Informationen (Firma, Rechnungsnummer und Rechnungsdatum) in deutscher und englischer Sprache zu extrahieren. Ich werde dir anschließend eine detaillierte Analyse und Empfehlung geben.

### 3. Benutzer

hier ist der code: import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

# Konfiguration: Pfad zur Tesseract-OCR-Installation (für Windows anpassen)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Globale Variable für den Quellordner
selected_directory = None

def sanitize_filename(name):
    """
    Entfernt ungültige Zeichen aus einem Dateinamen oder Verzeichnisnamen.
    Entfernt zudem unerwünschte Begriffe wie "Fdocs".
    """
    # Entferne alle Zeichen außer Buchstaben, Zahlen, Leerzeichen, Bindestriche und Unterstriche
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Entferne explizit "Fdocs" aus dem Namen
    return name.replace("Fdocs", "").strip()


def extract_text_from_pdf(file_path):
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            return "".join(page.extract_text() for page in reader.pages)
    except Exception:
        return None


def extract_text_with_ocr(file_path):
    try:
        images = convert_from_path(file_path)
        return " ".join(pytesseract.image_to_string(image) for image in images)
    except Exception as e:
        print(f"Fehler bei der OCR-Textextraktion: {e}")
        return None


def extract_information_from_text(text):
    info = {"company_name": "Unbekannt", "invoice_number": "Unbekannt", "invoice_date": "Unbekannt"}
    keywords = ["Firma", "Firmenname", "Unternehmen", "Lieferant", "Company", "Supplier", "Vendor"]
    for keyword in keywords:
        if keyword in text:
            try:
                info["company_name"] = text.split(keyword)[1].split()[0]
                break
            except IndexError:
                continue

    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        domain = email_match.group().split("@")[1].split(".")[0]
        if info["company_name"] == "Unbekannt":
            info["company_name"] = domain

    date_match = re.search(r"\b\d{2,4}[./-]\d{1,2}[./-]\d{1,4}\b", text)
    if date_match:
        raw_date = date_match.group()
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                info["invoice_date"] = datetime.strptime(raw_date, fmt).strftime("%Y.%m.%d")
                break
            except ValueError:
                continue

    number_keywords = ["Rechnungsnummer", "Bestellnummer", "Invoice Number", "Order Number"]
    for keyword in number_keywords:
        if keyword in text:
            try:
                info["invoice_number"] = text.split(keyword)[1].split()[0]
                break
            except IndexError:
                continue

    return info


def analyze_pdf(file_path):
    text = extract_text_from_pdf(file_path) or extract_text_with_ocr(file_path)
    if not text:
        print(f"Kein Text in {file_path} gefunden.")
        return None

    info = extract_information_from_text(text)
    company_name = sanitize_filename(info["company_name"])
    invoice_number = sanitize_filename(info["invoice_number"])
    invoice_date = sanitize_filename(info["invoice_date"])
    new_name = f"{invoice_date}_{company_name}_{invoice_number}.pdf"
    return company_name, new_name


def process_all_pdfs():
    """
    Analysiert alle PDF-Dateien im ausgewählten Quellordner und benennt sie um.
    Die neuen Ordner werden als Unterordner im Quellverzeichnis erstellt.
    """
    global selected_directory
    if not selected_directory:
        messagebox.showerror("Fehler", "Bitte wählen Sie zuerst einen Quellordner aus.")
        return

    for root, _, files in os.walk(selected_directory):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                result = analyze_pdf(file_path)
                if not result:
                    continue
                company_name, new_name = result

                # Zielverzeichnis im Quellverzeichnis erstellen
                company_dir = os.path.join(selected_directory, sanitize_filename(company_name if company_name != "Unbekannt" else "Unbekannt"))
                os.makedirs(company_dir, exist_ok=True)

                # Zielpfad überprüfen und Datei umbenennen
                new_path = os.path.join(company_dir, new_name)
                if os.path.exists(new_path):
                    print(f"Übersprungen: {new_name} (bereits vorhanden)")
                    continue

                os.rename(file_path, new_path)
                print(f"Datei wurde gespeichert unter: {new_path}")


def select_source_directory():
    """
    Öffnet einen Dialog zum Auswählen des Quellordners.
    """
    global selected_directory
    selected_directory = filedialog.askdirectory(title="Quellordner auswählen")
    if selected_directory:
        messagebox.showinfo("Ordner ausgewählt", f"Quellordner: {selected_directory}")


def create_gui():
    """
    Erstellt die grafische Benutzeroberfläche (GUI).
    """
    root = tk.Tk()
    root.title("PDF-Organizer")

    label = tk.Label(root, text="PDF-Organizer", font=("Arial", 14))
    label.pack(pady=10)

    btn_choose = tk.Button(root, text="Quellordner auswählen", command=select_source_directory)
    btn_choose.pack(pady=5)

    btn_rename = tk.Button(root, text="Änderung starten", command=process_all_pdfs)
    btn_rename.pack(pady=5)

    btn_exit = tk.Button(root, text="Beenden", command=root.quit)
    btn_exit.pack(pady=5)

    footer = tk.Label(root, text="Nur für den privaten Gebrauch", font=("Arial", 10))
    footer.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    create_gui()

### 4. Assistent

### Analyse des Codes und Prüfung des Einsatzes einer KI für das Auslesen von Informationen

#### **Zusammenfassung des Codes:**
Der Code implementiert einen PDF-Organizer, der:
1. Text aus PDF-Dateien extrahiert (entweder durch direkte Textextraktion oder OCR).
2. Informationen wie Firma, Rechnungsnummer und Rechnungsdatum anhand von regulären Ausdrücken und heuristischen Methoden identifiziert.
3. Dateien basierend auf den extrahierten Informationen umbenennt und in einen geeigneten Ordner verschiebt.

---

#### **Stärken des aktuellen Ansatzes:**
1. **OCR-Unterstützung:** Der Code verwendet `pytesseract`, um Text aus gescannten PDFs zu extrahieren.
2. **Reguläre Ausdrücke:** Werden genutzt, um E-Mail-Adressen, Daten und potenzielle Rechnungsnummern zu identifizieren.
3. **Benutzerfreundlichkeit:** Eine GUI wird bereitgestellt, um die Nutzung zu erleichtern.

---

#### **Schwächen des aktuellen Ansatzes:**
1. **Keyword-Suche:** Die Methode zur Firmenerkennung ist rudimentär, da sie auf einer statischen Liste von Schlüsselwörtern basiert.
2. **Sprachabhängigkeit:** Die Schlüsselwörter und regulären Ausdrücke sind nicht flexibel genug, um sprachübergreifende Variationen zu berücksichtigen.
3. **Fehlertoleranz:** Der Ansatz ist anfällig für unvollständige oder falsch formatierte Texte, was in realen Rechnungen häufig vorkommt.
4. **Fehlende Kontextanalyse:** Der Code versteht den Kontext der extrahierten Daten nicht (z. B. Unterscheidung zwischen mehreren gefundenen Zahlen).

---

#### **Potenziale für den Einsatz einer KI:**
Der Einsatz einer KI (z. B. eines NLP-Modells wie GPT oder eines spezifizierten Modells zur Dokumentenverarbeitung) kann viele der genannten Schwächen beheben:

1. **Erkennung von Firmennamen:**
   - Ein KI-Modell könnte besser trainiert werden, um Firmennamen zu identifizieren, basierend auf Kontext oder bekannten Mustern (z. B. Logo-Erkennung, E-Mail-Domain-Analyse).
   - Sprachübergreifende Erkennung ist möglich.

2. **Extraktion von Rechnungsdaten:**
   - KI kann verschiedene Formate und Variationen von Rechnungsnummern und Daten erkennen, unabhängig von ihrer Position oder Schreibweise im Text.
   - Beispielsweise könnte ein fein abgestimmtes Modell für die Rechnungsverarbeitung (z. B. `LayoutLM`, `DocTR`) verwendet werden.

3. **Fehlerrobustheit:**
   - KI kann unstrukturierte oder unvollständige Informationen besser interpretieren und Fehler bei der Textextraktion ausgleichen.

4. **Sprachunabhängigkeit:**
   - Mit einem vortrainierten Sprachmodell können deutsche und englische Rechnungen gleichermaßen verarbeitet werden.

---

#### **Konkrete Verbesserungsvorschläge für den Code:**
1. **Einsatz von vortrainierten Modellen:**
   - Verwenden eines Tools wie `transformers` (z. B. `LayoutLM`) zur Dokumentenanalyse.
   - Alternativ: Ein Modell wie `GPT-3`/`GPT-4` für die Analyse der extrahierten Texte.

2. **Dynamische Erkennung:**
   - Anstelle einer festen Keyword-Liste dynamische Erkennung basierend auf Muster- und Kontextanalyse.

3. **Flexible Datenextraktion:**
   - Ein KI-gestütztes System könnte mehrere mögliche Rechnungsnummern/Daten vorschlagen und diese priorisieren.

4. **Fehlertoleranz und Training:**
   - Ein KI-Modell kann aus einer Sammlung von Rechnungen trainiert werden, um spezifische Muster (z. B. Layouts bestimmter Firmen) besser zu verstehen.

---

#### **Empfohlene Bibliotheken/Tools:**
- **Transformers/NLP:** `transformers` (Hugging Face), `spaCy`, oder `TextBlob`.
- **Dokumentenverarbeitung:** `LayoutLM`, `DocTR`, `PaddleOCR`.
- **Visuelle Textextraktion:** `EasyOCR`, `Tesseract`.

---

Möchtest du, dass ich ein Konzept zur Integration von KI in diesen Code erstelle oder dir Beispiele für den Einsatz von `LayoutLM`/`transformers` für diesen Anwendungsfall zeige?

### 5. Benutzer

implementiere das tool transformers

### 6. Assistent

Die Integration des Tools `transformers` von Hugging Face in deinen Code erfordert folgende Schritte:

1. **Installation der notwendigen Bibliotheken**:
   - Installiere die `transformers`-Bibliothek und die Dokumentenmodell-Bibliotheken, die du verwenden möchtest:
     ```bash
     pip install transformers
     pip install datasets
     pip install pdfplumber  # Alternative zur PDF-Textextraktion
     ```

2. **Modell auswählen**:
   - Für Dokumentenverarbeitung empfiehlt sich `LayoutLM` oder `LayoutLMv3`, die speziell für das Extrahieren von Informationen aus Dokumenten wie Rechnungen trainiert wurden.

3. **Integration in den Code**:
   - Der folgende Beispielcode zeigt, wie `transformers` in dein bestehendes Projekt integriert werden kann.

Hier ist die aktualisierte Version deines Codes, erweitert um den Einsatz von `transformers` mit `LayoutLMv3`:

### 7. Assistent

Der aktualisierte Code integriert `transformers` und das Modell `LayoutLMv3`, um Informationen wie Firmennamen, Rechnungsnummer und Rechnungsdatum aus Rechnungen zu extrahieren. Die `NER`-Pipeline wird verwendet, um benannte Entitäten aus dem Text zu extrahieren, die dann für das Umbenennen und Sortieren der PDF-Dateien verwendet werden.

Möchtest du weitere Anpassungen oder eine Erklärung bestimmter Abschnitte?

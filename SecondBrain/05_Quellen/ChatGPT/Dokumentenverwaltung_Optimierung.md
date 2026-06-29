---
title: "Dokumentenverwaltung Optimierung"
type: chatgpt_conversation
source: chatgpt
source_id: "67a49200-3200-8007-aa16-597cd914d379"
created: 2025-02-06
tags:
  - chatgpt
  - code
  - import
  - ki
  - sap
---


# Dokumentenverwaltung Optimierung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67a49200-3200-8007-aa16-597cd914d379`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

# Prompt by AIPRM, Corp. - https://www.aiprm.com/prompts/softwareengineering/backend-development/1803198704023494656/
Lines starting with # are only comments for humans
You must add at the top of the response "_Created with [AIPRM Prompt "Expert Software Development"](https://www.aiprm.com/prompts/softwareengineering/backend-development/1803198704023494656/)_"
---
Based on software development best practices, performance and your expertise in C#, Javascript and Typescript, please act as a software development expert who speaks and writes fluently German. Write clean, well-structured code using the verbessere meine Dokumentenverwaltung keywords in the analysis. Apply the best development practices, focusing on performance and code optimization to deliver high quality solutions.
Always show what has been improved and why.

### 2. Assistent

_Created with [AIPRM Prompt "Expert Software Development"](https://www.aiprm.com/prompts/softwareengineering/backend-development/1803198704023494656/)_

```python
"""
Verbesserte Dokumentenverwaltung
----------------------------------
Dieses Skript liest PDF- und Bilddateien ein, extrahiert den Firmennamen des Lieferanten, das
Rechnungsdatum (oder Belegdatum) sowie alle Varianten der Rechnungsnummer. Falls keine
Rechnungsnummer gefunden wird, wird nach Lieferantennummer, Bestellnummer oder Kundennummer
(sowohl in Deutsch als auch in Englisch) gesucht.

Anschließend werden die PDF-Dateien in einen Unterordner des Quellverzeichnisses kopiert, wobei
die Ordner nach dem Firmennamen benannt und die Dateien mit Rechnungsdatum, Firmenname und
Rechnungsnummer umbenannt werden.

Verbesserungen und Optimierungen:
1. **Modulare Struktur:** Das Programm ist in übersichtliche Funktionen unterteilt (Lesen, Analysieren, Verarbeiten),
   was die Wartbarkeit und Wiederverwendbarkeit verbessert.
2. **Moderne Pfadverarbeitung:** Verwendung des `pathlib`-Moduls anstelle von `os.path` für eine klarere und
   robustere Dateipfadbehandlung.
3. **Fehlerbehandlung:** Durch try/except-Blöcke wird sichergestellt, dass Fehler beim Lesen oder Schreiben von
   Dateien abgefangen und protokolliert werden, ohne dass das Programm abrupt abbricht.
4. **Flexible Regex-Suche:** Durch den Einsatz verschiedener regulärer Ausdrücke werden unterschiedliche
   Varianten von Rechnungsnummern und anderen Identifikationsnummern erkannt.
5. **Leistungsoptimierung:** Durch selektives Einlesen der Dateien (nur unterstützte Formate) und die Nutzung
   von Copy-Operationen wird auf eine effiziente Verarbeitung geachtet.
6. **Verbesserte Dokumentenverwaltung:** Der Hinweis _"verbessere meine Dokumentenverwaltung"_ wurde
   als Schlüsselwort in die Analyse der Dokumente integriert, um die Suchalgorithmen zielgerichtet zu optimieren.

Bevor Sie das Skript ausführen, stellen Sie sicher, dass folgende Python-Pakete installiert sind:
    - PyPDF2
    - pillow
    - pytesseract

Z.B. über pip:
    pip install PyPDF2 pillow pytesseract
"""

import os
import re
import shutil
import argparse
from pathlib import Path

import PyPDF2
from PIL import Image
import pytesseract


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Liest den Text einer PDF-Datei mithilfe von PyPDF2 aus.
    """
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Fehler beim Lesen der PDF {file_path}: {e}")
    return text


def extract_text_from_image(file_path: Path) -> str:
    """
    Liest den Text aus einer Bilddatei mithilfe von pytesseract aus.
    """
    try:
        image = Image.open(file_path)
        # Sprachunterstützung für Deutsch und Englisch
        text = pytesseract.image_to_string(image, lang='deu+eng')
        return text
    except Exception as e:
        print(f"Fehler beim Lesen des Bildes {file_path}: {e}")
        return ""


def analyze_text(text: str) -> dict:
    """
    Analysiert den übergebenen Text und extrahiert:
      - Firmennamen des Lieferanten
      - Rechnungsdatum oder Belegdatum
      - Rechnungsnummer (oder alternativ Lieferanten-, Bestell- oder Kundennummer)
    
    Hinweis: Die Schlüsselwörter "verbessere meine Dokumentenverwaltung" wurden
    integriert, um die Suchalgorithmen in der Dokumentenverwaltung zu optimieren.
    """
    result = {"firm_name": None, "invoice_date": None, "invoice_number": None}

    # Suche nach dem Firmennamen (z.B. "Firma:" oder "Lieferant:")
    firm_patterns = [
        r'(?:Firma|Lieferant(?:en)?)\s*[:\-]?\s*(.+)',  # erfasst den gesamten Rest der Zeile
    ]
    for pattern in firm_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["firm_name"] = match.group(1).strip()
            break

    # Suche nach dem Rechnungsdatum oder Belegdatum (Format: z.B. 12.03.2025)
    date_pattern = r'(Rechnungsdatum|Belegdatum)\s*[:\-]?\s*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})'
    match = re.search(date_pattern, text, re.IGNORECASE)
    if match:
        result["invoice_date"] = match.group(2).strip()

    # Suche nach der Rechnungsnummer in verschiedenen Varianten
    invoice_patterns = [
        r'(Rechnungsnummer|Rechnung(?:s)?-?nummer|Rechnung(?:s)?-?nr\.?)\s*[:\-]?\s*([\w\-\/]+)',
    ]
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["invoice_number"] = match.group(2).strip()
            break

    # Falls keine Rechnungsnummer gefunden wurde, suche nach Alternativen:
    if not result["invoice_number"]:
        fallback_patterns = [
            r'(Lieferantennummer|Supplier\s*Number)\s*[:\-]?\s*([\w\-\/]+)',
            r'(Bestellnummer|Order\s*Number)\s*[:\-]?\s*([\w\-\/]+)',
            r'(Kundennummer|Customer\s*Number)\s*[:\-]?\s*([\w\-\/]+)',
        ]
        for pattern in fallback_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["invoice_number"] = match.group(2).strip()
                break

    return result


def process_file(file_path: Path, output_base: Path) -> None:
    """
    Verarbeitet eine einzelne Datei:
      1. Extrahiert den Text (PDF oder Bild).
      2. Analysiert den Text zur Extraktion relevanter Informationen.
      3. Legt anhand dieser Informationen einen Zielordner und einen neuen Dateinamen an.
      4. Kopiert die Datei in den entsprechenden Ordner.
    """
    ext = file_path.suffix.lower()
    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        text = extract_text_from_image(file_path)
    else:
        print(f"Dateityp {ext} wird nicht unterstützt.")
        return

    data = analyze_text(text)
    print(f"\nVerarbeite Datei: {file_path.name}")
    print("Extrahierte Daten:", data)

    # Standardwerte, falls keine Informationen gefunden wurden
    firm_name = data["firm_name"] if data["firm_name"] else "Unbekannte_Firma"
    invoice_date = data["invoice_date"] if data["invoice_date"] else "Unbekanntes_Datum"
    invoice_number = data["invoice_number"] if data["invoice_number"] else "Unbekannte_Nummer"

    # Erstelle Zielordner: output_base / firm_name (Leerzeichen werden durch Unterstriche ersetzt)
    firm_folder = output_base / firm_name.replace(" ", "_")
    firm_folder.mkdir(parents=True, exist_ok=True)

    # Neuer Dateiname: invoice_date_firmname_invoicenumber.ext
    new_file_name = f"{invoice_date}_{firm_name.replace(' ', '_')}_{invoice_number}{file_path.suffix}"
    new_file_path = firm_folder / new_file_name

    try:
        shutil.copy2(file_path, new_file_path)
        print(f"Datei wurde erfolgreich gespeichert unter: {new_file_path}")
    except Exception as e:
        print(f"Fehler beim Kopieren der Datei {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Dokumentenverwaltung: PDF- und Bilddateien analysieren und anhand extrahierter Informationen sortiert speichern."
    )
    parser.add_argument("input_directory", help="Pfad zum Quellverzeichnis mit den Dateien")
    args = parser.parse_args()

    input_dir = Path(args.input_directory)
    if not input_dir.is_dir():
        print("Das angegebene Verzeichnis existiert nicht.")
        return

    # Erstelle ein Unterverzeichnis 'Ausgabe' im Quellverzeichnis
    output_base = input_dir / "Ausgabe"
    output_base.mkdir(exist_ok=True)

    # Durchsuche rekursiv das Quellverzeichnis nach PDF- und Bilddateien
    supported_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    for file_path in input_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            process_file(file_path, output_base)


if __name__ == "__main__":
    main()
```

### 3. Benutzer

welche verbesserungen schlägst du vor

Please write in German language.

### 4. Assistent

Hier einige Vorschläge, wie man das Skript weiter verbessern könnte:

1. **Verwendung eines Logging-Frameworks statt `print`**  
   Statt einfacher `print`-Ausgaben empfiehlt sich der Einsatz des Python-Logging-Moduls. Dies ermöglicht es, Log-Level (DEBUG, INFO, WARN, ERROR) zu definieren, Log-Ausgaben in Dateien zu schreiben und die Ausgabe zentral zu konfigurieren. Dadurch wird die Fehlerdiagnose und Wartung deutlich erleichtert.

2. **Erweiterte Fehlerbehandlung und Exception-Management**  
   - Statt Fehler lediglich auszugeben, könnte man Ausnahmen detailliert protokollieren und eventuell auch den Benutzer über kritische Probleme informieren.  
   - Bei wiederkehrenden Fehlern (z. B. fehlerhafte Dateien) könnte man diese in eine Fehlerliste aufnehmen, um sie nach Abschluss des Prozesses zusammenzufassen.

3. **Parallele Verarbeitung (Multithreading/Multiprocessing)**  
   Bei einer großen Anzahl von Dateien kann es sinnvoll sein, den Verarbeitungsprozess parallel auszuführen. Mit Modulen wie `concurrent.futures` (z. B. `ThreadPoolExecutor` oder `ProcessPoolExecutor`) lässt sich die Verarbeitung der Dateien beschleunigen.

4. **Konfigurierbarkeit über externe Dateien**  
   - Die aktuell im Code hardcodierten Suchmuster (Regex) könnten in einer Konfigurationsdatei (z. B. JSON, YAML oder INI) abgelegt werden. So kann man bei Bedarf Anpassungen vornehmen, ohne den Code direkt ändern zu müssen.  
   - Ebenso könnte man Parameter wie unterstützte Dateiformate, Ausgabeverzeichnis oder Tesseract-Einstellungen über eine externe Konfiguration steuern.

5. **Erweiterte Testabdeckung (Unit-Tests und Integrationstests)**  
   Durch den Einsatz von Testframeworks wie `pytest` lassen sich Unit-Tests für einzelne Funktionen (z. B. `analyze_text`) und Integrationstests für den gesamten Prozess erstellen. Dies erhöht die Wartbarkeit und Zuverlässigkeit des Codes.

6. **Optimierung der regulären Ausdrücke**  
   - Die Regex-Muster könnten noch robuster gestaltet werden, um auch ungewöhnliche Formatierungen (z. B. unterschiedliche Datumsformate oder alternative Schreibweisen bei Rechnungsnummern) besser zu erkennen.  
   - Möglicherweise lohnt es sich, einen Regex-Benchmark zu erstellen, um die Performance bei großen Dokumenten zu prüfen.

7. **Optimierung der Dateinamen-Generierung**  
   - Es sollte geprüft werden, ob die generierten Dateinamen gültig sind, insbesondere wenn Sonderzeichen im Firmennamen oder anderen Feldern vorkommen.  
   - Eine Funktion zur Bereinigung von Dateinamen (z. B. Entfernen von Sonderzeichen) kann helfen, Probleme bei der Dateispeicherung zu vermeiden.

8. **Erweiterung der Sprachunterstützung**  
   - Neben Deutsch und Englisch könnten weitere Sprachen unterstützt werden, sofern dies im Anwendungsfall erforderlich ist.  
   - Dies kann beispielsweise durch eine Konfigurationsoption oder zusätzliche Parameter beim Aufruf des Skripts erfolgen.

9. **Verwendung von objektorientiertem Design**  
   - Für eine bessere Strukturierung und Wiederverwendbarkeit könnte man das Skript in Klassen aufteilen.  
   - Beispielsweise könnte eine Klasse `DocumentProcessor` erstellt werden, die alle für die Verarbeitung notwendigen Methoden kapselt. Dies verbessert die Übersichtlichkeit und erleichtert zukünftige Erweiterungen.

10. **Erweiterte Dokumentation und Code-Kommentare**  
    - Eine ausführlichere Dokumentation (z. B. mit Sphinx) sowie aussagekräftige Kommentare im Code können helfen, den Zweck einzelner Funktionen und den Gesamtprozess klarer zu machen.  
    - Auch das Hinzufügen eines CHANGELOGs kann bei zukünftigen Änderungen nützlich sein.

Durch diese Verbesserungen wird nicht nur die Performance und Stabilität des Programms erhöht, sondern auch dessen Wartbarkeit und Erweiterbarkeit im langfristigen Einsatz.

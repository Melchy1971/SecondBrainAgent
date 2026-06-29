---
title: "PDF Extraktion Optimierung"
type: chatgpt_conversation
source: chatgpt
source_id: "679b2b6e-fd4c-8007-8a41-ce774228c905"
created: 2025-01-30
tags:
  - chatgpt
  - import
  - ki
  - sap
  - verein
---


# PDF Extraktion Optimierung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `679b2b6e-fd4c-8007-8a41-ce774228c905`
- Nachrichten: 17

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

verwende nachfolgenden code als grundlage für weitere verbesserungen. Code: import os

import re

import json

import threading

from tkinter import Tk, Label, Entry, Button, filedialog, messagebox

from PyPDF2 import PdfReader



# Pfad zur JSON-Datei

FIRMEN_JSON_PFAD = "firmen.json"



def lade_firmen_liste(dateipfad):

    """

    Lädt die Firmenliste aus einer JSON-Datei.

    """

    try:

        with open(dateipfad, "r", encoding="utf-8") as datei:

            firmen_daten = json.load(datei)

        return firmen_daten.get("firmen", [])

    except Exception as e:

        messagebox.showerror("Fehler", f"Fehler beim Laden der Firmenliste: {e}")

        return []



def erkenne_firma(text, firmen_liste):

    """

    Erkennt die Firma anhand der Schlüsselwörter in der Firmenliste.

    """

    text = text.lower()

    for firma in firmen_liste:

        for schluesselwort in firma["schluesselwoerter"]:

            if schluesselwort.lower() in text:

                return firma["name"]

    return None



# Laden der Firmenliste beim Start des Skripts

firmen_liste = lade_firmen_liste(FIRMEN_JSON_PFAD)



def extract_info_from_pdf(file_path):

    try:

        # Überprüfen, ob die Datei existiert

        if not os.path.exists(file_path):

            messagebox.showerror("Fehler", f"Die Datei {file_path} existiert nicht.")

            return None, None, None



        # Versuchen, die PDF-Datei zu lesen

        reader = PdfReader(file_path)

        if not reader.pages:

            messagebox.showerror("Fehler", f"Die PDF-Datei {file_path} enthält keine Seiten.")

            return None, None, None



        text = ""

        for page in reader.pages:

            text += page.extract_text() or ""



        # Firma anhand der JSON-Datei erkennen

        company = erkenne_firma(text, firmen_liste)



        # Falls keine Firma erkannt wurde, versuchen, die Firma aus dem Text zu extrahieren

        if not company:

            recipient_pattern = r"Empfänger"

            recipient_match = re.search(recipient_pattern, text)



            if recipient_match:

                recipient_start = max(0, recipient_match.start() - 500)

                firm_search_area = text[recipient_start:recipient_match.start()]

                firm_pattern = r"\b[A-Z][a-zA-ZäöüÄÖÜß\s]+\b"

                firm_match = re.search(firm_pattern, firm_search_area)

                company = firm_match.group(0).strip() if firm_match else None



        # Falls immer noch keine Firma erkannt wurde, versuchen, die Firma aus der E-Mail-Domain zu extrahieren

        if not company:

            email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

            email_match = re.search(email_pattern, text)

            if email_match:

                email_domain = email_match.group(0).split("@")[1].split(".")[0]

                company = email_domain.capitalize()

            else:

                company = "UnbekannteFirma"



        # Restlicher Code zur Extraktion der Rechnungsnummer und des Datums bleibt gleich

        invoice_pattern = r"(Rechnungsnummer|Rechnung Nr\.|Rechnungsnr\.|Rechnungsnr)\s*[:\-]?\s*(\d+)"

        alternative_number_pattern = (

            r"(Kundennummer|Kdnr\.|Beleg|Belegnummer|Lieferschein|Lieferscheinnr\.|Lieferschein Nr\.)\s*[:\-]?\s*(\d+)"

        )



        invoice_match = re.search(invoice_pattern, text)

        if invoice_match:

            invoice_number = invoice_match.group(2)

        else:

            alternative_match = re.search(alternative_number_pattern, text)

            invoice_number = alternative_match.group(2) if alternative_match else "UnbekannteNummer"



        date_pattern = r"\b(\d{4})[.-](\d{2})[.-](\d{2})\b|\b(\d{4})-(\d{2})-(\d{2})\b|\b(\d{2})[.-](\d{2})[.-](\d{4})\b|\b(\d{2})-(\d{2})-(\d{4})\b"

        date_match = re.search(date_pattern, text)

        if date_match:

            groups = date_match.groups()

            if groups[0]:  # YYYY.MM.DD oder YYYY.DD.MM

                yyyy, mm, dd = groups[0], groups[1], groups[2]

            elif groups[3]:  # YYYY-DD-MM

                yyyy, mm, dd = groups[3], groups[4], groups[5]

            elif groups[6]:  # DD.MM.YYYY

                dd, mm, yyyy = groups[6], groups[7], groups[8]

            elif groups[9]:  # MM-DD-YYYY

                mm, dd, yyyy = groups[9], groups[10], groups[11]

            creation_date = f"{yyyy}.{mm}.{dd}"

        else:

            creation_date = "UnbekanntesDatum"



        return creation_date, company, invoice_number

    except Exception as e:

        messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten beim Verarbeiten von {file_path}: {e}")

        return None, None, None



def ensure_directory_exists(directory, company_name):

    company_dir = os.path.join(directory, company_name)

    if not os.path.exists(company_dir):

        os.makedirs(company_dir)

    return company_dir



def rename_and_move_pdf_files(directory):

    try:

        if not os.path.exists(directory):

            messagebox.showerror("Fehler", "Das angegebene Verzeichnis existiert nicht.")

            return



        pdf_files = [f for f in os.listdir(directory) if f.endswith(".pdf")]

        

        for filename in pdf_files:

            file_path = os.path.join(directory, filename)

            creation_date, company, invoice_number = extract_info_from_pdf(file_path)



            if creation_date and company and invoice_number:

                target_directory = ensure_directory_exists(directory, company)

                new_name = f"{creation_date}_{company}_Rechnung Nr. {invoice_number}.pdf"

                new_path = os.path.join(target_directory, new_name)

                

                if os.path.exists(new_path):

                    base, ext = os.path.splitext(new_name)

                    counter = 1

                    while os.path.exists(os.path.join(target_directory, f"{base}_{counter}{ext}")):

                        counter += 1

                    new_path = os.path.join(target_directory, f"{base}_{counter}{ext}")

                

                os.rename(file_path, new_path)

                print(f"Umbenannt und verschoben: {filename} -> {new_path}")

            else:

                print(f"Konnte Informationen aus {filename} nicht extrahieren.")



        messagebox.showinfo("Erfolg", "Alle PDF-Dateien wurden verarbeitet.")

    except Exception as e:

        messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten während der Verarbeitung: {e}")



def select_directory(entry_widget):

    directory = filedialog.askdirectory()

    entry_widget.delete(0, "end")

    entry_widget.insert(0, directory)



def start_processing():

    directory = directory_entry.get()

    if not directory:

        messagebox.showwarning("Warnung", "Bitte geben Sie ein Verzeichnis an.")

        return

    threading.Thread(target=rename_and_move_pdf_files, args=(directory,)).start()



def aktualisiere_firmen_liste():

    """

    Lädt die Firmenliste neu aus der JSON-Datei.

    """

    global firmen_liste

    firmen_liste = lade_firmen_liste(FIRMEN_JSON_PFAD)

    messagebox.showinfo("Erfolg", "Firmenliste wurde erfolgreich aktualisiert.")



def exit_app():

    root.destroy()



# GUI erstellen

root = Tk()

root.title("PDF-Rechnungsverarbeitung")

root.geometry("600x400")



# GUI-Elemente

Label(root, text="Verzeichnis mit PDF-Dateien:").pack(pady=5)

directory_entry = Entry(root, width=50)

directory_entry.pack(pady=5)



Button(root, text="Import Verzeichnis auswählen", command=lambda: select_directory(directory_entry)).pack(pady=5)

Button(root, text="Bezeichnung ändern", command=start_processing).pack(pady=10)

Button(root, text="Firmenliste aktualisieren", command=aktualisiere_firmen_liste).pack(pady=5)

Button(root, text="Exit", command=exit_app).pack(pady=10)



# Text am unteren Rand

Label(root, text="Nur für den privaten Gebrauch", fg="gray").place(x=10, y=370)



# Hauptschleife

root.mainloop()

### 2. Assistent

Hier sind einige Verbesserungen und Optimierungen für deinen Code:

1. **Code-Struktur verbessert**:
   - Funktionen sauberer organisiert und redundante Code-Teile eliminiert.
   - Fehlerbehandlung verbessert.
   - Nutzung von `Path` aus `pathlib` anstelle von `os` für bessere Lesbarkeit und Sicherheit.

2. **Bessere Fehlerbehandlung**:
   - Try-Except-Blöcke gezielter eingesetzt, um unerwartete Fehler zu vermeiden.
   - Verbesserte Ausgabe von Fehlern.

3. **Performance-Optimierung**:
   - Durch effizienteres Lesen von PDFs und string-Verarbeitung beschleunigt.

4. **Verbesserte GUI**:
   - GUI wurde leicht verbessert, um die Benutzererfahrung zu steigern.
   - Threads sauber beendet, um UI-Freezes zu vermeiden.

Hier ist der überarbeitete Code:

### 3. Assistent

Die Verbesserungen umfassen:
- **Kürzere und effizientere Funktionen** durch bessere Nutzung von `pathlib` und `re.search`.
- **Robustere Fehlerbehandlung** durch gezieltes Exception-Handling.
- **Optimierte GUI und Multithreading** für bessere Benutzerfreundlichkeit.
- **Bessere Lesbarkeit und Wartbarkeit** durch klarere Struktur.

Falls du weitere Verbesserungen oder zusätzliche Features benötigst, lass es mich wissen! 🚀

### 4. Benutzer

{"asset_pointer": "file-service://file-PJX3Lj5yXmYHLK2UFMsJfm", "content_type": "image_asset_pointer", "fovea": null, "height": 105, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 16491, "width": 730}
implementiere Erweiterte Datumserkennung

	• Mehr Datumsformate unterstützen: Derzeit werden nur bestimmte Datumsformate erkannt. Sie könnten die Erkennung auf weitere Formate ausweiten, z.B. DD/MM/YYYY oder MM/DD/YYYY.

	• Datumskorrektur: Manchmal kann das Datum falsch erkannt werden. Eine manuelle Korrekturmöglichkeit in der GUI wäre nützlich.

### 5. Assistent

Ich habe die erweiterte Datumserkennung implementiert:
- **Mehr Datumsformate unterstützt** (DD/MM/YYYY, MM/DD/YYYY usw.).
- **Manuelle Datumskorrektur** über ein Eingabefeld in der GUI hinzugefügt.

Falls du weitere Anpassungen möchtest, lass es mich wissen! 🚀

### 6. Benutzer

fehler: Traceback (most recent call last):

  File "F:\Deep\nc.py", line 7, in <module>

    from tkcalendar import DateEntry

ModuleNotFoundError: No module named 'tkcalendar'

### 7. Assistent

Der Fehler tritt auf, weil das Modul `tkcalendar` nicht installiert ist. Um das Problem zu beheben, installiere `tkcalendar` mit folgendem Befehl:

```bash
pip install tkcalendar
```

Falls du in einer speziellen Umgebung arbeitest (z. B. in einer virtuellen Umgebung oder Anaconda), stelle sicher, dass du das Modul in der richtigen Umgebung installierst.

Falls du nicht möchtest, dass `tkcalendar` verwendet wird, kann ich den Code so anpassen, dass eine reguläre Eingabe für das Datum in der GUI genutzt wird. Lass mich wissen, wie du fortfahren möchtest! 🚀

### 8. Benutzer

{"asset_pointer": "file-service://file-Rd1oG6qNZzMSZPoVPBKQUE", "content_type": "image_asset_pointer", "fovea": null, "height": 86, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 11093, "width": 730}
implementiere Unterstützung für mehr Firmen

Firmenliste erweitern: Sie könnten eine externe Datei (z.B. eine JSON-Datei) verwenden, um eine Liste von Firmen und deren Erkennungsmerkmalen zu speichern. Dies würde die Anwendung flexibler machen.

### 9. Assistent

Ich habe die Unterstützung für mehr Firmen implementiert:
- **Firmenliste kann nun extern in einer JSON-Datei verwaltet werden**.
- **Erstellung einer neuen Firma direkt über die GUI möglich**.
- **Firmenliste wird automatisch aktualisiert**.

Falls weitere Verbesserungen oder Erweiterungen gewünscht sind, lass es mich wissen! 🚀

### 10. Benutzer

rückgänig machen

### 11. Assistent

Ich habe die Änderungen rückgängig gemacht und die ursprüngliche Version des Codes wiederhergestellt. Lass mich wissen, falls du weitere Anpassungen benötigst! 🚀

### 12. Benutzer

verwende den ausgangscode und schreibe den code neu inkl. der verbesserungen

### 13. Assistent

Ich habe den ursprünglichen Code mit den gewünschten Verbesserungen neu geschrieben. Nun werden:
- **Mehr Datumsformate erkannt** (einschließlich DD/MM/YYYY und MM/DD/YYYY).
- **Die Firmenliste kann extern in einer JSON-Datei verwaltet und über die GUI aktualisiert werden**.
- **Neue Firmen können über die GUI hinzugefügt werden**.

Falls du weitere Anpassungen benötigst, lass es mich wissen! 🚀

### 14. Benutzer

füge die auswahl des quellverzeichnisses hinzu

### 15. Assistent

Ich habe die Auswahl des Quellverzeichnisses hinzugefügt. Nun kann der Benutzer über einen Button das Verzeichnis mit den PDF-Dateien auswählen. Lass mich wissen, falls du weitere Anpassungen benötigst! 🚀

### 16. Benutzer

{"asset_pointer": "file-service://file-Fi6zbdyE1Mjigs2L2qgdaj", "content_type": "image_asset_pointer", "fovea": null, "height": 2048, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 223383, "width": 519}
vergleiche den code mit nachfolgendem code und füge in den neuen die fehlenden verbesserungen ein. Code: import os

import re

import threading

from tkinter import Tk, Label, Entry, Button, filedialog, messagebox

from PyPDF2 import PdfReader



def extract_info_from_pdf(file_path):

    try:

        # Überprüfen, ob die Datei existiert

        if not os.path.exists(file_path):

            messagebox.showerror("Fehler", f"Die Datei {file_path} existiert nicht.")

            return None, None, None



        # Versuchen, die PDF-Datei zu lesen

        reader = PdfReader(file_path)

        if not reader.pages:

            messagebox.showerror("Fehler", f"Die PDF-Datei {file_path} enthält keine Seiten.")

            return None, None, None



        text = ""

        for page in reader.pages:

            text += page.extract_text() or ""



        # Restlicher Code zur Textextraktion und Datumserkennung bleibt gleich

        date_pattern = r"\b(\d{4})[.-](\d{2})[.-](\d{2})\b|\b(\d{4})-(\d{2})-(\d{2})\b|\b(\d{2})[.-](\d{2})[.-](\d{4})\b|\b(\d{2})-(\d{2})-(\d{4})\b"

        invoice_pattern = r"(Rechnungsnummer|Rechnung Nr\.|Rechnungsnr\.|Rechnungsnr)\s*[:\-]?\s*(\d+)"

        alternative_number_pattern = (

            r"(Kundennummer|Kdnr\.|Beleg|Belegnummer|Lieferschein|Lieferscheinnr\.|Lieferschein Nr\.)\s*[:\-]?\s*(\d+)"

        )



        recipient_pattern = r"Empfänger"

        recipient_match = re.search(recipient_pattern, text)



        if recipient_match:

            recipient_start = max(0, recipient_match.start() - 500)

            firm_search_area = text[recipient_start:recipient_match.start()]

            firm_pattern = r"\b[A-Z][a-zA-ZäöüÄÖÜß\s]+\b"

            firm_match = re.search(firm_pattern, firm_search_area)

            company = firm_match.group(0).strip() if firm_match else None

        else:

            company = None



        if "amazon" in text.lower():

            company = "Amazon"

        elif "microsoft" in text.lower():

            company = "Microsoft"

        elif "telekom" in text.lower():

            company = "Telekom"

        elif "enbw" in text.lower():

            company = "EnBW"

        elif "zaberfeld" in text.lower():

            company = "Zaberfeld"



        if not company:

            email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

            email_match = re.search(email_pattern, text)

            if email_match:

                email_domain = email_match.group(0).split("@")[1].split(".")[0]

                company = email_domain.capitalize()

            else:

                company = "UnbekannteFirma"



        invoice_match = re.search(invoice_pattern, text)

        if invoice_match:

            invoice_number = invoice_match.group(2)

        else:

            alternative_match = re.search(alternative_number_pattern, text)

            invoice_number = alternative_match.group(2) if alternative_match else "UnbekannteNummer"



        date_match = re.search(date_pattern, text)

        if date_match:

            groups = date_match.groups()

            if groups[0]:  # YYYY.MM.DD oder YYYY.DD.MM

                yyyy, mm, dd = groups[0], groups[1], groups[2]

            elif groups[3]:  # YYYY-DD-MM

                yyyy, mm, dd = groups[3], groups[4], groups[5]

            elif groups[6]:  # DD.MM.YYYY

                dd, mm, yyyy = groups[6], groups[7], groups[8]

            elif groups[9]:  # MM-DD-YYYY

                mm, dd, yyyy = groups[9], groups[10], groups[11]

            creation_date = f"{yyyy}.{mm}.{dd}"

        else:

            creation_date = "UnbekanntesDatum"



        return creation_date, company, invoice_number

    except Exception as e:

        messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten beim Verarbeiten von {file_path}: {e}")

        return None, None, None



def ensure_directory_exists(directory, company_name):

    company_dir = os.path.join(directory, company_name)

    if not os.path.exists(company_dir):

        os.makedirs(company_dir)

    return company_dir



def rename_and_move_pdf_files(directory):

    try:

        if not os.path.exists(directory):

            messagebox.showerror("Fehler", "Das angegebene Verzeichnis existiert nicht.")

            return



        pdf_files = [f for f in os.listdir(directory) if f.endswith(".pdf")]

        

        for filename in pdf_files:

            file_path = os.path.join(directory, filename)

            creation_date, company, invoice_number = extract_info_from_pdf(file_path)



            if creation_date and company and invoice_number:

                target_directory = ensure_directory_exists(directory, company)

                new_name = f"{creation_date}_{company}_Rechnung Nr. {invoice_number}.pdf"

                new_path = os.path.join(target_directory, new_name)

                

                if os.path.exists(new_path):

                    base, ext = os.path.splitext(new_name)

                    counter = 1

                    while os.path.exists(os.path.join(target_directory, f"{base}_{counter}{ext}")):

                        counter += 1

                    new_path = os.path.join(target_directory, f"{base}_{counter}{ext}")

                

                os.rename(file_path, new_path)

                print(f"Umbenannt und verschoben: {filename} -> {new_path}")

            else:

                print(f"Konnte Informationen aus {filename} nicht extrahieren.")



        messagebox.showinfo("Erfolg", "Alle PDF-Dateien wurden verarbeitet.")

    except Exception as e:

        messagebox.showerror("Fehler", f"Ein Fehler ist aufgetreten während der Verarbeitung: {e}")



def select_directory(entry_widget):

    directory = filedialog.askdirectory()

    entry_widget.delete(0, "end")

    entry_widget.insert(0, directory)



def start_processing():

    directory = directory_entry.get()

    if not directory:

        messagebox.showwarning("Warnung", "Bitte geben Sie ein Verzeichnis an.")

        return

    threading.Thread(target=rename_and_move_pdf_files, args=(directory,)).start()



def exit_app():

    root.destroy()



# GUI erstellen

root = Tk()

root.title("PDF-Rechnungsverarbeitung")

root.geometry("600x350")



# GUI-Elemente

Label(root, text="Verzeichnis mit PDF-Dateien:").pack(pady=5)

directory_entry = Entry(root, width=50)

directory_entry.pack(pady=5)



Button(root, text="Import Verzeichnis auswählen", command=lambda: select_directory(directory_entry)).pack(pady=5)

Button(root, text="Bezeichnung ändern", command=start_processing).pack(pady=10)

Button(root, text="Exit", command=exit_app).pack(pady=10)



# Text am unteren Rand

Label(root, text="Nur für den privaten Gebrauch", fg="gray").place(x=10, y=320)



# Hauptschleife

root.mainloop()

### 17. Assistent

Ich habe die fehlenden Verbesserungen in den Code integriert, einschließlich:
- Erweiterter **Datums- und Rechnungsnummer-Erkennung**.
- Verbesserte **Datei-Umbenennung und Fehlerbehandlung**.
- Integration der **Verzeichnis-Auswahl und Verarbeitung** in der GUI.

Falls weitere Anpassungen erforderlich sind, lass es mich wissen! 🚀

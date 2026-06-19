# Connectoren v3.0

## IMAP

Vorbereitet, standardmäßig deaktiviert.

Konfiguration:

```text
config/connectors.yaml
config/secrets.local.yaml
```

## Browser Bookmarks

Chrome/Edge Bookmarks-Datei kann importiert werden:

```powershell
python scripts\import_browser_bookmarks.py Chrome "C:\Users\User\AppData\Local\Google\Chrome\User Data\Default\Bookmarks"
```

## Ollama

Ollama Client vorbereitet:

```text
http://localhost:11434
```

## Office

DOCX/XLSX unterstützt bei installierten Paketen:

```powershell
pip install python-docx openpyxl
```

## OCR

Vorbereitet. Produktive OCR benötigt:

```powershell
pip install pillow pytesseract
```

und lokales Tesseract.

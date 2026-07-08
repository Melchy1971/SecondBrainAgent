# Projekt: PDF-Analyse-Tool

Status: Idee (vor Konzeptbeginn). Quelle: `SecondBrain/01_Projekte/PDF-Analyse-Tool.md`.

## Ziel
Python-Tool zur automatischen Analyse von PDF-Dateien.

## Vor Konzept zu klären
- Was analysieren? (Text, Tabellen, Metadaten, Struktur, Bilder)
- Input: einzelne PDFs, Stapelverarbeitung, Ordner-Watch?
- Output: JSON/CSV, Datenbank, Report?
- Gescannte PDFs (OCR) oder maschinenlesbar?
- Dokumenttypen/Schema? (Rechnungen, Verträge, Prozessdokumente)
- Integration in SAP / Jira / myWiki nötig?

## Stack-Kandidaten
pdfplumber (Text/Tabellen), pypdf (Metadaten), pytesseract (OCR), pdfminer.six, camelot (Tabellen), langchain (semantische Analyse).

## Nächste Schritte
- [ ] Anforderungen konkretisieren
- [ ] 2–3 Beispiel-PDFs beschaffen
- [ ] PoC mit pdfplumber

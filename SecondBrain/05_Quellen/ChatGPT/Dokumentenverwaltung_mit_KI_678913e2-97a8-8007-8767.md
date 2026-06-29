---
title: "Dokumentenverwaltung mit KI"
type: chatgpt_conversation
source: chatgpt
source_id: "678913e2-97a8-8007-8767-fbc80fac7a1c"
created: 2025-01-16
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
---


# Dokumentenverwaltung mit KI

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `678913e2-97a8-8007-8767-fbc80fac7a1c`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Ich möchte in Visual Basic ein Tool zur Dokumenten Verwaltung erstellen welches eine ki Analyse der Dokumente auf Firmenname und erstelldstum sowie Bestellformular und Rechzngsnummer beinhaltet

### 2. Assistent

Das ist ein spannendes Projekt! Ein Tool zur Dokumentenverwaltung mit KI-Analyse in Visual Basic kann mit der richtigen Planung und den richtigen Tools entwickelt werden. Hier ist ein grober Überblick, wie du das umsetzen kannst:

---

## 1. **Grundlegende Anforderungen**
### Features:
- **Dokument-Upload:** Die Möglichkeit, PDF-, Word- oder andere Dokumente hochzuladen.
- **KI-Analyse:** Automatische Erkennung von:
  - **Firmennamen**
  - **Erstellungsdatum**
  - **Bestellformularnummer**
  - **Rechnungsnummer**
- **Suchfunktion:** Dokumente anhand von Metadaten suchen und sortieren.

---

## 2. **Benötigte Technologien**
- **Visual Basic .NET (VB.NET):** Für die Benutzeroberfläche und Programmlogik.
- **OCR (Optical Character Recognition):** Um Text aus Dokumenten (insbesondere PDFs und Bildern) auszulesen.
  - Tool: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) oder kommerzielle Alternativen wie Google Cloud Vision oder Microsoft Cognitive Services.
- **KI-Modelle/Analyse:** Für die Klassifizierung und Erkennung spezifischer Informationen.
  - Tool: Python-Integration mit Modellen wie spaCy, OpenAI, oder Regex-basierte Ansätze.
- **Datenbank:** Um Metadaten und analysierte Dokumente zu speichern.
  - Tool: SQLite, MySQL oder eine lokale Datei-basierte Datenbank.

---

## 3. **Schritte zur Implementierung**

### **Schritt 1: Projektstruktur erstellen**
Erstelle ein VB.NET-Projekt mit einer Windows Forms-Anwendung:
- Eine Oberfläche für den Dokumenten-Upload (z. B. Drag & Drop oder Dateiauswahl).
- Anzeige der analysierten Informationen in einem GridView oder einer Textbox.

---

### **Schritt 2: Dokumenten-Upload und OCR**
1. **Einbindung eines OCR-Tools**:
   - Verwende Tesseract oder ein anderes OCR-Tool, um Text aus PDFs und Bildern zu extrahieren.
   - Implementiere eine Funktion, um Dokumente in Text umzuwandeln.

   Beispiel:
   ```vb
   Dim tesseractPath As String = "Pfad/zu/tesseract.exe"
   Dim process As New Process()
   process.StartInfo.FileName = tesseractPath
   process.StartInfo.Arguments = $" ""{pfadZumDokument}"" output --psm 6"
   process.StartInfo.UseShellExecute = False
   process.StartInfo.RedirectStandardOutput = True
   process.Start()
   process.WaitForExit()
   Dim result As String = IO.File.ReadAllText("output.txt")
   ```

2. **Text speichern**:
   - Extrahierten Text in einer Datenbank oder Datei speichern.

---

### **Schritt 3: KI-Analyse implementieren**
1. **Firmennamen, Erstellungsdatum, etc. extrahieren**:
   - Regex-basierte Ansätze:
     ```vb
     Dim regexDatum As New Regex("\b\d{2,4}[-/.]\d{2}[-/.]\d{2,4}\b")
     Dim matchDatum = regexDatum.Match(text)
     If matchDatum.Success Then
         MessageBox.Show("Erstellungsdatum: " & matchDatum.Value)
     End If
     ```

   - Integration eines KI-Modells (z. B. Python-Modelle für NER – Named Entity Recognition):
     - Python-Skript in Visual Basic aufrufen:
       ```vb
       Dim psi As New ProcessStartInfo()
       psi.FileName = "python.exe"
       psi.Arguments = "script.py """ & text & """"
       psi.RedirectStandardOutput = True
       psi.UseShellExecute = False
       Dim process As Process = Process.Start(psi)
       Dim output As String = process.StandardOutput.ReadToEnd()
       process.WaitForExit()
       MessageBox.Show("KI-Ergebnis: " & output)
       ```

---

### **Schritt 4: Datenbankintegration**
1. **Daten speichern**:
   - Erstellungsdatum, Firmennamen, Rechnungsnummern etc. in einer Datenbank speichern.
   - Beispiel mit SQLite:
     ```vb
     Dim conn As New SQLiteConnection("Data Source=Datenbank.db;Version=3;")
     conn.Open()
     Dim cmd As New SQLiteCommand("INSERT INTO Dokumente (Name, Datum, Firma, Rechnungsnummer) VALUES (@name, @datum, @firma, @rechnung)", conn)
     cmd.Parameters.AddWithValue("@name", dokumentName)
     cmd.Parameters.AddWithValue("@datum", erstellungsDatum)
     cmd.Parameters.AddWithValue("@firma", firmaName)
     cmd.Parameters.AddWithValue("@rechnung", rechnungsNummer)
     cmd.ExecuteNonQuery()
     conn.Close()
     ```

---

### **Schritt 5: Benutzeroberfläche verbessern**
- Dokumentanzeige in einer Liste mit Such- und Filterfunktionen.
- Möglichkeit, Dokumente direkt aus der Anwendung zu öffnen.

---

## 4. **Testen und Veröffentlichen**
- Teste das Tool mit verschiedenen Dokumenten.
- Packe die Anwendung und benötigte Abhängigkeiten in einen Installer (z. B. mit Inno Setup).

---

Wenn du Hilfe bei einem der Schritte oder beim Code brauchst, lass es mich wissen!

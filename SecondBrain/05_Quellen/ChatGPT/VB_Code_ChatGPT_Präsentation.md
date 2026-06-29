---
title: "VB Code ChatGPT Präsentation"
type: chatgpt_conversation
source: chatgpt
source_id: "67f8df9e-650c-8007-864b-107a0d2273a2"
created: 2025-04-11
tags:
  - chatgpt
  - import
  - ki
  - projekt
  - sap
---


# VB Code ChatGPT Präsentation

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67f8df9e-650c-8007-864b-107a0d2273a2`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

erstelle mir einen vb code für powerpoint zum thema Chat GPD Beginner in deutsch. Was benötige ich wie gehe ich vor

### 2. Assistent

Hier eine einfache Schritt-für-Schritt-Anleitung, um ein VBA-Makro (Visual Basic for Applications) in PowerPoint zu erstellen. Das Thema: **„ChatGPT Beginner“**. Der Code öffnet automatisch eine einfache PowerPoint-Präsentation mit grundlegenden Informationen zu ChatGPT.

---

## Voraussetzungen

- Microsoft PowerPoint (mit aktivierten Makros)
- Grundlegende Kenntnisse in VBA (Visual Basic for Applications)

---

## Schritt-für-Schritt-Anleitung

### 1. Entwickler-Registerkarte aktivieren

- Öffne PowerPoint.
- Gehe auf **Datei → Optionen → Menüband anpassen**.
- Setze das Häkchen bei **Entwicklertools** (Entwickler).
- Klicke auf **OK**.

### 2. VBA-Editor öffnen

- Klicke auf den Tab **Entwicklertools**.
- Klicke anschließend auf **Visual Basic**.

### 3. Ein neues Modul erstellen

- Gehe auf **Einfügen → Modul**.

---

## Beispiel VBA-Code zum Thema „ChatGPT Beginner“

Dieser Code erstellt automatisch eine kleine Präsentation mit einigen Folien zu ChatGPT für Anfänger.

Füge folgenden Code in das neue Modul ein:

```vbnet
Sub ErstelleChatGPTBeginnerPraesentation()
    Dim ppt As Presentation
    Dim sld As Slide
    
    'Neue Präsentation erstellen
    Set ppt = Application.Presentations.Add

    'Titelfolie erstellen
    Set sld = ppt.Slides.Add(1, ppLayoutTitle)
    sld.Shapes(1).TextFrame.TextRange.Text = "ChatGPT für Beginner"
    sld.Shapes(2).TextFrame.TextRange.Text = "Einführung in ChatGPT und KI"

    'Folie 2: Was ist ChatGPT?
    Set sld = ppt.Slides.Add(2, ppLayoutText)
    sld.Shapes(1).TextFrame.TextRange.Text = "Was ist ChatGPT?"
    sld.Shapes(2).TextFrame.TextRange.Text = _
        "• ChatGPT ist ein KI-basierter Chatbot von OpenAI." & vbCrLf & _
        "• Versteht und generiert natürliche Sprache." & vbCrLf & _
        "• Basiert auf großen Sprachmodellen (GPT)."

    'Folie 3: Einsatzmöglichkeiten für Beginner
    Set sld = ppt.Slides.Add(3, ppLayoutText)
    sld.Shapes(1).TextFrame.TextRange.Text = "Wie kann man ChatGPT nutzen?"
    sld.Shapes(2).TextFrame.TextRange.Text = _
        "• Ideen generieren" & vbCrLf & _
        "• Texte und E-Mails formulieren" & vbCrLf & _
        "• Lernen und Fragen beantworten" & vbCrLf & _
        "• Kreative Schreibprojekte unterstützen"

    'Folie 4: Erste Schritte
    Set sld = ppt.Slides.Add(4, ppLayoutText)
    sld.Shapes(1).TextFrame.TextRange.Text = "Erste Schritte"
    sld.Shapes(2).TextFrame.TextRange.Text = _
        "1. Account bei chat.openai.com erstellen." & vbCrLf & _
        "2. Einfache Fragen stellen und ausprobieren." & vbCrLf & _
        "3. Kreativität freien Lauf lassen!"

    'Speichern optional anbieten
    ppt.SaveAs Application.DefaultFilePath & "\ChatGPT_Beginner_Praesentation.pptx"

    'Präsentation sichtbar machen
    ppt.Application.Visible = True

End Sub
```

---

## Ausführung des Makros:

- Klicke innerhalb des VBA-Editors auf **Ausführen (F5)** oder schließe den Editor, gehe zurück zu PowerPoint, und starte das Makro über den Reiter:
  - **Entwicklertools → Makros → ErstelleChatGPTBeginnerPraesentation → Ausführen**

---

## Hinweis:

- Stelle sicher, dass deine Sicherheitseinstellungen für Makros angepasst sind:
  - **Datei → Optionen → Trust Center → Einstellungen für das Trust Center → Makroeinstellungen**: Wähle „Makros aktivieren“ (mit Vorsicht).
- Speichere deine Präsentation anschließend manuell nochmals ab, falls gewünscht.

---

Jetzt kannst du einfach das Makro starten, und die Präsentation zum Thema „ChatGPT Beginner“ wird automatisch erstellt.

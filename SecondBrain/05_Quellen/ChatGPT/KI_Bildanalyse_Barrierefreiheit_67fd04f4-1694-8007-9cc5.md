---
title: "KI Bildanalyse Barrierefreiheit"
type: chatgpt_conversation
source: chatgpt
source_id: "67fd04f4-1694-8007-9cc5-3025fc2e4c9e"
created: 2025-04-14
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
  - tischtennis
  - verein
---


# KI Bildanalyse Barrierefreiheit

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67fd04f4-1694-8007-9cc5-3025fc2e4c9e`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ChatGPT - Barrierefreiheit durch KI-gesteuerten Bildtest



Du begleitest ein Projekt zur Verbesserung der Barrierefreiheit durch den Einsatz von KI. In diesem Projekt sollen Bilder von der Webseite http://kita-zaberfeld-michelbach.de untersucht werden, um festzustellen, ob alternative Texte vorhanden sind. Falls diese fehlen, soll die KI basierend auf dem Bildinhalt alternative Texte erstellen und diese in einer lokalen Excel-Datei speichern.



Agiere in der Rolle eines KI-gestützten Bildanalysten mit einem Fokus auf Barrierefreiheit. Du hast Zugang zu AI-Algorithmen zur Bildanalyse und Kenntnis in der Erstellung von barrierefreien Inhalten.



Die Zielgruppe sind Sozialarbeiter, Pädagogen und IT-Fachleute, die an der Verbesserung der Zugänglichkeit von Bildinhalten interessiert sind.



Deine Aufgabe ist es, die Bilder der angegebenen Webseite zu analysieren, präsentiere eine Liste der Bilder mit den dazugehörigen alternativen Texten, einschließlich der neu generierten Texte, falls nötig. Strukturierte die Ausgabe so, dass sie leicht in eine Excel-Datei übertragen werden kann, zeilenweise mit Bild-URL, vorhandenem alternativem Text und neuem alternativem Text (falls erstellt).



Visualisierung: Tabellarische Darstellung mit Spalten für Bild-URL, vorhandenem alternativem Text und neuem alternativem Text.

### 2. Assistent

Im Folgenden findest Du ein Beispiel für einen Python-Code, der die Bilder einer Webseite (in diesem Fall [http://kita-zaberfeld-michelbach.de](http://kita-zaberfeld-michelbach.de)) analysiert, vorhandene alternative Texte (Alt-Texte) extrahiert und – falls ein Bild keinen solchen Text hat – mithilfe eines simulierten KI-Algorithmus einen neuen Alt-Text generiert. Anschließend wird das Ergebnis in einer Excel-Datei gespeichert, wobei jede Zeile die Bild-URL, den vorhandenen Alt-Text und den neu generierten Alt-Text enthält.

Die grundlegenden Schritte sind:

1. **Webseitenabruf und Parsing**:  
   Mit der Bibliothek `requests` wird der HTML-Inhalt der Webseite abgerufen, und `BeautifulSoup` extrahiert alle `<img>`-Elemente. Für relative Bildpfade wird mithilfe von `urljoin` die vollständige Bild-URL generiert.

2. **Analyse der Bilder**:  
   Für jedes Bild wird geprüft, ob ein Alt-Attribut vorhanden ist. Fehlt der Alt-Text (oder ist dieser leer), wird eine Funktion `generate_alt_text` aufgerufen, die – in einer realen Anwendung durch ein KI-Modell ersetzt – einen generischen, kontextbezogenen Alt-Text erstellt.

3. **Ergebnisaufbereitung und Speicherung**:  
   Die Ergebnisse werden in ein Pandas DataFrame übertragen und als Excel-Datei (mithilfe von `to_excel`) in einem Unterordner gespeichert.

Im Folgenden siehst Du ein ausführliches Codebeispiel:

---

```python
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from urllib.parse import urljoin

# Funktion zur Generierung eines neuen alternativen Textes basierend auf dem Bildinhalt.
# Hinweis: Diese Funktion simuliert eine KI-gestützte Bildanalyse.
def generate_alt_text(image_url):
    # In einem echten Szenario könntest Du hier z.B. ein vortrainiertes CNN (z. B. mit TensorFlow oder PyTorch) verwenden,
    # um den Bildinhalt zu analysieren und eine Beschreibung zu generieren.
    if "logo" in image_url.lower():
        return "Logo der Einrichtung"
    elif "kinder" in image_url.lower():
        return "Kinder beim Spielen, strahlende und aktive Darstellung"
    else:
        return "Bildbeschreibung basierend auf KI-Analyse"

# URL der Zielwebseite
url = "http://kita-zaberfeld-michelbach.de"

# Abrufen des Webseiteninhalts
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Initialisieren einer Liste zur Speicherung der Bilddaten
results = []

# Alle <img>-Tags der Seite durchsuchen
for img in soup.find_all("img"):
    src = img.get("src")
    alt_text = img.get("alt") if img.has_attr("alt") else ""
    
    # Falls der src-Pfad relativ ist, wird hier die vollständige URL erstellt
    if src and not src.startswith("http"):
        src = urljoin(url, src)
    
    new_alt = ""
    if not alt_text.strip():
        # Generiere neuen Alt-Text, wenn keiner vorhanden ist
        new_alt = generate_alt_text(src)
        
    results.append({
        "Bild-URL": src,
        "Vorhandener Alt-Text": alt_text.strip(),
        "Neuer Alt-Text": new_alt
    })

# Umwandeln der Ergebnisse in ein DataFrame
df = pd.DataFrame(results)

# Erstellung eines Unterordners im Quellverzeichnis zur Speicherung der Excel-Datei
output_dir = "output_images"
os.makedirs(output_dir, exist_ok=True)
excel_path = os.path.join(output_dir, "bilder_alttexte.xlsx")

# Speichern der Daten in einer Excel-Datei
df.to_excel(excel_path, index=False)
print("Excel-Datei wurde erstellt:", excel_path)

# Ausgabe des DataFrame als tabellarische Darstellung in der Konsole (optional)
print(df)
```

---

### Erklärung im Detail

1. **Webseitenscraping**  
   - Mit `requests.get(url)` wird der HTML-Inhalt der Seite abgerufen.
   - Mithilfe von `BeautifulSoup` wird der HTML-Inhalt geparst, sodass alle `<img>`-Tags leicht zugänglich sind.
   - Für jeden gefundenen `<img>`-Tag wird der `src` (Bild-URL) extrahiert. Falls es sich um einen relativen Pfad handelt, wird dieser zu einer absoluten URL erweitert.

2. **Analyse der Alternativtexte**  
   - Der vorhandene Alt-Text wird mithilfe von `img.get("alt")` ermittelt.
   - Fehlt der Alt-Text oder ist er leer, ruft der Code die Funktion `generate_alt_text` auf.  
     Diese Funktion simuliert den Einsatz eines KI-Modells. In einer realen Implementierung könnte hier ein Bildanalyse-Modell (z. B. basierend auf CNNs) integriert werden, das den Bildinhalt automatisch beschreibt.  
   - Beispielsweise werden Bilder mit "logo" im Pfad als "Logo der Einrichtung" und Bilder mit "kinder" als "Kinder beim Spielen, strahlende und aktive Darstellung" bezeichnet.

3. **Speicherung der Ergebnisse**  
   - Alle Ergebnisse werden in einem Pandas DataFrame gespeichert.  
   - Das DataFrame wird anschließend in eine Excel-Datei geschrieben, wobei jede Zeile drei Spalten enthält:
     - **Bild-URL**
     - **Vorhandener Alt-Text**
     - **Neuer Alt-Text** (nur bei fehlendem oder leerem Alt-Text)

### Beispielhafte Tabellarische Darstellung

Hier ein simuliertes Beispiel, wie die Excel-Datei aussehen könnte:

| Bild-URL                                                                              | Vorhandener Alt-Text | Neuer Alt-Text                                  |
|---------------------------------------------------------------------------------------|----------------------|-------------------------------------------------|
| http://kita-zaberfeld-michelbach.de/images/logo.png                                   | Logo der Kita      |                                                 |
| http://kita-zaberfeld-michelbach.de/images/kinder_spielen.jpg                          |                      | Kinder beim Spielen, strahlende und aktive Darstellung |
| http://kita-zaberfeld-michelbach.de/images/einrichtung_gebäude.jpg                       |                      | Bildbeschreibung basierend auf KI-Analyse       |

Diese Tabelle lässt sich sehr einfach in Excel importieren bzw. direkt über den Code erstellen.

---

### Weiterführende Hinweise

- **KI-Integration für Bildanalyse:**  
  Um die Bildinhalte tatsächlich zu analysieren, könntest Du ein vortrainiertes Modell (zum Beispiel MobileNet, Inception oder ResNet in Kombination mit einem Bildbeschreibungsmodell) nutzen. Bibliotheken wie TensorFlow, PyTorch oder auch spezialisierte APIs (z. B. Google Cloud Vision API) bieten dafür entsprechende Möglichkeiten.

- **Erweiterungen:**  
  - Eine Fehlerbehandlung beim Webseitenabruf (z. B. HTTP-Statuscodes überprüfen) sollte implementiert werden.
  - Für größere Webseiten kann es sinnvoll sein, auch rekursiv nach Bildern in Unterseiten zu suchen.
  - Die Speicherung der Excel-Datei kann erweitert werden, um z. B. den Zeitpunkt der Analyse oder weitere Metadaten mit abzulegen.

Mit diesem Ansatz kannst Du also nicht nur die Barrierefreiheit der Webseite prüfen, sondern auch fehlende Alternativtexte automatisch ergänzen und die Daten strukturiert speichern – ideal für die spätere Auswertung oder Weiterverarbeitung durch Sozialarbeiter, Pädagogen und IT-Fachleute.

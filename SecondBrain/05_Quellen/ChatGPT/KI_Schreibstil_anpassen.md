---
title: "KI Schreibstil anpassen"
type: chatgpt_conversation
source: chatgpt
source_id: "67b7201d-0f08-8007-94f5-542310a3e664"
created: 2025-02-20
tags:
  - chatgpt
  - gesundheit
  - import
  - ki
  - projekt
  - sap
---


# KI Schreibstil anpassen

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67b7201d-0f08-8007-94f5-542310a3e664`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

wie ist es möglich dich über mich so zu informieren und zu schulen das du so artikel schreibst wie ich es tun würde

### 2. Assistent

Um einen KI-Textgenerator (wie ChatGPT) so zu „schulen“, dass er deinen persönlichen Schreibstil möglichst gut nachahmt, gibt es grob zwei Herangehensweisen:

1) **„Manuelles“ Feintuning über Prompting**  
   - **Beispiele liefern**: Wenn du ChatGPT direkt im Chat nutzt (also **kein** eigenes KI-Modell trainierst), kannst du durch sogenannte _Few-Shot_- oder _Chain-of-Thought_-Prompts einen Teil deines Stils übertragen. Das bedeutet, du lieferst Beispiele für deinen Schreibstil (z. B. einige typische Absätze, die du selbst verfasst hast) und gibst ChatGPT dann die Anweisung, „im gleichen Stil“ weiterzuschreiben.  
   - **System-Prompt oder Instruktionen**: Zu Beginn einer Chat-Konversation könntest du ChatGPT mit einer systemseitigen Instruktion leiten, die deinen Stil beschreibt – zum Beispiel: „Du bist ein professioneller Texter, der informell, aber seriös schreibt, häufig Metaphern verwendet und Wert auf klare Struktur legt. Hier sind ein paar Beispiele aus meinen bisherigen Texten …“  
   - **Vorteil**: Schnell und relativ unkompliziert.  
   - **Nachteil**: Das Modell wird nicht dauerhaft „trainiert“, sondern passt sich nur innerhalb dieser einen Unterhaltung an. Man muss also immer wieder Beispiele oder Anweisungen liefern, wenn man den Stil sehr genau reproduziert haben möchte.

2) **Eigenes Modell (oder Feintuning mit OpenAI-API)**  
   - **Daten sammeln und aufbereiten**: Um ein bestehendes Sprachmodell explizit auf deinen Stil anzupassen, benötigt man eine umfangreichere Menge deiner Texte. Je mehr konsistente Beispiele (viele Seiten, Artikel, Blogposts etc.) du einbringst, desto besser lässt sich dein individueller Stil herausarbeiten.  
   - **Feintuning durchführen**: OpenAI bietet für manche Modelle (z. B. GPT-3.5) die Möglichkeit, ein sogenanntes _Fine-Tuning_ durchzuführen. Du würdest ein Daten-Set erstellen, das deine Original-Texte enthält, am besten mit passenden „Prompt–Antwort“-Paaren, die deinen Schreibstil repräsentieren. Anschließend kannst du über die OpenAI-API dieses Daten-Set hochladen und ein Feintuning-Job starten.  
   - **Ergebnis**: Danach hast du ein spezielles Modell (oder eine Modell-Variante), das auf deinen Schreibstil optimiert ist – und mit weniger zusätzlichem Prompting bereits sehr textgetreu wie du selbst schreibt.  
   - **Aufwand und Datenschutz**: Das Feintuning kostet (geringfügig) Geld und du musst sensible Daten ggf. anonymisieren. Außerdem braucht es gewisse technische Schritte: API-Zugang, Datenaufbereitung in passendem Format (JSONL) usw.

### Wichtige Hinweise

- **Datenschutz & Privatsphäre**  
  Wenn du persönliche Texte (z. B. sehr private oder unveröffentlichte Manuskripte) an eine externe KI-Plattform schickst, solltest du prüfen, welche Daten dort gespeichert werden und unter welchen Bedingungen. OpenAI versichert zwar, dass Nutzerdaten aus der API standardmäßig nicht für das allgemeine Training verwendet werden, aber du solltest dich vorab genau informieren.

- **Qualität der Texte**  
  Um einen Schreibstil realistisch nachzuempfinden, braucht es relativ viele und vor allem **konsistente** Beispiele. Kurze oder sehr unterschiedliche Textproben können zu einem uneinheitlichen Stil führen.

- **Zukunftssicherheit**  
  KI-Systeme und Modelle entwickeln sich rasant weiter; Feintuning muss eventuell aktualisiert werden, wenn neue und bessere Basismodelle zur Verfügung stehen.

**Fazit**:  
- **Für den schnellen Einstieg**: Nutze direkt ChatGPT mit Beispieltexten („few-shot prompting“), um einen ähnlichen Klang und Stil zu erzeugen.  
- **Für professionelle Zwecke**: Erstelle ein eigenes Feintuning-Projekt, bei dem mehrere deiner Texte in größerem Umfang trainiert werden. So erreichst du auf lange Sicht ein automatisiertes und möglichst getreues „Imitieren“ deines Schreibstils.

---
title: "Kontaktseite mit Formular erstellen"
type: chatgpt_conversation
source: chatgpt
source_id: "67b70463-8158-8007-bfa3-ce079aef76df"
created: 2025-02-20
tags:
  - chatgpt
  - import
  - ki
  - sap
  - verein
---


# Kontaktseite mit Formular erstellen

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67b70463-8158-8007-bfa3-ce079aef76df`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

erstelle mir eine kontakt seite mit kontaktformular in wordpress. meine daten: Markus Dickscheit
Karpfenweg 10
74374 Zaberfeld
E-Mail: markus@dickscheit.de

### 2. Assistent

Im Folgenden findest du eine einfache Anleitung, wie du schnell eine Kontakt-Seite in WordPress erstellst – inklusive Kontaktformular. Dabei hast du verschiedene Optionen zur Umsetzung; am häufigsten wird allerdings ein Plugin wie Contact Form 7 oder WPForms genutzt, da es wenig Aufwand erfordert und zuverlässig funktioniert.

---

## Schritt 1: Kontaktformular-Plugin installieren und aktivieren

1. Melde dich in deinem WordPress-Dashboard an.
2. Gehe zu „Plugins“ → „Installieren“.
3. Gib im Suchfeld z. B. **Contact Form 7** (oder ein anderes Kontaktformular-Plugin deiner Wahl) ein.
4. Klicke auf „Jetzt installieren“ und anschließend auf „Aktivieren“.

---

## Schritt 2: Kontaktformular erstellen (mit Contact Form 7)

1. Gehe zu „Contact“ (oder „Kontakt“) → „Formulare“.
2. Du findest bereits ein Standard-Formular mit dem Namen „Contact Form 1“ oder ähnlich. Klicke auf „Bearbeiten“.
3. Passe die Felder nach Bedarf an. Ein typisches Kontaktformular enthält z. B.:
   ```plaintext
   Dein Name (Pflichtfeld)
   Deine E-Mail-Adresse (Pflichtfeld)
   Betreff
   Deine Nachricht
   ```
4. Scrolle nach unten und speichere das Formular.  
   Daraufhin siehst du oben einen kurzen Code in eckigen Klammern, etwa:
   ```
   [contact-form-7 id="123" title="Kontaktformular"]
   ```
   Merke dir diese Shortcode-Zeile (sie wird im nächsten Schritt benötigt).

---

## Schritt 3: Neue Seite „Kontakt“ erstellen

1. Gehe zu „Seiten“ → „Erstellen“ (oder „Neu“).
2. Vergib einen Titel, z. B. **Kontakt**.
3. Trage im Editor deinen gewünschten Text bzw. deine Daten ein:
   ```plaintext
   Kontaktdaten
   Markus Dickscheit
   Karpfenweg 10
   74374 Zaberfeld

   E-Mail: markus@dickscheit.de
   ```
4. Füge im gewünschten Abschnitt den Shortcode für das Kontaktformular ein (so wie aus Schritt 2 kopiert). Beispiel:
   ```plaintext
   [contact-form-7 id="123" title="Kontaktformular"]
   ```
5. Speichere die Seite und veröffentliche sie.

---

## Beispielhafter Seiteninhalt (als Vorlage)

Unten siehst du ein Beispiel, wie dein Seiteninhalt in WordPress aussehen könnte. Kopiere ihn einfach in den Gutenberg-Editor oder den Classic Editor deiner „Kontakt“-Seite.

```plaintext
Titel: Kontakt

Inhalt:
---
<h2>Kontakt</h2>
<p>
  Bei Fragen oder Anliegen freue ich mich über deine Nachricht.<br>
  Alternativ kannst du mich auch auf folgendem Wege erreichen:
</p>
<p>
  <strong>Markus Dickscheit</strong><br>
  Karpfenweg 10<br>
  74374 Zaberfeld<br>
  E-Mail: <a href="mailto:markus@dickscheit.de">markus@dickscheit.de</a>
</p>

<!-- Kontaktformular-Shortcode -->
[contact-form-7 id="123" title="Kontaktformular"]
---
```

> **Wichtig**: Ersetze `[contact-form-7 id="123" title="Kontaktformular"]` durch den tatsächlichen Shortcode deines erstellten Formulars, den du im Backend angezeigt bekommst.

---

### Tipps

- **Datenschutz**: Füge eventuell einen Hinweis zum Datenschutz hinzu, damit die Nutzer wissen, wie du mit ihren Daten umgehst.
- **Spam-Schutz**: Nutze ein Captcha (z. B. Google reCAPTCHA oder das in Contact Form 7 integrierte Quiz-Feld), um Spam zu reduzieren.
- **E-Mail-Einstellungen**: Unter „E-Mail“ (im Formular-Editor) kannst du das Layout deiner E-Mail-Benachrichtigungen anpassen und sicherstellen, dass E-Mails an markus@dickscheit.de geschickt werden.

Fertig! Mit diesen Schritten hast du eine funktionsfähige Kontakt-Seite in WordPress inklusive Kontaktformular erstellt.

### 3. Benutzer

erstelle mir eine kontakt seite in wordpress. meine daten: Markus Dickscheit
Karpfenweg 10
74374 Zaberfeld
E-Mail: markus@dickscheit.de

### 4. Assistent

Hier ist eine kompakte Anleitung, wie du eine Kontakt-Seite in WordPress mit Kontaktformular erstellst. Nutze dafür am besten ein Plugin wie **Contact Form 7** oder **WPForms**, da es schnell eingerichtet ist und zuverlässig funktioniert:

---

## 1. Kontaktformular-Plugin installieren

1. Melde dich in deinem WordPress-Dashboard an.  
2. Gehe zu „Plugins“ → „Installieren“.  
3. Suche z. B. nach **Contact Form 7**.  
4. Klicke auf „Jetzt installieren“ und danach auf „Aktivieren“.  

---

## 2. Kontaktformular erstellen (am Beispiel Contact Form 7)

1. Gehe zu „Contact“ → „Formulare“ (oder „Kontakt“ → „Formulare“).  
2. Ein Standardformular ist meist schon vorhanden („Kontaktformular 1“). Klicke auf „Bearbeiten“.  
3. Bearbeite die Felder nach Wunsch (Name, E-Mail, Betreff, Nachricht usw.).  
4. Scrolle nach unten und speichere.  
5. Du erhältst einen Shortcode in der Form  
   ```
   [contact-form-7 id="123" title="Kontaktformular"]
   ```  
   Kopiere diesen Shortcode.

---

## 3. Neue Seite „Kontakt“ erstellen und veröffentlichen

1. Gehe zu „Seiten“ → „Erstellen“.  
2. Vergib den Seitentitel **Kontakt**.  
3. Füge deine Kontaktdaten sowie den Shortcode ein, zum Beispiel so:

   ```html
   <h2>Kontakt</h2>
   <p>
     Bei Fragen oder Anliegen freue ich mich über deine Nachricht.
     Du erreichst mich außerdem unter:
   </p>
   <p>
     <strong>Markus Dickscheit</strong><br>
     Karpfenweg 10<br>
     74374 Zaberfeld<br>
     E-Mail: <a href="mailto:markus@dickscheit.de">markus@dickscheit.de</a>
   </p>

   <!-- Kontaktformular einfügen -->
   [contact-form-7 id="123" title="Kontaktformular"]
   ```

4. Ersetze den obigen Platzhalter-Shortcode mit dem eigenen, den du in Schritt 2 kopiert hast.  
5. **Speichere** die Seite und klicke auf „Veröffentlichen“.

---

### 4. Zusätzliche Hinweise

- **Spam-Schutz**: Aktiviere ein Captcha (z. B. reCAPTCHA) im Formular, um unerwünschte Nachrichten zu reduzieren.  
- **Datenschutzhinweis**: Achte darauf, einen Hinweis zu hinterlegen, wie du mit eingehenden Daten umgehst.  
- **E-Mail-Einstellungen**: Prüfe bei „E-Mail“ (in den Plugin-Einstellungen), ob Nachrichten an deine Adresse (markus@dickscheit.de) gesendet werden.  

Damit ist deine Kontakt-Seite fertig und einsatzbereit!

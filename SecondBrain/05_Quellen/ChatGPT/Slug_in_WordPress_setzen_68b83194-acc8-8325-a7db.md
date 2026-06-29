---
title: "Slug in WordPress setzen"
type: chatgpt_conversation
source: chatgpt
source_id: "68b83194-acc8-8325-a7db-edd81211de14"
created: 2025-09-03
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# Slug in WordPress setzen

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68b83194-acc8-8325-a7db-edd81211de14`
- Nachrichten: 6

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

wie setze ich in wordpress einen slag

### 2. Assistent

Du meinst wahrscheinlich **Slug** (nicht „Slag“ 😊).  
In WordPress ist der *Slug* der Teil einer URL, der nach dem Domainnamen steht und einen Beitrag, eine Seite oder Kategorie eindeutig beschreibt – meistens in Kleinbuchstaben und ohne Sonderzeichen. Beispiel:  

```
https://deineseite.de/ki-im-alltag/
```

Hier ist `ki-im-alltag` der Slug.  

So setzt oder änderst du ihn:  

1. **Bei Beiträgen oder Seiten**  
   - Gehe im Backend auf **Beiträge → Alle Beiträge** (oder **Seiten**).  
   - Bearbeite den gewünschten Beitrag.  
   - Rechts in der Seitenleiste findest du im **Dokument**-Tab den Bereich **Permalink** (bei neueren WP-Versionen).  
   - Dort kannst du den Slug anpassen. WordPress schlägt ihn normalerweise automatisch aus dem Titel vor, du kannst ihn aber beliebig ändern.  

2. **Bei Kategorien oder Schlagwörtern**  
   - Gehe auf **Beiträge → Kategorien** (oder **Schlagwörter**).  
   - Dort kannst du beim Anlegen oder Bearbeiten auch den Slug setzen.  

**Wichtige Tipps:**  
- Verwende nur **Kleinbuchstaben, Zahlen und Bindestriche**.  
- Vermeide Umlaute (ä → ae, ö → oe, ü → ue, ß → ss), sonst gibt’s manchmal unschöne URLs.  
- Wenn du den Slug später änderst, kann es passieren, dass alte Links ins Leere führen → dafür solltest du dann eine Weiterleitung einrichten.  

Möchtest du, dass ich dir gleich noch eine kleine Anleitung schreibe, wie du **Weiterleitungen einrichtest**, falls du Slugs nachträglich änderst?

### 3. Benutzer

ja

### 4. Assistent

Alles klar – hier kommt die kleine Anleitung für **Weiterleitungen in WordPress**, wenn du Slugs nachträglich änderst. Das ist wichtig, damit alte Links (z. B. aus Google oder von Social Media) nicht ins Leere führen.  

### 1. Einfachste Lösung: Plugin  
Am bequemsten geht es mit einem Plugin:  

- **Redirection** (kostenlos, sehr beliebt und zuverlässig)  
  - Installiere das Plugin unter **Plugins → Installieren → "Redirection" suchen → Aktivieren**.  
  - Danach findest du im Menü **Werkzeuge → Redirection**.  
  - Dort kannst du eine alte URL (z. B. `/ki-im-alltag-alt/`) eintragen und die neue URL (z. B. `/ki-im-alltag/`).  
  - Ab dann werden Besucher automatisch weitergeleitet.  

### 2. Alternative ohne Plugin: `.htaccess` (nur Apache-Server)  
Wenn du direkten Zugriff auf die `.htaccess` hast (z. B. bei IONOS Hosting), kannst du Weiterleitungen auch dort einfügen:  

```apache
Redirect 301 /alter-slug/ https://deineseite.de/neuer-slug/
```

- `301` bedeutet: permanente Weiterleitung.  
- Vorteil: Lädt schneller, weil kein Plugin benötigt wird.  
- Nachteil: Manuelle Pflege ist aufwendiger.  

### 3. SEO-Tipp  
Eine 301-Weiterleitung ist suchmaschinenfreundlich – Google versteht, dass sich die URL dauerhaft geändert hat, und überträgt Ranking-Signale auf die neue Seite.  

---

Willst du, dass ich dir eine kleine Schritt-für-Schritt-Anleitung speziell für **IONOS WordPress-Hosting** schreibe, wie du die Weiterleitungen dort am besten umsetzt?

### 5. Benutzer

ja

### 6. Assistent

Perfekt – dann machen wir es konkret für **WordPress bei IONOS**. Da gibt’s zwei Wege, je nachdem ob du lieber **per Plugin** oder **per .htaccess** arbeitest.  

---

## 1. Weiterleitung über Plugin (empfohlen für Anfänger)
1. Melde dich in deinem **WordPress-Backend** an.  
2. Gehe auf **Plugins → Installieren**.  
3. Suche nach **Redirection** (Autor: John Godley).  
4. Installieren → Aktivieren.  
5. Gehe zu **Werkzeuge → Redirection**.  
6. Beim ersten Start fragt dich das Plugin nach Grundkonfiguration → einfach durchklicken.  
7. Dann „Neue Weiterleitung hinzufügen“:  
   - **Quelle-URL**: dein alter Slug, z. B. `/hallo-welt/`  
   - **Ziel-URL**: die neue URL, z. B. `/ki-im-alltag/`  
8. Speichern. Ab jetzt werden Besucher automatisch weitergeleitet.  

---

## 2. Weiterleitung über `.htaccess` (wenn du direkt auf den Server willst)
IONOS verwendet bei WordPress meistens **Apache** → Weiterleitungen gehen über die Datei `.htaccess`.  

1. Melde dich im **IONOS Kundenbereich** an.  
2. Gehe zu **Hosting → WebspaceExplorer** oder verbinde dich per **FTP**.  
3. Öffne den Ordner, in dem WordPress liegt (meist `htdocs/`).  
4. Dort findest du die Datei `.htaccess`.  
   - Wenn sie nicht angezeigt wird: „versteckte Dateien anzeigen“ aktivieren.  
5. Füge am Ende folgende Zeile hinzu:  

   ```apache
   Redirect 301 /alter-slug/ https://deinedomain.de/neuer-slug/
   ```  

   Beispiel:  

   ```apache
   Redirect 301 /hallo-welt/ https://deineseite.de/ki-im-alltag/
   ```  

6. Datei speichern → hochladen.  

Jetzt leitet der Server automatisch weiter, noch bevor WordPress überhaupt lädt.  

---

## 3. Extra Hinweis
- Ändere nicht zu oft Slugs – jede Änderung erzeugt neue Weiterleitungen.  
- Prüfe nach dem Einrichten, ob die alte URL wirklich sauber weiterleitet.  
- Für viele Weiterleitungen ist **Plugin einfacher** (weil du nicht jedes Mal in die `.htaccess` musst).  

---

Soll ich dir direkt eine kleine **Checkliste geben, wie du herausfindest, ob deine Weiterleitung bei IONOS funktioniert** (inklusive kleinem Trick mit Google)?

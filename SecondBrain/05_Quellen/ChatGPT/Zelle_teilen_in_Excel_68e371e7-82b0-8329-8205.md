---
title: "Zelle teilen in Excel"
type: chatgpt_conversation
source: chatgpt
source_id: "68e371e7-82b0-8329-8205-1b1b332df9df"
created: 2025-10-06
tags:
  - chatgpt
  - import
  - ki
---


# Zelle teilen in Excel

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68e371e7-82b0-8329-8205-1b1b332df9df`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Excel Tabellen Zelle mit Inhalt Zelle teilen

### 2. Assistent

Das lässt sich in Excel auf verschiedene Arten machen – je nachdem, **was du mit „Zelle teilen“ meinst**. Ich erkläre dir kurz die drei typischen Fälle:  

---

### **1. Eine Zelle in zwei Spalten oder Zeilen aufteilen**
In Excel kann man **eine einzelne Zelle nicht physisch teilen** (wie z. B. in Word). Was du tun kannst, ist den **Inhalt der Zelle auf mehrere Zellen aufteilen**.

**Beispiel:**
Zelle A1 enthält `Max Mustermann`.  
Du möchtest Vor- und Nachnamen trennen.

**Lösung:**
1. Markiere die Zelle(n) → z. B. A1:A10.  
2. Menüband → **Daten** → **Text in Spalten**.  
3. Wähle **Getrennt** → Weiter.  
4. Wähle das Trennzeichen (z. B. **Leerzeichen**) → Weiter → Fertig stellen.  
   → Ergebnis: `Max` in Spalte A, `Mustermann` in Spalte B.

---

### **2. Zellinhalt mit einer Formel teilen**
Wenn du lieber eine Formel nutzt:

```excel
=LINKS(A1;FINDEN(" ";A1)-1)
```
→ gibt das Wort **vor dem ersten Leerzeichen** zurück.  

```excel
=TEIL(A1;FINDEN(" ";A1)+1;999)
```
→ gibt den **Rest nach dem ersten Leerzeichen** zurück.  

---

### **3. Zelle visuell „teilen“ (optisch, nicht inhaltlich)**
Wenn du nur **eine Linie** in einer Zelle möchtest (z. B. diagonal geteilt, um Überschriften für Zeile/Spalte zu machen):

1. Markiere die Zelle.  
2. Rechtsklick → **Zellen formatieren** → **Rahmen**.  
3. Wähle die **diagonale Linie**.  
4. Gib z. B. in die obere Ecke „Zeile“ und in die untere „Spalte“ Text ein, indem du **Alt+Enter** nutzt, um eine Zeilenumbruch innerhalb der Zelle zu machen.

---

Möchtest du, dass ich dir ein konkretes Beispiel mit Formeln zeige – etwa „teile nach Komma“ oder „teile Datum in Tag/Monat/Jahr“?

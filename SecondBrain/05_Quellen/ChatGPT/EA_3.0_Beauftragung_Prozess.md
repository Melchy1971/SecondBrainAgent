---
title: "EA 3.0 Beauftragung Prozess"
type: chatgpt_conversation
source: chatgpt
source_id: "68679020-c48c-8007-8171-dab707538461"
created: 2025-07-04
tags:
  - chatgpt
  - import
  - ki
  - projekt
  - sap
---


# EA 3.0 Beauftragung Prozess

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68679020-c48c-8007-8171-dab707538461`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

formatiere nachstehenden text neu und ergänze ihn. Text: EA 3.0 von Cisco beauftragung erfolgt nur im TDN/TDS
Alt in VA36 Komplxe Handelsware oder VA 21 einfache Handelsware, hier muss im falle eines True Forward eine migration erfolgen. Nur manuell möglich
Vorgehensweise:
1.	Anlage ZGSL mit hilfe Stammdatenerfassungsblatt
2.	Ermittlung des alten Lizenz bestand 
3.	Erfassung des alt bestand in sap p02 als werteposition
4.	Im falle eine mehrung – differenz per ebanf beauftragen
5.	Bestellung kommt so ins OPC

### 2. Assistent

**Beauftragung EA 3.0 von Cisco**

---

### 1. Geltungsbereich und Voraussetzungen
- **Leistungsumfang**  
  Enterprise Agreement (EA) 3.0 von Cisco kann **nur** über die Kanäle **TDN/TDS** beauftragt werden.  
- **Alt-Abwicklung**  
  Bisherige Bestellungen liefen über:  
  - **VA36** (komplexe Handelsware)  
  - **VA21** (einfache Handelsware)  
- **True Forward**  
  Erweiterung oder Migration vorhandener Lizenzen unter EA 3.0 („True Forward“) ist **manuell** durchzuführen.  

---

### 2. Begriffsdefinitionen
| Abkürzung | Bedeutung                                            |
|-----------|------------------------------------------------------|
| TDN/TDS   | Technischer Dienst (Netze) / Technische Dienstleistungen |
| VA36      | Kundenauftrag für komplexe Handelsware               |
| VA21      | Kundenauftrag für einfache Handelsware               |
| ZGSL      | Zentrale Geschäfts- und Systemlizenz                 |
| P02       | SAP-Bestelltyp für Wertepositionen                   |
| eBANF     | Elektronische Bestellanforderung                     |
| OPC       | Order Processing Center                              |

---

### 3. Verantwortlichkeiten
- **Order Manager**  
  Erstellung und Anlage der ZGSL in SAP.
- **Lizenz-Administrator**  
  Ermittlung des Altbestands und Nachhaltung im System.
- **Beschaffungsstelle**  
  Aufbau und Freigabe der eBANF, Übergabe an OPC.

---

### 4. Detaillierte Vorgehensweise

1. **Anlage der ZGSL**  
   - Formular: „Stammdatenerfassungsblatt Cisco EA 3.0“  
   - Verantwortlich: Order Manager  
   - Ergebnis: ZGSL-Nummer in SAP

2. **Ermittlung des alten Lizenzbestands**  
   - Quelle: Cisco-Account-Portal oder interne Lizenzdatenbank  
   - Verantwortlich: Lizenz-Administrator  
   - Dokumentation: Excel-Liste oder direkt im Stammdatenerfassungsblatt

3. **Erfassung im SAP P02**  
   - Anlage einer Werteposition im Bestelltyp P02  
   - Feld „Altbestand“ ausfüllen mit ermittelter Lizenzmenge  
   - Verantwortlich: Order Manager

4. **Mehrmengen-Beauftragung**  
   - Ist die neue EA-Menge größer als der Altbestand,  
     → Differenzmenge ermitteln  
   - Anlage einer **eBANF** für die Differenz  
   - Verantwortlich: Beschaffungsstelle

5. **Übergabe an OPC**  
   - eBANF wird im OPC-System übernommen  
   - OPC prüft und erstellt finalen Einkaufsvorgang  
   - Abschließende Kontrolle und Freigabe  

---

### 5. Ergänzende Hinweise
- **Fristen**  
  - Erfassung Altbestand: spätestens 3 Werktage vor geplanter Beauftragung  
  - Bearbeitungszeit im OPC: ca. 5 Werktage  
- **Dokumentation**  
  - Alle Schritte sind im EA-3.0-Projektordner abzulegen (SharePoint).  
  - Änderungsnachweise (True Forward-Migration) im Änderungslog festhalten.  
- **Kommunikation**  
  - Bei Rückfragen an den Cisco-Sales-Manager wenden.  
  - Interne Eskalation über Teamleiter IT-Beschaffung.  

---

#### Beispiel-Checkliste im Übersicht:

| Schritt | Aktion                                         | Verantwortlich       | Frist                |
|---------|------------------------------------------------|----------------------|----------------------|
| 1       | ZGSL anlegen                                   | Order Manager        | –3 Werktage          |
| 2       | Altbestand ermitteln                           | Lizenz-Administrator | –3 Werktage          |
| 3       | Werteposition SAP P02 mit Altbestand anlegen   | Order Manager        | –2 Werktage          |
| 4       | eBANF für Mehrmenge anlegen                    | Beschaffungsstelle   | –1 Werktag           |
| 5       | Auftrag im OPC abschließend bearbeiten         | OPC                  | +5 Werktage          |

Dieses strukturierte Vorgehen stellt sicher, dass Ihre EA 3.0-Beauftragung reibungslos und fristgerecht abläuft – auch bei komplexen True-Forward-Szenarien.

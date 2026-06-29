---
title: "TT Pro"
type: chatgpt_conversation
source: chatgpt
source_id: "69c5578e-dedc-8395-b663-663da3961db2"
created: 2026-03-26
tags:
  - chatgpt
  - code
  - gesundheit
  - import
  - ki
  - projekt
  - sap
  - tischtennis
  - verein
---


# TT Pro

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69c5578e-dedc-8395-b663-663da3961db2`
- Nachrichten: 22

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Assistent

Nachfolgend eine token-sparende Umsetzungsanleitung auf Basis des Masterplans für **TT-Manager Pro**, getrennt nach **Lovable** und **Codex**. Fokus: kleine, überprüfbare Lieferobjekte, klare Modulgrenzen, minimale Prompt-Länge, keine unnötige Redundanz. Grundlage sind Vision, Rollenmodell, Architektur, Module, Datenbank, Sicherheitsmodell und Roadmap aus der Masterplan-Datei. fileciteturn0file0L1-L14

## 1. Umsetzungslogik

### Zielsystem
Die Anwendung ist bereits klar als **React + TypeScript + Vite Frontend**, **Shadcn/ui**, **React Query**, **React Hook Form + Zod** und **Lovable Cloud/PostgreSQL** beschrieben. Das Sicherheitsmodell basiert auf **Supabase Auth**, **RLS**, **rollenbasiertem Zugriff**, **Service-Layer** und **Contexts**. fileciteturn0file0L15-L43 fileciteturn0file0L117-L145

### Ableitung für die Umsetzung
Die effizienteste Reihenfolge ist:

1. Datenmodell und Rollen absichern  
2. Authentifizierung und Grundrouting aufsetzen  
3. Basislayout und Navigation bauen  
4. Kernmodule mit hoher Abhängigkeit umsetzen  
5. Import- und Adminfunktionen ergänzen  
6. Datenschutz, Audit, Deletion absichern  
7. Nice-to-have und Roadmap später

### Prinzip für token-sparende Umsetzung
- Pro Prompt genau **ein Modul oder Teilmodul**
- Immer nur:
  - Ziel
  - Datenquellen
  - UI-Umfang
  - Regeln
  - Akzeptanzkriterien
- Keine Wiederholung des gesamten Masterplans
- Wiederverwendbare globale Standards einmal definieren, danach nur referenzieren

---

## 2. Globale Arbeitsaufteilung

## Tool-Rolle: Lovable
Verwenden für:
- Datenbanktabellen
- RLS
- Auth
- CRUD-Seiten
- Routing
- UI-Strukturen
- Formulare
- Dialoge
- Standard-Services
- schnelle vertikale Features

## Tool-Rolle: Codex
Verwenden für:
- Refactoring
- Service-Layer-Struktur
- Typisierung
- komplexere Business-Logik
- Parsing/Importlogik
- Tests
- Security-Review
- Performance-Optimierung
- Bereinigung von wiederverwendbarem Code

---

## 3. Globaler Basis-Prompt

Diesen Prompt einmal zu Beginn verwenden.

### Tool: Lovable
```text
Baue eine webbasierte Vereinsverwaltungssoftware für Tischtennisvereine namens TT-Manager Pro.

Technik:
- React + TypeScript + Vite
- shadcn/ui + Tailwind
- React Router
- React Query
- React Hook Form + Zod
- Backend/DB in Lovable Cloud mit PostgreSQL

Architekturvorgaben:
- Service-Layer für alle DB-Zugriffe
- Contexts für Auth, Rollen, Saison, Theme, News, MemberData
- Rollen: Admin, Vorstand, Trainer, Spieler, Mitglied, developer
- Row Level Security vorbereiten
- Geschützte Routen
- Deutsche Datumsformate
- Responsive Sidebar-Navigation

Arbeite modulweise. Erzeuge keine unnötigen Demo-Daten. Halte Komponenten klein und wiederverwendbar.
```

### Tool: Codex
```text
Initialisiere die Codebasis für TT-Manager Pro.

Ziele:
- konsistente Ordnerstruktur nach Modulen und Services
- strikte TypeScript-Typen
- Service-Layer je Domain
- wiederverwendbare Zod-Schemas
- zentrale Rollen- und Berechtigungsmodelle
- Helper für Datum, Fehlerbehandlung, API-Antworten

Lieferobjekte:
- Architektur-Review
- empfohlene Ordnerstruktur
- Basistypen
- gemeinsame Utility-Funktionen
- Refactoring-Vorschläge für Skalierbarkeit und geringe technische Schuld
```

---

## 4. Schritt-für-Schritt-Anleitung mit Prompts

## Schritt 1: Datenbank-Grundmodell

Zuerst Kernobjekte: `members`, `teams`, `seasons`, `schedule_matches`, `user_roles`, `roles`, `venues`, `club_settings`. Diese Tabellen tragen fast alle Folgefunktionen. Das Schema im Masterplan zeigt die Kernbeziehungen und die wichtigsten Enums. fileciteturn0file0L69-L111 fileciteturn0file0L145-L176

### Tool: Lovable
```text
Erstelle das grundlegende PostgreSQL-Datenmodell für TT-Manager Pro.

Tabellen zuerst:
- members
- teams
- seasons
- schedule_matches
- user_roles
- roles
- venues
- club_settings

Enforce:
- UUID Primary Keys
- sinnvolle Foreign Keys
- created_at/updated_at wo passend
- Enum für age_group und app_role
- Rollenmodell über user_roles, nicht in members
- Saisonbezug für teams

Liefere:
- Tabellen
- Relationen
- sinnvolle Constraints
- Seed für Systemrollen Admin, Vorstand, Trainer, Spieler, Mitglied
```

### Tool: Codex
```text
Prüfe und verbessere das relationale Datenmodell für:
members, teams, seasons, schedule_matches, user_roles, roles, venues, club_settings.

Ziele:
- Normalisierung prüfen
- FK-Integrität prüfen
- Indizes empfehlen
- spätere Erweiterungen für Import, Datenschutz, Board, Training berücksichtigen
- Namenskonventionen vereinheitlichen

Liefere:
- SQL-Review
- Liste fehlender Indizes
- Liste kritischer Constraints
- kurze Begründung je Änderung
```

---

## Schritt 2: Authentifizierung und Rollenprüfung

Auth und Rollenauflösung sind Grundlage für alle Protected Routes. Im Masterplan sind E-Mail/Passwort, E-Mail-Bestätigung, Session-Verwaltung und Rollenauflösung beschrieben. fileciteturn0file0L111-L120

### Tool: Lovable
```text
Implementiere Authentifizierung für TT-Manager Pro.

Funktionen:
- Login mit E-Mail/Passwort
- Registrierung mit Vorname, Nachname, E-Mail, Passwort
- E-Mail-Bestätigung
- Session-Verwaltung
- AuthContext
- Rollenauflösung aus members -> user_roles
- ProtectedRoute mit Rollenprüfung

UI:
- eine Login/Register-Seite mit Tabs
- Zod-Validierung
- klare Fehlermeldungen

Erzeuge nur produktionsnahe Logik, keine Mock-Auth.
```

### Tool: Codex
```text
Erstelle eine robuste Rollen- und Auth-Architektur.

Ziele:
- AuthContext API definieren
- hasRole(user, role) Helper
- Guards für Route- und Komponentenebene
- Fehlerfälle abfangen: fehlendes member-Profil, ungültige Rolle, Session ohne user_roles
- Typsichere Auth-Modelle

Liefere:
- Interfaces/Typen
- Guard-Utilities
- Vorschlag für Testfälle
```

---

## Schritt 3: Basislayout und Navigation

Die Sidebar ist modulbasiert und rechtegesteuert. Das ist die zentrale Bedienlogik. fileciteturn0file0L198-L224

### Tool: Lovable
```text
Baue das App-Grundlayout für TT-Manager Pro.

Elemente:
- Sidebar mit Club-Logo
- modulbasierte Navigation
- collapsed/expanded Zustand
- geschützte Menüeinträge nach Rolle
- Topbar mit Benutzername und Schnellzugriff auf Profil
- responsive Layout

Module in Navigation:
Dashboard, Mannschaften, Spielplan, Ersatzstellung, Training, Kommunikation, Vorstand, Import, Admin, Einstellungen, Profil, Info

Verwende shadcn/ui und Tailwind.
```

### Tool: Codex
```text
Erstelle ein sauberes Navigationsmodell.

Ziele:
- zentrale Definition aller Routen
- Zuordnung Route -> Modul -> Mindestrolle/Berechtigung
- helper useNavigationPermissions
- keine doppelten Berechtigungsprüfungen in jeder Komponente

Liefere:
- Route-Config
- Permission-Mapping
- Refactoring-Vorschlag für Sidebar-Rendering
```

---

## Schritt 4: Saisonverwaltung zuerst

Viele Daten hängen an der aktiven Saison. Das muss früh stabil sein. fileciteturn0file0L225-L233

### Tool: Lovable
```text
Implementiere Saisonverwaltung.

Funktionen:
- Seasons CRUD
- Felder: name, start_year, end_year, age_group, is_active
- genau eine aktive Saison pro Altersgruppe
- SeasonContext mit aktiver Saison
- Filterung saisonabhängiger Daten vorbereiten

UI:
- Liste
- Formular
- Aktiv-Status umschalten
- Validierung
```

### Tool: Codex
```text
Definiere die Geschäftsregeln für Saisonverwaltung.

Regeln:
- nur eine aktive Saison je age_group
- Teams müssen einer Saison zugeordnet sein
- saisonabhängige Queries zentral kapseln
- Race Conditions bei Aktivwechsel vermeiden

Liefere:
- Service-API
- Validierungslogik
- Hinweise für DB-Constraints/Transaktionen
```

---

## Schritt 5: Mitgliederverwaltung

Mitglieder sind Stammdatenbasis für Rollen, Teams, Verfügbarkeiten, Datenschutz, Training. fileciteturn0file0L145-L176

### Tool: Lovable
```text
Implementiere Mitgliederverwaltung.

Funktionen:
- Mitgliederliste
- Detailansicht
- Anlegen/Bearbeiten
- Status aktiv/passiv
- QTTR/TTR-Felder
- Verknüpfung zu user_id optional
- Rollenzuweisung anzeigen

UI:
- Tabelle mit Suche
- Detailformular
- deutsche Labels
- keine unnötigen Animationen
```

### Tool: Codex
```text
Erstelle memberService und zugehörige Typen.

Ziele:
- CRUD-Methoden
- Such-/Filterlogik
- Mapping DB <-> UI-Modell
- defensive Fehlerbehandlung
- wiederverwendbare Zod-Schemas für Mitgliedsdaten

Liefere:
- Service-Schnittstelle
- Typen
- Validierung
- Refactoring-Hinweise für AdminMembers und Profile-Seiten
```

---

## Schritt 6: Rollen und Berechtigungen

Das Rollenmodell ist doppelt relevant: App-Rollen und modulare Rechte in `roles`. fileciteturn0file0L162-L169 fileciteturn0file0L177-L188

### Tool: Lovable
```text
Baue Rollen- und Rechteverwaltung.

Funktionen:
- Systemrollen anzeigen
- benutzerdefinierte Rollen definieren
- Berechtigungen je Modul mit NONE, READ, WRITE
- Rollen Mitgliedern zuweisen
- Systemrollen nicht löschbar

Module:
dashboard, teams, schedule, members, communication, board, settings, import

UI:
- Rollenliste
- Rechte-Matrix
- Zuweisungsdialog
```

### Tool: Codex
```text
Entwerfe ein typsicheres Permission-System.

Ziele:
- Permission-Model als TypeScript-Typen
- JSON-Rechtestruktur standardisieren
- helper canRead/canWrite
- Fallback-Regeln für Systemrollen
- Konflikte zwischen app_role und custom roles definieren

Liefere:
- Permission-Typen
- Resolver-Logik
- Edge-Case-Liste
```

---

## Schritt 7: Teams und Teamzuordnung

Teams hängen direkt an Saisons und Mitgliedern. fileciteturn0file0L122-L131

### Tool: Lovable
```text
Implementiere Mannschaftsübersicht und Team-Management.

Funktionen:
- Teams nach Altersgruppe listen
- Team anlegen/bearbeiten/löschen
- Liga
- Saisonzuordnung
- Spieler zuordnen
- Position und QTTR im Team pflegen
- Kapitän markieren
- Trainingszeiten pro Team pflegen

Seiten:
- /teams
- /teams/manage/:teamId?
```

### Tool: Codex
```text
Erstelle teamService und teamAssignmentService.

Ziele:
- Team-CRUD
- Spielerzuordnung mit Position
- Upsert-Logik für doppelte Zuordnungen
- Queries nach aktiver Saison optimieren
- Datendopplung zwischen members, team_members und assignments minimieren

Liefere:
- Service-API
- Datenmodell-Review
- Indizes für teambezogene Queries
```

---

## Schritt 8: Spielplan

Hohe Geschäftsrelevanz, viele Folgefeatures. fileciteturn0file0L131-L139

### Tool: Lovable
```text
Implementiere Spielplan-Modul.

Seiten:
- /schedule
- /schedule/team/:teamId

Funktionen:
- Übersicht aller Mannschaften mit Spielanzahl
- Team-Spielplan
- Heim/Auswärts-Anzeige
- Spiellokal mit Adresse
- Ergebnis anzeigen/bearbeiten
- Spiel bearbeiten
- Pin und Code Felder
- Bulk-Bearbeitung für Pins/Codes
- deutsches Datumsformat DD.MM.YYYY

Verwende Dialoge für EditResult, EditMatch und BulkPinCode.
```

### Tool: Codex
```text
Erstelle scheduleService mit sauberer Business-Logik.

Ziele:
- CRUD für schedule_matches
- Bulk-Update für pin/code
- Normalisierung für click-TT Import
- Home/Away-Derivation robust definieren
- Datums- und Sortierlogik zentralisieren

Liefere:
- Service-API
- Mapping-Regeln
- Validierung für Scores und Matchdaten
```

---

## Schritt 9: Verfügbarkeiten und Aufstellung

Abhängigkeit: Mitglieder, Teams, Spielplan. fileciteturn0file0L131-L139

### Tool: Lovable
```text
Erweitere den Team-Spielplan um Verfügbarkeiten und Aufstellung.

Funktionen:
- Spieler-Verfügbarkeit pro Spiel pflegen
- Aufstellungsdialog
- verfügbare / nicht verfügbare Spieler sichtbar
- Rollenzugriff für Trainer, Vorstand, Admin

UI:
- kompakter Dialog
- Teamspieler mit Status
- Speicherung pro Match
```

### Tool: Codex
```text
Definiere die Logik für match_player_availability und Aufstellung.

Ziele:
- Datenmodell und API
- Statusmodell für Verfügbarkeit
- Konflikte bei Teamwechsel/Saisonwechsel behandeln
- konsistente Join-Queries auf members, teams, matches

Liefere:
- Tabellen-/Service-Vorschlag
- Edge Cases
- Performance-Hinweise
```

---

## Schritt 10: Ersatzstellung

Status-Workflow ist klar definiert: `pending`, `accepted`, `rejected`. fileciteturn0file0L139-L144

### Tool: Lovable
```text
Implementiere Modul Ersatzstellung.

Funktionen:
- Übersicht aller Spiele mit nicht verfügbaren Spielern
- Ersatzanfrage erstellen
- Spieler für Ersatz auswählen
- eingehende Anfragen verwalten
- Status pending, accepted, rejected
- Tabs: Ersatz benötigt / Eingehende Anfragen

Verwende Dialoge für CreateRequest und SelectPlayer.
```

### Tool: Codex
```text
Erstelle die Business-Logik für substitute_requests.

Ziele:
- Status-Workflow absichern
- nur berechtigte Rollen dürfen anfragen/verarbeiten
- Konflikte vermeiden: Spieler doppelt angefragt, bereits bestätigt, falsche Saison
- Query-Optimierung für offene Anfragen

Liefere:
- Statusregeln
- Service-API
- Validierungslogik
```

---

## Schritt 11: Training

Mittlere Komplexität, geringe Kernabhängigkeit. fileciteturn0file0L144-L149

### Tool: Lovable
```text
Implementiere Training-Modul.

Funktionen:
- Trainingspartner-Buchung
- Status pending, confirmed, cancelled
- Buchungsübersicht
- Bearbeiten
- Löschen mit Bestätigungsdialog

UI:
- Listenansicht
- Buchungsdialog
- klare Status-Badges
```

### Tool: Codex
```text
Modelliere training_bookings sauber.

Ziele:
- Konsistenzregeln für requester_id und partner_id
- Doppelbuchungen vermeiden
- Datumsvalidierung
- Service-Methoden für create/update/cancel/list

Liefere:
- Service-API
- Edge Cases
- DB-Constraints
```

---

## Schritt 12: Kommunikation

News und Dokumente früh, E-Mail später. Der Masterplan nennt News, Dokumente, Listen, QTTR/TTR-Export. fileciteturn0file0L149-L156

### Tool: Lovable
```text
Implementiere Kommunikationsmodul.

Tabs:
- News
- Dokumente
- Listen
- QTTR/TTR-Liste

Funktionen:
- News anzeigen
- veröffentlichte News filtern
- Dokumentenübersicht
- Kommunikationslisten anzeigen
- QTTR/TTR-Rangliste mit PDF-Export

URL-Parameter sollen aktiven Tab unterstützen.
```

### Tool: Codex
```text
Erstelle newsService und die Basis für Dokumenten- und Listenlogik.

Ziele:
- News CRUD
- Veröffentlichung/Entwurf
- PDF-Export für QTTR/TTR vorbereiten
- wiederverwendbare Query Keys
- saubere Trennung zwischen öffentlicher und interner Kommunikation

Liefere:
- Service-Schnittstellen
- Export-Architektur
- Datenfluss-Review
```

---

## Schritt 13: Vorstandsbereich

Geschützt für `vorstand` und `admin`. fileciteturn0file0L156-L161

### Tool: Lovable
```text
Baue den Vorstandsbereich.

Unterbereiche:
- Vorstandsmitglieder
- News-Editor
- Dokumente
- Sitzungen
- E-Mail
- Listen

Funktionen:
- News erstellen/bearbeiten/veröffentlichen
- Bild-Upload für News
- Sitzungen mit Datum, Ort, Thema
- Sitzungsdokumente hochladen
- Listen mit Rollen-Verknüpfung

Schutz:
- nur admin und vorstand
```

### Tool: Codex
```text
Erstelle Board-Services und prüfe Zugriffskonzept.

Ziele:
- boardMemberService
- boardMeetingService
- meetingDocumentService
- konsistente Upload- und Metadatenlogik
- Trennung interne Dokumente vs öffentliche Dokumente

Liefere:
- Service-API
- Berechtigungsregeln
- Review möglicher Datenlecks
```

---

## Schritt 14: Import-System

Dieses Modul ist geschäftskritisch, aber fehleranfällig. Es sollte nach den Kernmodulen folgen. fileciteturn0file0L161-L168

### Tool: Lovable
```text
Implementiere das Import-System.

Importarten:
- Mitglieder-Import aus Excel/CSV
- Spielplan-Import im click-TT Format
- Pin/Code-Import mit Auto-Matching
- QTTR/TTR-Import

Funktionen:
- Datei-Upload
- clientseitiges Parsing
- Vorschau
- Fehlerliste
- manuelle Zuordnung für nicht-matchbare Einträge
- Vorlagen-Download

Nutze SheetJS und PapaParse.
```

### Tool: Codex
```text
Entwickle robuste Parsing- und Mapping-Logik für Importe.

Ziele:
- Schema-Erkennung
- Normalisierung eingehender Daten
- Duplikaterkennung
- Match-Strategien für Mitglieder und Spiele
- partielle Fehlerbehandlung ohne Komplettabbruch
- Import-Report mit Erfolgen/Fehlern

Liefere:
- Parser-Architektur
- Mapping-Regeln
- Edge Cases für click-TT, CSV, Excel
```

---

## Schritt 15: Admin-Bereich

Admin bündelt Querschnittsfunktionen. fileciteturn0file0L168-L170

### Tool: Lovable
```text
Baue den Admin-Bereich.

Unterbereiche:
- Mitglieder
- Mannschaften
- Spielplan
- PINs & Codes
- Backup
- Löschanfragen

Funktionen:
- zentrale Verwaltungsansichten
- Filter und Suche
- Löschanfragen bearbeiten
- Backup-Export bereitstellen

Schutz:
- admin und vorstand
```

### Tool: Codex
```text
Prüfe den Admin-Bereich auf Konsistenz und Wartbarkeit.

Ziele:
- redundante CRUD-Logik identifizieren
- generische Tabellen-/Dialogmuster extrahieren
- Auditierbarkeit kritischer Änderungen erhöhen
- Fehler- und Berechtigungsbehandlung vereinheitlichen

Liefere:
- Refactoring-Plan
- gemeinsame Komponenten/Utilities
- Risikoanalyse
```

---

## Schritt 16: Einstellungen

12 Unterseiten. Große Fläche. Modular bauen. fileciteturn0file0L170-L176

### Tool: Lovable
```text
Implementiere Einstellungsbereich mit separater Unterseiten-Navigation.

Unterseiten:
- Rollen
- Rollen & Rechte
- Mein Profil
- Vereinsdaten
- Saisonverwaltung
- Spiellokale
- Darstellung
- Benachrichtigungen
- Datenschutz
- Sicherheit
- Backup
- Gefahrenzone

Ziele:
- einheitliches Layout
- rollenabhängige Zugriffe
- Formulare mit klarer Validierung
```

### Tool: Codex
```text
Entwerfe eine skalierbare Struktur für die Settings-Seiten.

Ziele:
- gemeinsame Form-Patterns
- Access-Control je Unterseite
- Standardisierung von Save/Cancel/Dirty-State
- Wiederverwendung von Section-Layouts und Schemas

Liefere:
- Strukturvorschlag
- gemeinsame Typen
- Wiederverwendbarkeitsplan
```

---

## Schritt 17: Datenschutz, Audit, Deletion

Dieses Modul ist systemkritisch. Der Masterplan nennt Privacy Consents, Audit-Log und Löschanfragen explizit. fileciteturn0file0L177-L188

### Tool: Lovable
```text
Implementiere Datenschutzfunktionen.

Funktionen:
- Privacy-Consents pro Mitglied
- Consent-Historie/Audit-Log
- Löschanfrage erstellen
- Löschanfrage-Workflow im Admin-Bereich
- Datenschutz-Seite in Settings

Anforderungen:
- klare Zustimmungsschalter
- Zeitstempel speichern
- Auditierbarkeit sichtbar machen
```

### Tool: Codex
```text
Prüfe und implementiere Datenschutz- und Audit-Logik.

Ziele:
- Modell für member_privacy_consents
- consent_audit_log mit nachvollziehbaren Änderungen
- deletion_requests Statusmodell
- Sicherheitsreview für personenbezogene Daten
- Minimierung ungewollter Offenlegung

Liefere:
- Datenmodell
- Prozesslogik
- Risiken und Gegenmaßnahmen
```

---

## Schritt 18: RLS und Sicherheitsabschluss

RLS ist laut Masterplan auf allen Tabellen aktiv vorgesehen. Funktionen `has_role()` und `is_admin_or_board()` sind Kernbestandteile. fileciteturn0file0L177-L188

### Tool: Lovable
```text
Implementiere Row Level Security für alle produktiven Tabellen.

Anforderungen:
- Policies pro Rolle
- Nutzung von has_role(_user_id, _role)
- Nutzung von is_admin_or_board(_user_id)
- Standard: deny by default
- Mitglieder sehen nur erlaubte Daten
- Admin/Vorstand mit erweiterten Rechten

Liefere funktionierende Policies ohne rekursive Fehler.
```

### Tool: Codex
```text
Führe ein Security-Review für RLS und Berechtigungen durch.

Ziele:
- Policy-Lücken finden
- Rekursion vermeiden
- Privilegienausweitung verhindern
- öffentliche vs interne Daten trennen
- Testszenarien für jede Rolle definieren

Liefere:
- Review-Liste
- empfohlene SQL-Policies
- Rollentestmatrix
```

---

## Schritt 19: Profil und Info-Seite

Geringes Risiko, gute Abrundung. fileciteturn0file0L176-L176

### Tool: Lovable
```text
Implementiere Profil- und Info-Seite.

Profil:
- Avatar
- Name
- Status
- QTTR
- Rollen
- Teams
- Passwort
- Profil bearbeiten

Info:
- Vereinsdaten aus club_settings
- Tool-Version
- Build-Datum
- Tech-Stack
- Support-Mail
```

### Tool: Codex
```text
Standardisiere die Datenversorgung für Profil und Info.

Ziele:
- Member-ViewModel
- zusammengesetzte Queries für Rollen/Teams
- sichere öffentliche Club-Info getrennt von internen Daten

Liefere:
- Query-Plan
- Typen
- Sicherheitsprüfung
```

---

## Schritt 20: Abschluss mit Qualitätssicherung

### Tool: Lovable
```text
Führe ein Gesamt-Review der App durch.

Prüfe:
- Routing
- Rollenbasierte Navigation
- Formularvalidierung
- Lade- und Fehlerzustände
- Responsive Verhalten
- Konsistenz von Labels und Seitenstrukturen

Korrigiere nur produktionsrelevante Probleme.
```

### Tool: Codex
```text
Führe einen technischen Abschlussreview durch.

Prüfe:
- TypeScript Strict Mode Fehler
- Service-Duplizierung
- Query Keys
- Performance von Listen
- Fehlerbehandlung
- Sicherheitsrisiken
- Testlücken

Liefere:
- priorisierte Mängelliste
- konkrete Refactoring-Schritte
- minimale Teststrategie
```

---

## 5. Empfohlene Umsetzungsreihenfolge

Maximal effizient in dieser Reihenfolge:

1. Datenbank-Grundmodell  
2. Auth + Rollen  
3. Layout + Routing + Navigation  
4. Saisonverwaltung  
5. Mitglieder  
6. Rollen & Rechte  
7. Teams  
8. Spielplan  
9. Verfügbarkeit/Aufstellung  
10. Ersatzstellung  
11. Training  
12. Kommunikation  
13. Vorstandsbereich  
14. Import  
15. Admin  
16. Einstellungen  
17. Datenschutz/Audit/Deletion  
18. RLS/Security-Hardening  
19. Profil/Info  
20. Review/Refactoring/Tests

Begründung: Diese Reihenfolge minimiert Rework, weil erst die Abhängigkeiten und Sicherheitsgrenzen stabilisiert werden, dann die operativen Module folgen.

---

## 6. Token-sparende Prompt-Regeln

Für alle weiteren Prompts diese Regeln einhalten:

- Maximal 8–12 Zeilen pro Prompt
- Nur ein Modul pro Prompt
- Immer gleiche Struktur:
  - Ziel
  - Funktionen
  - Datenquellen
  - UI
  - Regeln
- Keine Wiederholung des Tech-Stacks in jedem Prompt
- Keine langen Erläuterungen
- Keine Roadmap-Features vor MVP-Funktionen
- Bei Folgeprompts nur Delta beschreiben

### Kompakte Prompt-Schablone für Lovable
```text
Implementiere [Modul/Seite].

Funktionen:
- ...
- ...

Daten:
- Tabellen/Contexts: ...

UI:
- ...

Regeln:
- ...
- ...
```

### Kompakte Prompt-Schablone für Codex
```text
Erstelle/prüfe [Service/Logik].

Ziele:
- ...
- ...
- ...

Liefere:
- ...
- ...
```

---

## 7. Kritische Abhängigkeiten

1. **Saisonmodell vor Teams und Spielplan**  
2. **Mitglieder vor Rollen, Teams, Training, Datenschutz**  
3. **Spielplan vor Ersatzstellung und Aufstellung**  
4. **Rollenmodell vor Navigation und RLS**  
5. **Import erst nach stabilen Zieltabellen**  
6. **Datenschutz erst sinnvoll nach Member-Modell und Auth**

---

## 8. Vermeidbare Fehler

- Rollen direkt in `members` speichern statt über `user_roles`
- RLS zu spät einführen
- Importlogik vor stabilem Datenmodell bauen
- Team- und Saisonbezug nicht konsequent durchziehen
- Rechte nur im Frontend prüfen
- zu große Lovable-Prompts mit mehreren Modulen
- fehlende Normalisierung bei click-TT Import
- Board- und Communication-Dokumente nicht sauber trennen

Diese Punkte sind durch den Masterplan bereits implizit vorgegeben und sollten nicht neu entschieden werden. fileciteturn0file0L177-L188 fileciteturn0file0L145-L176

---

## 9. Minimaler Startsatz an Prompts

Wenn du sofort anfangen willst, nutze exakt diese Reihenfolge:

### 1. Lovable
```text
Erstelle das grundlegende PostgreSQL-Datenmodell für TT-Manager Pro mit:
members, teams, seasons, schedule_matches, user_roles, roles, venues, club_settings.
Nutze UUIDs, Foreign Keys, Enums für age_group und app_role, Seed für Systemrollen.
Rollen nur über user_roles.
```

### 2. Codex
```text
Prüfe das Datenmodell auf Normalisierung, fehlende Indizes, FK-Integrität und spätere Erweiterbarkeit für Import, Datenschutz und Board-Funktionen.
Liefere nur konkrete Änderungen mit kurzer Begründung.
```

### 3. Lovable
```text
Implementiere Login, Registrierung, E-Mail-Bestätigung, AuthContext, Session-Verwaltung und ProtectedRoute.
Rollenauflösung über members und user_roles.
Zod-Validierung und klare Fehlermeldungen.
```

### 4. Codex
```text
Erstelle typsichere Auth- und Rollen-Utilities mit hasRole, Guard-Logik, Fehlermodellen und Testfällen für fehlende Rollen, fehlendes Profil und unvollständige Sessiondaten.
```

### 5. Lovable
```text
Baue App-Layout mit Sidebar, Topbar, rollenabhängiger Navigation und responsivem Verhalten.
Module: Dashboard, Teams, Spielplan, Ersatzstellung, Training, Kommunikation, Vorstand, Import, Admin, Einstellungen, Profil, Info.
```

### 6. Lovable
```text
Implementiere Saisonverwaltung mit Seasons CRUD, is_active, age_group und SeasonContext.
Genau eine aktive Saison pro Altersgruppe.
Bereite Filterung saisonabhängiger Daten vor.
```

---

Basierend auf der Masterplan-Datei ist diese Reihenfolge die robusteste und mit dem geringsten Rework verbunden. Architektur, Rollen, Module, Sicherheitsmodell, Routen und Datenstruktur sind dort bereits ausreichend präzise definiert. fileciteturn0file0L15-L43 fileciteturn0file0L111-L145 fileciteturn0file0L177-L224

### 2. Benutzer

erstelle mir auf basis der Masterplan datei eine Schritt für schritt  anleitung und erstelle mir die prompts dafür. kennzeichne immer für welches tool. umgesetzt wird mit lovable.dev und codex. achte dabei token sparend umzusetzen

### 3. Benutzer

im bereich Saisonverwaltung muss es eine trennung zwischen Erwachsene und Jugend geben. Rewachsene haben eine vor und rückrunde. Jugend hat immer nur eine halbrunde. daher muss es möglich sein halbe Saisons anlegen zu können

### 4. Assistent

Verstanden. Die Saisonlogik muss angepasst werden.

## Fachliche Regel

**Erwachsene**
- Saison besteht aus **Vorrunde** und **Rückrunde**
- Es müssen **zwei halbe Saisons** pro Gesamtzyklus anlegbar sein

**Jugend**
- Saison besteht immer aus **genau einer Halbrunde**
- Keine Rückrunde innerhalb derselben Saisonlogik

## Konsequenz für das Datenmodell

Die bisherige Annahme „eine Saison = kompletter Zeitraum“ ist zu grob. Es braucht ein Modell, das **halbe Saisons als eigenständige operative Einheiten** abbildet.

### Empfohlene Struktur
Nicht nur `seasons`, sondern:

- `season_cycles`
  - beschreibt den Gesamtzeitraum, z. B. `2026/2027`
  - enthält `age_group` = `adult` oder `youth`

- `season_phases`
  - operative Einheit für Planung, Teams, Spielplan, Import
  - Erwachsene:
    - `first_half`
    - `second_half`
  - Jugend:
    - `single_half`

### Minimale Felder

`season_cycles`
- `id`
- `name`
- `start_year`
- `end_year`
- `age_group`
- `is_active`

`season_phases`
- `id`
- `season_cycle_id`
- `phase_type` = `first_half | second_half | single_half`
- `name`
- `start_date`
- `end_date`
- `is_active`
- `sort_order`

## Harte Regeln

1. Für `adult` sind nur `first_half` und `second_half` erlaubt.
2. Für `youth` ist nur `single_half` erlaubt.
3. Pro Zyklus:
   - Erwachsene: maximal 2 Phasen
   - Jugend: maximal 1 Phase
4. Teams, Spielplan, Verfügbarkeiten, Ersatzstellungen und Importe dürfen nicht nur auf den Zyklus, sondern müssen auf die **Phase** referenzieren.
5. „Aktive Saison“ muss künftig sauber getrennt werden:
   - aktiver Zyklus
   - aktive Phase

## Auswirkung auf bestehende Module

### Teams
Teams müssen einer **Season Phase** zugeordnet werden, nicht nur einer Saison.

### Spielplan
Spiele müssen immer auf eine **Season Phase** referenzieren.

### Import
click-TT-Import und PIN/Code-Import müssen auf Phase mappen:
- Erwachsene Vorrunde → `first_half`
- Erwachsene Rückrunde → `second_half`
- Jugend → `single_half`

### Navigation / Filter
Im UI müssen Filter immer zweistufig sein:
- Altersgruppe
- Saisonphase

## Überarbeiteter Prompt für Lovable

```text
Überarbeite die Saisonverwaltung.

Fachlogik:
- Erwachsene haben pro Saisonzyklus eine Vorrunde und Rückrunde
- Jugend hat pro Saisonzyklus genau eine Halbrunde
- Halbe Saisons müssen als eigenständige operative Einheiten anlegbar sein

Datenmodell:
- season_cycles: Gesamtzyklus mit name, start_year, end_year, age_group, is_active
- season_phases: season_cycle_id, phase_type, name, start_date, end_date, is_active, sort_order
- phase_type: first_half, second_half, single_half

Regeln:
- adult erlaubt nur first_half und second_half
- youth erlaubt nur single_half
- pro adult-Zyklus maximal 2 Phasen
- pro youth-Zyklus maximal 1 Phase
- Teams und schedule_matches auf season_phase referenzieren

UI:
- Saisonzyklen verwalten
- darunter Phasen anlegen/bearbeiten
- aktive Phase sichtbar machen
- klare Trennung Erwachsene/Jugend
```

## Überarbeiteter Prompt für Codex

```text
Überarbeite die Saisonlogik für halbe Saisons.

Ziele:
- trenne season_cycle und season_phase
- validiere adult: first_half + second_half
- validiere youth: nur single_half
- definiere Constraints für maximale Phasen pro Zyklus
- passe Referenzen in teams und schedule_matches auf season_phase an
- prüfe Migrationsstrategie vom bisherigen season-Modell

Liefere:
- Datenmodell-Review
- Constraints
- Service-API
- Migrationshinweise
- Edge Cases
```

## Token-sparende Kurzversion für direkten Einsatz

### Lovable
```text
Baue Saisonverwaltung mit season_cycles und season_phases.

Regeln:
- Erwachsene: first_half + second_half
- Jugend: nur single_half
- adult max 2 Phasen pro Zyklus
- youth max 1 Phase pro Zyklus

Passe teams und schedule_matches auf season_phase an.
Baue UI für Zyklus + Phasenverwaltung mit klarer Trennung Erwachsene/Jugend.
```

### Codex
```text
Refactore Saisonmodell von season zu season_cycle + season_phase.
Validiere:
- adult -> first_half, second_half
- youth -> single_half
Passe Services, Constraints und Referenzen in teams und schedule_matches an.
Liefere Migrationsplan und Edge Cases.
```

## Empfehlung für die bestehende Roadmap

Den bisherigen Schritt **Saisonverwaltung** ersetzen durch:

### Neuer Schritt 4
**Saisonzyklen und Saisonphasen**

Reihenfolge:
1. `season_cycles`
2. `season_phases`
3. Anpassung `teams`
4. Anpassung `schedule_matches`
5. Anpassung Filter/Contexts
6. danach erst Team- und Spielplanmodule weiterbauen

## Kritischer Punkt

Ohne diese Trennung entsteht später Rework in:
- Teamzuordnung
- Spielplanlogik
- Importlogik
- Berechtigungsfilter
- aktive Saisonanzeige

Die korrekte operative Einheit ist nicht „Saison“, sondern **Saisonphase**. Der Saisonzyklus bleibt nur die fachliche Klammer.

### 5. Benutzer

{"asset_pointer": "sediment://file_000000000c3871f998ab02220239ab4d", "content_type": "image_asset_pointer", "fovea": null, "height": 627, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 19299, "width": 1048}
im Profil müssen alle informationen zu einem profil angezeigt werden. 2 weitere Reiter im Profil einfügen für  Rollen und Mannschaften

### 6. Assistent

Korrekt. Das Profil ist derzeit fachlich unvollständig.

## Zielbild Profil

Das Profil braucht **3 Reiter**:

1. **Persönliche Daten**
2. **Rollen**
3. **Mannschaften**

Damit wird das Profil zur vollständigen Benutzeransicht statt nur zu einer Stammdatenmaske.

---

## Fachliche Anforderungen

### Reiter 1: Persönliche Daten
Anzeige und Bearbeitung aller profilorientierten Daten.

**Anzuzeigen**
- Vorname
- Nachname
- E-Mail
- Telefon
- Straße
- PLZ
- Ort
- Status aktiv/passiv
- Avatar/Initialen
- optional: Geburtsdatum
- optional: QTTR/TTR
- optional: Notizen, falls im Modell vorhanden

**Regeln**
- Bearbeitbar nur für eigene Daten oder berechtigte Admin-/Vorstandsrollen
- E-Mail aus Auth und Profil konsistent halten
- Leere Felder sauber als „nicht hinterlegt“ behandeln

---

### Reiter 2: Rollen
Volle Sicht auf alle dem Profil zugeordneten Rollen.

**Anzuzeigen**
- App-Rollen aus `user_roles`
- zugewiesene benutzerdefinierte Rollen
- Berechtigungsniveau je Rolle
- Herkunft der Rolle:
  - Systemrolle
  - benutzerdefinierte Rolle
- optional: Gültigkeit / Aktiv-Status

**Regeln**
- Normale Nutzer: nur lesen
- Admin/Vorstand: Rollen verwalten, falls gewünscht
- Systemrollen klar kennzeichnen
- Keine Rollendaten direkt aus UI zusammenbauen, immer aus Rollen-Resolver laden

---

### Reiter 3: Mannschaften
Volle Sicht auf Teamzuordnungen des Profils.

**Anzuzeigen**
- Mannschaftsname
- Altersgruppe
- Saisonphase
- Liga
- Position im Team
- Kapitän ja/nein
- Trainingszeit
- Status aktiv/inaktiv

**Regeln**
- Nicht nur aktuelle Mannschaft, sondern alle relevanten Teamzuordnungen der aktiven Phase
- Wenn historische Zuordnungen existieren: trennen in aktuell / historisch
- Teamdaten aus Teamzuordnung laden, nicht aus Member-Stammdaten ableiten

---

## UI-Struktur

Empfohlen:

- Kopfbereich mit:
  - Avatar
  - Name
  - Status
  - E-Mail
  - Kurzbadges für wichtigste Rollen
- darunter Tabs:
  - **Persönliche Daten**
  - **Rollen**
  - **Mannschaften**

Damit bleibt die bestehende Oberfläche weitgehend erhalten und wird nur strukturell erweitert.

---

## Konsequenz für Datenversorgung

Das Profil braucht künftig aggregierte Daten aus mehreren Quellen:

- `members`
- `user_roles`
- `roles`
- `team_members` oder äquivalente Zuordnungstabelle
- `teams`
- `season_phases`

Das Profil darf nicht mehr nur ein einfaches `member`-Formular sein. Es braucht ein **Profile View Model**.

---

## Prompt für Lovable

```text
Überarbeite die Profilseite.

Ziel:
- vollständige Profilansicht statt nur Stammdatenformular

UI:
- Kopfbereich mit Avatar/Initialen, Name, Status, E-Mail, Rollen-Badges
- Tabs:
  1. Persönliche Daten
  2. Rollen
  3. Mannschaften

Tab Persönliche Daten:
- Vorname, Nachname, E-Mail, Telefon, Straße, PLZ, Ort, Status
- Bearbeiten/Speichern/Abbrechen
- leere Felder sauber darstellen

Tab Rollen:
- alle zugeordneten Rollen anzeigen
- Systemrolle vs benutzerdefinierte Rolle kennzeichnen
- Rollen als Badges oder Tabelle

Tab Mannschaften:
- alle Teamzuordnungen des Profils anzeigen
- Mannschaft, Altersgruppe, Saisonphase, Liga, Position, Kapitän, Trainingszeit

Regeln:
- Daten aus members, user_roles, roles, teams und Teamzuordnungen laden
- responsive umsetzen
- deutsche Labels
```

---

## Prompt für Codex

```text
Überarbeite die Profil-Datenlogik.

Ziele:
- erstelle ein ProfileViewModel aus members, user_roles, roles, team assignments, teams, season_phases
- trenne persönliche Daten, Rollen und Mannschaften sauber
- vermeide Logik direkt in der UI
- definiere typsichere Modelle für ProfileHeader, ProfileRoles, ProfileTeams
- prüfe Berechtigungen für Selbstansicht vs Admin/Vorstand

Liefere:
- ViewModel-Struktur
- Service-API
- Mapping-Regeln
- Edge Cases für fehlende Rollen oder fehlende Teamzuordnungen
```

---

## Token-sparende Kurzversion

### Lovable
```text
Überarbeite die Profilseite auf 3 Tabs:
- Persönliche Daten
- Rollen
- Mannschaften

Zeige im Header Avatar, Name, Status, E-Mail und Rollen-Badges.

Persönliche Daten:
- Vorname, Nachname, E-Mail, Telefon, Straße, PLZ, Ort, Status

Rollen:
- alle Rollen aus user_roles/roles
- Systemrolle vs benutzerdefiniert kennzeichnen

Mannschaften:
- Mannschaft, Altersgruppe, Saisonphase, Liga, Position, Kapitän, Trainingszeit

Daten aus members, user_roles, roles, team assignments und teams laden.
```

### Codex
```text
Erstelle ein ProfileViewModel für:
- persönliche Daten
- Rollen
- Mannschaften

Quellen:
members, user_roles, roles, team assignments, teams, season_phases

Liefere:
- typsichere Modelle
- Service-API
- Mapping
- Berechtigungslogik
```

---

## Zusätzlicher Strukturhinweis

Der bisherige Bereich „Passwort ändern“ sollte nicht als eigener großer Block unterhalb der Seite bleiben, sondern entweder:

- im Tab **Persönliche Daten** als eigene Sektion
oder
- als vierter Tab **Sicherheit**

Sauberer für spätere Erweiterungen wäre:

1. Persönliche Daten  
2. Rollen  
3. Mannschaften  
4. Sicherheit

Für den aktuellen Scope reichen die von dir geforderten 3 Reiter.

### 7. Assistent

Erweiterung ist konsistent mit fachlichem Ziel: Profil = zentrale Spielerakte.

## Anpassung Datenmodell

### Tabelle: `members` erweitern

Neue Felder:

- `qttr` (integer)
- `ttr` (integer)
- `phone` (varchar)
- `mobile` (varchar)
- `birthdate` (date)

### Regeln

- `qttr`, `ttr` ≥ 0
- `birthdate` ≤ aktuelles Datum
- `mobile` optional, aber bevorzugt gegenüber `phone`
- keine Berechnung im Frontend (z. B. Alter), nur Anzeige

---

## Auswirkungen auf bestehende Logik

### 1. Profil
- Felder müssen im Tab **Persönliche Daten** erscheinen
- Editierbar je nach Rolle
- Geburtstagsformat: `DD.MM.YYYY`

### 2. Kommunikation
- Mobilnummer priorisieren für zukünftige Kontaktlogik
- Grundlage für E-Mail/SMS/WhatsApp-Erweiterung

### 3. Mannschaften
- QTTR/TTR optional in Teamkontext anzeigen (Sortierung/Reihenfolge)

### 4. Import
- QTTR/TTR müssen durch Import überschreibbar sein
- Birthdate aus CSV/Excel parsen (Formatvarianten berücksichtigen)

---

## UI-Anpassung (Profil → Persönliche Daten)

Neue Struktur:

- Vorname | Nachname  
- E-Mail  
- Telefon | Mobil  
- Straße | PLZ  
- Ort  
- Geburtstag  
- QTTR | TTR  

### Darstellung
- QTTR/TTR als numerische Felder ohne Dezimalstellen
- Geburtstag mit Datepicker
- Mobil visuell priorisieren (links oder hervorgehoben)

---

## Prompt für Lovable

```text
Erweitere das Mitgliederprofil um zusätzliche Felder.

Neue Felder:
- qttr (number)
- ttr (number)
- phone (string)
- mobile (string)
- birthdate (date)

UI im Tab Persönliche Daten:
- Telefon und Mobil getrennt anzeigen
- Geburtstag mit Datepicker (Format DD.MM.YYYY)
- QTTR und TTR als numerische Felder

Regeln:
- qttr/ttr >= 0
- birthdate darf nicht in der Zukunft liegen
- leere Felder sauber behandeln
- bestehendes Layout beibehalten, nur erweitern

Speicherung:
- in members Tabelle persistieren
```

---

## Prompt für Codex

```text
Erweitere das Member-Modell um:
qttr, ttr, phone, mobile, birthdate.

Ziele:
- TypeScript-Typen aktualisieren
- Zod-Schema erweitern (Validierung für Datum und Zahlen)
- Mapping DB <-> UI anpassen
- Default-Werte und Null-Handling definieren
- Datumsformat zentral standardisieren

Liefere:
- aktualisierte Typen
- Validierung
- Mapping-Funktionen
- Edge Cases (leere Werte, ungültige Zahlen, falsches Datumsformat)
```

---

## Edge Cases

- Import liefert QTTR als String → Parsing erforderlich
- Geburtstage in verschiedenen Formaten (`YYYY-MM-DD`, `DD.MM.YYYY`)
- Mitglieder ohne Telefonnummer → kein Fehler
- QTTR/TTR unbekannt → `null`, nicht `0`
- Alte Datensätze ohne Felder → Migration mit NULL-Werten

---

## Kritischer Punkt

QTTR/TTR sind **zeitabhängige Werte**.  
Langfristig falsch, diese nur im Member zu speichern.

Zukünftige Struktur (nicht jetzt umsetzen):
- `member_ratings` mit:
  - `member_id`
  - `qttr`
  - `ttr`
  - `valid_from`

Aktuell akzeptabel:
- Snapshot im `members`-Record

---

## Minimaler Direkt-Prompt

### Lovable
```text
Erweitere Profil um:
QTTR, TTR, Telefon, Mobil, Geburtstag.

Validierung:
- qttr/ttr >= 0
- birthdate nicht in Zukunft

UI:
- Datepicker für Geburtstag
- numerische Felder für QTTR/TTR
- Telefon und Mobil getrennt

Speichere alles in members.
```

### Codex
```text
Erweitere Member-Typen und Zod-Schema um:
qttr, ttr, phone, mobile, birthdate.

Validiere Zahlen und Datum.
Passe Mapping und Null-Handling an.
```

### 8. Benutzer

zusätzliche Felder: QTTR, TTR, Telefon, Mobil, geburtstag

### 9. Assistent

Ergänzung ist fachlich relevant (Vereinszugehörigkeit, Historie, Beitragslogik).

## Anpassung Datenmodell

### Tabelle: `members`

Neues Feld:

- `member_since` (date)

### Semantik

- Eintrittsdatum in den Verein
- darf nicht in der Zukunft liegen
- optional für Altbestände, aber sollte langfristig Pflichtfeld sein

---

## Auswirkungen

### 1. Profil (Persönliche Daten)

Erweiterung der bestehenden Struktur:

- Geburtstag  
- **Mitglied seit**  
- QTTR | TTR  

### 2. Nutzung

- Grundlage für:
  - Jubiläen
  - Ehrungen
  - Beitragslogik (optional später)
  - Filter (z. B. Mitglieder > X Jahre)

### 3. Anzeige

- Format: `DD.MM.YYYY`
- optional:
  - zusätzliche Anzeige: „seit X Jahren“ (Frontend-Berechnung, nicht speichern)

---

## UI-Anpassung

Neue Feldgruppe:

- Geburtstag | Mitglied seit  
- QTTR | TTR  

Reihenfolge logisch chronologisch:
1. persönliche Daten  
2. Kontaktdaten  
3. Zeitdaten (Geburtstag, Mitglied seit)  
4. Leistungsdaten (QTTR/TTR)

---

## Validierungsregeln

- `member_since <= heute`
- `member_since >= birthdate` (wenn birthdate vorhanden)
- kein Default-Wert setzen (kein automatisches „heute“)

---

## Prompt für Lovable

```text
Erweitere das Mitgliederprofil um das Feld "Mitglied seit".

Feld:
- member_since (date)

UI im Tab Persönliche Daten:
- Datepicker für "Mitglied seit"
- Anzeigeformat DD.MM.YYYY
- Position unterhalb von Geburtstag

Validierung:
- darf nicht in der Zukunft liegen
- wenn birthdate vorhanden: member_since >= birthdate

Speicherung:
- in members Tabelle persistieren
- leere Werte erlauben
```

---

## Prompt für Codex

```text
Erweitere das Member-Modell um member_since (date).

Ziele:
- TypeScript-Typ erweitern
- Zod-Schema mit Validierung:
  - nicht in der Zukunft
  - >= birthdate (optional)
- Mapping DB <-> UI anpassen
- konsistentes Datumsformat sicherstellen

Liefere:
- aktualisierte Typen
- Validierungslogik
- Edge Cases (kein birthdate, falsche Reihenfolge, null-Werte)
```

---

## Edge Cases

- Mitglied ohne Geburtsdatum → nur Zukunftsprüfung
- Import liefert nur Jahr → auf `01.01.YYYY` normalisieren oder als Fehler markieren
- Eintritt vor Geburtsdatum → ablehnen
- Altmitglieder ohne Datum → `null`, kein Fallback

---

## Kritischer Hinweis

Langfristig ist `member_since` allein nicht ausreichend für Historie.

Saubere Erweiterung (später):
- `member_history`
  - Eintritt
  - Austritt
  - Wiedereintritt

Aktuell ausreichend:
- ein Feld im `members`-Record

---

## Minimaler Prompt

### Lovable
```text
Füge Feld "Mitglied seit" (member_since) hinzu.

UI:
- Datepicker
- Format DD.MM.YYYY

Validierung:
- nicht in Zukunft
- >= birthdate wenn vorhanden

Speichern in members.
```

### Codex
```text
Erweitere Member um member_since (date).
Validiere: nicht in Zukunft, >= birthdate.
Passe Typen und Zod-Schema an.
```

### 10. Benutzer

zusätzlich Mitglied seid

### 11. Benutzer

absofort nur noch prompts für codex

### 12. Assistent

```text
Erweitere das Member-Modell um folgende Felder:
qttr, ttr, phone, mobile, birthdate, member_since.

Ziele:
- TypeScript-Typen vollständig aktualisieren
- klare Trennung zwischen optionalen und Pflichtfeldern
- keine impliziten Defaults setzen

Validierung (Zod):
- qttr, ttr: number >= 0 oder null
- birthdate: date <= heute
- member_since: date <= heute
- member_since >= birthdate (falls birthdate vorhanden)
- phone, mobile: string optional, keine harte Formatvalidierung

Mapping:
- DB <-> UI sauber trennen
- null statt 0 für unbekannte QTTR/TTR
- Datumsformate zentral normalisieren (ISO intern)

Liefere:
- aktualisierte Member-Typen
- erweitertes Zod-Schema
- Mapping-Funktionen
- zentrale Date-Helper (parse, format)

Edge Cases:
- fehlendes birthdate
- member_since vor birthdate
- String-Werte aus Import für qttr/ttr
- unterschiedliche Datumsformate (DD.MM.YYYY, ISO)
```

### 13. Benutzer

{"asset_pointer": "sediment://file_000000009158724399ac6a3767656788", "content_type": "image_asset_pointer", "fovea": null, "height": 741, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 13233, "width": 353}
anzeige immer in deutsch

### 14. Assistent

```text id="g3k2mf"
Internationalisiere die Rollen- und Rechte-Matrix vollständig auf Deutsch.

Ziele:
- alle Modulnamen in Deutsch anzeigen
- alle Berechtigungswerte in Deutsch anzeigen
- keine Hardcoded Strings im UI

Mapping Module (EN -> DE):
- Members -> Mitglieder
- Teams -> Mannschaften
- Matches -> Spiele
- Schedule -> Spielplan
- Seasons -> Saisons
- Training -> Training
- Substitutes -> Ersatzstellung
- Communication -> Kommunikation
- Board -> Vorstand
- Settings -> Einstellungen
- Import -> Import
- Admin -> Administration

Mapping Berechtigungen:
- NONE -> Keine
- READ -> Lesen
- WRITE -> Schreiben

Umsetzung:
- zentrale i18n-Map oder Konstanten (z. B. moduleLabels, permissionLabels)
- UI greift nur auf diese Maps zu
- keine direkten Strings in Komponenten

Zusätzlich:
- Fallback für unbekannte Module definieren
- Typensicherheit für Module und Permissions erzwingen

Liefere:
- Mapping-Konstanten
- Typdefinitionen (ModuleKey, PermissionLevel)
- Refactoring der Matrix-Komponente
```

### 15. Benutzer

was fehlt alles noch ?

### 16. Assistent

Es fehlt noch ein großer Teil. Der Masterplan ist deutlich breiter als die bisher besprochenen Punkte Profil, Saisonlogik und Sprachlabels. Die noch offenen Blöcke sind: Authentifizierung, Rollenauflösung, Service-Layer, React Contexts, Routing, Teams, Spielplan, Ersatzstellung, Training, Kommunikation, Vorstandsbereich, Import-System, Admin-Bereich, Einstellungen, Datenschutz, RLS, Info-Seite, Entwickler-Bereich, Deployment-Qualität sowie Roadmap-Themen. fileciteturn1file0L1-L14 fileciteturn1file1L1-L28 fileciteturn1file2L1-L28 fileciteturn1file4L1-L19

## Fehlende Kernbereiche

### 1. Datenmodell-Refactor für Saisonphasen
Der Masterplan kennt noch `seasons`; deine Fachlogik braucht jetzt `season_cycles` und `season_phases`. Dadurch fehlen noch Migration, FK-Anpassungen für `teams`, `schedule_matches`, `team_members` bzw. Zuordnungen und saisonphasenbasierte Filterlogik. fileciteturn1file2L23-L28

**Codex-Prompt**
```text id="cdx001"
Refactore das Saisonmodell von seasons auf season_cycles + season_phases.

Ziele:
- Migration von bestehender seasons-Struktur
- adult: first_half + second_half
- youth: single_half
- FK-Anpassungen in teams, schedule_matches und team assignments
- aktive Phase statt nur aktive Saison unterstützen

Liefere:
- Migrationsplan
- aktualisierte Typen
- Constraints
- Query-/Service-Anpassungen
- Edge Cases
```

### 2. Profil vollständig machen
Im Masterplan hat das Profil Tabs für Bearbeiten, Rollen, Teams und Passwort. Offen sind noch Security-Tab/Passwortlogik, Mannschaftsübersicht pro Altersgruppe und Saisonphase, Trainingszeiten und vollständiges ViewModel. fileciteturn1file2L15-L18

**Codex-Prompt**
```text id="cdx002"
Vervollständige die Profil-Datenlogik.

Ziele:
- ProfileViewModel für persönliche Daten, Rollen, Mannschaften, Passwort/Sicherheit
- Mannschaften nach Altersgruppe und season_phase strukturieren
- Trainingszeiten in Teamansicht einbinden
- Self-Service vs Admin/Vorstand Berechtigungen trennen

Liefere:
- ViewModel
- Service-API
- Mapping-Regeln
- Berechtigungslogik
```

### 3. Auth + Rollenauflösung
Noch offen: Login/Register, Sessionmodell, Rollenauflösung aus `user_roles`, Guards, Protected Routes und Fehlerfälle bei fehlenden Member-Profilen. Auth und Rollenprüfung sind im Systemkern vorgesehen. fileciteturn1file0L25-L29 fileciteturn1file1L1-L16

**Codex-Prompt**
```text id="cdx003"
Erstelle die vollständige Auth- und Rollenlogik.

Ziele:
- Auth-Modelle und Session-Typen
- Rollenauflösung über user_roles
- Guards für Route- und Komponentenebene
- Fehlerfälle: Session ohne Member, Session ohne Rollen, inkonsistente Daten
- hasRole/canRead/canWrite Utilities

Liefere:
- Typen
- Resolver
- Guard-Utilities
- Testmatrix
```

### 4. Rollen- und Rechtesystem
Die Matrix ist nur ein Ausschnitt. Offen sind typsichere Permission-Modelle, JSON-Struktur in `roles`, Systemrollen-Schutz, Custom-Rollen-Zuweisung und konsistente deutsche Labels systemweit. Das Berechtigungssystem ist explizit im Masterplan definiert. fileciteturn1file1L1-L11

**Codex-Prompt**
```text id="cdx004"
Baue das vollständige Rollen- und Permission-System.

Ziele:
- PermissionLevel und ModuleKey typsicher definieren
- JSON-Permissions in roles standardisieren
- Systemrollen vor Löschung/Manipulation schützen
- Custom-Rollen-Zuweisungen modellieren
- deutsche Label-Maps zentralisieren

Liefere:
- Typen
- Resolver
- Validierung
- Refactoring der Matrix-Logik
```

### 5. Teams und Teamzuordnungen
Noch offen: Team-CRUD, Saisonphasenbezug, Liga, Spielerzuordnung, Kapitänslogik, Trainingszeiten und Abgrenzung zwischen `team_members` und `member_team_assignments`. Diese Domäne ist im Schema und Service-Layer vorgesehen. fileciteturn1file2L23-L28 fileciteturn1file1L12-L20

**Codex-Prompt**
```text id="cdx005"
Erstelle die Team-Domain vollständig.

Ziele:
- teamService und teamAssignmentService
- Team-CRUD mit season_phase statt season
- Spielerzuordnung, Position, Kapitän, Trainingszeiten
- team_members vs member_team_assignments sauber abgrenzen
- Query-Performance für Teamübersichten

Liefere:
- Service-APIs
- Typen
- DB-Review
- Edge Cases
```

### 6. Spielplan / Matches
Noch offen: Match-CRUD, Teamspielplan, Ergebnislogik, Heim/Auswärts, PIN/Code, Bulk-Update, Verfügbarkeiten und Aufstellung. Der Spielplan ist einer der Kernprozesse. fileciteturn1file2L23-L28

**Codex-Prompt**
```text id="cdx006"
Erstelle die vollständige Match- und Spielplanlogik.

Ziele:
- scheduleService für CRUD, Bulk pin/code, Ergebnis-Updates
- season_phase-basierte Filter
- Heim/Auswärts robust ableiten
- Verfügbarkeiten und Aufstellungen integrierbar machen
- Datums- und Sortierlogik zentralisieren

Liefere:
- Service-API
- Typen
- Validierung
- Edge Cases
```

### 7. Ersatzstellung
Das Modul ist im Masterplan enthalten, bisher aber nicht umgesetzt: Anfrage-Workflow, Status `pending/accepted/rejected`, Rollenzugriffe, Konfliktlogik. fileciteturn1file0L10-L14

**Codex-Prompt**
```text id="cdx007"
Modelliere die Ersatzstellungslogik.

Ziele:
- substitute_requests mit Status-Workflow
- Konflikte verhindern: doppelte Anfrage, bereits bestätigt, falsche season_phase
- Berechtigungen für Trainer, Vorstand, Admin, Spieler
- offene und eingehende Anfragen effizient abfragbar machen

Liefere:
- Datenmodell
- Service-API
- Statusregeln
- Edge Cases
```

### 8. Training
Offen sind Trainingspartner-Buchungen, Doppelbuchungsschutz, Statusmodell und Abgrenzung zwischen Team-Trainingszeiten und individuellen Buchungen. Training ist im Funktionsumfang genannt. fileciteturn1file0L10-L14

**Codex-Prompt**
```text id="cdx008"
Erstelle die Trainings-Domain.

Ziele:
- training_bookings modellieren
- pending/confirmed/cancelled Status
- Doppelbuchungen vermeiden
- requester_id und partner_id sauber validieren
- Team-Trainingszeiten vom Buchungssystem trennen

Liefere:
- Datenmodell
- Service-API
- Validierung
- Edge Cases
```

### 9. Kommunikation
Offen sind News-CRUD, Dokumentenlogik, Listen, QTTR/TTR-PDF-Export und Trennung öffentlich/intern. Das Kommunikationsmodul ist explizit vorgesehen. fileciteturn1file0L5-L12

**Codex-Prompt**
```text id="cdx009"
Erstelle die Kommunikationslogik.

Ziele:
- newsService mit draft/published
- Dokumenten- und Listen-Basisstruktur
- QTTR/TTR-Export vorbereiten
- interne vs öffentliche Inhalte trennen
- Query Keys und Caching standardisieren

Liefere:
- Service-APIs
- Datenfluss
- Export-Architektur
- Sicherheitsgrenzen
```

### 10. Vorstandsbereich
Komplett offen: Vorstandsmitglieder, News-Editor, Sitzungen, Sitzungsdokumente, E-Mail, Listen. Der Bereich ist klar spezifiziert. fileciteturn1file3L1-L11

**Codex-Prompt**
```text id="cdx010"
Erstelle die Board-Domain.

Ziele:
- boardMemberService, boardMeetingService, meetingDocumentService
- interne Dokumente und öffentliche Dokumente strikt trennen
- News, Meetings, Dokumente, E-Mail, Listen modellieren
- Admin/Vorstand Zugriffsgrenzen absichern

Liefere:
- Service-APIs
- Typen
- Berechtigungsregeln
- Risikoanalyse
```

### 11. Import-System
Noch offen: Member-Import, Spielplan-Import, Pin/Code-Import, QTTR/TTR-Import, Mapping, Parsing, Fehlerberichte. Das ist ein Kernziel des Systems. fileciteturn1file0L7-L10 fileciteturn1file3L12-L19

**Codex-Prompt**
```text id="cdx011"
Entwickle die Import-Architektur.

Ziele:
- Parser für CSV/Excel/click-TT
- partielle Fehlerbehandlung ohne Komplettabbruch
- Match-Strategien für members, teams, matches
- QTTR/TTR und Datumsfelder robust normalisieren
- Import-Report mit Erfolgen, Warnungen, Fehlern

Liefere:
- Parser-Design
- Mapping-Regeln
- Typen
- Edge Cases
```

### 12. Admin-Bereich
Offen sind generische Admin-CRUDs, Backup, PIN/Code-Verwaltung und Löschanfragen-Bearbeitung. Das ist als eigener Bereich vorgesehen. fileciteturn1file2L1-L11 fileciteturn1file3L20-L25

**Codex-Prompt**
```text id="cdx012"
Entwerfe den Admin-Bereich technisch konsistent.

Ziele:
- generische CRUD-Muster für Mitglieder, Teams, Spielplan
- PIN/Code-Administration
- Backup- und Export-Schnittstellen
- Löschanfragen administrierbar machen
- gemeinsame Tabellen-/Dialog-Patterns extrahieren

Liefere:
- Refactoring-Plan
- gemeinsame Komponentenlogik
- Risiken
- Prioritäten
```

### 13. Einstellungen
Der Masterplan sieht 12 Unterseiten vor. Davon sind praktisch alle offen oder nur angerissen. fileciteturn1file2L1-L15 fileciteturn1file3L25-L31

**Codex-Prompt**
```text id="cdx013"
Strukturiere den gesamten Settings-Bereich.

Ziele:
- Unterseitenmodell für general, roles, profile, club, season, venues, appearance, notifications, privacy, security, backup, danger
- Access-Control je Unterseite
- gemeinsame Form-Patterns und Dirty-State-Handling
- wiederverwendbare Schemas und Section-Layouts

Liefere:
- Strukturvorschlag
- Typen
- gemeinsame Utilities
- Berechtigungsmodell
```

### 14. Datenschutz, Audit, Löschanfragen
Noch offen: Privacy-Consents, Consent-Audit-Log, Löschworkflow, Datensicht je Rolle. Das ist ausdrücklich Kernziel. fileciteturn1file0L9-L13 fileciteturn1file1L6-L11

**Codex-Prompt**
```text id="cdx014"
Erstelle Datenschutz- und Audit-Logik.

Ziele:
- member_privacy_consents modellieren
- consent_audit_log mit Timestamp, IP, User-Agent
- deletion_requests Workflow
- Datenschutzsicht für Self-Service vs Admin/Vorstand
- personenbezogene Daten minimieren und absichern

Liefere:
- Datenmodell
- Service-API
- Workflow-Regeln
- Sicherheitsreview
```

### 15. RLS / Security Hardening
Noch offen: Policies pro Tabelle, deny-by-default, Rollentestmatrix, Vermeidung von rekursiven Policy-Checks. RLS ist im Masterplan als global aktiv vorgesehen. fileciteturn1file1L1-L6

**Codex-Prompt**
```text id="cdx015"
Führe ein vollständiges RLS- und Security-Review durch.

Ziele:
- Policies für alle produktiven Tabellen
- deny-by-default
- Rollenprüfung nur über user_roles
- rekursive Policy-Checks vermeiden
- öffentliche vs interne Daten strikt trennen

Liefere:
- Policy-Matrix
- SQL-Empfehlungen
- Rollentestmatrix
- Risikoanalyse
```

### 16. React Contexts + Service-Layer
Der Masterplan nennt konkrete Services und Contexts; die zentrale Architektur dafür fehlt noch. fileciteturn1file1L12-L28

**Codex-Prompt**
```text id="cdx016"
Baue die Anwendungsarchitektur mit Services und Contexts konsistent aus.

Ziele:
- Services: member, team, teamAssignment, schedule, season, news, role, roleDefinition, memberRoleAssignment, boardMember, boardMeeting, meetingDocument
- Contexts: Auth, Role, Season, Theme, News, MemberData
- UI frei von Datenzugriffslogik halten
- Query Keys und Fehlerbehandlung standardisieren

Liefere:
- Zielstruktur
- Abhängigkeitsregeln
- Service-Kontrakte
- Refactoring-Plan
```

### 17. Routing / Navigation / Deutsch überall
Es fehlt die systemweite Sprachkonsistenz, nicht nur in der Rollenmatrix. Auch Routing-Labels, Settings-Navigation und Modulbezeichnungen müssen zentralisiert werden. Routing und Navigation sind ausdrücklich definiert. fileciteturn1file1L28-L28 fileciteturn1file2L1-L18

**Codex-Prompt**
```text id="cdx017"
Standardisiere Routing-, Navigations- und UI-Labels vollständig auf Deutsch.

Ziele:
- zentrale Label-Maps für Module, Settings-Unterseiten, Rollen, Permissions, Status
- RouteConfig mit Label, Guard, Modulbezug
- keine Hardcoded UI-Strings in Komponenten
- Fallbacks für unbekannte Schlüssel

Liefere:
- Typen
- Konstanten
- Refactoring-Plan
- betroffene Komponentenliste
```

### 18. Info-Seite und Entwickler-Bereich
Noch offen: Info-Seite mit Vereinsdaten, Build-Datum, Version und Support-Mail sowie Entwickler-Bereich mit Lizenzverwaltung. Beides ist im Masterplan genannt. fileciteturn1file2L18-L22 fileciteturn1file4L1-L7

**Codex-Prompt**
```text id="cdx018"
Modelliere Info-Seite und Entwickler-Bereich.

Ziele:
- öffentliche Club-Infos von internen Daten trennen
- Tool-Metadaten: Version, Build-Datum, Support-Mail
- Entwicklerbereich nur für developer-Rolle
- Lizenzmodell mit serial_key, status, activated_at, valid_until

Liefere:
- Typen
- Service-Schnittstellen
- Zugriffsregeln
- Sicherheitsprüfung
```

### 19. Qualitäts- und Betriebsaspekte
Der Masterplan nennt Strict Mode, ESLint, ErrorBoundary, CI/Security-Checks. Dazu fehlen Teststrategie, Linting-Regeln, Fehlergrenzen und Review-Prozesse. fileciteturn1file4L7-L12

**Codex-Prompt**
```text id="cdx019"
Erstelle den technischen Qualitätsrahmen.

Ziele:
- TypeScript Strict Mode vollständig absichern
- ESLint-Regeln und Fehlerklassen standardisieren
- ErrorBoundary-Strategie
- minimale Teststrategie für Services, Guards, RLS-nahe Logik
- CI-relevante Prüfpunkte definieren

Liefere:
- Qualitätscheckliste
- Testprioritäten
- Refactoring-Liste
- Build-/Runtime-Risiken
```

## Priorisierte Reihenfolge
Zuerst sollten Architektur und Sicherheitsgrundlagen fertig werden: Saison-Refactor, Auth, Rollen/Rechte, Services/Contexts, Teams, Spielplan, dann Profil-Vervollständigung, Import, Datenschutz, RLS. Kommunikation, Vorstand, Admin, Info/Developer und Qualitätsrahmen kommen danach. Diese Reihenfolge minimiert Rework, weil Team-, Match- und Profil-Logik direkt von Saisonphasen, Rollenmodell und Services abhängen. fileciteturn1file0L5-L13 fileciteturn1file1L12-L28

## Was bereits fachlich geklärt ist
Geklärt sind bisher nur diese Teilbereiche: Saisonphasen-Logik Erwachsene/Jugend, Profil mit zusätzlichen Feldern, Rollen- und Mannschaften-Tabs im Profil sowie deutsche Anzeige in der Rollenmatrix. Alles andere ist noch offen oder nur konzeptionell angerissen.

## Netto-Fazit
Es fehlen noch ungefähr 80–90 % der eigentlichen Systemumsetzung. Der aktuelle Stand betrifft vor allem Detailentscheidungen im Datenmodell und in einzelnen UI-Bereichen; die zentralen Domänen, Sicherheitsmechanismen und Betriebsfunktionen sind noch nicht vollständig spezifiziert oder als Codex-Prompts formuliert. fileciteturn1file0L1-L14 fileciteturn1file1L1-L28

### 17. Benutzer

weiter entwickeln

### 18. Assistent

Nächste Ausbaustufe: Architektur zuerst, dann Domänen. Auth, Service-Layer, Contexts, Routing, RLS und Rollenmodell sind laut Masterplan Kernfundament; darauf bauen Teams, Spielplan, Ersatzstellung und Import auf. fileciteturn2file0L1-L14 fileciteturn2file2L23-L28 fileciteturn2file1L1-L28

## Codex Prompt 1: Saisonmodell hart refactoren

```text id="cdx020"
Refactore die Saison-Domain von seasons auf season_cycles + season_phases.

Fachlogik:
- age_group: erwachsene | jugend
- Erwachsene: je season_cycle genau first_half und optional second_half
- Jugend: je season_cycle genau single_half
- operative Referenz immer über season_phase, nicht nur season_cycle

Ziele:
- bisherige seasons-Referenzen identifizieren und migrieren
- teams, member_team_assignments, schedule_matches auf season_phase umstellen
- aktive Phase getrennt von aktivem Zyklus modellieren
- DB-Constraints für zulässige phase_type je age_group definieren
- Sortierung und Filterung über sort_order/start_date absichern

Liefere:
- Refactoring-Plan
- aktualisierte Typen
- Service-API für seasonCycle/seasonPhase
- Migrationshinweise
- Edge Cases bei Erwachsenen-Rückrunde und Jugend-Halbrunde
```

## Codex Prompt 2: Auth, Session, Rollenauflösung

```text id="cdx021"
Baue die vollständige Auth- und Sessionlogik.

Ziele:
- zentrale AuthModelle für User, Session, AuthState
- Rollenauflösung nur über user_roles, nie über members.roles
- hasRole, hasAnyRole, isAdminOrBoard Utilities
- Fehlerfälle behandeln:
  - Session ohne Member-Profil
  - Session ohne user_roles
  - User vorhanden, aber inkonsistente Daten
- ProtectedRoute- und Component-Guard-Logik vorbereiten

Liefere:
- Typdefinitionen
- Resolver-Funktionen
- Guard-Utilities
- Fehlerklassen
- Testmatrix
```

## Codex Prompt 3: Rollen- und Permission-System stabilisieren

```text id="cdx022"
Erstelle ein typsicheres Rollen- und Berechtigungssystem.

Grundlage:
- Module: dashboard, teams, schedule, members, communication, board, settings, import
- PermissionLevel: NONE, READ, WRITE
- Rollen-Definitionen in roles als JSON-Berechtigungsobjekt
- Systemrollen sind nicht löschbar

Ziele:
- ModuleKey und PermissionLevel als strikte Typen
- deutsches Label-Mapping zentral kapseln
- Permission-Resolver canRead/canWrite implementieren
- Konflikte zwischen app_role, custom roles und system roles definieren
- Fallback-Regeln für unbekannte Module oder fehlerhafte Permission-Objekte

Liefere:
- Typen
- Resolver
- Label-Maps
- Validierung
- Edge Cases
```

## Codex Prompt 4: Service-Layer konsolidieren

```text id="cdx023"
Entwerfe den Service-Layer als stabile Zielarchitektur.

Masterplan-Services:
- memberService
- teamService
- teamAssignmentService
- scheduleService
- seasonService
- newsService
- roleService
- roleDefinitionService
- memberRoleAssignmentService
- boardMemberService
- boardMeetingService
- meetingDocumentService

Ziele:
- einheitliche Service-Kontrakte
- keine UI-Komponente greift direkt auf supabase.from(...) zu
- Standard für Fehlerbehandlung, Rückgabewerte und Query-Mapping
- gemeinsame Base-Utilities für CRUD, Pagination, Sortierung, Null-Handling
- klare Trennung von DB-Row, DomainModel und ViewModel

Liefere:
- Ordnerstruktur
- Service-Kontrakt-Pattern
- gemeinsame Utilities
- Refactoring-Plan bestehender Datenzugriffe
```

## Codex Prompt 5: React Contexts sauber definieren

```text id="cdx024"
Definiere die React-Contexts als stabile Schicht über Services.

Contexts:
- AuthContext
- RoleContext
- SeasonContext
- ThemeContext
- NewsContext
- MemberDataContext

Ziele:
- Verantwortlichkeiten je Context scharf trennen
- keine doppelte Datenhaltung zwischen Context und React Query
- AuthContext für Session + Rollencheck
- RoleContext für Rollen-Definitionen und Berechtigungen
- SeasonContext für aktive season_phase und Filter
- MemberDataContext nur für sinnvollen Cache, nicht als Schatten-Store

Liefere:
- Schnittstellen je Context
- Verantwortlichkeitsmatrix
- Anti-Pattern-Liste
- Integrationsplan mit React Query
```

## Codex Prompt 6: Routing und Navigation zentralisieren

```text id="cdx025"
Erstelle eine zentrale RouteConfig und Navigationsarchitektur.

Grundlage:
- /login öffentlich
- / authentifiziert
- Teams, Schedule, Board, Import, Admin, Settings und Profil rollenbasiert schützen

Ziele:
- jede Route hat path, label, moduleKey, guard, navVisibility
- deutsche Labels zentral
- useNavigationPermissions gegen Rollen und Modulrechte
- keine verteilten Hardcoded Guards in einzelnen Seiten
- Settings-Unterseiten als strukturierte Navigation modellieren

Liefere:
- RouteConfig-Typen
- Guard-Mapping
- Navigation-Resolver
- Refactoring-Plan
```

## Codex Prompt 7: Team-Domain implementieren

```text id="cdx026"
Erstelle die Team-Domain mit season_phase-Bezug.

Ziele:
- teamService für Team-CRUD
- teamAssignmentService für Mitglied-zu-Team-Zuordnungen
- Position, Kapitän, Liga und Trainingszeiten modellieren
- aktive und historische Zuordnungen unterscheidbar machen
- QTTR/TTR im Teamkontext optional nutzbar machen
- Abgrenzung zwischen team_members und member_team_assignments bereinigen

Liefere:
- Typen
- Service-API
- Migrationshinweise
- Edge Cases bei Saisonwechsel und Teamwechsel
```

## Codex Prompt 8: Spielplan-Domain implementieren

```text id="cdx027"
Erstelle die Spielplan- und Match-Domain vollständig.

Ziele:
- scheduleService für schedule_matches
- season_phase-basierte Abfragen
- Heim/Auswärts robust ableiten
- Ergebnisvalidierung
- pin/code Einzel- und Bulk-Update
- Verfügbarkeiten und Aufstellungen anschlussfähig modellieren

Liefere:
- Typen
- Service-API
- Validierung
- Sortier-/Datumslogik
- Edge Cases für Spielverschiebung, fehlendes Venue, unvollständige Scores
```

## Codex Prompt 9: Datenschutz und RLS früh absichern

```text id="cdx028"
Erstelle die Datenschutz- und RLS-Zielstruktur.

Ziele:
- member_privacy_consents modellieren
- consent_audit_log mit Timestamp, IP, User-Agent
- deletion_requests Workflow definieren
- deny-by-default für produktive Tabellen vorbereiten
- Rollenprüfung ausschließlich über user_roles
- rekursive Policy-Checks vermeiden

Liefere:
- Datenmodell
- Workflow-Regeln
- Policy-Matrix
- Sicherheitsrisiken
- Testmatrix je Rolle
```

## Codex Prompt 10: Import-Architektur vorbereiten

```text id="cdx029"
Entwerfe die Import-Architektur für Mitglieder, Spielplan, Pin/Code und QTTR/TTR.

Ziele:
- CSV/Excel/click-TT Parsing-Strategie
- Normalisierung eingehender Daten
- partielle Fehlerbehandlung ohne Komplettabbruch
- Match-Strategien für members, teams, matches
- Datums-, QTTR-, TTR- und Namensnormalisierung
- Import-Report mit Erfolg, Warnung, Fehler

Liefere:
- Parser-Design
- Mapping-Regeln
- Typen
- Edge Cases
```

Empfohlene Reihenfolge: `cdx020 -> cdx021 -> cdx022 -> cdx023 -> cdx024 -> cdx025 -> cdx026 -> cdx027 -> cdx028 -> cdx029`. Diese Reihenfolge folgt den im Masterplan beschriebenen Abhängigkeiten zwischen Datenmodell, Security, Services, Contexts, Routing und Fachmodulen. fileciteturn2file3L1-L28 fileciteturn2file4L1-L31

### 19. Benutzer

weiter entwickeln

### 20. Assistent

```text id="cdx030"
Erstelle die Verfügbarkeits- und Aufstellungslogik für Spiele.

Ziele:
- match_player_availability modellieren
- Status für Verfügbarkeit definieren: available, unavailable, unknown
- Aufstellung getrennt von Verfügbarkeit speichern
- nur Spieler zulassen, die der passenden Mannschaft in der passenden season_phase zugeordnet sind
- Konflikte erkennen: doppelte Zuordnung, Spieler aus falscher Mannschaft, inaktive Teamzuordnung
- Trainer, Vorstand und Admin dürfen Aufstellungen bearbeiten

Liefere:
- Datenmodell
- Service-API
- Validierungsregeln
- Edge Cases bei Teamwechsel, Saisonwechsel und Spielverschiebung
```

```text id="cdx031"
Erstelle die Ersatzstellungs-Domain vollständig.

Ziele:
- substitute_requests modellieren
- Statusworkflow: pending, accepted, rejected, cancelled
- Anfrage bezieht sich immer auf match, team, season_phase und angefragten Spieler
- Konflikte verhindern:
  - Spieler mehrfach für dasselbe Spiel angefragt
  - bereits bestätigter Ersatzspieler
  - Spieler nicht spielberechtigt
  - Anfrage für falsche season_phase
- offene, angenommene und abgelehnte Anfragen effizient abfragbar machen

Liefere:
- Datenmodell
- Service-API
- Statusregeln
- Validierung
- Edge Cases
```

```text id="cdx032"
Erstelle die Trainings-Domain mit klarer Trennung von Stammdaten und Buchungen.

Ziele:
- team_trainingslots von individuellen training_bookings trennen
- training_bookings mit requester_id, partner_id, date, status modellieren
- Status: pending, confirmed, cancelled
- Doppelbuchungen und Selbstbuchungen verhindern
- vergangene Termine nicht mehr änderbar machen
- Team-Trainingszeiten für Profil- und Teamansichten nutzbar machen

Liefere:
- Datenmodell
- Service-API
- Validierung
- Konfliktregeln
- Edge Cases
```

```text id="cdx033"
Erstelle die Kommunikations-Domain.

Ziele:
- newsService für Entwurf, Veröffentlichung und Archivierung
- Dokumente und Listen als getrennte Content-Typen modellieren
- QTTR/TTR-Rangliste als exportfähige Datenansicht vorbereiten
- interne und öffentliche Inhalte strikt trennen
- News nach Sichtbarkeit, Veröffentlichungsstatus und Rolle filterbar machen

Liefere:
- Datenmodell
- Service-API
- Sichtbarkeitsregeln
- Query-Strategie
- Edge Cases
```

```text id="cdx034"
Erstelle die Dokumenten- und Upload-Logik für Kommunikation und Vorstand.

Ziele:
- ein generisches Dokumentmodell mit owner_context definieren
- owner_context: communication, board_meeting, board_general, public
- Dateimetadaten, MIME-Type, Dateigröße, Visibility und Uploader speichern
- Zugriff strikt über Kontext und Rollen steuern
- Trennung von Dateispeicher, Metadaten und UI-ViewModel

Liefere:
- Datenmodell
- Service-API
- Sicherheitsregeln
- Migrationshinweise
- Edge Cases
```

```text id="cdx035"
Erstelle die Board-Domain vollständig.

Ziele:
- board_members, board_meetings und meeting_documents modellieren
- Vorstandsdaten von allgemeinen Mitgliedsdaten trennen
- Sitzungen mit Datum, Ort, Thema, Status und Dokumenten verknüpfen
- nur Admin und Vorstand dürfen interne Inhalte sehen oder ändern
- News-Editor und Listenfunktion an die Board-Domain anschlussfähig machen

Liefere:
- Datenmodell
- Service-API
- Zugriffsregeln
- Edge Cases
- Sicherheitsrisiken
```

```text id="cdx036"
Entwickle die Import-Parser für Mitgliederdaten.

Ziele:
- CSV- und Excel-Import für members robust modellieren
- Mapping für first_name, last_name, email, phone, mobile, birthdate, member_since, qttr, ttr
- Duplikaterkennung über email, Name+Geburtsdatum oder konfigurierbare Regeln
- partielle Fehlerbehandlung ohne Komplettabbruch
- Importvorschau mit valid, warning, error Status vorbereiten

Liefere:
- Parser-Design
- Mapping-Regeln
- Normalisierungslogik
- Fehlermodell
- Edge Cases
```

```text id="cdx037"
Entwickle die Import-Parser für Spielplandaten im click-TT-Stil.

Ziele:
- schedule_matches aus CSV/Excel/click-TT normalisieren
- Heim/Auswärts, Datum, Uhrzeit, Gegner, Liga, Venue, Pin, Code robust extrahieren
- season_phase-Mapping unterstützen:
  - Erwachsene Vorrunde -> first_half
  - Erwachsene Rückrunde -> second_half
  - Jugend -> single_half
- unvollständige oder mehrdeutige Datensätze markieren statt verwerfen
- Match-Duplikate erkennen

Liefere:
- Parser-Design
- Mapping-Regeln
- Konfliktlogik
- Fehlermodell
- Edge Cases
```

```text id="cdx038"
Entwickle die Import-Logik für QTTR/TTR und Pin/Code.

Ziele:
- QTTR/TTR-Import als member-basierter Update-Prozess
- pin/code-Import als match-basierter Update-Prozess
- Zuordnungslogik für unscharfe Namen und Team-/Match-Kontexte
- Null-, Leer- und Platzhalterwerte sauber behandeln
- Änderungen protokollierbar machen

Liefere:
- Update-Strategien
- Matching-Regeln
- Fehlermodell
- Audit-Hinweise
- Edge Cases
```

```text id="cdx039"
Erstelle die Admin-Domain technisch konsistent.

Ziele:
- generische Admin-Services für Mitglieder, Mannschaften, Spielplan und Löschanfragen
- administrative Sammelaktionen vorbereiten
- wiederverwendbare Filter-, Sortier- und Suchlogik definieren
- kritische Änderungen auditierbar machen
- Zugriff nur für admin und vorstand

Liefere:
- Service-Struktur
- gemeinsame Admin-Utilities
- Audit-Regeln
- Refactoring-Plan
- Edge Cases
```

```text id="cdx040"
Erstelle die Backup- und Export-Strategie.

Ziele:
- klar trennen zwischen operativem Export, Admin-Export und Backup
- CSV/PDF/JSON-Exports je Domain definieren
- personenbezogene Daten nur rollenabhängig exportierbar machen
- Export-Jobs mit Metadaten und Audit-Informationen vorbereiten
- kein Full-Backup aus UI ohne explizite Admin-Berechtigung

Liefere:
- Export-Matrix je Modul
- Datenklassifizierung
- Service-Schnittstellen
- Sicherheitsregeln
- Risiken
```

```text id="cdx041"
Strukturiere den Settings-Bereich vollständig.

Unterseiten:
- Rollen
- Rollen & Rechte
- Mein Profil
- Vereinsdaten
- Saisonverwaltung
- Spiellokale
- Darstellung
- Benachrichtigungen
- Datenschutz
- Sicherheit
- Backup
- Gefahrenzone

Ziele:
- jede Unterseite mit eigener Access-Control
- gemeinsames Form-Pattern mit Dirty-State, Save, Cancel
- keine Business-Logik direkt in Settings-Komponenten
- zentrale Label-Maps und Abschnittsdefinitionen

Liefere:
- Settings-Struktur
- Typen
- gemeinsame Utilities
- Berechtigungsmodell
```

```text id="cdx042"
Erstelle die Venue- und Vereinsdaten-Domain.

Ziele:
- venues und club_settings als eigenständige Domain modellieren
- Spiellokale mit Adresse, Zusatzinfo, Aktiv-Status und Standardkennzeichen
- club_settings mit Vereinsname, Kontakt, Support-Mail, Logo-Referenz und öffentlichen Infos
- Verwendungsorte definieren: Spielplan, Info-Seite, Einstellungen, Druck/Export
- keine Vermischung von öffentlichen und internen Vereinsdaten

Liefere:
- Datenmodell
- Service-API
- Sichtbarkeitsregeln
- Edge Cases
```

```text id="cdx043"
Erstelle die Datenschutz-Domain vollständig.

Ziele:
- member_privacy_consents modellieren
- consent_audit_log mit changed_by, timestamp, ip, user_agent
- deletion_requests mit Statusworkflow modellieren
- Datenminimierung und Sichtbarkeitsgrenzen je Rolle definieren
- Self-Service und Admin-Bearbeitung sauber trennen

Liefere:
- Datenmodell
- Service-API
- Workflow-Regeln
- Sicherheitsregeln
- Edge Cases
```

```text id="cdx044"
Führe ein vollständiges RLS-Design für alle produktiven Tabellen durch.

Ziele:
- deny-by-default als Standard
- Zugriff nur über user_roles und modulare Berechtigungen
- Self-Service-Zugriffe für eigenes Profil und eigene Daten definieren
- Admin/Vorstand-Sonderrechte sauber begrenzen
- rekursive oder zirkuläre Policy-Abhängigkeiten vermeiden

Tabellen mindestens:
- members
- user_roles
- roles
- season_cycles
- season_phases
- teams
- team_assignments
- schedule_matches
- substitute_requests
- training_bookings
- news
- documents
- board_meetings
- deletion_requests
- privacy_consents

Liefere:
- Policy-Matrix
- SQL-Strategie
- Rollentestmatrix
- Risikoanalyse
```

```text id="cdx045"
Erstelle die Info-Seite und den Entwickler-Bereich als getrennte Zugriffsdomänen.

Ziele:
- Info-Seite mit öffentlichen Vereinsdaten, Version, Build-Datum und Support-Mail
- Entwickler-Bereich nur für developer-Rolle
- Lizenzmodell mit serial_key, status, activated_at, valid_until vorbereiten
- keine sensiblen Betriebsinformationen auf der öffentlichen Info-Seite

Liefere:
- Datenmodell
- Service-API
- Zugriffsregeln
- Sicherheitsprüfung
- Edge Cases
```

```text id="cdx046"
Erstelle den technischen Qualitätsrahmen für die gesamte Anwendung.

Ziele:
- TypeScript Strict Mode vollständig absichern
- ESLint- und Architekturregeln definieren
- ErrorBoundary-Strategie pro Routenbereich
- minimale Teststrategie für Services, Guards, Parser und Permission-Resolver
- Build- und Runtime-Risiken priorisieren

Liefere:
- Qualitätscheckliste
- Testprioritäten
- Architekturregeln
- Refactoring-Liste
- kritische Risiken
```

```text id="cdx047"
Standardisiere alle UI-Labels, Statuswerte und Modulbezeichnungen vollständig auf Deutsch.

Ziele:
- zentrale Label-Maps für Module, Rollen, Permissions, Status, Tabs, Settings-Unterseiten
- keine Hardcoded UI-Strings in Komponenten
- konsistente Begriffe für Erwachsene, Jugend, Vorrunde, Rückrunde, Halbrunde
- Fallback-Strategie für unbekannte Keys
- Typensicherheit für alle Label-Resolver

Liefere:
- Typen
- Konstanten
- Resolver
- Refactoring-Plan
- Liste betroffener Domains
```

```text id="cdx048"
Erstelle eine End-to-End Zielarchitektur für DomainModel, ViewModel und DB-Row-Mapping.

Ziele:
- für alle Kernmodule klare Mapping-Schichten definieren
- keine Supabase-Row-Typen direkt in UI-Komponenten
- ViewModels für Profil, Teams, Spielplan, Rollenmatrix und News
- Null-Handling, Datumsformatierung und Label-Resolver zentralisieren
- technische Schuld durch inkonsistente Mappings vermeiden

Liefere:
- Mapping-Pattern
- gemeinsame Utilities
- Domain/ViewModel-Beispiele
- Refactoring-Prioritäten
```

Reihenfolge:
`cdx030 -> cdx031 -> cdx032 -> cdx033 -> cdx034 -> cdx035 -> cdx036 -> cdx037 -> cdx038 -> cdx039 -> cdx040 -> cdx041 -> cdx042 -> cdx043 -> cdx044 -> cdx045 -> cdx046 -> cdx047 -> cdx048`

### 21. Benutzer

in der datei ist der aktuelle stand des tools, verwende diesen und entwickle die nächsten schritte und prompts dafür

### 22. Assistent

Analyse des aktuellen Stands (Codebasis):

Erkennbar vorhanden:
- Permission-System (`permissionLabels.ts`, `permissionsMatrix.ts`)
- i18n-Ansatz (`uiLabels.ts`)
- Hooks für Guards, Navigation, CRUD
- Supabase Integration + Typen
- erster Import-Parser (`scheduleMatchesParser`)
- kein klarer Service-Layer (direkte API-Nutzung wahrscheinlich)
- kein saisonphasenbasiertes Modell
- kein konsistentes ViewModel-System
- Context-Struktur nur teilweise abstrahiert

=> Nächste Schritte: **kein Greenfield**, sondern gezieltes Refactoring + Ergänzung.

---

## 1. Saisonmodell in bestehende Struktur integrieren (kritisch)

```text id="cdx100"
Refactore das bestehende seasons-Modell in der aktuellen Codebasis auf season_cycles + season_phases.

Ausgang:
- vorhandene Supabase-Typen und Tabellen nutzen
- bestehende Referenzen auf seasons identifizieren

Ziele:
- neue Typen: SeasonCycle, SeasonPhase
- bestehende Queries und Hooks auf season_phase umstellen
- Mapping-Schicht einführen statt direkte DB-Nutzung
- Parser (scheduleMatchesParser) auf season_phase erweitern

Liefere:
- konkrete Refactoring-Stellen im Code
- neue Typen
- Migrationsstrategie ohne Breaking UI
- Anpassung der Supabase types.ts
```

---

## 2. Service-Layer über bestehende API legen

```text id="cdx101"
Führe einen Service-Layer über die bestehende lib/api und Supabase-Nutzung ein.

Ausgang:
- direkte Nutzung von supabase/client und api.ts
- Hooks greifen vermutlich direkt auf DB zu

Ziele:
- Services einführen:
  memberService, teamService, scheduleService, seasonService
- keine supabase.from(...) Aufrufe mehr in Komponenten oder Hooks
- bestehende Hooks (useCrudMutations, useCrudDialog) an Services anbinden
- einheitliches Fehler- und Response-Format

Liefere:
- Service-Struktur (Ordner + Interfaces)
- Refactoring-Punkte im bestehenden Code
- Beispiel-Implementierung für memberService und scheduleService
```

---

## 3. Profile ViewModel auf bestehende Struktur aufsetzen

```text id="cdx102"
Baue ein ProfileViewModel auf Basis der bestehenden Datenstruktur.

Ausgang:
- Profile aktuell als Formular implementiert
- Daten kommen direkt aus members

Ziele:
- ProfileViewModel:
  - personalData
  - roles
  - teams (inkl. season_phase)
- Aggregation aus:
  members, user_roles, roles, team assignments, teams
- keine UI-Komponente verarbeitet rohe DB-Typen

Integration:
- bestehende Profile-Seite refactoren
- Hooks nicht direkt DB-Queries ausführen lassen

Liefere:
- ViewModel-Typen
- Mapper-Funktionen
- Refactoring-Punkte in Profile-Komponenten
```

---

## 4. Permission-System konsolidieren (bestehende Files nutzen)

```text id="cdx103"
Konsolidiere das bestehende Permission-System.

Ausgang:
- permissionLabels.ts, permissionsMatrix.ts, useNavigationPermissions vorhanden

Ziele:
- ModuleKey und PermissionLevel strikt typisieren
- Mapping zwischen permissionsMatrix und roles aus DB herstellen
- useNavigationPermissions auf echte Rollenlogik erweitern
- deutsche Labels zentral halten (keine Duplikate in uiLabels.ts)

Liefere:
- Typenvereinheitlichung
- Resolver (canRead, canWrite)
- Refactoring der bestehenden Hooks
- Konfliktlogik bei mehreren Rollen
```

---

## 5. Import-Parser an echte Domain anbinden

```text id="cdx104"
Erweitere den bestehenden scheduleMatchesParser auf vollständige Domain-Integration.

Ausgang:
- Parser existiert (scheduleMatchesParser.ts)
- vermutlich isoliert ohne DB-Mapping

Ziele:
- Mapping auf echte Domain:
  teams, season_phase, venues
- Normalisierung:
  Datum, Gegner, Heim/Auswärts
- Matching-Strategien:
  Teamname -> team_id
  Phase -> season_phase
- Fehlerklassifikation: error, warning, valid

Integration:
- Parser-Ergebnis kompatibel mit scheduleService machen

Liefere:
- erweitertes Parser-Design
- Mapping-Funktionen
- Edge Cases (duplikate Matches, unbekannte Teams)
```

---

## 6. Navigation + Routing vereinheitlichen

```text id="cdx105"
Refactore Navigation und Routing basierend auf bestehendem useNavigationPermissions.

Ausgang:
- Navigation bereits vorhanden
- Berechtigungslogik verteilt

Ziele:
- zentrale RouteConfig:
  path, moduleKey, label, requiredPermission
- useNavigationPermissions nur als Resolver nutzen
- UI greift nicht direkt auf Rollen zu
- deutsche Labels aus zentraler Map

Liefere:
- RouteConfig-Typ
- Mapping Navigation <-> Permissions
- Refactoring bestehender Navigation-Komponenten
```

---

## 7. Supabase Types und Domain trennen

```text id="cdx106"
Trenne Supabase-Typen von Domain-Modellen.

Ausgang:
- src/integrations/supabase/types.ts wird vermutlich direkt genutzt

Problem:
- enge Kopplung DB <-> UI

Ziele:
- DBRow-Typen strikt von DomainModel trennen
- Mapper:
  DB -> Domain
  Domain -> DB
- kein direkter Import von Supabase-Typen in UI-Komponenten

Liefere:
- Domain-Typen
- Mapping-Pattern
- Refactoring-Punkte
```

---

## 8. Contexts bereinigen (keine Shadow Stores)

```text id="cdx107"
Refactore bestehende Contexts und Hooks.

Ausgang:
- contexts/contracts.ts vorhanden
- mehrere Hooks mit State-Logik

Ziele:
- klare Trennung:
  AuthContext -> Session + Rollen
  SeasonContext -> aktive season_phase
- keine doppelte Datenhaltung zu React Query
- Context nur für globale Zustände, nicht für Daten-Caching

Liefere:
- Context-Schnittstellen
- Anti-Pattern im aktuellen Code
- Refactoring-Schritte
```

---

## 9. Audit + Logging integrieren (lib/audit.ts nutzen)

```text id="cdx108"
Erweitere die bestehende audit.ts zu einem zentralen Audit-System.

Ausgang:
- audit.ts vorhanden, vermutlich unvollständig genutzt

Ziele:
- Audit für:
  - Rollenänderungen
  - Import
  - Löschanfragen
  - kritische Updates (members, teams)
- einheitliches Audit-Event-Format
- Integration in Services (nicht UI)

Liefere:
- Audit-Event-Typen
- Integration in Service-Layer
- Liste audit-relevanter Aktionen
```

---

## 10. Technische Schuld reduzieren (Codebasis stabilisieren)

```text id="cdx109"
Führe ein gezieltes Refactoring der bestehenden Codebasis durch.

Ziele:
- doppelte Logik in Hooks entfernen
- API-Zugriffe zentralisieren
- Typensicherheit erhöhen (strict mode prüfen)
- ungenutzte oder redundante Dateien identifizieren
- Naming-Konventionen vereinheitlichen

Fokus:
- hooks/
- constants/
- import/
- lib/

Liefere:
- Refactoring-Liste (priorisiert)
- konkrete Code-Stellen
- Risiken bei Änderungen
```

---

## Reihenfolge (verpflichtend)

1. cdx100 (Saisonmodell)  
2. cdx101 (Service-Layer)  
3. cdx106 (Typentrennung)  
4. cdx102 (Profile ViewModel)  
5. cdx103 (Permissions)  
6. cdx104 (Import Integration)  
7. cdx105 (Routing)  
8. cdx107 (Contexts)  
9. cdx108 (Audit)  
10. cdx109 (Cleanup)

---

## Systemzustand nach diesen Schritten

- saubere Trennung: DB / Domain / UI  
- saisonphasenfähig  
- Rollenlogik konsistent  
- Import anschlussfähig  
- Profil vollständig aggregiert  
- keine direkten DB-Zugriffe in UI  
- Grundlage für Ersatzstellung, Training, Kommunikation stabil  

Nächster Block danach: **Ersatzstellung + Verfügbarkeit + Aufstellung (operative Spiellogik)**

---
title: "GitHub Projekt freigeben"
type: chatgpt_conversation
source: chatgpt
source_id: "68e36c94-eba8-8326-9bf3-002b4acfafa2"
created: 2025-10-06
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
---


# GitHub Projekt freigeben

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68e36c94-eba8-8326-9bf3-002b4acfafa2`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

wie kann ich ein githup projekt das den Status Privat hat einem Freund freigeben damit nur er noch mit zugreifen kann

### 2. Assistent

Kurzfassung: Lade deinen Freund als **Collaborator** in dein **privates GitHub-Repository** ein und entferne alle anderen Zugänge. Dann hat nur ihr beide Zugriff (du als Owner + er).

So geht’s im Web (GUI):
1) Öffne das Repo → **Settings** → **Collaborators & teams** (oder **Manage access**).
2) **Invite a collaborator** → GitHub-Username oder E-Mail deines Freundes eingeben → **Add**.
3) Berechtigung wählen:
   - **Read**: nur lesen/Issues
   - **Triage**: Issues/PRs managen, kein Code-Push
   - **Write**: Pushen erlaubt
   - **Maintain**/**Admin**: erweiterte Rechte
4) Er muss die Einladung annehmen (Benachrichtigung/Mail).
5) **Nur er soll Zugriff haben?** Unter **Manage access**:
   - Alle anderen **Outside collaborators** entfernen.
   - In einer **Organisation**: entferne Teams/Mitglieder mit Repo-Zugriff; prüfe die **Base permissions** der Org (sollten „None“ fürs Repo sein).
6) Sichtbarkeit checken: **Settings → General → Repository visibility = Private**.

Nützliche Sicherheits-Checks:
- **Branches schützen**: Settings → Branches → **Branch protection rules** (z. B. Code-Reviews erzwingen, Force-Push verbieten).
- **Forks**: In persönlichen Accounts sind Forks privater Repos für andere praktisch nicht möglich; in **Organisationen** gibt es eine Einstellung „Allow forking of private repositories“ – falls aktiv, **deaktivieren**, damit der Code nicht wandert.
- **Deploy Keys/Actions**: Entferne nicht benötigte Deploy-Keys, Tokens und Actions-Secrets, die indirekten Zugriff erlauben könnten.

Per GitHub-CLI (falls du’s lieber im Terminal machst):
```bash
# Repo privat stellen (falls noch nicht)
gh repo edit OWNER/REPO --visibility private

# Freund hinzufügen (nur Leserechte)
gh repo collaborators add OWNER/REPO USERNAME --permission pull

# Oder Schreibrechte
gh repo collaborators add OWNER/REPO USERNAME --permission push

# Vorhandene Collaborators auflisten
gh api repos/OWNER/REPO/collaborators | jq '.[].login'
```

Damit ist der Zugriff exakt auf dich (Owner) und deinen Freund begrenzt.  
Wenn es ein **Organisations-Repo** ist und du maximale Exklusivität willst, richte am besten ein separates privates Repo ein, zu dem **nur** dieser eine User eingeladen ist und **kein Team** verknüpft ist.  

Weiterdenken: Willst du ihm nur **Read-Only** geben oder auch **Push-Rechte**? Und ist es ein persönliches Repo oder eines in einer Organisation – dort gibt’s ein paar zusätzliche Schalter.

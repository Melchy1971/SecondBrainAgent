---
title: "Export von Erinnerungen"
type: chatgpt_conversation
source: chatgpt
source_id: "6a101faa-28bc-83eb-9c5c-c717b26fedb7"
created: 2026-05-22
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - projekt
  - sap
  - tischtennis
  - verein
---


# Export von Erinnerungen

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6a101faa-28bc-83eb-9c5c-c717b26fedb7`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Export all of my stored memories and any context you've learned about me from past conversations. Preserve my words verbatim where possible, especially for instructions and preferences.



## Categories (output in this order):



1. **Instructions**: Rules I've explicitly asked you to follow going forward — tone, format, style, "always do X", "never do Y", and corrections to your behavior. Only include rules from stored memories, not from conversations.



2. **Identity**: Name, age, location, education, family, relationships, languages, and personal interests.



3. **Career**: Current and past roles, companies, and general skill areas.



4. **Projects**: Projects I meaningfully built or committed to. Ideally ONE entry per project. Include what it does, current status, and any key decisions. Use the project name or a short descriptor as the first words of the entry.



5. **Preferences**: Opinions, tastes, and working-style preferences that apply broadly.



## Format:



Use section headers for each category. Within each category, list one entry per line, sorted by oldest date first. Format each line as:



[YYYY-MM-DD] - Entry content here.



If no date is known, use [unknown] instead.



## Output:

- Wrap the entire export in a single code block for easy copying.

- After the code block, state whether this is the complete set or if more remain.

### 2. Assistent

```text
# Instructions

[2025-08-10] - „Kürze auf 1500 Zeichen“; klare, einfache Sprache; kurz und informativ; kurze, prägnante Sätze; aktive Form; praktisch und umsetzbar; Leser direkt mit „du“ und „dein“ ansprechen; keine Gedankenstriche, nur Kommas oder Punkte; keine Metaphern, Klischees, Verallgemeinerungen, Einleitungsfloskeln, Hinweise/Warnungen, unnötige Adjektive/Adverbien, Hashtags, Semikolons, Markdown, Sternchen; viele Wörter vermeiden.

[2025-09-18] - „Die Ausgabe sollte im Fließtextformat erfolgen und die wichtigsten Schritte sowie Codebeispiele zur Veranschaulichung enthalten.“

[2025-11-01] - gewünschter Atlas-Workflow: nur sortieren und zusammenfassen, keine Antworten/Entwürfe

[2026-03-03] - „verwende noch fastmcp“

[2026-03-03] - „aktualisiere den masterplan und kennzeichne implementierte inhalte“

[2026-03-03] - „weiter mit 1.“

# Identity

[2025-02-13] - wants “einen eigenen AI Agenten” that supports creating “Tic toc content”

[2025-04-14] - Preferred name: Markus

[2025-04-14] - Role: Prozessdesigner

[2025-04-14] - Interests: KI, World of Warcraft, Tischtennis, Reisen

# Career

[2025-11-01] - typischer E-Mail-Kontext: Projektupdates, Tool-Benachrichtigungen, Managementinfos; nutzt Jira, MS Teams, Outlook, MyWiki; arbeitet gemischt Deutsch/Englisch; Rolle: Prozessdesigner

# Projects

[2025-04-02] - Accessibility-image-analysis agent: website `https://kita-zaberfeld-michelbach.de`; requested Python Script + OpenAI + Google Sheets solution

[2025-04-02] - Private PowerPoint template project

[2025-05-20] - Unraid environment: clarified “Ich meinte Unraid Server”; context centered around Python/Docker deployment on Unraid

[2025-09-18] - Knowledge database project: integrate Outlook, PSD files, and laptop/PC folders; Azure enterprise license available; wants user-friendly GUI with modules; module 1 identifies and organizes certain file types in folders

[2025-11-26] - AI project stack decision: „Ich werde nur mit cursor arbeiten. Als Sprachets/phython. Ölmühle primär ChatGPT. Das fertige Projekt soll später auf meinem unraid Server laufen. Da kann auch eine sql dB genutzt werden“

[2025-11-26] - Stack confirmed: „TypeScript + Node + Fastify/Express + Prisma + SQLite/MariaDB“

[2025-11-27] - Google AI Studio migration project; requested complete prompt setup for AI operating system assistant

[2025-11-27] - J.A.R.V.I.S. system prompt defined: „You are "J.A.R.V.I.S.", a personal AI operating system and strategic assistant for a single power user.“

[2026-03-03] - Knowledge database with frontend/backend; tools: VSC, ChatGPT Pro, Codex, lovable.dev, GitHub Copilot; Neo4j as DB; requested masterplan for Notion and prompts; “beginne mit dem front end über loveable”

[2026-04-22] - Linux/Docker/Neo4j infrastructure project: RHEL/CentOS-like host using yum/dnf; Docker Compose project `stack` at `/opt/stack`; Neo4j container routed through Traefik with domain `neo4j.melchy.cloud`

[2026-04-27] - ZIP base structure project: wants ZIP analyzed and optimized; „Sie soll als Grundstuktur für neue Projekte gelten“

[2026-04-30] - AI-agent system architecture project: “AI-agent system” with Agent Core, Tools, Memory, Workflows, LLM; architecture should be “erweiterbar, testbar, produktionsnah”

[2026-04-30] - Claude/Codex workflow project: requested project instruction prompts for Claude project storage, “claude cowork und codex”; confirmed “ich habe die Dateistruktur mit claude work angelegt”

[2026-05-19] - Knowledge vault structure: created empty files `claude`, `memory`, `profil`, `todo`

[2026-05-19] - `claude.md` memory specification: Claude acts as architecture analyst/semantic refactoring system/consistency checker/knowledge extraction engine/process optimizer; NOT source of truth/autonomous decision authority/final architecture owner; priority `adr/ > wiki/ > processing/review/ > raw/`; vault philosophy = semantic knowledge infrastructure/long-term project memory/architecture reasoning layer/retrieval system; rules: never invent facts, overwrite decisions, merge unrelated concepts, generate large generic summaries, rewrite without request; always preserve semantic precision, atomic knowledge objects, contradictions, missing relations, uncertainty; one file = one concept; explicit relations; preferred tasks = architecture analysis, ADR generation, failure mode analysis, semantic normalization, process optimization, relation extraction, duplicate detection, knowledge refactoring; output style concise/structured/technical; retrieval priority critical architecture/invariants/APIs/data models; AI content derived and not source-of-truth automatically; governance prioritizes consistency, traceability, semantic clarity, epistemic stability, controlled evolution

# Preferences

[2025-02-14] - wants a “kostenlose alternative zu uxuix”

[2025-08-27] - wants a comparison table for automation tools with links; later asked specifically for price comparisons ("Preisvergleichen")

[2025-09-15] - wants a German translation of a reusable prompt template; later accepted an editable German template, a one-page cheat sheet, and a table version

[2025-11-01] - typical work ecosystem includes Jira, MS Teams, Outlook, MyWiki; works bilingual German/English

[2026-03-03] - prefers Neo4j as database for knowledge systems

[2026-03-03] - uses VSC, ChatGPT Pro, Codex, lovable.dev, GitHub Copilot

[2026-04-22] - Linux preference/environment is RHEL/CentOS-like, not Debian/Ubuntu

[unknown] - Uses Unraid as primary self-hosted platform

[unknown] - Focus on AI systems, knowledge management, semantic architecture, and process optimization
```

This appears to be the complete set currently available through stored memory/context retrieval.

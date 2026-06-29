---
title: "Cheat-Code Prompts für ChatGPT"
type: chatgpt_conversation
source: chatgpt
source_id: "68bfea18-e048-8320-b791-5c9388163650"
created: 2025-09-09
tags:
  - chatgpt
  - import
  - ki
  - sap
  - verein
---


# Cheat-Code Prompts für ChatGPT

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68bfea18-e048-8320-b791-5c9388163650`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

übersetze: 14 Cheat-Code Prompts That Turn ChatGPT Into a Powerhouse
Business & Professional
TL;DR: If your AI outputs feel random, your prompts are under-specified. Use these 14 operator-grade prompts (with format + constraints) and watch quality jump. I included a one-line “mode switch” you can prepend to any prompt.

A universal one-liner (prepend to any prompt)
Workstyle: {Thinking: Fast|Auto|High}. Verbosity: {Short|Medium|Long}. Format: {Bullets|Table|Steps|JSON}. Constraints: {tokens/words, tone}. Show reasoning as a brief numbered outline. Ask 1 clarifying question if critical.
Why it works: it sets thinking style, length, output form, and guardrails—the four levers that control quality.

The 14 prompts
1) Investigate a Problem
Workstyle: Thinking High. Verbosity: Long. Format: Steps → Conclusion.
Role: Senior analyst.
Task: Break down [problem].
Deliverables:
  1) Problem statement (1–2 sentences)
  2) Assumptions (bullet list)
  3) 5–9 step reasoning outline
  4) Risks/unknowns and how to test
  5) Conclusion + decision recommendation
Use when you need structure and defensible logic.

2) Speed-Read Anything
Workstyle: Fast. Verbosity: Short. Format: Bullets.
Task: Summarize [text or URL].
Rules: 5 bullets, max 12 words each. One “so what” line at the end.
Use when you need signal, not noise.

3) Self-Critique & Rewrite
Workstyle: Auto. Verbosity: Medium. Format: Before/After.
Task: Draft [X]. Then self-critique and rewrite.
Steps:
  A) Draft v1 (<=150 words)
  B) Critique: clarity, logic, tone, evidence (bullets)
  C) Rewrite v2 (<=120 words), fixes applied
Use when you want writer + editor in one pass.

4) Create Under Constraints
Workstyle: Auto. Verbosity: Short. Format: Paragraph.
Task: Write [content type].
Constraints: ≤80 words, exactly 1 metaphor, end with a question.
Use when constraints force creativity.

5) Recall & Expand (long input → coherent report)
Workstyle: Thinking High. Verbosity: Long. Format: Report.
Task: Read the provided notes/text. Produce a coherent 2,000-word [report].
Sections: Exec summary → Key insights → Evidence (with inline refs) → Risks → Next steps.
Consistency: unify terminology; resolve contradictions explicitly.
Use when you need long-context synthesis.
Note: Works best on models with large context windows; if yours is smaller, chunk inputs and run section by section.

6) Blend Sources into One Briefing
Workstyle: Thinking Medium. Verbosity: Balanced. Format: Briefing.
Inputs: [article 1], [notes], [data].
Output:
  - What’s true across sources (consensus)
  - Where they disagree (and why)
  - 5-point POV with implications for [audience]
  - One-page action checklist
Use when inputs are messy but output must be crisp.

7) Build in Layers (progressive deepening)
Workstyle: Thinking. Verbosity: Long. Format: Outline → Expansion.
Task: Create a structured explainer on [topic].
Layers:
  1) 5-bullet overview (no jargon)
  2) Expand each bullet into a short section with examples
  3) Add FAQs (5) and pitfalls (5)
Use when you want depth without dumping complexity upfront.

8) Wear the Expert Mask
Workstyle: Thinking High. Verbosity: Balanced. Format: Answer + Caveats.
Persona: [named expert or role].
Task: Answer [question] as this expert.
Include:
  - Reasoning outline
  - Blind spots / what this lens might miss
  - Alternative lens: how it would answer differently
Use when you want a borrowed lens without tunnel vision.

9) Map Ideas (from chaos to clusters)
Workstyle: Auto. Verbosity: Medium. Format: Clusters.
Task: List angles on [topic], then cluster.
Steps:
  - Generate 20 raw angles
  - Group into 3 themes with labels
  - For each theme: 3 high-leverage sub-ideas + example
Use when brainstorming needs structure.

10) Turn Goals into Plans
Workstyle: Thinking Auto→High. Verbosity: Long. Format: Plan.
Goal: [X].
Deliver:
  - 30-day plan (weekly milestones)
  - Assets to create (with owners/effort)
  - Risks, leading indicators, kill-switch criteria
  - Day-1 checklist (10 items)
Use when you want execution, not theory.

11) Reframe for Audience
Workstyle: Auto. Verbosity: Medium. Format: Side-by-Side.
Task: Rewrite [text] for [new audience].
Include:
  - Audience map (needs, objections, vocabulary)
  - Rewritten version (≤150 words)
  - 3 headline options, 3 CTAs
Use when the same idea must land for someone new.

12) Polish Copy (web/product)
Workstyle: Thinking. Verbosity: Medium. Format: Sections.
Task: Write sharp copy for [page/section].
Include: H1/H2s, scannable bullets, benefit > feature, one proof point, one CTA.
Style: concrete verbs, no filler, plain English.
Use when you need clean, reader-friendly text.

13) Diagnose a Case (reasoned workup)
Workstyle: Thinking High. Verbosity: Long. Format: Case Sheet.
Case: [symptoms/context].
Output:
  - Differential hypotheses (ranked)
  - Tests to confirm/deny each
  - Most likely diagnosis and rationale
  - Plan: immediate, near-term, follow-up
Use when careful step-by-step reasoning matters.

14) Add Personality (tone on purpose)
Workstyle: Fast. Verbosity: Short. Format: Bullets.
Persona: [Cynic|Coach|Professor|Stand-up].
Task: Explain [concept] in 3 punchy bullets.
Rule: each bullet ≤14 words; 1 surprising twist; no insults.
Use when tone carries as much weight as content.

Pro tips
Always specify output format. Bullets, table, steps, JSON. It removes guesswork.

Set constraints. Word caps, section counts, number of examples.

Ask it to show a brief reasoning outline. You see the why without a wall of text.

Chain the prompts. #6 (Blend) → #10 (Plan) → #12 (Polish) is a killer sequence.

Want more great prompting inspiration? Check out all my best prompts for free at Prompt Magic and create your own prompt library to keep track of all your prompts.

### 2. Assistent

**14 Cheat-Code-Prompts, die ChatGPT zur Power-Maschine machen**  
Business & Professional

**TL;DR:** Wenn deine KI-Ausgaben zufällig wirken, sind deine Prompts zu wenig spezifiziert. Nutze diese 14 Prompts auf Operator-Niveau (mit Format + Constraints) und beobachte, wie die Qualität hochspringt. Ich habe einen einzeiligen „Modus-Schalter“ beigefügt, den du jedem Prompt voranstellen kannst.

### Ein universeller Einzeiler (vor jeden Prompt setzen)
**Arbeitsstil:** {Denken: Schnell|Auto|Hoch}. **Ausführlichkeit:** {Kurz|Mittel|Lang}. **Format:** {Stichpunkte|Tabelle|Schritte|JSON}. **Einschränkungen:** {Token/Wörter, Ton}. **Zeige die Begründung als kurze nummerierte Gliederung. Stelle 1 klärende Frage, falls kritisch.**  
**Warum das funktioniert:** Er legt Denkstil, Länge, Ausgabeform und Guardrails fest – die vier Hebel für Qualität.

---

## Die 14 Prompts

### 1) Ein Problem untersuchen
**Arbeitsstil:** Denken Hoch. **Ausführlichkeit:** Lang. **Format:** Schritte → Fazit.  
**Rolle:** Senior-Analyst:in.  
**Aufgabe:** [Problem] zerlegen.  
**Ergebnisse:**
1) Problemstatement (1–2 Sätze)  
2) Annahmen (Stichpunkte)  
3) Begründungs-Outline mit 5–9 Schritten  
4) Risiken/Unbekanntes und wie testen  
5) Fazit + Entscheidungsempfehlung  
**Einsatz:** Wenn du Struktur und belastbare Logik brauchst.

### 2) Alles im Schnelllese-Modus
**Arbeitsstil:** Schnell. **Ausführlichkeit:** Kurz. **Format:** Stichpunkte.  
**Aufgabe:** [Text oder URL] zusammenfassen.  
**Regeln:** 5 Stichpunkte, max. 12 Wörter je Punkt. Eine „So-what?“-Zeile am Ende.  
**Einsatz:** Wenn du Signal statt Rauschen willst.

### 3) Selbstkritik & Neufassung
**Arbeitsstil:** Auto. **Ausführlichkeit:** Mittel. **Format:** Vorher/Nachher.  
**Aufgabe:** [X] entwerfen. Dann selbst kritisieren und neu schreiben.  
**Schritte:**  
A) Entwurf v1 (≤150 Wörter)  
B) Kritik: Klarheit, Logik, Ton, Evidenz (Stichpunkte)  
C) Neufassung v2 (≤120 Wörter), mit Fixes  
**Einsatz:** Wenn du Autor:in + Editor:in in einem Durchgang willst.

### 4) Unter Vorgaben kreieren
**Arbeitsstil:** Auto. **Ausführlichkeit:** Kurz. **Format:** Absatz.  
**Aufgabe:** [Content-Typ] schreiben.  
**Einschränkungen:** ≤80 Wörter, genau 1 Metapher, Ende mit einer Frage.  
**Einsatz:** Wenn Constraints Kreativität erzwingen.

### 5) Erinnern & Ausbauen (langer Input → kohärenter Bericht)
**Arbeitsstil:** Denken Hoch. **Ausführlichkeit:** Lang. **Format:** Report.  
**Aufgabe:** Lies die gegebenen Notizen/Texte. Erzeuge einen kohärenten 2.000-Wörter-[Report].  
**Abschnitte:** Executive Summary → Zentrale Erkenntnisse → Belege (mit Inline-Refs) → Risiken → Nächste Schritte.  
**Konsistenz:** Terminologie vereinheitlichen; Widersprüche explizit auflösen.  
**Einsatz:** Wenn du Long-Context-Synthese brauchst.  
**Hinweis:** Funktioniert am besten mit Modellen mit großem Kontextfenster; bei kleinerem Fenster Input stückeln und abschnittsweise laufen lassen.

### 6) Quellen zu einem Briefing verschmelzen
**Arbeitsstil:** Denken Mittel. **Ausführlichkeit:** Ausgewogen. **Format:** Briefing.  
**Inputs:** [Artikel 1], [Notizen], [Daten].  
**Output:**  
- Was über alle Quellen hinweg stimmt (Konsens)  
- Wo sie widersprechen (und warum)  
- 5-Punkte-Standpunkt mit Implikationen für [Zielgruppe]  
- Einseitige Aktions-Checkliste  
**Einsatz:** Wenn Inputs chaotisch sind, Output aber kristallklar sein muss.

### 7) Schichtweise aufbauen (progressive Vertiefung)
**Arbeitsstil:** Denken. **Ausführlichkeit:** Lang. **Format:** Gliederung → Ausbau.  
**Aufgabe:** Erstelle einen strukturierten Erklärtext zu [Thema].  
**Ebenen:**  
1) 5-Stichpunkte-Übersicht (ohne Jargon)  
2) Jeden Punkt zu kurzem Abschnitt mit Beispielen ausbauen  
3) FAQs (5) und Fallstricke (5) ergänzen  
**Einsatz:** Wenn du Tiefe willst, ohne anfangs Komplexität zu kippen.

### 8) Die Expert:innen-Maske tragen
**Arbeitsstil:** Denken Hoch. **Ausführlichkeit:** Ausgewogen. **Format:** Antwort + Vorbehalte.  
**Persona:** [benannte:r Expert:in oder Rolle].  
**Aufgabe:** [Frage] als diese:r Expert:in beantworten.  
**Enthält:**  
- Begründungs-Outline  
- Blinde Flecken / Was diese Linse übersehen könnte  
- Alternative Linse: Wie sie anders antworten würde  
**Einsatz:** Wenn du eine geliehene Perspektive ohne Tunnelblick willst.

### 9) Ideen kartieren (vom Chaos zu Clustern)
**Arbeitsstil:** Auto. **Ausführlichkeit:** Mittel. **Format:** Cluster.  
**Aufgabe:** Blickwinkel zu [Thema] auflisten, dann clustern.  
**Schritte:**  
- 20 rohe Blickwinkel generieren  
- In 3 Themen mit Labels gruppieren  
- Je Thema: 3 hochwirksame Unterideen + Beispiel  
**Einsatz:** Wenn Brainstorming Struktur braucht.

### 10) Ziele in Pläne verwandeln
**Arbeitsstil:** Denken Auto→Hoch. **Ausführlichkeit:** Lang. **Format:** Plan.  
**Ziel:** [X].  
**Liefern:**  
- 30-Tage-Plan (wöchentliche Meilensteine)  
- Zu erstellende Assets (mit Verantwortlichen/Aufwand)  
- Risiken, Frühindikatoren, Abbruchkriterien  
- Tag-1-Checkliste (10 Punkte)  
**Einsatz:** Wenn es um Umsetzung statt Theorie geht.

### 11) Für Zielgruppe neu rahmen
**Arbeitsstil:** Auto. **Ausführlichkeit:** Mittel. **Format:** Gegenüberstellung.  
**Aufgabe:** [Text] für [neue Zielgruppe] neu schreiben.  
**Enthält:**  
- Zielgruppenkarte (Bedürfnisse, Einwände, Vokabular)  
- Neu geschriebene Version (≤150 Wörter)  
- 3 Überschriften-Optionen, 3 CTAs  
**Einsatz:** Wenn dieselbe Idee bei jemand Neuem landen muss.

### 12) Copy polieren (Web/Produkt)
**Arbeitsstil:** Denken. **Ausführlichkeit:** Mittel. **Format:** Abschnitte.  
**Aufgabe:** Prägnante Copy für [Seite/Abschnitt] schreiben.  
**Enthalten:** H1/H2s, scannbare Stichpunkte, Nutzen > Feature, ein Beleg, ein CTA.  
**Stil:** Konkrete Verben, kein Füllstoff, klares Deutsch.  
**Einsatz:** Wenn du sauberen, leserfreundlichen Text brauchst.

### 13) Einen Fall diagnostizieren (begründetes Workup)
**Arbeitsstil:** Denken Hoch. **Ausführlichkeit:** Lang. **Format:** Fallblatt.  
**Fall:** [Symptome/Kontext].  
**Output:**  
- Differenzialhypothesen (gerankt)  
- Tests zum Bestätigen/Widerlegen  
- Wahrscheinlichste Diagnose und Begründung  
- Plan: sofort, kurzfristig, Nachverfolgung  
**Einsatz:** Wenn sorgfältiges Schritt-für-Schritt-Denken zählt.

### 14) Persönlichkeit hinzufügen (Ton mit Absicht)
**Arbeitsstil:** Schnell. **Ausführlichkeit:** Kurz. **Format:** Stichpunkte.  
**Persona:** [Zyniker:in|Coach|Professor:in|Stand-up].  
**Aufgabe:** [Konzept] in 3 knackigen Stichpunkten erklären.  
**Regel:** Jeder Punkt ≤14 Wörter; 1 überraschende Wendung; keine Beleidigungen.  
**Einsatz:** Wenn Ton genauso wichtig ist wie Inhalt.

---

## Pro-Tipps
- **Format immer festlegen.** Stichpunkte, Tabelle, Schritte, JSON. Nimmt das Rätselraten raus.  
- **Constraints setzen.** Wortlimits, Abschnittsanzahl, Zahl der Beispiele.  
- **Kurze Begründungs-Outline zeigen lassen.** Du siehst das „Warum“ ohne Textwand.  
- **Prompts ketten.** #6 (Blend) → #10 (Plan) → #12 (Polish) ist eine Killer-Sequenz.  

Mehr Prompt-Inspiration? Schau dir all meine besten Prompts gratis bei **Prompt Magic** an und erstelle deine eigene Prompt-Bibliothek, um den Überblick zu behalten.

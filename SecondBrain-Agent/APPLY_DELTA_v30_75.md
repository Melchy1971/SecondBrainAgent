# APPLY DELTA v30.75

## Umfang

- Deterministische `AnswerEvaluator`-Stufe im bestehenden ChatEngine-Antwortpfad.
- Claim-basierte Hallucination Detection gegen vorhandene RAG-/Memory-Evidenz.
- Source Verification gegen Retrieval-IDs statt ungepruefter Zitattexte.
- Evidence und Answer Rating mit nachvollziehbaren Teilfaktoren.
- Einheitliches `Confidence`-Modell aus der bestehenden Reasoning Engine.
- Oeffentliche Self Critique und konkrete Improvement Suggestions, kein internes Chain-of-Thought.

Die Evaluation wird am Assistant-Message-Metadatensatz und im synchronen Chat-Ergebnis ausgegeben. Es entsteht keine zweite Chat-/RAG-Pipeline und keine neue Datenhaltung.

## Pruefung

```powershell
python -m compileall .
pytest -q
```

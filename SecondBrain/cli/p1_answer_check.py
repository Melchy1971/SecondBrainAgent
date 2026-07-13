"""P1 v19.6 - grounded answer check CLI."""

from __future__ import annotations

import json

from secondbrain.rag.answer_composer import AnswerComposer
from secondbrain.rag.evidence_policy import EvidenceItem


def run_answer_check() -> dict:
    answer = AnswerComposer().compose(
        "baseline",
        [EvidenceItem("baseline-source", "Baseline", "Dies ist ein belegter Antwortauszug.", 1.0)],
    )
    return {
        "status": answer.status,
        "citations": answer.citations,
        "evidence_count": answer.evidence_count,
        "answer": answer.answer,
    }


def main() -> int:
    result = run_answer_check()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result["status"] == "PASS" and result["citations"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

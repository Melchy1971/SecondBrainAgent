import re
from uuid import uuid4


class ContradictionDetector:
    def __init__(self, store):
        self.store = store

    def scan_claims(self, text: str, source: str = "manual") -> list[dict]:
        claims = []
        for match in re.finditer(r"([A-Za-zÄÖÜäöüß0-9_-]+)\s+ist\s+(nicht\s+)?([A-Za-zÄÖÜäöüß0-9_-]+)", text):
            claims.append({
                "id": str(uuid4()),
                "subject": match.group(1),
                "negated": bool(match.group(2)),
                "predicate": match.group(3),
                "source": source,
            })
        existing = self.store.load("claims", [])
        existing.extend(claims)
        self.store.save("claims", existing)
        return claims

    def contradictions(self) -> list[dict]:
        claims = self.store.load("claims", [])
        result = []
        for a in claims:
            for b in claims:
                if a["id"] == b["id"]:
                    continue
                if a["subject"].lower() == b["subject"].lower() and a["predicate"].lower() == b["predicate"].lower() and a["negated"] != b["negated"]:
                    result.append({"claim_a": a, "claim_b": b, "type": "direct_negation"})
        return result

from pathlib import Path
from .v99_common import VAULT, now_date, ensure

def read_file(p: Path, limit=2500):
    if not p.exists():
        return "Nicht vorhanden."
    return p.read_text(encoding="utf-8", errors="ignore")[:limit]

def write_knowledge_dashboard(vault: Path = VAULT) -> Path:
    target = ensure(vault / "119_KnowledgeIntelligenceDashboard") / "Knowledge_Intelligence_Dashboard_v99.md"
    sources = [
        vault / "113_EntityExtraction" / "Entity_Index.md",
        vault / "114_RelationshipEngine" / "Relationship_Index.md",
        vault / "115_TemporalKnowledgeGraph" / "Temporal_Knowledge_Graph.md",
        vault / "116_ContradictionDetection" / f"{now_date()}_contradictions.md",
        vault / "117_KnowledgeQuality" / f"{now_date()}_knowledge-quality.md",
        vault / "118_CrossSourceIntelligence" / f"{now_date()}_cross-source-intelligence.md",
    ]
    lines = ["# Knowledge Intelligence Dashboard v9.9", "", f"Aktualisiert: {now_date()}", ""]
    for src in sources:
        lines.append(f"## {src.parent.name}")
        lines.append("")
        lines.append(read_file(src))
        lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

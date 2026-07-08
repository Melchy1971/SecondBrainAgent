"""v30.46.2 - Tests fuer MemorySelector (komponiert Bestandsmodule)."""
from dataclasses import dataclass
from pathlib import Path
from time import time

from secondbrain.chat.context.memory_selector import MemorySelector


@dataclass
class Item:
    memory_id: str
    text: str
    score: float = 1.0
    created_at: float = 0.0


class FakeMemoryExplorer:
    def search(self, query: str, limit: int = 5):
        return {"ok": True, "memories": [{"content": f"Semantik zu {query}"}]}


def test_conversation_memory_keeps_tail(tmp_path: Path) -> None:
    selector = MemorySelector(tmp_path, memory_explorer=FakeMemoryExplorer())
    history = [{"role": "user", "content": str(index)} for index in range(30)]
    rows = selector.conversation(history, limit=12)
    assert len(rows) == 12
    assert rows[-1]["content"] == "29"


def test_working_memory_ranks_via_memory_ranker(tmp_path: Path) -> None:
    selector = MemorySelector(tmp_path, memory_explorer=FakeMemoryExplorer())
    now = time()
    items = [
        Item("alt", "alter Eintrag", score=1.0, created_at=now - 100_000),
        Item("neu", "neuer Eintrag", score=1.0, created_at=now),
        Item("wichtig", "wichtiger Eintrag", score=5.0, created_at=now - 100_000),
    ]
    selected = selector.working(items, limit=2)
    assert len(selected) == 2
    assert "wichtiger Eintrag" in selected
    assert "neuer Eintrag" in selected


def test_semantic_memory_uses_memory_explorer(tmp_path: Path) -> None:
    selector = MemorySelector(tmp_path, memory_explorer=FakeMemoryExplorer())
    memories = selector.semantic("pgvector", limit=3)
    assert memories == [{"content": "Semantik zu pgvector"}]


def test_select_respects_include_memory_flag(tmp_path: Path) -> None:
    selector = MemorySelector(tmp_path, memory_explorer=FakeMemoryExplorer())
    result = selector.select("frage", [{"role": "user", "content": "hi"}], include_memory=False)
    assert result["semantic"] == []
    assert result["working"] == []
    assert result["conversation"] == [{"role": "user", "content": "hi"}]

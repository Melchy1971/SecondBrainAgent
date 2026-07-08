from __future__ import annotations

from secondbrain.agent.memory_injection import MemoryInjector, MemoryQuery
from secondbrain.agent.memory_injection.budget import MemoryBudget, estimate_tokens

from tests._mem_helpers import make_record, make_store


def test_estimate_tokens_is_char_based():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1        # 4 chars -> 1 token
    assert estimate_tokens("abcde") == 2       # 5 chars -> 2 tokens


def test_budget_can_fit_and_add():
    b = MemoryBudget(max_tokens=3)
    assert b.can_fit("abcd") is True           # 1 token
    b.add("abcd")
    assert b.used == 1
    assert b.remaining == 2
    assert b.can_fit("a" * 12) is False        # 3 tokens, only 2 remain


def test_unlimited_budget_fits_everything():
    b = MemoryBudget(max_tokens=None)
    assert b.unlimited is True
    assert b.can_fit("x" * 10_000) is True
    assert b.remaining is None


def test_injection_respects_token_budget(tmp_path):
    # each text is ~40 chars -> ~10 tokens; budget of 12 admits exactly one
    store = make_store([
        make_record("g" * 40, source="a"),
        make_record("h" * 40, source="b"),
        make_record("i" * 40, source="c"),
    ])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", token_budget=12))
    assert len(ctx.evidences) == 1
    assert ctx.tokens_used <= 12
    assert any(x.reason == "token_budget" for x in ctx.exclusions)


def test_injection_respects_count_limit(tmp_path):
    store = make_store([make_record(f"Fakt {i}", source=str(i)) for i in range(5)])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", limit=2))
    assert len(ctx.evidences) == 2
    assert any(x.reason == "token_budget" and "count_limit" in x.detail for x in ctx.exclusions)


def test_budget_reported_in_context(tmp_path):
    store = make_store([make_record("kurz", source="a")])
    ctx = MemoryInjector(store).preview(MemoryQuery(text="", token_budget=100))
    d = ctx.to_dict()
    assert d["budget"]["limit"] == 100
    assert d["budget"]["used"] == ctx.tokens_used
    assert d["budget"]["remaining"] == 100 - ctx.tokens_used

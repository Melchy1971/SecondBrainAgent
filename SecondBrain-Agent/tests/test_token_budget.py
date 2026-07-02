"""v30.46.2 - Tests fuer TokenBudgetManager."""
from secondbrain.chat.context.token_budget import TokenBudgetManager


def test_token_estimation_uses_char_heuristic() -> None:
    assert TokenBudgetManager.estimate_tokens("") == 0
    assert TokenBudgetManager.estimate_tokens("abcd") == 1
    assert TokenBudgetManager.estimate_tokens("abcde") == 2
    assert TokenBudgetManager.estimate_chars(10) == 40


def test_input_budget_reserves_output_tokens() -> None:
    budget = TokenBudgetManager(max_tokens=4096, reserved_output_tokens=1024)
    assert budget.input_budget == 3072


def test_section_budgets_follow_shares_and_normalize() -> None:
    budget = TokenBudgetManager(max_tokens=4096, reserved_output_tokens=0, shares={"a": 2.0, "b": 2.0})
    assert budget.section_budget("a") == budget.section_budget("b") == int(4096 * 0.5)
    # Unbekannte Sektion bekommt ein Minimalbudget statt KeyError.
    assert budget.section_budget("unbekannt") >= 64


def test_allocate_reports_over_budget_sections() -> None:
    budget = TokenBudgetManager(max_tokens=1024, reserved_output_tokens=0, shares={"documents": 1.0})
    report = budget.allocate({"documents": "x" * 100_000})
    section = report["sections"]["documents"]
    assert section["over_budget"] is True
    assert section["budget"] == budget.section_budget("documents")
    assert report["remaining"] == 0


def test_fits_respects_section_budget() -> None:
    budget = TokenBudgetManager(max_tokens=1024, reserved_output_tokens=0, shares={"documents": 1.0})
    assert budget.fits("kurz", "documents") is True
    assert budget.fits("x" * 100_000, "documents") is False

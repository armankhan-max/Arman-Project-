import pytest

from fda.permissions import budget_manager as budget
from fda.providers import registry


def test_free_provider_needs_no_budget(db):
    p = registry.get(db, "pollinations_image")
    rec = budget.reserve(db, p, "image", 1, "images")
    assert float(rec.estimated_usd) == 0


def test_paid_provider_blocked_without_limit(db):
    p = registry.get(db, "anthropic")
    with pytest.raises(budget.BudgetError, match="spending limit"):
        budget.reserve(db, p, "llm", 1, "1k tokens")


def test_paid_provider_needs_cost_estimate(db):
    budget.set_limit(db, "daily", "", 5)
    p = registry.get(db, "anthropic")
    with pytest.raises(budget.BudgetError, match="cost estimate"):
        budget.reserve(db, p, "llm", 1, "1k tokens")


def test_limit_enforced_and_release(db):
    budget.set_limit(db, "daily", "", 1.0)
    registry.save(db, "anthropic", config={"usd_per_unit": 0.4})
    p = registry.get(db, "anthropic")
    a = budget.reserve(db, p, "llm", 1, "1k tokens")
    budget.reserve(db, p, "llm", 1, "1k tokens")
    with pytest.raises(budget.BudgetError, match="exceed"):
        budget.reserve(db, p, "llm", 1, "1k tokens")
    budget.release(db, a)
    db.flush()
    budget.reserve(db, p, "llm", 1, "1k tokens")  # released money is available again
    assert budget.status(db)["daily"]["spent"] == pytest.approx(0.8)

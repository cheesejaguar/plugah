import os
import pytest


@pytest.mark.asyncio
async def test_smoke_mock_mode(monkeypatch):
    # Ensure mock mode for deterministic CI behavior
    monkeypatch.setenv("PLUGAH_MODE", "mock")

    from plugah import BoardRoom, BudgetPolicy

    br = BoardRoom()

    # Phase 1: discovery questions
    questions = await br.startup_phase(
        problem="Test project",
        budget_usd=100.0,
        policy=BudgetPolicy.BALANCED,
    )
    assert isinstance(questions, list) and len(questions) > 0

    # Phase 2: PRD from answers
    answers = [
        "Developers",
        "Accurate summaries, Fast processing, Easy integration",
        "Must handle rate limits, Secure API keys",
        "2 weeks",
        "Slack API",
    ]
    prd = await br.process_discovery(
        answers=answers,
        problem="Test project",
        budget_usd=100.0,
        policy=BudgetPolicy.BALANCED,
    )

    # Phase 3: plan org
    oag = await br.plan_organization(prd=prd, budget_usd=100.0, policy=BudgetPolicy.BALANCED)
    assert len(oag.get_tasks()) >= 1

    # Phase 4: execute
    result = await br.execute()
    assert result.total_cost >= 0.0
    assert "tasks_completed" in result.metrics


import pytest


@pytest.mark.asyncio
async def test_smoke_mock_mode(monkeypatch, tmp_path):
    # Ensure mock mode for deterministic CI behavior
    monkeypatch.setenv("PLUGAH_MODE", "mock")
    # PRD.md files are written under ./.runs; keep them out of the repo
    monkeypatch.chdir(tmp_path)

    from plugah import BoardRoom, BudgetPolicy

    br = BoardRoom()

    # Phase 1: discovery questions
    questions = await br.startup_phase(
        problem="Test project",
        budget_usd=100.0,
        policy=BudgetPolicy.BALANCED,
    )
    assert len(questions) == 5
    assert all(q.endswith("?") for q in questions)

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
    assert prd.to_dict()["title"]
    assert len(oag.get_tasks()) >= 1
    assert oag.budget.caps.hard_cap_usd == 100.0

    # Phase 4: execute
    result = await br.execute()
    assert result.total_cost == pytest.approx(0.1)
    assert result.total_cost <= oag.budget.caps.hard_cap_usd
    assert result.metrics["tasks_completed"] == len(oag.get_tasks())
    assert result.details["project_id"] == br.project_id

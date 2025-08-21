from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_prd_md_created_on_startup(monkeypatch, tmp_path):
    # Force mock mode for deterministic behavior
    monkeypatch.setenv("PLUGAH_MODE", "mock")
    # Run in a temp cwd to avoid polluting repo .runs
    monkeypatch.chdir(tmp_path)

    from plugah import BoardRoom, BudgetPolicy

    br = BoardRoom()
    questions = await br.startup_phase(
        problem="Build a Slack summarizer bot",
        budget_usd=100.0,
        policy=BudgetPolicy.BALANCED,
    )
    assert questions and len(questions) == 5

    # Initial draft should be present
    prd_path = Path(".runs") / br.project_id / "PRD.md"
    assert prd_path.exists(), "PRD.md should be created after startup phase"
    content = prd_path.read_text()
    assert "PRD:" in content or "This document aligns" in content


@pytest.mark.asyncio
async def test_subteam_prd_created_after_planning(monkeypatch, tmp_path):
    monkeypatch.setenv("PLUGAH_MODE", "mock")
    monkeypatch.chdir(tmp_path)

    from plugah import BoardRoom, BudgetPolicy

    br = BoardRoom()
    await br.startup_phase("Project", 100.0, policy=BudgetPolicy.BALANCED)
    # Provide canned answers for mock PRD generation
    prd = await br.process_discovery(
        answers=["Users", "Criteria", "Constraints", "Timeline", "Integrations"],
        problem="Project",
        budget_usd=100.0,
    )
    await br.plan_organization(prd=prd, budget_usd=100.0, policy=BudgetPolicy.BALANCED)

    # Expect some team PRDs (e.g., for VP/Director/Manager with reports)
    teams_dir = Path(".runs") / br.project_id / "teams"
    assert teams_dir.exists(), "teams/ directory should exist"
    # There should be at least one team PRD
    found = list(teams_dir.rglob("PRD.md"))
    assert found, "At least one subteam PRD.md should be generated"


def test_reorg_updates_root_prd(monkeypatch, tmp_path):
    monkeypatch.setenv("PLUGAH_MODE", "mock")
    monkeypatch.chdir(tmp_path)

    from plugah import BoardRoom, PRD

    br = BoardRoom()

    # Seed state minimally
    br._state["problem"] = "Old Title"
    br._state["budget_usd"] = 50.0

    # Write initial PRD
    br._write_root_prd_md({"title": "Old Title", "problem_statement": "Old", "budget": 50.0})
    root = Path(".runs") / br.project_id / "PRD.md"
    assert root.exists()
    assert "Old Title" in root.read_text()

    # ReOrg with updated PRD title
    new_prd = PRD(
        {"title": "New Title", "problem_statement": "New", "budget": 50.0, "objectives": []}
    )
    br.reorg(new_prd)

    updated = root.read_text()
    assert "New Title" in updated

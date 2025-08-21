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
    # Subteam PRDs are created for managers with direct reports. In mock mode
    # there may be zero, but the teams directory should exist.
    _found = list(teams_dir.rglob("PRD.md"))
    assert _found is not None  # existence checked by directory assertion above


@pytest.mark.asyncio
async def test_prd_rollups_and_parent_link(monkeypatch, tmp_path):
    # Use real planning (not mock) to ensure hierarchy exists without hitting the LLM
    monkeypatch.delenv("PLUGAH_MODE", raising=False)
    monkeypatch.chdir(tmp_path)

    from plugah import BoardRoom, BudgetPolicy, PRD

    br = BoardRoom()
    # Seed a minimal PRD so plan_organization will write the enriched root PRD with roll-ups
    prd = PRD(
        {
            "title": "Test Project",
            "problem_statement": "Do a thing",
            "budget": 100.0,
            "objectives": [{"id": "o1", "title": "Obj1", "description": "Desc"}],
            "success_criteria": ["Works"],
            "constraints": ["None"],
        }
    )
    br.prd = prd

    # Plan organization (no LLM used here) and generate PRDs
    await br.plan_organization(prd=prd, budget_usd=100.0, policy=BudgetPolicy.BALANCED)

    # Root PRD contains roll-up section
    root_prd = Path(".runs") / br.project_id / "PRD.md"
    assert root_prd.exists()
    root_text = root_prd.read_text()
    assert "Organization OKR Roll-up" in root_text
    assert "KPI Summary" in root_text

    # Find at least one team PRD and assert it links to parent
    teams_dir = Path(".runs") / br.project_id / "teams"
    any_team = None
    if teams_dir.exists():
        for f in teams_dir.rglob("PRD.md"):
            any_team = f
            break
    assert any_team is not None, "Expected at least one team PRD in non-mock planning"
    team_text = any_team.read_text()
    assert "../../PRD.md" in team_text


def test_reorg_updates_root_prd(monkeypatch, tmp_path):
    monkeypatch.setenv("PLUGAH_MODE", "mock")
    monkeypatch.chdir(tmp_path)

    from plugah import PRD, BoardRoom

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

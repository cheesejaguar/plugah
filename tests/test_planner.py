"""
Tests for the Planner module
"""

from plugah.oag_schema import RoleLevel, TaskStatus
from plugah.planner import Planner


def test_planner_creates_board_room():
    """Test that planner creates C-suite executives"""

    planner = Planner()

    prd = {
        "title": "Test Project",
        "domain": "web",
        "objectives": [
            {"id": "obj1", "title": "Build MVP", "description": "Create minimum viable product"}
        ],
        "constraints": ["Must be scalable"],
        "success_criteria": ["Works correctly", "Good performance"]
    }

    oag = planner.plan(prd, budget_usd=100.0)

    # Check board room exists
    agents = oag.get_agents()

    # Find C-suite
    c_suite = [a for a in agents.values() if a.level == RoleLevel.C_SUITE]

    assert len(c_suite) >= 3  # CEO, CTO, CFO

    # Check specific roles
    roles = [a.role for a in c_suite]
    assert "CEO" in roles
    assert "CTO" in roles
    assert "CFO" in roles


def test_planner_creates_tasks():
    """Test that planner creates tasks with contracts"""

    planner = Planner()

    prd = {
        "title": "Test Project",
        "domain": "api",
        "objectives": [
            {"id": "obj1", "title": "Build API", "description": "Create REST API"}
        ],
        "constraints": [],
        "success_criteria": ["API works"]
    }

    oag = planner.plan(prd, budget_usd=50.0)

    # Check tasks exist
    tasks = oag.get_tasks()
    assert len(tasks) > 0

    # Check tasks have contracts
    for task in tasks.values():
        assert task.contract is not None
        assert task.contract.definition_of_done != ""
        assert task.status == TaskStatus.PLANNED


def test_planner_creates_edges():
    """Test that planner creates task dependencies"""

    planner = Planner()

    prd = {
        "title": "Test Project",
        "domain": "data",
        "objectives": [
            {"id": "obj1", "title": "Process Data", "description": "ETL pipeline"}
        ],
        "constraints": [],
        "success_criteria": []
    }

    oag = planner.plan(prd, budget_usd=200.0)

    # Check edges exist
    assert len(oag.edges) > 0

    # Check edges connect tasks
    task_ids = set(oag.get_tasks().keys())
    for edge in oag.edges:
        # At least one end should be a task
        assert edge.from_id in task_ids or edge.to_id in task_ids


def test_budget_policy_selection():
    """Test that budget policy is selected appropriately"""

    planner = Planner()

    # Small budget -> conservative
    prd_small = {
        "title": "Small Project",
        "domain": "web",
        "objectives": [{"id": "obj1", "title": "Simple task"}],
        "constraints": [],
        "success_criteria": []
    }

    oag_small = planner.plan(prd_small, budget_usd=15.0)
    assert oag_small.budget.policy.value == "conservative"

    # Large budget with few objectives -> aggressive
    prd_large = {
        "title": "Large Project",
        "domain": "web",
        "objectives": [
            {"id": "obj1", "title": "Task 1"},
            {"id": "obj2", "title": "Task 2"}
        ],
        "constraints": [],
        "success_criteria": []
    }

    oag_large = planner.plan(prd_large, budget_usd=500.0)
    assert oag_large.budget.policy.value == "aggressive"


def test_staffing_levels():
    """Test that staffing levels adjust based on budget"""

    planner = Planner()

    prd = {
        "title": "Test Project",
        "domain": "web",
        "objectives": [{"id": "obj1", "title": "Build site"}],
        "constraints": [],
        "success_criteria": []
    }

    # Small budget = fewer staff
    oag_small = planner.plan(prd, budget_usd=30.0)
    agents_small = oag_small.get_agents()

    # Large budget = more staff
    oag_large = planner.plan(prd, budget_usd=300.0)
    agents_large = oag_large.get_agents()

    assert len(agents_large) > len(agents_small)
